# 第七课：数据库、缓存与 Docker（PostgreSQL、SQLAlchemy、Redis、docker compose）

**覆盖知识点**：P0-17 PostgreSQL 与 SQLAlchemy 基础、P0-18 Redis 基础、P0-19 Docker 与 docker-compose（目标都是 L3）
**预计用时**：6 到 7 小时

## 学习步骤

1. 先读第 1 节，运行两个数据库示例。它们默认用 SQLite 内存库，不需要启动任何服务：

   ```bash
   cd P0_python基础/lesson07_数据库缓存与Docker
   python 01_SQLAlchemy基础.py
   python 02_SQL注入与参数化.py
   ```

   用 `python`，不要用 `python3`。你电脑上的 `python3` 是另一个没装依赖的版本。

2. 用本课的 `docker-compose.yml` 启动 PostgreSQL 和 Redis（第一次要拉镜像，需要几分钟）：

   ```bash
   docker compose up -d        # 后台启动
   docker compose ps           # 两个服务的 STATUS 都显示 (healthy) 才算就绪
   ```

   如果报 `port is already allocated` 或 `address already in use`，说明本机端口被占了。你的电脑上用 Homebrew 装的 Redis 正在监听 6379，所以 Redis 要换一个端口启动，脚本也要用 `REDIS_URL` 指过去：

   ```bash
   REDIS_PORT=6380 docker compose up -d
   export REDIS_URL=redis://localhost:6380/0
   ```

   PostgreSQL 的 5432 被占时同理：`PG_PORT=5433 docker compose up -d`，连接串里的端口也改成 5433。

3. 用 PostgreSQL 再跑一遍 01 示例，对比两次打印的建表语句（`INTEGER` 和 `SERIAL`）：

   ```bash
   DATABASE_URL=postgresql+psycopg://learn:learn123@localhost:5432/learn python 01_SQLAlchemy基础.py
   ```

4. 读第 2 节，运行 `python 03_Redis基础.py`。连不上 Redis 时，脚本会提示你先运行 `docker compose up -d`。没设 `REDIS_URL` 时脚本连 `localhost:6379`，也就是 Homebrew 装的那个 Redis，同样能用。示例和练习只读写以 `lesson07:` 开头的键，用完会删掉。
5. 读第 3 节，进入 `docker_demo/` 构建并运行一个镜像（命令见 3.4 节）。做完删掉镜像：`docker rmi lesson07-demo`。
6. 完成 `练习.py` 里的 6 道题，运行 `python 练习.py`，直到全部通过。Redis 题在连不上 Redis 时显示 ⏭（跳过），不算错。
7. 学完后关掉服务：`docker compose down`（保留数据）或 `docker compose down -v`（连数据一起删）。
8. 告诉教练“第七课学完了”，开始评估。

**关于代理**：你的电脑设置了系统代理 127.0.0.1:8080。psycopg 和 redis-py 直接建 TCP 连接，不走 HTTP 代理，连本机数据库不受影响。但用 httpx、requests、curl 访问本机的 HTTP 服务（比如容器里的 FastAPI）时，请求可能被发给代理，要加 `NO_PROXY=localhost,127.0.0.1`：

```bash
NO_PROXY=localhost,127.0.0.1 curl http://localhost:8000/
```

---

## 1. PostgreSQL 与 SQLAlchemy（P0-17）

### 1.1 SQL 速览

关系数据库把数据存成**表**：每一行是一条记录，每一列有固定的类型。下面的 SQL 在 PostgreSQL 和 SQLite 里都能运行。想亲手试，启动服务后执行 `docker compose exec postgres psql -U learn -d learn`，进入交互终端（输入 `\q` 退出）。

