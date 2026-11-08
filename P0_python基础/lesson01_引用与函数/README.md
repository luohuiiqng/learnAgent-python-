# 第一课：写给 C++ 程序员的 Python（引用、容器、函数）

**覆盖知识点**：P0-01 变量与引用语义 ★、P0-02 内置容器与推导式、P0-03 函数与参数 ★
**预计用时**：3 到 4 小时

## 学习步骤

1. 按顺序读下面三节。每节读完，运行对应的示例文件，对照输出读代码注释：

   ```bash
   cd P0_python基础/lesson01_引用与函数
   python 01_引用语义.py
   python 02_容器与推导式.py
   python 03_函数参数.py
   ```

   用 `python`，不要用 `python3`。你电脑上的 `python3` 是另一个没装依赖的版本。

2. 遇到和你预期不一样的输出，先自己改代码验证猜想。比如在示例里加几行 `print(id(x))`。
3. 完成 `练习.py` 里的 6 道题，运行 `python 练习.py`，直到全部通过。
4. 告诉教练“第一课学完了”，开始评估：L1 口述、L2 预测输出、L3 闭卷编码。

---

## 1. 变量与引用语义（P0-01）

### 1.1 Python 的变量是贴在对象上的名字

C++ 里，`int a = 1;` 的 `a` 是一块内存，`b = a` 把值复制过去。
Python 里，**所有数据都是堆上的对象，变量只是指向对象的名字**。最接近的 C++ 类比是：每个变量都是一个 `std::shared_ptr<Object>`。

```python
a = [1, 2, 3]
b = a          # 复制的是"指针"，列表本身只有一份
b.append(4)
print(a)       # [1, 2, 3, 4]
```

这个类比在两点上也成立：

- Python 用**引用计数**管理内存（和 `shared_ptr` 一样），计数归零时对象被回收，另有垃圾回收器处理循环引用。
- 没有 `delete`，也没有悬空指针。

### 1.2 `==` 和 `is`

| Python | C++ 类比 | 含义 |
|---|---|---|
| `a == b` | `*pa == *pb` | 值是否相等（调用 `__eq__`） |
| `a is b` | `pa == pb` | 是不是同一个对象 |
| `id(a)` | `(void*)pa` | 对象的身份标识 |

`is` 基本只用在 `x is None` 上。不要用 `is` 比较数字和字符串：小整数和部分字符串会被解释器缓存，`is` 有时为真有时为假，这是实现细节，不能依赖。

### 1.3 可变对象与不可变对象

| 不可变（immutable） | 可变（mutable） |
|---|---|
| `int` `float` `bool` `str` `tuple` `bytes` `frozenset` `None` | `list` `dict` `set` 以及大多数自定义类的实例 |

不可变对象没有任何方法能改变它本身。看起来像"修改"的操作，其实是**创建新对象，再把名字指过去**：

```python
n = 10
m = n
n += 1     # 创建新对象 11，n 指向它；m 仍然指向 10
```

同样写 `+=`，结果却取决于对象是否可变：

```python
l1 = [1]; l2 = l1
l1 += [2]        # list 可变，+= 原地修改（等价 extend），l2 也变成 [1, 2]
l1 = l1 + [3]    # + 创建新列表，l1 指向新对象，l2 还是 [1, 2]
```

Python 没有 `const`。`tuple` 不可变，指的是它里面那几个"指针"不能换，但指针指向的 `list` 照样可以修改：`(1, [2, 3])[1].append(4)` 是合法的。

### 1.4 函数传参：传的是对象引用

Python 既不是传值也不是传引用，官方叫法是"传对象引用"（call by sharing）。用 C++ 类比，就是**按值传一个 `shared_ptr`**：

- 函数里**修改对象**（`items.append(...)`），调用方能看到。
- 函数里**给参数重新赋值**（`items = [...]`），只是让局部名字指向别处，调用方看不到。

所以，如果函数不打算修改调用方的数据，就不要在传进来的可变对象上直接改。

### 1.5 拷贝

| 写法 | 效果 |
|---|---|
| `b = a` | 不拷贝，两个名字指向同一对象 |
| `a.copy()`、`a[:]`、`list(a)`、`copy.copy(a)` | **浅拷贝**：新建外层容器，里面的元素仍然是共享的 |
| `copy.deepcopy(a)` | **深拷贝**：递归复制所有层 |

两个高频陷阱：

```python
grid = [[0] * 3] * 3     # 外层 3 个元素指向同一个内层列表，改一个三行全变
grid = [[0] * 3 for _ in range(3)]   # 正确：每行是独立的列表
```

`[0] * 3` 没问题，因为 `0` 是不可变的；`[[0] * 3] * 3` 复制的是指向同一个列表的引用。

---

## 2. 内置容器与推导式（P0-02）

### 2.1 四种容器

| Python | C++/Qt 类比 | 特点 |
|---|---|---|
| `list` `[1, 2]` | `std::vector` / `QList` | 有序、可变；存的是对象引用，可以混放不同类型 |
| `dict` `{"k": 1}` | `std::unordered_map` / `QHash` | 键值对；从 3.7 起**保持插入顺序**；键必须可哈希 |
| `set` `{1, 2}` | `std::unordered_set` / `QSet` | 去重、集合运算 `& \| -` |
| `tuple` `(1, 2)` | 不可变的 `std::tuple` | 不可变；元素都可哈希时，tuple 本身也可哈希，能当 dict 的键 |

