# 第三课：作用域与闭包、迭代器与生成器、装饰器

**覆盖知识点**：P0-04 作用域与闭包、P0-07 迭代器与生成器 ★、P0-08 装饰器 ★
**预计用时**：5 到 6 小时

## 学习步骤

1. 按顺序读下面三节。每节读完，运行对应的示例文件，对照输出读代码注释：

   ```bash
   cd P0_python基础/lesson03_闭包生成器装饰器
   python 01_作用域与闭包.py
   python 02_迭代器与生成器.py
   python 03_装饰器.py
   ```

   用 `python`，不要用 `python3`。你电脑上的 `python3` 是另一个没装依赖的版本。

2. 遇到和你预期不一样的输出，先自己改代码验证猜想。比如在生成器里多加几行 `print`，看它什么时候真正执行。
3. 完成 `练习.py` 里的 7 道题，运行 `python 练习.py`，直到全部通过。
4. 告诉教练“第三课学完了”，开始评估：L1 口述、L2 预测输出、L3 闭卷编码。

这三个知识点是连在一起的：闭包是装饰器的基础，生成器又能通过 `@contextmanager` 这个装饰器变成上下文管理器。建议按顺序学，不要跳。

---

## 1. 作用域与闭包（P0-04）

### 1.1 LEGB：Python 按四层查找名字

在函数里用到一个名字时，Python 按下面的顺序查找，找到就停：

| 层 | 含义 | 例子 |
|---|---|---|
| L（Local） | 当前函数内部 | 函数里赋值的变量、函数参数 |
| E（Enclosing） | 外层函数（函数嵌套时） | `outer` 里定义的变量，`inner` 能读到 |
| G（Global） | 当前模块（.py 文件）顶层 | 文件顶层定义的变量、函数、import 的模块 |
| B（Builtins） | 内置名字 | `len`、`print`、`list`、`Exception` |

四层都找不到，抛 `NameError`。

和 C++ 的区别：

- **Python 没有块作用域。** 只有函数、类、模块（以及推导式）会创建作用域。`if`、`for`、`while`、`with`、`try` 都不会。`for i in range(3)` 结束后 `i` 还在，值是 2。C++ 里 `for (int i...)` 的 `i` 出了循环就没了。
- **内置名字可以被覆盖。** `list = [1, 2]` 之后，当前作用域里的 `list` 就不是内置类型了，再调用 `list(...)` 会报 `TypeError`。变量名不要用 `list`、`dict`、`str`、`id`、`type`、`input` 这些。
- **类体不算 E 层。** 方法里不能直接用类属性的名字，要写 `self.x` 或 `类名.x`。

### 1.2 赋值决定一个名字是不是局部变量

Python 在**编译函数时**就决定每个名字属于哪一层：只要函数体里**任何位置**对某个名字赋值（包括 `=`、`+=`、`for x in`、`import`、`def`），这个名字在整个函数里都是局部变量。

```python
count = 0
def bad():
    count += 1     # count 是局部变量，但还没赋值就读了
bad()              # UnboundLocalError
```

C++ 程序员容易以为"先读全局的 count，再写一个局部的"。Python 不会这样做，一个名字在一个函数里只能属于一层。

### 1.3 global 和 nonlocal

要在函数里**重新绑定**外层的名字，需要声明：

| 声明 | 作用 |
|---|---|
| `global x` | 这个函数里的 `x` 指模块顶层的 `x` |
| `nonlocal x` | 这个函数里的 `x` 指最近一层外层函数里的 `x`（必须已经存在，否则 `SyntaxError`） |

注意，只有**重新绑定**（`x = ...`、`x += 1`）才需要声明。如果只是修改可变对象（`items.append(1)`、`d["k"] = 1`），名字本身没有变，不需要声明。这和第一课讲的"修改对象"和"重新赋值"是同一件事。

`global` 在业务代码里尽量少用，它让函数依赖隐藏的全局状态，难测试。`nonlocal` 主要用在闭包里。

### 1.4 闭包：函数带着它用到的外层变量

```python
def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

c = make_counter()
c(), c()           # 1, 2
```

