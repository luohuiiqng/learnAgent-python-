# 第五课：并发与异步（GIL、asyncio、HTTP 调用）

**覆盖知识点**：P0-12 GIL、多线程与多进程 ★、P0-13 asyncio ★、P0-14 HTTP 调用
**预计用时**：6 到 7 小时

## 学习步骤

1. 按顺序读下面三节。每节读完，运行对应的示例文件，对照输出读代码注释：

   ```bash
   cd P0_python基础/lesson05_并发与异步
   python 01_GIL与多线程多进程.py     # 第 1 节
   python 02_asyncio基础.py           # 第 2 节
   python 03_超时取消与限流.py         # 第 2 节
   python 04_HTTP调用.py              # 第 3 节
   ```

   用 `python`，不要用 `python3`。每个脚本 10 秒内跑完，全部离线运行。
   示例里的耗时每次运行都会浮动，看量级和相对快慢，不要纠结具体数字。

2. 遇到和预期不一样的输出，先改代码验证猜想。比如把 Semaphore 的上限从 3 改成 1，看总耗时怎么变。
3. 完成 `练习.py` 里的 7 道题，运行 `python 练习.py`，直到全部通过。
4. 告诉教练“第五课学完了”，开始评估：L1 口述、L2 预测输出、L3 闭卷编码。

---

## 1. GIL、多线程与多进程（P0-12）

### 1.1 先对照 C++/Qt

| C++ / Qt | Python | 说明 |
|---|---|---|
| `std::thread` / `QThread` | `threading.Thread(target=f, args=(...))` | `start()` 启动，`join()` 等待结束 |
| `std::mutex` / `QMutex` | `threading.Lock()` | |
| `std::lock_guard` / `QMutexLocker` | `with lock:` | 离开 `with` 自动解锁，异常时也会解锁 |
| `QThreadPool` / `QtConcurrent::run` | `ThreadPoolExecutor` | 线程池 |
| `std::future` / `QFuture` | `concurrent.futures.Future` | `result()` 等待并取结果 |
| 多个进程 + IPC | `multiprocessing` / `ProcessPoolExecutor` | 函数和数据通过 pickle 序列化后在进程间传递 |

最大的区别：C++ 里 4 个线程做计算，能同时用满 4 个核；CPython（官方解释器，默认构建）里不行，原因是 GIL。

另外两点不同：

- Python 没有强制终止线程的 API（没有 `QThread::terminate` 这样的东西）。想让线程停下，只能让它自己检查一个标志后退出。
- `daemon=True` 的线程在程序退出时被直接停止，它打开的文件、数据库事务等资源可能没有被正确释放。

### 1.2 GIL 是什么，为什么存在

GIL（Global Interpreter Lock，全局解释器锁）是 CPython 里的一把全局锁：**同一时刻，一个进程里只有一个线程能执行 Python 字节码**。

为什么需要它：第一课讲过，CPython 用引用计数管理内存，每个对象上都有一个计数器，赋值、传参、离开作用域时都会加减。如果两个线程同时修改同一个对象的引用计数，计数会出错，导致对象被提前释放或永远不释放。给每个对象单独加锁开销很大，CPython 选择用一把大锁保护整个解释器。这样做的好处是单线程程序快、C 扩展好写，代价是多线程不能并行执行 Python 代码。

GIL 什么时候释放：

- 线程做阻塞 IO 时（读写文件、socket 收发、`time.sleep`）会释放 GIL，其他线程可以运行。
- 持有 GIL 的线程运行一段时间后会被要求让出，这个间隔由 `sys.getswitchinterval()` 决定，默认 0.005 秒。
- 很多 C 扩展（例如 NumPy 的部分运算、`hashlib` 处理大块数据）在计算期间主动释放 GIL。

### 1.3 对 IO 密集和 CPU 密集任务的影响

`01_GIL与多线程多进程.py` 在这台机器（8 核）上的一次运行结果：

