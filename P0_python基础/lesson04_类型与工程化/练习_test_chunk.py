"""
练习 6（P0-11）：给 demo_pkg/chunking.py 里的 chunk_text 写 pytest 测试。

先读 chunk_text 的 docstring，弄清楚它的规则，然后在这个文件里写测试。
不要修改 demo_pkg/chunking.py。

要求：
- 用到 @pytest.mark.parametrize（至少一处）和 pytest.raises（至少一处）；
- 测试在正确的 chunk_text 上全部通过；
- 测试要能发现错误的实现。检查程序准备了几种常见的错误实现
  （例如忘了处理最后一段、忽略 overlap、参数不合法时不报错），
  每一种都必须让你的至少一个测试失败。

自己运行（在 lesson04_类型与工程化 目录下）：
    python -m pytest 练习_test_chunk.py -q
这个文件名不符合 pytest 的自动发现规则（test_*.py 或 *_test.py），
所以 `python -m pytest tests` 不会收集它，需要在命令行里写出文件名。

检查（会把你的测试分别跑在正确实现和几种错误实现上）：
    python 练习.py
"""

# 检查程序会在这个文件被导入之前，把 demo_pkg.chunking.chunk_text 换成错误实现，
# 所以要保留下面这种导入方式。写完测试后可以删掉两行末尾的 noqa 注释
import pytest  # noqa: F401

from demo_pkg.chunking import chunk_text  # noqa: F401


def test_todo():
    raise NotImplementedError  # 删掉这个占位测试，写你自己的测试
