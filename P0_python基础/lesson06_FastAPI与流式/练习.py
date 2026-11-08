"""
第六课练习。补全每道题，然后运行：python 练习.py
运行结果里每道题会显示 ✅ / ❌ / ⏳（未完成）。

规则：
- 每道题要补全的是路由函数、依赖函数、生成器或解析函数。
- 和第一课不同，这里可以修改装饰器参数（status_code、response_model 等）和函数参数列表，这正是练习内容。
  不要改函数名、URL 路径和 HTTP 方法，不要改“已给出的代码”和下面的检查代码。
- 写完一道题就运行一次。检查代码用 TestClient 发请求，不需要启动服务。
- 这是练习不是考试，可以回看 README 和示例，但不要让 AI 替你写。
"""

import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 已给出的代码，不要修改
# ---------------------------------------------------------------------------


class TodoCreate(BaseModel):
    """创建待办的请求体。"""

    title: str = Field(min_length=1, max_length=100)
    done: bool = False


class Todo(BaseModel):
    """返回给客户端的待办。"""

    id: int
    title: str
    done: bool


class TodoInDB(Todo):
    """服务端内部存储的待办，多一个 created_at，不能出现在响应里。"""

    created_at: float


class TodoPage(BaseModel):
    """分页查询的响应。"""

    items: list[Todo]
    total: int


class TodoStore:
    """内存版“数据库”。"""

    def __init__(self):
        self._items: dict[int, TodoInDB] = {}
        self._next_id = 1

    def add(self, title: str, done: bool = False) -> TodoInDB:
        todo = TodoInDB(id=self._next_id, title=title, done=done, created_at=time.time())
        self._items[todo.id] = todo
        self._next_id += 1
        return todo

    def get(self, todo_id: int) -> TodoInDB | None:
        return self._items.get(todo_id)

    def delete(self, todo_id: int) -> bool:
        return self._items.pop(todo_id, None) is not None

    def all(self) -> list[TodoInDB]:
        """按 id 从小到大返回全部待办。"""
        return list(self._items.values())


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = TodoStore()  # 每次启动都是一个空的 store
    yield


def get_store(request: Request) -> TodoStore:
    return request.app.state.store


StoreDep = Annotated[TodoStore, Depends(get_store)]  # 路由参数写 store: StoreDep 就能拿到 TodoStore

API_KEYS = {"key-alice": "alice", "key-bob": "bob"}  # API Key -> 用户名

FAKE_ANSWER = "你好！\n我是假模型。"


async def fake_llm(prompt: str):
    """假模型：把 FAKE_ANSWER 按 2 个字符一块逐个产出（忽略 prompt）。"""
    for i in range(0, len(FAKE_ANSWER), 2):
        await asyncio.sleep(0)
        yield FAKE_ANSWER[i : i + 2]


app = FastAPI(title="第六课练习", lifespan=lifespan)


# ---------------------------------------------------------------------------
# 练习 1（P0-15）创建待办
# ---------------------------------------------------------------------------


@app.post("/todos")
def create_todo():
    """POST /todos，请求体是 TodoCreate 的 JSON。
    - 用 store.add(...) 保存，成功返回状态码 201，响应体形如 {"id": 1, "title": "...", "done": false}；
    - 响应里不能出现 created_at（提示：response_model）；
    - 请求体不合法（缺 title、title 为空或超过 100 字符）时返回 422（声明好参数类型，FastAPI 会自动做）。
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 练习 2（P0-15）查询和删除单个待办
# ---------------------------------------------------------------------------


@app.get("/todos/{todo_id}")
def get_todo():
    """GET /todos/{todo_id}
    - 存在：返回 200 和 Todo（不含 created_at）；
    - 不存在：返回 404，响应体 {"detail": "..."}（提示：HTTPException）；
    - todo_id 不是整数（/todos/abc）：返回 422。
    """
    raise NotImplementedError


@app.delete("/todos/{todo_id}")
def delete_todo():
    """DELETE /todos/{todo_id}
    - 删除成功：返回 204，响应体为空；
    - 不存在：返回 404。
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 练习 3（P0-15）分页查询
# ---------------------------------------------------------------------------


