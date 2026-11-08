# 第二课：写给 C++ 程序员的 Python（类、异常、with）

**覆盖知识点**：P0-05 类（self、魔术方法、@property、dataclass）、P0-06 异常处理与上下文管理器（with）
**预计用时**：4 到 5 小时

## 学习步骤

1. 按顺序读下面两部分。每读完一节，运行对应的示例文件，对照输出读代码注释：

   ```bash
   cd P0_python基础/lesson02_类与异常
   python 01_类基础.py              # 1.1 到 1.6
   python 02_魔术方法.py            # 1.7
   python 03_继承与dataclass.py     # 1.8 到 1.11
   python 04_异常与上下文管理器.py  # 第 2 部分
   ```

   和第一课一样，用 `python`，不要用 `python3`。

2. 遇到和预期不一样的输出，先自己改代码验证猜想。比如删掉某个魔术方法，看哪一行开始报错。
3. 完成 `练习.py` 里的 7 道题，运行 `python 练习.py`，直到全部通过。
4. 告诉教练“第二课学完了”，开始评估：L1 口述、L2 预测输出、L3 闭卷编码、L4 找 bug。

---

## 1. 类（P0-05）

### 1.1 self 就是显式的 this

```python
class Counter:
    def __init__(self, start=0):
        self.value = start

    def increment(self, step=1):
        self.value += step
```

| C++ | Python |
|---|---|
| `this` 隐式存在 | `self` 必须写成方法的第一个参数 |
| 成员函数里直接写 `value` 就能访问成员 | 必须写 `self.value`；单写 `value` 是局部变量 |
| `c.increment(1)` | `c.increment(1)` 等价于 `Counter.increment(c, 1)` |

`self` 只是约定俗成的名字，不是关键字，但不要改成别的名字。

### 1.2 `__init__` 和 C++ 构造函数的区别

Python 创建对象分两步：`__new__` 分配对象，`__init__` 往对象里放属性。平时只需要写 `__init__`。和 C++ 构造函数相比有这些不同：

| 区别 | C++ 构造函数 | Python `__init__` |
|---|---|---|
| 成员在哪里声明 | 类定义里声明，构造时已经存在 | 不需要声明，第一次给 `self.xxx` 赋值时才出现 |
| 能不能后加成员 | 不能 | 能，类外也可以写 `obj.new_attr = 1` |
| 重载 | 可以写多个构造函数 | 没有重载，用默认参数或 `@classmethod` 代替（见 1.5） |
| 父类构造 | 自动调用基类构造函数 | 子类写了 `__init__`，父类的 `__init__` **不会**自动调用，要自己写 `super().__init__(...)`（见 1.8） |
| 返回值 | 没有 | 必须返回 `None`，返回别的值会抛 `TypeError` |

属性存在实例的 `__dict__` 里，可以用 `vars(obj)` 查看。

Python 的语言规范不保证对象什么时候被回收。CPython 的引用计数通常会及时回收，但遇到循环引用就要等垃圾回收器。所以不要靠 `__del__` 释放文件、锁这类资源，要用第 2 部分讲的 `with`。

### 1.3 没有访问控制

Python 没有 `public`、`private`、`protected`，所有属性都能从外面访问。只有两个命名约定：

| 写法 | 含义 |
|---|---|
| `self.name` | 公开 |
| `self._name` | 约定为内部使用。外面能访问，只是不该访问 |
| `self.__name` | 名字改写（name mangling）：在类 `Account` 里会被改名成 `_Account__name` |

`__name` 的目的是防止子类不小心定义同名属性，把父类的覆盖掉，并不是为了保密。知道改写后的名字照样能访问。日常代码用单下划线就够了。

注意前后都有双下划线的名字（`__init__`、`__len__`）不会被改写，它们是魔术方法。

### 1.4 实例属性与类属性

写在类体里、方法外面的变量是**类属性**，只有一份，挂在类上，所有实例共享。最接近的 C++ 类比是 `static` 成员变量。

读 `obj.x` 时，Python 先在实例的 `__dict__` 里找，找不到再去类里找（再找不到就沿继承链往上找）。所以：

- `obj.x = 1` 是给实例**新建**一个属性，遮住类属性，类属性本身不变。
- `obj.items.append(1)` 是先找到 `items`。如果实例上没有，找到的就是类上那一份，原地修改后所有实例都能看到。

这就是类属性的陷阱，和第一课的可变默认参数是同一类问题：

