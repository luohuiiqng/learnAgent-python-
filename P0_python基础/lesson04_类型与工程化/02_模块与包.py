"""P0-10 模块、包与 import 机制。运行：python 02_模块与包.py"""

import importlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]


def section(title):
    print(f"\n===== {title} =====")


def run(args, cwd):
    """用当前这个 python 解释器启动一个子进程，返回输出的最后一行。-B 表示不写 .pyc。"""
    proc = subprocess.run(
        [sys.executable, "-B", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    out = (proc.stdout + proc.stderr).strip()
    return out.splitlines()[-1] if out else "(无输出)"


section("1. 模块就是 .py 文件，import 之后得到一个 module 对象")

import demo_pkg.mathutils  # noqa: E402  为了分段演示，import 写在了中间

print("type:", type(demo_pkg.mathutils).__name__)
print("__name__:", demo_pkg.mathutils.__name__)
print("__file__:", Path(demo_pkg.mathutils.__file__).relative_to(HERE))
print("这个脚本自己的 __name__:", __name__)  # 直接运行的脚本，__name__ 是 "__main__"

section("2. import 会执行模块顶层代码，而且只执行一次")

print("第一次 import demo_pkg.noisy：")
import demo_pkg.noisy  # noqa: E402

print("第二次 import demo_pkg.noisy（不会再打印）：")
import demo_pkg.noisy  # noqa: E402, F811

print("缓存在 sys.modules 里:", "demo_pkg.noisy" in sys.modules)
print("取出来是同一个对象:", sys.modules["demo_pkg.noisy"] is demo_pkg.noisy)
demo_pkg.noisy.bump()
print("bump() 之后 counter =", demo_pkg.noisy.counter)
print("importlib.reload 会强制重新执行顶层代码：")
importlib.reload(demo_pkg.noisy)
print("reload 之后模块里的变量被重新初始化，counter =", demo_pkg.noisy.counter)

section("3. 导入包会先执行包的 __init__.py")

import demo_pkg  # noqa: E402

print("demo_pkg.__file__:", Path(demo_pkg.__file__).relative_to(HERE))
print("__init__.py 里提上来的名字：demo_pkg.mean([1, 3]) =", demo_pkg.mean([1, 3]))
print("demo_pkg.__all__ =", demo_pkg.__all__)
loaded = sorted(name for name in sys.modules if name.startswith("demo_pkg"))
print("目前加载过的 demo_pkg 模块:", loaded)

section("4. from x import y 拿到的是当时那个对象的引用")

from demo_pkg import noisy  # noqa: E402
from demo_pkg.noisy import counter  # noqa: E402

noisy.bump()
print("noisy.counter =", noisy.counter, "（每次通过模块访问，能看到最新值）")
print("counter =", counter, "（import 那一刻绑定的 int，之后不会跟着变）")

section("5. sys.path：import 去哪些目录找模块")

print("sys.path[0] 是这个脚本所在的目录:", Path(sys.path[0]).resolve() == HERE)
print("所以能直接 import demo_pkg。sys.path 后面几项是标准库和 site-packages 的目录")
print(
    "pydantic 来自 site-packages:",
    "site-packages" in importlib.import_module("pydantic").__file__,
)

section("6. 运行方式不同，sys.path[0] 不同")

print("python -m demo_pkg                 ->", run(["-m", "demo_pkg"], HERE))
print("python demo_pkg/__main__.py        ->", run(["demo_pkg/__main__.py"], HERE))
print("python demo_pkg/tools/stats.py     ->", run(["demo_pkg/tools/stats.py"], HERE))
print(
    "python -m demo_pkg.tools.stats     ->", run(["-m", "demo_pkg.tools.stats"], HERE)
)
# 第 2 行失败：直接运行文件时，sys.path[0] 是文件所在目录 demo_pkg/，那里找不到 demo_pkg 包
# 第 3 行失败：直接运行文件时没有"所属包"，相对导入 from ..mathutils 无从解析

section("7. 仓库里的 main_fc.py 为什么能 import FunctionCallingAgent")

example_dir = REPO_ROOT / "example_agents"
code = "import FunctionCallingAgent; print('导入成功', FunctionCallingAgent.__all__)"
print("在 example_agents/ 下 python -c ... ->", run(["-c", code], example_dir))
print("在本课目录下 python -c ...        ->", run(["-c", code], HERE))
# python -c 和 python -m 都把"当前目录"放进 sys.path[0]；python 某文件.py 把"文件所在目录"放进去。
# FunctionCallingAgent/ 在 example_agents/ 下面，所以只有 sys.path 里有 example_agents/ 才找得到它

section("8. 循环导入")

try:
    import demo_pkg.circular.a  # noqa: E402, F401
except ImportError as e:
    print("ImportError:", str(e).split(" (/")[0])  # 去掉末尾的绝对路径
# 过程：执行 a.py 第一行 -> 去导入 b -> 执行 b.py 第一行 from a import func_a
# -> a 已经在 sys.modules 里，但只执行了一半，还没有 func_a -> 报错