```sql
-- 建表。PRIMARY KEY：主键，唯一标识一行；REFERENCES：外键，值必须在另一张表里存在
CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(50) NOT NULL UNIQUE);
CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id)
);

-- 增删改查
INSERT INTO users (name) VALUES ('alice'), ('bob');
INSERT INTO notes (title, user_id) VALUES ('学 SQL', 1), ('学 Redis', 1);
SELECT id, title FROM notes WHERE user_id = 1 AND title LIKE '学%' ORDER BY id LIMIT 10;
UPDATE notes SET title = '学 SQL 进阶' WHERE id = 1;
DELETE FROM notes WHERE id = 2;
-- UPDATE 和 DELETE 忘了写 WHERE，会改掉或删掉整张表

-- JOIN：按条件把两张表的行拼起来
SELECT users.name, COUNT(notes.id)
FROM users LEFT JOIN notes ON notes.user_id = users.id
GROUP BY users.id, users.name
ORDER BY users.id;

-- 索引：让 WHERE user_id = ? 不用扫全表
CREATE INDEX ix_notes_user_id ON notes (user_id);

-- 事务：多条语句要么全部生效，要么全部不生效
BEGIN;
UPDATE accounts SET balance = balance - 30 WHERE id = 1;
UPDATE accounts SET balance = balance + 30 WHERE id = 2;
COMMIT;      -- 出错时执行 ROLLBACK，两条 UPDATE 都撤销
```

| 概念 | 说明 |
|---|---|
| `INNER JOIN`（简写 `JOIN`） | 只保留两边都匹配上的行。没有笔记的用户不会出现 |
| `LEFT JOIN` | 保留左表所有行，右表没匹配上的列填 `NULL`。`COUNT(notes.id)` 不计 `NULL`，所以结果是 0 |
| `GROUP BY` | 按列分组，配合 `COUNT`、`SUM`、`MAX` 等聚合函数 |
| 索引 | 类似 `std::map` 的 B 树，查找从 O(n) 变成 O(log n)；代价是占空间、写入变慢。主键和 `UNIQUE` 列自动有索引 |
| 事务 | ACID：原子性（全做或全不做）、一致性（约束始终满足）、隔离性（并发事务互不干扰）、持久性（提交后断电也不丢） |

### 1.2 为什么后端常用 PostgreSQL

你用过的 SQLite 是一个库，数据库就是一个文件，嵌在进程里运行。PostgreSQL 是一个独立的服务器进程，客户端通过网络连接。

| | SQLite | PostgreSQL |
|---|---|---|
| 运行方式 | 嵌在应用进程里，读写本地文件 | 独立服务，多个应用通过 TCP 连接 |
| 并发写 | 同一时刻只有一个写者 | 多个连接可以同时写（MVCC：读写互不阻塞） |
| 类型和约束 | 类型检查宽松 | 类型严格，支持 JSONB、数组、全文检索 |
| 扩展 | 少 | 丰富，例如 **pgvector** 存向量做相似度检索 |
| 适合 | 桌面和移动端应用、测试、原型 | Web 后端、多实例部署 |

做大模型应用时，pgvector 让你在同一个数据库里存业务数据和向量，P2 阶段做 RAG 会用到。本课的示例和练习用 SQLite，是为了不启动任何服务也能运行；SQLAlchemy 屏蔽了大部分差异，换连接串就能切到 PostgreSQL。

### 1.3 连接串

```
dialect+driver://用户名:密码@主机:端口/数据库名
```

| 连接串 | 含义 |
|---|---|
| `postgresql+psycopg://learn:learn123@localhost:5432/learn` | PostgreSQL，驱动用 psycopg 3（本机已装） |
| `postgresql://...` | 不写驱动时默认用 psycopg2。本机没装，会报 `ModuleNotFoundError: No module named 'psycopg2'` |
| `sqlite+pysqlite:///:memory:` | SQLite 内存库，程序结束数据就没了 |
| `sqlite:///app.db` | 当前目录下的 `app.db`（三个斜杠后面是相对路径） |
| `sqlite:////tmp/app.db` | 绝对路径 `/tmp/app.db`（四个斜杠） |

- 密码里有 `@`、`:`、`/` 时要做 URL 编码（`urllib.parse.quote_plus`），或者用 `sqlalchemy.URL.create(...)` 拼连接串。
- 连接串里有密码，从环境变量读，不要写进代码，打日志时用 `engine.url.render_as_string(hide_password=True)`。

### 1.4 SQLAlchemy 2.0 的核心对象

