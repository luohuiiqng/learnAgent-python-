"""
第二课练习。补全每个函数和类，然后运行：python 练习.py
运行结果里每道题会显示 ✅ / ❌ / ⏳（未完成）。

规则：
- 只改函数体和类的内容，不要改函数名、类名和参数列表，也不要改下面的检查代码。
- 类的内容包括：补全方法、添加需要的魔术方法、按题目要求给类加装饰器或改基类。
- 这是练习不是考试，可以回看 README 和示例，但不要让 AI 替你写。
- 不要用 copy.deepcopy、functools.total_ordering 和 contextlib，用这节课学的写法完成。
"""
from abc import ABC, abstractmethod  # noqa: F401  练习 4 会用到
from dataclasses import dataclass, field  # noqa: F401  练习 3 会用到



def deep_copy(str_src):
    output = None
    if isinstance(str_src,dict):
        output = {}
        for key in str_src:
             output[key] = deep_copy(str_src[key])
    else:
        output = str_src

    if isinstance(str_src,list):
        output = []
        for value in str_src:
             output.append(deep_copy(value))
    return output

# 练习 1（P0-05）
class ChatHistory:
    """保存一段对话的消息，每条消息是 {"role": ..., "content": ...} 形式的 dict。

    - ChatHistory()：空的对话；ChatHistory("你是助手")：先放一条 system 消息
    - add(role, content)：追加一条消息；role 不在 ROLES 里时抛 ValueError，且不追加
    - len(h)：消息条数
    - h[i]、h[-1]、h[1:3]：和 list 一样支持下标和切片
    - to_list()：返回消息列表的副本，修改返回的列表或其中的 dict，都不能影响 h 内部的数据
    - ChatHistory.from_pairs([("user", "你好"), ...])：类方法，按顺序 add 每一对，返回新对象；
      子类调用时要返回子类的对象
    - 不同的 ChatHistory 对象不能共享消息

    h = ChatHistory("你是助手")
    h.add("user", "你好")
    len(h)  -> 2
    h[-1]   -> {"role": "user", "content": "你好"}
    """

    ROLES = ("system", "user", "assistant", "tool")

    def __init__(self, system_prompt=None):
        self.chats = []
        if system_prompt is not None:
            self.chats.append({"role":"system","content":system_prompt})

    def add(self, role, content):
        if role not in ChatHistory.ROLES:
            raise ValueError
        chat = {
            "role":role,
            "content":content
        }            
        self.chats.append(chat)

    def to_list(self):
        return deep_copy(self.chats)

    def __len__(self):
        return len(self.chats)

    def __getitem__(self, index):
        if index == -1 and len(self.chats) != 0:
            return self.chats[len(self.chats)-1]
        if isinstance(index,slice):
            return self.chats[index]
        if(len(self.chats)<index):
            return None
        return self.chats[index]

    @classmethod
    def from_pairs(cls, pairs):
        # print(f"pairs type:{type(pairs)},pairs value:{pairs}")
        # chathistory = ChatHistory()
        # for role,value in pairs:
        #     chathistory.add(role,value)
        # return cls(chathistory)
        history = cls()
        for role,value in pairs:
            history.add(role,value)
        return history
            




# 练习 2（P0-05）
class Money:
    """金额。cents 是以"分"为单位的非负整数，currency 是币种，例如 "CNY"。

    - cents 和 currency 是只读属性：读取正常，赋值时抛 AttributeError
    - repr(Money(1050, "CNY")) -> "Money(1050, 'CNY')"
    - str(Money(1050, "CNY"))  -> "10.50 CNY"；str(Money(5, "USD")) -> "0.05 USD"
    - ==：cents 和 currency 都相同才相等；和不是 Money 的对象比较时结果为 False，不能抛异常
    - 可以放进 set、当 dict 的键，相等的 Money 只算一个
    - <：同币种按 cents 比较，sorted() 能用；币种不同时抛 ValueError
    - +：同币种返回一个新的 Money，不修改两个操作数；币种不同时抛 ValueError；
      和不是 Money 的对象相加时抛 TypeError
    需要哪些魔术方法自己判断，下面只给出了 __init__ 和两个属性。
    """

    def __init__(self, cents, currency):
        raise NotImplementedError

    @property
    def cents(self):
        raise NotImplementedError

    @property
    def currency(self):
        raise NotImplementedError


