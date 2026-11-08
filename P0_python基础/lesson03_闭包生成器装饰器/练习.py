"""
第三课练习。补全每个函数，然后运行：python 练习.py
运行结果里每道题会显示 ✅ / ❌ / ⏳（未完成）。

规则：
- 只改函数体，不要改函数签名和下面的检查代码。
- 这是练习不是考试，可以回看 README 和示例，但不要让 AI 替你写。
- 可以用 functools 和 itertools，但练习 3 不能用 itertools.batched。
"""
import functools  # 练习 6 会用到 functools.wraps


# 练习 1（P0-04）
def make_counter(start=0, step=1):
    """返回一个计数函数（闭包）。第一次调用返回 start，之后每次比上一次多 step。
    不同的计数器互不影响。不能用全局变量，也不能用类。

    c = make_counter()
    c(), c(), c()     -> 0, 1, 2
    d = make_counter(10, 5)
    d(), d()          -> 10, 15
    c()               -> 3      （不受 d 影响）
    """
    raise NotImplementedError


# 练习 2（P0-04）
def make_multipliers(n):
    """返回一个长度为 n 的列表，第 i 个元素是函数 f(x) = i * x（i 从 0 开始）。
    提示：先写一个有晚绑定 bug 的版本，看看结果是什么，再修复。

    [f(10) for f in make_multipliers(4)] -> [0, 10, 20, 30]
    """
    raise NotImplementedError


# 练习 3（P0-07）
def chunked(iterable, size):
    """生成器：把 iterable 按 size 个一组切开，每次 yield 一个 list，最后一组可以不足 size 个。
    - iterable 可以是任何可迭代对象，包括生成器，所以不能用 len() 和切片。
    - 必须是惰性的：取第一组时，只能从输入里读出大约 size 个元素。
    - size 小于 1 时抛 ValueError（在第一次取值时抛出也可以）。

    list(chunked([1, 2, 3, 4, 5], 2)) -> [[1, 2], [3, 4], [5]]
    list(chunked(range(6), 3))         -> [[0, 1, 2], [3, 4, 5]]
    """
    raise NotImplementedError


# 练习 4（P0-07）
def stream_sentences(tokens):
    """生成器：把模型流式输出的 token 拼成完整的句子，每凑齐一句就 yield 一句。
    （真实场景：模型边生成，下游边把整句送去做语音合成。）
    - tokens 是一个可迭代对象，元素是字符串或 None。None 对应 chunk.choices[0].delta.content 为 None 的情况，跳过即可。
    - 遇到 "。！？!?" 中任意一个字符，一句结束，句子包含这个标点。一个 token 里可能有多个标点，也可能标点在中间。
    - 每句去掉首尾空白再 yield；去掉空白后是空字符串的不 yield。
    - 流结束时，缓冲区里剩下的不完整句子也要 yield（同样去掉首尾空白，空的不 yield）。
    - 必须是惰性的：凑齐一句就马上 yield，不能先把所有 token 读完。

    list(stream_sentences(["你", "好", "。", "今天", "不错！明", "天呢", "？", None, " 没有标点"]))
    -> ["你好。", "今天不错！", "明天呢？", "没有标点"]
    """
    raise NotImplementedError


# 练习 5（P0-07）
def flatten(nested):
    """生成器：把任意层嵌套的 list / tuple 展平，按原顺序 yield 每个元素。用 yield from 递归实现。
    只有 list 和 tuple 需要展开；其他类型（包括 str、dict）都当作一个元素原样 yield。
    不能修改输入。

    list(flatten([1, [2, [3, [4]]], (5, 6), "ab", []])) -> [1, 2, 3, 4, 5, 6, "ab"]
    """
    raise NotImplementedError


# 练习 6（P0-08）
def retry(times, exceptions=(Exception,)):
    """带参数的装饰器：被装饰的函数抛出 exceptions 里的异常时自动重试。
    - times 是最多调用的总次数（包含第一次）。times 小于 1 时，调用 retry(...) 本身就抛 ValueError。
    - exceptions 可以是一个异常类，也可以是异常类组成的 tuple。
    - 成功时返回函数的返回值；参数（包括关键字参数）要原样传给原函数。
    - 抛出的异常不在 exceptions 里：不重试，直接抛出。
    - 调用 times 次都失败：抛出最后一次的异常，不能吞掉后返回 None。
    - 用 functools.wraps 保留原函数的 __name__ 和 __doc__。
    - 不需要等待（不要 sleep）。

    @retry(3, (ConnectionError, TimeoutError))
    def call_llm(prompt): ...
    """
    raise NotImplementedError