`make_counter` 返回之后，它的局部变量 `count` 按理说该销毁了，但 `counter` 还在用它。Python 会把 `count` 放进一个 cell 对象里，`counter` 持有这个 cell。函数加上它捕获的这些变量，就叫**闭包**。可以用 `c.__closure__[0].cell_contents` 看到里面的值。

对照 C++ lambda：

| | C++ `[=]` 按值捕获 | C++ `[&]` 按引用捕获 | Python 闭包 |
|---|---|---|---|
| 捕获的是 | 创建 lambda 那一刻的值的副本 | 外层变量本身 | 外层变量本身（cell） |
| 外层之后改了变量 | 看不到 | 看得到 | 看得到 |
| 外层函数返回后 | 安全 | 悬空引用，未定义行为 | 安全，cell 由引用计数保活 |

一句话：**Python 闭包捕获的是变量，不是值**。行为像 C++ 的 `[&]`，但不会悬空。

### 1.5 晚绑定陷阱：循环里创建函数

```python
funcs = [lambda: i for i in range(3)]
[f() for f in funcs]    # [2, 2, 2]，不是 [0, 1, 2]
```

三个 lambda 捕获的是**同一个变量 `i`**。调用时才去读 `i`，此时循环已经结束，`i` 是 2。这叫晚绑定（late binding）。如果是 C++ 的 `[=]`，会得到 0、1、2。

三种修复方法：

```python
# 1. 默认参数：默认值在 def/lambda 执行时求值（第一课讲过），相当于把当时的值复制一份
funcs = [lambda i=i: i for i in range(3)]

# 2. 工厂函数：每次调用 make 都创建一个新的作用域，里面有一个新的 i
def make(i):
    return lambda: i
funcs = [make(i) for i in range(3)]

# 3. functools.partial：把参数值提前绑定进去
from functools import partial
funcs = [partial(lambda i: i, i) for i in range(3)]
```

方法 1 最常见，但有个副作用：调用方可以传参覆盖 `i`。方法 2 最清楚。这个陷阱在面试里常和第一课 3.3 节的"默认参数陷阱"一起问，两者正好相反：默认参数是**定义时**求值，闭包变量是**调用时**读取。

---

## 2. 迭代器与生成器（P0-07）★

### 2.1 可迭代对象和迭代器

| 概念 | 要实现的方法 | 例子 | C++ 类比 |
|---|---|---|---|
| 可迭代对象（iterable） | `__iter__()`，返回一个迭代器 | `list`、`dict`、`str`、`range`、文件对象 | 有 `begin()`/`end()` 的容器 |
| 迭代器（iterator） | `__next__()` 返回下一个元素，没有了就抛 `StopIteration`；`__iter__()` 返回自己 | `iter([1, 2])` 的返回值、生成器、文件对象 | 迭代器本身 |

内置函数 `iter(x)` 调用 `x.__iter__()`，`next(it)` 调用 `it.__next__()`。如果类没有 `__iter__` 但有 `__getitem__`，`iter()` 会退回到从下标 0 开始逐个调用 `__getitem__`，直到 `IndexError`。新代码应该实现 `__iter__`。

和 C++ 的区别：

- **C++ 用一对迭代器表示范围**，通过 `it != end` 判断结束。Python 只有一个迭代器对象，**用抛 `StopIteration` 异常表示结束**。
- **Python 迭代器只能往前走，走完就废了**，不能复制、不能回退、不能重置。最接近 C++ 的 input iterator（比如 `std::istream_iterator`）。
- **容器和迭代器是两个对象。** `list` 是可迭代对象但不是迭代器，每次 `iter(lst)` 都得到一个新的迭代器，所以 list 可以反复遍历。迭代器的 `__iter__` 返回自己，所以迭代器只能遍历一次。

### 2.2 for 循环背后发生了什么

```python
for x in obj:
    body(x)
```

等价于：

```python
it = iter(obj)            # 1. 取迭代器，相当于 C++ range-for 里的 begin()
while True:
    try:
        x = next(it)      # 2. 取下一个元素
    except StopIteration: # 3. 没有元素了，结束循环
        break
    body(x)
```

