"""循环导入的 a 端。执行到第一行时 a 还没定义 func_a，就去导入 b。"""

from demo_pkg.circular.b import func_b


def func_a() -> str:
    return "a 调用了 " + func_b()
