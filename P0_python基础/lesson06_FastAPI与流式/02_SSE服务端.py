"""P0-16 SSE 服务端：用 StreamingResponse + 异步生成器，把“假模型”的 token 逐个推给客户端。

两种运行方式：
    python 02_SSE服务端.py          启动服务 http://127.0.0.1:8000
    python 02_SSE服务端.py --demo   不启动服务，直接迭代生成器 + 用 TestClient 请求一遍

服务启动后，另开一个终端：
    curl -N "http://127.0.0.1:8000/chat/stream?prompt=hello"    逐块看到 data: 行
    curl "http://127.0.0.1:8000/chat/once?prompt=hello"         非流式：等全部生成完才一次返回
    curl -N http://127.0.0.1:8000/sse/format                    看 event:、id:、多行 data、注释行
-N 的作用是关闭 curl 自己的输出缓冲，否则可能攒一批才显示。
prompt 里有中文时，不要直接写进 URL（uvicorn 会报 Invalid HTTP request），让 curl 做 URL 编码：
    curl -N -G http://127.0.0.1:8000/chat/stream --data-urlencode "prompt=你好"
"""

import asyncio
import json
import sys
import time
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

# ---------------------------------------------------------------------------
# 1. 假模型：逐个 token 产出文本。真实模型的流式接口在调用方看来也是这样一个异步迭代器
# ---------------------------------------------------------------------------

FIRST_TOKEN_DELAY = 0.6  # 模拟首 token 延迟（模型处理 prompt 的时间）
TOKEN_INTERVAL = 0.15  # 模拟后续每个 token 的生成间隔


async def fake_llm(prompt: str) -> AsyncIterator[str]:
    answer = f"你说的是「{prompt}」。\n我是一个假模型，会把回答拆成很多小块，一块一块地发给你。"
    tokens = [answer[i : i + 2] for i in range(0, len(answer), 2)]  # 每 2 个字符算一个 token
    await asyncio.sleep(FIRST_TOKEN_DELAY)
    for token in tokens:
        yield token
        await asyncio.sleep(TOKEN_INTERVAL)


# ---------------------------------------------------------------------------
# 2. 把一条消息格式化成 SSE 事件
# ---------------------------------------------------------------------------


def format_sse(data: str, event: str | None = None, id: str | None = None) -> str:
    """生成一条 SSE 事件文本。

    格式规则：
    - 每个字段一行，形如 "字段名: 值"；
    - data 里有换行时，要拆成多行 data:，客户端会用 \\n 把它们拼回去；
    - 一个空行表示这条事件结束。所以整条事件以 "\\n\\n" 结尾。
    """
    lines = []
    if event is not None:
        lines.append(f"event: {event}")
    if id is not None:
        lines.append(f"id: {id}")
    for line in data.split("\n"):
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


# Cache-Control: no-cache   防止中间代理或浏览器缓存流式内容
# X-Accel-Buffering: no     告诉 Nginx 不要缓冲这个响应，否则 Nginx 会攒满缓冲区才往下发
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

app = FastAPI(title="第六课示例：SSE")


# ---------------------------------------------------------------------------
# 3. OpenAI 风格的流式接口：每个 token 一条 data: {json}，最后 data: [DONE]
# ---------------------------------------------------------------------------


async def chat_events(prompt: str, request: Request) -> AsyncIterator[str]:
    sent = 0
    try:
        async for token in fake_llm(prompt):
            # 客户端断开后继续生成就是白白消耗模型额度，所以每次产出前检查一下
            if await request.is_disconnected():
                print(f"[chat_events] is_disconnected() 为 True，停止生成（已发送 {sent} 个 token）")
                return
            # 用 JSON 包装 token：token 里可能有换行，直接放进 data: 会破坏事件格式
            payload = json.dumps({"delta": token}, ensure_ascii=False)
            yield format_sse(payload)
            sent += 1
        # [DONE] 是 OpenAI 的约定，告诉客户端“正常结束了”。SSE 标准里没有这个东西
        yield format_sse("[DONE]")
        print(f"[chat_events] 正常结束，共发送 {sent} 个 token")
    except asyncio.CancelledError:
        # Starlette 自己也在监听断开：在 uvicorn 下，客户端断开后它会取消正在跑的生成器，
        # 生成器在当前 await 处收到 CancelledError。这里只记录日志，然后必须重新抛出
        print(f"[chat_events] 被取消（客户端断开），已发送 {sent} 个 token")
        raise


