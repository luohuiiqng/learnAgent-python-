"""
第七课练习。补全每个函数（练习 1 是补全类的字段，练习 6 是补全文件），然后运行：python 练习.py
运行结果里每道题会显示 ✅ / ❌ / ⏳（未完成）/ ⏭（跳过）。

规则：
- 只改要求你改的地方，不要改函数签名和下面的检查代码。
- 这是练习不是考试，可以回看 README 和示例，但不要让 AI 替你写。
- 数据库题用 SQLite 内存库检查，不需要启动任何服务。
- 练习 5 需要 Redis：先在本课目录运行 docker compose up -d。连不上 Redis 时这道题显示 ⏭，不算错。
  Redis 不在 localhost:6379 时，用环境变量 REDIS_URL 指定，例如 REDIS_URL=redis://localhost:6380/0
- 练习 6 补全的是 练习_docker/ 目录里的 Dockerfile 和 .dockerignore。
"""
import hashlib
import time

import redis
from sqlalchemy import CheckConstraint, ForeignKey, String, Text, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# 练习 1（P0-17）
class Message(Base):
    """一条对话记录，表名 messages。id 已经写好，补全下面 4 个字段：
    - session_id：字符串，最长 64，不能为空，要建索引（按会话查历史是最常见的查询）
    - role：字符串，最长 16，不能为空
    - content：长文本（Text），不能为空
    - tokens：整数，可以为空（有的消息还没统计 token 数）
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 在这里补全 4 个字段


# ---------------------------------------------------------------------------
# 练习 2、3 用到的模型，已经写好，不要修改
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    notes: Mapped[list["Note"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, default="")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped[User] = relationship(back_populates="notes")


# 练习 2（P0-17）：笔记的增删改查和统计。参数 session 是 sqlalchemy.orm.Session
def create_note(session, user_id, title, content=""):
    """新建一篇笔记并提交，返回 Note 对象（提交后它的 id 已经有值）。"""
    raise NotImplementedError


def list_notes(session, user_id, keyword=None):
    """返回该用户的笔记列表（list[Note]），按 id 升序。
    keyword 不为 None 时，只返回标题里包含 keyword 的笔记。
    """
    raise NotImplementedError


def update_note_title(session, note_id, new_title):
    """修改笔记标题并提交。笔记存在返回 True，不存在返回 False。"""
    raise NotImplementedError


def delete_note(session, note_id):
    """删除笔记并提交。笔记存在返回 True，不存在返回 False。"""
    raise NotImplementedError


def count_notes_by_user(session):
    """返回 {用户名: 笔记数}。没有笔记的用户也要出现，值为 0。
    只能执行一条 SELECT（用 JOIN + GROUP BY），不能先查用户再逐个查笔记。
    """
    raise NotImplementedError


# 练习 3（P0-17）：修复 SQL 注入
def find_user_unsafe(session, name):
    """有注入漏洞的写法，留作对照，不要修改。"""
    sql = f"SELECT id, name FROM users WHERE name = '{name}' ORDER BY id"
    return [tuple(row) for row in session.execute(text(sql))]


def find_user(session, name):
    """功能和 find_user_unsafe 一样：返回 [(id, name), ...]，按 id 升序。
    用 text() + 命名参数（:name）改写，修复注入漏洞。
    """
    raise NotImplementedError


def list_users_sorted(session, order_by, desc=False):
    """用 text() 写 SQL，返回按 order_by 排序的用户名列表（list[str]）。
    - order_by 只允许 "id" 或 "name"，其他值抛 ValueError（列名不能用占位符绑定）
    - desc=True 时降序
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 练习 4 用到的模型，已经写好，不要修改
# ---------------------------------------------------------------------------
class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("balance >= 0", name="balance_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(50))
    balance: Mapped[int]


# 练习 4（P0-17）：事务
def transfer(session, from_id, to_id, amount):
    """从 from_id 账户转 amount 到 to_id 账户。扣款和加款要么都生效，要么都不生效。
    - amount <= 0：抛 ValueError
    - 任一账户不存在：抛 LookupError
    - 余额不足：抛 ValueError
    - 成功：提交事务
    - 失败：回滚事务，再把异常抛出去。回滚后数据保持原样，session 还能继续使用
    调用时 session 里没有进行中的事务，可以用 with session.begin():，也可以自己 commit / rollback。
    """
    raise NotImplementedError


# 练习 5（P0-18）：Redis。参数 r 是 decode_responses=True 的 redis.Redis 客户端
def cached_answer(r, prompt, compute, ttl=60):
    """带缓存地获取答案。
    - 键："lesson07:ex:cache:" + prompt 的 sha256 十六进制摘要（hashlib.sha256(prompt.encode()).hexdigest()）
    - 命中缓存：直接返回缓存的字符串，不调用 compute
    - 未命中：调用 compute(prompt) 得到字符串，存进 Redis 并设置 ttl 秒过期，然后返回
    """
    raise NotImplementedError


def allow_request(r, user_id, limit, window_seconds=60):
    """固定窗口限流：同一用户在一个窗口内最多允许 limit 次，第 limit+1 次起返回 False。
    - 键："lesson07:ex:rate:<user_id>:<窗口编号>"，窗口编号 = int(time.time() // window_seconds)
    - 计数键必须有过期时间（不超过 window_seconds 秒），否则会一直占用内存
    """
    raise NotImplementedError


# 练习 6（P0-19）：补全 练习_docker/Dockerfile 和 练习_docker/.dockerignore
# 要求：
# - 基础镜像用 python:3.13-slim
# - 设置环境变量 PYTHONUNBUFFERED=1
# - 工作目录 /code
# - 利用层缓存：先复制 requirements.txt 并用 pip install --no-cache-dir -r requirements.txt 安装依赖，再复制代码
# - 声明端口 9000
# - 用 exec 形式（JSON 数组）的 CMD 启动：uvicorn server:api，监听 0.0.0.0 的 9000 端口
# - .dockerignore 至少排除 .env、__pycache__/、.venv/
# 完成后删掉两个文件里所有的 TODO 注释。
# 这里的检查只看文件内容。真正的验证是在本课目录执行：
#   docker build -t lesson07-ex 练习_docker
#   docker run --rm -p 9090:9000 lesson07-ex      （本机 9090 → 容器 9000。本机 9000 已被 MinIO 占用）
#   NO_PROXY=localhost,127.0.0.1 curl http://localhost:9090/
# 验证完删除镜像：docker rmi lesson07-ex


# ---------------------------------------------------------------------------
# 下面是检查代码，不要修改
# ---------------------------------------------------------------------------
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

from sqlalchemy import Integer, create_engine, event, inspect  # noqa: E402

EXERCISE_DOCKER_DIR = Path(__file__).resolve().parent / "练习_docker"
REDIS_PREFIX = "lesson07:ex:"


class _Skip(Exception):
    """检查需要的外部服务不可用。"""


def _new_session(model):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    model.metadata.create_all(engine)
    return engine, Session(engine)


class _SqlRecorder:
    """记录驱动真正收到的 SQL 和参数。"""

    def __init__(self, engine):
        self.engine = engine
        self.items = []

    def _on_execute(self, conn, cursor, statement, parameters, context, executemany):
        self.items.append((statement, parameters))

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._on_execute)
        return self

    def __exit__(self, *exc):
        event.remove(self.engine, "before_cursor_execute", self._on_execute)
        return False


