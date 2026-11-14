"""
第一课练习。补全每个函数，然后运行：python 练习.py
运行结果里每道题会显示 ✅ / ❌ / ⏳（未完成）。

规则：
- 只改函数体，不要改函数签名和下面的检查代码。
- 这是练习不是考试，可以回看 README 和示例，但不要让 AI 替你写。
- 不要用 copy.deepcopy 和 collections.Counter，用这节课学的基础写法完成。
"""
import copy


# 练习 1（P0-03）
def append_unique(item, items=None):
    """把 item 追加到 items 末尾（已存在则不追加），返回这个列表。
    不传 items 时，每次调用都要从一个新的空列表开始。

    append_unique(1)          -> [1]
    append_unique(2)          -> [2]        （不能是 [1, 2]）
    append_unique(1, [1, 2])  -> [1, 2]
    """
    if items is None:
        items = [item]
    if  item not in items:
        items.append(item)
    return items
            


# 练习 2（P0-02）
def word_freq(text):
    """统计词频：按空白字符切分，不区分大小写，返回 {小写单词: 次数}。

    word_freq("Qt qt  Python") -> {"qt": 2, "python": 1}
    word_freq("")              -> {}
    """
    if text == "" or text == None:
        return {}
    low_text = text.lower()
    strs = " ".join(low_text.split())
    strs = strs.split(' ')
    #4.统计句中每个词出现的次数
    list = {}
    for str in strs:
        if str == '':
            continue
        if list.get(str) == None :
            list[str] = 1
        else:
            list[str] += 1
    return list        



# 练习 3（P0-02）
def group_by_first_letter(words):
    """按首字母（小写）分组，组内保持原顺序，忽略空字符串。

    group_by_first_letter(["Qt", "python", "qml", "", "Pydantic"])
    -> {"q": ["Qt", "qml"], "p": ["python", "Pydantic"]}
    """
    q_dict = {}
    for k_str in words:
        q_str = k_str.lower()
        if q_str != "":
            if q_str[0] not in q_dict:
                q_dict[q_str[0]] = [k_str]
            else:
                q_dict[q_str[0]].append(k_str)
    return q_dict


# 练习 4（P0-01）
def make_grid(rows, cols, fill=0):
    """创建 rows 行 cols 列的二维列表，每个格子是 fill。
    修改任意一个格子，不能影响其他行。

    make_grid(2, 3) -> [[0, 0, 0], [0, 0, 0]]
    """
    return [[fill for _ in range(cols)] for _ in range(rows)]

def copy_config(str_src):
    output = {}
    if isinstance(str_src,dict):
        for key in str_src:
             output[key] = copy_config(str_src[key])
    else:
        output = str_src
    return output

# 练习 5（P0-01，较难）
def merge_config(base, override):
    """合并两份配置，返回一个新 dict：
    - override 中的键覆盖 base 中的同名键；
    - 如果同名键两边的值都是 dict，就递归合并，而不是整个替换；
    - 不能修改 base 和 override；
    - 修改返回结果（包括嵌套的 dict），也不能影响 base 和 override。
    假设配置中的值只有 dict、str、int、float、bool、None 这几种。

    merge_config({"llm": {"model": "qwen", "temperature": 0.7}, "debug": False},
                 {"llm": {"temperature": 0}, "debug": True})
    -> {"llm": {"model": "qwen", "temperature": 0}, "debug": True}
    """
    print(f"base:{base}. override:{override}")
    print("===========")
    c_base = copy_config(base)
    c_override = copy_config(override)
    if type(base) != type(override) or type(base) != dict:
        return c_override

    for cb_base in c_base:
        if cb_base in c_override:
            if  isinstance(c_base.get(cb_base),dict) and c_override.get(cb_base) != None:
                c_override[cb_base] = merge_config(c_base.get(cb_base),c_override.get(cb_base))
        else:
            c_override[cb_base] = c_base.get(cb_base)
    print(f"c_override: {c_override}")
    return c_override



