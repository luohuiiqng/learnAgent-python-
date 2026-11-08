# 第四课：类型标注、Pydantic、模块与工程化

**覆盖知识点**：P0-09 类型标注与 Pydantic v2（目标 L4）、P0-10 模块、包与 import 机制（目标 L3）、P0-11 工程化：虚拟环境、uv、ruff、pytest、logging（目标 L3）
**预计用时**：5 到 6 小时

## 学习步骤

1. 按顺序读下面三节。每节读完，运行对应的示例，对照输出读代码注释：

   ```bash
   cd P0_python基础/lesson04_类型与工程化
   python 01_类型标注与Pydantic.py
   python 02_模块与包.py
   python 03_工程化.py
   python -m pytest tests -q
   ```

   用 `python`，不要用 `python3`。你电脑上的 `python3` 是另一个没装依赖的版本。
   本课的示例和测试都要在 `lesson04_类型与工程化` 目录下运行，第 2 节会讲为什么。

2. 第 3 节的 uv 和 ruff 实操，在本课目录下新建的 `scratch` 子目录里做。**不要在仓库根目录运行 `uv init`**，否则整个仓库会变成一个 uv 项目。练完可以把 `scratch` 目录删掉。
3. 完成 `练习.py` 里的练习 1 到 5，以及 `练习_test_chunk.py`（练习 6）。运行 `python 练习.py`，直到全部通过。
4. 告诉教练“第四课学完了”，开始评估：L1 口述、L2 预测输出、L3 闭卷编码。P0-09 的目标是 L4，还有一轮找 bug。

### 本课文件

| 文件 | 内容 |
|---|---|
| `01_类型标注与Pydantic.py` | P0-09 示例 |
| `02_模块与包.py` | P0-10 示例，用到 `demo_pkg/` |
| `03_工程化.py` | P0-11 的虚拟环境信息和 logging 示例 |
| `demo_pkg/` | 示例包：`mathutils.py`、`config.py`（Pydantic + logging）、`tools/stats.py`（相对导入）、`circular/`（循环导入）、`noisy.py`（导入时执行）、`chunking.py`（练习 6 的被测函数） |
| `tests/` | pytest 示例测试，测试 `demo_pkg` 里的函数 |
| `练习.py`、`练习_test_chunk.py` | 练习和检查代码 |

---

## 1. 类型标注与 Pydantic v2（P0-09）

### 1.1 标注只是元数据，运行时不检查

C++ 的类型由编译器检查，类型不对就编译不过。Python 的类型标注（type hints）只是写在函数和变量上的说明，**解释器运行时完全不看它**：

```python
def add(a: int, b: int) -> int:
    return a + b

add("1", "2")   # 不报错，返回 "12"
```

标注存在函数对象的 `__annotations__` 里，有三类工具会读它：

| 谁 | 什么时候 | 做什么 |
|---|---|---|
| Python 解释器 | 运行时 | 不检查 |
| mypy、pyright（VS Code 的 Pylance 基于 pyright） | 运行前，静态分析 | 类似 C++ 编译器的类型检查，但只报告，不阻止运行 |
| Pydantic、FastAPI 等库 | 运行时 | 主动读取标注，按标注校验和转换数据 |

mypy 能发现的问题，例如：

```python
def find_user(uid: int) -> str | None: ...

name = find_user(1)
print(name.upper())   # mypy: Item "None" of "str | None" has no attribute "upper"
add("1", "2")         # mypy: Argument 1 to "add" has incompatible type "str"; expected "int"
```

想自己试，可以在 scratch 目录里运行 `uvx mypy 文件名.py` 或 `uvx pyright 文件名.py`（uvx 见第 3 节）。

### 1.2 常用写法

| 写法 | 含义 | C++ 类比 |
|---|---|---|
| `int` `str` `float` `bool` `None` | 基本类型 | |
| `list[int]` | 元素是 int 的列表 | `std::vector<int>` |
| `dict[str, list[int]]` | 键是 str、值是 int 列表的字典 | `std::unordered_map<std::string, std::vector<int>>` |
| `tuple[int, str]`、`tuple[int, ...]` | 固定两个元素；任意多个 int | `std::tuple<int, std::string>` |
| `str \| None`，等价 `Optional[str]` | str 或 None | `std::optional<std::string>` |
| `int \| str`，等价 `Union[int, str]` | 二者之一 | `std::variant<int, std::string>` |
| `Callable[[str, int], bool]` | 接收 (str, int)、返回 bool 的可调用对象 | `std::function<bool(std::string, int)>` |
| `Literal["user", "assistant"]` | 只能取这几个值 | 轻量的 `enum class` |
| `TypedDict` | 规定每个键类型的 dict | 只有字段的 `struct`，但运行时就是普通 dict |
| `Any` | 任意类型，关闭检查 | `void*` / `std::any` |

几点说明：

- `list[int]`、`dict[str, X]` 这种小写写法从 Python 3.9 开始支持，`X | None` 从 3.10 开始。老代码里的 `typing.List`、`typing.Dict`、`Optional` 意思一样。仓库里 `example_agents/FunctionCallingAgent/tools.py` 用的 `Dict[str, Any]` 就是老写法。
- `Optional[int]` 的意思是“可以是 None”，**不是“可以不传”**。`def f(x: Optional[int])` 调用时仍然必须传 `x`；想让它可以不传，要写默认值 `x: int | None = None`。
- 带参数的泛型不能用于 `isinstance`：`isinstance(x, list[int])` 会抛 `TypeError`。运行时只能写 `isinstance(x, list)`。