`for`、`list(...)`、`sum(...)`、`in`、解包 `a, b = ...`、`"".join(...)` 都走这套协议。所以自己写的类只要实现了 `__iter__`，就能直接用在这些地方。

### 2.3 生成器函数：用 yield 写迭代器

手写迭代器类要维护状态、写 `__next__`、记得抛 `StopIteration`，比较啰嗦。生成器函数可以做同样的事：

```python
def countdown(n):
    while n > 0:
        yield n        # 交出一个值，然后在这里暂停
        n -= 1
                       # 函数结束时自动抛 StopIteration

g = countdown(3)       # 这一行不执行函数体，只创建生成器对象
next(g)                # 3：从头执行到第一个 yield
next(g)                # 2：从上次暂停的地方继续，执行到下一个 yield
list(g)                # [1]：把剩下的取完
```

关键点：

- 函数体里只要出现 `yield`，它就是生成器函数。**调用它不会执行函数体**，只返回一个生成器对象。
- 生成器对象就是迭代器：`iter(g) is g` 为 `True`。
- 每次 `next()` 执行到下一个 `yield` 暂停，局部变量都保留着。可以理解成一个能暂停的函数，C++20 的协程（C++23 的 `std::generator`）是同一个思路。
- 生成器里的 `return x` 表示结束，`x` 会放在 `StopIteration.value` 里，`for` 循环拿不到它，一般不用。

### 2.4 惰性求值与内存

| 写法 | 什么时候计算 | 内存 |
|---|---|---|
| `[x * x for x in range(10**6)]` | 立刻算完全部 100 万个 | 列表本身约 8 MB（每个元素一个 8 字节指针），还不算元素对象 |
| `(x * x for x in range(10**6))` | 每次 `next` 算一个 | 生成器对象只有约 200 字节，和数据量无关 |

惰性的好处：

- **内存不随数据量增长。** 逐行读几 GB 的日志文件、逐条处理数据库结果，都应该用迭代的方式。
- **可以表示无限序列。** `itertools.count()` 永远不会结束，配合 `islice` 只取需要的部分。
- **可以边产生边消费。** 下游不用等上游全部算完。大模型流式输出就是这样（见 2.9）。

代价：只能遍历一次、不能用 `len()` 和下标、调试时看不到全部内容。数据不大且需要反复使用时，用列表更简单。

### 2.5 生成器表达式

把列表推导式的 `[]` 换成 `()` 就是生成器表达式。作为函数唯一的参数时，括号可以省略：

```python
total = sum(x * x for x in nums)            # 不创建中间列表
has_error = any("ERROR" in line for line in lines)   # 找到第一个就停止
```

### 2.6 陷阱：生成器只能遍历一次

```python
squares = (x * x for x in range(3))
list(squares)    # [0, 1, 4]
list(squares)    # []，不报错，静默返回空
```

第二次遍历**不会报错**，只是什么都没有，所以这类 bug 很难发现。常见场景：

- 把生成器传给一个函数，函数里先 `max(data)` 再 `min(data)`，第二次拿到的是空的（`min` 对空序列会报 `ValueError`）。
- 先用 `x in gen` 判断，`in` 会消耗掉找到 `x` 之前的所有元素。
- 调试时 `print(list(gen))` 看了一眼，后面的代码就拿不到数据了。

解决方法：需要多次遍历就先 `list(gen)` 转成列表；或者每次重新调用生成器函数；或者写一个可迭代类，它的 `__iter__` 写成生成器函数，这样每次 `for` 都会得到一个新的生成器。

### 2.7 yield from

`yield from 子迭代器` 把子迭代器的每个值依次交出去，相当于：

```python
for item in 子迭代器:
    yield item
```

常用于把工作委托给另一个生成器，特别是递归：

```python
def flatten(items):
    for x in items:
        if isinstance(x, list):
            yield from flatten(x)    # 递归展开，子生成器产生的值直接交给调用方
        else:
            yield x
```

`yield from` 表达式的值是子生成器 `return` 的值。它还会把调用方的 `send()`、`throw()` 转发给子生成器，这些在写协程时才用到，这里不展开。

### 2.8 itertools 常用函数

`itertools` 里的函数都返回迭代器，都是惰性的：

