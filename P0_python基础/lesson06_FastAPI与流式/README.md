# 第六课：FastAPI 与 SSE 流式响应

**覆盖知识点**：P0-15 FastAPI（路由、请求模型、依赖注入）、P0-16 FastAPI SSE 流式响应
**预计用时**：5 到 6 小时

本课以本机安装的版本为准：fastapi 0.116.1（底层 starlette 0.47.3）、uvicorn 0.35.0、httpx 0.28.1、pydantic 2.11.7。文中标“实测”的行为都在这些版本上跑过。

## 学习步骤

1. 按顺序读下面两部分。每读完一节，先用离线方式运行对应示例。`--demo` 不启动服务，用 TestClient 在进程内发请求并打印结果：

   ```bash
   cd P0_python基础/lesson06_FastAPI与流式
   python 01_FastAPI基础.py --demo
   python 02_SSE服务端.py --demo
   python 03_SSE客户端.py --demo
   ```

   用 `python`，不要用 `python3`。

2. 真实启动服务。服务端示例都监听 **127.0.0.1:8000**，同一时间只能运行一个，按 Ctrl+C 停止：

   ```bash
   python 01_FastAPI基础.py
   ```

   浏览器打开 http://127.0.0.1:8000/docs ，展开一个接口，点 “Try it out” 发请求。`/todos` 下的接口要在 `x-api-key` 一栏填 `key-alice`。也可以用 curl：

   ```bash
   curl http://127.0.0.1:8000/health
   curl -X POST http://127.0.0.1:8000/todos -H "X-API-Key: key-alice" \
        -H "Content-Type: application/json" -d '{"title": "学 FastAPI"}'
   curl -i http://127.0.0.1:8000/todos/99 -H "X-API-Key: key-alice"     # -i 显示状态码和响应头
   ```

3. 停掉 01，启动 SSE 服务，再开一个终端用 curl 看流式输出：

   ```bash
   python 02_SSE服务端.py
   # 另一个终端
   curl -N "http://127.0.0.1:8000/chat/stream?prompt=hello"
   curl -N http://127.0.0.1:8000/sse/format
   ```

   `-N` 关闭 curl 的输出缓冲，你会看到 `data:` 行一行一行地出现，而不是最后一次性出现。prompt 里有中文时用 `curl -N -G http://127.0.0.1:8000/chat/stream --data-urlencode "prompt=你好"`，直接把中文写进 URL 会被 uvicorn 拒绝（实测报 `Invalid HTTP request received`）。

   02 还在运行时，在第三个终端运行 Python 客户端：

   ```bash
   python 03_SSE客户端.py
   ```

   > **代理注意**：你的机器开了系统代理 127.0.0.1:8080。httpx 和 requests 默认会读取系统代理，访问 `127.0.0.1:8000` 的请求也会被发给代理，结果是 **503**。curl 不受影响。用 Python 访问本机服务时二选一：
   > - 运行前设置环境变量：`NO_PROXY=localhost,127.0.0.1 python 你的脚本.py`
   > - 代码里给 httpx 传 `trust_env=False`：`httpx.AsyncClient(trust_env=False)`。03 用的是这种方式。
   >
   > TestClient 不走网络，不受代理影响。

4. 完成 `练习.py` 里的 6 道题，运行 `python 练习.py`，直到全部通过。不需要启动服务。
5. 告诉教练“第六课学完了”，开始评估：L1 口述、L2 预测输出、L3 闭卷编码、L4 找 bug。

---

# 第一部分：FastAPI（P0-15）

## 1. HTTP 和 REST 速览

你在 Qt 里用 `QNetworkAccessManager` 当客户端发请求。这一课换到另一端：写服务端，接收请求、返回响应。

### 1.1 一个请求由哪几部分组成

```
POST /todos?notify=true HTTP/1.1        ← 方法、路径、查询参数
Host: 127.0.0.1:8000
X-API-Key: key-alice                     ← 请求头
Content-Type: application/json

{"title": "学 FastAPI"}                   ← 请求体
```

| 部分 | 例子 | Qt 客户端里对应的写法 |
|---|---|---|
| 方法 | `GET` `POST` | `manager.get(...)`、`manager.post(...)` |
| 路径参数 | `/todos/42` 里的 `42` | 拼进 `QUrl` 的路径 |
| 查询参数 | `?limit=10&offset=0` | `QUrlQuery` |
| 请求头 | `X-API-Key: ...` | `request.setRawHeader(...)` |
| 请求体 | JSON 文本 | `post(request, QByteArray)` 的第二个参数 |

