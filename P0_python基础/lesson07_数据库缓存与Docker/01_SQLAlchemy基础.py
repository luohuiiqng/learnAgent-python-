"""P0-17 SQLAlchemy 2.0 基础：engine、模型、Session、增删改查、一对多、事务回滚。

运行：
    python 01_SQLAlchemy基础.py
        默认用 SQLite 内存库，不需要任何服务，程序结束数据就没了。
    DATABASE_URL=postgresql+psycopg://learn:learn123@localhost:5432/learn python 01_SQLAlchemy基础.py
        先在本课目录执行 docker compose up -d，再用这条命令连 PostgreSQL。
        脚本开头会先删掉本脚本用到的两张表再重建，所以可以反复运行。
"""
import os

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    create_engine,
    delete,
    func,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.schema import CreateTable


def section(title):
    print(f"\n===== {title} =====")


# ---------------------------------------------------------------------------
# 1. 模型：一个 Python 类对应一张表，一个类属性对应一列
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """所有模型的基类。Base.metadata 记录了所有继承它的表。"""


class User(Base):
    __tablename__ = "lesson07_users"

    id: Mapped[int] = mapped_column(primary_key=True)  # 整数主键，数据库自动生成
    name: Mapped[str] = mapped_column(String(50), unique=True)  # Mapped[str] 表示 NOT NULL
    email: Mapped[str | None] = mapped_column(String(100))  # 带 None 表示允许 NULL

    # 一对多：一个用户有多篇笔记。这不是数据库里的列，是 ORM 提供的便捷属性
    notes: Mapped[list["Note"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",  # 删用户时，ORM 顺带删掉他的笔记
        order_by="Note.id",
    )

    def __repr__(self):
        return f"User(id={self.id}, name={self.name!r})"


class Note(Base):
    __tablename__ = "lesson07_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, default="")
    # 外键：这一列的值必须是 lesson07_users.id 里存在的值。index=True 建索引，按用户查笔记更快
    user_id: Mapped[int] = mapped_column(ForeignKey("lesson07_users.id"), index=True)

    user: Mapped[User] = relationship(back_populates="notes")

    def __repr__(self):
        return f"Note(id={self.id}, title={self.title!r}, user_id={self.user_id})"


def demo_engine():
    section("1. 连接串与 engine")
    url = os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    # engine 管理连接池，整个程序通常只创建一个。echo=True 会把每条 SQL 打印出来，调试时很有用
    engine = create_engine(url, echo=False)
    print("  数据库类型:", engine.dialect.name)
    print("  连接串（隐藏密码）:", engine.url.render_as_string(hide_password=True))
    try:
        with engine.connect():  # create_engine 不会连数据库，第一次用到连接时才连
            pass
    except OperationalError as e:
        print("  连不上数据库:", str(e.orig).splitlines()[0])
        print("  先在本课目录运行 docker compose up -d，或者去掉 DATABASE_URL 改用 SQLite")
        engine.dispose()
        return None
    return engine


def demo_create_tables(engine):
    section("2. 建表：metadata.create_all")
    Base.metadata.drop_all(engine)  # 先删后建，保证每次运行结果一样。正式项目里不要这样做，用 Alembic
    Base.metadata.create_all(engine)  # 只创建还不存在的表，不会修改已有表的结构
    print("  已创建的表:", sorted(Base.metadata.tables))
    print("  Note 对应的 CREATE TABLE（不同数据库生成的 SQL 不一样）:")
    ddl = str(CreateTable(Note.__table__).compile(engine)).strip()
    for line in ddl.splitlines():
        print("   ", line.rstrip())


def demo_insert(SessionLocal):
    section("3. 增：add / add_all + commit")
    with SessionLocal() as session:  # with 结束时自动 close，归还连接
        alice = User(name="alice", email="alice@example.com")
        bob = User(name="bob")
        session.add_all([alice, bob])
        print("  commit 之前 alice.id =", alice.id)  # 还没写入数据库，没有 id

        # 通过关系属性添加笔记，不用手动填 user_id
        alice.notes.append(Note(title="学 SQL", content="SELECT / JOIN / 索引"))
        alice.notes.append(Note(title="学 Redis", content="TTL 和限流"))
        bob.notes.append(Note(title="学 Docker"))

        session.commit()  # 真正写入数据库，事务结束
        print("  commit 之后 alice.id =", alice.id, " bob.id =", bob.id)


def demo_select(SessionLocal):
    section("4. 查：get / select / where / order_by")
    with SessionLocal() as session:
        print("  按主键取:", session.get(User, 1))
        print("  主键不存在:", session.get(User, 999))

        stmt = select(Note).where(Note.title.like("学%")).order_by(Note.id)
        print("  select 语句会被编译成:", " ".join(str(stmt).split()))
        notes = session.scalars(stmt).all()  # scalars：每行只取第一个对象
        print("  标题以“学”开头的笔记:", notes)

        bob = session.scalars(select(User).where(User.name == "bob")).one()  # 必须正好一行，否则抛异常
        print("  name == 'bob':", bob)
        nobody = session.scalars(select(User).where(User.name == "carol")).one_or_none()
        print("  name == 'carol':", nobody)

        total = session.scalar(select(func.count()).select_from(Note))
        print("  笔记总数:", total)

        rows = session.execute(select(User.name, User.email).order_by(User.id)).all()
        print("  只查两列，得到的是 Row（像 tuple）:", [tuple(r) for r in rows])


def demo_update_delete(SessionLocal):
    section("5. 改与删")
    with SessionLocal() as session:
        note = session.get(Note, 3)
        note.title = "学 Docker Compose"  # 改属性就行，commit 时 ORM 生成 UPDATE
        session.commit()
        print("  改标题后:", session.get(Note, 3))

        # 批量更新：直接生成一条 UPDATE ... WHERE，不用先把对象查出来
        result = session.execute(update(Note).where(Note.user_id == 1).values(content="已复习"))
        session.commit()
        print("  批量 UPDATE 影响行数:", result.rowcount)

        session.delete(session.get(Note, 2))
        session.commit()
        print("  删除 id=2 后剩余:", session.scalars(select(Note).order_by(Note.id)).all())

        result = session.execute(delete(Note).where(Note.title == "不存在的标题"))
        session.commit()
        print("  批量 DELETE 没匹配到时 rowcount:", result.rowcount)


def demo_relationship(SessionLocal):
    section("6. 一对多：关系属性与 JOIN")
    with SessionLocal() as session:
        alice = session.scalars(select(User).where(User.name == "alice")).one()
        print("  alice.notes:", alice.notes)  # 第一次访问时 ORM 自动发一条 SELECT
        note = session.get(Note, 1)
        print("  note.user:", note.user)

        session.add(User(name="carol"))  # carol 没有笔记
        session.commit()

        # 每个用户的笔记数。outerjoin = LEFT OUTER JOIN，没有笔记的用户也保留，计数为 0
        stmt = (
            select(User.name, func.count(Note.id))
            .outerjoin(Note, Note.user_id == User.id)
            .group_by(User.id, User.name)
            .order_by(User.id)
        )
        print("  LEFT JOIN 计数:", [tuple(r) for r in session.execute(stmt)])
        stmt_inner = (
            select(User.name, func.count(Note.id))
            .join(Note, Note.user_id == User.id)
            .group_by(User.id, User.name)
            .order_by(User.id)
        )
        print("  INNER JOIN 计数（carol 不见了）:", [tuple(r) for r in session.execute(stmt_inner)])


def demo_transaction(SessionLocal):
    section("7. 事务：出错就 rollback")
    with SessionLocal() as session:
        session.add(Note(title="这条会被回滚", user_id=1))
        session.add(User(name="alice"))  # name 有唯一约束，重复了
        try:
            session.commit()
        except IntegrityError as e:
            print("  commit 失败:", type(e).__name__)
            session.rollback()  # 必须回滚，否则这个 session 后续操作都会报 PendingRollbackError
        titles = session.scalars(select(Note.title).order_by(Note.id)).all()
        print("  回滚后笔记标题（同一事务里的笔记也没写进去）:", titles)

    # 更常用的写法：Session.begin() 正常结束自动 commit，出异常自动 rollback 并继续抛出
    try:
        with SessionLocal.begin() as session:
            session.add(Note(title="也会被回滚", user_id=1))
            raise ValueError("业务校验失败")
    except ValueError as e:
        print("  with SessionLocal.begin() 里抛出:", e)

    with SessionLocal.begin() as session:
        session.add(Note(title="正常提交", user_id=2))

    with SessionLocal() as session:
        titles = session.scalars(select(Note.title).order_by(Note.id)).all()
        print("  最终笔记标题:", titles)


def main():
    engine = demo_engine()
    if engine is None:
        return
    # sessionmaker 是创建 Session 的工厂，绑定 engine。expire_on_commit=False 让 commit 后还能读对象属性
    SessionLocal = sessionmaker(engine, expire_on_commit=False)
    demo_create_tables(engine)
    demo_insert(SessionLocal)
    demo_select(SessionLocal)
    demo_update_delete(SessionLocal)
    demo_relationship(SessionLocal)
    demo_transaction(SessionLocal)
    engine.dispose()  # 关闭连接池里的所有连接


if __name__ == "__main__":
    main()
