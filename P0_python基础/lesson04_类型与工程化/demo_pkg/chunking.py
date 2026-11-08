"""文本切块。RAG 里把长文档切成小段再做向量化，用的就是这类函数。

这是 练习_test_chunk.py 的被测函数，不要修改这个文件。
"""


def chunk_text(text: str, size: int, overlap: int = 0) -> list[str]:
    """把 text 按字符切成长度为 size 的块，相邻两块重叠 overlap 个字符。

    规则：
    - size 必须大于 0，否则抛 ValueError；
    - overlap 必须满足 0 <= overlap < size，否则抛 ValueError；
    - 每块的起点比上一块往后移 size - overlap 个字符；
    - 最后一块可以比 size 短；某一块已经到达文本末尾时就停止，
      不会再产生一个被上一块完全包含的块；
    - 空字符串返回 []。

    chunk_text("abcdefg", 3)     -> ["abc", "def", "g"]
    chunk_text("abcdefg", 3, 1)  -> ["abc", "cde", "efg"]
    chunk_text("abcdef", 4, 2)   -> ["abcd", "cdef"]
    chunk_text("ab", 5)          -> ["ab"]
    """
    if size <= 0:
        raise ValueError("size 必须大于 0")
    if not 0 <= overlap < size:
        raise ValueError("overlap 必须满足 0 <= overlap < size")
    chunks = []
    step = size - overlap
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        if start + size >= len(text):
            break
        start += step
    return chunks