```python
class BadAgent:
    tools = []                   # 只有一份

    def add_tool(self, name):
        self.tools.append(name)  # 修改的是类上的那一份

a1, a2 = BadAgent(), BadAgent()
a1.add_tool("search")
a2.tools                         # ['search']
```

规则：每个实例自己的数据（尤其是 list、dict、set）在 `__init__` 里创建。类属性只放所有实例共用、不会被修改的东西，比如常量和默认配置。

### 1.5 实例方法、`@classmethod`、`@staticmethod`

| 种类 | 第一个参数 | C++ 类比 | 常见用途 |
|---|---|---|---|
| 实例方法 | `self`（对象） | 普通成员函数 | 绝大多数方法 |
| `@classmethod` | `cls`（类本身） | 没有直接对应 | 另一种构造方式，例如 `from_dict`、`from_json` |
| `@staticmethod` | 无 | `static` 成员函数 | 和类有关、但不需要访问对象和类的工具函数 |

```python
class LLMConfig:
    def __init__(self, model, temperature=0.7): ...

    @classmethod
    def from_dict(cls, data):
        return cls(data["model"], data.get("temperature", 0.7))
```

`from_dict` 里要写 `cls(...)`，不要写死 `LLMConfig(...)`。这样子类调用 `QwenConfig.from_dict(...)` 时，得到的是子类对象。

### 1.6 `@property`

`@property` 的作用和 Qt 的 `Q_PROPERTY(qreal temperature READ temperature WRITE setTemperature)` 类似：读写属性时实际调用的是 getter 和 setter。区别是调用方的写法和普通属性完全一样，没有 `setTemperature()` 这种函数名，也没有 `NOTIFY` 信号。

```python
class ChatModel:
    @property
    def temperature(self):             # 读 m.temperature 时调用
        return self._temperature

    @temperature.setter
    def temperature(self, value):      # 写 m.temperature = 0 时调用
        if not 0 <= value <= 2:
            raise ValueError("temperature 必须在 0 到 2 之间")
        self._temperature = value      # 真正的数据存在另一个名字里
```

要点：

- 只写 getter、不写 setter，就是只读属性，赋值时抛 `AttributeError`。
- setter 里要存到 `self._temperature`。写成 `self.temperature = value` 会再次调用 setter，无限递归。
- 不需要像 C++ 那样一开始就给每个成员写 getter/setter。先用普通属性，以后需要校验时再改成 `@property`，调用方的代码不用改。

### 1.7 魔术方法：Python 的运算符重载

C++ 用 `operator+` 重载运算符，Python 用名字前后带双下划线的特殊方法。`len(x)` 会调用 `x.__len__()`，`a + b` 会调用 `a.__add__(b)`。

| 魔术方法 | 触发方式 | C++ 类比 |
|---|---|---|
| `__repr__` | `repr(x)`、交互环境显示、容器里的元素显示 | 没有直接对应，类似调试用的 `operator<<` |
| `__str__` | `str(x)`、`print(x)`、f-string | `operator<<` |
| `__eq__` | `a == b`（`!=` 自动取反） | `operator==` |
| `__hash__` | `hash(x)`、放进 set、当 dict 的键 | `std::hash` 特化 |
| `__lt__` | `a < b`、`sorted()` | `operator<` |
| `__len__` | `len(x)` | `size()` |
| `__getitem__` | `x[i]`、`x[1:3]` | `operator[]` |
| `__contains__` | `item in x` | 没有直接对应 |
| `__add__` / `__radd__` | `a + b` / `b` 不支持时反过来调用 `b + a` 的版本 | `operator+` |
| `__call__` | `x(...)` | `operator()` |
| `__bool__` | `if x:` | `explicit operator bool` |

**`__repr__` 和 `__str__`。** `__repr__` 给开发者看，约定写成能看出怎么构造这个对象的样子，例如 `Message('user', '你好')`。`__str__` 给用户看。只定义 `__repr__` 时，`str()` 也会用它；反过来不行。所以优先写 `__repr__`。打印 `[msg]` 这样的列表时，显示的是元素的 `__repr__`。

**`__eq__` 和 `__hash__` 必须一起考虑。** 这是本节最容易出错的地方：

- 不定义 `__eq__`：`==` 比较的是身份，相当于 `is`。
- 只定义 `__eq__`：Python 会自动把 `__hash__` 设为 `None`，对象不能放进 set，也不能当 dict 的键。
- 规则：**相等的对象，哈希值必须相等**。做法是对参与比较的字段组成的 tuple 求哈希：`hash((self.x, self.y))`。
- 参与哈希的字段不应该再被修改，否则对象放进 set 以后就找不到了。所以可哈希的对象一般是不可变的。

