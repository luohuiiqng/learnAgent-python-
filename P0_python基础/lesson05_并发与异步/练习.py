"""
第五课练习。补全每个函数，然后运行：python 练习.py
运行结果里每道题会显示 ✅ / ❌ / ⏳（未完成）。

规则：
- 只改函数体（练习 1 是改两个方法的方法体），不要改函数签名和下面的检查代码。
- 这是练习不是考试，可以回看 README 和示例，但不要让 AI 替你写。
- 检查代码会测耗时和同时运行的任务数，串行执行、不限并发、吞掉取消都会被判错。
- 全部完成后，整个文件应该在 15 秒内跑完。
"""

import asyncio
import json
import random
import threading
import time

import httpx


# 练习 1（P0-12）
class _RacyAccount:
    """不要修改这个类。_unsafe_add 模拟一段"读、计算、写"的非原子更新。"""

    def __init__(self):
        self.balance = 0

    def _unsafe_add(self, amount):
        current = self.balance
        time.sleep(0)  # 让出 GIL，模拟读和写之间的其他计算；这时别的线程可能插进来
        self.balance = current + amount


class SafeAccount(_RacyAccount):
    """线程安全的账户。

    - __init__：先调用 super().__init__()，再创建一把 threading.Lock 保存到 self 上；
    - deposit(amount)：通过 self._unsafe_add(amount) 完成存款（不要直接改 self.balance），
      用锁保证多个线程同时存款时不丢更新。
    """

    def __init__(self):
        raise NotImplementedError

    def deposit(self, amount):
        raise NotImplementedError


def parallel_deposit(account, n_threads, n_per_thread):
    """用 threading.Thread 创建 n_threads 个线程，每个线程调用 n_per_thread 次 account.deposit(1)。
    所有线程要同时运行：先全部 start，再全部 join。函数返回时所有线程都已结束。
    """
    raise NotImplementedError


# 练习 2（P0-13）
async def gather_limited(factories, limit):
    """并发运行一组异步任务，但同一时刻最多运行 limit 个。

    factories: 列表，每个元素是一个无参数的 async 函数，调用 f() 得到协程。
    返回：结果列表，顺序和 factories 一致（不是完成顺序）。
    任一任务抛异常时，把异常抛给调用方。
    提示：asyncio.Semaphore。
    """
    raise NotImplementedError


# 练习 3（P0-13）
def slow_checksum(data):
    """不要修改：一个阻塞函数（比如调用了不支持 async 的 SDK），每次耗时约 0.2 秒。"""
    time.sleep(0.2)
    return sum(data) % 256


async def checksum_all(chunks):
    """对 chunks 里每个 bytes 调用 slow_checksum，返回结果列表（顺序和输入一致）。

    要求：
    - 不能卡住事件循环（不能在协程里直接调用 slow_checksum）；
    - 多个调用要并发执行，总耗时接近一次调用的耗时。
    提示：asyncio.to_thread。
    """
    raise NotImplementedError


# 练习 4（P0-13）
async def results_within(jobs, timeout):
    """同时启动所有任务，最多等 timeout 秒，返回这段时间内成功完成的结果。

    jobs: dict，{任务名: 无参数的 async 函数}
    返回：dict，{任务名: 结果}，只包含在 timeout 内成功完成的任务：
    - 抛了异常的任务不放进结果；
    - 到时间还没完成的任务要取消，并且等它们真正结束后再返回；
    - 所有任务都提前完成时，立即返回，不要等满 timeout。
    提示：asyncio.wait(..., timeout=...) 返回 (done, pending)。
    """
    raise NotImplementedError


