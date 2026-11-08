"""P0-01 变量与引用语义。运行后对照输出读注释：python 01_引用语义.py"""
import copy


def section(title):
    print(f"\n===== {title} =====")


section("1. 赋值只是给对象贴名字，不复制对象")
a = [1, 2, 3]
b = a  # 相当于 C++ 里复制了一个 shared_ptr，vector 本身没有复制
b.append(4)
print("a =", a)  # a 也变了，因为 a 和 b 指向同一个对象
print("a is b:", a is b)
print("id(a) == id(b):", id(a) == id(b))  # id() 类似取地址

section("2. == 比较值，is 比较是不是同一个对象")
c = [1, 2, 3, 4]
print("a == c:", a == c)  # 值相等，类似调用 operator==
print("a is c:", a is c)  # 不是同一个对象，类似比较两个指针
x = None
print("判断 None 用 is:", x is None)  # is 基本只用于和 None 比较

section("3. 不可变对象：'修改'其实是创建新对象，再把名字指过去")
n = 10
m = n
n += 1  # int 不可变，这里创建了新对象 11，n 改为指向它
print("n =", n, " m =", m)  # m 还是 10
s = "hi"
t = s
s += "!"  # str 也不可变
print("s =", s, " t =", t)

section("4. 同样写 +=，list 原地修改，int/str/tuple 重新绑定")
l1 = [1]
l2 = l1
l1 += [2]  # list 的 += 等价于 extend，原地修改
print("l1 += [2] 之后 l2 =", l2)
l1 = l1 + [3]  # + 会创建新列表，l1 指向新对象，l2 不受影响
print("l1 = l1 + [3] 之后 l1 =", l1, " l2 =", l2)

section("5. 函数传参：传的是对象引用，像按值传 shared_ptr")


def mutate(items):
    items.append("改了")  # 修改对象本身，调用方能看到


def rebind(items):
    items = ["新列表"]  # 只是让局部名字指向新对象，调用方看不到


data = ["原始"]
mutate(data)
rebind(data)
print("data =", data)

section("6. 浅拷贝只复制最外层")
grid = [[1, 2], [3, 4]]
shallow = grid.copy()  # 等价写法：grid[:]、list(grid)、copy.copy(grid)
deep = copy.deepcopy(grid)
grid[0].append(99)
print("shallow =", shallow)  # 内层列表是共享的，所以也变了
print("deep    =", deep)  # 完全独立
print("shallow is grid:", shallow is grid, " shallow[0] is grid[0]:", shallow[0] is grid[0])

section("7. 经典陷阱：[[0] * 3] * 3")
bad = [[0] * 3] * 3  # 外层的 3 个元素指向同一个内层列表
bad[0][0] = 1
print("bad  =", bad)
good = [[0] * 3 for _ in range(3)]  # 每次循环都创建新的内层列表
good[0][0] = 1
print("good =", good)

section("8. tuple 本身不可变，但里面的 list 可以变")
tp = (1, [2, 3])
tp[1].append(4)
print("tp =", tp)
try:
    tp[0] = 100
except TypeError as e:
    print("TypeError:", e)
