"""P0-09 类型标注与 Pydantic v2。运行：python 01_类型标注与Pydantic.py"""

import json
from typing import (
    Callable,
    Literal,
    Optional,
    TypedDict,
    TypeVar,
    Union,
    get_type_hints,
)

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


def section(title):
    print(f"\n===== {title} =====")


section("1. 类型标注在运行时不检查")


def add(a: int, b: int) -> int:
    return a + b


# C++ 里这行编译不过；Python 照样运行，结果是字符串拼接
print('add("1", "2") =', repr(add("1", "2")))
# 标注只是存在函数对象上的元数据，给 IDE、mypy/pyright 和 Pydantic 这类库读取
print("add.__annotations__ =", add.__annotations__)

section("2. 常用标注写法")

scores: dict[str, list[int]] = {
    "qt": [90, 85]
}  # 3.9 起内置容器可以直接写 list[int]、dict[str, X]
maybe_name: str | None = None  # 3.10 起的写法，等价于 Optional[str]
id_or_name: int | str = 42  # 等价于 Union[int, str]
print("Optional[int] == int | None:", Optional[int] == (int | None))
print("Union[int, str] == int | str:", Union[int, str] == (int | str))

# Callable[[参数类型...], 返回类型]，类似 std::function<std::string(const std::string&)>
Handler = Callable[[str], str]


def run_handler(handler: Handler, text: str) -> str:
    return handler(text)


print("run_handler(str.upper, 'qt') =", run_handler(str.upper, "qt"))

# Literal：只能取这几个值，类似一个轻量的 enum
Role = Literal["system", "user", "assistant", "tool"]


def make_message(role: Role, content: str) -> dict[str, str]:
    return {"role": role, "content": content}


print(make_message("user", "你好"))
print("运行时同样不检查 Literal：", make_message("boss", "随便写也不报错"))  # type: ignore[arg-type]


# TypedDict：给 dict 标注每个键的类型。运行时它就是普通 dict
class ChatMessage(TypedDict):
    role: Role
    content: str


msg: ChatMessage = {"role": "user", "content": "hi"}
print("TypedDict 实例的真实类型:", type(msg).__name__)
print("get_type_hints(ChatMessage) =", get_type_hints(ChatMessage))

section("3. 简单泛型：让返回类型跟着参数类型走")

T = TypeVar("T")  # 老写法，现有代码里大量使用


def first_old(items: list[T]) -> T:
    return items[0]


def first[U](items: list[U]) -> U:  # 3.12 起的新写法，类似 template <typename U>
    return items[0]


# 静态检查器会推断出 first([1, 2]) 是 int，first(["a"]) 是 str；运行时两者没有区别
print(first_old([1, 2]), first(["a", "b"]))

section("4. Pydantic BaseModel：按标注在运行时校验和转换")


class User(BaseModel):
    name: str
    age: int
    tags: list[
        str
    ] = []  # Pydantic 会给每个实例复制一份默认值，不会出现第一课的"可变默认参数"问题


u = User(name="hq", age="18")  # 默认是宽松（lax）模式："18" 能转成 int
print(repr(u))
print("age 的类型:", type(u.age).__name__)
a, b = User(name="a", age=1), User(name="b", age=2)
a.tags.append("x")
print("b.tags 不受 a 影响:", b.tags)

for bad in [{"name": "hq", "age": "abc"}, {"name": "hq", "age": 18.5}, {"name": "hq"}]:
    try:
        User(**bad)
    except ValidationError as e:
        err = e.errors()[0]
        print(f"  输入 {bad} -> type={err['type']}, msg={err['msg']}")


class StrictUser(BaseModel):
    model_config = ConfigDict(strict=True)  # 严格模式：不做类型转换
    age: int


try:
    StrictUser(age="18")
except ValidationError as e:
    print("strict 模式拒绝 '18':", e.errors()[0]["msg"])

section("5. Field 约束，以及怎么读 ValidationError")


class WeatherArgs(BaseModel):
    city: str = Field(min_length=1, description="城市名，例如 北京")
    days: int = Field(default=1, ge=1, le=7, description="预报天数，1 到 7")
    unit: Literal["celsius", "fahrenheit"] = "celsius"


try:
    WeatherArgs(city="", days=10, unit="kelvin")
except ValidationError as e:
    print(f"一共 {e.error_count()} 个错误。str(e) 的样子：")
    print(e)
    print("用 e.errors() 逐条读取（loc 是字段路径，msg 是原因，type 是错误类型）：")
    for err in e.errors():
        print(f"  loc={err['loc']} type={err['type']} msg={err['msg']}")

section("6. 嵌套模型，四个最常用的方法")


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, str | int | float]


class AssistantReply(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] = []