```python
def __eq__(self, other):
    if not isinstance(other, Point):
        return NotImplemented          # 不认识的类型，交给 Python 处理
    return (self.x, self.y) == (other.x, other.y)

def __hash__(self):
    return hash((self.x, self.y))
```

**`NotImplemented`。** 二元运算的魔术方法遇到不支持的类型时，应该**返回** `NotImplemented`（一个特殊的单例值，不是异常），而不是抛异常。Python 收到它以后会尝试另一边的方法：`a + b` 先调 `a.__add__(b)`，返回 `NotImplemented` 就调 `b.__radd__(a)`。两边都不支持时：

- `+`、`<` 等抛出标准的 `TypeError`。
- `==` 退回到身份比较，结果是 `False`。这就是 `Point(1, 2) == 1` 返回 `False` 而不是报错的原因。

注意不要和 `NotImplementedError` 混淆，后者是异常，用来表示“这个方法还没实现”，练习的占位代码用的就是它。

**比较运算符。** `sorted()` 只需要 `__lt__`。没有定义 `__gt__` 时，`a > b` 会改用 `b.__lt__(a)`。但 `<=` 对应 `__le__`，不会自动由 `__lt__` 和 `__eq__` 推出来。需要全部 6 个比较运算符时，可以用 `functools.total_ordering`，只写 `__eq__` 和 `__lt__`。

**容器协议。** 定义 `__len__` 和 `__getitem__` 后，对象就能用 `len()`、下标和切片。把 `__getitem__` 直接转给内部的 list，切片和负数下标自动都支持。没有定义 `__iter__` 时，`for` 循环会从 0 开始反复调用 `__getitem__`，直到抛出 `IndexError`；`__iter__` 第三课讲。没有定义 `__bool__` 时，`if x:` 用 `len(x) != 0` 判断。

**算术运算符返回新对象。** `__add__` 应该返回新对象，不修改 `self` 和 `other`，和 C++ 的 `operator+` 一样。原地修改是 `__iadd__`（`+=`）的事。

### 1.8 继承与 `super()`

```python
class Tool:
    def __init__(self, name):
        self.name = name

class SearchTool(Tool):
    def __init__(self, timeout):
        super().__init__("search")     # 相当于 C++ 初始化列表里的 Tool("search")
        self.timeout = timeout
```

| C++ | Python |
|---|---|
| `class B : public A` | `class B(A):` |
| 基类构造函数自动调用 | 子类写了 `__init__` 就要自己调 `super().__init__(...)`，否则父类设置的属性都不存在 |
| 子类没写构造函数时，默认构造函数会调用基类的 | 子类没写 `__init__` 时，直接继承父类的 `__init__` |
| `Base::method()` | `super().method()` |
| 只有 `virtual` 函数能多态 | **所有方法**都能被子类重写，父类里 `self.method()` 调到的是子类版本 |
| `override`、`final` 关键字 | 没有 |

忘记 `super().__init__` 不会在创建对象时报错，要等到访问父类设置的属性时才抛 `AttributeError`。

**MRO 简介。** Python 支持多继承。方法查找的顺序叫 MRO（Method Resolution Order），用 C3 线性化算法计算，可以用 `类名.__mro__` 查看。菱形继承 `class D(B, C)`，B 和 C 都继承 A 时，MRO 是 `D, B, C, A, object`。

`super()` 的意思是“MRO 里的下一个类”，不一定是直接父类。在 D 的对象上调用时，B 里的 `super().hello()` 调到的是 C，不是 A，所以 A 只被调用一次。日常开发很少写菱形继承，知道 `super()` 按 MRO 走、能用 `__mro__` 查顺序就够了。

### 1.9 鸭子类型与抽象基类

C++ 里，要让一个函数接受多种对象，通常定义一个带虚函数的基类，函数参数写成 `Base&`。Python 的函数参数没有类型限制，**只要对象有需要的方法就能用**，不要求有公共基类。这叫鸭子类型（duck typing）：“走起来像鸭子、叫起来像鸭子，就当它是鸭子”。

```python
def execute(tool, arg):
    return tool.run(arg)       # 任何有 run 方法的对象都可以传进来
```