def _check_message_model():
    cols = Message.__table__.c
    wanted = ["session_id", "role", "content", "tokens"]
    if not any(name in cols for name in wanted):
        raise NotImplementedError
    for name in wanted:
        assert name in cols, f"缺少字段 {name}"
    sid, role, content, tokens = (cols[n] for n in wanted)
    assert isinstance(sid.type, String) and not isinstance(sid.type, Text), "session_id 应该是 String(64)"
    assert sid.type.length == 64, f"session_id 最长应为 64，现在是 {sid.type.length}"
    assert isinstance(role.type, String) and role.type.length == 16, "role 应该是 String(16)"
    assert isinstance(content.type, Text), "content 应该是 Text"
    assert isinstance(tokens.type, Integer), "tokens 应该是整数"
    assert not sid.nullable and not role.nullable and not content.nullable, "session_id、role、content 不能为空"
    assert tokens.nullable, "tokens 应该允许为空：类型写成 Mapped[int | None]"
    indexed = any([c.name for c in ix.columns] == ["session_id"] for ix in Message.__table__.indexes)
    assert indexed, "session_id 没有建索引：mapped_column(..., index=True)"

    engine, session = _new_session(Message)
    with session:
        session.add(Message(session_id="s1", role="user", content="你好"))
        session.commit()
        m = session.scalars(select(Message)).one()
        assert (m.session_id, m.role, m.content, m.tokens) == ("s1", "user", "你好", None)
        session.add(Message(session_id="s1", content="缺 role"))
        try:
            session.commit()
            raise AssertionError("缺 role 时数据库应该拒绝插入")
        except IntegrityError:
            session.rollback()
    engine.dispose()