data = {"tool_calls": [{"name": "calculate", "arguments": {"expression": "1+2"}}]}
reply = AssistantReply.model_validate(data)  # dict -> 对象
print("model_validate:", repr(reply))
print(
    "嵌套字段是对象，不是 dict:",
    type(reply.tool_calls[0]).__name__,
    reply.tool_calls[0].name,
)

reply2 = AssistantReply.model_validate_json(
    '{"content": "你好"}'
)  # JSON 字符串 -> 对象
print("model_validate_json:", repr(reply2))
print("model_dump:", reply.model_dump())  # 对象 -> dict（嵌套对象也转成 dict）
print("model_dump_json:", reply2.model_dump_json())  # 对象 -> JSON 字符串

try:
    AssistantReply.model_validate(
        {"tool_calls": [{"name": "calc", "arguments": "1+2"}]}
    )
except ValidationError as e:
    print("嵌套字段出错时 loc 是完整路径:", e.errors()[0]["loc"])

try:
    AssistantReply.model_validate_json('{"content": "没写完')
except ValidationError as e:
    err = e.errors()[0]
    print(f"JSON 本身不合法: type={err['type']}, loc={err['loc']}")

section("7. field_validator：自定义校验和清洗")


class SearchArgs(BaseModel):
    query: str
    top_k: int = 5

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        # 默认 mode="after"：v 已经通过了 str 的类型校验
        v = v.strip()
        if not v:
            raise ValueError(
                "query 不能是空白"
            )  # 抛 ValueError，Pydantic 会把它包装进 ValidationError
        return v  # 返回值就是最终存进字段的值

    @field_validator("top_k", mode="before")
    @classmethod
    def parse_top_k(cls, v):
        # mode="before"：拿到的是原始输入，还没做类型校验
        if v == "all":
            return 100
        return v


print(repr(SearchArgs(query="  Qt 信号槽  ", top_k="all")))
try:
    SearchArgs(query="   ")
except ValidationError as e:
    print("validator 抛出的错误:", e.errors()[0]["msg"])

section("8. model_json_schema()：自动生成工具参数的 JSON Schema")

# 这是 example_agents/FunctionCallingAgent/builtin_tools.py 里手写的 CALCULATE_SCHEMA（原样复制）
HANDWRITTEN = {
    "type": "object",
    "properties": {
        "expression": {
            "type": "string",
            "description": "数学表达式，例如 '(3 + 5) * 2 ** 10'",
        }
    },
    "required": ["expression"],
}


class CalculateArgs(BaseModel):
    expression: str = Field(description="数学表达式，例如 '(3 + 5) * 2 ** 10'")


generated = CalculateArgs.model_json_schema()
print("Pydantic 生成的:", json.dumps(generated, ensure_ascii=False))
# 生成的版本多了 title 字段，其余部分和手写的一致
same = {
    "type": generated["type"],
    "required": generated["required"],
    "properties": {
        k: {kk: vv for kk, vv in v.items() if kk != "title"}
        for k, v in generated["properties"].items()
    },
}
print("去掉 title 后和手写的相同:", same == HANDWRITTEN)
print(
    "WeatherArgs 的 schema:",
    json.dumps(WeatherArgs.model_json_schema(), ensure_ascii=False),
)

# 同一个模型还能校验模型返回的参数。模型返回的 arguments 是 JSON 字符串
for arguments_json in ['{"expression": "1 + 2"}', '{"expr": "1 + 2"}']:
    try:
        args = CalculateArgs.model_validate_json(arguments_json)
        print(f"  {arguments_json} -> 校验通过, expression={args.expression!r}")
    except ValidationError as e:
        err = e.errors()[0]
        print(f"  {arguments_json} -> 校验失败: {err['loc']} {err['msg']}")

section("9. 结构化输出：给模型 schema，再用 Pydantic 校验模型的回复")


class Sentiment(BaseModel):
    label: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0, le=1)
    reason: str


# 第一步：把 schema 放进提示词（或者传给支持结构化输出的 API 参数）
prompt = "判断下面评论的情感，只输出符合这个 JSON Schema 的 JSON：\n" + json.dumps(
    Sentiment.model_json_schema(), ensure_ascii=False
)
print("提示词前 60 个字符:", prompt[:60], "...")

# 第二步：校验模型的回复。这里用写死的字符串代替真实的模型输出
fake_replies = [
    '{"label": "positive", "confidence": 0.92, "reason": "用户说很好用"}',
    '{"label": "好评", "confidence": 1.5, "reason": "..."}',
]
for text in fake_replies:
    try:
        result = Sentiment.model_validate_json(text)
        print("  通过:", repr(result))
    except ValidationError as e:
        # 真实项目里，通常把这些错误信息发回给模型，让它重新生成
        problems = "; ".join(
            f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()
        )
        print("  失败:", problems)