SQLAlchemy 是 Python 最常用的数据库库，分两层：Core（用 Python 拼 SQL）和 ORM（把表映射成类，把行映射成对象）。本课用 2.0 风格，网上很多教程是 1.x 的 `session.query(User)` 写法，看到时知道是旧写法。

| 对象 | 作用 | Qt 类比 |
|---|---|---|
| `create_engine(url)` | 管理连接池，整个程序通常只创建一个 | `QSqlDatabase::addDatabase` |
| `DeclarativeBase` | 所有模型的基类，`Base.metadata` 记录所有表 | |
| `Mapped[类型]` + `mapped_column()` | 声明一列 | |
| `Session` | 一次“工作单元”：跟踪对象的改动，`commit` 时一起写入，自带事务 | 一个连接上的 `transaction()` 到 `commit()` |
| `sessionmaker(engine)` | 创建 Session 的工厂 | |
| `select(...)` | 构造查询语句 | `QSqlQuery` 的 SQL 字符串 |

### 1.5 定义模型

```python
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[list["Note"]] = relationship(back_populates="user")

class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, default="")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped[User] = relationship(back_populates="notes")
```

| 写法 | 生成的列 |
|---|---|
| `Mapped[int]`，`mapped_column(primary_key=True)` | 整数主键。PostgreSQL 生成 `SERIAL`，插入时数据库自动编号 |
| `Mapped[str]` | `NOT NULL`。类型标注里没有 `None` 就不允许空 |
| `Mapped[str \| None]` | 允许 `NULL` |
| `mapped_column(String(50))` | `VARCHAR(50)`；不写 `mapped_column` 时 `Mapped[str]` 对应不限长度的 `VARCHAR` |
| `Text` | 长文本 |
| `unique=True` / `index=True` | 唯一约束 / 普通索引 |
| `default=""` | 插入时没给值就用 `""`（由 SQLAlchemy 填，不是数据库的 DEFAULT） |
| `ForeignKey("users.id")` | 外键，参数是“表名.列名”，不是类名 |

`relationship` 不是数据库里的列，是 ORM 提供的属性：`user.notes` 得到这个用户的笔记列表，`note.user` 得到笔记的作者。`back_populates` 让两边同步。这就是**一对多**：外键放在“多”的一方（Note）。

建表用 `Base.metadata.create_all(engine)`，它只创建不存在的表，**不会修改已有表的结构**。表结构变更交给 Alembic（见 1.10）。

### 1.6 增删改查

```python
from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(engine, expire_on_commit=False)

with SessionLocal() as session:          # with 结束时 close，把连接还给连接池
    # 增
    note = Note(title="学 SQL", user_id=1)
    session.add(note)
    session.commit()                     # commit 之后 note.id 才有值

    # 查
    session.get(Note, 1)                                       # 按主键，不存在返回 None
    session.scalars(select(Note).where(Note.user_id == 1).order_by(Note.id)).all()   # list[Note]
    session.scalars(select(User).where(User.name == "bob")).one_or_none()
    session.scalar(select(func.count()).select_from(Note))     # 单个值
    session.execute(select(User.name, User.email)).all()       # list[Row]，Row 像 tuple

    # 改：改属性，再 commit
    note.title = "新标题"
    session.commit()

    # 删
    session.delete(note)
    session.commit()
```

| 方法 | 返回 |
|---|---|
| `session.execute(stmt)` | `Result`，每行是 `Row`（可以按下标或列名取） |
| `session.scalars(stmt)` | 每行只取第一列。查 `select(Note)` 时得到 `Note` 对象 |
| `session.scalar(stmt)` | 第一行第一列，没有结果时为 `None` |
| `.all()` / `.first()` / `.one()` / `.one_or_none()` | 全部 / 第一个或 None / 必须正好一行否则抛异常 / 零或一行 |

常用条件：`Note.title == "x"`、`Note.id.in_([1, 2])`、`Note.title.like("学%")`、`Note.title.contains("SQL")`、`Note.email.is_(None)`。多个 `.where()` 之间是 AND。判断 NULL 用 `User.email.is_(None)`。不能写 `User.email is None`：`is` 是 Python 自己的运算，直接得到 `False`，不会生成 SQL。