# 练习 5（P0-13）
async def retry_async(
    func,
    *,
    max_attempts=3,
    base_delay=0.1,
    max_delay=2.0,
    retry_on=(Exception,),
    sleep=asyncio.sleep,
    rand=random.random,
):
    """调用 await func()，失败时按指数退避重试，返回第一次成功的结果。

    - 第 k 次失败后（k 从 1 开始）等待：min(max_delay, base_delay * 2 ** (k - 1)) * rand()
      也就是指数退避加"全抖动"。rand() 返回 [0, 1) 之间的数。
    - 等待必须用 await sleep(秒数)，不要直接调用 asyncio.sleep（检查代码会替换 sleep 和 rand）。
    - 只重试 retry_on 里的异常类型；其他异常立即抛出，不重试。
    - 共尝试 max_attempts 次，全部失败时抛出最后一次的异常；最后一次失败后不再等待。
    - 任务被取消时（CancelledError）必须立刻停止，不能当成普通失败去重试。
    """
    raise NotImplementedError


# 练习 6（P0-14）
async def fetch_json(client, url, *, timeout=5.0):
    """用 httpx.AsyncClient 发 GET 请求，返回解析后的 JSON。

    - 把 timeout 传给 client.get（真实网络下由 httpx 执行）；
    - 同时用 asyncio.timeout(timeout) 限制整个调用的总耗时（MockTransport 不执行 httpx 的超时）；
    - 超时，或者 httpx 抛出 httpx.TimeoutException 时，统一抛出内置的 TimeoutError；
    - 状态码 404：返回 None；
    - 其他非 2xx 状态码：调用 raise_for_status()，让 httpx.HTTPStatusError 抛给调用方；
    - 2xx：返回 response.json()。
    """
    raise NotImplementedError


# 练习 7（P0-14）
async def stream_deltas(client, url):
    """异步生成器：流式读取一个 SSE 风格的响应，每解析出一段文本就 yield 一次。

    响应体是若干行文本：
    - 以 "data: " 开头的行，后面是 JSON，例如 data: {"delta": "你"}，yield 其中 "delta" 的值；
    - 遇到 data: [DONE] 时结束，后面的内容都不要处理；
    - 其他行（空行、以 ":" 开头的注释行等）跳过。
    要求边收边处理：用 client.stream(...) 和 aiter_lines()，不要等整个响应下载完。
    遇到非 2xx 状态码时调用 raise_for_status() 抛出异常。
    """
    raise NotImplementedError
    yield  # 有这一行，这个函数才是异步生成器。实现时删掉上面的 raise，这一行可以留着或删掉


# ---------------------------------------------------------------------------
# 下面是检查代码，不要修改
# ---------------------------------------------------------------------------


class _Probe:
    """记录同时运行的任务数。"""

    def __init__(self):
        self.running = 0
        self.peak = 0

    def enter(self):
        self.running += 1
        self.peak = max(self.peak, self.running)

    def leave(self):
        self.running -= 1


def _check_safe_account():
    acc = SafeAccount()
    assert acc.balance == 0, "__init__ 里要先调用 super().__init__()"
    parallel_deposit(acc, 8, 200)
    assert acc.balance == 1600, f"期望 1600，实际 {acc.balance}：丢失了更新，检查锁有没有包住 _unsafe_add"

    calls = []
    orig = acc._unsafe_add
    acc._unsafe_add = lambda amount: (calls.append(amount), orig(amount))
    acc.deposit(5)
    assert calls == [5], "deposit 要通过 self._unsafe_add 完成存款"

    class Watcher:
        """deposit 里故意不加锁并 sleep，用来观察线程是否同时运行。"""

        def __init__(self):
            self.lock = threading.Lock()
            self.inside = 0
            self.peak = 0
            self.count = 0

        def deposit(self, amount):
            with self.lock:
                self.inside += 1
                self.peak = max(self.peak, self.inside)
            time.sleep(0.005)
            with self.lock:
                self.inside -= 1
                self.count += amount

    w = Watcher()
    parallel_deposit(w, 4, 5)
    assert w.count == 20, f"期望调用 deposit 20 次，实际 {w.count} 次"
    assert w.peak > 1, "线程是一个接一个跑的：不要在同一个循环里 start 完马上 join"