更接近的 C++ 类比是模板：`template <class T> void execute(T& tool)` 也只要求 T 有 `run`。区别是 C++ 模板在编译时检查，Python 在运行到这一行时才检查，对象没有 `run` 就抛 `AttributeError`。

需要强制子类实现某些方法时，用抽象基类 `abc.ABC`，作用相当于 C++ 的纯虚函数：

```python
from abc import ABC, abstractmethod

class BaseTool(ABC):
    @abstractmethod
    def run(self, **kwargs): ...     # 相当于 virtual ... = 0

    def __call__(self, **kwargs):     # 抽象基类里也可以有普通方法
        return str(self.run(**kwargs))
```

- 实例化 `BaseTool`，或者实例化没有实现全部抽象方法的子类，都会抛 `TypeError`。
- 检查发生在**实例化时**。定义一个没实现 `run` 的子类本身不会报错。
- 抽象基类适合框架代码，用来规定“一个工具必须有哪些方法”。业务代码里，鸭子类型往往就够了。

### 1.10 dataclass

很多类只是用来装数据的，例如一条聊天消息。手写 `__init__`、`__repr__`、`__eq__` 很啰嗦，`@dataclass` 会根据带类型标注的字段自动生成它们。最接近的 C++ 类比是聚合初始化的 `struct`，再加上编译器生成的 `operator==`。

```python
from dataclasses import dataclass, field

@dataclass
class ChatMessage:
    role: str
    content: str
    name: str | None = None
    tool_calls: list = field(default_factory=list)
```

| 规则 | 说明 |
|---|---|
| 字段必须有类型标注 | 没有标注的 `y = 2` 只是普通类属性，不是字段 |
| 有默认值的字段放在后面 | 和函数参数的规则一样，否则定义类时抛 `TypeError` |
| 可变默认值用 `field(default_factory=list)` | 写 `tool_calls: list = []`，定义类时就抛 `ValueError` |
| 自己定义了 `__init__` | dataclass 不会再生成 `__init__`，会保留你写的那个 |
| 默认生成 `__eq__` | 按字段逐个比较；`__hash__` 被设为 `None`，对象不可哈希 |

`default_factory` 和第一课的可变默认参数陷阱是同一个问题。默认值只计算一次，如果允许写 `= []`，所有对象就会共享同一个列表，所以 dataclass 直接拒绝 list、dict、set 这类默认值。`default_factory=list` 表示每创建一个对象就调用一次 `list()`，得到一个新列表。

类型标注在运行时不检查，`ChatMessage(role=1, content=None)` 不会报错。运行时校验要用 Pydantic，P0-09 讲。

### 1.11 frozen dataclass

`@dataclass(frozen=True)` 生成不可修改的对象：

- 给字段赋值抛 `dataclasses.FrozenInstanceError`。
- 同时设置了 `eq=True`（默认就是）时，会生成 `__hash__`，可以放进 set、当 dict 的键。
- 要“修改”，用 `dataclasses.replace(obj, name="新值")` 生成一个新对象。
- frozen 是浅层的，和第一课讲的 tuple 一样：字段不能重新赋值，但字段指向的 list 照样可以 `append`。这样的对象也没法求哈希，因为 list 不可哈希。

在大模型应用里，用 dataclass 表示消息、工具调用、Agent 状态很常见。不会被修改的值（比如一次工具调用的名字和参数）适合用 frozen。

### 1.12 面试怎么问

1. Python 的类属性和实例属性有什么区别？类属性是一个 list 时会出现什么问题？
2. `__eq__` 和 `__hash__` 有什么关系？只重写 `__eq__` 会发生什么？
3. `@classmethod` 和 `@staticmethod` 有什么区别？各举一个使用场景。
4. Python 的 `__name` 是私有属性吗？`super()` 在多继承里调用的是哪个类的方法？

---

## 2. 异常处理与上下文管理器（P0-06）

### 2.1 Python 和 C++/Qt 的错误处理习惯

| | C++/Qt | Python |
|---|---|---|
| 常见做法 | 返回错误码、`bool`、`std::optional`；Qt 很少用异常，例如 `QString::toInt(bool *ok)` | 失败就抛异常，例如 `int("abc")` 抛 `ValueError` |
| 异常的开销 | 很多项目认为开销大，有的直接 `-fno-exceptions` | 没有异常时 `try` 几乎没有开销（3.11 起），抛出才有开销 |
| 函数声明 | `noexcept` 说明不抛异常 | 没有任何声明，可能抛什么只能看文档 |
| 标准库 | 多数接口不抛异常 | 大量使用异常：`d["不存在的键"]` 抛 `KeyError`，`lst[100]` 抛 `IndexError` |

