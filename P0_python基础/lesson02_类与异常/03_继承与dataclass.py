"""P0-05 继承、super()、MRO、鸭子类型、抽象基类、dataclass。运行：python 03_继承与dataclass.py"""
from abc import ABC, abstractmethod
from dataclasses import FrozenInstanceError, dataclass, field, fields, replace


def section(title):
    print(f"\n===== {title} =====")


section("1. 子类定义了 __init__，父类的 __init__ 不会自动调用")


class Tool:
    def __init__(self, name):
        self.name = name
        self.calls = 0


class ForgetSuper(Tool):
    def __init__(self, timeout):
        self.timeout = timeout  # 忘了调用 super().__init__，name 和 calls 都没有设置


class SearchTool(Tool):
    def __init__(self, timeout):
        super().__init__("search")  # 显式调用父类初始化，相当于 C++ 初始化列表里的 Base(...)
        self.timeout = timeout


print("ForgetSuper 的属性:", vars(ForgetSuper(3)))
print("SearchTool 的属性:", vars(SearchTool(3)))


class EchoTool(Tool):
    pass  # 子类没写 __init__ 时，直接继承父类的 __init__


print("EchoTool 的属性:", vars(EchoTool("echo")))

section("2. 所有方法都可以被子类重写，效果相当于 C++ 的虚函数")


class BaseAgent:
    def run(self, task):
        return f"[{self.name()}] 处理: {task}"  # self.name() 会调用子类的版本

    def name(self):
        return "base"


class PlanAgent(BaseAgent):
    def name(self):  # 不需要 virtual 或 override 关键字
        return "plan"

    def run(self, task):
        return super().run(task) + "（先思考再行动）"  # super() 调用父类版本


print(BaseAgent().run("查天气"))
print(PlanAgent().run("查天气"))

section("3. 多继承与 MRO：super() 找的是 MRO 里的下一个类，不一定是直接父类")


class A:
    def hello(self):
        return ["A"]


class B(A):
    def hello(self):
        return ["B"] + super().hello()


class C(A):
    def hello(self):
        return ["C"] + super().hello()


class D(B, C):  # 菱形继承：D -> B, C -> A
    def hello(self):
        return ["D"] + super().hello()


print("D.__mro__:", [k.__name__ for k in D.__mro__])  # D, B, C, A, object
print("D().hello():", D().hello())  # B 里的 super() 调到的是 C，不是 A；A 只调用一次

section("4. 鸭子类型：不看类型，只看有没有需要的方法")


class Calculator:  # 和 Tool 没有任何继承关系
    def run(self, expression):
        return f"{expression} 的计算结果"


class Weather:
    def run(self, expression):
        return f"{expression} 的天气"


def execute(tool, arg):
    return tool.run(arg)  # 只要求 tool 有 run 方法，不要求有公共基类


for t in [Calculator(), Weather()]:
    print(execute(t, "北京"))
try:
    execute("不是工具", "北京")
except AttributeError as e:
    print("AttributeError:", e)  # 错误发生在调用时，而不是像 C++ 那样在编译时

section("5. 抽象基类：没实现全部抽象方法的类不能实例化")


class BaseTool(ABC):
    @abstractmethod
    def run(self, **kwargs):  # 相当于 C++ 的纯虚函数 virtual ... = 0
        ...

    def __call__(self, **kwargs):  # 抽象基类里也可以有普通方法
        return str(self.run(**kwargs))


class Incomplete(BaseTool):
    pass


class AddTool(BaseTool):
    def run(self, a, b):
        return a + b


for cls in [BaseTool, Incomplete]:
    try:
        cls()
    except TypeError as e:
        print("TypeError:", e)  # 检查发生在实例化时，定义 Incomplete 这个类本身不会报错
print("AddTool()(a=1, b=2) =", repr(AddTool()(a=1, b=2)))
print("isinstance(AddTool(), BaseTool):", isinstance(AddTool(), BaseTool))

section("6. dataclass：自动生成 __init__、__repr__、__eq__")


@dataclass
class ChatMessage:
    role: str  # 必须写类型标注，才算 dataclass 的字段
    content: str
    name: str | None = None  # 有默认值的字段必须放在没有默认值的字段后面
    tool_calls: list = field(default_factory=list)  # 可变默认值必须用 default_factory


m1 = ChatMessage("user", "你好")
m2 = ChatMessage("user", "你好")
print(m1)  # 自动生成的 __repr__
print("m1 == m2:", m1 == m2)  # 自动生成的 __eq__ 按字段逐个比较
m1.tool_calls.append("search")
print("m1.tool_calls =", m1.tool_calls, " m2.tool_calls =", m2.tool_calls)  # 每个实例有自己的列表
print("字段:", [f.name for f in fields(ChatMessage)])
print("ChatMessage.__hash__ =", ChatMessage.__hash__)  # eq=True 且不 frozen 时，__hash__ 被设为 None

try:
    @dataclass
    class Bad:
        items: list = []  # 和第一课的 def f(items=[]) 是同一个坑，dataclass 直接拒绝
except ValueError as e:
    print("ValueError:", e)


@dataclass
class NoAnnotation:
    x: int = 1
    y = 2  # 没有类型标注：只是普通的类属性，不是字段


print("NoAnnotation 的字段:", [f.name for f in fields(NoAnnotation)])

section("7. frozen dataclass：不可修改、可哈希")


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: tuple = ()


call = ToolCall("search", ("北京",))
try:
    call.name = "calc"
except FrozenInstanceError as e:
    print("FrozenInstanceError:", e)
print("可以放进 set:", len({ToolCall("search"), ToolCall("search")}))  # frozen 且 eq 时自动生成 __hash__
print("replace 生成修改后的新对象:", replace(call, name="calc"), " 原对象:", call)


@dataclass(frozen=True)
class Shallow:
    items: list = field(default_factory=list)


s = Shallow()
s.items.append(1)  # frozen 只禁止给字段重新赋值，字段指向的 list 仍然可以修改（和 tuple 里放 list 一样）
print("frozen 是浅层的:", s)