@app.get("/chat/stream")
async def chat_stream(prompt: str, request: Request):
    # 返回 StreamingResponse 时路由函数立即返回，生成器之后由 Starlette 逐块迭代并发送
    return StreamingResponse(
        chat_events(prompt, request),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@app.get("/chat/once")
async def chat_once(prompt: str):
    """非流式对照：等全部 token 生成完再返回。"""
    text = "".join([token async for token in fake_llm(prompt)])
    return {"content": text}


# ---------------------------------------------------------------------------
# 4. SSE 格式全貌：event、id、多行 data、注释行
# ---------------------------------------------------------------------------


async def format_events() -> AsyncIterator[str]:
    yield ": 以冒号开头的是注释行，客户端会忽略。常用来定期发送保持连接（心跳）\n\n"
    yield format_sse("第一条，没有 event 字段，客户端当作默认的 message 事件", id="1")
    await asyncio.sleep(0.3)
    yield format_sse('{"step": "search", "status": "running"}', event="tool", id="2")
    await asyncio.sleep(0.3)
    yield format_sse("第一行\n第二行\n第三行", id="3")  # 一条事件，拆成 3 行 data:
    await asyncio.sleep(0.3)
    yield format_sse("bye", event="end", id="4")


@app.get("/sse/format")
async def sse_format():
    return StreamingResponse(format_events(), media_type="text/event-stream", headers=SSE_HEADERS)


# ---------------------------------------------------------------------------
# 离线演示
# ---------------------------------------------------------------------------


def section(title):
    print(f"\n===== {title} =====")


async def show_token_timing():
    start = time.perf_counter()
    async for token in fake_llm("你好"):
        print(f"  {time.perf_counter() - start:5.2f}s  {token!r}")
    print(f"  首 token 在 {FIRST_TOKEN_DELAY}s 左右到达；非流式接口要等到最后一行的时间才能返回")


def demo():
    from fastapi.testclient import TestClient

    section("1. 直接迭代假模型，看每个 token 的到达时间")
    asyncio.run(show_token_timing())

    section("2. format_sse 生成的原始文本（repr 能看到 \\n）")
    print(" ", repr(format_sse('{"delta": "你好"}')))
    print(" ", repr(format_sse("第一行\n第二行", event="tool", id="7")))

    client = TestClient(app)

    section("3. 请求 /chat/stream：响应头")
    # TestClient 会等生成器跑完再交出响应，所以这里看不到“逐块到达”，只验证内容和格式
    with client.stream("GET", "/chat/stream", params={"prompt": "你好"}) as resp:
        print("  status        :", resp.status_code)
        print("  content-type  :", resp.headers["content-type"])
        print("  cache-control :", resp.headers["cache-control"])
        body = resp.read().decode()

    section("4. /chat/stream 的原始响应体（前 3 条事件和最后一条）")
    events = [e + "\n\n" for e in body.split("\n\n")[:-1]]  # 按空行切开，最后一段是空串
    for e in events[:3]:
        print(" ", repr(e))
    print("  ...")
    print(" ", repr(events[-1]))
    print(f"  共 {len(events)} 条事件。token 里的换行在 JSON 里是 \\n 转义，不会破坏事件格式")

    section("5. /sse/format 的原始响应体")
    print(client.get("/sse/format").text)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        uvicorn.run(app, host="127.0.0.1", port=8000)