在 Python 里，异常是正常的错误处理方式，不是只在“出大事”时才用。写函数时，遇到无法完成的情况就 `raise`，让知道怎么处理的那一层去 `except`。

### 2.2 try / except / else / finally

```python
try:
    value = int(text)          # 只放可能出错的那一句
except ValueError as e:
    print("不是整数:", e)
else:
    print("没有异常才执行")    # 这里抛的异常不会被上面的 except 接住
finally:
    print("无论如何都执行")    # 包括 try 或 except 里 return 的情况
```

| 子句 | 什么时候执行 |
|---|---|
| `except X as e` | try 里抛出 X 或 X 的子类时 |
| `else` | try 里没有抛异常时 |
| `finally` | 总是执行，用来做清理 |

要点：

- `try` 包住的代码越少越好。包得太多，会把不该处理的异常也接住。
- 多个 `except` 从上往下匹配，第一个匹配上的生效。子类要写在父类前面，否则永远轮不到。
- 一次接多种：`except (KeyError, IndexError) as e:`。
- **`except ... as e` 里的 `e` 在 except 块结束后会被删除**，后面再用会抛 `NameError`。需要在外面用，就先赋值给另一个名字。
- 不要在 `finally` 里写 `return`，它会让 try 里的异常消失。

### 2.3 异常的继承体系

所有异常都是类，`except` 父类会接住所有子类：

```
BaseException
├── SystemExit           sys.exit() 抛出
├── KeyboardInterrupt    用户按 Ctrl+C
├── GeneratorExit
└── Exception            普通异常都在这下面
    ├── ArithmeticError → ZeroDivisionError
    ├── LookupError     → KeyError、IndexError
    ├── OSError         → FileNotFoundError、TimeoutError、ConnectionError ...
    ├── ValueError、TypeError、AttributeError、NameError、RuntimeError ...
    └── 你自己定义的异常
```

`SystemExit` 和 `KeyboardInterrupt` 故意不继承 `Exception`，这样 `except Exception` 不会拦住“程序退出”和“用户中断”。

**不要用裸 `except:`。** 不写类型的 `except:` 等价于 `except BaseException:`，连 `SystemExit` 和 `KeyboardInterrupt` 都会接住，程序按 Ctrl+C 都停不下来。

| C++ | Python |
|---|---|
| `catch (const std::exception& e)` | `except Exception as e` |
| `catch (...)` | `except:`（不要用） |

`except Exception` 一般只用在最外层，例如记录日志后继续处理下一个请求。业务代码里应该接住具体的异常类型。

### 2.4 raise 与自定义异常

- `raise ValueError("说明")`：抛出一个异常对象。
- 在 except 块里写不带参数的 `raise`：原样重新抛出当前异常，适合“记录日志后继续往上抛”。

自定义异常继承 `Exception`（不要继承 `BaseException`）。一个项目通常先定义一个基类，再按失败原因派生：

```python
class AgentError(Exception):
    """本项目所有异常的基类"""

class LLMTimeoutError(AgentError):
    def __init__(self, model, seconds):
        super().__init__(f"模型 {model} 超过 {seconds} 秒没有响应")   # 决定 str(e)
        self.model = model                                            # 额外信息
        self.seconds = seconds

class ToolArgumentError(AgentError):
    pass
```

这样调用方可以按原因分别处理：模型超时可以重试；工具参数错了，重试没用，应该把错误信息交给模型让它改参数。只想统一处理时，写 `except AgentError` 一次全部接住。

### 2.5 异常链：raise ... from e

捕获一个底层异常，再抛出一个更有业务含义的异常时，用 `from` 把两者关联起来：

```python
try:
    return config["temperature"]
except KeyError as e:
    raise AgentError("配置缺少 temperature") from e
```

| 写法 | 效果 |
|---|---|
| `raise New(...) from e` | `New.__cause__ = e`，traceback 里两个异常之间写着 “The above exception was the direct cause of the following exception” |
| 在 except 里 `raise New(...)`，不写 from | 原始异常记在 `__context__`，traceback 写着 “During handling of the above exception, another exception occurred”，看起来像处理代码本身出了 bug |
| `raise New(...) from None` | 明确表示不需要显示原始异常 |

包装异常时写 `from e`，排查问题时能看到最初的原因。