### 1.2 方法

REST 风格用 URL 表示“资源”，用方法表示“对资源做什么”：

| 方法 | 含义 | 例子 |
|---|---|---|
| GET | 查询，不改数据 | `GET /todos`、`GET /todos/42` |
| POST | 创建 | `POST /todos` |
| PUT | 整体替换 | `PUT /todos/42` |
| PATCH | 部分修改 | `PATCH /todos/42`，只传要改的字段 |
| DELETE | 删除 | `DELETE /todos/42` |

### 1.3 状态码

| 状态码 | 含义 | 本课什么时候用 |
|---|---|---|
| 200 OK | 成功 | 查询成功 |
| 201 Created | 创建成功 | POST 创建资源 |
| 204 No Content | 成功，没有响应体 | DELETE 成功 |
| 400 Bad Request | 请求有问题（通用） | 业务层面的错误请求 |
| 401 Unauthorized | 没有认证或认证失败 | 缺少或错误的 API Key |
| 403 Forbidden | 认证了，但没有权限 | 普通用户访问管理接口 |
| 404 Not Found | 资源不存在 | 查不到这条待办 |
| 422 Unprocessable Entity | 格式对，但内容校验不通过 | FastAPI 参数校验失败时自动返回 |
| 500 Internal Server Error | 服务端代码出错 | 路由函数抛了未处理的异常 |
| 503 Service Unavailable | 服务暂时不可用 | 你的代理拦截本机请求时返回的就是它 |

2xx 成功，4xx 是客户端的错，5xx 是服务端的错。

## 2. FastAPI 应用与路由

### 2.1 谁负责什么

| 组件 | 职责 | 类比 |
|---|---|---|
| uvicorn | ASGI 服务器：监听端口、解析 HTTP 报文、运行事件循环 | `QTcpServer` 加上你自己写的 HTTP 解析 |
| FastAPI（基于 Starlette） | 框架：按方法和路径找到处理函数，校验参数，把返回值转成 JSON | 一张“URL → 槽函数”的分发表 |
| 路由函数 | 你写的业务逻辑 | 槽函数 |

ASGI 是 Python 异步 Web 服务器和框架之间的接口标准。uvicorn 和 FastAPI 都遵守它，所以能组合使用。

### 2.2 最小应用

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")          # 第三课的装饰器：把函数登记到路由表，函数本身不变
def health():
    return {"status": "ok"}  # dict、list、Pydantic 对象都会被自动转成 JSON
```

启动有两种方式：

| 方式 | 写法 | 说明 |
|---|---|---|
| 在代码里启动 | `uvicorn.run(app, host="127.0.0.1", port=8000)` | 本课示例用这种，`python 文件名.py` 就能跑 |
| 命令行启动 | `uvicorn main:app --reload` | `main` 是模块名，`app` 是模块里的变量名。`--reload` 改代码后自动重启 |

命令行方式要求文件名是合法的模块名。`01_FastAPI基础.py` 以数字开头，不能 import，所以本课用第一种。`uvicorn.run` 传 app 对象时不能用 `reload=True`，热重载要求传 `"模块名:app"` 字符串。真实项目里文件用英文命名，一般用命令行方式。

`host="127.0.0.1"` 只接受本机访问。改成 `"0.0.0.0"` 才能被局域网其他机器访问，在 docker 里部署时会用到。

### 2.3 自动文档

| 地址 | 内容 |
|---|---|
| `/docs` | Swagger UI，可以直接在网页上发请求 |
| `/redoc` | 另一种风格的只读文档 |
| `/openapi.json` | 机器可读的接口描述（OpenAPI 规范） |

文档是根据路由函数的参数类型、Pydantic 模型、`response_model` 自动生成的。类型标注写得越完整，文档越准确。

## 3. 路径参数、查询参数、请求体

### 3.1 FastAPI 怎么判断参数从哪里来

FastAPI 看函数参数的名字和类型标注，决定从请求的哪个部分取值：

| 参数声明 | 来源 | 例子 |
|---|---|---|
| 名字出现在路径的 `{}` 里 | 路径参数 | `@app.get("/todos/{todo_id}")` 配 `todo_id: int` |
| 简单类型（int、str、bool、float），不在路径里 | 查询参数 | `limit: int = 10` 对应 `?limit=5` |
| Pydantic 模型 | 请求体（JSON） | `body: TodoCreate` |
| `Annotated[str \| None, Header()]` | 请求头 | `x_api_key` 对应 `X-API-Key` |
| `Request` | 原始请求对象 | `request: Request` |
| `Annotated[T, Depends(f)]` | 依赖 f 的返回值 | 见第 5 节 |

```python
from typing import Annotated
from fastapi import Query
from pydantic import BaseModel, Field