| 任务 | 串行 | 多线程 | 多进程 |
|---|---|---|---|
| CPU 密集：4 个纯 Python 循环 | 0.47s | 0.45s（4 线程） | 0.19s（4 进程） |
| IO 密集：8 次 `time.sleep(0.2)` | 1.63s | 0.21s（8 线程） | 没测 |

- **CPU 密集**（纯 Python 计算）：多线程几乎不加速，因为线程轮流持有 GIL，同一时刻只有一个在算。多进程能加速，因为每个进程有自己的解释器和自己的 GIL。
- **IO 密集**（等网络、等磁盘）：多线程能加速，因为等待期间 GIL 已经释放，多个等待可以重叠。

大模型应用开发的大部分工作是 IO 密集的：调用模型 API、查数据库、请求向量库，时间都花在等网络上。所以这类代码通常用线程或协程（第 2 节），很少需要多进程。

### 1.4 有 GIL 不等于你的代码线程安全

GIL 保护的是解释器自己的数据结构，不保护你的业务逻辑。`counter += 1` 会编译成几条字节码：

```text
LOAD_GLOBAL   counter    # 读
LOAD_CONST    1
BINARY_OP     +=         # 加
STORE_GLOBAL  counter    # 写
```

线程可能在“读”之后、“写”之前被切走。另一个线程读到同一个旧值，两次加法只生效一次，这和 C++ 里两个线程同时 `++` 一个普通 `int` 是同一类问题。

示例第 3 节的实测（为了让问题更容易出现，示例临时用 `sys.setswitchinterval` 把切换间隔调小了）：

- 简单的 `counter += 1`，在当前版本上跑几次通常不丢。这是解释器在哪些位置切换线程的实现细节，语言不保证它是原子的。
- `counter += one()`，读和写之间多了一次函数调用，结果明显小于期望值（4 个线程各加 20 万次，期望 80 万，实测约 30 万）。
- 加锁后结果每次都正确。

正确做法：多个线程读写同一份数据时加锁，锁要包住整个“读、计算、写”过程。

```python
lock = threading.Lock()

def add(n):
    global counter
    for _ in range(n):
        with lock:
            counter += 1
```

`queue.Queue` 是线程安全的队列，线程之间传数据优先用它，比自己加锁更不容易写错。

### 1.5 threading 的基本用法

```python
threads = [threading.Thread(target=work, args=(1000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:      # 先全部 start，再逐个 join
    t.join()
```

常见错误是在同一个循环里 `start()` 完马上 `join()`，这样线程是一个接一个跑的，没有并发。

### 1.6 concurrent.futures：线程池和进程池

`ThreadPoolExecutor` 和 `ProcessPoolExecutor` 的接口相同，切换时只改类名：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(download, urls))          # 结果顺序和 urls 一致
    futures = [pool.submit(download, u) for u in urls]
    for f in as_completed(futures):                   # 谁先完成先拿谁
        print(f.result())                             # 子线程的异常在这里重新抛出
```

| 写法 | 说明 |
|---|---|
| `pool.submit(f, *args)` | 提交一个任务，返回 `Future` |
| `future.result(timeout=None)` | 等待结果；任务里的异常在这里重新抛出 |
| `pool.map(f, items)` | 批量提交，按提交顺序返回结果 |
| `as_completed(futures)` | 按完成顺序遍历 |
| `with ... as pool:` | 退出时调用 `shutdown(wait=True)`，等所有任务结束 |

线程池默认的 `max_workers` 是 `min(32, CPU 核数 + 4)`，进程池默认等于 CPU 核数。

### 1.7 multiprocessing 与 spawn：必须写 `if __name__ == "__main__"`

启动子进程有几种方式：

| 方式 | 做法 | 默认用于 |
|---|---|---|
| `spawn` | 启动一个全新的解释器，重新导入主模块 | macOS（3.8 起）、Windows |
| `fork` | 复制当前进程 | Linux（3.13 及以前） |

你的 Mac 上默认是 `spawn`。子进程会**重新导入你的主文件**，只是这时 `__name__` 是 `'__mp_main__'` 而不是 `'__main__'`（示例第 5 节打印了这一点）。所以：

- 模块顶层的代码会在每个子进程里再执行一遍。
- 如果在顶层直接创建进程池，子进程导入时又会去创建进程池。实测结果：子进程打印 `RuntimeError`，提示要用 `if __name__ == '__main__'`；主进程这边抛出 `BrokenProcessPool`。
- 解决办法：要执行的代码全部放进 `if __name__ == "__main__":` 里，顶层只放函数和类的定义。

```python
def cpu_task(n): ...

