"""P0-17 SQL 注入与参数化查询。运行：python 02_SQL注入与参数化.py

只用 SQLite 内存库，不需要任何服务。
演示里的“危险写法”只用于理解原理，不要在真实代码里使用。
"""
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


def section(title):
    print(f"\n===== {title} =====")


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]  # 演示用明文。真实项目只存密码哈希（例如 bcrypt / argon2）
    is_admin: Mapped[bool] = mapped_column(default=False)


def setup():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([
            Account(name="admin", password="s3cret", is_admin=True),
            Account(name="alice", password="alice123"),
            Account(name="O'Brien", password="ob123"),
        ])
        session.commit()
    return engine


# ---------------------------------------------------------------------------
# 危险写法：把用户输入用 f-string 拼进 SQL
# ---------------------------------------------------------------------------
def login_unsafe(session, name, password):
    sql = f"SELECT id, name, is_admin FROM accounts WHERE name = '{name}' AND password = '{password}'"
    print("    实际执行的 SQL:", sql)
    # 外面包一层 text() 也没用：拼接已经发生了，text() 只是原样执行这个字符串
    return session.execute(text(sql)).first()


def search_unsafe(session, name):
    sql = f"SELECT id, name FROM accounts WHERE name = '{name}' ORDER BY id"
    print("    实际执行的 SQL:", sql)
    return [tuple(r) for r in session.execute(text(sql))]


# ---------------------------------------------------------------------------
# 安全写法：SQL 里只写占位符 :name，值通过第二个参数单独传给数据库驱动
# ---------------------------------------------------------------------------
def login_safe(session, name, password):
    sql = text("SELECT id, name, is_admin FROM accounts WHERE name = :name AND password = :password")
    return session.execute(sql, {"name": name, "password": password}).first()


def search_safe(session, name):
    sql = text("SELECT id, name FROM accounts WHERE name = :name ORDER BY id")
    return [tuple(r) for r in session.execute(sql, {"name": name})]


ALLOWED_SORT = {"id": "id", "name": "name"}


def list_sorted(session, order_by):
    """列名、表名、ASC/DESC 不能用占位符绑定，只能用白名单。"""
    column = ALLOWED_SORT.get(order_by)
    if column is None:
        raise ValueError(f"不支持的排序字段: {order_by!r}")
    sql = text(f"SELECT name FROM accounts ORDER BY {column}")  # column 只可能是白名单里的值
    return session.scalars(sql).all()


def demo_unsafe(engine):
    section("1. f-string 拼 SQL：登录绕过")
    with Session(engine) as session:
        print("  正常登录 alice / alice123:")
        print("    结果:", tuple(login_unsafe(session, "alice", "alice123")))
        print("  攻击者用户名填 admin' --，密码随便填:")
        row = login_unsafe(session, "admin' --", "随便")
        print("    结果:", tuple(row), "  ← 没有密码也以 admin 身份登录了")
        print("  原因：-- 在 SQL 里是注释，后面的 AND password = ... 被注释掉了")


def demo_unsafe_search(engine):
    section("2. f-string 拼 SQL：数据泄露和语法错误")
    with Session(engine) as session:
        print("  输入 ' OR '1'='1:")
        print("    结果:", search_unsafe(session, "' OR '1'='1"), " ← 返回了全部用户")
        print("  输入正常的名字 O'Brien:")
        try:
            search_unsafe(session, "O'Brien")
        except OperationalError as e:
            print("    报错:", type(e).__name__, "← 名字里的单引号把 SQL 截断了")


def demo_safe(engine):
    section("3. 参数化查询：text() + :占位符")
    captured = []

    # 监听驱动真正收到的内容：SQL 字符串和参数是分开传的
    def capture(conn, cursor, statement, parameters, context, executemany):
        captured.append((statement, parameters))

    event.listen(engine, "before_cursor_execute", capture)
    with Session(engine) as session:
        print("  admin' -- 登录:", login_safe(session, "admin' --", "随便"))
        print("  ' OR '1'='1 搜索:", search_safe(session, "' OR '1'='1"))
        print("  O'Brien 搜索:", search_safe(session, "O'Brien"))
        print("  正常登录 alice:", tuple(login_safe(session, "alice", "alice123")))
    event.remove(engine, "before_cursor_execute", capture)

    statement, parameters = captured[2]
    print("  驱动收到的 SQL:", statement)
    print("  驱动收到的参数:", parameters)
    print("  SQL 里只有占位符（SQLite 驱动用 ?），用户输入只出现在参数里，不会被当成 SQL 解析")


def demo_orm(engine):
    section("4. ORM 的 select() 自动参数化")
    stmt = select(Account.id).where(Account.name == "' OR '1'='1")
    print("  编译后的 SQL:", " ".join(str(stmt).split()))
    print("  绑定参数:", stmt.compile().params)
    with Session(engine) as session:
        print("  查询结果:", session.scalars(stmt).all())


def demo_whitelist(engine):
    section("5. 列名不能绑定：用白名单")
    with Session(engine) as session:
        print("  order_by='name':", list_sorted(session, "name"))
        try:
            list_sorted(session, "name; DROP TABLE accounts")
        except ValueError as e:
            print("  恶意排序字段:", e)


def main():
    engine = setup()
    demo_unsafe(engine)
    demo_unsafe_search(engine)
    demo_safe(engine)
    demo_orm(engine)
    demo_whitelist(engine)
    engine.dispose()


if __name__ == "__main__":
    main()