class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    done: bool = False

@app.post("/todos")
def create_todo(body: TodoCreate):          # body 已经是校验好的 TodoCreate 对象
    ...

@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):                 # /todos/abc 直接返回 422，函数不会被调用
    ...

@app.get("/todos")
def list_todos(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,   # 1 <= limit <= 50
    keyword: str | None = None,                        # 可选，不传就是 None
):
    ...
```

`Query(ge=..., le=...)` 和第四课 Pydantic 的 `Field(ge=..., le=...)` 是同一套约束，`ge` 是大于等于，`le` 是小于等于。

### 3.2 校验失败：422

C++ 里收到请求要自己解析 JSON、判断字段是否存在、类型对不对。FastAPI 在调用你的函数之前就做完了，失败时直接返回 422，响应体指出哪里错了：

```json
{"detail": [{"type": "greater_than_equal", "loc": ["query", "limit"],
             "msg": "Input should be greater than or equal to 1", "input": "0", "ctx": {"ge": 1}}]}
```

`loc` 的第一项是来源（`path`、`query`、`header`、`body`），后面是字段名。

### 3.3 坑

- **路由按注册顺序匹配**。先注册 `/todos/{todo_id}` 再注册 `/todos/stats`，请求 `/todos/stats` 会先命中前者，`"stats"` 转 int 失败，返回 422（实测）。固定路径要写在带参数的路径前面。
- **请求头名字的转换**：参数名 `x_api_key` 会自动对应请求头 `x-api-key`。HTTP 请求头不区分大小写，`X-API-Key` 也能匹配。
- **查询参数都是字符串**：URL 里只有文本，`?limit=5` 收到的是 `"5"`，FastAPI 按类型标注转成 int。转不了就是 422。

## 4. 响应：response_model、状态码、HTTPException

### 4.1 response_model 过滤字段

服务端内部的数据往往比要返回的多（创建时间、所属用户、密码哈希）。`response_model` 指定返回给客户端的形状，多余字段会被过滤：

```python
class TodoOut(BaseModel):
    id: int
    title: str
    done: bool

class TodoInDB(TodoOut):
    owner: str           # 内部字段

@app.post("/todos", status_code=201, response_model=TodoOut)
def create_todo(body: TodoCreate):
    return TodoInDB(id=1, title=body.title, done=body.done, owner="alice")
    # 客户端收到 {"id": 1, "title": "...", "done": false}，没有 owner
```

`response_model` 还会校验返回值：返回的数据缺少 `TodoOut` 要求的字段时，服务端报错（500），而不是把残缺数据发出去。

### 4.2 状态码

成功时的状态码写在装饰器上。默认是 200：

```python
@app.post("/todos", status_code=201)                   # 也可以写 status.HTTP_201_CREATED
@app.delete("/todos/{todo_id}", status_code=204)       # 函数返回 None，响应体为空
```

### 4.3 HTTPException

出错时**抛出** `HTTPException`，FastAPI 把它转成对应状态码的响应：

```python
from fastapi import HTTPException

todo = store.get(todo_id)
if todo is None:
    raise HTTPException(status_code=404, detail=f"todo {todo_id} 不存在")
