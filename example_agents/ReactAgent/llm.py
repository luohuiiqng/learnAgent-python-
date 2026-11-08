from typing import List,Dict
import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from openai import OpenAI


class HelloAgentsLLM:
    """LLM客户端"""
    def __init__(self,model:str=None,apiKey:str=None,baseUrl:str=None,timeout:int=10000):
         self.model=model or os.getenv("LLM_MODEL_ID")
         apiKey = apiKey or os.getenv("LLM_API_KEY")
         baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
         timeout = timeout or int(os.getenv("LLM_TIMEOUT",60))

         if not all([self.model,apiKey,baseUrl]):
             return ValueError("模型ID，api密钥和服务地址必须被提供或者在.env文件中定义.")

         self.api_key = apiKey
         self.base_url = baseUrl
         self.timeout = timeout
         self.client = OpenAI(api_key=apiKey,base_url=baseUrl,timeout=timeout)

    def _is_ollama(self)->bool:
        """本地 Ollama 的 OpenAI 兼容接口不会关闭思考通道。"""
        return urlparse(self.base_url).port == 11434

    def think(self,messages:List[Dict[str,str]],temperature:float=0)->str:
        """调用大模型思考"""
        print(f"正在调用{self.model}模型")

        try:
            # qwen3.5 默认把输出写进 reasoning，content 会一直是空的。
            # Ollama 原生接口可以用 think=false，让正文直接进入 content 并流式显示。
            if self._is_ollama():
                return self._think_ollama(messages, temperature)
            return self._think_openai(messages, temperature)
        except Exception as e:
            print(f"调用LLM API发生错误:{e}")
            return None

    def _think_ollama(self,messages:List[Dict[str,str]],temperature:float)->str:
        parsed = urlparse(self.base_url)
        url = f"{parsed.scheme}://{parsed.netloc}/api/chat"
        body = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "think": False,
            "options": {"temperature": temperature},
        }
        request = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        print("大语言模型响应成功，llm.py")
        collected_content = []
        with urlopen(request, timeout=self.timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise RuntimeError(data["error"])
                content = (data.get("message") or {}).get("content") or ""
                if content:
                    print(content, end="", flush=True)
                    collected_content.append(content)
                if data.get("done"):
                    break
        print("============================")
        return "".join(collected_content)

    def _think_openai(self,messages:List[Dict[str,str]],temperature:float)->str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream = True
        )
        #处理流式响应
        print("大语言模型响应成功，llm.py")
        collected_content = []
        for chunk in response:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content or ""
            print(content,end="",flush=True)
            collected_content.append(content)
        print("============================")
        return "".join(collected_content)