# 练习 3（P0-05）
class Message:
    """把它改写成 frozen dataclass。注意要删掉下面占位的 __init__：
    类里已经定义了 __init__ 时，dataclass 不会再生成。

    字段依次是：role: str、content: str、name: str | None = None

    Message("user", "你好") == Message("user", "你好")  -> True
    repr(Message("user", "你好")) -> "Message(role='user', content='你好', name=None)"
    给字段赋值时抛 dataclasses.FrozenInstanceError；可以放进 set。
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError


class AgentState:
    """把它改写成普通的（不 frozen）dataclass，同样要删掉占位的 __init__。

    字段依次是：task: str、steps: list[str]（默认空列表）、max_steps: int = 3
    - add_step(step)：steps 的长度已经达到 max_steps 时抛 RuntimeError，否则把 step 追加到 steps
    - done：只读属性，steps 的长度达到 max_steps 时为 True
    - 不同的 AgentState 对象不能共享 steps 列表

    s = AgentState("查天气", max_steps=1)
    s.add_step("搜索")
    s.done  -> True
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def add_step(self, step):
        raise NotImplementedError

    @property
    def done(self):
        raise NotImplementedError


# 练习 4（P0-05）
class BaseTool:
    """工具的基类。把它改成抽象基类：继承 ABC，并给 run 加上 @abstractmethod。

    - __init__(name, description="")：保存 name 和 description，并把调用次数 calls 设为 0
    - run(**kwargs)：抽象方法，由子类实现
    - __call__(**kwargs)：calls 加 1，调用 self.run(**kwargs)，把返回值转成 str 后返回
    - 直接实例化 BaseTool，或者实例化没有实现 run 的子类，都要抛 TypeError
    """

    def __init__(self, name, description=""):
        raise NotImplementedError

    def run(self, **kwargs):
        raise NotImplementedError

    def __call__(self, **kwargs):
        raise NotImplementedError


class EchoTool(BaseTool):
    """原样返回文本的工具。

    - __init__(prefix="")：通过 super().__init__ 把 name 设为 "echo"、description 设为 "原样返回文本"，
      再保存 prefix
    - run(text)：返回 prefix + text

    EchoTool(prefix="> ")(text="hi") -> "> hi"
    """

    def __init__(self, prefix=""):
        raise NotImplementedError

    def run(self, text):
        raise NotImplementedError


class UpperEchoTool(EchoTool):
    """只重写 run：通过 super() 调用 EchoTool 的 run，再把结果转成大写。

    UpperEchoTool(prefix="re: ")(text="hi") -> "RE: HI"
    """

    def run(self, text):
        raise NotImplementedError


# 练习 5（P0-06）
class AgentError(Exception):
    """本练习所有异常的基类（已写好，不用改）"""


class ToolNotFoundError(AgentError):
    """工具不存在。补全 __init__：

    e = ToolNotFoundError("mul")
    str(e)       -> "未知工具 mul"
    e.tool_name  -> "mul"
    """

    def __init__(self, tool_name):
        raise NotImplementedError


class ToolArgumentError(AgentError):
    """工具参数不匹配（已写好，不用改）"""


