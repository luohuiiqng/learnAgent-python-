"""P0-06 异常处理与上下文管理器。运行：python 04_异常与上下文管理器.py"""
import os
import sys
import tempfile
import threading


def section(title):
    print(f"\n===== {title} =====")


section("1. try / except / else / finally 的执行顺序")


def parse(text):
    try:
        value = int(text)  # try 里只放可能出错的那一句
    except ValueError as e:
        print(f"  except: {e}")
        return None
    else:
        print(f"  else: 没有异常才执行，value = {value}")  # 放"成功之后才做的事"，它抛的异常不会被上面的 except 接住
        return value
    finally:
        print("  finally: 无论成功、失败还是 return，都会执行")


print("parse('42') ->", parse("42"))
print("parse('abc') ->", parse("abc"))

section("2. 异常的继承体系：except 父类会接住所有子类")
print("KeyError 的 MRO:", [k.__name__ for k in KeyError.__mro__])
print("KeyboardInterrupt 的 MRO:", [k.__name__ for k in KeyboardInterrupt.__mro__])  # 不继承 Exception

for bad in [lambda: {}["x"], lambda: [][0]]:
    try:
        bad()
    except LookupError as e:  # KeyError 和 IndexError 都是 LookupError 的子类
        print(f"  LookupError 接住了 {type(e).__name__}: {e}")

try:
    {}["x"]
except Exception:  # 多个 except 从上往下匹配，第一个匹配上的生效
    print("  先写的 except Exception 接住了，后面的 except KeyError 永远轮不到")
except KeyError:
    print("  不会执行")

section("3. 不要写裸 except：它连 SystemExit 和 KeyboardInterrupt 都会接住")
try:
    sys.exit(1)  # sys.exit 的实现就是抛出 SystemExit
except:  # noqa: E722  这里是故意写的反例
    print("  裸 except 接住了 SystemExit，程序本来应该退出的")

try:
    try:
        sys.exit(1)
    except Exception:
        print("  不会执行：SystemExit 不是 Exception 的子类")
except SystemExit as e:
    print(f"  except Exception 没有拦它，SystemExit 继续往外传，退出码 {e.code}")

section("4. 自定义异常：让调用方能区分不同的失败原因")


class AgentError(Exception):
    """本项目所有异常的基类，调用方可以用 except AgentError 一次接住全部"""


class LLMTimeoutError(AgentError):
    def __init__(self, model, seconds):
        super().__init__(f"模型 {model} 超过 {seconds} 秒没有响应")  # 传给父类的参数决定 str(e)
        self.model = model  # 额外的属性，方便调用方做判断
        self.seconds = seconds


class ToolArgumentError(AgentError):
    pass  # 不需要额外属性时，pass 就够了


def step(kind):
    if kind == "timeout":
        raise LLMTimeoutError("qwen", 30)
    if kind == "bad_args":
        raise ToolArgumentError("缺少参数 city")
    return "ok"


for kind in ["ok", "timeout", "bad_args"]:
    try:
        print(f"  {kind}: {step(kind)}")
    except LLMTimeoutError as e:
        print(f"  {kind}: 超时可以重试 -> {e}（model={e.model}）")
    except ToolArgumentError as e:
        print(f"  {kind}: 参数错了，重试没用，应该把错误告诉模型 -> {e}")

section("5. raise 不带参数：原样重新抛出当前异常")


def load(d):
    try:
        return d["model"]
    except KeyError:
        print("  记录一条日志，然后继续往上抛")
        raise  # 抛出的还是原来那个 KeyError 对象


try:
    load({})
except KeyError as e:
    print(f"  外层收到 KeyError: {e}")

section("6. 异常链：raise ... from e")


def read_config(d):
    try:
        return d["temperature"]
    except KeyError as e:
        raise AgentError("配置缺少 temperature") from e  # 新异常的 __cause__ 指向原始异常


try:
    read_config({})
except AgentError as e:
    print("  e =", repr(e))
    print("  e.__cause__ =", repr(e.__cause__))  # 打印 traceback 时两个异常都会显示，中间写着 direct cause


def read_config_implicit(d):
    try:
        return d["temperature"]
    except KeyError:
        raise AgentError("配置缺少 temperature")  # 没写 from：原始异常只记在 __context__ 里


try:
    read_config_implicit({})