async def _check_gather_limited():
    probe = _Probe()

    def make(i):
        async def job():
            probe.enter()
            try:
                await asyncio.sleep(0.05 + (i % 3) * 0.05)  # 耗时不同，完成顺序和传入顺序不一样
                return i * i
            finally:
                probe.leave()

        return job

    t0 = time.perf_counter()
    results = await gather_limited([make(i) for i in range(10)], 3)
    elapsed = time.perf_counter() - t0
    assert probe.peak <= 3, f"同时运行了 {probe.peak} 个任务，超过上限 3"
    assert probe.peak == 3, f"最多只同时运行了 {probe.peak} 个任务，没有用满并发"
    assert results == [i * i for i in range(10)], f"结果顺序不对：{results}"
    assert elapsed < 0.7, f"用时 {elapsed:.2f}s，太慢了（串行需要约 0.95s）"

    probe2 = _Probe()

    def make2(i):
        async def job():
            probe2.enter()
            try:
                await asyncio.sleep(0.05)
                return i
            finally:
                probe2.leave()

        return job

    assert await gather_limited([make2(i) for i in range(4)], 10) == [0, 1, 2, 3]
    assert probe2.peak == 4, "上限大于任务数时，所有任务应该同时运行"

    async def ok():
        return 1

    async def boom():
        raise ValueError("任务失败")

    try:
        await gather_limited([ok, boom], 2)
        raise AssertionError("任务抛异常时应该把异常抛给调用方")
    except ValueError:
        pass


async def _check_checksum_all():
    ticks = 0
    stop = False

    async def heartbeat():
        nonlocal ticks
        while not stop:
            await asyncio.sleep(0.02)
            ticks += 1

    hb = asyncio.create_task(heartbeat())
    await asyncio.sleep(0)
    chunks = [bytes([i, i + 1, i + 2]) for i in range(5)]
    t0 = time.perf_counter()
    results = await checksum_all(chunks)
    elapsed = time.perf_counter() - t0
    stop = True
    await hb
    assert results == [sum(c) % 256 for c in chunks], f"结果不对：{results}"
    assert ticks >= 4, f"执行期间心跳只跳了 {ticks} 次：事件循环被卡住了，阻塞函数要放到线程里"
    assert elapsed < 0.6, f"用时 {elapsed:.2f}s：5 个调用是一个接一个执行的（串行约 1.0s）"


async def _check_results_within():
    cancelled = []

    def make(name, seconds, value=None, error=None):
        async def job():
            try:
                await asyncio.sleep(seconds)
            except asyncio.CancelledError:
                cancelled.append(name)
                raise
            if error:
                raise error
            return value

        return job

    jobs = {
        "fast": make("fast", 0.05, "A"),
        "broken": make("broken", 0.08, error=ValueError("出错")),
        "medium": make("medium", 0.15, "B"),
        "slow": make("slow", 2.0, "C"),
    }
    t0 = time.perf_counter()
    result = await results_within(jobs, 0.3)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.6, f"用时 {elapsed:.2f}s：超时后应该立刻返回，不要等慢任务"
    assert result == {"fast": "A", "medium": "B"}, f"结果不对：{result}"
    if cancelled != ["slow"]:
        await asyncio.sleep(0.05)
        if cancelled == ["slow"]:
            raise AssertionError("调用了 cancel() 但没有等被取消的任务结束就返回了")
        raise AssertionError("超时没完成的任务没有被取消")

    t0 = time.perf_counter()
    result = await results_within({"x": make("x", 0.05, 1), "y": make("y", 0.1, 2)}, 1.0)
    elapsed = time.perf_counter() - t0
    assert result == {"x": 1, "y": 2}, f"结果不对：{result}"
    assert elapsed < 0.4, f"用时 {elapsed:.2f}s：所有任务完成后应该立即返回，不要等满 timeout"


