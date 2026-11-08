"""演示"import 会执行模块顶层代码，而且只执行一次"。

真实项目里不要在模块顶层 print 或做耗时操作（连数据库、加载模型），
因为任何 import 这个模块的地方都会触发它。
"""

print("  [noisy.py] 顶层代码正在执行")

counter = 0


def bump() -> int:
    global counter
    counter += 1
    return counter
