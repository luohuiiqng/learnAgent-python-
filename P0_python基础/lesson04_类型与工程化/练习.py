"""
第四课练习。补全每道题，然后在本课目录下运行：python 练习.py
运行结果里每道题会显示 ✅ / ❌ / ⏳（未完成）。

规则：
- 只改题目要求你补全的部分，不要改函数签名、类名和下面的检查代码。
- 这是练习不是考试，可以回看 README 和示例，但不要让 AI 替你写。
- 练习 1、4 是补全 Pydantic 模型：删掉类体里的 `...`，写上字段定义。类里还没有字段时，检查结果显示 ⏳。
- 练习 6 写在另一个文件 练习_test_chunk.py 里，这里只负责检查。
"""

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

# 下面这几个名字留给你在练习 1、4 里用。全部用上之后，这一行可以删掉
_ = (Literal, Field, field_validator)


# 练习 1（P0-09）
class KbSearchArgs(BaseModel):
    """知识库检索工具的参数。

    补全三个字段，每个字段都要用 Field(description=...) 写上说明（模型靠它理解参数）：
    - query：字符串，必填，至少 1 个字符；
    - top_k：整数，默认 5，取值 1 到 20（含两端）；
    - source：只能是 "wiki"、"docs"、"all" 之一，默认 "all"。

    KbSearchArgs(query="RAG")              -> query='RAG' top_k=5 source='all'
    KbSearchArgs(query="RAG", top_k="3")   -> top_k 是 int 3
    KbSearchArgs(query="", top_k=0)        -> 抛 ValidationError
    """

    ...


# 练习 2（P0-09）
def to_openai_tool(model_cls, name, description=None):
    """把一个 Pydantic 模型转成 OpenAI tools 参数里的一项：

    {"type": "function",
     "function": {"name": name, "description": ..., "parameters": ...}}

    - description：优先用参数 description；没传时用 model_cls.__doc__ 去掉首尾空白后的内容；
      两者都没有（docstring 是 None 或只有空白）时抛 ValueError。
      注意用 model_cls.__doc__，不要用 inspect.getdoc（它会找到 BaseModel 自己的文档）。
    - parameters：用 model_cls.model_json_schema() 生成，去掉最外层的 "title" 和 "description" 两个键
      （最外层没有 "description" 时也不能报错）。properties 里每个字段自己的 "title" 保留不动。

    对比 example_agents/FunctionCallingAgent/tools.py 的 register()：那里 parameters 是手写的。
    """
    raise NotImplementedError


# 练习 3（P0-09）
def parse_tool_args(model_cls, arguments_json):
    """把模型返回的工具参数（JSON 字符串）解析成 model_cls 的实例。

    返回一个二元组：
    - 成功：(实例, None)
    - 失败：(None, 错误说明)
    arguments_json 是 None 或 "" 时，按 "{}" 处理。
    JSON 本身不合法、字段不合法，都算失败，都不能让异常抛出去。

    错误说明的格式：ValidationError 里每条错误占一行，写成 "字段路径: 错误信息"，行之间用 "\\n" 连接，
    顺序和 e.errors() 一致。字段路径是 loc 里的各项用 "." 连起来（例如 ("items", 1, "qty") -> "items.1.qty"），
    loc 为空时（JSON 本身不合法）写成 "(root)"。错误信息就是每条错误的 "msg"。

    例如缺了 customer、第 2 个 item 的 qty 是 0 时，错误说明是：
    customer: Field required
    items.1.qty: Input should be greater than or equal to 1
    """
    raise NotImplementedError


# 练习 4（P0-09）
class ChatMessage(BaseModel):
    """一条对话消息。补全字段和校验器：

    - role：只能是 "system"、"user"、"assistant"、"tool" 之一（用 Literal，不要用 str）。
      输入不区分大小写，允许首尾空白："User " 也算 "user"。
      提示：需要在类型校验之前处理原始输入，想想 field_validator 的哪个 mode。
      输入不是字符串（例如 1）时，要得到 ValidationError，而不是别的异常。
    - content：字符串，去掉首尾空白后保存；去掉空白后为空时，抛 ValueError("content 不能为空")。
    - tool_call_id：字符串或 None，默认 None。

    ChatMessage(role="User ", content="  你好 ") -> role='user' content='你好' tool_call_id=None
    """

    ...