async def _check_retry_async():
    import math

    def close_list(a, b):
        return len(a) == len(b) and all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(a, b))

    delays = []

    async def fake_sleep(seconds):
        delays.append(seconds)

    def flaky(fail_times, exc_type=ConnectionError):
        calls = 0

        async def func():
            nonlocal calls
            calls += 1
            if calls <= fail_times:
                raise exc_type(f"第 {calls} 次失败")
            return "ok"

        func.calls = lambda: calls
        return func

    f = flaky(2)
    result = await retry_async(f, max_attempts=5, base_delay=0.1, max_delay=10, sleep=fake_sleep, rand=lambda: 1.0)
    assert result == "ok", f"应该返回 'ok'，实际 {result!r}"
    assert f.calls() == 3, f"失败 2 次后第 3 次成功，应该调用 3 次，实际 {f.calls()} 次"
    assert close_list(delays, [0.1, 0.2]), f"退避间隔应该是 [0.1, 0.2]，实际 {delays}"

    delays.clear()
    f = flaky(100)
    try:
        await retry_async(f, max_attempts=4, base_delay=1, max_delay=3, sleep=fake_sleep, rand=lambda: 1.0)
        raise AssertionError("全部失败时应该抛出异常")
    except ConnectionError as e:
        assert str(e) == "第 4 次失败", f"应该抛出最后一次的异常，实际是 {e}"
    assert f.calls() == 4, f"应该尝试 4 次，实际 {f.calls()} 次"
    assert close_list(delays, [1, 2, 3]), f"间隔应该是 [1, 2, 3]（第三次被 max_delay 截断，最后一次失败后不等待），实际 {delays}"

    delays.clear()
    await retry_async(flaky(2), base_delay=0.2, sleep=fake_sleep, rand=lambda: 0.5)
    assert close_list(delays, [0.1, 0.2]), f"抖动后间隔应该是 [0.1, 0.2]（乘以 rand()），实际 {delays}"

    delays.clear()
    f = flaky(1, ValueError)
    try:
        await retry_async(f, retry_on=(ConnectionError,), sleep=fake_sleep)
        raise AssertionError("ValueError 不在 retry_on 里，应该直接抛出")
    except ValueError:
        pass
    assert f.calls() == 1 and delays == [], "不在 retry_on 里的异常不应该重试"

    async def hang():
        await asyncio.sleep(10)

    task = asyncio.create_task(retry_async(hang, max_attempts=3, base_delay=0.01))
    await asyncio.sleep(0.05)
    task.cancel()
    await asyncio.wait([task], timeout=0.3)
    if not task.done():
        for _ in range(5):
            task.cancel()
            await asyncio.wait([task], timeout=0.1)
        raise AssertionError("取消后任务还在运行：CancelledError 被当成普通失败重试了")
    assert task.cancelled(), "任务被取消后应该以 CancelledError 结束"


def _make_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://mock")


async def _check_fetch_json():
    seen = {}

    async def handler(request):
        seen[request.url.path] = request.extensions.get("timeout", {})
        path = request.url.path
        if path == "/ok":
            return httpx.Response(200, json={"model": "qwen", "ok": True})
        if path == "/missing":
            return httpx.Response(404, json={"error": "not found"})
        if path == "/boom":
            return httpx.Response(500, text="Internal Server Error")
        if path == "/slow":
            await asyncio.sleep(2)
            return httpx.Response(200, json={"late": True})
        if path == "/read-timeout":
            raise httpx.ReadTimeout("读超时", request=request)
        return httpx.Response(400)

    async with _make_client(handler) as client:
        assert await fetch_json(client, "/ok", timeout=1.5) == {"model": "qwen", "ok": True}
        assert seen["/ok"].get("read") == 1.5, "要把 timeout 传给 client.get"
        assert await fetch_json(client, "/missing") is None, "404 应该返回 None"
        try:
            await fetch_json(client, "/boom")
            raise AssertionError("500 应该抛出 httpx.HTTPStatusError")
        except httpx.HTTPStatusError as e:
            assert e.response.status_code == 500
        try:
            await fetch_json(client, "/bad")
            raise AssertionError("400 应该抛出 httpx.HTTPStatusError")
        except httpx.HTTPStatusError:
            pass

        t0 = time.perf_counter()
        try:
            await fetch_json(client, "/slow", timeout=0.2)
            raise AssertionError("服务端 2 秒才返回，timeout=0.2 时应该抛出 TimeoutError（用 asyncio.timeout）")
        except TimeoutError:
            pass
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.5, f"用时 {elapsed:.2f}s，没有在 timeout 附近返回"

        try:
            await fetch_json(client, "/read-timeout")
            raise AssertionError("httpx.ReadTimeout 应该转换成 TimeoutError")
        except TimeoutError:
            pass
        except httpx.TimeoutException:
            raise AssertionError("httpx.ReadTimeout 应该转换成内置的 TimeoutError")


