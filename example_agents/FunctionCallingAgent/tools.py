import json
from typing import Any, Callable, Dict, List


class ToolRegistry:
    """
    工具注册表。
    和 ReAct 版的 ToolExecutor 相比，多了一份 JSON Schema：
    模型靠它知道每个工具叫什么、做什么、需要哪些参数。
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, parameters: Dict[str, Any], func: Callable[..., str]):
        self._tools[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
            "func": func,
        }

    def schemas(self) -> List[Dict[str, Any]]:
        """传给 chat.completions.create(tools=...) 的列表。"""
        return [tool["schema"] for tool in self._tools.values()]

    def execute(self, name: str, arguments_json: str) -> str:
        """
        执行一次工具调用。所有错误都转成字符串返回给模型，
        让模型有机会看到错误后自己修正参数，而不是让程序崩溃。
        """
        tool = self._tools.get(name)
        if tool is None:
            return f"错误：不存在名为 '{name}' 的工具。"
        try:
            # 模型返回的 arguments 是 JSON 字符串，不是 dict，而且可能格式不合法。
            arguments = json.loads(arguments_json or "{}")
        except json.JSONDecodeError as e:
            return f"错误：参数不是合法 JSON（{e}），原始参数：{arguments_json}"
        try:
            return str(tool["func"](**arguments))
        except TypeError as e:
            return f"错误：参数与工具定义不匹配（{e}）。"
        except Exception as e:
            return f"错误：工具执行失败（{e}）。"
