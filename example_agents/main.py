from dotenv import load_dotenv
load_dotenv()


from ReactAgent import ReActAgent
from ReactAgent import HelloAgentsLLM
from ReactAgent import ToolExecutor
from ReactAgent.tools import search

# --- 工具初始化与使用示例 ---
if __name__ == '__main__':

   llm = HelloAgentsLLM()
   toolExecutor = ToolExecutor()
   search_description ="一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
   toolExecutor.registerTool("search", search_description, search)
   agent = ReActAgent(llm,toolExecutor,500)
   agent.run("英伟达最新的GPU型号是什么?")