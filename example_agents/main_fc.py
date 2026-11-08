import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from FunctionCallingAgent import FunctionCallingAgent, ToolRegistry
from FunctionCallingAgent.builtin_tools import (
    CALCULATE_SCHEMA,
    GET_CURRENT_TIME_SCHEMA,
    calculate,
    get_current_time,
)

load_dotenv()

if __name__ == "__main__":
    # 和 ReAct 版共用同一组环境变量。
    # 云端示例：LLM_BASE_URL=https://api.deepseek.com
    # 本地 Ollama：LLM_BASE_URL=http://localhost:11434/v1，LLM_API_KEY 随便填
    client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"))
    model = os.getenv("LLM_MODEL_ID")

    registry = ToolRegistry()
    registry.register("calculate", "计算数学表达式，需要精确数值结果时使用。", CALCULATE_SCHEMA, calculate)
    registry.register("get_current_time", "获取某个时区的当前日期和时间。", GET_CURRENT_TIME_SCHEMA, get_current_time)

    # 配了 SerpApi 才注册搜索工具（需要 pip install google-search-results）
    if os.getenv("SERAPI_API_KEY"):
        from ReactAgent.tools import search

        registry.register(
            "search",
            "网页搜索。回答时事或你不知道的事实时使用。",
            {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索关键词"}},
                "required": ["query"],
            },
            search,
        )

    question = sys.argv[1] if len(sys.argv) > 1 else "现在北京时间几点？另外帮我算一下 (1234 + 5678) * 3 等于多少。"
    agent = FunctionCallingAgent(client, model, registry)
    agent.run(question)