@app.get("/todos")
def list_todos():
    """GET /todos?limit=10&offset=0
    - 返回 TodoPage：{"items": [...], "total": 全部待办的数量}，items 按 id 从小到大；
    - limit：默认 10，必须在 1 到 50 之间（含两端）；
    - offset：默认 0，不能小于 0；
    - 参数超出范围或不是整数时返回 422（提示：Query）。
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 练习 4（P0-15）API Key 鉴权依赖
# ---------------------------------------------------------------------------


def require_api_key():
    """依赖函数：从请求头 X-API-Key 读取 key，返回对应的用户名（查 API_KEYS）。
    - 缺少请求头，或 key 不在 API_KEYS 里：返回 401（不是 422）；
    - 下面已给出的 admin_router 用它保护 /admin/stats，你写好这个函数后那里也会生效。
    """
    raise NotImplementedError


@app.get("/me")
def me():
    """GET /me：通过依赖拿到用户名，返回 {"user": 用户名}。"""
    raise NotImplementedError


# 已给出的代码，不要修改：router 级依赖，下面所有路由都先经过 require_api_key
admin_router = APIRouter(prefix="/admin", dependencies=[Depends(require_api_key)])


@admin_router.get("/stats")
def admin_stats(store: StoreDep):
    return {"todo_count": len(store.all())}


app.include_router(admin_router)


# ---------------------------------------------------------------------------
# 练习 5（P0-16）SSE 流式接口
# ---------------------------------------------------------------------------


async def sse_chat(prompt):
    """异步生成器：把 fake_llm(prompt) 的每个 token 包装成一条 SSE 事件产出。
    - 每个 token 产出一条事件，数据是 JSON：data: {"delta": "<token>"}，后面跟一个空行；
    - token 里可能有换行，所以要用 json.dumps 包装，不能直接把 token 放在 data: 后面；
    - 全部 token 发完后，再产出一条 data: [DONE]；
    - 每次 yield 的是一条完整的事件（str），不要把多条事件拼在一起 yield。
    """
    raise NotImplementedError
    yield  # 这一行让函数成为异步生成器。写完后删掉它和上面的 raise


@app.get("/chat/stream")
async def chat_stream():
    """GET /chat/stream?prompt=...（prompt 必填）
    - 用 StreamingResponse 返回 sse_chat(prompt) 的内容；
    - Content-Type 是 text/event-stream；
    - 响应头带 Cache-Control: no-cache。
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 练习 6（P0-16）客户端 SSE 解析
# ---------------------------------------------------------------------------


