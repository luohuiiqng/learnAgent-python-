"""循环导入的 b 端。此时 a 已经在 sys.modules 里，但只执行了一半，func_a 还不存在。"""

from demo_pkg.circular.a import func_a


def func_b() -> str:
    return "b"


def use_a() -> str:
    return func_a()
