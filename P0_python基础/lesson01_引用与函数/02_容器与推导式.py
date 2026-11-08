"""P0-02 内置容器与推导式。运行：python 02_容器与推导式.py"""
import timeit
from collections import Counter, defaultdict


def section(title):
    print(f"\n===== {title} =====")


section("1. list：类似 QList / std::vector，可以混放任意类型")
nums = [5, 3, 8, 1]
nums.append(10)  # 末尾追加，均摊 O(1)
nums.insert(0, 0)  # 头部插入，O(n)
print("nums =", nums)
print("首个:", nums[0], " 最后一个:", nums[-1])  # 负数下标从末尾数
print("切片 [1:3]:", nums[1:3], " 反转 [::-1]:", nums[::-1])  # 切片返回新列表
first, *middle, last = nums  # 解包，*middle 收集中间部分
print("first =", first, " middle =", middle, " last =", last)
a, b = 1, 2
a, b = b, a  # 交换不需要临时变量
print("交换后 a =", a, " b =", b)

section("2. dict：类似 QHash / std::unordered_map，但会保持插入顺序")
ages = {"alice": 30, "bob": 25}
ages["carol"] = 35
print("ages =", ages)
print("get 不存在的键:", ages.get("dave"), " 带默认值:", ages.get("dave", 0))
try:
    ages["dave"]  # 用 [] 读不存在的键会抛异常，而 C++ 的 operator[] 会插入默认值
except KeyError as e:
    print("KeyError:", e)
for name, age in ages.items():
    print(f"  {name} -> {age}")
print("'bob' in ages:", "bob" in ages)  # in 检查的是键

section("3. set：去重和集合运算")
tags = ["qt", "python", "qt", "llm", "python"]
print("去重:", set(tags))
s1, s2 = {"qt", "cpp", "llm"}, {"python", "llm"}
print("交集:", s1 & s2, " 并集:", s1 | s2, " 差集:", s1 - s2)

section("4. tuple 可以做 dict 的键，list 不行（键必须可哈希）")
distance = {("北京", "上海"): 1200}
print(distance[("北京", "上海")])
try:
    {["北京", "上海"]: 1200}
except TypeError as e:
    print("TypeError:", e)

section("5. 推导式：用一行表达式构造容器")
squares = [x * x for x in range(6)]
evens = [x for x in range(10) if x % 2 == 0]
words = ["qt", "python", "llm", "agent"]
lengths = {w: len(w) for w in words}  # 字典推导式
unique_lens = {len(w) for w in words}  # 集合推导式
print("squares =", squares)
print("evens =", evens)
print("lengths =", lengths)
print("unique_lens =", unique_lens)

section("6. enumerate 和 zip：替代 C 风格的下标循环")
for i, w in enumerate(words, start=1):
    print(f"  {i}. {w}")
scores = [90, 85, 77, 60]
print("zip 成字典:", dict(zip(words, scores)))

section("7. defaultdict 和 Counter")
by_len = defaultdict(list)  # 读不存在的键时自动创建空 list
for w in words:
    by_len[len(w)].append(w)
print("按长度分组:", dict(by_len))
print("词频:", Counter("hello world").most_common(3))

section("8. 复杂度：在 list 里用 in 是 O(n)，在 set 里平均 O(1)")
big_list = list(range(100_000))
big_set = set(big_list)
t_list = timeit.timeit(lambda: 99_999 in big_list, number=200)
t_set = timeit.timeit(lambda: 99_999 in big_set, number=200)
print(f"list: {t_list:.4f}s  set: {t_set:.6f}s")

section("9. 不要边遍历边删除")
data = [1, 2, 2, 3]
for x in data:
    if x == 2:
        data.remove(x)  # 删除后后面的元素前移，会跳过下一个元素
print("边遍历边删除的结果:", data)  # 期望 [1, 3]，实际少删了一个
data = [1, 2, 2, 3]
data = [x for x in data if x != 2]  # 正确做法：生成新列表
print("推导式过滤的结果:", data)