# 客户端收到 404，响应体 {"detail": "todo 99 不存在"}
```

它和第二课学的异常是同一个机制。在依赖函数里抛也一样有效，这是做鉴权的基础。

### 4.4 坑

- **返回错误字典不会改变状态码**：`return {"error": "不存在"}` 的状态码还是 200，客户端会以为成功了。要用 `raise HTTPException(...)`。
- **`return HTTPException(...)` 不等于 `raise`**：return 会把异常对象当普通数据返回。
- **未处理的异常是 500**：路由函数里抛出 `KeyError` 之类的普通异常，客户端收到 500。用 TestClient 测试时，异常默认会直接从 `client.get(...)` 里抛出来（`raise_server_exceptions=True`），方便定位。练习.py 正是利用这一点：你没写完的函数抛出 `NotImplementedError`，检查代码捕获到它，显示 ⏳。

## 5. 依赖注入 Depends

### 5.1 对照 Qt

在 Qt 里，一个组件需要网络服务时，好的写法是把服务对象从外面传进来，而不是组件自己 new 一个或者去拿全局单例：

```cpp
class TodoWidget : public QWidget {
public:
    TodoWidget(ApiClient *client, QWidget *parent = nullptr);  // 构造函数注入
};
```

这样测试时可以传一个假的 `ApiClient`。FastAPI 的 `Depends` 是同一个思路，只是注入的时机是**每个请求**：路由函数在参数里声明“我需要什么”，FastAPI 在调用它之前先调用提供者函数，把结果传进来。

```python
def get_store(request: Request) -> TodoStore:       # 提供者：返回共享资源
    return request.app.state.store

@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, store: Annotated[TodoStore, Depends(get_store)]):
    ...
```

依赖函数本身也可以声明参数（路径、查询、请求头、其他依赖），FastAPI 会递归解析。

### 5.2 常见用途

| 用途 | 例子 |
|---|---|
| 鉴权 | 从请求头取 API Key，校验失败抛 401，成功返回用户名 |
| 提供共享资源 | 数据库会话、httpx 客户端、模型客户端 |
| 复用公共参数 | 多个接口共用的分页参数 |

### 5.3 API Key 鉴权

```python
API_KEYS = {"key-alice": "alice"}

def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    if x_api_key is None or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="缺少或错误的 API Key")
    return API_KEYS[x_api_key]

UserDep = Annotated[str, Depends(require_api_key)]   # 起个别名，多处复用

@app.get("/me")
def me(user: UserDep):
    return {"user": user}
```

### 5.4 三种挂载方式

| 写法 | 作用范围 | 返回值 |
|---|---|---|
| 路由参数 `user: Annotated[str, Depends(f)]` | 这一个路由 | 作为参数传入 |
| `APIRouter(dependencies=[Depends(f)])` | router 下的所有路由 | 丢弃，只用来做检查 |
| `FastAPI(dependencies=[Depends(f)])` | 整个应用 | 丢弃 |

同一个请求里，同一个依赖被多处声明时只调用一次，结果会复用（实测）。

### 5.5 测试时替换依赖

```python
app.dependency_overrides[require_api_key] = lambda: "测试用户"   # 之后的请求不再校验 key
app.dependency_overrides.clear()                                  # 恢复
```

这就是 Qt 里给组件传假服务对象的做法。01 的 demo 第 7 节演示了效果。

### 5.6 坑

- **缺少必填请求头返回的是 422，不是 401**。如果写成 `x_api_key: Annotated[str, Header()]`（必填），没带请求头时 FastAPI 在调用你的函数之前就返回 422。要返回 401，就把参数声明成可选（默认 `None`），自己判断后抛 401。
- **`Depends(get_store)` 传的是函数本身**。写成 `Depends(get_store())` 会先调用一次，把返回值传给 Depends，注册路由时就报 `TypeError: ... is not a callable object`（实测）。
- **带 yield 的依赖和流式响应**：依赖可以写成生成器，`yield` 之前创建资源，之后清理。本机 0.116.1 实测：路由返回 `StreamingResponse` 时，`yield` 之后的清理代码在流开始发送**之前**就执行了。所以流式生成器里不要使用这类依赖提供的资源（比如一个会被关闭的数据库会话）。FastAPI 不同版本在这点上有过调整，升级后要重新确认。

## 6. APIRouter 和 lifespan

### 6.1 APIRouter 拆分路由

所有路由都写在 `app` 上，文件会越来越长。`APIRouter` 把一组相关路由放在一起，最后挂到 app 上：

```python
todo_router = APIRouter(prefix="/todos", tags=["todos"], dependencies=[Depends(require_api_key)])

@todo_router.get("/{todo_id}")      # 实际路径是 /todos/{todo_id}
def get_todo(todo_id: int): ...