| 函数 | 作用 | 例子 |
|---|---|---|
| `count(start=0, step=1)` | 无限计数 | `count(10, 5)` → 10, 15, 20, ... |
| `islice(it, stop)` / `islice(it, start, stop[, step])` | 对迭代器切片（不支持负数） | `islice(count(), 3)` → 0, 1, 2 |
| `chain(a, b, ...)` | 把多个可迭代对象首尾相连 | `chain([1, 2], "ab")` → 1, 2, 'a', 'b' |
| `chain.from_iterable(x)` | 同上，参数是一个"可迭代对象的可迭代对象" | 展开一层嵌套 |
| `takewhile(pred, it)` | 条件为真时一直取，第一次为假就停 | `takewhile(lambda x: x < 3, count())` → 0, 1, 2 |
| `batched(it, n)` | 每 n 个打成一个 tuple（Python 3.12 新增） | `batched("abcde", 2)` → ('a','b'), ('c','d'), ('e',) |

`islice` 是迭代器的切片：生成器不支持 `g[:3]`，要写 `islice(g, 3)`。

### 2.9 用生成器写上下文管理器：contextlib.contextmanager

第二课用类写上下文管理器，要定义 `__enter__` 和 `__exit__`。`contextlib.contextmanager` 可以用一个生成器函数代替：

```python
from contextlib import contextmanager

@contextmanager
def opened(name):
    print("打开", name)            # 相当于 __enter__ 的内容
    try:
        yield name                 # yield 的值就是 as 后面拿到的值，with 块在这里执行
    finally:
        print("关闭", name)        # 相当于 __exit__ 的内容

with opened("db") as conn:
    ...
```

对照第二课的类写法：

| | 类写法 | `@contextmanager` 写法 |
|---|---|---|
| 进入 | `__enter__` 的返回值给 `as` | `yield` 之前的代码，`yield` 的值给 `as` |
| 退出 | `__exit__(exc_type, exc, tb)` | `yield` 之后的代码 |
| with 块里抛了异常 | 作为参数传给 `__exit__` | 在 `yield` 那一行重新抛出 |
| 吞掉异常 | `__exit__` 返回 `True` | 在生成器里 `except` 住，不再抛出 |

坑：**`yield` 外面一定要包 `try/finally`**。不写的话，with 块里一旦抛异常，异常会在 `yield` 处抛出，`yield` 后面的清理代码就不会执行。另外，生成器必须**正好 yield 一次**。

适合场景：逻辑简单、不需要保存额外状态的上下文管理器，比如计时、临时切换目录、临时修改配置。需要复杂状态或要复用的，用类写更清楚。

### 2.10 联系大模型：流式输出就是迭代

调用大模型时传 `stream=True`，模型生成一点就返回一点，用户不用等整段回答生成完。OpenAI Python SDK 里，这时返回的是一个可迭代的 `Stream` 对象，每次迭代得到一个 chunk：

```python
stream = client.chat.completions.create(model=..., messages=..., stream=True)
parts = []
for chunk in stream:                      # 走的就是 2.2 节的迭代器协议
    if not chunk.choices:                 # 某些 chunk（例如开启用量统计时的最后一块）没有 choices
        continue
    delta = chunk.choices[0].delta.content
    if delta:                             # 第一块和最后一块的 content 可能是 None
        print(delta, end="", flush=True)  # 逐块显示
        parts.append(delta)
full_text = "".join(parts)                # 下游自己拼出完整回答
```

几点和本节内容直接相关：

- `Stream` 背后是一次 HTTP 响应，**只能遍历一次**，读完就没有了。要保存完整内容，必须在遍历时自己收集。
- 字符串拼接用 `parts.append` 再 `"".join(parts)`，不要在循环里 `text += delta`。
- 实际项目里常把流处理写成一串生成器：一个生成器从 chunk 里取出文本，下一个按句子切分（例如送去做语音合成），再下一个做过滤。每一步都是惰性的，第一句话生成完就能往下游送。练习 4 就是这个场景。

`02_迭代器与生成器.py` 的最后一节用假数据模拟了这个过程，不需要联网。

### 2.11 面试怎么问