# 练习 7（P0-08）
def tool(registry, name=None):
    """带参数的注册型装饰器：把函数登记到 registry（一个 dict）里，然后把原函数原样返回（不包装）。
    - 登记的键：name，不传 name 时用函数的 __name__。
    - 登记的值：{"func": 原函数, "description": 描述}。
      描述取 docstring 的第一行，去掉首尾空白；没有 docstring 时是空字符串 ""。
    - 同一个 registry 里名字已经存在时，抛 ValueError，并且不能覆盖原来登记的工具。

    registry = {}
    @tool(registry)
    def add(a, b):
        '''两数相加。'''
        return a + b
    registry -> {"add": {"func": add, "description": "两数相加。"}}
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 下面是检查代码，不要修改
# ---------------------------------------------------------------------------


def _is_iterator(obj):
    """生成器和迭代器的 __iter__ 返回自己；list 不是迭代器。"""
    return hasattr(obj, "__next__") and iter(obj) is obj


def _check_make_counter():
    c = make_counter()
    assert callable(c), "make_counter 应该返回一个函数"
    assert [c(), c(), c()] == [0, 1, 2]
    d = make_counter(10, 5)
    assert [d(), d()] == [10, 15]
    assert c() == 3, "两个计数器互相影响了（是不是用了全局变量？）"
    assert make_counter()() == 0, "新的计数器应该从 start 重新开始"
    assert getattr(c, "__closure__", None), "请用闭包实现：计数应该保存在外层函数的变量里"


def _check_make_multipliers():
    fs = make_multipliers(4)
    assert isinstance(fs, list) and len(fs) == 4, "应该返回长度为 n 的列表"
    assert [f(10) for f in fs] == [0, 10, 20, 30], "晚绑定：所有函数都用了循环结束时的 i"
    assert fs[3](7) == 21
    assert make_multipliers(0) == []


def _check_chunked():
    r = chunked([1, 2, 3, 4, 5], 2)
    assert _is_iterator(r), "chunked 应该是生成器（用 yield），而不是返回 list"
    assert list(r) == [[1, 2], [3, 4], [5]]
    assert list(chunked(range(6), 3)) == [[0, 1, 2], [3, 4, 5]], "整除时最后不能多出一个空列表"
    assert list(chunked([], 3)) == []
    assert list(chunked(iter(range(5)), 2)) == [[0, 1], [2, 3], [4]], "输入是迭代器时也要能用（不能用 len 和切片）"
    assert all(type(c) is list for c in chunked("abc", 2)), "每一组应该是 list"

    consumed = []

    def source():
        for i in range(1000):
            consumed.append(i)
            yield i

    assert next(chunked(source(), 3)) == [0, 1, 2]
    assert len(consumed) <= 4, f"没有做到惰性：只取第一组，却从输入读了 {len(consumed)} 个元素"

    try:
        list(chunked([1, 2], 0))
    except ValueError:
        pass
    else:
        raise AssertionError("size < 1 时应该抛 ValueError")


def _check_stream_sentences():
    tokens = ["你", "好", "。", "今天", "不错！明", "天呢", "？", None, " 没有标点"]
    r = stream_sentences(tokens)
    assert _is_iterator(r), "stream_sentences 应该是生成器（用 yield），而不是返回 list"
    assert list(r) == ["你好。", "今天不错！", "明天呢？", "没有标点"]
    assert list(stream_sentences(["Hello", " world", "! How", " are", " you", "?"])) == [
        "Hello world!",
        "How are you?",
    ], "句子首尾的空白要去掉"
    assert list(stream_sentences(["一。二。三"])) == ["一。", "二。", "三"], "一个 token 里有多个标点时要切成多句"
    assert list(stream_sentences([])) == []
    assert list(stream_sentences([None, "  ", None])) == [], "空白和 None 不应该产生句子"

    def stream():
        yield "第一句"
        yield "。第二"
        raise RuntimeError("读到了不该读的地方")

    gen = stream_sentences(stream())
    try:
        first = next(gen)
    except RuntimeError:
        raise AssertionError("没有做到惰性：第一句已经完整了，却还在继续读后面的 token") from None
    assert first == "第一句。"


def _check_flatten():
    data = [1, [2, [3, [4]]], (5, 6), "ab", [], {"k": 1}]
    r = flatten(data)
    assert _is_iterator(r), "flatten 应该是生成器（用 yield），而不是返回 list"
    assert list(r) == [1, 2, 3, 4, 5, 6, "ab", {"k": 1}], "str 和 dict 应该当作一个元素，不展开"
    assert data == [1, [2, [3, [4]]], (5, 6), "ab", [], {"k": 1}], "不能修改输入"
    assert list(flatten([])) == []
    assert list(flatten([[[[]]], ()])) == []
    deep = [0]
    for _ in range(100):
        deep = [deep]
    assert list(flatten(deep)) == [0], "多层嵌套没有完全展开"
    assert list(flatten(("a", ("b", ["c"])))) == ["a", "b", "c"]


def _check_retry():
    attempts = []

    @retry(3, (ConnectionError, TimeoutError))
    def flaky(x, *, y=0):
        """前两次超时，第三次成功。"""
        attempts.append(1)
        if len(attempts) < 3:
            raise TimeoutError(f"第 {len(attempts)} 次超时")
        return x + y

    assert attempts == [], "装饰时不应该调用原函数"
    assert flaky.__name__ == "flaky", "没有用 functools.wraps，__name__ 变了"
    assert flaky.__doc__ == "前两次超时，第三次成功。", "没有用 functools.wraps，__doc__ 丢了"
    assert flaky(1, y=2) == 3, "重试成功后应该返回原函数的返回值（检查参数有没有原样转发）"
    assert len(attempts) == 3

    attempts.clear()

    @retry(2, ConnectionError)
    def always_down():
        attempts.append(1)
        raise ConnectionError(f"第 {len(attempts)} 次失败")

    try:
        always_down()
    except ConnectionError as e:
        assert str(e) == "第 2 次失败", f"应该抛出最后一次的异常，实际抛出的是：{e}"
    else:
        raise AssertionError("一直失败时应该抛出异常，而不是返回")
    assert len(attempts) == 2, "times 是总调用次数（包含第一次）"

    attempts.clear()

    @retry(5, (ConnectionError,))
    def bad_args():
        attempts.append(1)
        raise ValueError("参数错误")

    try:
        bad_args()
    except ValueError:
        pass
    else:
        raise AssertionError("不在 exceptions 里的异常应该直接抛出")
    assert len(attempts) == 1, "不在 exceptions 里的异常不应该重试"

    attempts.clear()

    @retry(2)
    def default_exceptions():
        attempts.append(1)
        raise KeyError("k")

    try:
        default_exceptions()
    except KeyError:
        pass
    assert len(attempts) == 2, "默认应该重试所有 Exception"

    try:
        retry(0)
    except ValueError:
        pass
    else:
        raise AssertionError("times < 1 时调用 retry(...) 应该抛 ValueError")


def _check_tool():
    registry = {}

    @tool(registry)
    def add(a, b):
        """两数相加。

        更详细的说明不放进描述。
        """
        return a + b

    assert callable(add), "装饰器应该返回函数（是不是忘了 return func？）"
    assert add(1, 2) == 3
    assert list(registry) == ["add"]
    assert registry["add"]["func"] is add, "登记的应该是原函数本身"
    assert registry["add"]["description"] == "两数相加。", "描述应该是 docstring 的第一行，去掉首尾空白"

    def multiply(a, b):
        return a * b

    assert tool(registry, name="mul")(multiply) is multiply, "应该把原函数原样返回，不要包装"
    assert "mul" in registry and "multiply" not in registry, "传了 name 时应该用 name 登记"
    assert registry["mul"]["description"] == "", "没有 docstring 时描述应该是空字符串"

    try:

        @tool(registry)
        def add(x):  # noqa: F811  故意重名
            return x

    except ValueError:
        pass
    else:
        raise AssertionError("名字重复时应该抛 ValueError")
    assert registry["add"]["func"](1, 2) == 3, "名字重复时不能覆盖原来的工具"

    other = {}

    @tool(other)
    def ping():
        """检查连通性。"""
        return "pong"

    assert list(other) == ["ping"] and "ping" not in registry, "不同的 registry 应该互不影响"


if __name__ == "__main__":
    checks = [
        ("练习 1 make_counter", _check_make_counter),
        ("练习 2 make_multipliers", _check_make_multipliers),
        ("练习 3 chunked", _check_chunked),
        ("练习 4 stream_sentences", _check_stream_sentences),
        ("练习 5 flatten", _check_flatten),
        ("练习 6 retry", _check_retry),
        ("练习 7 tool", _check_tool),
    ]
    passed = 0
    for title, check in checks:
        try:
            check()
            print(f"✅ {title}")
            passed += 1
        except NotImplementedError:
            print(f"⏳ {title}：未完成")
        except AssertionError as e:
            print(f"❌ {title}：{e or '结果不正确'}")
        except Exception as e:
            print(f"❌ {title}：运行出错 {type(e).__name__}: {e}")
    print(f"\n通过 {passed}/{len(checks)}")
