"""P0-13 asyncio 基础。运行：python 02_asyncio基础.py

计时结果会浮动，看量级。
"""

import asyncio
import threading
import time


def section(title):
    print(f"\n===== {title} =====")


START = time.perf_counter()


def log(msg):
    """打印时带上从程序启动到现在的秒数，方便看出哪些事是同时发生的。"""
    print(f"  [{time.perf_counter() - START:5.2f}s] {msg}")


async def fake_llm(name, seconds):
    """模拟一次耗时的模型调用。await asyncio.sleep 期间，事件循环可以去跑别的协程。"""
    log(f"{name} 开始")
    await asyncio.sleep(seconds)
    log(f"{name} 结束")
    return f"{name} 的回答"


async def demo_coroutine_object():
    section("1. 调用协程函数只会得到一个协程对象，不会执行函数体")
    coro = fake_llm("qwen", 0.1)
    print("  fake_llm(...) 返回:", type(coro).__name__)
    print("  await 它才会真正执行:", await coro)


async def demo_await_vs_task():
    section("2. 直接 await 是串行；create_task 才是并发")
    t0 = time.perf_counter()
    a = await fake_llm("A", 0.3)  # 等 A 完全结束，才开始 B
    b = await fake_llm("B", 0.3)
    print(f"  直接 await 两次: {time.perf_counter() - t0:.2f}s  {a}, {b}")

    t0 = time.perf_counter()
    task_a = asyncio.create_task(fake_llm("A", 0.3))  # 立刻交给事件循环调度
    task_b = asyncio.create_task(fake_llm("B", 0.3))
    a = await task_a  # 等待期间 B 也在跑
    b = await task_b
    print(f"  create_task 后再 await: {time.perf_counter() - t0:.2f}s  {a}, {b}")


async def demo_gather():
    section("3. gather：并发运行，结果顺序和传入顺序一致")
    t0 = time.perf_counter()
    results = await asyncio.gather(
        fake_llm("慢模型", 0.3),
        fake_llm("快模型", 0.1),
    )
    print(f"  用时 {time.perf_counter() - t0:.2f}s，结果: {results}")

    async def broken():
        await asyncio.sleep(0.05)
        raise ValueError("工具调用失败")

    results = await asyncio.gather(fake_llm("正常", 0.1), broken(), return_exceptions=True)
    print("  return_exceptions=True 时异常作为结果返回:", results)


async def demo_taskgroup():
    section("4. TaskGroup（3.11+）：一个任务失败，其余任务会被取消")
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fake_llm("deepseek", 0.1))
        t2 = tg.create_task(fake_llm("qwen", 0.2))
    print("  离开 async with 时所有任务都已完成:", t1.result(), t2.result())

    async def failing():
        await asyncio.sleep(0.05)
        raise ConnectionError("连接断开")

    slow = None
    try:
        async with asyncio.TaskGroup() as tg:
            slow = tg.create_task(fake_llm("很慢的任务", 1.0))
            tg.create_task(failing())
    except* ConnectionError as eg:  # TaskGroup 把异常包装成 ExceptionGroup，用 except* 处理
        print("  捕获到:", eg.exceptions)
    print("  很慢的任务被取消了吗:", slow.cancelled())


async def heartbeat(stop):
    """每 0.1 秒打一次点。如果事件循环被卡住，这里就打不出来。"""
    ticks = 0
    while not stop.is_set():
        await asyncio.sleep(0.1)
        ticks += 1
    return ticks


async def demo_blocking():
    section("5. 在协程里调用阻塞函数会卡住整个事件循环")

    async def run_with_heartbeat(label, work):
        stop = asyncio.Event()
        hb = asyncio.create_task(heartbeat(stop))
        t0 = time.perf_counter()
        await work()
        elapsed = time.perf_counter() - t0
        stop.set()
        ticks = await hb
        print(f"  {label:<26} 用时 {elapsed:.2f}s，心跳 {ticks} 次（数值会浮动，看量级）")

    async def three_async_sleeps():
        await asyncio.gather(*(asyncio.sleep(0.5) for _ in range(3)))

    async def three_time_sleeps():
        async def bad():
            time.sleep(0.5)  # 阻塞调用：整个线程睡着，事件循环也跟着停住

        await asyncio.gather(*(bad() for _ in range(3)))

    async def three_to_thread():
        await asyncio.gather(*(asyncio.to_thread(time.sleep, 0.5) for _ in range(3)))

    await run_with_heartbeat("3 个 asyncio.sleep(0.5)", three_async_sleeps)
    await run_with_heartbeat("3 个 time.sleep(0.5)", three_time_sleeps)
    await run_with_heartbeat("3 个 to_thread(time.sleep)", three_to_thread)
    print("  time.sleep 版本：3 次睡眠排队执行，期间心跳停了")
    print("  to_thread 版本：阻塞函数放到线程池里跑，事件循环照常运转")
    print("  requests.get、读大文件、长时间的纯计算，在协程里都属于阻塞调用")


class FakeConnection:
    """async with 的对象要实现 __aenter__ / __aexit__，进入和退出时都可以 await。"""

    async def __aenter__(self):
        await asyncio.sleep(0.05)
        log("连接已建立")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await asyncio.sleep(0.05)
        log("连接已关闭")
        return False  # 不吞异常


async def fake_stream(text):
    """异步生成器：async def 里写 yield。模型流式输出就是这种形状。"""
    for ch in text:
        await asyncio.sleep(0.05)  # 模拟每个 token 之间的网络间隔
        yield ch


async def demo_async_with_for():
    section("6. async with 和 async for")
    async with FakeConnection():
        pieces = []
        async for token in fake_stream("你好，世界"):
            pieces.append(token)
            log(f"收到 token {token!r}")
    print("  拼接结果:", "".join(pieces))


async def demo_single_thread():
    section("7. 所有协程都在同一个线程里运行")
    names = set()

    async def where():
        await asyncio.sleep(0.01)
        names.add(threading.current_thread().name)

    await asyncio.gather(*(where() for _ in range(5)))
    print("  5 个协程运行所在的线程:", names)
    print("  对比 Qt：事件循环相当于 QEventLoop，await 相当于把控制权交回事件循环")


async def main():
    await demo_coroutine_object()
    await demo_await_vs_task()
    await demo_gather()
    await demo_taskgroup()
    await demo_blocking()
    await demo_async_with_for()
    await demo_single_thread()


if __name__ == "__main__":
    asyncio.run(main())  # 创建事件循环，运行 main()，结束后关闭循环