def run_tool(registry, name, arguments):
    """按名字调用工具，返回函数的原始返回值（不转成 str）。
    registry: {工具名: 函数}；arguments: {参数名: 参数值}

    - 工具不存在：抛 ToolNotFoundError
    - 调用时出现 TypeError（缺参数、多参数）：抛 ToolArgumentError，消息为 "工具 <name> 参数不匹配"，
      并用 raise ... from 保留原始的 TypeError
    - 工具内部抛出的其他异常（包括 KeyError）：不要处理，原样传给调用方
    （和第一课一样，这里不区分 TypeError 来自参数不匹配还是工具内部。）

    run_tool({"add": lambda a, b: a + b}, "add", {"a": 1, "b": 2}) -> 3
    """
    raise NotImplementedError


# 练习 6（P0-06）
def retry(func, times=3, retry_on=(TimeoutError,)):
    """调用 func()（不带参数），失败时重试，成功时返回 func() 的返回值。
    调用大模型 API 时经常需要这样处理超时。

    - 最多调用 times 次；times 小于 1 时抛 ValueError，且一次都不调用
    - retry_on 是异常类型组成的 tuple，只有这些异常（包括它们的子类）才重试
    - 其他异常立即原样传出，不再重试
    - times 次全部失败时，原样重新抛出最后一次的异常对象，不要包装成别的异常
    """
    raise NotImplementedError


# 练习 7（P0-06）
class Transaction:
    """给 dict 加上"事务"：with 块正常结束时保留修改；with 块里抛出异常时，
    把 dict 恢复成进入 with 之前的内容，并让异常继续往外传。
    假设 dict 的值都是 str、int 这类不可变对象，浅拷贝就够了。

    config = {"model": "qwen"}
    with Transaction(config) as c:   # c 就是 config 这个 dict 本身
        c["model"] = "deepseek"
        raise ValueError("出错")      # 退出时 config 恢复成 {"model": "qwen"}，ValueError 继续往外传

    - rolled_back 属性：发生过回滚时为 True，否则为 False（刚创建时为 False）
    - 恢复时要修改原来那个 dict 对象，调用方手里的 config 才能看到
    """

    def __init__(self, data):
        raise NotImplementedError

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 下面是检查代码，不要修改
# ---------------------------------------------------------------------------
import dataclasses  # noqa: E402


def _expect_raises(exc_type, func, message):
    try:
        func()
    except exc_type:
        return
    raise AssertionError(message)


