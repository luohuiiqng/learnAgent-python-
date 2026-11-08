"""P0-08 装饰器。运行后对照输出读注释：python 03_装饰器.py"""
import functools
import inspect
import time


def section(title):
    print(f"\n===== {title} =====")


section("1. 函数是对象：可以当参数，也可以当返回值")


def shout(text):
    return text.upper() + "!"


def apply(func, value):  # 接收函数作为参数
    return func(value)


def make_prefixer(prefix):  # 返回一个函数（闭包，捕获了 prefix）
    def add_prefix(text):
        return prefix + text

    return add_prefix


print(apply(shout, "hello"))
print(make_prefixer(">> ")("hello"))

section("2. 手写装饰器，@ 等价于 f = deco(f)")


def log_calls(func):
    print(f"  [装饰时] 正在装饰 {func.__name__}")  # 只在装饰时执行一次

    def wrapper(*args, **kwargs):  # *args, **kwargs 接住任意参数
        print(f"  [调用时] 调用 {func.__name__}{args}")
        return func(*args, **kwargs)  # 原样转发，并返回原函数的结果

    return wrapper


def add(a, b):
    return a + b


add = log_calls(add)  # 手动装饰
print("手动装饰后 add(1, 2) =", add(1, 2))


@log_calls  # 这一行执行时就会打印 [装饰时]，还没有调用 mul
def mul(a, b):
    return a * b


print("定义完了，现在开始调用")
print("@ 装饰后 mul(3, 4) =", mul(3, 4))

section("3. 常见错误：wrapper 忘了 return")


def broken(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)  # 调用了，但没有 return 结果

    return wrapper


@broken
def get_answer():
    return 42


print("get_answer() =", get_answer())  # None

section("4. 不加 functools.wraps，会丢失 __name__ 和 __doc__")


