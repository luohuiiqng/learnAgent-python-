"""P0-15 FastAPI 基础：路由、参数校验、请求体、状态码、依赖注入、APIRouter、lifespan。

两种运行方式：
    python 01_FastAPI基础.py          启动服务 http://127.0.0.1:8000 ，浏览器打开 /docs
    python 01_FastAPI基础.py --demo   不启动服务，用 TestClient 自动发一遍请求并打印结果

服务启动后可以用 curl 试：
    curl http://127.0.0.1:8000/health
    curl -X POST http://127.0.0.1:8000/todos -H "X-API-Key: key-alice" \
         -H "Content-Type: application/json" -d '{"title": "学 FastAPI"}'
    curl "http://127.0.0.1:8000/todos?limit=5" -H "X-API-Key: key-alice"
"""

import asyncio
import sys
import time
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
import uvicorn
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. 数据模型：请求体和响应体都用 Pydantic 模型描述
# ---------------------------------------------------------------------------


class TodoCreate(BaseModel):
    """POST /todos 的请求体。字段约束不满足时，FastAPI 自动返回 422。"""

    title: str = Field(min_length=1, max_length=100)
    done: bool = False


class TodoOut(BaseModel):
    """返回给客户端的样子。response_model 会按它过滤字段。"""

    id: int
    title: str
    done: bool


class TodoInDB(TodoOut):
    """服务端内部存的样子，比 TodoOut 多一个 owner 字段，不想暴露给客户端。"""

    owner: str


class TodoPage(BaseModel):
    items: list[TodoOut]
    total: int


# ---------------------------------------------------------------------------
# 2. 共享资源：一个内存“数据库”，在 lifespan 里创建，挂到 app.state 上
# ---------------------------------------------------------------------------


class TodoStore:
    def __init__(self):
        self._items: dict[int, TodoInDB] = {}
        self._next_id = 1

    def add(self, title: str, done: bool, owner: str) -> TodoInDB:
        todo = TodoInDB(id=self._next_id, title=title, done=done, owner=owner)
        self._items[todo.id] = todo
        self._next_id += 1
        return todo

    def get(self, todo_id: int) -> TodoInDB | None:
        return self._items.get(todo_id)

    def delete(self, todo_id: int) -> bool:
        return self._items.pop(todo_id, None) is not None

    def all(self) -> list[TodoInDB]:
        return list(self._items.values())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # yield 之前：服务启动时执行一次。适合创建数据库连接池、httpx.AsyncClient、OpenAI 客户端
    print("[lifespan] 启动：创建 TodoStore 和 httpx.AsyncClient")
    app.state.store = TodoStore()
    app.state.http = httpx.AsyncClient(timeout=10)  # 本示例不发外部请求，只演示创建和释放
    yield
    # yield 之后：服务关闭时执行一次，释放资源
    await app.state.http.aclose()
    print("[lifespan] 关闭：httpx.AsyncClient 已 aclose")


# ---------------------------------------------------------------------------
# 3. 依赖：FastAPI 在调用路由函数之前，先调用依赖函数，把返回值作为参数传进去
# ---------------------------------------------------------------------------

API_KEYS = {"key-alice": "alice", "key-bob": "bob"}


def get_store(request: Request) -> TodoStore:
    """提供共享资源。路由里写 store: Annotated[TodoStore, Depends(get_store)] 就能拿到它。"""
    return request.app.state.store


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    """从请求头 X-API-Key 取 key，返回用户名。参数名里的下划线会自动对应到请求头里的连字符。

    注意这里把参数声明成可选（默认 None），再自己抛 401。
    如果写成必填的 Header()，缺少请求头时 FastAPI 会先返回 422，轮不到这里的 401。
    """
    if x_api_key is None or x_api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或错误的 API Key",
        )
    return API_KEYS[x_api_key]


StoreDep = Annotated[TodoStore, Depends(get_store)]
UserDep = Annotated[str, Depends(require_api_key)]

# ---------------------------------------------------------------------------
# 4. APIRouter：把 /todos 相关路由放在一起，类似把一组槽函数放进一个独立的类
# ---------------------------------------------------------------------------

# dependencies=[...] 对这个 router 下的所有路由生效：每个请求都要先通过 API Key 校验
todo_router = APIRouter(prefix="/todos", tags=["todos"], dependencies=[Depends(require_api_key)])


@todo_router.post("", status_code=status.HTTP_201_CREATED, response_model=TodoOut)
def create_todo(body: TodoCreate, store: StoreDep, user: UserDep):
    # body 是已经校验好的 TodoCreate 对象，不是 dict
    # 返回的是 TodoInDB（带 owner），response_model=TodoOut 会把 owner 过滤掉
    return store.add(body.title, body.done, owner=user)


@todo_router.get("", response_model=TodoPage)
def list_todos(
    store: StoreDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,  # 查询参数 ?limit=..，范围不对返回 422
    offset: Annotated[int, Query(ge=0)] = 0,
    keyword: str | None = None,  # 可选查询参数，不传就是 None
):
    items = store.all()
    if keyword is not None:
        items = [t for t in items if keyword in t.title]
    return {"items": items[offset : offset + limit], "total": len(items)}


