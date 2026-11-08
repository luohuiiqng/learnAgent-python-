"""P0-11 工程化：虚拟环境信息和 logging。运行：python 03_工程化.py

uv、ruff、pytest 是命令行工具，按 README 第 3 节在终端里操作。
"""

import logging
import sys
import tempfile
from pathlib import Path


def section(title):
    print(f"\n===== {title} =====")


section("1. 现在用的是哪个 Python、哪个环境")

print("sys.executable:", sys.executable)
print("sys.prefix:    ", sys.prefix)
# venv（包括 uv 创建的 .venv）里，sys.prefix 指向 .venv，sys.base_prefix 指向创建它的那个 Python。
# conda 环境不是 venv，两者相等
print("在 venv 里:", sys.prefix != sys.base_prefix)
print(
    '在 uv 项目里执行 uv run python -c "import sys; print(sys.prefix != sys.base_prefix)"，会输出 True'
)

section("2. 为什么不用 print：logging 有级别，可以统一控制输出")

# basicConfig 配置根 logger，只在程序入口调用一次。
# 默认输出到 stderr，这里改成 stdout，是为了和 print 的输出按顺序显示。
# 真实项目的格式一般会带上时间：'%(asctime)s %(levelname)s %(name)s: %(message)s'。
# 这里不带时间，是为了让每次运行的输出完全一样
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s: %(message)s",
    stream=sys.stdout,
)

log = logging.getLogger("lesson04")
log.debug("DEBUG 低于 INFO，不会输出")
log.info("INFO 正常运行信息")
log.warning("WARNING 值得注意，但程序还能继续")
log.error("ERROR 某个操作失败了")

section("3. 用 %s 占位，把参数交给 logging 格式化")

model, tokens = "qwen-plus", 1234
log.info("调用 %s，消耗 %d tokens", model, tokens)
# 写成 f-string 也能工作，区别是：f-string 无论这条日志输出不输出都会先拼好字符串；
# %s 写法在级别不够时直接跳过格式化
log.debug("这条不会输出，所以 %s 也不会被格式化", model)

section("4. 调整级别：不改代码，就能打开或关闭某一类日志")

log.setLevel(logging.DEBUG)
log.debug("把 lesson04 这个 logger 调到 DEBUG 之后，DEBUG 也输出了")
log.setLevel(logging.WARNING)
log.info("调到 WARNING 之后，INFO 不输出了")
log.setLevel(logging.NOTSET)  # 恢复成跟随根 logger

section("5. logger 按名字分层：demo_pkg.config 的日志会传给 demo_pkg，再传给根 logger")

import demo_pkg.config  # noqa: E402  为了分段演示，import 写在了中间

config_logger = demo_pkg.config.logger

print("demo_pkg.config 里的 logger 名字:", config_logger.name)
with tempfile.TemporaryDirectory() as tmp:  # 临时目录，with 结束时自动删除
    hot = Path(tmp) / "hot.json"
    hot.write_text('{"model": "qwen", "temperature": 1.8}', encoding="utf-8")
    # load_config 内部调用 logger.warning(...)，输出格式由上面的 basicConfig 决定
    demo_pkg.config.load_config(hot)
    # 只影响 demo_pkg 及其子 logger
    logging.getLogger("demo_pkg").setLevel(logging.ERROR)
    demo_pkg.config.load_config(hot)
    print("把 demo_pkg 调到 ERROR 后，第二次 load_config 的 WARNING 没有输出")
    log.warning("lesson04 这个 logger 不受影响")

section("6. logger.exception：在 except 里记录错误和完整的调用栈")

try:
    1 / 0
except ZeroDivisionError:
    log.exception("计算失败")  # 级别是 ERROR，后面自动附上 traceback
