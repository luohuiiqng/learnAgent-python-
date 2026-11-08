"""P0-13 asyncio 的超时、取消、并发限制。运行：python 03_超时取消与限流.py

计时结果会浮动，看量级。
"""

import asyncio
import time


def section(title):
    print(f"\n===== {title} =====")


async def slow_call(name, seconds):
    await asyncio.sleep(seconds)
    return f"{name} 完成"


async def demo_timeout():
    section("1. 超时：asyncio.timeout（3.11+）和 asyncio.wait_for")
    try:
        async with asyncio.timeout(0.2):  # 块里的代码超过 0.2 秒就被取消
            await slow_call("A", 1.0)
    except TimeoutError:  # 3.11 起 asyncio.TimeoutError 就是内置的 TimeoutError
        print("  asyncio.timeout: 超时，抛出 TimeoutError")

    try:
        await asyncio.wait_for(slow_call("B", 1.0), timeout=0.2)
    except TimeoutError:
        print("  wait_for: 超时，抛出 TimeoutError")

    print("  没超时的情况:", await asyncio.wait_for(slow_call("C", 0.05), timeout=0.2))


async def demo_cancel():
    section("2. 取消：CancelledError 会在 await 的位置抛出")

    async def worker():
        try:
            print("  worker: 开始等待")
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("  worker: 收到 CancelledError，做清理（比如关闭连接）")
            raise  # 清理完必须重新抛出
        finally:
            print("  worker: finally 也会执行")

    task = asyncio.create_task(worker())
    await asyncio.sleep(0.1)
    task.cancel()  # 只是"请求取消"，worker 要等到下一次被调度时才会收到异常
    try:
        await task
    except asyncio.CancelledError:
        print("  主协程: await 被取消的任务也会抛 CancelledError")
    print("  task.cancelled() =", task.cancelled())
    print("  CancelledError 是 Exception 的子类吗:", issubclass(asyncio.CancelledError, Exception))


async def demo_swallow():
    section("3. 吞掉 CancelledError 会让超时失效")

    async def bad_worker():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            return "假装正常完成"  # 错误：吞掉了取消

    t0 = time.perf_counter()
    try:
        async with asyncio.timeout(0.2):
            result = await bad_worker()
        print(f"  没有抛 TimeoutError，拿到了 {result!r}，用时 {time.perf_counter() - t0:.2f}s")
        print("  调用方以为请求成功了，其实结果是假的")
    except TimeoutError:
        print("  （不会走到这里）")
    print("  规则：捕获 CancelledError 只为了清理，清理完 raise；")
    print("  except Exception 不会捕获它，裸 except: 和 except BaseException 会")


async def demo_semaphore():
    section("4. Semaphore 限制同时运行的数量（防止被模型服务限流）")
    sem = asyncio.Semaphore(3)
    running = 0
    peak = 0

    async def call_model(i):
        nonlocal running, peak
        async with sem:  # 已经有 3 个在里面时，第 4 个在这里等
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.2)
            running -= 1
            return i

    t0 = time.perf_counter()
    results = await asyncio.gather(*(call_model(i) for i in range(10)))
    print(f"  10 个请求，上限 3：用时 {time.perf_counter() - t0:.2f}s，最多同时运行 {peak} 个")
    print("  结果:", results)
    print("  耗时约 4 轮 × 0.2s：前 3 个、再 3 个、再 3 个、最后 1 个（数值会浮动）")


async def demo_wait_partial():
    section("5. asyncio.wait：到点后拿走已完成的，取消没完成的")
    tasks = {
        name: asyncio.create_task(slow_call(name, s))
        for name, s in [("快", 0.05), ("中", 0.15), ("慢", 1.0)]
    }
    done, pending = await asyncio.wait(tasks.values(), timeout=0.3)
    print(f"  已完成 {len(done)} 个，未完成 {len(pending)} 个")
    for t in pending:
        t.cancel()
    await asyncio.gather(*pending, return_exceptions=True)  # 等被取消的任务真正结束
    for name, t in tasks.items():
        status = "已取消" if t.cancelled() else t.result()
        print(f"  {name}: {status}")
    print("  wait 不会抛 TimeoutError，也不会自动取消未完成的任务")


async def demo_fan_out():
    section("6. 综合：并发问多个模型，每个调用有超时，总并发有上限")
    sem = asyncio.Semaphore(2)
    latencies = {"deepseek": 0.2, "qwen": 0.1, "glm": 0.6, "kimi": 0.08, "ollama": 0.15}

    async def ask(model):
        async with sem:
            async with asyncio.timeout(0.3):  # 单次调用最多等 0.3 秒
                await asyncio.sleep(latencies[model])  # 模拟网络延迟
            return f"{model} 回答（{latencies[model]:.2f}s）"

    models = list(latencies)
    t0 = time.perf_counter()
    results = await asyncio.gather(*(ask(m) for m in models), return_exceptions=True)
    for m, r in zip(models, results):
        print(f"  {m:<9}", "超时" if isinstance(r, TimeoutError) else r)
    print(f"  总用时 {time.perf_counter() - t0:.2f}s（数值会浮动）")
    print("  return_exceptions=True：个别模型超时不影响拿到其他模型的结果")


async def main():
    await demo_timeout()
    await demo_cancel()
    await demo_swallow()
    await demo_semaphore()
    await demo_wait_partial()
    await demo_fan_out()


if __name__ == "__main__":
    asyncio.run(main())