# 练习 5（P0-10）
def import_from_string(path):
    """按 "模块路径:属性名" 导入一个对象并返回。很多框架用这种字符串写配置，例如 uvicorn 的 "main:app"。

    import_from_string("json:dumps")                   -> json.dumps 这个函数本身
    import_from_string("demo_pkg.tools.stats:describe") -> demo_pkg/tools/stats.py 里的 describe
    import_from_string("os:path.join")                 -> 属性名可以用 "." 往下取多层，结果是 os.path.join

    - 没有 ":"，或者冒号前后有一边是空的，抛 ValueError；
    - 模块不存在时，让 import 机制抛出的 ModuleNotFoundError 原样抛出；
    - 属性不存在时，让 AttributeError 原样抛出；
    - 用 importlib.import_module，不要用 eval / exec。
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 下面是检查代码，不要修改
# ---------------------------------------------------------------------------


def _require_fields(model_cls):
    if not model_cls.model_fields:
        raise NotImplementedError


def _expect_invalid(model_cls, data, hint):
    try:
        model_cls.model_validate(data)
    except ValidationError:
        return
    raise AssertionError(f"{hint}：应该抛 ValidationError，输入 {data!r}")


def _check_kb_search_args():
    _require_fields(KbSearchArgs)
    args = KbSearchArgs(query="RAG")
    assert (args.query, args.top_k, args.source) == ("RAG", 5, "all"), "默认值不对"
    args = KbSearchArgs(query="RAG", top_k="3", source="docs")
    assert args.top_k == 3 and type(args.top_k) is int, "top_k 应该把 '3' 转成 int 3"
    _expect_invalid(KbSearchArgs, {"query": ""}, "query 为空字符串")
    _expect_invalid(KbSearchArgs, {}, "缺少 query")
    _expect_invalid(KbSearchArgs, {"query": "a", "top_k": 0}, "top_k 小于 1")
    _expect_invalid(KbSearchArgs, {"query": "a", "top_k": 21}, "top_k 大于 20")
    assert KbSearchArgs(query="a", top_k=20).top_k == 20, "top_k=20 应该合法"
    _expect_invalid(
        KbSearchArgs, {"query": "a", "source": "web"}, "source 不在可选值里"
    )
    schema = KbSearchArgs.model_json_schema()
    props = schema["properties"]
    assert set(props) == {"query", "top_k", "source"}, (
        f"字段应该正好是 query/top_k/source，现在是 {set(props)}"
    )
    assert schema.get("required") == ["query"], "只有 query 是必填的"
    for field_name, prop in props.items():
        assert prop.get("description"), f"字段 {field_name} 缺少 description"
    assert props["source"].get("enum") == ["wiki", "docs", "all"], (
        "source 应该用 Literal 定义"
    )
    top_k_range = (props["top_k"].get("minimum"), props["top_k"].get("maximum"))
    assert top_k_range == (1, 20), "top_k 的范围应该用 Field(ge=, le=) 定义"


def _check_to_openai_tool():
    class _Calc(BaseModel):
        """计算数学表达式。"""

        expression: str = Field(description="数学表达式")

    class _NoDoc(BaseModel):
        city: str
        days: int = Field(default=1, ge=1, le=7)

    expected = {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "description": "数学表达式",
                        "title": "Expression",
                        "type": "string",
                    }
                },
                "required": ["expression"],
            },
        },
    }
    tool = to_openai_tool(_Calc, "calculate")
    assert tool == expected, f"结果和预期不同：{tool}"
    tool = to_openai_tool(_Calc, "calc", "自定义说明")
    assert tool["function"]["name"] == "calc"
    assert tool["function"]["description"] == "自定义说明", (
        "传了 description 参数时应该优先用它"
    )
    assert "description" not in tool["function"]["parameters"], (
        "parameters 最外层的 description 应该去掉"
    )
    try:
        to_openai_tool(_NoDoc, "weather")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "模型没有 docstring 又没传 description 时，应该抛 ValueError"
        )
    tool = to_openai_tool(_NoDoc, "weather", "查天气")
    params = tool["function"]["parameters"]
    assert "title" not in params, "parameters 最外层的 title 应该去掉"
    assert params["required"] == ["city"]
    assert params["properties"]["days"]["maximum"] == 7, (
        "parameters 应该由 model_json_schema() 生成"
    )
    assert params["properties"]["city"]["title"] == "City", (
        "properties 里字段自己的 title 不要删"
    )


def _check_parse_tool_args():
    class _Item(BaseModel):
        name: str
        qty: int = Field(ge=1)

    class _Order(BaseModel):
        customer: str
        items: list[_Item]

    class _Page(BaseModel):
        page: int = 1

    result = parse_tool_args(
        _Order, '{"customer": "hq", "items": [{"name": "a", "qty": "2"}]}'
    )
    assert isinstance(result, tuple) and len(result) == 2, "应该返回二元组"
    obj, err = result
    assert err is None, f"合法输入不应该有错误：{err}"
    assert isinstance(obj, _Order) and obj.items[0].qty == 2

    obj, err = parse_tool_args(
        _Order, '{"items": [{"name": "a", "qty": 2}, {"name": "b", "qty": 0}]}'
    )
    assert obj is None, "失败时第一个元素应该是 None"
    expected = "customer: Field required\nitems.1.qty: Input should be greater than or equal to 1"
    assert err == expected, f"错误说明格式不对。\n期望：\n{expected}\n实际：\n{err}"

    obj, err = parse_tool_args(_Order, '{"customer": "hq", ')
    assert obj is None and isinstance(err, str), (
        "JSON 不合法时应该返回 (None, 错误说明)"
    )
    assert err.startswith("(root): Invalid JSON"), (
        f"JSON 不合法时字段路径应该是 (root)，实际：{err}"
    )

    for empty in ["", None]:
        obj, err = parse_tool_args(_Page, empty)
        assert err is None and obj == _Page(), (
            f"arguments_json={empty!r} 应该按 '{{}}' 处理"
        )


def _check_chat_message():
    _require_fields(ChatMessage)
    m = ChatMessage(role="User ", content="  你好 ")
    assert (m.role, m.content, m.tool_call_id) == ("user", "你好", None), (
        f"结果不对：{m!r}"
    )
    m = ChatMessage.model_validate_json(
        '{"role": "TOOL", "content": "42", "tool_call_id": "call_1"}'
    )
    assert (m.role, m.tool_call_id) == ("tool", "call_1")
    _expect_invalid(ChatMessage, {"role": "boss", "content": "hi"}, "role 不在可选值里")
    _expect_invalid(ChatMessage, {"role": "user"}, "缺少 content")
    try:
        ChatMessage(role=1, content="hi")
    except ValidationError:
        pass
    except Exception as e:
        raise AssertionError(
            f"role=1 时应该得到 ValidationError，实际抛了 {type(e).__name__}"
        ) from e
    else:
        raise AssertionError("role=1 时应该抛 ValidationError")
    try:
        ChatMessage(role="user", content="   ")
    except ValidationError as e:
        assert "content 不能为空" in e.errors()[0]["msg"], (
            "错误信息里应该有 'content 不能为空'"
        )
    else:
        raise AssertionError("content 只有空白时应该抛 ValidationError")
    role_schema = ChatMessage.model_json_schema()["properties"]["role"]
    assert role_schema.get("enum") == ["system", "user", "assistant", "tool"], (
        "role 应该用 Literal 定义"
    )


def _check_import_from_string():
    import json
    import os
    import sys

    assert import_from_string("json:dumps") is json.dumps
    obj = import_from_string("demo_pkg.tools.stats:describe")
    assert "demo_pkg.tools.stats" in sys.modules, "应该真正导入 demo_pkg.tools.stats"
    assert obj is sys.modules["demo_pkg.tools.stats"].describe, (
        "拿到的不是 demo_pkg.tools.stats.describe"
    )
    assert import_from_string("os:path.join") is os.path.join, (
        "属性名里的 '.' 应该逐层 getattr"
    )
    for bad in ["json.dumps", ":dumps", "json:", ""]:
        try:
            import_from_string(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad!r} 格式不对，应该抛 ValueError")
    try:
        import_from_string("no_such_module_xyz:f")
    except ModuleNotFoundError:
        pass
    else:
        raise AssertionError("模块不存在时应该抛 ModuleNotFoundError")
    try:
        import_from_string("json:no_such_attr")
    except AttributeError:
        pass
    else:
        raise AssertionError("属性不存在时应该抛 AttributeError")


# 练习 6 的检查：在子进程里运行 pytest，先用正确的 chunk_text，再逐个换成错误实现
_PYTEST_RUNNER = r"""
import json
import sys