def _check_note_crud():
    engine, session = _new_session(Note)
    with session:
        session.add_all([User(name="alice"), User(name="bob"), User(name="carol")])
        session.commit()

        n1 = create_note(session, 1, "学 SQL", "JOIN")
        assert isinstance(n1, Note), "create_note 应该返回 Note 对象"
        assert n1.id == 1, "提交后 id 应该有值"
        create_note(session, 1, "学 Redis")
        create_note(session, 2, "学 Docker")
        create_note(session, 1, "复习 SQL")
        session.rollback()  # 已经提交的数据不会被回滚
        assert session.scalar(select(func.count()).select_from(Note)) == 4, "create_note 没有 commit"
        assert session.get(Note, 2).content == "", "content 默认应为空字符串"

        titles = [n.title for n in list_notes(session, 1)]
        assert titles == ["学 SQL", "学 Redis", "复习 SQL"], f"list_notes 结果不对: {titles}"
        titles = [n.title for n in list_notes(session, 1, keyword="SQL")]
        assert titles == ["学 SQL", "复习 SQL"], f"按关键字过滤不对: {titles}"
        assert list_notes(session, 3) == [], "没有笔记的用户应该返回空列表"
        assert [n.title for n in list_notes(session, 2, keyword="SQL")] == [], "不能返回其他用户的笔记"

        assert update_note_title(session, 2, "学 Redis 限流") is True
        assert update_note_title(session, 99, "x") is False, "笔记不存在时应返回 False"
        session.rollback()
        session.expire_all()
        assert session.get(Note, 2).title == "学 Redis 限流", "update_note_title 没有 commit"

        assert delete_note(session, 3) is True
        assert delete_note(session, 3) is False, "删过的笔记再删应返回 False"
        session.rollback()
        assert session.get(Note, 3) is None, "delete_note 没有 commit"

        session.commit()
        with _SqlRecorder(engine) as rec:
            counts = count_notes_by_user(session)
        assert counts == {"alice": 3, "bob": 0, "carol": 0}, f"统计结果不对: {counts}（没有笔记的用户也要出现）"
        selects = [s for s, _ in rec.items if s.lstrip().upper().startswith("SELECT")]
        assert len(selects) == 1, f"执行了 {len(selects)} 条 SELECT，应该只用一条（JOIN + GROUP BY）"
    engine.dispose()


def _check_sql_injection():
    engine, session = _new_session(User)
    with session:
        session.add_all([User(name="alice"), User(name="O'Brien"), User(name="bob")])
        session.commit()
        assert find_user(session, "alice") == [(1, "alice")]
        assert find_user(session, "nobody") == []
        try:
            found = find_user(session, "O'Brien")
        except NotImplementedError:
            raise
        except Exception as e:
            raise AssertionError(f"查 O'Brien 时报错 {type(e).__name__}：名字里的单引号截断了 SQL，说明还在拼接字符串") from e
        assert found == [(2, "O'Brien")], f"查 O'Brien 结果不对: {found}"

        evil = "' OR '1'='1"
        assert len(find_user_unsafe(session, evil)) == 3  # 对照：有漏洞的版本返回了全部用户
        with _SqlRecorder(engine) as rec:
            result = find_user(session, evil)
        assert result == [], f"恶意输入返回了数据: {result}"
        assert rec.items, "find_user 没有执行 SQL"
        for statement, params in rec.items:
            assert evil not in statement, "用户输入出现在了 SQL 字符串里：仍然在拼接 SQL，要用 :name 参数绑定"
            values = params.values() if isinstance(params, dict) else params
            assert evil in values, "用户输入应该原样作为绑定参数传给驱动，不要自己转义引号再拼接"

        assert list_users_sorted(session, "id") == ["alice", "O'Brien", "bob"]
        assert list_users_sorted(session, "name") == ["O'Brien", "alice", "bob"]
        assert list_users_sorted(session, "id", desc=True) == ["bob", "O'Brien", "alice"]
        for bad in ["password", "name; DROP TABLE users", "id DESC"]:
            try:
                list_users_sorted(session, bad)
                raise AssertionError(f"order_by={bad!r} 应该抛 ValueError")
            except ValueError:
                pass
        session.rollback()
        assert "users" in inspect(engine).get_table_names(), "users 表被删掉了"
    engine.dispose()


