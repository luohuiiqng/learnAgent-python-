"""demo_pkg：第四课的示例包。

`import demo_pkg` 时会执行这个文件。这里只做两件事：
1. 定义包级别的变量（__version__）；
2. 把常用的名字从子模块"提上来"，让使用者可以写 `from demo_pkg import mean`，
   不必知道它具体在 demo_pkg/mathutils.py 里。
"""

from .config import LLMConfig, load_config
from .mathutils import clamp, mean

__version__ = "0.1.0"

# `from demo_pkg import *` 只导入 __all__ 里列出的名字
__all__ = ["LLMConfig", "load_config", "clamp", "mean"]
