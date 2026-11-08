import ast
import operator
from datetime import datetime
from zoneinfo import ZoneInfo

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError("只支持数字和 + - * / ** % 运算")


def calculate(expression: str) -> str:
    """
    计算数学表达式。
    不能直接用 eval()：参数来自模型输出，等于执行不可信代码。
    这里用 ast 只放行数字和算术运算符。
    """
    return str(_eval_node(ast.parse(expression, mode="eval").body))


CALCULATE_SCHEMA = {
    "type": "object",
    "properties": {
        "expression": {
            "type": "string",
            "description": "数学表达式，例如 '(3 + 5) * 2 ** 10'",
        }
    },
    "required": ["expression"],
}


def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """返回指定时区的当前时间。"""
    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M:%S %A")


GET_CURRENT_TIME_SCHEMA = {
    "type": "object",
    "properties": {
        "timezone": {
            "type": "string",
            "description": "IANA 时区名，例如 'Asia/Shanghai'、'America/New_York'。默认 Asia/Shanghai",
        }
    },
    "required": [],
}
