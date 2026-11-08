"""`python -m demo_pkg` 运行的就是这个文件。"""

from demo_pkg import __version__, mean

print(f"demo_pkg {__version__}，__name__ = {__name__}")
print("mean([2, 4, 9]) =", mean([2, 4, 9]))