批量操作不用先查对象：`session.execute(update(Note).where(...).values(title="x"))`、`session.execute(delete(Note).where(...))`，返回值的 `rowcount` 是影响的行数。

**N+1 查询**：先查出 N 个用户，再逐个访问 `user.notes`，会发 1 + N 条 SQL（关系属性默认在第一次访问时才查询，叫懒加载）。统计类需求用 `JOIN + GROUP BY` 一条 SQL 解决；确实要加载关系时用 `selectinload`（P0 项目里遇到再查文档）。

### 1.7 事务：提交与回滚

Session 第一次执行 SQL 时自动开始事务，`commit()` 提交，`rollback()` 撤销本事务里所有没提交的改动。

```python
try:
    session.add(User(name="alice"))   # 假设 name 重复
    session.commit()
except IntegrityError:
    session.rollback()                # 必须回滚
    raise
```

- commit 失败后不回滚，这个 Session 再执行任何 SQL 都会报 `PendingRollbackError`。
- 自己抛的业务异常（余额不足等）如果发生在修改对象之后，也要回滚，否则改了一半的对象会在下一次 `commit` 时被写进去。练习 4 专门检查这一点。

更省心的写法是 `begin()` 上下文管理器，和第二课的 `Transaction` 练习是同一个思路：

```python
with SessionLocal.begin() as session:     # 新建 Session 并开始事务
    session.add(...)
# 正常结束自动 commit；块里抛异常自动 rollback，异常继续往外抛

with session.begin():                     # 已有 Session 时，在它上面开一个事务
    ...
```

`expire_on_commit`：默认 `True`，commit 后对象的属性全部失效，下次访问会重新查数据库。如果 commit 后 Session 已经关闭，再访问属性会报 `DetachedInstanceError`。Web 服务里常设为 `False`，方便 commit 后直接把对象转成响应。

### 1.8 SQL 注入与参数化查询

把用户输入用 f-string 拼进 SQL，用户就能改写你的 SQL。`02_SQL注入与参数化.py` 演示了：

```python
sql = f"SELECT * FROM accounts WHERE name = '{name}' AND password = '{password}'"
# name 填 admin' --  →  WHERE name = 'admin' --' AND password = '...'
# -- 之后是注释，密码检查没了，直接以 admin 登录
```

修复方法是**参数化查询**：SQL 里只写占位符，值单独传给数据库驱动，驱动保证它只被当作数据，不会被解析成 SQL。

```python
from sqlalchemy import text
session.execute(text("SELECT * FROM accounts WHERE name = :name"), {"name": name})
```

| 写法 | 是否安全 |
|---|---|
| ORM：`select(User).where(User.name == name)` | 安全，自动参数化 |
| `text("... WHERE name = :name")` + 参数字典 | 安全 |
| `text(f"... WHERE name = '{name}'")` | **不安全**，`text()` 只是原样执行拼好的字符串 |
| 自己把 `'` 替换成 `''` 再拼接 | 不安全，转义规则因数据库而异，总有遗漏 |
| 表名、列名、`ASC/DESC` | 占位符只能代替**值**，不能代替标识符。用白名单校验后再拼 |

后面做 Text-to-SQL 或让 Agent 执行 SQL 时，注入问题会换个形式出现：模型生成的 SQL 也是不可信输入，需要只读账号、白名单和权限限制。

### 1.9 在 FastAPI 里用 Session（预告 P0 项目）

```python
def get_session():
    with SessionLocal() as session:
        yield session            # 第三课的生成器 + 第六课的依赖注入

@app.get("/notes/{note_id}")
def read_note(note_id: int, session: Session = Depends(get_session)):
    ...
```

每个请求一个 Session，请求结束关闭。不要把一个 Session 放在全局变量里给所有请求共用，Session 不是线程安全的。

### 1.10 Alembic 迁移（简介）

`create_all` 不会给已有的表加列。生产环境改表结构用 **Alembic**（SQLAlchemy 作者写的迁移工具，本机没装，用到时 `pip install alembic`）：