### 1.3 简单泛型

```python
from typing import TypeVar

T = TypeVar("T")
def first(items: list[T]) -> T:      # 老写法，现有代码里大量使用
    return items[0]

def first[T](items: list[T]) -> T:   # Python 3.12 起的新写法
    return items[0]
```

静态检查器会推断出 `first([1, 2])` 是 `int`，`first(["a"])` 是 `str`。写法像 C++ 的 `template <typename T>`，区别是 Python 不会为每个类型生成一份代码，运行时这个 `T` 没有任何作用。

### 1.4 TypedDict、dataclass、Pydantic 怎么选

| | TypedDict | dataclass（第二课） | Pydantic BaseModel |
|---|---|---|---|
| 运行时的对象 | 普通 dict | 普通类的实例 | BaseModel 子类的实例 |
| 运行时校验类型 | 否 | 否 | **是**，还会做类型转换 |
| 典型用途 | 给已有的 dict 结构（如 OpenAI 的 messages）加标注 | 程序内部传递的数据 | 外部输入：HTTP 请求、配置文件、**大模型的输出** |

判断原则：数据来自程序外部、不可信，就用 Pydantic。

### 1.5 Pydantic BaseModel：按标注在运行时校验

在 Qt 里解析一个 JSON 配置，要用 `QJsonDocument` 读出来，再一个字段一个字段地判断类型、检查范围、给默认值。Pydantic 把这些工作变成声明：

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    tags: list[str] = []      # 有默认值的字段可以不传

u = User(name="hq", age="18")   # age 被转换成 int 18
```

**默认是宽松（lax）模式，会做“合理的”类型转换**：

| 字段类型 | 输入 | 结果 |
|---|---|---|
| `int` | `"18"`、`18.0` | `18` |
| `int` | `18.5`、`"abc"` | ValidationError |
| `str` | `123` | ValidationError（v2 不会把数字转成字符串） |
| `bool` | `"yes"`、`1` | `True` |
| `bool` | `"maybe"` | ValidationError |

**严格（strict）模式不做类型转换**，`"18"` 传给 `int` 字段直接报错。三种开启方式：整个模型 `model_config = ConfigDict(strict=True)`；单个字段 `Field(strict=True)`；单次调用 `Model.model_validate(data, strict=True)`。

另外两个默认行为要知道：

- 输入里多出来的字段默认**被忽略**，不报错。要报错，设 `model_config = ConfigDict(extra="forbid")`。
- 创建之后给字段赋值，默认**不校验**：`u.age = "abc"` 不报错。要校验，设 `ConfigDict(validate_assignment=True)`。

第一课讲过函数的可变默认参数陷阱。Pydantic 字段写 `tags: list[str] = []` 没有这个问题，Pydantic 会给每个实例复制一份默认值。也可以写 `Field(default_factory=list)`。

### 1.6 Field 约束

```python
from typing import Literal
from pydantic import BaseModel, Field

class WeatherArgs(BaseModel):
    city: str = Field(min_length=1, description="城市名，例如 北京")
    days: int = Field(default=1, ge=1, le=7, description="预报天数，1 到 7")
    unit: Literal["celsius", "fahrenheit"] = "celsius"
