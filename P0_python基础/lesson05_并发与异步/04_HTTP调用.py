"""P0-14 HTTP 调用：requests 与 httpx。运行：python 04_HTTP调用.py

全部离线运行：
- 第 1 节在本机 127.0.0.1 上起一个临时 HTTP 服务，演示真实的网络请求和超时；
- 其余各节用 httpx.MockTransport 模拟服务端，请求不会离开本进程。
计时结果会浮动，看量级。
"""

import asyncio
import http.server
import json
import random
import threading
import time

import httpx
import requests


def section(title):
    print(f"\n===== {title} =====")


# ---------------------------------------------------------------------------
# 第 1 节用的本机 HTTP 服务
# ---------------------------------------------------------------------------


class LocalHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            time.sleep(1.0)  # 模拟服务端处理很慢
        body = json.dumps({"path": self.path, "msg": "来自本机服务"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # 不打印访问日志
        pass


def start_local_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), LocalHandler)  # 端口 0：系统随机分配
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def demo_real_requests():
    section("1. 真实请求：requests 和 httpx 的同步用法（访问本机临时服务）")
    server = start_local_server()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        # requests：没有默认超时，不传 timeout 可能永远等下去
        with requests.Session() as s:  # Session 复用连接
            s.trust_env = False  # 不读环境变量和系统里的代理设置
            r = s.get(f"{base}/hello", timeout=2)
            r.raise_for_status()
            print("  requests:", r.status_code, r.json())

        # httpx 默认会读系统代理。本机开了代理时，访问 127.0.0.1 也会被转给代理
        try:
            r = httpx.get(f"{base}/hello", timeout=2)
            print("  httpx 默认设置:", r.status_code, "（503 说明请求被系统代理拦截了）" if r.status_code == 503 else "")
        except httpx.HTTPError as e:
            print("  httpx 默认设置出错:", type(e).__name__)

        with httpx.Client(base_url=base, timeout=2, trust_env=False) as client:
            r = client.get("/hello")
            print("  httpx trust_env=False:", r.status_code, r.json())

            t0 = time.perf_counter()
            try:
                client.get("/slow", timeout=0.3)  # 单次请求可以覆盖 Client 的默认超时
            except httpx.ReadTimeout as e:
                print(f"  httpx 读超时: {type(e).__name__}，用时 {time.perf_counter() - t0:.2f}s")

        t0 = time.perf_counter()
        try:
            requests.Session().get(f"{base}/slow", timeout=(1, 0.3))  # (连接超时, 读超时)
        except requests.exceptions.ReadTimeout as e:
            print(f"  requests 读超时: {type(e).__name__}，用时 {time.perf_counter() - t0:.2f}s")
    finally:
        server.shutdown()


# ---------------------------------------------------------------------------
# 第 2 节起用 MockTransport：handler 收到 httpx.Request，返回 httpx.Response
# ---------------------------------------------------------------------------


def sync_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/chat" and request.method == "POST":
        payload = json.loads(request.content)
        return httpx.Response(200, json={"reply": f"你说的是：{payload['message']}"})
    if request.url.path == "/stream":
        lines = [
            ": 这是注释行，SSE 里用来保活",
            'data: {"delta": "你"}',
            "",
            'data: {"delta": "好"}',
            "",
            "data: [DONE]",
            "",
        ]
        return httpx.Response(200, text="\n".join(lines))
    if request.url.path == "/boom":
        return httpx.Response(500, json={"error": "服务端出错"})
    return httpx.Response(404, json={"error": "没有这个接口"})


def demo_json_and_status():
    section("2. JSON 请求、状态码和 raise_for_status（MockTransport）")
    with httpx.Client(transport=httpx.MockTransport(sync_handler), base_url="http://mock") as client:
        r = client.post("/chat", json={"message": "你好"})  # json= 会序列化并设置 Content-Type
        print("  请求头 Content-Type:", r.request.headers["content-type"])
        print("  状态码:", r.status_code, " r.json():", r.json())

        r = client.get("/nothing")
        print("  404 不会自动抛异常: r.status_code =", r.status_code, " r.is_success =", r.is_success)

        for path in ("/nothing", "/boom"):
            try:
                client.get(path).raise_for_status()
            except httpx.HTTPStatusError as e:
                print(f"  raise_for_status: {e.response.status_code} -> {type(e).__name__}")