app.include_router(todo_router)
```

真实项目里一般一个 router 一个文件，比如 `routers/todos.py`、`routers/chat.py`。`tags` 决定它们在 /docs 里的分组。

### 6.2 lifespan：启动时初始化，关闭时释放

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=10)   # 启动时执行一次
    yield                                             # 服务运行期间停在这里
    await app.state.http.aclose()                     # 关闭时执行一次

app = FastAPI(lifespan=lifespan)
```

路由里通过 `request.app.state.http` 拿到它，一般再包一层依赖函数（就是上面的 `get_store`）。

为什么不在每个请求里创建客户端：上一课讲过，`httpx.AsyncClient` 内部有连接池，复用它才能复用 TCP 和 TLS 连接。OpenAI 客户端、数据库连接池也一样。这相当于 Qt 程序里整个应用只创建一个 `QNetworkAccessManager`。

旧写法 `@app.on_event("startup")` 已经废弃，本机运行会报 `DeprecationWarning`。新代码用 lifespan。

### 6.3 坑

- **TestClient 不用 `with` 就不执行 lifespan**。`client = TestClient(app)` 直接发请求时，`app.state.store` 不存在，会报 `AttributeError`。要写 `with TestClient(app) as client:`。

## 7. async def 和普通 def 路由

### 7.1 规则

| 路由写法 | FastAPI 怎么执行 |
|---|---|
| `async def` | 直接在事件循环里运行（第五课的 asyncio 事件循环） |
| `def` | 放到线程池里运行，事件循环不等它 |

依赖函数也遵守同样的规则。线程池来自 anyio，默认最多 40 个线程（实测 `total_tokens` 为 40）。

### 7.2 实测对比

01 的 demo 第 8 节同时发 3 个请求，每个路由内部等待 0.5 秒：

| 路由 | 内部写法 | 3 个并发请求总耗时 |
|---|---|---|
| `/block/async-await` | `async def` + `await asyncio.sleep(0.5)` | 0.50s |
| `/block/async-blocking` | `async def` + `time.sleep(0.5)` | 1.51s |
| `/block/sync-blocking` | `def` + `time.sleep(0.5)` | 0.51s |

中间那一行是错误示范：`time.sleep` 不会让出事件循环，3 个请求只能排队执行。这和在 Qt 的 GUI 线程里调用阻塞函数会冻住整个界面是同一个问题。真实服务里，它卡住的是所有用户的请求，包括正在流式输出的连接。

### 7.3 怎么选

| 你要调用的东西 | 用哪种 |
|---|---|
| 异步库：`httpx.AsyncClient`、`AsyncOpenAI`、异步数据库驱动 | `async def`，配合 `await` |
| 只有同步版本的库：`requests`、同步 SDK、`time.sleep` | `def` |
| CPU 密集计算 | 两种都不解决问题（第五课的 GIL），要放到进程池或单独的服务 |

**async 路由里不要调用阻塞函数。** 常见的阻塞调用：`requests.get`、同步的 `OpenAI().chat.completions.create`、`time.sleep`、同步读写大文件。

## 8. 用 TestClient 测试

`fastapi.testclient.TestClient` 是 `httpx.Client` 的子类，用法和 httpx 一样，但请求不走网络，直接在进程内调用 app：

```python
from fastapi.testclient import TestClient

def test_create_todo():
    with TestClient(app) as client:          # with：执行 lifespan
        r = client.post("/todos", json={"title": "学 FastAPI"}, headers={"X-API-Key": "key-alice"})
        assert r.status_code == 201
        assert r.json()["title"] == "学 FastAPI"
```

放进 `test_xxx.py` 就能用第五课的 pytest 运行。它不经过网络，所以不受系统代理影响。

## P0-15 面试怎么问

1. FastAPI 里 `async def` 和普通 `def` 路由有什么区别？在 `async def` 路由里调用 `requests.get` 会发生什么？
2. 依赖注入 `Depends` 解决了什么问题？写单元测试时怎么替换掉一个依赖？
3. FastAPI 是怎么做参数校验的？校验失败返回什么状态码，和 400 有什么区别？
4. 服务里要用的 HTTP 客户端、数据库连接池应该在哪里创建？为什么不在每个请求里创建？

---

# 第二部分：SSE 流式响应（P0-16）

## 1. 为什么大模型接口要流式

大模型逐个 token 生成文本。一个 500 token 的回答可能要生成十几秒。

- 非流式：等全部生成完，一次返回。用户盯着空白界面等十几秒。
- 流式：生成一个 token 就发一个。用户等待的只是**首 token 延迟**（TTFT，Time To First Token），通常不到一两秒，之后文字逐渐出现。

