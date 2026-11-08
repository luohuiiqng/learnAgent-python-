"""演示：assert、pytest.raises、parametrize。

运行（在 lesson04_类型与工程化 目录下）：python -m pytest tests -q
"""

import pytest

from demo_pkg.mathutils import clamp, mean
from demo_pkg.tools.stats import describe


def test_mean_basic():
    # 直接写 assert。失败时 pytest 会把两边的值都打印出来，不需要 assertEqual 之类的方法
    assert mean([1, 2, 3]) == 2


def test_mean_float():
    # 浮点数不要用 == 比较，用 pytest.approx
    assert mean([0.1, 0.2]) == pytest.approx(0.15)


def test_mean_empty_raises():
    # 断言"一定会抛这个异常"；match 是正则，用 re.search 匹配异常信息
    with pytest.raises(ValueError, match="不能为空"):
        mean([])


# 一组输入输出跑同一段测试逻辑，每组数据算一个独立的测试用例
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (5, 5),  # 在区间内
        (-1, 0),  # 低于下限
        (99, 10),  # 高于上限
        (0, 0),  # 正好等于边界
    ],
)
def test_clamp(value, expected):
    assert clamp(value, 0, 10) == expected


def test_clamp_invalid_range():
    with pytest.raises(ValueError):
        clamp(1, 10, 0)


def test_describe():
    assert describe([3, 1, 2]) == {"min": 1, "max": 3, "mean": 2.0}