if __name__ == "__main__":
    with ProcessPoolExecutor() as pool:
        print(list(pool.map(cpu_task, [10**7] * 4)))
```

多进程的其他限制：

- 函数和参数要用 pickle 序列化后发给子进程。lambda 和函数内部定义的函数不能 pickle，要用模块顶层定义的函数。
- 在 Jupyter 里直接定义的函数，通常也没法交给 `ProcessPoolExecutor`，因为子进程导入不到它。
- 进程启动和数据传输都有开销，任务太小时多进程反而更慢。

### 1.8 自由线程构建（PEP 703）

从 Python 3.13 开始，官方提供一个实验性的无 GIL 构建（free-threaded build），需要单独安装。默认构建仍然有 GIL。你现在用的就是默认构建，可以这样确认：

```python
import sys
print(sys._is_gil_enabled())   # 3.13 新增，你的环境输出 True
```

即使在无 GIL 构建里，1.4 节的数据竞争问题依然存在，该加的锁一样要加。

### 1.9 怎么选

| 场景 | 选择 |
|---|---|
| 并发调用 API、读写网络（IO 密集） | asyncio（第 2 节）；代码是同步的就用线程池 |
| 纯 Python 的大量计算（CPU 密集） | 进程池 |
| 计算在 NumPy、PyTorch 等 C 扩展里 | 通常线程就够，这些库计算时会释放 GIL，具体看库的文档 |

### 面试怎么问

1. GIL 是什么？CPython 为什么需要它？
2. 有了 GIL，多线程程序还需要加锁吗？举个例子。
3. IO 密集和 CPU 密集的任务分别用线程还是进程？为什么？
4. 在 macOS 上使用多进程，为什么必须写 `if __name__ == "__main__"`？

---

## 2. asyncio（P0-13）

### 2.1 对照 QEventLoop

你在 Qt 里已经用过事件循环：主线程跑 `QEventLoop`，网络请求发出去后立刻返回，结果到了再通过信号触发槽函数。整个过程只有一个线程，靠“不阻塞、等结果时把控制权还给事件循环”来同时处理很多事。

asyncio 是同一个模型，只是写法不同：

| Qt | asyncio |
|---|---|
| `QEventLoop`，一个线程 | 事件循环，一个线程 |
| 发起异步请求，连接 `finished` 信号到槽函数 | `result = await client.get(url)`，等待点之后的代码就是“槽函数” |
| 槽函数里做耗时操作会卡住界面 | 协程里调用阻塞函数会卡住所有协程 |
| `QTimer::singleShot` | `await asyncio.sleep(秒数)` |

Qt 的回调写法会把一段逻辑拆进多个槽函数。`await` 让你按顺序写代码，执行到 `await` 时当前协程暂停，事件循环去运行其他协程，等待的结果到了再从暂停处继续。

协程之间不会被抢占：两个 `await` 之间的代码不会被其他协程打断。所以单纯的 `counter += 1` 在协程里不需要锁。但如果“读”和“写”之间有 `await`，其他协程可能在这期间修改数据，问题和线程一样。

### 2.2 协程、async/await、asyncio.run

```python
import asyncio

async def ask(model):            # async def 定义协程函数
    await asyncio.sleep(1)       # await 只能写在 async def 里
    return f"{model} 的回答"

async def main():
    print(await ask("qwen"))