def _check_transfer():
    engine, session = _new_session(Account)
    with session:
        session.add_all([Account(owner="alice", balance=100), Account(owner="bob", balance=50)])
        session.commit()

        def balances():
            session.expire_all()
            result = (session.get(Account, 1).balance, session.get(Account, 2).balance)
            session.commit()  # 结束读取用的事务，下次调用 transfer 时 session 是干净的
            return result

        transfer(session, 1, 2, 30)
        session.rollback()
        assert balances() == (70, 80), "转账成功后没有提交，或金额不对"

        failures = [
            (1, 2, 0, ValueError, "amount <= 0"),
            (1, 2, -5, ValueError, "amount <= 0"),
            (1, 999, 10, LookupError, "收款账户不存在"),
            (999, 1, 10, LookupError, "付款账户不存在"),
            (2, 1, 1000, ValueError, "余额不足"),
        ]
        for from_id, to_id, amount, exc_type, desc in failures:
            try:
                transfer(session, from_id, to_id, amount)
                raise AssertionError(f"{desc} 时应该抛 {exc_type.__name__}")
            except exc_type:
                pass
            except AssertionError:
                raise
            except Exception as e:
                raise AssertionError(f"{desc} 时应该抛 {exc_type.__name__}，实际抛了 {type(e).__name__}") from e
            # 模拟调用方接着做别的事并提交。如果 transfer 失败时没有回滚，改了一半的数据会在这里被提交
            try:
                session.commit()
            except Exception as e:
                raise AssertionError(f"{desc} 之后 session 不能继续使用（没有 rollback）: {type(e).__name__}") from e
            got = balances()
            assert got == (70, 80), f"{desc} 之后余额变成了 {got}，失败时没有回滚"

        transfer(session, 2, 1, 80)
        assert balances() == (150, 0), "余额正好够时应该能转"
    engine.dispose()


def _redis_or_skip():
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    r = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=1, socket_timeout=2)
    try:
        r.ping()
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        raise _Skip(f"连不上 {url}") from e
    return r


def _redis_cleanup(r):
    keys = list(r.scan_iter(match=REDIS_PREFIX + "*"))
    if keys:
        r.delete(*keys)