async def _check_stream_deltas():
    def sse_body():
        text = (
            ": keep-alive\n"
            'data: {"delta": "你"}\n\n'
            "event: message\n"
            'data: {"delta": "好，"}\n\n'
            'data: {"delta": "世界"}\n\n'
            "data: [DONE]\n\n"
            'data: {"delta": "不应该出现"}\n\n'
        )
        raw = text.encode()
        cut = raw.index("你".encode()) + 1  # 故意从"你"字的 UTF-8 编码中间切开
        return [raw[:cut], raw[cut:40], raw[40:70], raw[70:]]

    async def body():
        for i, chunk in enumerate(sse_body()):
            if i >= 2:
                await asyncio.sleep(0.2)  # 后面的块来得慢
            yield chunk

    async def handler(request):
        if request.url.path == "/err":
            return httpx.Response(503, text="busy")
        return httpx.Response(200, content=body(), headers={"Content-Type": "text/event-stream"})

    async with _make_client(handler) as client:
        t0 = time.perf_counter()
        got = []
        first_at = None
        async for d in stream_deltas(client, "/chat"):
            if first_at is None:
                first_at = time.perf_counter() - t0
            got.append(d)
        assert got == ["你", "好，", "世界"], f"结果不对：{got}"
        assert first_at < 0.15, f"第一段文本在 {first_at:.2f}s 才拿到：没有边收边处理"

        try:
            async for _ in stream_deltas(client, "/err"):
                pass
            raise AssertionError("503 应该抛出 httpx.HTTPStatusError")
        except httpx.HTTPStatusError:
            pass


if __name__ == "__main__":
    import inspect

    checks = [
        ("练习 1 SafeAccount（P0-12）", _check_safe_account),
        ("练习 2 gather_limited（P0-13）", _check_gather_limited),
        ("练习 3 checksum_all（P0-13）", _check_checksum_all),
        ("练习 4 results_within（P0-13）", _check_results_within),
        ("练习 5 retry_async（P0-13）", _check_retry_async),
        ("练习 6 fetch_json（P0-14）", _check_fetch_json),
        ("练习 7 stream_deltas（P0-14）", _check_stream_deltas),
    ]

    class _Hang(Exception):
        pass

    async def _run_async(check):
        try:
            async with asyncio.timeout(5) as cm:  # 防止写错的实现卡住整个检查
                await check()
        except TimeoutError:
            if cm.expired():
                raise _Hang() from None
            raise

    passed = 0
    for title, check in checks:
        try:
            if inspect.iscoroutinefunction(check):
                asyncio.run(_run_async(check))
            else:
                check()
            print(f"✅ {title}")
            passed += 1
        except NotImplementedError:
            print(f"⏳ {title}：未完成")
        except AssertionError as e:
            print(f"❌ {title}：{e or '结果不正确'}")
        except _Hang:
            print(f"❌ {title}：超过 5 秒没有完成，可能卡住了（串行、阻塞或没处理超时）")
        except asyncio.CancelledError:
            print(f"❌ {title}：CancelledError 漏到了外面")
        except Exception as e:
            print(f"❌ {title}：运行出错 {type(e).__name__}: {e}")
    print(f"\n通过 {passed}/{len(checks)}")