asyncio.run(main())              # 程序入口：创建事件循环，运行 main()，结束后关闭
```

- 调用 `ask("qwen")` 不会执行函数体，只返回一个协程对象。必须 `await` 它，或者交给 `create_task`，它才会运行。忘了 `await` 时，Python 会给出 `RuntimeWarning: coroutine ... was never awaited`。
- `asyncio.run()` 一般在程序入口调用一次。在已经有事件循环运行的地方（例如 Jupyter 里）不能调用它，这时直接写 `await main()`。
- 能被 `await` 的对象叫 awaitable：协程、Task、Future。

### 2.3 直接 await 和 create_task 的区别

```python
a = await ask("A")    # 等 A 完全结束
b = await ask("B")    # 才开始 B，共 2 秒

task_a = asyncio.create_task(ask("A"))   # 立刻交给事件循环调度，开始运行
task_b = asyncio.create_task(ask("B"))
a = await task_a       # 等 A 期间，B 也在运行
b = await task_b       # 共 1 秒
```

直接 `await` 一个协程是串行执行，`create_task` 才能让多个协程同时推进。常见错误是在循环里逐个 `await`，以为在并发，其实是串行。

`create_task` 返回的 Task 要保存引用（存进变量或列表）。事件循环只持有 Task 的弱引用，没人引用的 Task 可能在执行中途被垃圾回收。

### 2.4 gather 和 TaskGroup

```python
results = await asyncio.gather(ask("A"), ask("B"), ask("C"))   # 结果顺序和传入顺序一致
```

| | `asyncio.gather` | `asyncio.TaskGroup`（3.11+） |
|---|---|---|
| 写法 | `await gather(c1, c2)` | `async with TaskGroup() as tg: tg.create_task(c1)` |
| 结果 | 返回列表，顺序和传入顺序一致 | 退出 `async with` 后调用 `task.result()` |
| 某个任务出错 | 第一个异常抛给调用方，**其他任务不会被取消，继续运行** | 取消其余任务，异常包装成 `ExceptionGroup` |
| 收集所有异常 | `return_exceptions=True`，异常作为结果返回 | 用 `except* 异常类型` 处理 |

选择：需要“一个失败就全部停下”时用 TaskGroup；需要“个别失败不影响其他结果”（例如同时问 5 个模型，有一个超时也要拿到其余 4 个）时用 `gather(..., return_exceptions=True)`。

### 2.5 超时

```python
try:
    async with asyncio.timeout(10):             # 3.11+，块里的代码超时会被取消
        result = await call_model()
except TimeoutError:
    ...

result = await asyncio.wait_for(call_model(), timeout=10)   # 只包一个 awaitable
```

两者超时后都会先取消正在等待的操作，再抛出 `TimeoutError`。3.11 起 `asyncio.TimeoutError` 就是内置的 `TimeoutError`。

如果超时后还想要已完成的部分结果，用 `asyncio.wait`：

```python
done, pending = await asyncio.wait(tasks, timeout=2)   # 不抛异常，返回两个集合
for t in pending:
    t.cancel()          # wait 不会自动取消未完成的任务
```

### 2.6 取消：不要吞掉 CancelledError

`task.cancel()` 会在任务当前暂停的 `await` 处抛出 `asyncio.CancelledError`。超时、TaskGroup 取消其他任务、程序退出，底层都是这个机制。

```python
async def worker():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        await conn.close()   # 只做清理
        raise                # 必须重新抛出
```

- `CancelledError` 继承自 `BaseException`，不是 `Exception`。所以 `except Exception` 不会误捕获它；裸 `except:` 和 `except BaseException` 会。
- 吞掉它（捕获后不再抛出）会破坏取消机制。示例 `03_超时取消与限流.py` 第 3 节演示了：`asyncio.timeout` 到点了，却没有抛 `TimeoutError`，调用方拿到一个假的“成功”结果。
- 清理代码优先写在 `finally` 里，这样不需要捕获 `CancelledError`。

### 2.7 Semaphore 限制并发数

模型服务都有限流（每分钟请求数、同时连接数）。一次 `gather` 1000 个请求，很快会收到 429。用 `Semaphore` 控制同时进行的请求数：

```python
sem = asyncio.Semaphore(5)