# 练习 6（P0-03）
def call_tool(registry, name, arguments):
    """按名字调用工具，和 example_agents 里 ToolRegistry.execute 的思路一样。
    registry: {工具名: 函数}；arguments: {参数名: 参数值}
    - 正常时返回 str(函数返回值)
    - 工具不存在时返回 "错误：未知工具 <name>"
    - 参数和函数不匹配（缺参数、多参数）时返回 "错误：参数不匹配"

    call_tool({"add": lambda a, b: a + b}, "add", {"a": 1, "b": 2}) -> "3"
    """
    func = registry.get(name)
    if func is None:
        return f"错误：未知工具 {name}"
    try:
        result = func(**arguments)
        print(f"re:{str(result)}")
        return str(result)
    except TypeError:
        return "错误：参数不匹配"


# ---------------------------------------------------------------------------
# 下面是检查代码，不要修改
# ---------------------------------------------------------------------------


def _check_append_unique():
    assert append_unique(1) == [1]
    assert append_unique(2) == [2], "第二次调用不应该带着上次的结果"
    assert append_unique(1, [1, 2]) == [1, 2]
    lst = [5]
    assert append_unique(6, lst) is lst, "传入列表时应该原地追加并返回同一个列表"
    assert lst == [5, 6]


def _check_word_freq():
    assert word_freq("Qt qt  Python") == {"qt": 2, "python": 1}
    assert word_freq("") == {}
    assert word_freq("a\tb\na A") == {"a": 3, "b": 1}


def _check_group_by_first_letter():
    words = ["Qt", "python", "qml", "", "Pydantic"]
    assert group_by_first_letter(words) == {"q": ["Qt", "qml"], "p": ["python", "Pydantic"]}
    assert words == ["Qt", "python", "qml", "", "Pydantic"], "不能修改输入"
    assert group_by_first_letter([]) == {}


def _check_make_grid():
    g = make_grid(2, 3)
    assert g == [[0, 0, 0], [0, 0, 0]]
    g[0][0] = 9
    assert g == [[9, 0, 0], [0, 0, 0]], "修改一行影响到了其他行"
    assert make_grid(0, 3) == []
    assert make_grid(1, 2, fill="x") == [["x", "x"]]


def _check_merge_config():
    base = {"llm": {"model": "qwen", "temperature": 0.7}, "debug": False}
    override = {"llm": {"temperature": 0}, "debug": True, "name": "agent"}
    result = merge_config(base, override)
    assert result == {"llm": {"model": "qwen", "temperature": 0}, "debug": True, "name": "agent"}
    assert base == {"llm": {"model": "qwen", "temperature": 0.7}, "debug": False}, "base 被修改了"
    assert override == {"llm": {"temperature": 0}, "debug": True, "name": "agent"}, "override 被修改了"
    result2 = merge_config(base, {})
    result2["llm"]["model"] = "deepseek"
    assert base["llm"]["model"] == "qwen", "修改结果影响到了 base（嵌套 dict 被共享了）"
    deep = merge_config({"a": {"b": {"c": 1, "d": 2}}}, {"a": {"b": {"d": 3}}})
    assert deep == {"a": {"b": {"c": 1, "d": 3}}}, "多层嵌套没有递归合并"
    assert merge_config({"a": {"x": 1}}, {"a": 5}) == {"a": 5}, "override 的值不是 dict 时应直接覆盖"


def _check_call_tool():
    registry = {"add": lambda a, b: a + b, "hello": lambda name="world": f"hello {name}"}
    assert call_tool(registry, "add", {"a": 1, "b": 2}) == "3"
    assert call_tool(registry, "hello", {}) == "hello world"
    assert call_tool(registry, "hello", {"name": "qt"}) == "hello qt"
    assert call_tool(registry, "mul", {"a": 1}) == "错误：未知工具 mul"
    assert call_tool(registry, "add", {"a": 1}) == "错误：参数不匹配"
    assert call_tool(registry, "add", {"a": 1, "b": 2, "c": 3}) == "错误：参数不匹配"


if __name__ == "__main__":
    checks = [
        ("练习 1 append_unique", _check_append_unique),
        ("练习 2 word_freq", _check_word_freq),
        ("练习 3 group_by_first_letter", _check_group_by_first_letter),
        ("练习 4 make_grid", _check_make_grid),
        ("练习 5 merge_config", _check_merge_config),
        ("练习 6 call_tool", _check_call_tool),
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
