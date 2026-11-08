"""读取大模型配置文件。演示 Pydantic 校验 + logging。tests/test_config.py 测试这里的代码。"""

import json
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# 惯用写法：每个模块用自己的 logger，名字取模块名（这里是 "demo_pkg.config"）。
# 库代码只负责"记日志"，日志输出到哪里、什么格式，由程序入口统一配置。
logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """大模型调用配置。"""

    model: str = Field(min_length=1, description="模型名，例如 qwen-plus")
    temperature: float = Field(default=0.7, ge=0, le=2, description="采样温度")
    max_tokens: int = Field(default=1024, gt=0, description="最多生成多少 token")
    provider: Literal["openai", "deepseek", "ollama"] = "openai"


def load_config(path: str | Path) -> LLMConfig:
    """从 JSON 文件读取配置。
    文件不存在抛 FileNotFoundError，内容不合法抛 pydantic.ValidationError。
    """
    path = Path(path)
    logger.debug("读取配置文件 %s", path)
    config = LLMConfig.model_validate_json(path.read_text(encoding="utf-8"))
    if config.temperature > 1.5:
        logger.warning("temperature=%s 偏高，输出可能不稳定", config.temperature)
    return config


def save_config(config: LLMConfig, path: str | Path) -> None:
    """把配置写回 JSON 文件。"""
    Path(path).write_text(
        json.dumps(config.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