@todo_router.get("/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int, store: StoreDep):
    # todo_id 是路径参数，类型标注 int：/todos/abc 会直接返回 422，函数不会被调用
    todo = store.get(todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"todo {todo_id} 不存在")
    return todo


@todo_router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, store: StoreDep):
    if not store.delete(todo_id):
        raise HTTPException(status_code=404, detail=f"todo {todo_id} 不存在")
    # 204 表示“成功但没有响应体”，函数返回 None 即可


# ---------------------------------------------------------------------------
# 5. async def 和普通 def 路由
# ---------------------------------------------------------------------------

block_router = APIRouter(prefix="/block", tags=["async 与阻塞"])


@block_router.get("/async-await")
async def async_await():
    await asyncio.sleep(0.5)  # 让出事件循环，其他请求可以同时处理
    return {"route": "async + await asyncio.sleep"}


@block_router.get("/async-blocking")
async def async_blocking():
    time.sleep(0.5)  # 错误示范：在 async 路由里调用阻塞函数，整个事件循环被卡住 0.5 秒
    return {"route": "async + time.sleep（错误示范）"}


@block_router.get("/sync-blocking")
def sync_blocking():
    time.sleep(0.5)  # 普通 def 路由在线程池里执行，阻塞的只是一个工作线程
    return {"route": "def + time.sleep"}


# ---------------------------------------------------------------------------
# 6. 组装应用
# ---------------------------------------------------------------------------

app = FastAPI(title="第六课示例：Todo API", lifespan=lifespan)
app.include_router(todo_router)
app.include_router(block_router)


@app.get("/health")
def health():
    """不需要 API Key 的公开接口。"""
    return {"status": "ok"}


@app.get("/me")
def me(user: UserDep):
    """单个路由上用依赖：直接拿到 require_api_key 的返回值。"""
    return {"user": user}


# ---------------------------------------------------------------------------
# 离线演示
# ---------------------------------------------------------------------------


def section(title):
    print(f"\n===== {title} =====")


def show(resp):
    url = resp.request.url
    target = url.path + ("?" + url.query.decode() if url.query else "")
    body = resp.text if resp.content else "(空)"
    print(f"  {resp.request.method} {target} -> {resp.status_code} {body}")


async def measure_concurrency():
    """同时发 3 个请求，看总耗时。ASGITransport 在当前事件循环里直接调用 app，不走网络。"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ["/block/async-await", "/block/async-blocking", "/block/sync-blocking"]:
            start = time.perf_counter()
            await asyncio.gather(*(client.get(path) for _ in range(3)))
            print(f"  3 个并发请求 {path:<22} 总耗时 {time.perf_counter() - start:.2f}s")


def demo():
    from fastapi.testclient import TestClient

    # 用 with 才会执行 lifespan 的启动和关闭部分；不用 with，app.state.store 不存在
    with TestClient(app) as client:
        alice = {"X-API-Key": "key-alice"}

        section("1. 公开接口")
        show(client.get("/health"))

        section("2. 依赖注入做鉴权：缺 key、错 key 都是 401")
        show(client.get("/me"))
        show(client.get("/me", headers={"X-API-Key": "wrong"}))
        show(client.get("/me", headers=alice))

        section("3. 请求体校验和 201")
        show(client.post("/todos", json={"title": "学 FastAPI"}, headers=alice))
        show(client.post("/todos", json={"title": "学 SSE", "done": True}, headers=alice))
        print("  ↑ 响应里没有 owner 字段，被 response_model=TodoOut 过滤掉了")
        r = client.post("/todos", json={"title": ""}, headers=alice)
        print(f"  标题为空 -> {r.status_code}，错误位置 {r.json()['detail'][0]['loc']}")
        r = client.post("/todos", json={"done": "不是布尔"}, headers=alice)
        print(f"  缺 title、done 类型错 -> {r.status_code}，共 {len(r.json()['detail'])} 条错误")

        section("4. 路径参数和 404")
        show(client.get("/todos/1", headers=alice))
        show(client.get("/todos/99", headers=alice))
        r = client.get("/todos/abc", headers=alice)
        print(f"  /todos/abc -> {r.status_code}，{r.json()['detail'][0]['msg']}")

        section("5. 查询参数校验")
        show(client.get("/todos", params={"limit": 1}, headers=alice))
        show(client.get("/todos", params={"keyword": "SSE"}, headers=alice))
        r = client.get("/todos", params={"limit": 0}, headers=alice)
        print(f"  limit=0 -> {r.status_code}，{r.json()['detail'][0]['msg']}")

        section("6. 204 删除")
        show(client.delete("/todos/1", headers=alice))
        show(client.delete("/todos/1", headers=alice))

        section("7. 测试时替换依赖：dependency_overrides")
        app.dependency_overrides[require_api_key] = lambda: "测试用户"
        show(client.get("/me"))  # 不带请求头也通过了
        app.dependency_overrides.clear()
        show(client.get("/me"))

    section("8. async def 和 def 路由的并发表现")
    asyncio.run(measure_concurrency())
    print("  async-blocking 约 1.5s：time.sleep 卡住了事件循环，3 个请求只能排队")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        # 直接传 app 对象启动。传对象时不能用 reload=True（热重载需要 "模块名:app" 字符串）
        uvicorn.run(app, host="127.0.0.1", port=8000)