def without_wraps(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def with_wraps(func):
    @functools.wraps(func)  # 把 func 的元信息复制到 wrapper 上
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@without_wraps
def search_a(query: str, top_k: int = 3):
    """在知识库里搜索。"""


@with_wraps
def search_b(query: str, top_k: int = 3):
    """在知识库里搜索。"""


print("不加 wraps: name =", search_a.__name__, " doc =", search_a.__doc__)
print("不加 wraps: 签名 =", inspect.signature(search_a))
print("加了 wraps: name =", search_b.__name__, " doc =", search_b.__doc__)
print("加了 wraps: 签名 =", inspect.signature(search_b))  # inspect 顺着 __wrapped__ 找到原函数
print("__wrapped__ 指向原函数:", search_b.__wrapped__.__name__)

section("5. 带参数的装饰器：三层嵌套")


def repeat(n):  # 第 1 层：接收装饰器参数
    def decorator(func):  # 第 2 层：接收被装饰的函数
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # 第 3 层：每次调用时执行
            return [func(*args, **kwargs) for _ in range(n)]

        return wrapper

    return decorator


@repeat(3)  # 等价于 greet = repeat(3)(greet)
def greet(name):
    return f"hi {name}"


print(greet("qt"))
print("repeat(3) 返回的是:", repeat(3).__name__)  # decorator，它才是真正的装饰器

section("6. 多个装饰器：从下往上装饰，从外往内调用")


def tag(name):
    def decorator(func):
        print(f"  [装饰时] {name} 包装 {func.__name__}")

        @functools.wraps(func)
        def wrapper():
            print(f"  [调用时] 进入 {name}")
            result = f"<{name}>{func()}</{name}>"
            print(f"  [调用时] 离开 {name}")
            return result

        return wrapper

    return decorator


@tag("b")  # 第二个装饰：拿到的是 i 包装过的函数
@tag("i")  # 第一个装饰：离 def 最近
def text():
    return "hello"


# 上面等价于 text = tag("b")(tag("i")(text))
print("结果:", text())

section("7. 实战：计时装饰器")


def timer(threshold):
    """超过 threshold 秒就打印警告。"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()  # 单调时钟，适合测时间间隔
            try:
                return func(*args, **kwargs)
            finally:  # 函数抛异常也要统计耗时
                elapsed = time.perf_counter() - start
                # 真实代码会打印 elapsed 的具体数值；这里只打印确定的比较结果，因为具体数值每次运行都不同
                print(f"  {func.__name__} 耗时是否超过 {threshold} 秒: {elapsed > threshold}")

        return wrapper

    return decorator


@timer(threshold=0.01)
def slow_task():
    time.sleep(0.02)  # sleep 至少会睡这么久，所以一定超过 0.01 秒
    return "完成"


@timer(threshold=1.0)
def fast_task():
    return "完成"


print("slow_task:", slow_task())
print("fast_task:", fast_task())

section("8. 实战：重试装饰器，只重试指定异常")


def retry(times, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)  # 成功就直接返回
                except exceptions as e:  # 只捕获指定的异常，其他异常直接往外抛
                    print(f"  第 {attempt} 次失败: {e!r}")
                    if attempt == times:
                        raise  # 最后一次也失败了，把异常抛出去，不能吞掉
                    # 真实项目里这里要 time.sleep(退避时间)，示例为了快不等待

        return wrapper

    return decorator


calls = {"n": 0}  # 用 dict 记录调用次数，函数里修改它不需要 global


@retry(times=3, exceptions=(ConnectionError, TimeoutError))
def call_llm(prompt):
    calls["n"] += 1
    if calls["n"] < 3:
        raise TimeoutError(f"第 {calls['n']} 次请求超时")
    return f"模型回答了: {prompt}"


print(call_llm("你好"))


@retry(times=3, exceptions=(ConnectionError,))
def bad_request():
    raise ValueError("参数错误")  # 不在重试列表里，第一次就直接抛出


try:
    bad_request()
except ValueError as e:
    print("ValueError 没有被重试，直接抛出:", e)


@retry(times=2, exceptions=(ConnectionError,))
def always_down():
    raise ConnectionError("服务不可用")


try:
    always_down()
except ConnectionError as e:
    print("重试 2 次后抛出最后一次的异常:", e)

section("9. 实战：functools.lru_cache")
fib_calls = {"n": 0}


def fib_plain(n):
    fib_calls["n"] += 1
    return n if n < 2 else fib_plain(n - 1) + fib_plain(n - 2)


@functools.lru_cache(maxsize=None)  # maxsize=None 表示不限大小，等价于 functools.cache
def fib_cached(n):
    fib_calls["n"] += 1
    return n if n < 2 else fib_cached(n - 1) + fib_cached(n - 2)


print("fib_plain(25) =", fib_plain(25), " 函数体执行次数:", fib_calls["n"])
fib_calls["n"] = 0
print("fib_cached(25) =", fib_cached(25), " 函数体执行次数:", fib_calls["n"])  # 每个 n 只算一次
print("cache_info:", fib_cached.cache_info())
fib_cached(25)  # 再调用一次，直接命中缓存
print("再调用一次后:", fib_cached.cache_info())


@functools.lru_cache(maxsize=128)
def total(values):
    return sum(values)


print("tuple 可哈希，可以缓存:", total((1, 2, 3)))
try:
    total([1, 2, 3])  # list 不可哈希，不能当缓存的 key
except TypeError as e:
    print("传 list 报 TypeError:", e)

section("10. 注册型装饰器：@tool 自动登记工具")
TOOLS = {}  # 工具名 -> {"description": ..., "func": ...}


def tool(func):
    TOOLS[func.__name__] = {
        "description": (func.__doc__ or "").strip(),  # 用 docstring 当工具描述，和 LangChain 的 @tool 思路一样
        "func": func,
    }
    return func  # 原样返回，不包装；忘了 return 的话，函数名会变成 None


@tool
def get_weather(city):
    """查询城市的天气。"""
    return f"{city}：晴，25 度"


@tool
def calculator(expression):
    """计算数学表达式。"""
    return str(eval(expression, {"__builtins__": {}}))  # 仅作演示，真实项目不要对模型输出用 eval


print("登记的工具:", {name: info["description"] for name, info in TOOLS.items()})
print("函数本身没变，还能直接调用:", get_weather("深圳"))

# 模型返回工具名和参数 dict，按名字查表调用（和第一课 call_tool 练习、ToolRegistry.execute 同一个思路）
tool_call = {"name": "calculator", "arguments": {"expression": "6 * 7"}}
func = TOOLS[tool_call["name"]]["func"]
print("按名字调用 calculator:", func(**tool_call["arguments"]))
# 对比 example_agents/FunctionCallingAgent/tools.py：那里要手动调用
# registry.register(name, description, parameters, func)，名字和描述要再写一遍
