"""P0-04 作用域与闭包。运行后对照输出读注释：python 01_作用域与闭包.py"""
from functools import partial


def section(title):
    print(f"\n===== {title} =====")


section("1. LEGB：Local -> Enclosing -> Global -> Builtins")
x = "global x"  # G 层：模块顶层


def outer():
    x = "enclosing x"  # E 层：外层函数

    def inner():
        x = "local x"  # L 层：当前函数
        print("  inner 里看到:", x)  # 先找 L，找到就停

    def inner_no_local():
        print("  inner_no_local 里看到:", x)  # L 没有，往外找到 E

    inner()
    inner_no_local()


outer()
print("模块顶层看到:", x)  # 函数里的赋值不影响 G 层
print("len 来自 B 层:", len("abc"))  # 前三层都没有 len，最后在内置名字里找到

section("2. 内置名字可以被覆盖，变量名不要叫 list、dict、str")


def shadow_builtin():
    list = [1, 2]  # 这个函数里的 list 不再是内置类型了
    try:
        list("ab")  # 实际是在调用 [1, 2]("ab")
    except TypeError as e:
        print("TypeError:", e)


shadow_builtin()
print("函数外面的 list 不受影响:", list("ab"))

section("3. 没有块作用域：if/for 里定义的变量，出了块还在")
for i in range(3):
    last = i * 10
print("循环结束后 i =", i, " last =", last)  # C++ 里这里会编译失败
if True:
    inside_if = "if 里定义的"
print("if 结束后:", inside_if)
squares = [n * n for n in range(3)]
print("推导式有自己的作用域，n 不会泄漏:", "n" in globals())

section("4. 赋值让名字变成局部变量：UnboundLocalError")
count = 0


def bad_increment():
    count += 1  # 函数体里对 count 赋值，所以整个函数里 count 都是局部变量；读的时候还没赋值


try:
    bad_increment()
except UnboundLocalError as e:
    print("UnboundLocalError:", e)


def read_only():
    return count  # 只读不赋值，count 不是局部变量，按 LEGB 找到 G 层


print("只读全局变量没问题:", read_only())

section("5. global：在函数里重新绑定模块顶层的名字")


def good_increment():
    global count  # 声明后，这个函数里的 count 就是模块顶层的 count
    count += 1


good_increment()
good_increment()
print("count =", count)

section("6. nonlocal：在内层函数里重新绑定外层函数的名字")


def make_counter():
    n = 0

    def counter():
        nonlocal n  # 没有这一行，n += 1 同样会 UnboundLocalError
        n += 1
        return n

    return counter


c1 = make_counter()
c2 = make_counter()  # 每次调用 make_counter 都创建新的 n，两个计数器互不影响
print("c1:", c1(), c1(), c1())
print("c2:", c2())

section("7. 只修改可变对象，不需要 nonlocal")


def make_logger():
    lines = []  # 名字 lines 一直指向同一个 list，没有重新绑定

    def log(msg):
        lines.append(msg)  # 修改对象，不是给 lines 赋值
        return lines

    return log


log = make_logger()
log("第一条")
print("lines =", log("第二条"))

section("8. 闭包里保存的是什么：__closure__ 和 cell")
print("自由变量名:", c1.__code__.co_freevars)  # counter 用到的外层变量
print("cell 里的当前值:", c1.__closure__[0].cell_contents)  # c1 调用了 3 次，所以是 3
print("make_counter 已经返回，n 还活着，因为 cell 被 counter 引用着")

section("9. 闭包捕获的是变量，不是值")


def make_show():
    value = "旧值"

    def show():
        return value  # 调用 show 时才去读 value

    value = "新值"  # 创建 show 之后才改的
    return show


print("show() 返回:", make_show()())  # 新值。C++ 的 [=] 会得到旧值，[&] 会得到新值但这里会悬空

section("10. 晚绑定陷阱：循环里创建 lambda")
funcs = [lambda: i for i in range(3)]  # 三个 lambda 捕获的是推导式里同一个变量 i
print("期望 [0, 1, 2]，实际:", [f() for f in funcs])  # 调用时 i 已经是 2
print("三个函数共享同一个 cell:", funcs[0].__closure__[0] is funcs[2].__closure__[0])

section("11. 修复方法 1：默认参数在创建时求值")
funcs = [lambda i=i: i for i in range(3)]  # 每个 lambda 的默认值是创建时的 i
print("默认参数:", [f() for f in funcs])
print("副作用：调用方可以覆盖它:", funcs[0](99))

section("12. 修复方法 2：工厂函数，每次调用创建新的作用域")


def make_getter(i):
    return lambda: i  # 这个 i 是 make_getter 的参数，每次调用都是一个新变量


funcs = [make_getter(i) for i in range(3)]
print("工厂函数:", [f() for f in funcs])

section("13. 修复方法 3：functools.partial 提前绑定参数")
funcs = [partial(lambda i: i, i) for i in range(3)]  # partial 创建时就把 i 的值存了下来
print("partial:", [f() for f in funcs])