| 命令 | 作用 |
|---|---|
| `alembic init migrations` | 生成迁移目录和配置 |
| `alembic revision --autogenerate -m "add tokens column"` | 对比模型和数据库，生成一个迁移脚本（要人工检查） |
| `alembic upgrade head` | 把数据库升级到最新版本 |
| `alembic downgrade -1` | 回退一个版本 |

迁移脚本和代码一起提交到 git，每个环境执行同样的脚本，表结构就能保持一致。

### 面试怎么问

1. `INNER JOIN` 和 `LEFT JOIN` 有什么区别？统计每个用户的订单数（包括没有订单的用户）怎么写？
2. 索引为什么能加快查询？是不是索引越多越好？
3. 什么是 SQL 注入？参数化查询为什么能防住？表名能不能用参数绑定？
4. 用 SQLAlchemy 时，事务中途出异常不回滚会怎样？什么是 N+1 查询？

---

## 2. Redis（P0-18）

### 2.1 Redis 是什么

Redis 是一个**内存里的键值数据库**，独立进程，客户端通过 TCP 连接。数据放在内存里，单次读写通常在 1 毫秒以内，比查 PostgreSQL 快一到两个数量级。代价是内存贵、容量有限，所以 Redis 一般不当主数据库，而是放**可以丢、可以重建、或者需要很快**的数据。

- 执行命令是单线程的，一条命令执行完才执行下一条，所以 `INCR` 这类单条命令天然是原子的。
- 可以持久化到磁盘（RDB 快照、AOF 日志），本课的 compose 开了 AOF，但不要把它当成和 PostgreSQL 一样可靠。
- 键名用冒号分层是约定俗成的写法，例如 `user:42`、`rate:alice:29030400`。

### 2.2 五种数据类型

| 类型 | 类比 | 常用命令（redis-py 方法同名小写） | 典型用途 |
|---|---|---|---|
| string | `QString` / 数字 | `SET` `GET` `INCR` `INCRBY` `SET ... NX EX` | 缓存、计数器、分布式锁 |
| hash | `QHash<QString, QString>` | `HSET` `HGET` `HGETALL` `HINCRBY` | 存一个对象的多个字段 |
| list | `QList`（两头操作快） | `RPUSH` `LPOP` `LRANGE` `LTRIM` | 消息队列、最近 N 条记录 |
| set | `QSet` | `SADD` `SMEMBERS` `SISMEMBER` | 去重、标签 |
| sorted set | 按分数排序的 `QMap` | `ZADD` `ZINCRBY` `ZRANGE ... REV` | 排行榜、按时间排序 |

所有值最终都是字节串。存进去的数字取出来是字符串 `'10'`，要自己 `int()`；存结构化数据用 `json.dumps` 转成字符串。

### 2.3 过期时间 TTL

```python
r.set("code", "123456", ex=60)    # 60 秒后自动删除；px=200 是毫秒
r.expire("key", 60)               # 给已有的键设过期时间
r.ttl("key")                      # 剩余秒数；-1：键存在但没有过期时间；-2：键不存在
r.persist("key")                  # 去掉过期时间
```

不带 `ex` 的 `SET` 会**清掉原来的过期时间**，这是常见的坑。内存满了时 Redis 按 `maxmemory-policy` 淘汰键（比如淘汰最近最少使用的），所以缓存一定要设 TTL，并且代码要能处理“缓存没了”的情况。

### 2.4 redis-py 基本用法

```python
import redis

r = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)
r.ping()                          # 连不上抛 redis.exceptions.ConnectionError
r.set("greeting", "你好")
r.get("greeting")                 # '你好'；键不存在返回 None
```

| 参数 / 用法 | 说明 |
|---|---|
| `redis://主机:端口/库号` | 库号 0 到 15，默认 0 |
| `decode_responses=True` | 返回 `str`。默认 `False`，返回 `bytes`（`b'\xe4\xbd\xa0\xe5\xa5\xbd'`） |
| `socket_connect_timeout=2` | 连不上时 2 秒失败，不然会等很久 |
| `r.pipeline(transaction=True)` | 把多条命令打包成 `MULTI ... EXEC` 一次发送，中间不会插入别的客户端的命令 |
| `r.scan_iter(match="prefix:*")` | 分批遍历键。不要在生产环境用 `KEYS *`，键多时会卡住整个 Redis |
| `redis.asyncio.Redis` | 异步客户端，方法相同，前面加 `await`，FastAPI 里用这个 |