02 的假模型首 token 延迟 0.6 秒，之后每 0.15 秒一个 token。实测 `/chat/once` 要约 3.5 秒才返回，`/chat/stream` 在 0.6 秒就收到第一条事件。总时间没有变短，变短的是用户感知到的等待。

流式还有一个好处：用户看到前几句不对就可以中断，服务端随之停止生成，省下后面的 token 费用（见第 5 节）。

## 2. SSE、WebSocket、普通分块传输

| | 普通分块传输（chunked） | SSE | WebSocket |
|---|---|---|---|
| 是什么 | HTTP/1.1 的传输方式：响应体分成多块发送，不需要预先知道总长度 | 一种文本格式（`text/event-stream`），跑在普通 HTTP 响应上 | 独立的协议，通过 HTTP Upgrade 握手后切换 |
| 方向 | 服务端 → 客户端 | 服务端 → 客户端 | 双向 |
| 消息边界 | 没有。块的边界可能被代理重新切分，不能当消息边界用 | 有。空行表示一条事件结束 | 有。按帧传输 |
| 浏览器 API | `fetch` 读流 | `EventSource`（自动重连），也可以 `fetch` 读流 | `WebSocket` |
| 典型用途 | 大文件下载 | 大模型输出、进度推送 | 聊天室、协同编辑、实时语音 |

几个关系要分清：

- SSE 不是新协议。它就是一个一直不结束的 HTTP 响应，内容按 SSE 格式书写。在 HTTP/1.1 上，这个响应用分块传输发送：实测 02 的响应头里有 `transfer-encoding: chunked`。
- 大模型对话是“客户端发一次请求，服务端持续输出”，SSE 正好够用，而且能直接经过现有的 HTTP 基础设施（负载均衡、鉴权、日志）。OpenAI 等大模型 API 的流式接口用的都是 SSE。
- 浏览器的 `EventSource` 只能发 GET 请求，也不能自定义请求头。大模型前端需要 POST 一段对话历史，并带上鉴权头，所以通常用 `fetch` 读取响应流、自己解析 SSE 格式。练习 6 做的就是这个解析。

## 3. text/event-stream 格式

### 3.1 字段

事件由若干行组成，每行一个字段，形如 `字段名: 值`，**一个空行表示一条事件结束**：

```
: 以冒号开头的是注释行，客户端忽略，常用来做心跳

id: 1
data: 第一条，没有 event 字段

event: tool
id: 2
data: {"step": "search", "status": "running"}

id: 3
data: 第一行
data: 第二行
data: 第三行

```

| 字段 | 含义 |
|---|---|
| `data` | 事件数据。一条事件里有多行 `data` 时，客户端用 `\n` 把它们拼起来。上面第三条事件的数据是 `"第一行\n第二行\n第三行"` |
| `event` | 事件类型。不写时是 `message` |
| `id` | 事件编号。`EventSource` 断线重连时会通过 `Last-Event-ID` 请求头带上最后收到的 id |
| `retry` | 建议客户端的重连间隔（毫秒） |
| `:` 开头 | 注释 |

细节规则：

- 文本必须是 UTF-8。
- 行结束符可以是 `\n`、`\r\n` 或 `\r`。
- 冒号后面如果紧跟一个空格，这一个空格不算值的一部分。`data:x` 和 `data: x` 的值都是 `x`。
- 不认识的字段忽略。

### 3.2 [DONE] 是 OpenAI 的约定

OpenAI 的流式接口每条事件的数据是一段 JSON，最后发一条 `data: [DONE]` 表示正常结束：

```
data: {"choices": [{"delta": {"content": "你"}}], ...}

data: {"choices": [{"delta": {"content": "好"}}], ...}

data: [DONE]

```

**SSE 标准里没有 `[DONE]`**。按标准，连接关闭就是流结束。OpenAI 加这一条，是为了让客户端能区分“正常结束”和“连接意外断开”。很多兼容 OpenAI 的服务也沿用了它。本课的 `/chat/stream` 用简化版：`data: {"delta": "..."}`，以 `data: [DONE]` 结束。

## 4. 服务端：StreamingResponse + 异步生成器

### 4.1 写法

