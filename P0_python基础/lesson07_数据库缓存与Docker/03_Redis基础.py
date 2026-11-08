"""P0-18 Redis 基础：五种数据类型、TTL、decode_responses，以及大模型应用里的三种用法。

运行前先启动 Redis（在本课目录）：
    docker compose up -d
然后：
    python 03_Redis基础.py
默认连接 redis://localhost:6379/0，可以用环境变量 REDIS_URL 修改，例如
    REDIS_URL=redis://localhost:6380/0 python 03_Redis基础.py

本脚本只读写以 lesson07:demo: 开头的键，开始和结束时都会清理这些键，不会动库里的其他数据。
"""
import hashlib
import json
import os
import time

import redis

PREFIX = "lesson07:demo:"


def section(title):
    print(f"\n===== {title} =====")


def connect():
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    # decode_responses=True：返回 str；不加则返回 bytes
    # socket_connect_timeout：连不上时 2 秒内失败，而不是一直等
    r = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
    try:
        r.ping()
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        print(f"连不上 Redis（{url}）：{e}")
        print("先在本课目录运行 docker compose up -d，等 docker compose ps 显示 healthy 后再运行本脚本。")
        print("如果 Redis 不在默认端口，用环境变量 REDIS_URL 指定，例如 REDIS_URL=redis://localhost:6380/0")
        return None, url
    return r, url


def cleanup(r):
    keys = list(r.scan_iter(match=PREFIX + "*"))  # scan_iter 分批遍历，不会像 KEYS 那样阻塞服务器
    if keys:
        r.delete(*keys)
    return len(keys)


def demo_decode(url):
    section("1. decode_responses：bytes 还是 str")
    raw = redis.Redis.from_url(url)  # 默认 decode_responses=False
    raw.set(PREFIX + "greeting", "你好")
    print("  decode_responses=False:", raw.get(PREFIX + "greeting"))
    text = redis.Redis.from_url(url, decode_responses=True)
    print("  decode_responses=True: ", text.get(PREFIX + "greeting"))
    print("  不存在的键:", text.get(PREFIX + "missing"))
    raw.close()
    text.close()


def demo_string(r):
    section("2. string：最基本的键值")
    k = PREFIX + "counter"
    r.set(k, 10)
    print("  set 10 后 get:", repr(r.get(k)), " ← 存进去的是数字，取出来是字符串")
    print("  incr:", r.incr(k), " incrby 5:", r.incrby(k, 5))  # 原子自增，多个进程同时加也不会丢
    print("  set nx=True（键已存在）:", r.set(k, 0, nx=True), " 值仍是:", r.get(k))
    print("  set nx=True（键不存在）:", r.set(PREFIX + "lock", "worker-1", nx=True))


def demo_hash(r):
    section("3. hash：一个键下面存多个字段，适合存对象")
    k = PREFIX + "user:42"
    r.hset(k, mapping={"name": "alice", "plan": "free", "used_tokens": 0})
    r.hincrby(k, "used_tokens", 1200)
    print("  hgetall:", r.hgetall(k))
    print("  hget plan:", r.hget(k, "plan"))


def demo_list(r):
    section("4. list：有序可重复，两头进出都是 O(1)")
    k = PREFIX + "queue"
    r.rpush(k, "task-1", "task-2", "task-3")  # 从右边（尾部）追加
    print("  lrange 0 -1:", r.lrange(k, 0, -1))  # -1 表示最后一个
    print("  lpop:", r.lpop(k), " 剩余:", r.lrange(k, 0, -1))
    r.rpush(k, "task-4", "task-5")
    r.ltrim(k, -2, -1)  # 只保留最后 2 个
    print("  ltrim 保留最后 2 个:", r.lrange(k, 0, -1))


def demo_set(r):
    section("5. set：无序去重")
    k = PREFIX + "tags"
    print("  sadd 返回新增个数:", r.sadd(k, "python", "redis", "python"))
    print("  smembers（排序后打印，set 本身无序）:", sorted(r.smembers(k)))
    print("  sismember redis:", r.sismember(k, "redis"))


def demo_zset(r):
    section("6. sorted set：每个成员带一个分数，按分数排序")
    k = PREFIX + "model_calls"
    r.zadd(k, {"qwen": 30, "deepseek": 50, "llama": 10})
    r.zincrby(k, 25, "qwen")
    print("  分数从高到低:", r.zrange(k, 0, -1, desc=True, withscores=True))
    print("  前 2 名:", r.zrange(k, 0, 1, desc=True))