### 2.5 在大模型应用里的三种用法

`03_Redis基础.py` 第 8 到 10 段是完整代码。

**缓存模型响应**：同样的问题、同样的参数，直接返回上次的答案，省钱也省时间。

```python
key = "llm_cache:" + hashlib.sha256(json.dumps({"model": m, "prompt": p, "temperature": t}, sort_keys=True).encode()).hexdigest()
cached = r.get(key)
if cached is not None:            # 用 is not None：空字符串也是合法的缓存值
    return cached
answer = call_llm(...)
r.set(key, answer, ex=3600)
```

- 键里要包含所有影响结果的参数（模型、温度、系统提示词），否则换了模型还命中旧缓存。
- 用哈希做键，避免几千字的 prompt 直接当键名。
- `temperature > 0` 时每次回答本来就不同，要想清楚缓存是否合适。

**按用户限流**：每个用户每分钟最多调用 N 次，保护 API 额度。

```python
key = f"rate:{user_id}:{int(time.time() // 60)}"   # 固定窗口：每分钟一个键
with r.pipeline(transaction=True) as pipe:
    pipe.incr(key)
    pipe.expire(key, 60)          # 一定要设过期，否则每分钟留下一个永久的键
    count, _ = pipe.execute()
allowed = count <= limit
```

计数放在 Redis 而不是进程内存里，是因为服务通常部署多个实例，计数要共享。固定窗口在窗口交界处可能放过两倍流量，更精确的是滑动窗口（用 sorted set 存时间戳）或令牌桶，面试时能说出这个取舍就行。

**保存会话历史**：多轮对话要把历史消息带给模型。用 list 存 JSON，`LTRIM` 只保留最近 N 条，`EXPIRE` 让闲置的会话自动过期。需要长期保存和查询的对话记录放 PostgreSQL，Redis 只放热数据。

### 面试怎么问

1. Redis 为什么快？它适合存什么数据，不适合存什么？
2. Redis 有哪些数据类型？排行榜、限流、会话历史分别用哪种？
3. 缓存模型响应时，缓存键怎么设计？什么情况下不该缓存？
4. 用 `INCR` + `EXPIRE` 做限流有什么问题？固定窗口和滑动窗口有什么区别？

---

## 3. Docker 与 docker compose（P0-19）

### 3.1 镜像和容器

| Docker | 类比 | 说明 |
|---|---|---|
| 镜像（image） | 安装包 | 只读的文件系统快照 + 启动命令。由多个**层**叠起来 |
| 容器（container） | 运行中的进程 | 从镜像启动，在镜像上面加一个可写层。删容器，可写层就没了 |
| Dockerfile | 构建脚本（类似 CMakeLists.txt） | 描述怎么一步步做出镜像 |
| 镜像仓库（registry） | 软件源 | Docker Hub 等，`docker pull` 从这里下载 |

一个镜像可以启动任意多个容器，互相隔离：各自有文件系统、网络、进程空间。容器和虚拟机的区别是容器共享宿主机内核，启动是秒级，开销小（Mac 上 Docker Desktop 在一个轻量 Linux 虚拟机里跑所有容器）。

Docker 解决的是“在我电脑上能跑”的问题：Python 版本、系统库、依赖包全部打进镜像，任何装了 Docker 的机器上行为一致。

### 3.2 Dockerfile 指令

`docker_demo/Dockerfile` 每一行都有注释，下面是汇总：

