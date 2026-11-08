"""P0-03 函数与参数。运行：python 03_函数参数.py"""


def section(title):
    print(f"\n===== {title} =====")


section("1. 返回多个值，实际上返回的是一个 tuple")


def min_max(values):
    return min(values), max(values)


lo, hi = min_max([3, 9, 1])
print("lo =", lo, " hi =", hi, " 原始返回值:", min_max([3, 9, 1]))


def no_return():
    pass


print("没写 return 时返回:", no_return())  # None

section("2. 位置参数和关键字参数")


def connect(host, port=8080, timeout=5.0):
    return f"{host}:{port} timeout={timeout}"


print(connect("localhost"))
print(connect("localhost", timeout=1.0))  # 跳过 port，直接指定 timeout
print(connect(port=9000, host="example.com"))  # 关键字参数可以不按顺序

section("3. * 后面的参数只能用关键字传")


def create_client(model, *, temperature=0.7, stream=False):
    return f"model={model} temperature={temperature} stream={stream}"


print(create_client("qwen", temperature=0))
try:
    create_client("qwen", 0.5)  # 0.5 是什么意思？强制关键字参数就是为了避免这种写法
except TypeError as e:
    print("TypeError:", e)

section("4. 默认参数陷阱：默认值只在 def 执行时计算一次")


def add_bad(item, items=[]):
    items.append(item)
    return items


print(add_bad(1))
print(add_bad(2))  # 期望 [2]，实际是 [1, 2]
print("默认值被保存在函数对象上:", add_bad.__defaults__)


def add_good(item, items=None):
    if items is None:  # 惯用写法：用 None 当默认值，在函数内部创建新对象
        items = []
    items.append(item)
    return items


print(add_good(1), add_good(2))

section("5. *args 收集多余的位置参数，**kwargs 收集多余的关键字参数")


def log(level, *args, **kwargs):
    print(f"  level={level!r} args={args} kwargs={kwargs}")


log("INFO")
log("INFO", "启动", 42, user="hq", retry=3)

section("6. 调用时解包：* 展开序列，** 展开字典")


def calculate(expression, precision=2):
    return f"计算 {expression}，保留 {precision} 位"


arguments = {"expression": "1 + 2", "precision": 4}  # 模型返回的工具参数解析后就是这样的 dict
print(calculate(**arguments))  # 等价于 calculate(expression="1 + 2", precision=4)
pair = ["3 * 4", 1]
print(calculate(*pair))  # 等价于 calculate("3 * 4", 1)
# 仓库里 example_agents/FunctionCallingAgent/tools.py 的 tool["func"](**arguments) 就是这个用法

section("7. 函数是对象：可以存进 dict，按名字调用（类似 std::function）")


def add(a, b):
    return a + b


tools = {"add": add, "mul": lambda a, b: a * b}
for name in ["add", "mul"]:
    print(f"  {name}(3, 4) = {tools[name](3, 4)}")

section("8. 没有函数重载：同名函数后定义的会覆盖前面的")


def greet(name):
    return f"你好，{name}"


def greet(name, title):  # noqa: F811  这里是故意重复定义
    return f"你好，{title}{name}"


try:
    greet("小罗")
except TypeError as e:
    print("TypeError:", e)
print("Python 用默认参数代替重载，例如 connect() 的 port 和 timeout")
