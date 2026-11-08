"""P0-05 魔术方法：Python 的"运算符重载"。运行：python 02_魔术方法.py"""


def section(title):
    print(f"\n===== {title} =====")


section("1. __repr__ 给开发者看，__str__ 给用户看")


class Plain:
    def __init__(self, x):
        self.x = x


p = Plain(1)
# 默认的 repr 形如 <__main__.Plain object at 0x...>，地址每次运行都不同，这里只打印开头
print("默认 repr 的开头:", repr(p).split(" at ")[0])


class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def __repr__(self):  # 约定：尽量写成"能看出怎么构造这个对象"的样子，用 !r 给字符串加引号
        return f"Message({self.role!r}, {self.content!r})"

    def __str__(self):
        return f"{self.role}: {self.content}"


msg = Message("user", "你好")
print(msg)  # print 和 str() 用 __str__
print(f"{msg}")  # f-string 默认也用 __str__
print(f"{msg!r}")  # !r 强制用 __repr__
print([msg])  # 容器显示元素时用的是元素的 __repr__


class OnlyRepr:
    def __repr__(self):
        return "OnlyRepr()"


print("只定义 __repr__ 时，str() 也会用它:", str(OnlyRepr()))

section("2. __eq__ 和 __hash__ 必须一起考虑")


class NoEq:
    def __init__(self, x):
        self.x = x


print("没定义 __eq__，== 比较的是身份:", NoEq(1) == NoEq(1))


class EqOnly:
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        if not isinstance(other, EqOnly):
            return NotImplemented  # 不认识的类型交给 Python 处理，不要直接抛异常
        return self.x == other.x


print("定义了 __eq__ 之后:", EqOnly(1) == EqOnly(1))
print("EqOnly(1) == 1:", EqOnly(1) == 1)  # 双方都返回 NotImplemented，最后退回到身份比较，结果 False
print("!= 自动取反:", EqOnly(1) != EqOnly(2))  # 不用另写 __ne__
print("EqOnly.__hash__ =", EqOnly.__hash__)  # 只定义 __eq__，Python 会把 __hash__ 设为 None
try:
    {EqOnly(1)}
except TypeError as e:
    print("TypeError:", e)  # 不能放进 set，也不能当 dict 的键


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):  # 规则：相等的对象哈希值必须相等。做法是对参与比较的字段组成的 tuple 求哈希
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


points = {Point(1, 2), Point(1, 2), Point(3, 4)}
print("set 去重后的个数:", len(points))
print("用新建的 Point(1, 2) 当键查 dict:", {Point(1, 2): "A"}[Point(1, 2)])

section("3. __lt__ 让 sorted() 能工作")


class Version:
    def __init__(self, major, minor):
        self.major = major
        self.minor = minor

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor) < (other.major, other.minor)  # tuple 按字典序比较

    def __repr__(self):
        return f"Version({self.major}, {self.minor})"


vs = [Version(1, 10), Version(1, 2), Version(0, 9)]
print("sorted:", sorted(vs))  # sorted 只用到 <
print("Version(2, 0) > Version(1, 0):", Version(2, 0) > Version(1, 0))  # 没有 __gt__ 时，Python 改用 b.__lt__(a)
try:
    Version(1, 0) <= Version(1, 0)  # <= 对应 __le__，没定义，反过来的 __ge__ 也没定义
except TypeError as e:
    print("TypeError:", e)
# 需要全部 6 个比较运算符时，可以用 functools.total_ordering，只写 __eq__ 和 __lt__

section("4. __len__、__getitem__、__contains__：让对象像容器一样用")


class Playlist:
    def __init__(self, songs):
        self._songs = list(songs)  # 复制一份，不和调用方共享列表（第一课的内容）

    def __len__(self):
        return len(self._songs)

    def __getitem__(self, index):  # 直接转给 list，下标、负数下标、切片都支持
        return self._songs[index]

    def __contains__(self, song):
        return song in self._songs


pl = Playlist(["a", "b", "c"])
print("len(pl) =", len(pl))
print("pl[0] =", pl[0], " pl[-1] =", pl[-1], " pl[0:2] =", pl[0:2])
print("'b' in pl:", "b" in pl)
print("for 循环:", [s for s in pl])  # 没定义 __iter__ 时，for 会从 0 开始调用 __getitem__，直到 IndexError
print("bool(Playlist([])):", bool(Playlist([])))  # 没定义 __bool__ 时，用 __len__() != 0 判断真假

section("5. __add__、__mul__、__rmul__：算术运算符")


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)  # 返回新对象，不修改 self

    def __mul__(self, k):  # v * 3
        if not isinstance(k, (int, float)):
            return NotImplemented
        return Vector(self.x * k, self.y * k)

    def __rmul__(self, k):  # 3 * v：int 的 __mul__ 不认识 Vector，返回 NotImplemented，Python 再调用 v.__rmul__(3)
        return self.__mul__(k)

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"


v = Vector(1, 2)
print("v + Vector(10, 20) =", v + Vector(10, 20))
print("v * 3 =", v * 3, " 3 * v =", 3 * v)
print("v 没有被修改:", v)
try:
    v + 1
except TypeError as e:
    print("TypeError:", e)  # __add__ 返回 NotImplemented，Python 生成标准的错误信息

section("6. __call__：让对象可以像函数一样调用")


class Multiplier:
    def __init__(self, k):
        self.k = k

    def __call__(self, x):
        return x * self.k


double = Multiplier(2)
print("double(21) =", double(21))  # 相当于 C++ 的 operator()，常用来实现"带状态的函数"，比如工具对象
print("callable(double):", callable(double))