| 指令 | 作用 |
|---|---|
| `FROM python:3.13-slim` | 基础镜像，必须是第一条指令。`slim` 是精简的 Debian，比完整版小很多；`alpine` 更小，但用 musl libc，部分 Python 包要现场编译，不推荐新手用 |
| `WORKDIR /app` | 设置后续指令的工作目录，不存在会自动创建 |
| `COPY 源 目标` | 把构建上下文里的文件复制进镜像 |
| `RUN 命令` | **构建时**执行命令，结果保存成一层（装依赖、建用户） |
| `ENV K=V` | 设置环境变量，构建时和运行时都有效 |
| `ARG K` | 只在构建时有效的变量 |
| `EXPOSE 8000` | 声明容器监听的端口，只是文档作用，不会真的对外开放 |
| `USER appuser` | 之后的命令和容器进程用这个用户运行 |
| `CMD [...]` | **容器启动时**默认执行的命令，`docker run 镜像 其他命令` 可以覆盖。只有最后一条 CMD 生效 |
| `ENTRYPOINT [...]` | 固定的启动程序，`docker run` 后面的参数会追加给它 |

`RUN` 和 `CMD` 的区别：`RUN` 在 `docker build` 时执行，`CMD` 在 `docker run` 时执行。

`CMD` 有两种写法：

```dockerfile
CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]   # exec 形式（推荐）：直接启动 uvicorn，它是 1 号进程
CMD uvicorn app:app --host 0.0.0.0                # shell 形式：先启动 /bin/sh，再由 sh 启动 uvicorn
```

shell 形式下 `docker stop` 发出的 SIGTERM 发给了 sh，uvicorn 收不到，没法优雅退出，10 秒后被强制杀掉。

### 3.3 为 Python 应用写 Dockerfile

```dockerfile
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**层缓存**是这里最重要的概念。每条指令生成一层，构建时 Docker 检查这条指令和它用到的文件有没有变化：没变就直接用缓存，变了就从这一层开始往后全部重新执行。

- 先 `COPY requirements.txt` 再 `RUN pip install`，最后才 `COPY . .`：改代码时只有最后几层重建，依赖不用重装，几秒就构建完。
- 如果一开始就 `COPY . .` 再 `pip install`，改任何一行代码都会重装全部依赖。
- 改了 `app.py` 再构建时，输出里 `RUN pip install` 那一步会显示 `CACHED`。

其他要点：

- `PYTHONUNBUFFERED=1`：不缓冲 `print` 输出，`docker logs` 能立刻看到。
- `--no-cache-dir`：不把 pip 的下载缓存留在镜像里。
- 容器里的服务必须监听 `0.0.0.0`。监听 `127.0.0.1` 时只有容器自己能访问，端口映射也没用。
- 不用 root 运行，容器被攻破时影响更小。

### 3.4 .dockerignore、端口、环境变量、数据卷

`docker build -t 名字 .` 最后那个 `.` 是**构建上下文**：这个目录下的文件会全部打包发送给 Docker，`COPY` 只能复制上下文里的文件。`.dockerignore` 的写法和 `.gitignore` 一样，用来排除不需要的文件：

```
__pycache__/
.venv/
.env
.git/
```

排除 `.env` 很关键：`COPY . .` 会把它打进镜像，任何拿到镜像的人都能看到你的 API Key。密钥在运行时通过环境变量传入。

构建并运行 `docker_demo`：

```bash
cd docker_demo
docker build -t lesson07-demo .
docker run --rm -p 8000:8000 -e APP_ENV=docker lesson07-demo
# 另开一个终端
NO_PROXY=localhost,127.0.0.1 curl http://localhost:8000/
```

| `docker run` 参数 | 作用 |
|---|---|
| `-p 8000:8000` | 端口映射，**本机端口:容器端口**。`-p 8080:8000` 就是用本机 8080 访问容器的 8000 |
| `-e APP_ENV=docker` | 设置环境变量；`--env-file .env` 从文件读 |
| `-v pgdata:/var/lib/postgresql/data` | 数据卷，把数据存到容器外面，删容器数据还在 |
| `-v $(pwd):/app` | 绑定挂载，把本机目录映射进容器，开发时改代码不用重新构建 |
| `-d` / `--rm` / `--name` | 后台运行 / 退出后自动删除容器 / 指定容器名 |

### 3.5 docker compose

一个应用通常要 app、PostgreSQL、Redis 几个容器一起跑。docker compose 用一个 YAML 文件描述所有服务，一条命令全部启动。本课的 `docker-compose.yml` 有 postgres 和 redis 两个服务，加上 app 的完整例子是这样（P0 项目会用到）：

```yaml
services:
  app:
    build: .                                  # 用当前目录的 Dockerfile 构建
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+psycopg://learn:learn123@postgres:5432/learn
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy            # 等 postgres 的 healthcheck 通过再启动 app
      redis:
        condition: service_healthy
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: learn
      POSTGRES_PASSWORD: learn123
      POSTGRES_DB: learn
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U learn -d learn"]
      interval: 5s
      retries: 10
  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 10
