"""P0-07 迭代器与生成器。运行后对照输出读注释：python 02_迭代器与生成器.py"""
import sys
import time
from contextlib import contextmanager
from itertools import batched, chain, count, islice, takewhile
from types import SimpleNamespace


def section(title):
    print(f"\n===== {title} =====")


section("1. 可迭代对象 vs 迭代器")
nums = [10, 20]
it = iter(nums)  # 调用 nums.__iter__()，得到一个新的迭代器
print("list 是迭代器吗（iter(x) is x）:", iter(nums) is nums)  # False：每次 iter 都得到新对象
print("迭代器是迭代器吗:", iter(it) is it)  # True：迭代器的 __iter__ 返回自己
print("next:", next(it))  # 调用 it.__next__()
print("next:", next(it))
try:
    next(it)  # 没有元素了
except StopIteration:
    print("没有元素时抛 StopIteration，相当于 C++ 里走到了 end()")

section("2. for 循环背后发生了什么")
it = iter(["a", "b", "c"])  # 1. 取迭代器
while True:
    try:
        x = next(it)  # 2. 取下一个
    except StopIteration:  # 3. 结束
        break
    print("  手写 for 循环拿到:", x)

section("3. 手写一个迭代器类：实现 __iter__ 和 __next__")


class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self  # 迭代器的 __iter__ 返回自己

    def __next__(self):
        if self.current <= 0:
            raise StopIteration  # 用异常表示结束
        value = self.current
        self.current -= 1
        return value


cd = Countdown(3)
print("第一次遍历:", list(cd))
print("第二次遍历:", list(cd))  # 空的：迭代器走到头就废了，不会自动重置

section("4. 生成器函数：调用时不执行函数体")


def countdown(n):
    print("  [生成器] 开始执行")
    while n > 0:
        print(f"  [生成器] 准备 yield {n}")
        yield n  # 交出 n，在这里暂停
        print(f"  [生成器] 从 yield {n} 之后继续")
        n -= 1
    print("  [生成器] 函数体结束，接下来自动抛 StopIteration")


g = countdown(2)
print("调用 countdown(2) 之后，还没有任何 [生成器] 输出。类型:", type(g).__name__)
print("生成器就是迭代器:", iter(g) is g)
print("第一次 next 得到:", next(g))
print("第二次 next 得到:", next(g))
print("用 for 取剩下的（一个都没有了）:", [v for v in g])

section("5. 惰性求值与内存")
n = 10**6
as_list = [x * x for x in range(n)]  # 立刻算完 100 万个
as_gen = (x * x for x in range(n))  # 什么都还没算
list_mb = sys.getsizeof(as_list) / 1024 / 1024  # 只算列表本身（存指针的数组），不含元素对象
gen_bytes = sys.getsizeof(as_gen)
print("列表本身超过 7 MB:", list_mb > 7)  # 约 8 MB，具体数值随 Python 版本略有不同
print("生成器对象小于 1 KB:", gen_bytes < 1024)  # 约 200 字节，和 n 无关
print("两者求和结果相同:", sum(as_list) == sum(as_gen))
del as_list

section("6. 无限序列：只能用惰性的方式表示")


def naturals():
    n = 0
    while True:  # 永远不结束，如果返回 list 会把内存耗尽
        yield n
        n += 1


print("前 5 个自然数:", list(islice(naturals(), 5)))  # islice 只取需要的部分

section("7. 生成器表达式：() 代替 []")
words = ["qt", "python", "agent", "llm"]
print("总长度:", sum(len(w) for w in words))  # 唯一参数时括号可以省略


def noisy_words():
    for w in words:
        print(f"  检查 {w}")
        yield w


print("有超过 5 个字母的词吗:", any(len(w) > 5 for w in noisy_words()))  # 找到 python 就停，后面不再检查

section("8. 陷阱：生成器只能遍历一次")
squares = (x * x for x in range(4))
print("第一次 list:", list(squares))
print("第二次 list:", list(squares))  # 空的，而且不报错


def describe(data):
    return f"max={max(data)}"  # 消耗了 data


squares = (x * x for x in range(4))
print(describe(squares))
try:
    min(squares)  # 生成器已经被 max 用完了
except ValueError as e:
    print("再 min 一次 ValueError:", e)

squares = (x * x for x in range(4))
print("4 in squares:", 4 in squares)  # in 会一直往后找，消耗掉 0、1、4
print("剩下的:", list(squares))

section("9. 需要多次遍历：可迭代类的 __iter__ 写成生成器")


