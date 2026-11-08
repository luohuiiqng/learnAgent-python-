"""数学小工具。tests/test_mathutils.py 演示了怎么测试这里的函数。"""


def mean(values: list[float]) -> float:
    """求平均值。空列表没有平均值，抛 ValueError。"""
    if not values:
        raise ValueError("values 不能为空")
    return sum(values) / len(values)


def clamp(value: float, low: float, high: float) -> float:
    """把 value 限制在 [low, high] 区间内。low > high 时抛 ValueError。"""
    if low > high:
        raise ValueError(f"low ({low}) 不能大于 high ({high})")
    return max(low, min(value, high))


# 直接运行这个文件时 __name__ 是 "__main__"，被 import 时是 "demo_pkg.mathutils"。
# 这一段只在直接运行时执行，适合放演示或自测代码。
if __name__ == "__main__":
    print("直接运行 mathutils，__name__ =", __name__)
    print("mean([1, 2, 3]) =", mean([1, 2, 3]))