```python
import json
from fastapi.responses import StreamingResponse

async def chat_events(prompt: str):
    async for token in fake_llm(prompt):
        payload = json.dumps({"delta": token}, ensure_ascii=False)
        yield f"data: {payload}\n\n"                 # 一条事件：data 行 + 空行
    yield "data: [DONE]\n\n"

@app.get("/chat/stream")
async def chat_stream(prompt: str):
    return StreamingResponse(
        chat_events(prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

执行顺序：路由函数立即返回 `StreamingResponse` 对象，这时生成器还没开始运行。Starlette 先发出响应头，然后用 `async for` 迭代生成器，每拿到一块就发一块。这就是第三课生成器“按需产出”的用法，`yield` 一次就是往网络上写一次。

`ensure_ascii=False` 让 JSON 里的中文保持原样。不加也是合法 JSON，只是中文会变成 `\u4f60` 这样的转义，客户端解析结果一样。

### 4.2 响应头

| 响应头 | 作用 |
|---|---|
| `Content-Type: text/event-stream` | 告诉客户端这是 SSE。用 `media_type` 参数设置；Starlette 会自动补上 `; charset=utf-8`（实测是 `text/event-stream; charset=utf-8`） |
| `Cache-Control: no-cache` | 不让浏览器或中间代理缓存这个响应 |
| `X-Accel-Buffering: no` | Nginx 专用。Nginx 默认会缓冲上游响应，攒够一定量再发给客户端，流式效果就没了。这个响应头让 Nginx 对这个响应关闭缓冲 |

### 4.3 为什么用 JSON 包装 token

token 本身可能包含换行。02 的假模型里有一个 token 是 `"。\n"`。如果直接写成 `data: 。\n\n`，换行会被当成行结束，接着的空行又会提前结束事件，客户端拿到的数据就错了。用 JSON 包装后，换行变成两个字符 `\n`，整条事件只有一行 data。

另一种做法是像 `format_sse` 那样把多行数据拆成多行 `data:`。两种都符合规范，大模型接口一般用 JSON。

### 4.4 坑

- **事件之间少了空行**：写成 `yield f"data: {payload}\n"`，客户端会把所有 data 行拼成一条事件，直到遇到空行为止。
- **攒齐了再返回**：先 `text = "".join([...])` 再 `return`，就不是流式了。
- **在异步生成器里调用阻塞函数**：生成器在事件循环里运行，`time.sleep` 或同步的模型 SDK 会卡住所有连接。同步生成器（普通 `def` + `yield`）也能传给 `StreamingResponse`，Starlette 会把它放到线程池里迭代，但每个连接会占用一个线程。
- **部署后流式失效**：本地 curl 正常，放到 Nginx 后面就一次性输出，多半是 Nginx 缓冲，加 `X-Accel-Buffering: no` 或在 Nginx 配置里关掉 `proxy_buffering`。
- **TestClient 看不出是否逐块发送**：实测 TestClient 会等生成器跑完再交出响应。它适合检查内容和格式，验证“逐块到达”要真实启动服务，用 `curl -N` 看。

## 5. 客户端断开时停止生成

用户关掉页面后，如果服务端继续生成，模型的 token 照样计费，GPU 也被白白占用。

本机版本（starlette 0.47.3 + uvicorn 0.35.0）实测：客户端断开后，Starlette 会取消正在迭代生成器的任务，生成器在当前的 `await` 处收到 `asyncio.CancelledError`。用 `curl --max-time 1.2` 中途断开，02 的服务端日志打印 `被取消（客户端断开），已发送 4 个 token`。

此外，还可以在每次产出前主动检查：

```python
async def chat_events(prompt: str, request: Request):
    try:
        async for token in fake_llm(prompt):
            if await request.is_disconnected():   # 主动检查，不依赖服务器的实现
                return                            # 结束生成器 = 结束响应
            yield ...
    except asyncio.CancelledError:
        # 被取消时做清理（记日志、关闭上游连接），然后必须重新抛出
        raise