class Squares:
    def __init__(self, n):
        self.n = n

    def __iter__(self):  # 每次 for/list 都会调用 __iter__，得到一个新的生成器
        for x in range(self.n):
            yield x * x


sq = Squares(4)
print("第一次:", list(sq))
print("第二次:", list(sq))  # 不是空的，这和 range、list 的行为一样

section("10. yield from：委托给子迭代器")


def two_parts():
    yield from [1, 2]  # 等价于 for x in [1, 2]: yield x
    yield from "ab"


print("two_parts:", list(two_parts()))


def flatten(items):
    for x in items:
        if isinstance(x, list):
            yield from flatten(x)  # 递归：子生成器产生的每个值都直接交给调用方
        else:
            yield x


print("flatten:", list(flatten([1, [2, [3, [4]]], 5])))


def sub():
    yield "子生成器的值"
    return "子生成器的 return 值"  # 放在 StopIteration.value 里


def main_gen():
    result = yield from sub()  # yield from 表达式的值就是子生成器的 return 值
    yield f"拿到: {result}"


print("yield from 的返回值:", list(main_gen()))

section("11. itertools 常用函数")
print("count(10, 5) 前 3 个:", list(islice(count(10, 5), 3)))
print("islice(range(10), 2, 8, 2):", list(islice(range(10), 2, 8, 2)))  # start, stop, step
print("chain([1, 2], 'ab'):", list(chain([1, 2], "ab")))
print("chain.from_iterable 展开一层:", list(chain.from_iterable([[1, 2], [3], []])))
print("takewhile x < 3:", list(takewhile(lambda x: x < 3, count())))  # count() 是无限的，靠 takewhile 停下
print("batched('abcde', 2):", list(batched("abcde", 2)))  # Python 3.12 新增，每组是 tuple

section("12. 用生成器写上下文管理器：@contextmanager")


class OpenedByClass:  # 第二课的写法
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print(f"  [类] 打开 {self.name}")
        return self.name

    def __exit__(self, exc_type, exc, tb):
        print(f"  [类] 关闭 {self.name}，异常类型: {exc_type.__name__ if exc_type else None}")
        return False  # 不吞异常


@contextmanager
def opened(name):
    print(f"  [生成器] 打开 {name}")  # yield 之前 = __enter__
    try:
        yield name  # yield 的值给 as；with 块在这里执行
    except ValueError as e:
        print(f"  [生成器] 在 yield 处收到异常: {e!r}")
        raise  # 重新抛出，不吞异常；不写 raise 就等于吞掉
    finally:
        print(f"  [生成器] 关闭 {name}")  # yield 之后 = __exit__，写在 finally 里保证执行


with OpenedByClass("文件A") as res:
    print("  with 块里拿到:", res)

with opened("文件B") as res:
    print("  with 块里拿到:", res)

try:
    with opened("文件C"):
        raise ValueError("with 块里出错了")
except ValueError:
    print("  异常最终传到了 with 外面，而且关闭代码执行了")


@contextmanager
def opened_without_finally(name):
    print(f"  [没写 finally] 打开 {name}")
    yield name
    print(f"  [没写 finally] 关闭 {name}")  # with 块抛异常时，这一行不会执行


try:
    with opened_without_finally("文件D"):
        raise ValueError("出错")
except ValueError:
    print("  看上面：文件D 没有被关闭")

section("13. 联系大模型：模拟流式输出")


def fake_stream(text):
    """模拟 OpenAI SDK stream=True 返回的对象：逐块产生 chunk，结构和 chunk.choices[0].delta.content 一致。"""
    yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))])  # 第一块通常只有角色，没有内容
    for i in range(0, len(text), 3):  # 每 3 个字符一块，真实的切法由模型决定
        time.sleep(0.02)  # 模拟网络延迟，只影响显示速度，不影响输出内容
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text[i : i + 3]))])
    yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))])  # 最后一块也没有内容


def iter_text(stream):
    """管道第一步：从 chunk 里取出文本，跳过 None。"""
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


stream = fake_stream("生成器适合处理流式输出。下游不用等全部生成完！")
parts = []
print("逐块显示: ", end="")
for piece in iter_text(stream):
    print(piece, end="|", flush=True)  # 用 | 标出每块的边界；真实场景用 end=""
    parts.append(piece)
print()
print("拼接后的完整回答:", "".join(parts))
print("再遍历一次 stream:", list(iter_text(stream)))  # 空的：和 SDK 的 Stream 一样只能读一次
