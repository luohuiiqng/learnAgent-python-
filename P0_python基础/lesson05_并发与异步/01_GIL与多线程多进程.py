"""P0-12 GIL、多线程与多进程。运行：python 01_GIL与多线程多进程.py

计时结果会随机器负载浮动，看量级和相对快慢，不要纠结具体数字。
"""

import dis
import multiprocessing
import os
import sys
import sysconfig
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

# 注意：在 macOS 上，ProcessPoolExecutor 的每个子进程启动时都会重新导入本文件。
# 所以模块顶层只放函数定义，真正要执行的代码全部放进 main()，由文件末尾的
# if __name__ == "__main__" 保护起来。


def section(title):
    print(f"\n===== {title} =====")


def cpu_task(n):
    """纯 Python 的计算，整个过程都要持有 GIL。"""
    total = 0
    for i in range(n):
        total += i * i
    return total


def io_task(seconds):
    """time.sleep 期间会释放 GIL，相当于在等网络或磁盘。"""
    time.sleep(seconds)
    return seconds


def whoami(_):
    """在子进程里返回进程号和本模块的 __name__。sleep 是为了让两个子进程都分到任务。"""
    time.sleep(0.1)
    return os.getpid(), __name__


def timed(label, func):
    start = time.perf_counter()
    result = func()
    print(f"  {label:<22} 用时 {time.perf_counter() - start:.2f}s")
    return result


def show_gil_status():
    section("0. 当前解释器是否带 GIL")
    print("  Python 版本:", sys.version.split()[0])
    # Py_GIL_DISABLED 为 1 表示这是无 GIL 的自由线程构建（3.13 起提供，实验性）
    print("  Py_GIL_DISABLED =", sysconfig.get_config_var("Py_GIL_DISABLED"))
    if hasattr(sys, "_is_gil_enabled"):  # 3.13 新增
        print("  sys._is_gil_enabled() =", sys._is_gil_enabled())
    print("  线程切换间隔 sys.getswitchinterval() =", sys.getswitchinterval(), "秒")


def compare_cpu_bound():
    section("1. CPU 密集：多线程几乎不加速，多进程加速（数值会浮动，看量级）")
    n, jobs = 3_000_000, 4
    print(f"  任务：{jobs} 个 cpu_task({n:,})，CPU 核数 {os.cpu_count()}")

    timed("串行", lambda: [cpu_task(n) for _ in range(jobs)])
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        timed("4 个线程", lambda: list(pool.map(cpu_task, [n] * jobs)))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        pool.submit(cpu_task, 1).result()  # 先让子进程启动起来，不把启动时间算进去
        timed("4 个进程", lambda: list(pool.map(cpu_task, [n] * jobs)))
    print("  线程版和串行差不多：同一时刻只有一个线程能执行 Python 字节码")
    print("  进程版明显更快：每个进程有自己的解释器和自己的 GIL")


def compare_io_bound():
    section("2. IO 密集：多线程能加速（数值会浮动，看量级）")
    jobs, seconds = 8, 0.2
    print(f"  任务：{jobs} 个 io_task({seconds})")
    timed("串行", lambda: [io_task(seconds) for _ in range(jobs)])
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        timed("8 个线程", lambda: list(pool.map(io_task, [seconds] * jobs)))
    print("  等待期间线程会释放 GIL，8 个等待可以重叠，总时间接近一次等待")


counter = 0


def one():
    return 1


def add_plain(n):
    global counter
    for _ in range(n):
        counter += 1


def add_with_call(n):
    global counter
    for _ in range(n):
        counter += one()  # 读出 counter 之后、写回之前，调用了一个 Python 函数


def run_threads(target, n_threads, n_per_thread):
    global counter
    counter = 0
    threads = [threading.Thread(target=target, args=(n_per_thread,)) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:  # 先全部 start，再逐个 join
        t.join()
    return counter


def show_race():
    section("3. 有 GIL 不等于线程安全：counter += 1 不是原子操作")
    print("  counter += 1 编译出的字节码（读、加、写是分开的几步）：")
    for ins in dis.get_instructions(add_plain):
        if "counter" in ins.argrepr or ins.opname in ("LOAD_CONST", "BINARY_OP"):
            print(f"    {ins.opname:<14} {ins.argrepr}")
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-5)  # 临时调小切换间隔，线程切换更频繁，问题更容易出现
    expected = 4 * 200_000
    print(f"  期望结果 {expected}，下面每种写法跑 3 次：")
    print("  counter += 1     :", [run_threads(add_plain, 4, 200_000) for _ in range(3)])
    print("  counter += one() :", [run_threads(add_with_call, 4, 200_000) for _ in range(3)])
    print("  第一行在当前版本上通常不丢，这是解释器在哪些位置切换线程的实现细节，不是保证")
    print("  第二行在读和写之间多了一次函数调用，线程会在中间被切走，结果小于期望值")

    lock = threading.Lock()

    def add_locked(n):
        global counter
        for _ in range(n):
            with lock:  # 相当于 std::lock_guard<std::mutex> / QMutexLocker
                counter += one()

    print("  加锁后            :", [run_threads(add_locked, 4, 200_000) for _ in range(3)])
    sys.setswitchinterval(old_interval)


def show_futures():
    section("4. concurrent.futures：submit / as_completed / 异常传递")
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(io_task, s): s for s in (0.3, 0.1, 0.2)}
        print("  as_completed 按完成顺序返回：", [f.result() for f in as_completed(futures)])
        print("  map 按提交顺序返回：      ", list(pool.map(io_task, (0.3, 0.1, 0.2))))

        bad = pool.submit(int, "不是数字")
        try:
            bad.result()  # 子线程里的异常在调用 result() 时重新抛出
        except ValueError as e:
            print("  result() 重新抛出了子线程的异常:", e)
    print("  离开 with 时会调用 shutdown(wait=True)，等所有任务结束")


def show_spawn():
    section("5. macOS 默认用 spawn 启动子进程")
    print("  当前启动方式:", multiprocessing.get_start_method())
    print("  主进程 pid:", os.getpid(), " __name__ =", repr(__name__))
    with ProcessPoolExecutor(max_workers=2) as pool:
        for pid, name in sorted(set(pool.map(whoami, range(4)))):
            print(f"  子进程 pid: {pid}  __name__ = {name!r}")
    print("  子进程重新导入了本文件，但 __name__ 是 '__mp_main__'，")
    print("  所以 if __name__ == '__main__' 里的代码不会在子进程里再跑一遍")

    try:
        with ProcessPoolExecutor(max_workers=1) as pool:
            pool.submit(lambda x: x * 2, 21).result()
    except Exception as e:
        print("  lambda 不能交给进程池（函数和参数都要 pickle 序列化后发给子进程）")
        print(f"    {type(e).__name__}: {e}")


def main():
    show_gil_status()
    compare_cpu_bound()
    compare_io_bound()
    show_race()
    show_futures()
    show_spawn()


if __name__ == "__main__":
    main()