```

- `request.is_disconnected()` 是协程，要 `await`。路由函数要声明 `request: Request` 参数，再把它传给生成器。
- 被取消的情况一定要 `raise`，不要吞掉 `CancelledError`（第五课讲过，吞掉会破坏取消机制）。
- 清理代码也可以放在 `finally` 里，正常结束和被取消都会执行。
- 两种机制都要会：自动取消依赖于 Starlette 和服务器的配合方式，`is_disconnected()` 是代码里显式的保证。

## 6. 客户端：用 httpx 流式读取

### 6.1 对照 QNetworkReply

| Qt | httpx | 说明 |
|---|---|---|
| `manager.get(request)` 返回 `QNetworkReply*` | `async with client.stream("GET", url) as resp:` | 收到响应头就返回，响应体还没读 |
| `readyRead` 信号 + `readAll()` | `async for chunk in resp.aiter_bytes():` | 每次拿到一段刚到达的字节，长度不固定 |
| `canReadLine()` + `readLine()` | `async for line in resp.aiter_lines():` | 按行读，跨块的行已经拼好 |
| `finished` 信号 | `async for` 循环结束 | |
| `abort()` | 提前 `break` 并离开 `async with` | 连接被关闭，服务端随之检测到断开 |

注意 `client.get(url)` 会把整个响应体读完才返回，拿不到流式效果。流式必须用 `client.stream(...)`。

```python
async with httpx.AsyncClient(trust_env=False, timeout=httpx.Timeout(10, read=30)) as client:
    async with client.stream("GET", "http://127.0.0.1:8000/chat/stream", params={"prompt": "hi"}) as resp:
        async for line in resp.aiter_lines():
            ...   # 交给行解析器，遇到空行就得到一条完整事件
```

- `trust_env=False`：不读系统代理，否则在你的机器上访问本机会得到 503。
- `read=30`：读超时指**两次收到数据之间**最多等多久，不是整个流的总时长。模型思考很久才出首 token 时，要把它设大一些。

### 6.2 块边界和事件边界无关

`readyRead` 触发时，你拿到的字节可能是半行，也可能是好几条事件。SSE 也一样，TCP 和中间代理不保证按事件切块。03 的 demo 第 3 节演示了两种错误做法：

- 每块单独 `decode("utf-8")`：一个汉字占 3 个字节，被切到两块里时报 `UnicodeDecodeError`。
- 把每块当成一条事件：拿到 `data:` 这样的残缺内容。

正确做法和 Qt 里处理 `readyRead` 一样：把收到的字节追加到缓冲区，从缓冲区里取出完整的行（找到 `\n`）再解码、解析，剩下的半行留在缓冲区等下一块。`aiter_lines()` 替你做了这件事，练习 6 要求你自己实现一遍。

实际项目里一般不用自己写解析器：OpenAI SDK 传 `stream=True` 后返回的迭代器内部已经解析好 SSE；也有 `httpx-sse` 这样的第三方库。但面试和排查问题时需要知道格式和边界处理。

### 6.3 和仓库里 agent.py 的关系

`example_agents/FunctionCallingAgent/agent.py` 目前是非流式的：`chat.completions.create(...)` 返回完整的 message，`run()` 最后返回整段答案。以后会给它加上 `stream=True`，把模型的增量输出转成本课的 SSE 事件，用 FastAPI 包装成流式接口。流式模式下工具调用的参数也是分段到达的，需要拼接，这是 P1-08 的内容。

## P0-16 面试怎么问

1. 为什么大模型接口普遍用流式输出？SSE 和 WebSocket 怎么选？
2. SSE 的报文格式是什么样的？`data: [DONE]` 是 SSE 标准的一部分吗？
3. 本地测试流式输出正常，部署到 Nginx 后面变成一次性输出，可能是什么原因，怎么解决？
4. 用户关掉页面后，服务端怎么感知并停止生成？

---

## 读完后的自查

下面的问题能不看资料答出来，再开始做练习：

1. 一个路由函数有参数 `todo_id: int`、`limit: int = 10`、`body: TodoCreate`，路径是 `/todos/{todo_id}`。这三个参数分别从请求的哪个部分取值？`/todos/abc` 会得到什么状态码？
2. API Key 鉴权为什么要把请求头参数声明成可选，再自己抛 401？直接声明成必填会返回什么？
3. 在 `async def` 路由里调用 `time.sleep(1)`，同时来 10 个请求，总共要多久？改成普通 `def` 呢？为什么？
4. 写出一条 SSE 事件的原始文本：事件类型是 `tool`，数据有两行 `a` 和 `b`。客户端解析后，data 是什么？
5. 客户端每次 `readyRead`（或 `aiter_bytes()`）拿到一块字节，为什么不能直接 `decode` 后按事件处理？正确做法是什么？