def parse_sse(chunks):
    """把从网络上收到的字节块列表解析成事件列表。
    chunks: list[bytes]，块的边界是任意的：可能在一行中间、在 \\r 和 \\n 之间，甚至在一个汉字的字节中间。
    返回 list[dict]，每个 dict 形如 {"event": "message", "data": "...", "id": None}。

    规则（简化版 SSE 规范）：
    - 行结束符是 \\n 或 \\r\\n（不需要处理单独的 \\r）；
    - 字段行形如 "字段名:值"，冒号后如果紧跟一个空格，去掉这一个空格；
    - data：同一事件里有多行 data 时，用 \\n 拼接；
    - event：事件类型，没有出现时为 "message"；
    - id：只记录本事件里出现的 id，没有出现时为 None；
    - 其他字段（如 retry）忽略；以 ":" 开头的是注释行，忽略；
    - 空行表示一条事件结束：如果这条事件一行 data 都没有，就不产出；
    - 所有块处理完后，最后没有遇到空行的残留内容丢弃。

    parse_sse([b"data: hel", b"lo\\n\\n"]) -> [{"event": "message", "data": "hello", "id": None}]
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 下面是检查代码，不要修改
# ---------------------------------------------------------------------------


def _client():
    from fastapi.testclient import TestClient

    return TestClient(app)  # 用 with 才会执行 lifespan，每道题拿到一个新的空 store


TODO_KEYS = {"id", "title", "done"}


def _check_create_todo():
    with _client() as client:
        r = client.post("/todos", json={"title": "学 FastAPI"})
        assert r.status_code == 201, f"创建成功应返回 201，实际是 {r.status_code}"
        assert r.json() == {"id": 1, "title": "学 FastAPI", "done": False}, f"响应体不对：{r.json()}"
        r = client.post("/todos", json={"title": "学 SSE", "done": True})
        assert r.status_code == 201 and r.json() == {"id": 2, "title": "学 SSE", "done": True}
        assert client.app.state.store.get(2) is not None, "没有保存到 store"
        assert client.post("/todos", json={}).status_code == 422, "缺 title 应返回 422"
        assert client.post("/todos", json={"title": ""}).status_code == 422, "title 为空应返回 422"
        assert client.post("/todos", json={"title": "x" * 101}).status_code == 422, "title 超长应返回 422"
        assert client.post("/todos", json={"title": "a", "done": "不是布尔"}).status_code == 422
        assert len(client.app.state.store.all()) == 2, "校验失败的请求不应该保存"


def _check_get_delete_todo():
    with _client() as client:
        store = client.app.state.store
        store.add("第一条")
        store.add("第二条", done=True)
        r = client.get("/todos/2")
        assert r.status_code == 200, f"查询存在的待办应返回 200，实际是 {r.status_code}"
        assert set(r.json()) == TODO_KEYS, f"响应字段应该是 {TODO_KEYS}，实际是 {set(r.json())}"
        assert r.json() == {"id": 2, "title": "第二条", "done": True}
        r = client.get("/todos/99")
        assert r.status_code == 404, f"不存在应返回 404，实际是 {r.status_code}"
        assert "detail" in r.json(), "404 响应体应该有 detail"
        assert client.get("/todos/abc").status_code == 422, "todo_id 不是整数应返回 422"
        r = client.delete("/todos/1")
        assert r.status_code == 204, f"删除成功应返回 204，实际是 {r.status_code}"
        assert r.content == b"", "204 响应体应该为空"
        assert client.get("/todos/1").status_code == 404, "删除后应查不到"
        assert client.delete("/todos/1").status_code == 404, "删除不存在的待办应返回 404"


def _check_list_todos():
    with _client() as client:
        store = client.app.state.store
        for i in range(1, 16):
            store.add(f"待办 {i}")
        r = client.get("/todos")
        assert r.status_code == 200, f"应返回 200，实际是 {r.status_code}"
        body = r.json()
        assert set(body) == {"items", "total"}, f"响应应包含 items 和 total，实际是 {set(body)}"
        assert body["total"] == 15
        assert [t["id"] for t in body["items"]] == list(range(1, 11)), "默认 limit 应为 10"
        assert all(set(t) == TODO_KEYS for t in body["items"]), "items 里不能有 created_at"
        r = client.get("/todos", params={"limit": 5, "offset": 10})
        assert [t["id"] for t in r.json()["items"]] == [11, 12, 13, 14, 15]
        assert r.json()["total"] == 15, "total 是全部待办的数量，不是本页数量"
        assert len(client.get("/todos", params={"offset": 14}).json()["items"]) == 1
        assert client.get("/todos", params={"offset": 20}).json()["items"] == []
        assert client.get("/todos", params={"limit": 50}).status_code == 200, "limit=50 是合法的"
        assert client.get("/todos", params={"limit": 1}).status_code == 200, "limit=1 是合法的"
        for bad in [{"limit": 0}, {"limit": 51}, {"offset": -1}, {"limit": "abc"}]:
            code = client.get("/todos", params=bad).status_code
            assert code == 422, f"参数 {bad} 应返回 422，实际是 {code}"


def _check_api_key():
    with _client() as client:
        r = client.get("/me")
        assert r.status_code == 401, f"缺少 X-API-Key 应返回 401，实际是 {r.status_code}"
        r = client.get("/me", headers={"X-API-Key": "wrong"})
        assert r.status_code == 401, f"错误的 key 应返回 401，实际是 {r.status_code}"
        r = client.get("/me", headers={"X-API-Key": "key-alice"})
        assert r.status_code == 200 and r.json() == {"user": "alice"}, f"/me 结果不对：{r.status_code} {r.text}"
        assert client.get("/me", headers={"X-API-Key": "key-bob"}).json() == {"user": "bob"}
        assert client.get("/admin/stats").status_code == 401, "/admin/stats 缺少 key 应返回 401"
        r = client.get("/admin/stats", headers={"X-API-Key": "key-bob"})
        assert r.status_code == 200 and r.json() == {"todo_count": 0}


def _split_events(text):
    """严格按 SSE 格式切分：每条事件以空行结束。"""
    assert text.endswith("\n\n"), f"事件必须以空行结束（\\n\\n），实际结尾是 {text[-10:]!r}"
    return text[:-2].split("\n\n")


def _check_event_list(events):
    tokens = [FAKE_ANSWER[i : i + 2] for i in range(0, len(FAKE_ANSWER), 2)]
    assert len(events) == len(tokens) + 1, f"应有 {len(tokens)} 条 token 事件加 1 条 [DONE]，实际 {len(events)} 条"
    assert events[-1] == "data: [DONE]", f"最后一条应是 data: [DONE]，实际是 {events[-1]!r}"
    for event, token in zip(events, tokens):
        assert event.startswith("data: ") and "\n" not in event, f"事件格式不对：{event!r}"
        payload = json.loads(event.removeprefix("data: "))
        assert payload == {"delta": token}, f"数据应为 {{'delta': {token!r}}}，实际是 {payload}"


def _check_sse():
    async def collect():
        return [item async for item in sse_chat("hi")]

    items = asyncio.run(collect())
    assert all(isinstance(x, str) for x in items), "每次 yield 一个 str"
    for item in items:
        assert item.endswith("\n\n") and item.count("\n\n") == 1, f"每次 yield 应该恰好是一条完整事件：{item!r}"
    _check_event_list(_split_events("".join(items)))

    with _client() as client:
        assert client.get("/chat/stream").status_code == 422, "prompt 是必填查询参数"
        with client.stream("GET", "/chat/stream", params={"prompt": "hi"}) as r:
            assert r.status_code == 200
            content_type = r.headers.get("content-type", "")
            assert content_type.startswith("text/event-stream"), f"Content-Type 应为 text/event-stream，实际是 {content_type!r}"
            assert r.headers.get("cache-control") == "no-cache", "缺少 Cache-Control: no-cache"
            body = r.read().decode("utf-8")
        _check_event_list(_split_events(body))


def _msg(data, event="message", id=None):
    return {"event": event, "data": data, "id": id}


def _check_parse_sse():
    assert parse_sse([]) == []
    assert parse_sse([b"data: hello\n\n"]) == [_msg("hello")]
    assert parse_sse([b"data: hel", b"lo\n\n"]) == [_msg("hello")]
    assert parse_sse([b"data: a\n\ndata: b\n\n"]) == [_msg("a"), _msg("b")], "一个块里可能有多条事件"
    assert parse_sse([b"event: tool\nid: 7\ndata: line1\ndata: line2\n\n"]) == [
        _msg("line1\nline2", event="tool", id="7")
    ], "多行 data 应该用 \\n 拼接"
    assert parse_sse([b": ping\n\ndata: x\n\n"]) == [_msg("x")], "注释行要忽略，没有 data 的事件不产出"
    assert parse_sse([b"retry: 3000\ndata: x\n\n"]) == [_msg("x")], "未知字段要忽略"
    assert parse_sse([b"data:x\n\ndata:  two\n\n"]) == [_msg("x"), _msg(" two")], "冒号后最多去掉一个空格"
    assert parse_sse([b"data: a\n\ndata: unfinished"]) == [_msg("a")], "没有遇到空行的残留内容要丢弃"
    assert parse_sse([b"data: a\r\n\r\nevent: e\r\ndata: b\r\n\r\n"]) == [_msg("a"), _msg("b", event="e")], "要支持 \\r\\n"
    assert parse_sse([b"id: 1\ndata: a\n\ndata: b\n\n"]) == [_msg("a", id="1"), _msg("b")], "id 只属于它所在的事件"

    raw = 'data: {"delta": "你好"}\r\n\r\nevent: done\ndata: 结束\n\n'.encode()
    expected = [_msg('{"delta": "你好"}'), _msg("结束", event="done")]
    for size in [1, 2, 3, 5, 7]:
        chunks = [raw[i : i + size] for i in range(0, len(raw), size)]
        try:
            result = parse_sse(chunks)
        except UnicodeDecodeError:
            raise AssertionError(f"按 {size} 字节分块时 UnicodeDecodeError：汉字的字节被切到两块里了，要先攒字节再解码")
        assert result == expected, f"按 {size} 字节分块时结果不对：{result}"


if __name__ == "__main__":
    checks = [
        ("练习 1（P0-15）create_todo", _check_create_todo),
        ("练习 2（P0-15）get_todo / delete_todo", _check_get_delete_todo),
        ("练习 3（P0-15）list_todos", _check_list_todos),
        ("练习 4（P0-15）require_api_key / me", _check_api_key),
        ("练习 5（P0-16）sse_chat / chat_stream", _check_sse),
        ("练习 6（P0-16）parse_sse", _check_parse_sse),
    ]
    passed = 0
    for title, check in checks:
        try:
            check()
            print(f"✅ {title}")
            passed += 1
        except NotImplementedError:
            print(f"⏳ {title}：未完成")
        except AssertionError as e:
            print(f"❌ {title}：{e or '结果不正确'}")
        except Exception as e:
            print(f"❌ {title}：运行出错 {type(e).__name__}: {e}")
    print(f"\n通过 {passed}/{len(checks)}")