注意 `{}` 是空 dict，空 set 要写 `set()`。

### 2.2 常用操作和复杂度

| 操作 | 复杂度 | 说明 |
|---|---|---|
| `lst.append(x)` | 均摊 O(1) | |
| `lst.insert(0, x)`、`lst.pop(0)` | O(n) | 频繁在头部操作用 `collections.deque` |
| `x in lst` | O(n) | 要频繁查找就转成 set |
| `x in st`、`k in dct` | 平均 O(1) | |
| `lst[i:j]` | O(j-i) | 切片会**创建新列表** |

dict 和 C++ 的一个关键区别：`d["不存在的键"]` 会抛 `KeyError`，而 C++ 的 `operator[]` 会插入默认值。读可能不存在的键用 `d.get(k, 默认值)`。需要"不存在就创建"时，用 `d.setdefault(k, [])` 或 `collections.defaultdict`。

### 2.3 写出 Python 风格的循环

```python
for i, w in enumerate(words):     # 代替 for (int i = 0; i < n; ++i)
for name, score in zip(names, scores):   # 同时遍历两个序列
for k, v in d.items():            # 遍历字典
first, *rest = [1, 2, 3]          # 解包
a, b = b, a                       # 交换
```

**不要边遍历边删除元素**：删除后后面的元素前移，循环会跳过下一个元素（和 C++ 里边遍历边 `erase` 导致迭代器失效是同一类问题）。正确做法是用推导式生成新列表。

### 2.4 推导式

```python
[x * x for x in nums]                 # 列表推导式
[x for x in nums if x > 0]            # 带过滤
{w: len(w) for w in words}            # 字典推导式
{len(w) for w in words}               # 集合推导式
```

可以理解为 `std::transform` 加 `std::copy_if` 的一行写法。推导式超过一行、逻辑变复杂时，改回普通 for 循环，可读性更重要。

---

## 3. 函数与参数（P0-03）

### 3.1 基本规则

- 没有 `return` 的函数返回 `None`。
- `return a, b` 实际返回一个 tuple，调用方用 `x, y = f()` 解包。
- **没有函数重载**。同名函数后定义的会覆盖前面的。Python 用默认参数和关键字参数代替重载。
- 类型标注（`def f(x: int) -> str`）运行时不检查，只给人和工具看。P0-09 会细讲。

### 3.2 参数的几种形式

```python
def f(a, b=2, *args, c, d=4, **kwargs): ...
```

| 部分 | 含义 |
|---|---|
| `a` | 普通参数，可以按位置传，也可以按关键字传 |
| `b=2` | 带默认值的参数 |
| `*args` | 收集多余的位置参数，类型是 **tuple** |
| `c`、`d=4` | 出现在 `*args`（或单独的 `*`）后面，**只能用关键字传** |
| `**kwargs` | 收集多余的关键字参数，类型是 **dict** |

强制关键字参数常用在 SDK 里：`create_client("qwen", temperature=0)` 比 `create_client("qwen", 0)` 清楚得多。OpenAI SDK 的 `chat.completions.create(...)` 所有参数都只能用关键字传。

### 3.3 默认参数陷阱（面试高频）

**默认值在 `def` 语句执行时计算一次，之后每次调用共用同一个对象。** C++ 的默认参数是每次调用时重新求值，所以 C++ 程序员特别容易踩这个坑：

```python
def add(item, items=[]):    # 这个 [] 只创建一次，保存在 add.__defaults__ 里
    items.append(item)
    return items

add(1)   # [1]
add(2)   # [1, 2]  ← 上次的结果还在
```

惯用写法是用 `None` 当默认值，在函数内部创建新对象：

```python
def add(item, items=None):
    if items is None:
        items = []
    ...
```

### 3.4 调用时解包

```python
args = ["3 * 4", 1]
kwargs = {"expression": "1 + 2", "precision": 4}
calculate(*args)       # 等价于 calculate("3 * 4", 1)
calculate(**kwargs)    # 等价于 calculate(expression="1 + 2", precision=4)
```

这就是仓库里 `example_agents/FunctionCallingAgent/tools.py` 中 `tool["func"](**arguments)` 的原理：模型返回的工具参数是 JSON，解析成 dict 后，用 `**` 展开成关键字参数调用函数。参数名对不上时会抛 `TypeError`，所以那里专门捕获了 `TypeError`。

### 3.5 函数是对象

函数可以赋值给变量、存进 dict、作为参数传递，类似 `std::function`。`lambda a, b: a + b` 是匿名函数，函数体只能是一个表达式。ToolRegistry 就是用 dict 把"工具名"映射到"函数对象"。

---

## 读完后的自查

下面的问题能不看资料答出来，再开始做练习：

1. `b = a` 之后修改 `b`，什么情况下 `a` 会变，什么情况下不会变？
2. 为什么 `[[0] * 3] * 3` 有问题，而 `[0] * 3` 没问题？
3. 函数里 `items.append(x)` 和 `items = [x]` 对调用方的影响有什么不同？
4. 为什么可变对象不能做默认参数？正确写法是什么？
5. `*args` 和 `**kwargs` 分别是什么类型？调用时的 `*` 和 `**` 又是什么意思？
