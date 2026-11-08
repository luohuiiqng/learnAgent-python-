"""相对导入示例。

`..` 表示上一级包，也就是 demo_pkg。相对导入依赖 __package__（"demo_pkg.tools"），
所以这个文件只能作为包的一部分被导入，或者用 `python -m demo_pkg.tools.stats` 运行。
直接 `python demo_pkg/tools/stats.py` 会报
ImportError: attempted relative import with no known parent package
"""

from ..mathutils import mean  # 等价于绝对导入：from demo_pkg.mathutils import mean


def describe(values: list[float]) -> dict[str, float]:
    """返回最小值、最大值、平均值。"""
    return {"min": min(values), "max": max(values), "mean": mean(values)}


if __name__ == "__main__":
    print("__name__ =", __name__, " __package__ =", __package__)
    print(describe([3, 1, 2]))
