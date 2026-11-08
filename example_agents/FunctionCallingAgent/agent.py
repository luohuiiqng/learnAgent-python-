from typing import Any, Dict, List, Optional

from openai import OpenAI

from .tools import ToolRegistry

SYSTEM_PROMPT = "你是一个能调用工具的助手。需要实时信息或精确计算时，调用工具，不要猜。"


class FunctionCallingAgent:
    """
    基于原生 Function Calling 的智能体。

    和 ReActAgent 的区别：
    - 不需要在 prompt 里描述输出格式，工具定义通过 tools 参数传入。
    - 不需要正则解析，模型直接返回结构化的 tool_calls。
    - 历史记录是标准的 messages 列表（assistant / tool 角色），而不是拼接的字符串。
    """

    def __init__(self, client: OpenAI, model: str, registry: ToolRegistry, max_steps: int = 10):
        self.client = client
        self.model = model
        self.registry = registry
        self.max_steps = max_steps
        self.messages: List[Dict[str, Any]] = []

    def run(self, question: str) -> Optional[str]:
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        for step in range(1, self.max_steps + 1):
            print(f"--- 第 {step} 步 ---")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.registry.schemas(),
                tool_choice="auto",  # 由模型决定调不调工具
                temperature=0,
            )
            message = response.choices[0].message

            # 1. 没有工具调用，说明模型给出了最终答案
            if not message.tool_calls:
                print(f"🎉 最终答案: {message.content}")
                self.messages.append({"role": "assistant", "content": message.content})
                return message.content

            # 2. 先把 assistant 的这条消息（含 tool_calls）原样放回历史。
            #    缺了它，后面的 tool 消息找不到对应的调用，API 会报错。
            self.messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in message.tool_calls
                ],
            })

            # 3. 执行每个工具调用。模型可能一次返回多个（并行工具调用）。
            for call in message.tool_calls:
                print(f"🎬 调用: {call.function.name}({call.function.arguments})")
                result = self.registry.execute(call.function.name, call.function.arguments)
                print(f"👀 结果: {result}")
                # tool_call_id 把结果和具体哪一次调用对应起来
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        print("已达到最大步数，流程终止。")
        return None