### 2.6 EAFP 与 LBYL

| 风格 | 全称 | 写法 |
|---|---|---|
| LBYL | Look Before You Leap，先检查再做 | `if key in d: v = d[key]` |
| EAFP | Easier to Ask Forgiveness than Permission，直接做，出错再处理 | `try: v = d[key]` / `except KeyError: ...` |

C++ 程序员习惯 LBYL。Python 社区更常用 EAFP，原因是：

- 检查和使用之间可能发生变化。例如先判断文件存在、再打开，中间文件可能被删掉；直接打开再处理 `FileNotFoundError` 没有这个问题。
- 有些情况很难提前检查完整，例如一个字符串能不能转成整数，直接 `int(s)` 再接 `ValueError` 更简单。

两种风格不是绝对的。像取字典默认值这种简单情况，直接用 `d.get(key, 默认值)`。

### 2.7 with 语句：Python 的 RAII

C++ 用 RAII 管理资源：`std::lock_guard`、`QMutexLocker`、`std::ifstream` 在析构时释放资源。Python 不能依赖析构时机，对应的写法是 `with`：

```python
with open("notes.txt", encoding="utf-8") as f:   # 文本文件要写 encoding
    text = f.read()
# 离开 with 块时文件一定已经关闭，无论是正常结束、return 还是抛异常

with lock:                                        # threading.Lock，相当于 std::lock_guard
    counter += 1

with open("a.txt") as src, open("b.txt", "w") as dst:   # 一条 with 写多个
    ...
```

一条 with 写多个时，退出顺序和进入顺序相反，和 C++ 局部对象的析构顺序一样。

注意 with 不会创建新的作用域。块里定义的变量，离开 with 后仍然可以访问，例如 `f.closed` 可以在外面检查。

### 2.8 自己写上下文管理器：`__enter__` 和 `__exit__`

任何定义了 `__enter__` 和 `__exit__` 的对象都能用在 with 里：

```python
class Tracer:
    def __enter__(self):
        print("进入")
        return self                     # 绑定到 as 后面的名字

    def __exit__(self, exc_type, exc_value, traceback):
        print("退出")
        return False                    # 不吞异常
```

`with Tracer() as t: ...` 的执行过程：

1. 调用 `__enter__()`，返回值绑定到 `t`。不写 `return` 时 `t` 是 `None`。
2. 执行 with 块。
3. 无论块里是否抛异常，都调用 `__exit__`。

`__exit__` 的三个参数：

| 情况 | `exc_type` | `exc_value` | `traceback` |
|---|---|---|---|
| 正常结束 | `None` | `None` | `None` |
| 块里抛了异常 | 异常类型，如 `ValueError` | 异常对象 | traceback 对象 |

`__exit__` 的返回值：

- 返回真值：表示异常已经处理，**异常被吞掉**，程序从 with 后面继续执行。
- 返回 `None` 或 `False`：异常继续往外传。不写 `return` 就是 `None`。

常见错误是 `__exit__` 无条件 `return True`，把所有异常都吞掉，出了问题也不知道。只在明确要忽略某类异常时才返回真值，并且用 `issubclass(exc_type, ...)` 判断类型。

另外，如果 `__enter__` 本身抛了异常，with 块不会执行，`__exit__` 也不会被调用。

第三课学完生成器后，会讲用 `contextlib.contextmanager` 写上下文管理器的更简洁写法。

### 2.9 面试怎么问

1. `try` / `except` / `else` / `finally` 各在什么时候执行？`else` 里的代码和直接写在 try 末尾有什么区别？
2. 为什么不要写裸 `except:`？`except Exception` 和它有什么区别？
3. `raise ... from e` 有什么作用？什么是 EAFP，为什么 Python 推荐它？
4. with 语句的原理是什么？`__exit__` 的返回值有什么作用？

---

## 读完后的自查

下面的问题能不看资料答出来，再开始做练习：

1. 在类体里写 `items = []`，和在 `__init__` 里写 `self.items = []`，有什么区别？
2. 子类定义了 `__init__` 但没有调用 `super().__init__()`，会发生什么？什么时候才会发现？
3. 只定义了 `__eq__` 的类，为什么不能放进 set？`__hash__` 应该怎么写？
4. dataclass 为什么不允许 `items: list = []`？`field(default_factory=list)` 解决了什么问题？
5. 自己写的 `__exit__` 返回 `True` 会怎样？什么时候应该返回 `True`？