def demo_sync_stream():
    section("3. 同步流式读取：client.stream + iter_lines")
    with httpx.Client(transport=httpx.MockTransport(sync_handler), base_url="http://mock") as client:
        with client.stream("GET", "/stream") as r:  # 只收完响应头就返回，响应体按需读取
            for line in r.iter_lines():
                print(f"  {line!r}")


async def async_handler(request: httpx.Request) -> httpx.Response:
    """MockTransport 也接受 async 函数，可以在里面 await asyncio.sleep 模拟慢响应。"""
    if request.url.path.startswith("/item/"):
        await asyncio.sleep(0.3)
        return httpx.Response(200, json={"id": request.url.path.split("/")[-1]})
    if request.url.path == "/slow":
        await asyncio.sleep(1.0)
        return httpx.Response(200, json={"msg": "终于返回了"})
    if request.url.path == "/stream":
        return httpx.Response(200, content=token_stream())
    return httpx.Response(404)


async def token_stream():
    """响应体是一个异步生成器：每隔一段时间吐出一块字节，模拟模型的流式输出。"""
    for word in ["你", "好", "，", "世界"]:
        yield f'data: {{"delta": "{word}"}}\n\n'.encode()
        await asyncio.sleep(0.15)
    yield b"data: [DONE]\n\n"


async def demo_async_client():
    section("4. AsyncClient：并发请求和总超时")
    transport = httpx.MockTransport(async_handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://mock") as client:
        t0 = time.perf_counter()
        responses = await asyncio.gather(*(client.get(f"/item/{i}") for i in range(5)))
        print(f"  5 个请求并发，每个 0.3s：总用时 {time.perf_counter() - t0:.2f}s")
        print("  结果:", [r.json()["id"] for r in responses])

        t0 = time.perf_counter()
        r = await client.get("/slow", timeout=0.1)
        print(f"  给 httpx 传了 timeout=0.1，却等了 {time.perf_counter() - t0:.2f}s 并拿到 {r.status_code}")
        print("  原因：超时由真实的网络层执行，MockTransport 不执行它")

        t0 = time.perf_counter()
        try:
            async with asyncio.timeout(0.2):  # 总耗时上限，不依赖网络层
                await client.get("/slow")
        except TimeoutError:
            print(f"  asyncio.timeout(0.2)：{time.perf_counter() - t0:.2f}s 后抛出 TimeoutError")


async def demo_async_stream():
    section("5. 异步流式读取：client.stream + aiter_lines（下一课 SSE 的基础）")
    async with httpx.AsyncClient(transport=httpx.MockTransport(async_handler), base_url="http://mock") as client:
        t0 = time.perf_counter()
        async with client.stream("GET", "/stream") as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue  # 跳过空行
                data = line.removeprefix("data: ")
                if data == "[DONE]":
                    break
                print(f"  [{time.perf_counter() - t0:.2f}s] 收到 {json.loads(data)['delta']!r}")
    print("  每一块一到就处理，不用等整个响应下载完")


async def demo_retry():
    section("6. 重试与指数退避（带抖动）")
    attempts = 0

    async def flaky_handler(request):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, text="服务繁忙")
        if attempts == 2:
            raise httpx.ConnectError("连接被重置", request=request)
        return httpx.Response(200, json={"answer": 42})

    def should_retry(exc):
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in (429, 500, 502, 503, 504)
        return isinstance(exc, httpx.TransportError)  # 连接错误、超时等

    async def get_with_retry(client, url, max_attempts=4, base_delay=0.05, max_delay=1.0):
        for attempt in range(1, max_attempts + 1):
            try:
                r = await client.get(url)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError as e:
                if attempt == max_attempts or not should_retry(e):
                    raise
                delay = min(max_delay, base_delay * 2 ** (attempt - 1))  # 0.05, 0.1, 0.2 ...
                delay = random.uniform(0, delay)  # 全抖动：在 [0, delay] 之间随机
                print(f"  第 {attempt} 次失败（{type(e).__name__}），{delay:.3f}s 后重试")
                await asyncio.sleep(delay)

    async with httpx.AsyncClient(transport=httpx.MockTransport(flaky_handler), base_url="http://mock") as client:
        print("  最终结果:", await get_with_retry(client, "/answer"), f"，共请求 {attempts} 次")
    print("  抖动让大量客户端不会在同一时刻一起重试")


def main():
    demo_real_requests()
    demo_json_and_status()
    demo_sync_stream()
    asyncio.run(demo_async_client())
    asyncio.run(demo_async_stream())
    asyncio.run(demo_retry())


if __name__ == "__main__":
    main()