1. 可迭代对象和迭代器有什么区别？`for` 循环背后做了什么？
2. 生成器和列表推导式有什么区别？什么时候该用生成器？
3. 为什么生成器只能遍历一次？第二次遍历会发生什么？
4. `yield` 和 `return` 有什么区别？`yield from` 做了什么？

---

## 3. 装饰器（P0-08）★

### 3.1 装饰器就是"接收函数、返回函数"的函数

第一课讲过函数是对象，可以当参数传，可以当返回值。再加上 1.4 节的闭包，就能写出装饰器：

```python
def log_calls(func):
    def wrapper(*args, **kwargs):          # 用 *args, **kwargs 接住任意参数
        print("调用", func.__name__)
        return func(*args, **kwargs)       # 原样转发参数，返回原函数的返回值
    return wrapper                         # wrapper 是闭包，捕获了 func

@log_calls
def add(a, b):
    return a + b
```

`@log_calls` 写在 `def` 上面，基本等价于定义完之后执行：

```python
add = log_calls(add)
```

也就是用 `wrapper` 替换掉了原来的 `add`。之后调用 `add(1, 2)`，实际执行的是 `wrapper(1, 2)`。

几点要记住：

- **装饰发生在 `def` 执行的时候**（通常是模块被 import 时），不是函数被调用的时候。`log_calls` 本身只执行一次，`wrapper` 每次调用都执行。
- **`wrapper` 一定要 `return func(...)` 的结果**，否则被装饰的函数永远返回 `None`。这是新手最常见的错误。
- C++ 没有对应的语法。C++ 的 `[[nodiscard]]` 这类 attribute 只是给编译器的标记，Python 装饰器是**运行时真的执行一个函数调用并替换原函数**。效果上类似设计模式里的装饰器模式，只是作用在函数上。

### 3.2 functools.wraps：保留原函数的名字和文档

上面的 `add` 被替换成 `wrapper` 之后，`add.__name__` 变成了 `"wrapper"`，`add.__doc__` 变成了 `None`。这会影响：

- 日志、报错信息里打印的函数名不对。
- `help(add)` 看不到文档。
- **按函数名和 docstring 自动注册工具的框架会出错。** 比如 LangChain 的 `@tool` 用函数名当工具名、用 docstring 当工具描述。如果你在它下面又套了一个没加 `wraps` 的装饰器，所有工具都会叫 `wrapper`，描述是空的。

修复方法是在 `wrapper` 上加 `@functools.wraps(func)`：

```python
import functools

def log_calls(func):
    @functools.wraps(func)                 # 把 func 的 __name__、__doc__ 等复制到 wrapper 上
    def wrapper(*args, **kwargs):
        ...
    return wrapper
```

`wraps` 会复制 `__name__`、`__qualname__`、`__doc__`、`__module__`、`__annotations__` 等属性，还会设置 `wrapper.__wrapped__ = func`，`inspect.signature` 会顺着 `__wrapped__` 找到原函数的签名。**写装饰器一律加 `wraps`。**

### 3.3 带参数的装饰器：三层嵌套

`@retry(times=3)` 这种带参数的写法，等价于：

```python
f = retry(times=3)(f)
```

`retry(times=3)` 先执行，返回一个真正的装饰器，再用它装饰 `f`。所以要写三层：

```python
def repeat(n):                    # 第 1 层：接收装饰器参数，返回装饰器
    def decorator(func):          # 第 2 层：接收被装饰的函数，返回 wrapper
        @functools.wraps(func)
        def wrapper(*args, **kwargs):   # 第 3 层：每次调用时执行
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator
```

注意 `@repeat(3)` 和 `@repeat` 不一样。写成 `@repeat` 时，`func` 会被当成 `n` 传进去，得到的是 `decorator`，调用时会出现莫名其妙的错误。

### 3.4 多个装饰器的叠加顺序

```python
@a
@b
def f(): ...
```

等价于 `f = a(b(f))`：

- **装饰顺序从下往上**：先 `b(f)`，再把结果交给 `a`。
- **调用顺序从外往内**：调用 `f()` 时先进入 `a` 的 wrapper，它调用 `b` 的 wrapper，最后才到原函数。返回时反过来。像洋葱一样一层套一层。