def _check_chat_history():
    h1 = ChatHistory()
    h1.add("user", "你好")
    h2 = ChatHistory()
    assert len(h2) == 0, "新建的对象里已经有消息：消息列表是不是写成了类属性，被所有实例共享了？"
    assert len(h1) == 1
    assert h1[0] == {"role": "user", "content": "你好"}
    h3 = ChatHistory("你是助手")
    assert len(h3) == 1 and h3[0] == {"role": "system", "content": "你是助手"}, "传了 system_prompt 时应该先放一条 system 消息"
    h3.add("user", "a")
    h3.add("assistant", "b")
    assert h3[-1] == {"role": "assistant", "content": "b"}
    assert h3[1:] == [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}], "__getitem__ 应该支持切片"
    _expect_raises(ValueError, lambda: h3.add("robot", "x"), "role 不合法时应该抛 ValueError")
    assert len(h3) == 3, "role 不合法时不应该追加消息"

    out = h3.to_list()
    assert out == [h3[0], h3[1], h3[2]]
    out.append({"role": "user", "content": "外面加的"})
    out[0]["content"] = "外面改的"
    assert len(h3) == 3, "往 to_list() 的结果里追加，影响到了内部数据"
    assert h3[0]["content"] == "你是助手", "修改 to_list() 结果里的 dict，影响到了内部数据（只复制了外层列表？）"

    class MyHistory(ChatHistory):
        pass
    h4 = MyHistory.from_pairs([("system", "s"), ("user", "u")])
    assert type(h4) is MyHistory, "子类调用 from_pairs 应该返回子类对象：用 cls(...) 创建，不要写死类名"
    print(f"==========h4.to_list() :{h4.to_list() }")
    assert h4.to_list() == [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    assert len(ChatHistory.from_pairs([])) == 0


def _check_money():
    a = Money(1050, "CNY")
    assert a.cents == 1050 and a.currency == "CNY"
    assert repr(a) == "Money(1050, 'CNY')", f"repr 不对：{a!r}"
    assert str(a) == "10.50 CNY", f"str 不对：{a}"
    assert str(Money(5, "USD")) == "0.05 USD", f"str 不对：{Money(5, 'USD')}"
    for attr in ("cents", "currency"):
        _expect_raises(AttributeError, lambda: setattr(a, attr, 1), f"{attr} 应该是只读属性")

    assert a == Money(1050, "CNY"), "两个值相同的 Money 应该相等"
    assert a != Money(1050, "USD") and a != Money(1, "CNY")
    try:
        result = a == 1050
    except (AttributeError, TypeError) as e:
        raise AssertionError(f"和非 Money 比较时抛了 {type(e).__name__}：遇到不认识的类型应该返回 NotImplemented")
    assert result is False, "Money(1050, 'CNY') == 1050 应该是 False"

    try:
        s = {Money(1, "CNY"), Money(1, "CNY")}
    except TypeError:
        raise AssertionError("Money 不能放进 set：定义了 __eq__ 之后，还需要定义 __hash__")
    assert len(s) == 1, "相等的 Money 哈希值不同，set 没有去重（__hash__ 要和 __eq__ 用同样的字段）"
    assert {Money(1, "CNY"): "x"}.get(Money(1, "CNY")) == "x", "用相等的 Money 查 dict 查不到"

    ms = [Money(300, "CNY"), Money(100, "CNY"), Money(200, "CNY")]
    assert sorted(ms) == [Money(100, "CNY"), Money(200, "CNY"), Money(300, "CNY")]
    assert Money(1, "CNY") < Money(2, "CNY") and not (Money(2, "CNY") < Money(1, "CNY"))
    _expect_raises(ValueError, lambda: Money(1, "CNY") < Money(2, "USD"), "币种不同时比较大小应该抛 ValueError")

    b = Money(50, "CNY")
    c = a + b
    assert isinstance(c, Money) and c == Money(1100, "CNY"), "加法结果不对"
    assert a == Money(1050, "CNY") and b == Money(50, "CNY"), "+ 修改了操作数"
    assert c is not a and c is not b, "+ 应该返回新对象"
    _expect_raises(ValueError, lambda: a + Money(1, "USD"), "币种不同时相加应该抛 ValueError")
    _expect_raises(TypeError, lambda: a + 1, "和 int 相加应该抛 TypeError（__add__ 返回 NotImplemented 即可）")


def _check_dataclasses():
    m = Message("user", "你好")
    assert dataclasses.is_dataclass(Message), "Message 还不是 dataclass"
    assert [f.name for f in dataclasses.fields(Message)] == ["role", "content", "name"], "Message 的字段不对"
    assert m == Message("user", "你好") and m != Message("user", "hi")
    assert m.name is None
    assert repr(m) == "Message(role='user', content='你好', name=None)", f"repr 不对：{m!r}"
    _expect_raises(dataclasses.FrozenInstanceError, lambda: setattr(m, "content", "x"), "Message 应该是 frozen 的")
    try:
        assert len({m, Message("user", "你好")}) == 1
    except TypeError:
        raise AssertionError("Message 不能放进 set")

    s1 = AgentState("查天气")
    assert dataclasses.is_dataclass(AgentState), "AgentState 还不是 dataclass"
    assert [f.name for f in dataclasses.fields(AgentState)] == ["task", "steps", "max_steps"], "AgentState 的字段不对"
    s2 = AgentState("写代码")
    s1.add_step("搜索")
    assert s2.steps == [], "不同的 AgentState 共享了 steps 列表"
    assert s1.steps == ["搜索"] and s1.max_steps == 3
    assert s1 == AgentState("查天气", ["搜索"]), "dataclass 应该按字段比较相等"

    s3 = AgentState("x", max_steps=2)
    assert s3.done is False
    s3.add_step("a")
    s3.add_step("b")
    assert s3.done is True
    _expect_raises(RuntimeError, lambda: s3.add_step("c"), "步数已满时应该抛 RuntimeError")
    assert s3.steps == ["a", "b"], "步数已满时不应该再追加"
    _expect_raises(AttributeError, lambda: setattr(s3, "done", False), "done 应该是只读属性")


def _check_tools():
    e = EchoTool(prefix="> ")
    assert isinstance(e, BaseTool)
    assert hasattr(e, "calls"), "EchoTool 对象没有 calls 属性：是不是没调用 super().__init__？"
    assert e.name == "echo" and e.description == "原样返回文本"
    assert e.calls == 0
    assert e(text="hi") == "> hi"
    assert e.calls == 1, "__call__ 应该把 calls 加 1"

    u = UpperEchoTool(prefix="re: ")
    assert u.name == "echo"
    assert u(text="hi") == "RE: HI", "UpperEchoTool 应该把父类 run 的整个结果转成大写"

    class Answer(BaseTool):
        def run(self):
            return 42

    a = Answer("answer")
    assert a.description == ""
    assert a() == "42", "__call__ 应该把 run 的返回值转成 str"

    class Incomplete(BaseTool):
        pass

    for cls in (BaseTool, Incomplete):
        _expect_raises(
            TypeError,
            lambda: cls("x"),
            f"{cls.__name__} 不应该能实例化：是不是忘了继承 ABC，或者忘了给 run 加 @abstractmethod？",
        )


def _check_run_tool():
    registry = {
        "add": lambda a, b: a + b,
        "div": lambda a, b: a / b,
        "get": lambda d, key: d[key],
    }
    assert run_tool(registry, "add", {"a": 1, "b": 2}) == 3
    e = ToolNotFoundError("mul")
    assert str(e) == "未知工具 mul", f"str(e) 不对：{e}"
    assert e.tool_name == "mul"

    try:
        run_tool(registry, "mul", {"a": 1})
    except ToolNotFoundError as err:
        assert err.tool_name == "mul"
    else:
        raise AssertionError("工具不存在时应该抛 ToolNotFoundError")

    try:
        run_tool(registry, "add", {"a": 1})
    except ToolArgumentError as err:
        assert str(err) == "工具 add 参数不匹配", f"消息不对：{err}"
        assert isinstance(err.__cause__, TypeError), "没有保留原始的 TypeError：要用 raise ... from e"
    else:
        raise AssertionError("缺参数时应该抛 ToolArgumentError")
    _expect_raises(ToolArgumentError, lambda: run_tool(registry, "add", {"a": 1, "b": 2, "c": 3}), "多参数时应该抛 ToolArgumentError")

    for tool, args, exc_type in [("div", {"a": 1, "b": 0}, ZeroDivisionError), ("get", {"d": {}, "key": "x"}, KeyError)]:
        try:
            run_tool(registry, tool, args)
        except AgentError as err:
            raise AssertionError(f"工具内部的 {exc_type.__name__} 被包装成了 {type(err).__name__}：try 包住的范围太大了")
        except exc_type:
            pass
        else:
            raise AssertionError(f"工具内部的 {exc_type.__name__} 应该原样传出来")


def _make_flaky(fail_times, exc_type=TimeoutError):
    """返回一个前 fail_times 次调用都抛 exc_type、之后返回 "成功" 的函数，以及记录调用情况的 dict"""
    state = {"calls": 0, "raised": []}

    def func():
        state["calls"] += 1
        if state["calls"] <= fail_times:
            err = exc_type(f"第 {state['calls']} 次失败")
            state["raised"].append(err)
            raise err
        return "成功"

    return func, state


def _check_retry():
    func, st = _make_flaky(0)
    assert retry(func) == "成功" and st["calls"] == 1

    func, st = _make_flaky(2)
    assert retry(func, times=3) == "成功", "失败 2 次、第 3 次成功时应该返回结果"
    assert st["calls"] == 3

    func, st = _make_flaky(10)
    try:
        retry(func, times=3)
    except TimeoutError as err:
        assert st["calls"] == 3, f"应该正好调用 3 次，实际调用了 {st['calls']} 次"
        assert err is st["raised"][-1], "应该原样抛出最后一次的异常对象（用不带参数的 raise）"
    else:
        raise AssertionError("全部失败时应该抛出最后一次的异常")

    func, st = _make_flaky(1, ConnectionResetError)
    assert retry(func, retry_on=(ConnectionError,)) == "成功", "retry_on 里异常的子类也应该重试"

    func, st = _make_flaky(10, ValueError)
    try:
        retry(func)
    except ValueError:
        assert st["calls"] == 1, "不在 retry_on 里的异常不应该重试"
    else:
        raise AssertionError("不在 retry_on 里的异常应该原样传出")

    func, st = _make_flaky(10, KeyboardInterrupt)
    try:
        retry(func, retry_on=(Exception,))
    except KeyboardInterrupt:
        assert st["calls"] == 1, "KeyboardInterrupt 被重试了：是不是用了裸 except 或 except BaseException？"
    else:
        raise AssertionError("KeyboardInterrupt 被吞掉了")

    func, st = _make_flaky(0)
    _expect_raises(ValueError, lambda: retry(func, times=0), "times 小于 1 时应该抛 ValueError")
    assert st["calls"] == 0, "times 小于 1 时不应该调用 func"


def _check_transaction():
    config = {"model": "qwen", "temperature": 0.7}
    tx = Transaction(config)
    assert tx.rolled_back is False
    with tx as c:
        assert c is config, "__enter__ 应该返回传进来的 dict 本身"
        c["temperature"] = 0
        c["debug"] = True
    assert config == {"model": "qwen", "temperature": 0, "debug": True}, "正常结束时应该保留修改"
    assert tx.rolled_back is False, "没有异常时 rolled_back 应该是 False"

    tx2 = Transaction(config)
    propagated = False
    try:
        with tx2 as c:
            c["model"] = "deepseek"
            del c["debug"]
            c["new_key"] = 1
            raise ValueError("出错")
    except ValueError:
        propagated = True
    assert propagated, "异常被吞掉了：只有想吞掉异常时 __exit__ 才返回真值"
    assert config == {"model": "qwen", "temperature": 0, "debug": True}, f"没有正确回滚，config = {config}"
    assert tx2.rolled_back is True

    propagated = False
    try:
        with Transaction(config) as c:
            c["x"] = 1
            c["不存在的键"]
    except KeyError:
        propagated = True
    assert propagated, "KeyError 被吞掉了"
    assert "x" not in config, "KeyError 之后没有回滚"


if __name__ == "__main__":
    checks = [
        ("练习 1 ChatHistory", _check_chat_history),
        ("练习 2 Money", _check_money),
        ("练习 3 Message / AgentState", _check_dataclasses),
        ("练习 4 BaseTool / EchoTool", _check_tools),
        ("练习 5 run_tool", _check_run_tool),
        ("练习 6 retry", _check_retry),
        ("练习 7 Transaction", _check_transaction),
    ]
    passed = 0
    for title, check in checks:
        try:
            check()
            print(f"✅ {title}")
            passed += 1
        except NotImplementedError:
            print(f"⏳ {title}：未完成")
        except AssertionError as e:
            print(f"❌ {title}：{e or '结果不正确'}")
        except Exception as e:
            print(f"❌ {title}：运行出错 {type(e).__name__}: {e}")
    print(f"\n通过 {passed}/{len(checks)}")