```

| 参数 | 作用 |
|---|---|
| `default` / `default_factory` | 默认值 / 生成默认值的函数。不写就是必填字段 |
| `ge` `gt` `le` `lt` | 数值 ≥ > ≤ < |
| `min_length` `max_length` | 字符串、列表的长度 |
| `pattern` | 字符串必须匹配的正则 |
| `description` | 字段说明。会写进 JSON Schema，大模型靠它理解参数含义 |

### 1.7 嵌套模型和四个常用方法

字段的类型可以是另一个模型，或者 `list[另一个模型]`，Pydantic 会递归校验，嵌套的 dict 会变成对应的模型对象。

| 方法 | 方向 | v1 的旧名字（看老代码时会遇到） |
|---|---|---|
| `Model.model_validate(dict)` | dict → 对象 | `parse_obj` |
| `Model.model_validate_json(str)` | JSON 字符串 → 对象 | `parse_raw` |
| `obj.model_dump()` | 对象 → dict（嵌套对象也转成 dict） | `.dict()` |
| `obj.model_dump_json()` | 对象 → JSON 字符串 | `.json()` |
| `Model.model_json_schema()` | 模型 → JSON Schema（dict） | `.schema()` |

`model_validate_json` 比 `json.loads` 再 `model_validate` 更合适：JSON 格式错误也会变成 `ValidationError`，只需要处理一种异常。

v2 的核心校验逻辑用 Rust 重写了（pydantic-core 包），API 也改了名。网上很多教程还是 v1 写法，`@validator`、`class Config:`、`.dict()` 都是 v1 的。本课全部用 v2。

### 1.8 读懂 ValidationError

```text
3 validation errors for WeatherArgs
city
  String should have at least 1 character [type=string_too_short, input_value='', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/string_too_short
days
  Input should be less than or equal to 7 [type=less_than_equal, input_value=10, input_type=int]
...
```

结构是：错误总数和模型名；然后每个错误一段，第一行是**字段路径**，第二行是**原因**，方括号里是**错误类型**和**实际输入**。

在代码里不要解析这段文字，用 `e.errors()`，它返回一个 list，每个元素是 dict：

| 键 | 含义 | 例子 |
|---|---|---|
| `loc` | 字段路径，tuple | `("days",)`；嵌套时 `("tool_calls", 0, "arguments")`；JSON 本身不合法时是 `()` |
| `msg` | 人能读懂的原因 | `"Input should be less than or equal to 7"` |
| `type` | 错误类型，适合程序判断 | `"less_than_equal"`、`"missing"`、`"json_invalid"` |
| `input` | 导致错误的输入值 | `10` |

`e.error_count()` 返回错误条数。一次校验会把所有字段的错误都收集起来，不会遇到第一个就停。

### 1.9 field_validator：自定义校验和清洗

```python
from pydantic import BaseModel, field_validator

class SearchArgs(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query 不能是空白")
        return v           # 返回值就是最终保存的值，一定要 return
```

- 装饰器顺序固定：`@field_validator(...)` 在上，`@classmethod` 在下。
- 默认 `mode="after"`：先做类型校验，再调用你的函数，`v` 已经是正确的类型。
- `mode="before"`：在类型校验**之前**调用，`v` 是原始输入，可能是任何类型，要自己判断。
- 校验失败时抛 `ValueError`（或 `AssertionError`），Pydantic 会把它包装进 `ValidationError`，`msg` 是 `"Value error, 你的信息"`。**抛其他异常（比如对 int 调用 `.strip()` 产生的 `AttributeError`）不会被包装**，会直接抛给调用方。
- 一个校验器可以同时作用于多个字段：`@field_validator("a", "b")`。需要同时看多个字段的校验用 `model_validator`，本课不展开。

### 1.10 和大模型的关系：工具参数和结构化输出

**工具参数的 JSON Schema 可以自动生成。** 仓库里 `example_agents/FunctionCallingAgent/builtin_tools.py` 的 `CALCULATE_SCHEMA` 是手写的 dict。用 Pydantic 写成模型：

```python
class CalculateArgs(BaseModel):
    expression: str = Field(description="数学表达式，例如 '(3 + 5) * 2 ** 10'")

CalculateArgs.model_json_schema()
# {'properties': {'expression': {'description': "数学表达式，例如 '(3 + 5) * 2 ** 10'",
#                                'title': 'Expression', 'type': 'string'}},
#  'required': ['expression'], 'title': 'CalculateArgs', 'type': 'object'}
```

除了多出 `title`，和手写的完全一样（`01_类型标注与Pydantic.py` 第 8 段做了对比）。生成的 schema 还有这些规律：有默认值的字段不在 `required` 里，并带上 `default`；`Literal` 变成 `enum`；`ge`/`le` 变成 `minimum`/`maximum`；`str | None` 变成 `anyOf`；嵌套模型放在 `$defs` 里，用 `$ref` 引用；类的 docstring 变成最外层的 `description`。

**同一个模型还能校验模型返回的参数。** `tools.py` 的 `execute()` 现在是 `json.loads` 之后直接 `func(**arguments)`，参数类型错了要等到工具内部才出问题。改成先校验：

```python
try:
    args = CalculateArgs.model_validate_json(arguments_json or "{}")
except ValidationError as e:
    return f"错误：参数不合法（{e.errors(include_url=False)}）"   # 把错误交给模型，让它修正
return calculate(**args.model_dump())
```

一份模型定义，同时得到“给模型看的 schema”和“检查模型输出的校验器”，两者不会不一致。练习 2、3 就是做这件事。

**结构化输出也是同一个思路**：让模型输出 JSON 而不是自由文本时，

1. 把 `Model.model_json_schema()` 放进提示词，或者传给支持结构化输出的 API 参数；
2. 用 `Model.model_validate_json(回复文本)` 校验；
3. 校验失败时，把 `e.errors()` 整理成文字发回给模型，让它重新生成（通常限制重试次数）。

有些 SDK 允许直接传入 Pydantic 模型类，内部做的也是这几步。OpenAI 的 strict 结构化输出对 schema 有额外要求（例如 `additionalProperties: false`），具体以官方文档为准。另外，OpenAI Python SDK 返回的 `ChatCompletion` 等对象本身就是 Pydantic 模型。

### 1.11 面试怎么问

1. Python 的类型标注在运行时有作用吗？和 C++ 的类型检查有什么区别？
2. Pydantic 和 dataclass 有什么区别？各自适合什么场景？
3. 大模型返回的工具参数或 JSON 不符合要求，你在工程上怎么处理？
4. Pydantic v1 和 v2 有哪些主要区别？

---

## 2. 模块、包与 import 机制（P0-10）

### 2.1 和 C++ 对照

| C++ | Python | 区别 |
|---|---|---|
| `#include "a.h"` | `import a` | `#include` 在编译前把文本粘贴进来，每个编译单元都处理一遍，所以需要 include guard。`import` 在**运行时**执行 `a.py`，得到一个 module 对象，整个进程只执行一次 |
| `namespace a { ... }` | 模块本身 | 每个 .py 文件就是一个命名空间，`a.func` 访问 |
| 头文件搜索路径 `-I` | `sys.path` | 按顺序在这些目录里找 |
| 第三方库安装目录 | `site-packages` | `pip install` / `uv add` 装到这里 |

### 2.2 模块和包

- **模块**：一个 `.py` 文件。文件名就是模块名（不带 `.py`）。
- **包**：一个包含 `__init__.py` 的目录，里面可以有模块和子包。`import demo_pkg` 执行的是 `demo_pkg/__init__.py`。
- `__init__.py` 可以是空的。常见用法是把子模块里的常用名字“提上来”，比如 `demo_pkg/__init__.py` 里写 `from .mathutils import mean`，使用者就能写 `from demo_pkg import mean`。
- `__all__` 规定 `from demo_pkg import *` 导入哪些名字。业务代码里不要用 `import *`，看不出名字从哪来。
- 没有 `__init__.py` 的目录也能 import，叫命名空间包（namespace package）。仓库里的 `example_agents/` 就没有 `__init__.py`。初学阶段，自己写的包都加上 `__init__.py`。

```text
demo_pkg/
├── __init__.py        # import demo_pkg 时执行
├── __main__.py        # python -m demo_pkg 时执行
├── mathutils.py       # 模块 demo_pkg.mathutils
├── config.py
└── tools/             # 子包 demo_pkg.tools
    ├── __init__.py
    └── stats.py       # 模块 demo_pkg.tools.stats，里面用了相对导入
```

### 2.3 import 时发生了什么

执行 `import demo_pkg.noisy` 时：

1. 查 `sys.modules`（一个 dict，模块名 → module 对象）。已经有了就直接用，**不会再执行一遍**。
2. 没有，就按 `sys.path` 的顺序找 `demo_pkg/noisy.py`。
3. 创建 module 对象，**先放进 `sys.modules`，再从头到尾执行模块的顶层代码**。`def` 和 `class` 语句也是在这时执行的，执行完函数和类才存在。
4. 在当前命名空间里绑定名字。

导入 `a.b.c` 时会依次导入 `a`、`a.b`、`a.b.c`，每一级包的 `__init__.py` 都会执行。

由此可以推出几个结论：

- 模块顶层代码只执行一次，所以模块级变量相当于进程内的单例。
- 模块顶层不要放耗时操作（连数据库、加载模型）或有副作用的代码，任何 import 它的地方都会触发。
- `importlib.reload(m)` 会强制重新执行，一般只在交互调试时用。
- `__pycache__/` 里的 `.pyc` 是编译好的字节码缓存，可以随便删，已经被 `.gitignore` 忽略。

### 2.4 import 的几种写法

| 写法 | 绑定的名字 | 说明 |
|---|---|---|
| `import json` | `json` | 用 `json.dumps` 访问 |
| `import demo_pkg.mathutils` | `demo_pkg` | 用 `demo_pkg.mathutils.mean` 访问 |
| `from demo_pkg.mathutils import mean` | `mean` | 直接用 `mean` |
| `import numpy as np` | `np` | 起别名 |

`from x import y` 相当于 `y = x.y`，复制的是**当时那个对象的引用**（第一课的引用语义）。如果 `x` 之后把 `y` 重新赋值，你手里的 `y` 不会变。`02_模块与包.py` 第 4 段演示了这一点。需要看到最新值时，用 `import x` 再访问 `x.y`。

### 2.5 sys.path 和模块搜索顺序

`sys.path` 是一个目录列表，import 按顺序在里面找，找到第一个就停：

1. `sys.path[0]`：运行 `python 某文件.py` 时是**这个文件所在的目录**；运行 `python -m 模块` 或 `python -c` 时是**当前工作目录**；
2. 环境变量 `PYTHONPATH` 里的目录；
3. 标准库目录；
4. `site-packages`（第三方包）。

常见的坑：自己的文件和标准库或第三方包同名，比如写了一个 `json.py` 或 `openai.py`。因为 `sys.path[0]` 排在前面，`import json` 会导入你的文件。

### 2.6 `if __name__ == "__main__":`

每个模块都有 `__name__`。被 import 时，它是模块的完整名字（`"demo_pkg.mathutils"`）；被直接运行时，它是 `"__main__"`。

```python
if __name__ == "__main__":
    main()     # 只有直接运行这个文件时才执行，被 import 时不执行
```

作用类似 C++ 的 `main()` 入口：同一个文件既能被别人 import，也能单独运行。

### 2.7 绝对导入和相对导入

```python
# demo_pkg/tools/stats.py 里
from demo_pkg.mathutils import mean    # 绝对导入：从 sys.path 里的顶层包开始写
from ..mathutils import mean           # 相对导入：. 是当前包 demo_pkg.tools，.. 是上一级 demo_pkg
```

- 相对导入只能在包内部使用，依赖模块的 `__package__` 属性。
- 带相对导入的文件**不能直接运行**：`python demo_pkg/tools/stats.py` 会报 `ImportError: attempted relative import with no known parent package`，因为直接运行的文件不属于任何包。
- 一般建议用绝对导入，更清楚；包内部模块之间互相引用时，相对导入也常见，比如 `example_agents/FunctionCallingAgent/__init__.py` 里的 `from .agent import FunctionCallingAgent`。

### 2.8 python -m

`python -m demo_pkg.tools.stats` 按**模块名**运行，而不是按文件路径：

- `sys.path[0]` 是当前目录，所以能找到 `demo_pkg`；
- 模块属于 `demo_pkg.tools` 包，相对导入能用；
- `python -m demo_pkg` 运行的是包里的 `__main__.py`。

`python -m pytest`、`python -m pip` 也是同一个机制。好处是明确用**当前这个 python** 对应环境里的 pytest 和 pip，不会用到 PATH 里另一个 Python 的。

一个小坑：如果包的 `__init__.py` 已经导入了某个子模块（`demo_pkg/__init__.py` 导入了 `mathutils`），再用 `python -m demo_pkg.mathutils` 运行它，会看到 `RuntimeWarning: 'demo_pkg.mathutils' found in sys.modules ...`。原因是这个文件被执行了两次：一次作为 `demo_pkg.mathutils` 被导入，一次作为 `__main__` 运行。

### 2.9 为什么 main_fc.py 能 import FunctionCallingAgent

`example_agents/main_fc.py` 第一行业务 import 是 `from FunctionCallingAgent import FunctionCallingAgent, ToolRegistry`。`FunctionCallingAgent/` 这个包在 `example_agents/` 目录下面，所以 **`sys.path` 里必须有 `example_agents/`** 才找得到它：

| 运行方式 | `sys.path[0]` | 结果 |
|---|---|---|
| 在 `example_agents/` 下 `python main_fc.py` | `example_agents/` | 能导入 |
| 在仓库根目录 `python example_agents/main_fc.py` | 文件所在目录，还是 `example_agents/` | 也能导入 |
| 在仓库根目录 `python -m example_agents.main_fc` | 仓库根目录 | `ModuleNotFoundError: No module named 'FunctionCallingAgent'` |
| 在别的目录写一个新脚本 `import FunctionCallingAgent` | 新脚本所在目录 | 同样找不到 |

所以准确的说法是：决定能不能导入的是 `sys.path`，而 `python 某文件.py` 会把文件所在目录放进 `sys.path[0]`。说明里让你“进入 example_agents 目录再运行”，是最不容易出错的做法。`02_模块与包.py` 第 7 段用子进程验证了这一点。

不想依赖运行目录，有两种办法：临时设置 `PYTHONPATH=example_agents`；或者正式一点，把代码做成可安装的包（`pyproject.toml` 里配置构建系统），装进虚拟环境，之后在哪里都能 import。

### 2.10 循环导入

`demo_pkg/circular/a.py` 第一行 `from demo_pkg.circular.b import func_b`，`b.py` 第一行 `from demo_pkg.circular.a import func_a`。导入 `a` 的过程：

1. 创建模块 `a`，放进 `sys.modules`，开始执行 `a.py` 第一行，转去导入 `b`；
2. 执行 `b.py` 第一行，要从 `a` 里取 `func_a`；
3. `a` 已经在 `sys.modules` 里，但只执行到第一行，`func_a` 还没定义；
4. 报错：`ImportError: cannot import name 'func_a' from partially initialized module 'demo_pkg.circular.a' (most likely due to a circular import)`。

C++ 里两个头文件互相 include，靠 include guard 和前置声明解决。Python 的解决办法：

1. **把两边都要用的代码抽到第三个模块里**，打破环。这是首选。
2. 把 import 挪进函数体内，用到时才导入。这时两个模块都已经执行完了。
3. 如果只是类型标注需要对方的类，用 `from typing import TYPE_CHECKING`，把 import 写在 `if TYPE_CHECKING:` 下面，运行时不会执行。

循环导入通常说明模块的职责划分有问题，优先用第 1 种。

### 2.11 面试怎么问

1. import 一个模块时 Python 做了哪些事？为什么第二次 import 不会重新执行？
2. `if __name__ == "__main__":` 有什么作用？
3. 什么是循环导入？报错的原因是什么？怎么解决？
4. `python xxx.py` 和 `python -m xxx` 有什么区别？

---

## 3. 工程化：虚拟环境、uv、ruff、pytest、logging（P0-11）

### 3.1 虚拟环境

不同项目需要的包版本可能冲突，比如项目 A 要 pydantic 1.x，项目 B 要 2.x。虚拟环境就是**一个独立的 site-packages 目录，加上一个指向某个 Python 解释器的入口**。激活哪个环境，`python` 和 `import` 就用哪套包。可以类比 Qt Creator 里给不同项目选不同的 Kit（Qt 版本 + 编译器）。

| | conda 环境 | venv（uv 创建的 `.venv` 也是这种） |
|---|---|---|
| 管理什么 | Python 解释器本身 + 包 + 非 Python 依赖（如 CUDA、MKL） | 只管包，复用一个已有的 Python 解释器 |
| 放在哪 | conda 安装目录下的 `envs/` | 通常在项目目录里，叫 `.venv` |
| 怎么判断 | `sys.prefix` 指向 conda 目录 | `sys.prefix != sys.base_prefix` |

你现在用的 `python` 是 conda 的 base 环境（`03_工程化.py` 第 1 段会打印出来）。在 scratch 里用 uv 创建项目后，`uv run` 用的是 scratch 自己的 `.venv`，里面的包和 conda 互不影响。

`.venv` 目录不要提交到 git（仓库的 `.gitignore` 已经忽略），别人拿到代码后用 `uv sync` 重建。

### 3.2 uv：项目和依赖管理

uv 一个工具代替了 `pip`、`venv`、`pip-tools` 等，速度很快，现在新项目用得很多。命令行在 `/opt/homebrew/bin/uv`。

**实操（在本课目录下）：**

```bash
cd P0_python基础/lesson04_类型与工程化
uv init scratch          # 新建 scratch 目录，生成项目骨架
cd scratch
ls -a                    # .python-version  README.md  main.py  pyproject.toml
uv run main.py           # 第一次运行会自动创建 .venv 和 uv.lock，然后输出 Hello from scratch!
uv add pydantic          # 添加依赖：写进 pyproject.toml，更新 uv.lock，装进 .venv
uv add --dev pytest      # 添加开发依赖（只有开发时需要，比如测试工具）
cat pyproject.toml       # 看看多了什么
uv run python -c "import sys, pydantic; print(sys.executable, pydantic.VERSION)"
python -c "import sys, pydantic; print(sys.executable, pydantic.VERSION)"   # 对比 conda 环境：解释器路径不同，pydantic 版本通常也不同
uv tree                  # 依赖树
uv remove pydantic       # 删除依赖
rm -rf .venv && uv sync  # 删掉环境，再按 uv.lock 原样重建
```

注意：

- 在 git 仓库里运行 `uv init`，它不会再创建 `.git` 和 `.gitignore`；在 git 仓库外运行，它会顺便执行 `git init`。
- 仓库的 `.gitignore` 只忽略了 `.venv`，scratch 里的 `pyproject.toml`、`uv.lock`、`main.py` 会出现在 `git status` 里。练完删掉 `scratch` 目录，不要提交。
- `uv run 命令` 会先检查环境和 `uv.lock` 是否同步，必要时自动安装，然后在 `.venv` 里执行命令。不需要手动激活虚拟环境。
- 下载慢可以换国内镜像，例如 `export UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`。

**常用命令：**

| 命令 | 作用 |
|---|---|
| `uv init 目录名` | 新建项目 |
| `uv add 包名`、`uv add "pydantic>=2.7"` | 添加依赖 |
| `uv add --dev 包名` | 添加开发依赖 |
| `uv remove 包名` | 删除依赖 |
| `uv sync` | 让 `.venv` 和 `uv.lock` 一致 |
| `uv lock` | 只更新 `uv.lock`，不安装 |
| `uv run 命令` | 在项目环境里运行命令 |
| `uv tree` | 显示依赖树 |
| `uvx 工具名`（等价 `uv tool run`） | 在一个临时的独立环境里运行命令行工具，不装进项目，例如 `uvx ruff check` |
| `uv export --format requirements-txt` | 导出成 requirements.txt 格式 |
| `uv pip install ...` | 兼容 pip 的用法，用于老项目 |

**pyproject.toml 各字段**（`uv add` 之后的样子）：

```toml
[project]
name = "scratch"                          # 项目名
version = "0.1.0"                         # 版本号
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"                # 支持的 Python 版本
dependencies = [                          # 运行时依赖，uv add 写到这里
    "pydantic>=2.14.3",                   # 下限是 uv add 时的最新版，你那里可能不同
]

[dependency-groups]
dev = [                                   # 开发依赖，uv add --dev 写到这里
    "pytest>=9.2.0",
]

[tool.ruff]                               # [tool.xxx] 是各个工具自己的配置
line-length = 100
```

| 字段 | 说明 |
|---|---|
| `[project]` | 项目元数据和依赖，是 Python 官方标准（PEP 621），不只 uv 认 |
| `dependencies` | 依赖要求。`>=2.7` 至少 2.7；`==2.11.7` 固定版本；`~=2.11` 表示 `>=2.11` 且 `<3` |
| `[dependency-groups]` | 依赖分组，`dev` 组放测试、检查工具，部署时可以不装 |
| `[project.optional-dependencies]` | 可选功能的依赖，安装时用 `包名[功能名]` 选装 |
| `[build-system]` | 构建成可安装包时用。`uv init` 默认生成的是应用项目，没有这一段；`uv init --package` 会生成，还会生成 `src/` 目录结构和 `[project.scripts]` |
| `[tool.ruff]`、`[tool.pytest.ini_options]` | 工具配置，集中在一个文件里 |

**`pyproject.toml` 和 `uv.lock` 的区别：** `pyproject.toml` 写的是“要求”（`pydantic>=2.7`），人来维护；`uv.lock` 记录的是解析后**整棵依赖树的确切版本和哈希值**，uv 自动生成，不要手改。两者都要提交到 git，这样别人 `uv sync` 得到的环境和你完全一样。如果用过 npm，对应 `package.json` 和 `package-lock.json`。

### 3.3 ruff：代码检查和格式化

ruff 一个工具同时做两件事，可以类比 clang-tidy 加 clang-format：

```bash
uvx ruff check .            # 检查问题（未使用的 import、变量、== None 等）
uvx ruff check --fix .      # 自动修复能安全修复的问题
uvx ruff format .           # 按统一风格格式化代码，直接改文件
uvx ruff format --check .   # 只检查格式，不改文件（适合 CI）
uvx ruff format --diff .    # 显示会怎么改
```

在 scratch 里新建一个 `bad.py` 试一下：

```python
import os, sys
def f( x ):
    y = 1
    return x+1
l = [1,2,
3]
if f(1) == None:
    pass
```

ruff 默认启用哪些规则，不同版本不一样。本机 `uvx` 拿到的 ruff 0.17.4，在没有配置时只报 `I001`、`F401`、`F841`。项目里应该在 `pyproject.toml` 里明确写出要启用的规则，团队每个人的检查结果才一致。在 scratch 的 `pyproject.toml` 末尾加上：

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I"]    # pycodestyle 错误、pyflakes、import 排序
```

再运行 `uvx ruff check bad.py`，会多出 `E401`、`E711`、`E741`：

| 规则代码 | 含义 |
|---|---|
| `F401` | import 了但没用 |
| `F841` | 局部变量赋值了但没用 |
| `E401` | 一行 import 了多个模块 |
| `E711` | 用 `== None` 比较，应该用 `is None` |
| `E741` | 变量名 `l`、`O`、`I` 容易和数字混淆 |
| `I001` | import 没有排序 |

`--fix` 只自动修复安全的问题（比如删掉没用的 import）。`F841`、`E711` 的修复可能改变程序行为，ruff 标为 unsafe，需要 `--fix --unsafe-fixes` 才会修，一般自己看过再改。

某一行确实要违反规则时，在行尾加 `# noqa: 规则代码`，`02_模块与包.py` 里就有 `# noqa: E402`。

ruff 会在运行目录生成 `.ruff_cache/`，已被 `.gitignore` 忽略。

### 3.4 pytest

可以类比 Qt Test：`QCOMPARE` 对应 `assert`，数据驱动测试的 `xxx_data()` 函数对应 `parametrize`，`init()`/`cleanup()` 对应 fixture。

**运行：**

```bash
python -m pytest tests -q                          # 本课示例测试
python -m pytest tests/test_mathutils.py -v        # 一个文件，-v 显示每个用例
python -m pytest tests -k clamp                    # 只跑名字里含 clamp 的用例
python -m pytest tests/test_config.py::test_load_config   # 只跑一个用例
python -m pytest tests -x                          # 遇到第一个失败就停
```

`-s` 让测试里的 `print` 直接显示出来（默认会被捕获，只有失败时才显示）。

**为什么要写 `python -m pytest` 而不是 `pytest`：** 在本课目录下直接运行 `pytest tests` 会报 `ModuleNotFoundError: No module named 'demo_pkg'`。`python -m` 会把当前目录放进 `sys.path`，所以能找到 `demo_pkg`。直接运行 `pytest` 时，pytest 默认把测试文件所在的目录往上找到的第一个没有 `__init__.py` 的目录（这里是 `tests/`）放进 `sys.path`，本课目录不在里面。

**测试发现规则：**

- 文件名是 `test_*.py` 或 `*_test.py`；
- 文件里名字以 `test` 开头的函数；
- 名字以 `Test` 开头、没有 `__init__` 方法的类里，名字以 `test` 开头的方法。
- 在命令行里直接写出文件名时，文件名不符合规则也会被收集。`练习_test_chunk.py` 就是这样：`python -m pytest tests` 不会跑它，`python -m pytest 练习_test_chunk.py` 会。

**基本写法（见 `tests/test_mathutils.py`）：**

```python
import pytest
from demo_pkg.mathutils import clamp, mean

def test_mean_basic():
    assert mean([1, 2, 3]) == 2                # 直接写 assert，失败时 pytest 会显示两边的值

def test_mean_float():
    assert mean([0.1, 0.2]) == pytest.approx(0.15)   # 浮点数用 approx

def test_mean_empty_raises():
    with pytest.raises(ValueError, match="不能为空"):  # 断言一定抛这个异常；match 是正则
        mean([])

@pytest.mark.parametrize(("value", "expected"), [(5, 5), (-1, 0), (99, 10)])
def test_clamp(value, expected):               # 每组数据是一个独立的用例
    assert clamp(value, 0, 10) == expected
```

`pytest.raises` 也可以写成 `with pytest.raises(ValidationError) as exc_info:`，之后用 `exc_info.value` 拿到异常对象，检查里面的内容（见 `tests/test_config.py`）。

**fixture：给测试准备数据或资源（见 `tests/conftest.py`、`tests/test_config.py`）：**

```python
@pytest.fixture
def config_dict():
    return {"model": "qwen-plus", "temperature": 0.3}

def test_config_defaults(config_dict):     # 参数名和 fixture 同名，pytest 自动调用并传进来
    ...
```

- 默认每个测试都重新调用一次 fixture，测试之间互不影响。
- 写在 `conftest.py` 里的 fixture，同目录和子目录下的测试文件都能直接用，不需要 import。
- fixture 里用 `yield` 代替 `return`，`yield` 之后的代码在测试结束后执行，用来清理资源，类似第二课的 `with`。
- 常用的内置 fixture：`tmp_path`（每个测试一个独立的临时目录，`pathlib.Path` 类型）、`caplog`（捕获日志）、`monkeypatch`（临时替换属性、环境变量）。

### 3.5 logging

**为什么不用 print：** `print` 没有级别，上线后没法只关掉调试信息；不能按模块控制；没有时间、模块名这些上下文；只能输出到 stdout。线上排查问题全靠日志，面试时写 `print` 调试会被认为缺少工程经验。

和 Qt 对照：

| Qt | Python logging |
|---|---|
| `qDebug()` `qInfo()` `qWarning()` `qCritical()` | `logger.debug()` `info()` `warning()` `error()` / `critical()` |
| `QLoggingCategory("app.net")` | `logging.getLogger("app.net")`，名字用 `.` 分层 |
| `qInstallMessageHandler`、`QT_MESSAGE_PATTERN` | handler 和 format，通常用 `logging.basicConfig` 配置 |

**级别**（从低到高）：`DEBUG`(10) < `INFO`(20) < `WARNING`(30) < `ERROR`(40) < `CRITICAL`(50)。logger 只输出不低于自己级别的日志。根 logger 默认是 `WARNING`，所以不配置的话 `info()` 什么都不输出。

**惯用写法：**

```python
# 库模块里（例如 demo_pkg/config.py）：只创建 logger，不做配置
import logging
logger = logging.getLogger(__name__)      # 名字是 "demo_pkg.config"

def load_config(path):
    logger.debug("读取配置文件 %s", path)   # 用 %s 占位，参数交给 logging

# 程序入口（main 函数里）：配置一次
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
```

- `basicConfig` 只在根 logger 还没有 handler 时生效，第二次调用默认什么都不做（需要覆盖时传 `force=True`）。所以只在程序入口调用一次，库代码里不要调用。
- 用 `logger.info("x=%s", x)` 而不是 f-string：级别不够时直接跳过，不会白白拼接字符串。
- 在 `except` 里用 `logger.exception("说明")`，它按 ERROR 级别记录，并自动附上完整的 traceback。
- logger 按名字分层：`logging.getLogger("demo_pkg").setLevel(logging.ERROR)` 会同时影响 `demo_pkg.config`，不影响其他 logger。
- 默认输出到 stderr。常用格式字段：`%(asctime)s` 时间、`%(levelname)s` 级别、`%(name)s` logger 名、`%(message)s` 内容、`%(filename)s:%(lineno)d` 位置。
- 不要把 API Key、用户隐私写进日志。

### 3.6 面试怎么问

1. 为什么要用虚拟环境？conda 环境和 venv 有什么区别？
2. `pyproject.toml` 和 `uv.lock` 分别是做什么的？`uv.lock` 要不要提交到 git？
3. pytest 的 fixture 是什么？和 unittest 的 setUp/tearDown 相比有什么好处？
4. 线上服务为什么用 logging 而不是 print？日志级别怎么选？

---

## 练习说明

| 题号 | 知识点 | 内容 |
|---|---|---|
| 练习 1 | P0-09 | 定义带 Field 约束的工具参数模型 `KbSearchArgs` |
| 练习 2 | P0-09 | `to_openai_tool`：从模型生成 OpenAI tools 格式的 schema |
| 练习 3 | P0-09 | `parse_tool_args`：解析模型返回的 JSON 参数，失败时返回可读的错误说明 |
| 练习 4 | P0-09 | 带 `field_validator` 的 `ChatMessage` 模型 |
| 练习 5 | P0-10 | `import_from_string`：按 `"模块:属性"` 字符串导入对象 |
| 练习 6 | P0-11 | 在 `练习_test_chunk.py` 里给 `demo_pkg/chunking.py` 的 `chunk_text` 写 pytest 测试 |

练习 6 的检查方式：`python 练习.py` 会在子进程里运行你的测试，先用正确的 `chunk_text`，要求全部通过；再把 `chunk_text` 依次换成几种常见的错误实现，要求每一种都至少让一个测试失败。没被发现的错误实现会在结果里列出来，提示你还缺哪类用例。写测试时可以先单独运行 `python -m pytest 练习_test_chunk.py -q`。

---

## 读完后的自查

下面的问题能不看资料答出来，再开始做练习：

1. `def f(x: int)` 传入 `"1"` 会怎样？换成 Pydantic 模型里的 `int` 字段呢？开启 strict 模式呢？
2. 怎样用一个 Pydantic 模型同时得到工具参数的 JSON Schema 和对模型返回参数的校验？分别用哪个方法？校验失败时，`e.errors()` 里的 `loc` 和 `msg` 各是什么？
3. import 一个模块时发生了什么？`sys.modules` 起什么作用？循环导入为什么会报 “partially initialized module”？
4. 为什么在本课目录下 `python demo_pkg/tools/stats.py` 报错，`python -m demo_pkg.tools.stats` 却可以？`pytest tests` 和 `python -m pytest tests` 的结果为什么不同？
5. `pyproject.toml`、`uv.lock`、`.venv` 分别是什么？哪些要提交到 git？