async def limited_call(prompt):
    async with sem:              # 已经有 5 个在里面时，后来的在这里等
        return await call_model(prompt)

results = await asyncio.gather(*(limited_call(p) for p in prompts))
```

`Semaphore` 对应 C++20 的 `std::counting_semaphore` 或 Qt 的 `QSemaphore`，区别是等待时让出的是事件循环，不是阻塞线程。

### 2.8 async with 和 async for

| 语法 | 需要的方法 | 典型用途 |
|---|---|---|
| `async with x:` | `__aenter__` / `__aexit__`（都是协程） | 打开和关闭连接：`async with httpx.AsyncClient() as client` |
| `async for item in x:` | `__aiter__` / `__anext__` | 逐块读取流式响应：`async for line in r.aiter_lines()` |

在 `async def` 里写 `yield`，就得到一个异步生成器，可以用 `async for` 遍历。第三课的生成器能做流式输出，异步生成器是它在 asyncio 里的版本，模型的流式输出通常就包装成这种形式。

### 2.9 阻塞调用会卡住整个事件循环

事件循环只有一个线程。协程里一旦调用阻塞函数，这个线程就停在那里，其他所有协程都停住。示例 `02_asyncio基础.py` 第 5 节的一次实测（同时有一个每 0.1 秒打一次点的心跳协程）：

| 写法 | 用时 | 心跳次数 |
|---|---|---|
| 3 个 `await asyncio.sleep(0.5)` 并发 | 0.50s | 5 |
| 3 个 `time.sleep(0.5)` | 1.51s | 1 |
| 3 个 `await asyncio.to_thread(time.sleep, 0.5)` 并发 | 0.51s | 6 |

常见的阻塞调用：`time.sleep`、`requests.get`、同步的数据库驱动、读大文件、长时间的纯 Python 计算。

处理办法：

- 有异步版本就用异步版本：`asyncio.sleep`、`httpx.AsyncClient`、异步数据库驱动。
- 没有异步版本（比如某个只有同步接口的 SDK），用 `await asyncio.to_thread(func, *args)` 放到线程池里执行。
- CPU 密集的计算放进进程池：`await loop.run_in_executor(process_pool, func, *args)`。
- 开发时可以用 `asyncio.run(main(), debug=True)`，执行超过 0.1 秒的回调会被记录到日志。

注意：线程无法被取消。`to_thread` 外面的协程被取消或超时后，线程里的函数仍会继续运行到结束。

### 2.10 协程和线程怎么选

| | 线程 | 协程 |
|---|---|---|
| 切换方式 | 操作系统抢占，任何位置都可能切走 | 只在 `await` 处切换 |
| 数据竞争 | 任何共享数据都要考虑加锁 | 两个 `await` 之间的代码不会被打断 |
| 单个开销 | 每个线程有自己的栈，几百上千个就很重 | 一个协程是一个小对象，上万个也没问题 |
| 库的要求 | 普通同步库都能用 | 要用支持 async 的库，否则会卡住循环 |
| 取消 | 不能强制终止 | `task.cancel()`，配合超时使用 |
| 适合 | 已有的同步代码、少量并发 | 大量并发的网络 IO，比如 Agent 并发调用模型和工具 |

FastAPI 和 OpenAI 的 Python SDK 都支持 async。大模型应用的服务端需要同时处理大量等待网络的请求，通常用 asyncio 来写。

### 2.11 联系大模型应用

- 一个 Agent 同时调用多个工具，或者同时问多个模型做对比：`gather` 或 `TaskGroup`。
- 批量处理几千条数据：`Semaphore` 限制并发，避免被限流。
- 每次模型调用设超时，超时的结果丢弃或重试：`asyncio.timeout`。
- 用户关闭页面时取消正在生成的请求：取消机制，清理后重新抛出 `CancelledError`。

### 面试怎么问

1. 协程和线程有什么区别？各适合什么场景？
2. `create_task` 和直接 `await` 有什么区别？`gather` 和 `TaskGroup` 呢？
3. 在 `async def` 里调用 `time.sleep` 或 `requests.get` 会发生什么？怎么解决？
4. 并发调用模型 API 时，怎么限制并发数、设置超时？取消任务时要注意什么？

---

## 3. HTTP 调用（P0-14）

### 3.1 requests 和 httpx

| | requests | httpx |
|---|---|---|
| 同步 | `requests.get(...)` | `httpx.get(...)` |
| 异步 | 不支持 | `httpx.AsyncClient` |
| 复用连接 | `requests.Session()` | `httpx.Client()` / `httpx.AsyncClient()` |
| 默认超时 | **没有**，不传 `timeout` 可能一直等下去 | 5 秒 |
| 重定向 | 默认跟随 | 默认不跟随，需要 `follow_redirects=True` |
| `raise_for_status()` | 4xx、5xx 时抛 `requests.HTTPError` | 非 2xx 时抛 `httpx.HTTPStatusError` |

两者接口很像。asyncio 代码里只能用 httpx（或其他异步库），在协程里调用 `requests` 会卡住事件循环。OpenAI 的 Python SDK 底层用的就是 httpx。

### 3.2 超时一定要设

```python
requests.get(url, timeout=(3, 30))          # (连接超时, 读超时)
httpx.get(url, timeout=10)                  # 连接、读、写、等连接池都是 10 秒
httpx.Client(timeout=httpx.Timeout(10, connect=3))
```

不设超时，服务端不响应时程序会一直挂着。

要注意，requests 和 httpx 的读超时都是**两次收到数据之间**的最长间隔，不是整个请求的总时间。服务端每 5 秒发一个字节，30 秒的读超时永远不会触发。需要限制总耗时，就在外面再套一层 `asyncio.timeout`。

### 3.3 状态码和 raise_for_status

| 状态码 | 含义 | 是否适合重试 |
|---|---|---|
| 200 | 成功 | |
| 400 | 请求参数错误 | 否，改请求 |
| 401 / 403 | 没认证 / 没权限（API Key 错误） | 否 |
| 404 | 资源不存在 | 否 |
| 429 | 请求太频繁，被限流 | 是，等一会儿；响应头 `Retry-After` 可能给出建议的等待时间 |
| 500 / 502 / 503 / 504 | 服务端错误、网关错误、服务不可用、网关超时 | 是 |

收到 4xx、5xx 时，requests 和 httpx 都**不会自动抛异常**，`r.json()` 可能解析出一个错误信息，你的代码却当成正常结果继续往下走。拿到响应后先检查状态码，或者调用 `r.raise_for_status()`。

### 3.4 JSON 请求和响应

```python
r = client.post("/chat", json={"message": "你好"})   # 自动序列化，并设置 Content-Type: application/json
r.raise_for_status()
data = r.json()                                      # 解析响应体
```

`json=` 和 `data=` 不同：`data=` 发送的是表单格式。

### 3.5 复用 Client（连接池）

```python
with httpx.Client(base_url="https://api.example.com", timeout=10) as client:
    for q in questions:
        client.post("/chat", json={"q": q})

