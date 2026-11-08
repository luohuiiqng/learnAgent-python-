"""conftest.py 里定义的 fixture，同目录及子目录下的所有测试文件都能直接用，不需要 import。"""

import pytest


@pytest.fixture
def config_dict():
    """一份合法的配置。每个用到它的测试都会拿到一个新的 dict，互不影响。"""
    return {"model": "qwen-plus", "temperature": 0.3, "provider": "openai"}