import pytest

import demo_pkg.chunking as target

variant, out_path, test_file = sys.argv[1], sys.argv[2], sys.argv[3]


def _validate(size, overlap):
    if size <= 0:
        raise ValueError("size 必须大于 0")
    if not 0 <= overlap < size:
        raise ValueError("overlap 必须满足 0 <= overlap < size")


def drop_tail(text, size, overlap=0):
    _validate(size, overlap)
    return [text[i : i + size] for i in range(0, len(text) - size + 1, size - overlap)]


def ignore_overlap(text, size, overlap=0):
    _validate(size, overlap)
    return [text[i : i + size] for i in range(0, len(text), size)]


def extra_tail(text, size, overlap=0):
    _validate(size, overlap)
    return [text[i : i + size] for i in range(0, len(text), size - overlap)]


def empty_blank(text, size, overlap=0):
    if not text:
        _validate(size, overlap)
        return [""]
    return original(text, size, overlap)


def no_size_check(text, size, overlap=0):
    if size <= 0:
        return []
    return original(text, size, overlap)


def no_overlap_check(text, size, overlap=0):
    if size <= 0:
        raise ValueError("size 必须大于 0")
    return original(text, size, max(0, min(overlap, size - 1)))


original = target.chunk_text
if variant != "correct":
    target.chunk_text = globals()[variant]


