"""演示：fixture、tmp_path、测试 Pydantic 校验错误、caplog 检查日志。"""

import json
import logging

import pytest
from pydantic import ValidationError

from demo_pkg.config import LLMConfig, load_config, save_config


def test_config_defaults(config_dict):
    # config_dict 来自 conftest.py：pytest 按参数名找到同名 fixture，把返回值传进来
    config = LLMConfig.model_validate(config_dict)
    assert config.model == "qwen-plus"
    assert config.max_tokens == 1024  # 没提供，用默认值


def test_config_rejects_bad_temperature(config_dict):
    config_dict["temperature"] = 3  # 改的是本测试自己的 dict，不影响其他测试
    with pytest.raises(ValidationError) as exc_info:
        LLMConfig.model_validate(config_dict)
    # exc_info.value 是捕获到的异常对象
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("temperature",)
    assert errors[0]["type"] == "less_than_equal"


def test_load_config(tmp_path, config_dict):
    # tmp_path 是 pytest 内置 fixture：每个测试一个独立的临时目录（pathlib.Path），测试之间互不干扰
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config_dict), encoding="utf-8")
    assert load_config(path).temperature == 0.3


def test_load_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "不存在.json")


def test_save_then_load(tmp_path):
    original = LLMConfig(model="deepseek-chat", provider="deepseek")
    path = tmp_path / "out.json"
    save_config(original, path)
    assert load_config(path) == original  # BaseModel 的 == 比较的是字段值


def test_high_temperature_warns(tmp_path, caplog):
    # caplog 是内置 fixture，能拿到测试期间记录的日志
    path = tmp_path / "hot.json"
    path.write_text('{"model": "qwen", "temperature": 1.8}', encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        load_config(path)
    assert "偏高" in caplog.text
