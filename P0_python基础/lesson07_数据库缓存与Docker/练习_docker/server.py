"""练习 6 用的应用，不需要修改。容器里用 uvicorn server:api 启动。"""
import os

from fastapi import FastAPI

api = FastAPI()


@api.get("/")
def index():
    return {"message": "练习 6 的容器跑起来了", "app_env": os.environ.get("APP_ENV", "dev")}