def _check_redis():
    r = _redis_or_skip()
    _redis_cleanup(r)
    try:
        calls = []

        def compute(prompt):
            calls.append(prompt)
            return f"答案:{prompt}"

        assert cached_answer(r, "什么是 RAG", compute, ttl=30) == "答案:什么是 RAG"
        assert cached_answer(r, "什么是 RAG", compute, ttl=30) == "答案:什么是 RAG"
        assert calls == ["什么是 RAG"], f"第二次应该命中缓存，实际调用了 compute {len(calls)} 次"
        key = REDIS_PREFIX + "cache:" + hashlib.sha256("什么是 RAG".encode()).hexdigest()
        assert r.get(key) == "答案:什么是 RAG", "缓存键的格式不对"
        assert 0 < r.ttl(key) <= 30, f"缓存没有按 ttl 设置过期时间，ttl={r.ttl(key)}"
        assert cached_answer(r, "什么是 Agent", compute) == "答案:什么是 Agent"
        assert len(calls) == 2, "不同的问题应该分别计算"

        empty_calls = []

        def compute_empty(prompt):
            empty_calls.append(prompt)
            return ""

        cached_answer(r, "空回答", compute_empty)
        assert cached_answer(r, "空回答", compute_empty) == ""
        assert len(empty_calls) == 1, "缓存值是空字符串时也算命中：判断要用 is not None"

        for _ in range(2):  # 万一正好跨过窗口边界，重试一次
            _redis_cleanup(r)
            window = int(time.time() // 3600)
            results = [allow_request(r, "alice", 3, window_seconds=3600) for _ in range(5)]
            other = allow_request(r, "bob", 3, window_seconds=3600)
            if int(time.time() // 3600) == window:
                break
        assert results == [True, True, True, False, False], f"限流结果不对: {results}"
        assert other is True, "不同用户的计数应该互相独立"
        rate_key = f"{REDIS_PREFIX}rate:alice:{window}"
        assert r.exists(rate_key), "计数键的格式不对"
        assert 0 < r.ttl(rate_key) <= 3600, f"计数键没有设置过期时间，ttl={r.ttl(rate_key)}"
    finally:
        _redis_cleanup(r)
        r.close()


def _dockerfile_instructions(path):
    """把 Dockerfile 解析成 [(指令, 参数字符串)]：去掉注释，合并以 \\ 结尾的续行。"""
    instructions, buf = [], ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not buf and (not line or line.startswith("#")):
            continue
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        buf += line
        parts = buf.split(None, 1)
        instructions.append((parts[0].upper(), parts[1] if len(parts) > 1 else ""))
        buf = ""
    return instructions


def _check_dockerfile():
    dockerfile = EXERCISE_DOCKER_DIR / "Dockerfile"
    ignore_file = EXERCISE_DOCKER_DIR / ".dockerignore"
    assert dockerfile.exists(), f"找不到 {dockerfile}"
    assert ignore_file.exists(), f"找不到 {ignore_file}"
    if "TODO" in dockerfile.read_text(encoding="utf-8") + ignore_file.read_text(encoding="utf-8"):
        raise NotImplementedError

    ins = _dockerfile_instructions(dockerfile)
    assert ins, "Dockerfile 是空的"
    assert ins[0][0] == "FROM", "第一条指令应该是 FROM"
    assert re.fullmatch(r"python:3\.13-slim", ins[0][1].split()[0]), f"基础镜像应该是 python:3.13-slim，现在是 {ins[0][1]}"

    def find(pred):
        return next((i for i, (cmd, args) in enumerate(ins) if pred(cmd, args)), None)

    i_env = find(lambda c, a: c == "ENV" and re.search(r"PYTHONUNBUFFERED[= ]1\b", a))
    assert i_env is not None, "没有设置 ENV PYTHONUNBUFFERED=1"
    i_workdir = find(lambda c, a: c == "WORKDIR" and a.strip() == "/code")
    assert i_workdir is not None, "没有 WORKDIR /code"
    i_copy_req = find(lambda c, a: c == "COPY" and a.split()[0] == "requirements.txt")
    assert i_copy_req is not None, "没有单独 COPY requirements.txt"
    i_pip = find(lambda c, a: c == "RUN" and "pip install" in a and "-r requirements.txt" in a)
    assert i_pip is not None, "没有 RUN pip install ... -r requirements.txt"
    assert "--no-cache-dir" in ins[i_pip][1], "pip install 要加 --no-cache-dir，不把下载缓存留在镜像里"
    i_copy_code = find(lambda c, a: c == "COPY" and a.split()[0] in (".", "./", "server.py"))
    assert i_copy_code is not None, "没有复制代码（COPY . .）"
    assert i_workdir < i_copy_req, "WORKDIR 应该在 COPY 之前"
    assert i_copy_req < i_pip < i_copy_code, "顺序应该是：COPY requirements.txt → RUN pip install → COPY 代码，才能利用层缓存"
    i_expose = find(lambda c, a: c == "EXPOSE" and "9000" in a.split())
    assert i_expose is not None, "没有 EXPOSE 9000"

    cmds = [args for cmd, args in ins if cmd == "CMD"]
    assert cmds, "没有 CMD"
    try:
        cmd = json.loads(cmds[-1])
    except json.JSONDecodeError:
        raise AssertionError('CMD 要用 exec 形式（JSON 数组，双引号）：CMD ["uvicorn", ...]') from None
    assert isinstance(cmd, list) and cmd and cmd[0] == "uvicorn", "CMD 应该以 uvicorn 开头"
    assert "server:api" in cmd, "CMD 里应该有 server:api"
    assert "0.0.0.0" in cmd, "要监听 0.0.0.0，否则容器外访问不到"
    assert "9000" in cmd, "端口应该是 9000"

    ignore = {line.strip().rstrip("/") for line in ignore_file.read_text(encoding="utf-8").splitlines()}
    for item in [".env", "__pycache__", ".venv"]:
        assert item in ignore, f".dockerignore 里没有排除 {item}"


if __name__ == "__main__":
    checks = [
        ("练习 1 Message 模型", _check_message_model),
        ("练习 2 笔记增删改查与统计", _check_note_crud),
        ("练习 3 修复 SQL 注入", _check_sql_injection),
        ("练习 4 transfer 事务", _check_transfer),
        ("练习 5 Redis 缓存与限流", _check_redis),
        ("练习 6 Dockerfile", _check_dockerfile),
    ]
    passed = skipped = 0
    for title, check in checks:
        try:
            check()
            print(f"✅ {title}")
            passed += 1
        except NotImplementedError:
            print(f"⏳ {title}：未完成")
        except _Skip as e:
            print(f"⏭ {title}：跳过（{e}），需要先 docker compose up -d")
            skipped += 1
        except AssertionError as e:
            print(f"❌ {title}：{e or '结果不正确'}")
        except Exception as e:
            print(f"❌ {title}：运行出错 {type(e).__name__}: {e}")
    print(f"\n通过 {passed}/{len(checks)}，跳过 {skipped}")