volumes:
  pgdata:
```

- **服务名就是主机名**。compose 把所有服务放进同一个虚拟网络，app 容器里连数据库写 `postgres:5432`，不是 `localhost:5432`。容器里的 `localhost` 指容器自己。
- 本机上的脚本连容器，走端口映射，写 `localhost:5432`。同一个数据库，从容器内外连接的地址不同，所以连接串一定要放环境变量。
- `depends_on` 只写服务名时，只保证启动顺序，不等对方就绪。PostgreSQL 容器启动后还要几秒才能接受连接，所以要配合 `healthcheck` 和 `condition: service_healthy`。
- 本课的 compose 把端口绑定在 `127.0.0.1` 上，只有本机能连；并且写了 `name: lesson07`，因为 compose 默认用目录名做项目名，而中文目录名不能用作项目名。

### 3.6 常用命令

在 `docker-compose.yml` 所在目录执行：

| 命令 | 作用 |
|---|---|
| `docker compose up -d` | 创建并后台启动所有服务（镜像不存在会先拉取或构建） |
| `docker compose up -d --build` | 先重新构建 app 镜像再启动，改了代码或 Dockerfile 后用 |
| `docker compose up -d --wait` | 启动并等到所有服务 healthy 再返回 |
| `docker compose ps` | 查看服务状态和端口 |
| `docker compose logs -f app` | 跟踪某个服务的日志，Ctrl+C 退出 |
| `docker compose exec postgres psql -U learn -d learn` | 在运行中的容器里执行命令 |
| `docker compose exec redis redis-cli` | 进入 Redis 命令行 |
| `docker compose build` | 只构建镜像 |
| `docker compose stop` | 停止容器，不删除 |
| `docker compose down` | 停止并删除容器和网络，**保留数据卷**，下次 up 数据还在 |
| `docker compose down -v` | 同时删除数据卷，**数据清空** |

单个容器和镜像的命令：`docker ps`（运行中的容器，`-a` 包括已停止的）、`docker images`、`docker logs 容器名`、`docker exec -it 容器名 sh`、`docker rmi 镜像名`、`docker volume ls`。

### 面试怎么问

1. 镜像和容器是什么关系？容器和虚拟机有什么区别？
2. 为 Python 应用写 Dockerfile 时，为什么要先 COPY requirements.txt 再 COPY 代码？
3. compose 里 app 连数据库为什么写 `postgres` 而不是 `localhost`？`depends_on` 能保证数据库已经可以连接了吗？
4. `docker compose down` 和 `docker compose down -v` 有什么区别？容器删了数据会丢吗？

---

## 读完后的自查

下面的问题能不看资料答出来，再开始做练习：

1. `Mapped[str]` 和 `Mapped[str | None]` 生成的列有什么区别？`session.scalars()` 和 `session.execute()` 的返回值有什么不同？
2. Session 里 commit 失败或者业务校验失败时，为什么必须 rollback？`with session.begin():` 帮你做了什么？
3. 为什么 `text(f"... '{name}'")` 仍然有注入风险？排序字段这种列名怎么安全地处理？
4. 用 Redis 缓存模型响应和做限流时，各自为什么一定要设过期时间？`SET` 不带 `ex` 对已有的 TTL 有什么影响？
5. Dockerfile 里 `RUN` 和 `CMD` 的区别是什么？为什么容器里的服务要监听 `0.0.0.0`？
