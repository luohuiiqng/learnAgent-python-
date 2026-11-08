"""P0-19 最小的容器化 FastAPI 应用。

本机直接运行（不用 Docker）：
    python app.py
用 Docker 运行（在 docker_demo 目录）：
    docker build -t lesson07-demo .
    docker run --rm -p 8000:8000 -e APP_ENV=docker lesson07-demo
然后访问：
    NO_PROXY=localhost,127.0.0.1 curl http://localhost:8000/
"""
import os
import platform
import socket

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def index():
    return {
        "message": "hello from lesson07",
        "app_env": os.environ.get("APP_ENV", "dev"),  # 配置从环境变量读，镜像不用改就能换环境
        "hostname": socket.gethostname(),  # 在容器里，这是容器 ID 的前 12 位
        "python": platform.python_version(),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # 容器里必须监听 0.0.0.0。只监听 127.0.0.1 的话，只有容器自己能访问，端口映射也没用
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