async with httpx.AsyncClient(timeout=10) as client:
    results = await asyncio.gather(*(client.get(u) for u in urls))
```

`httpx.get()` 这样的顶层函数每次调用都新建连接，用完就关。`Client` 内部有连接池，同一个服务器的连接可以复用，省掉每次建立 TCP 连接和 TLS 握手的时间。一个程序里通常创建一个 Client 并一直使用，用完关闭（用 `with` / `async with`）。

### 3.6 流式读取响应

模型的流式输出是服务端一边生成一边发送。客户端要边收边处理，不能等全部收完：

```python
# 同步
with client.stream("POST", "/chat", json=payload) as r:
    r.raise_for_status()
    for line in r.iter_lines():
        ...

# 异步
async with client.stream("POST", "/chat", json=payload) as r:
    r.raise_for_status()
    async for line in r.aiter_lines():
        ...

# requests
with requests.post(url, json=payload, stream=True, timeout=30) as r:
    for line in r.iter_lines(decode_unicode=True):
        ...
```

`client.stream(...)` 收到响应头就返回，响应体在遍历时才逐块读取。`iter_lines` / `aiter_lines` 会处理跨块的行和跨块的多字节 UTF-8 字符。自己用 `aiter_bytes()` 逐块 `decode()`，遇到一个汉字被拆在两块里就会出错。

模型 API 的流式响应通常是 SSE 格式，每条数据一行 `data: {...}`，用空行分隔，最后可能是 `data: [DONE]`。下一课细讲 SSE。

### 3.7 重试与指数退避

网络请求一定会偶尔失败。只重试临时性的错误：

- 连接错误、超时（httpx 里是 `httpx.TransportError` 及其子类，包括 `httpx.TimeoutException`）；
- 状态码 429、500、502、503、504。

400、401、403、404 重试也没用，应该直接报错。

两次重试之间要等待，而且等待时间要逐次增加（指数退避），还要加随机抖动：

```python
delay = min(max_delay, base_delay * 2 ** (attempt - 1))   # 0.5, 1, 2, 4 ... 不超过 max_delay
delay = random.uniform(0, delay)                         # 全抖动：在 0 到 delay 之间随机取
await asyncio.sleep(delay)
```

- 指数增长：服务端过载时，越来越长的间隔给它恢复的时间。
- 上限 `max_delay`：防止等待时间无限增长。
- 抖动：服务出故障时，成千上万个客户端会在同一时刻失败。没有抖动，它们会在同一时刻一起重试，再次把服务压垮。

POST 请求重试前要想清楚是否会产生重复操作。调用模型接口重试一般没问题，但每次请求都可能计费。

### 3.8 本机代理问题

你的机器开了系统代理 `127.0.0.1:8080`。在这台机器上实测：

- httpx 默认会读取系统代理设置，访问 `localhost` 或 `127.0.0.1` 时请求也被转给代理，返回 503；
- requests 访问本机地址时没有被拦截，但不同环境、不同代理软件的表现不一样，不要依赖这一点。

访问本机服务（例如以后本地跑的 Ollama、自己写的 FastAPI 服务）返回 503 时，用下面任意一种办法：

```bash
export NO_PROXY=localhost,127.0.0.1    # 在终端里设置，对 httpx 和 requests 都有效
```

```python
httpx.Client(trust_env=False)   # 不读取环境变量和系统的代理设置
session = requests.Session()
session.trust_env = False
```

`04_HTTP调用.py` 第 1 节会打印 httpx 默认设置下的状态码，你可以亲眼看到这个 503。

### 3.9 用 MockTransport 离线测试

`httpx.MockTransport(handler)` 把网络层换成一个函数：handler 收到 `httpx.Request`，返回 `httpx.Response`，请求不会离开本进程。写测试和练习时用它模拟各种服务端行为：

```python
def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/boom":
        return httpx.Response(500)
    return httpx.Response(200, json={"ok": True})

client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://mock")
```

- handler 可以是 `async def`，在里面 `await asyncio.sleep(...)` 模拟慢响应。
- `httpx.Response(200, content=异步生成器)` 可以模拟流式响应。
- handler 里 `raise httpx.ConnectError(...)` 可以模拟网络错误。
- MockTransport **不执行** httpx 的 `timeout` 参数，超时由真实的网络层负责。示例第 4 节演示了：传了 `timeout=0.1`，仍然等了 1 秒。要在测试里验证超时逻辑，用 `asyncio.timeout`。

---

## 读完后的自查

下面的问题能不看资料答出来，再开始做练习：

1. 4 个线程同时跑纯 Python 计算，为什么不比串行快？换成 4 个线程同时下载网页呢？
2. `counter += 1` 为什么可能丢更新？加锁时锁要包住哪一段？
3. `a = await f(); b = await g()` 和 `a, b = await asyncio.gather(f(), g())` 的执行过程有什么区别？
4. 捕获 `CancelledError` 后为什么必须重新抛出？吞掉它会发生什么？
5. 用 httpx 调用模型接口，可能出现哪几类失败？哪些应该重试，重试间隔怎么算？