class Collector:
    def __init__(self):
        self.collected = 0
        self.passed = []
        self.failed = []
        self.todo = False

    def pytest_collection_modifyitems(self, items):
        self.collected = len(items)

    def pytest_runtest_logreport(self, report):
        if report.failed:
            self.failed.append(report.nodeid)
            if "NotImplementedError" in str(report.longrepr):
                self.todo = True
        elif report.when == "call" and report.passed:
            self.passed.append(report.nodeid)


collector = Collector()
code = pytest.main([test_file, "-q", "-p", "no:cacheprovider"], plugins=[collector])
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "exit_code": int(code),
            "collected": collector.collected,
            "passed": collector.passed,
            "failed": collector.failed,
            "todo": collector.todo,
        },
        f,
    )
"""

_MUTANTS = {
    "drop_tail": "最后一段不足 size 长度时被丢掉了",
    "ignore_overlap": "完全忽略了 overlap 参数",
    "extra_tail": "到达文本末尾后没有停，多出被上一块完全包含的块",
    "empty_blank": "空字符串返回了 [''] 而不是 []",
    "no_size_check": "size <= 0 时没有抛 ValueError",
    "no_overlap_check": "overlap 不满足 0 <= overlap < size 时没有抛 ValueError",
}


def _run_chunk_tests(variant):
    import json
    import os
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    here = Path(__file__).resolve().parent
    fd, out_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        subprocess.run(
            [
                sys.executable,
                "-c",
                _PYTEST_RUNNER,
                variant,
                out_path,
                "练习_test_chunk.py",
            ],
            cwd=here,
            capture_output=True,
            text=True,
            timeout=60,
        )
        text = Path(out_path).read_text(encoding="utf-8")
        return json.loads(text) if text else None
    finally:
        os.remove(out_path)


def _check_chunk_tests():
    import ast
    from pathlib import Path

    test_file = Path(__file__).resolve().parent / "练习_test_chunk.py"
    result = _run_chunk_tests("correct")
    if result is None:
        raise AssertionError(
            "pytest 没有正常运行，先自己执行 python -m pytest 练习_test_chunk.py -q 看看报错"
        )
    if result["todo"] or (result["collected"] == 0 and result["exit_code"] == 5):
        raise NotImplementedError
    if result["exit_code"] not in (0, 1):
        raise AssertionError(
            "收集测试时出错，先自己执行 python -m pytest 练习_test_chunk.py -q 看看报错"
        )
    if result["failed"]:
        raise AssertionError(
            f"这些测试在正确的 chunk_text 上失败了：{result['failed']}"
        )
    tree = ast.parse(test_file.read_text(encoding="utf-8"))
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "parametrize" in attrs, "至少要用一次 @pytest.mark.parametrize"
    assert "raises" in attrs, "至少要用一次 pytest.raises"
    missed = []
    for variant, hint in _MUTANTS.items():
        mutant_result = _run_chunk_tests(variant)
        if mutant_result is not None and not mutant_result["failed"]:
            missed.append(hint)
    if missed:
        raise AssertionError("这些错误实现没有被你的测试发现：" + "；".join(missed))


if __name__ == "__main__":
    checks = [
        ("练习 1 KbSearchArgs", _check_kb_search_args),
        ("练习 2 to_openai_tool", _check_to_openai_tool),
        ("练习 3 parse_tool_args", _check_parse_tool_args),
        ("练习 4 ChatMessage", _check_chat_message),
        ("练习 5 import_from_string", _check_import_from_string),
        ("练习 6 练习_test_chunk.py", _check_chunk_tests),
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
