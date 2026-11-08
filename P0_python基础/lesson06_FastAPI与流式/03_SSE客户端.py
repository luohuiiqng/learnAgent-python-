"""P0-16 SSE 客户端：用 httpx 流式读取响应，边收边解析事件。

两种运行方式：
    python 03_SSE客户端.py          连接 http://127.0.0.1:8000/chat/stream（先在另一个终端运行 python 02_SSE服务端.py）
    python 03_SSE客户端.py --demo   不需要服务，用 TestClient 直接调用 02 里的 app，再演示按字节块解析时的坑

注意系统代理：本机开了 127.0.0.1:8080 的系统代理，httpx 默认会读取代理设置，
访问 127.0.0.1:8000 也会发给代理，结果是 503。所以下面的 AsyncClient 传了 trust_env=False。
另一种办法是运行前设置环境变量：NO_PROXY=localhost,127.0.0.1 python 03_SSE客户端.py
"""

import asyncio
import importlib.util
import json
import sys
import time
from pathlib import Path

import httpx

URL = "http://127.0.0.1:8000/chat/stream"

# ---------------------------------------------------------------------------
# 1. 按“行”解析 SSE：一次喂一行，遇到空行时交出一条完整事件
# ---------------------------------------------------------------------------


class SSELineParser:
    """最小的 SSE 行解析器。输入必须是已经切好、去掉换行符的一行文本。"""

    def __init__(self):
        self._event = "message"
        self._data_lines: list[str] = []

    def feed_line(self, line: str) -> dict | None:
        if line == "":  # 空行：一条事件结束
            if not self._data_lines:
                return None
            event = {"event": self._event, "data": "\n".join(self._data_lines)}
            self._event, self._data_lines = "message", []
            return event
        if line.startswith(":"):  # 注释行，忽略
            return None
        field, _, value = line.partition(":")
        value = value.removeprefix(" ")  # 冒号后面最多去掉一个空格
        if field == "data":
            self._data_lines.append(value)
        elif field == "event":
            self._event = value
        return None  # id、retry 等字段这里不处理


def handle_event(event: dict) -> str | None:
    """把 /chat/stream 的事件转成文本增量。返回 None 表示流结束。"""
    if event["data"] == "[DONE]":
        return None
    return json.loads(event["data"])["delta"]


# ---------------------------------------------------------------------------
# 2. 真实网络：httpx.AsyncClient.stream + aiter_lines
# ---------------------------------------------------------------------------


async def stream_chat(prompt: str):
    parser = SSELineParser()
    start = time.perf_counter()
    first_token_at = None
    # trust_env=False：不读取系统代理和环境变量里的代理设置
    # timeout：read 超时指“两次收到数据之间”最多等多久，不是整个流的总时长
    async with httpx.AsyncClient(trust_env=False, timeout=httpx.Timeout(10, read=30)) as client:
        # client.stream(...) 收到响应头就返回，响应体还没读。对比 client.get(...) 会把整个响应体读完
        async with client.stream("GET", URL, params={"prompt": prompt}) as resp:
            resp.raise_for_status()
            print(f"状态码 {resp.status_code}，Content-Type: {resp.headers['content-type']}")
            # aiter_lines() 内部已经处理好两件事：把跨块的行拼起来、按 UTF-8 正确解码
            async for line in resp.aiter_lines():
                event = parser.feed_line(line)
                if event is None:
                    continue
                delta = handle_event(event)
                if delta is None:
                    break
                if first_token_at is None:
                    first_token_at = time.perf_counter() - start
                print(delta, end="", flush=True)  # flush 让文字立即显示，不等换行
    total = time.perf_counter() - start
    print(f"\n\n首 token 用时 {first_token_at:.2f}s，总用时 {total:.2f}s")


# ---------------------------------------------------------------------------
# 离线演示
# ---------------------------------------------------------------------------


def section(title):
    print(f"\n===== {title} =====")


def load_server_module():
    """02_SSE服务端.py 的文件名不能直接 import（以数字开头），用 importlib 按路径加载。"""
    path = Path(__file__).with_name("02_SSE服务端.py")
    spec = importlib.util.spec_from_file_location("sse_server", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def demo():
    from fastapi.testclient import TestClient

    server = load_server_module()
    client = TestClient(server.app)  # TestClient 是 httpx.Client 的子类，stream/iter_lines 用法一样

    section("1. 同步写法：client.stream + iter_lines")
    parser = SSELineParser()
    text = []
    with client.stream("GET", "/chat/stream", params={"prompt": "你好"}) as resp:
        for line in resp.iter_lines():
            event = parser.feed_line(line)
            if event is None:
                continue
            delta = handle_event(event)
            if delta is None:
                break
            text.append(delta)
    print("拼起来的回答:", "".join(text))

    section("2. 解析 /sse/format：event 字段和多行 data")
    parser = SSELineParser()
    with client.stream("GET", "/sse/format") as resp:
        for line in resp.iter_lines():
            event = parser.feed_line(line)
            if event is not None:
                print(" ", event)

    section("3. 坑：网络按字节块到达，块边界和事件边界无关")
    raw = 'data: {"delta": "你好"}\n\ndata: [DONE]\n\n'.encode()
    chunks = [raw[:5], raw[5:19], raw[19:30], raw[30:]]  # 故意在任意位置切开，第 2、3 块之间切断了“你”字
    for c in chunks:
        print(f"  收到块 {c!r}")
    print("  错误做法 A：每块单独 decode")
    for c in chunks:
        try:
            c.decode("utf-8")
        except UnicodeDecodeError as e:
            print(f"    {c!r} -> UnicodeDecodeError：{e.reason}（一个汉字的 3 个字节被拆到了两块里）")
    print("  错误做法 B：把每块当成一条事件 -> 拿到的是", [c.decode("utf-8", errors="replace") for c in chunks[:1]], "这种残缺数据")
    print("  正确做法：先把字节攒进缓冲区，凑出完整的一行（遇到 \\n）再解码、解析。")
    print("  这正是 aiter_lines() 替你做的事；练习 6 要求你自己实现一遍。")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        try:
            asyncio.run(stream_chat("讲讲 SSE"))
        except httpx.ConnectError:
            print("连接失败：先在另一个终端运行 python 02_SSE服务端.py")
