"""P0-05 类的基础：self、__init__、访问控制、类属性、三种方法、@property。运行：python 01_类基础.py"""


def section(title):
    print(f"\n===== {title} =====")


section("1. self 就是显式写出来的 this")


class Counter:
    def __init__(self, start=0):
        self.value = start  # 必须写 self.value，单写 value 只是一个局部变量

    def increment(self, step=1):
        self.value += step
        return self.value


c = Counter()
c.increment()
print("c.increment() 之后 c.value =", c.value)
Counter.increment(c, 10)  # c.increment(10) 其实就是这样调用的：对象作为第一个参数传进去
print("Counter.increment(c, 10) 之后 c.value =", c.value)

section("2. __init__ 是初始化方法：对象已经创建好，它只负责往里面放属性")
# 属性不需要在类里声明，第一次给 self.xxx 赋值时才出现
print("vars(c) =", vars(c))  # vars() 返回实例的 __dict__，属性就存在这个 dict 里
c.note = "后来加的"  # 类外面也能随时加属性（C++ 做不到）
print("加了 note 之后 vars(c) =", vars(c))
c2 = Counter(5)
print("另一个实例 c2 有 note 吗:", hasattr(c2, "note"))  # False：属性属于单个实例，不属于类

section("3. 没有 private：_ 是约定，__ 只是改名字")


class Account:
    def __init__(self, owner, balance):
        self.owner = owner
        self._balance = balance  # 单下划线：约定为内部使用，但外面照样能访问
        self.__pin = "1234"  # 双下划线：会被改名成 _Account__pin


acc = Account("hq", 100)
print("acc._balance =", acc._balance)  # 能访问，只是约定上不该这样做
try:
    print(acc.__pin)
except AttributeError as e:
    print("AttributeError:", e)
print("vars(acc) =", vars(acc))  # 能看到改名后的 _Account__pin
print("acc._Account__pin =", acc._Account__pin)  # 知道名字照样能访问，所以它不是访问控制

section("4. 类属性被所有实例共享；类属性是可变对象时会出问题")


class BadAgent:
    tools = []  # 类属性：只有一份，挂在类上

    def add_tool(self, name):
        self.tools.append(name)  # 实例上没有 tools，于是找到类上的那一份并原地修改


a1 = BadAgent()
a2 = BadAgent()
a1.add_tool("search")
print("只给 a1 加了工具，a2.tools =", a2.tools)  # ['search']
print("a1.tools is a2.tools is BadAgent.tools:", a1.tools is a2.tools is BadAgent.tools)


class GoodAgent:
    max_steps = 5  # 不可变的类属性用作"所有实例共用的默认配置"没问题

    def __init__(self):
        self.tools = []  # 每个实例在 __init__ 里创建自己的列表


g1 = GoodAgent()
g2 = GoodAgent()
g1.tools.append("search")
print("g1.tools =", g1.tools, " g2.tools =", g2.tools)

g1.max_steps = 10  # 给实例赋值：在实例上新建一个同名属性，遮住类属性，不会改类属性
print("g1.max_steps =", g1.max_steps, " g2.max_steps =", g2.max_steps, " GoodAgent.max_steps =", GoodAgent.max_steps)
GoodAgent.max_steps = 8  # 改类属性：所有没有同名实例属性的对象都会看到新值
print("改类属性之后 g1.max_steps =", g1.max_steps, " g2.max_steps =", g2.max_steps)

section("5. 实例方法、@classmethod、@staticmethod")


class LLMConfig:
    def __init__(self, model, temperature=0.7):
        self.model = model
        self.temperature = temperature

    def describe(self):  # 实例方法：第一个参数是对象本身
        return f"{type(self).__name__}(model={self.model}, temperature={self.temperature})"

    @classmethod
    def from_dict(cls, data):  # 类方法：第一个参数是类本身，常用来写"另一个构造函数"
        return cls(data["model"], data.get("temperature", 0.7))  # 用 cls 而不是写死 LLMConfig

    @staticmethod
    def is_valid_temperature(t):  # 静态方法：既不需要对象也不需要类，相当于放在类里的普通函数
        return 0 <= t <= 2


class QwenConfig(LLMConfig):
    pass


print(LLMConfig.from_dict({"model": "qwen"}).describe())
print(QwenConfig.from_dict({"model": "qwen", "temperature": 0}).describe())  # cls 是 QwenConfig，所以创建的是子类对象
print("is_valid_temperature(3):", LLMConfig.is_valid_temperature(3))

section("6. @property：用属性的写法调用 getter/setter（类似 Q_PROPERTY）")


class ChatModel:
    def __init__(self, model, temperature=0.7):
        self._model = model
        self.temperature = temperature  # 这里已经在调用下面的 setter，初始化时也会校验

    @property
    def model(self):  # 只有 getter，没有 setter：只读属性
        return self._model

    @property
    def temperature(self):  # 读 obj.temperature 时调用
        return self._temperature

    @temperature.setter
    def temperature(self, value):  # 写 obj.temperature = x 时调用
        if not 0 <= value <= 2:
            raise ValueError(f"temperature 必须在 0 到 2 之间，收到 {value}")
        self._temperature = value  # 真正的数据存在 _temperature 里，不能再写 self.temperature，否则无限递归


m = ChatModel("qwen")
m.temperature = 0  # 调用方的写法和普通属性完全一样
print("m.temperature =", m.temperature)
try:
    m.temperature = 5
except ValueError as e:
    print("ValueError:", e)
try:
    m.model = "deepseek"
except AttributeError as e:
    print("AttributeError:", e)
print("vars(m) =", vars(m))  # 实例里存的是 _model 和 _temperature