实际影响：`@retry` 和 `@timer` 一起用，`@timer` 写在上面，测的是包括所有重试在内的总时间；写在下面，测的是单次调用的时间。

### 3.5 常用实战

**计时**：用 `time.perf_counter()`，它是单调时钟，适合测时间间隔。不要用 `time.time()`，系统时间被调整时会跳变。

**重试**：调用大模型 API、网络请求经常会偶发失败（超时、限流），需要重试。写重试装饰器要注意：

- 只重试**指定类型**的异常，比如网络超时。参数错误这类重试也没用的异常应该直接抛出。
- 超过次数后要**把最后一次的异常抛出去**，不能吞掉后返回 `None`，否则调用方以为成功了。
- 实际项目里每次重试前要等待一段时间，通常是指数退避（1 秒、2 秒、4 秒……）。示例和练习里为了运行快，不等待。

**缓存：functools.lru_cache**

```python
from functools import lru_cache

@lru_cache(maxsize=128)       # 最多缓存 128 个结果，超出时淘汰最久没用的；maxsize=None 表示不限
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

fib.cache_info()              # CacheInfo(hits=..., misses=..., maxsize=128, currsize=...)
fib.cache_clear()             # 清空缓存
```

- 用参数做 key，所以**参数必须可哈希**。传 list、dict 会报 `TypeError`。
- 缓存的是返回值对象本身。如果返回的是 list 这类可变对象，调用方改了它，下次命中缓存拿到的就是改过的。
- `f(1, 2)` 和 `f(a=1, b=2)` 可能被当成不同的 key 分别缓存。
- Python 3.9 起有 `functools.cache`，等价于 `lru_cache(maxsize=None)`。
- 只适合纯函数（相同输入总是相同输出、没有副作用）。调用大模型这种每次结果可能不同、又有成本的函数，要不要缓存需要想清楚。

### 3.6 注册型装饰器：@tool

装饰器不一定要包装函数。它也可以只做一件"登记"的事，然后把原函数原样返回：

```python
TOOLS = {}

def tool(func):
    TOOLS[func.__name__] = func   # 定义函数时自动登记
    return func                   # 原样返回，函数本身不变

@tool
def get_weather(city): ...
```

对比仓库里 `example_agents/FunctionCallingAgent/tools.py` 的 `ToolRegistry`，那里是手动调用 `registry.register(name, description, parameters, func)`，名字和描述要再写一遍，容易和函数本身对不上。注册型装饰器的好处：

- 函数定义和注册写在一起，不会漏注册。
- 可以直接从函数上取信息：`func.__name__` 当工具名，`func.__doc__` 当描述。LangChain 的 `@tool`（`from langchain_core.tools import tool`）就是这样做的，它还会根据参数的类型标注生成参数的 JSON Schema。
- Flask 的 `@app.route("/path")`、pytest 的 `@pytest.fixture` 也都是注册型装饰器。

注册发生在模块被 import 时。如果定义工具的模块没有被 import，工具就不会出现在表里，这是用注册型装饰器时常见的"工具找不到"的原因。

### 3.7 面试怎么问

1. 装饰器的原理是什么？`@decorator` 等价于什么代码？
2. `functools.wraps` 有什么用？不加会怎样？
3. 怎么写一个带参数的装饰器？为什么要三层？
4. 多个装饰器叠加时，装饰顺序和执行顺序分别是怎样的？

---

## 读完后的自查

下面的问题能不看资料答出来，再开始做练习：

1. 函数里写 `count += 1`，而 `count` 是模块顶层的变量，会发生什么？怎么改？`global` 和 `nonlocal` 有什么区别？
2. `[lambda: i for i in range(3)]` 里每个函数返回什么？为什么？至少说出两种修复方法。
3. 不看代码，写出 `for x in obj: ...` 等价的 `while` 循环。
4. 调用一个生成器函数时，函数体执行了吗？什么时候执行？为什么一个生成器第二次遍历是空的？
5. `@a` 写在 `@b` 上面装饰 `f`，等价于什么？调用 `f()` 时谁的代码先执行？`functools.wraps` 解决了什么问题？
