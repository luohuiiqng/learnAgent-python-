# 基础镜像：官方 Python 3.13 的 slim 版（Debian 精简版，约 120 MB；完整版约 1 GB）
FROM python:3.13-slim

# 不生成 .pyc 文件；print 输出不缓冲，docker logs 能立刻看到
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 之后的命令都在 /app 目录下执行，目录不存在会自动创建
WORKDIR /app

# 先只复制依赖清单并安装依赖。
# 只要 requirements.txt 没变，这两层就直接用缓存，改代码后重新 build 不用重新装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制代码。代码经常改，放在后面，只让这一层及之后的层失效
COPY . .

# 用普通用户运行，不用 root，容器被攻破时权限更小
RUN useradd --create-home appuser
USER appuser

# 声明容器内监听的端口，只是文档作用。真正对外暴露靠 docker run -p
EXPOSE 8000

# 容器启动时执行的命令。用 JSON 数组（exec 形式），进程能直接收到 docker stop 发的 SIGTERM
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