except AgentError as e:
    print("  不写 from：__cause__ =", e.__cause__, " __context__ =", repr(e.__context__))
    # traceback 里显示的是 "During handling of the above exception, another exception occurred"，看起来像处理代码自己出了 bug


def read_config_hide(d):
    try:
        return d["temperature"]
    except KeyError:
        raise AgentError("配置缺少 temperature") from None  # 明确表示不需要显示原始异常


try:
    read_config_hide({})
except AgentError as e:
    print("  from None：__suppress_context__ =", e.__suppress_context__)

section("7. except ... as e 里的 e 在 except 块结束后会被删除")
try:
    1 / 0
except ZeroDivisionError as e:
    saved = e  # 需要在外面用，就赋值给另一个名字
try:
    print(e)
except NameError as err:
    print("  NameError:", err)
print("  saved =", repr(saved))

section("8. EAFP 和 LBYL")
config = {"model": "qwen"}

# LBYL（Look Before You Leap）：先检查再做，C++ 里常见的写法
if "temperature" in config:
    t = config["temperature"]
else:
    t = 0.7
print("  LBYL:", t)

# EAFP（Easier to Ask Forgiveness than Permission）：直接做，出错再处理，Python 里更常见
try:
    t = config["temperature"]
except KeyError:
    t = 0.7
print("  EAFP:", t)
print("  这种简单场景用 dict.get 最直接:", config.get("temperature", 0.7))

# 字符串转数字：Qt 的 QString::toInt(&ok) 返回 bool，Python 的 int() 失败时抛 ValueError
for s in ["12", "1.5", "abc"]:
    try:
        print(f"  int({s!r}) = {int(s)}")
    except ValueError as e:
        print(f"  int({s!r}) 失败: {e}")

section("9. with 语句：离开代码块时自动清理，相当于 RAII")
with tempfile.TemporaryDirectory() as tmp:  # TemporaryDirectory 本身也是上下文管理器，退出时删除整个目录
    path = os.path.join(tmp, "notes.txt")
    with open(path, "w", encoding="utf-8") as f:  # 文本文件要写 encoding
        f.write("第一行\n")
    print("  离开 with 之后 f.closed =", f.closed)  # 文件已经关闭，名字 f 仍然可以访问

    try:
        with open(path, encoding="utf-8") as f:
            print("  读到:", f.read().strip())
            raise RuntimeError("读完之后出错")
    except RuntimeError as e:
        print(f"  {e}，但文件照样关闭了: f.closed = {f.closed}")
    tmp_saved = tmp
print("  临时目录已删除:", not os.path.exists(tmp_saved))

lock = threading.Lock()
with lock:  # 相当于 std::lock_guard / QMutexLocker
    print("  with 里面 lock.locked() =", lock.locked())
print("  with 外面 lock.locked() =", lock.locked())

section("10. 自己写上下文管理器：__enter__ 和 __exit__")


class Tracer:
    def __init__(self, name, suppress=()):
        self.name = name
        self.suppress = suppress  # 允许吞掉的异常类型

    def __enter__(self):
        print(f"  __enter__({self.name})")
        return self  # 返回值绑定到 as 后面的名字；不写 return 就是 None

    def __exit__(self, exc_type, exc_value, traceback):
        # 正常结束：三个参数都是 None；有异常：分别是异常类型、异常对象、traceback 对象
        print(f"  __exit__({self.name}): exc_type={exc_type and exc_type.__name__}, exc_value={exc_value!r}")
        # 返回真值表示"异常我处理了"，with 后面的代码照常执行；返回 None 或 False 时异常继续往外传
        return exc_type is not None and issubclass(exc_type, self.suppress)


with Tracer("正常") as t:
    print("  as 拿到的是 __enter__ 的返回值:", t.name)

with Tracer("吞掉 KeyError", suppress=(KeyError,)):
    {}["x"]
    print("  不会执行：异常发生后 with 块里剩下的代码被跳过")
print("  KeyError 被 __exit__ 吞掉了，程序继续")

try:
    with Tracer("不吞 ValueError", suppress=(KeyError,)):
        int("abc")
except ValueError as e:
    print("  ValueError 照常传出来:", e)

with Tracer("外层"), Tracer("内层"):  # 一条 with 写多个，退出顺序和进入相反，和 C++ 析构顺序一样
    print("  两个都进入了")