def demo_ttl(r):
    section("7. 过期时间 TTL")
    k = PREFIX + "code"
    r.set(k, "123456", ex=60)  # 60 秒后自动删除
    print("  ttl 在 (0, 60] 之内:", 0 < r.ttl(k) <= 60)
    r.persist(k)
    print("  persist 后 ttl:", r.ttl(k), " ← -1 表示键存在但没有过期时间")
    print("  不存在的键 ttl:", r.ttl(PREFIX + "missing"), " ← -2 表示键不存在")
    r.set(k, "123456", px=200)  # px 单位是毫秒
    time.sleep(0.3)
    print("  0.3 秒后:", r.get(k))
    r.set(k, "v1", ex=60)
    r.set(k, "v2")  # 注意：普通 set 会清掉原来的过期时间
    print("  重新 set 不带 ex 后 ttl:", r.ttl(k))


# ---------------------------------------------------------------------------
# 大模型应用里的三种常见用法
# ---------------------------------------------------------------------------
def cached_chat(r, model, prompt, temperature, call_llm, ttl=3600):
    """缓存模型响应。键里要包含所有影响结果的参数，否则换了模型也会命中旧缓存。"""
    raw_key = json.dumps({"model": model, "prompt": prompt, "temperature": temperature}, sort_keys=True)
    key = PREFIX + "llm_cache:" + hashlib.sha256(raw_key.encode()).hexdigest()
    cached = r.get(key)
    if cached is not None:
        return cached, True
    answer = call_llm(model, prompt)
    r.set(key, answer, ex=ttl)
    return answer, False


def allow_request(r, user_id, limit, window_seconds):
    """固定窗口限流：每个用户每个时间窗口最多 limit 次。"""
    window = int(time.time() // window_seconds)
    key = f"{PREFIX}rate:{user_id}:{window}"
    # pipeline(transaction=True) 把两条命令打包成 MULTI/EXEC 一起执行
    with r.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, window_seconds)  # 一定要设过期，否则计数键永远留在内存里
        count, _ = pipe.execute()
    return count <= limit


def append_history(r, session_id, role, content, max_messages=6, ttl=1800):
    """会话历史：list 里存 JSON，只保留最近 max_messages 条，闲置 ttl 秒后整段过期。"""
    key = f"{PREFIX}history:{session_id}"
    with r.pipeline(transaction=True) as pipe:
        pipe.rpush(key, json.dumps({"role": role, "content": content}, ensure_ascii=False))
        pipe.ltrim(key, -max_messages, -1)
        pipe.expire(key, ttl)
        pipe.execute()


def get_history(r, session_id):
    return [json.loads(x) for x in r.lrange(f"{PREFIX}history:{session_id}", 0, -1)]


def demo_llm(r):
    section("8. 用法一：缓存模型响应")
    calls = []

    def fake_llm(model, prompt):
        calls.append(prompt)
        return f"[{model}] 对“{prompt}”的回答"

    print("  第一次:", cached_chat(r, "qwen", "什么是 RAG", 0, fake_llm))
    print("  第二次:", cached_chat(r, "qwen", "什么是 RAG", 0, fake_llm))
    print("  换模型:", cached_chat(r, "deepseek", "什么是 RAG", 0, fake_llm))
    print("  真正调用模型的次数:", len(calls))

    section("9. 用法二：按用户限流")
    # 窗口取 3600 秒，演示几毫秒就跑完，正好跨过整点的概率可以忽略
    print("  alice 连续 4 次（每小时 3 次）:", [allow_request(r, "alice", 3, 3600) for _ in range(4)])
    print("  bob 第 1 次:", allow_request(r, "bob", 3, 3600))

    section("10. 用法三：保存会话历史")
    for i in range(1, 5):
        append_history(r, "s1", "user", f"问题 {i}", max_messages=6)
        append_history(r, "s1", "assistant", f"回答 {i}", max_messages=6)
    history = get_history(r, "s1")
    print("  写入 8 条，只保留最近 6 条:")
    for m in history:
        print("   ", m)
    print("  ttl 在 (0, 1800] 之内:", 0 < r.ttl(f"{PREFIX}history:s1") <= 1800)


def main():
    r, url = connect()
    if r is None:
        return  # 正常退出，退出码 0
    cleanup(r)
    print("已连接:", url)
    demo_decode(url)
    demo_string(r)
    demo_hash(r)
    demo_list(r)
    demo_set(r)
    demo_zset(r)
    demo_ttl(r)
    demo_llm(r)
    section("清理")
    print("  删除本脚本创建的键:", cleanup(r), "个")
    r.close()


if __name__ == "__main__":
    main()
