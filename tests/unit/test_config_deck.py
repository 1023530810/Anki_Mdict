"""测试牌组级配置数据结构"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mdict_tokenizer.config import (
    MainConfig,
    DeckInjection,
    DeckFieldConfig,
    resolve_deck_language,
    _to_dict,
    _from_dict,
)


def test_deck_injection_round_trip() -> None:
    """测试序列化/反序列化往返"""
    config = MainConfig(
        injections=[
            DeckInjection(
                note_type_name="Basic",
                note_type_id=123,
                deck_configs=[
                    DeckFieldConfig(
                        deck_name="日語",
                        fields=[{"name": "Front", "language": "ja"}],
                    )
                ],
                injected_at="2026-01-01",
            )
        ]
    )
    
    # 序列化
    d = _to_dict(config)
    assert "injections" in d
    assert len(d["injections"]) == 1
    assert "deckConfigs" in d["injections"][0]
    
    # 反序列化
    config2 = _from_dict(d)
    assert len(config2.injections) == 1
    assert config2.injections[0].note_type_id == 123
    assert len(config2.injections[0].deck_configs) == 1
    assert config2.injections[0].deck_configs[0].deck_name == "日語"


def test_resolve_deck_language_exact_match() -> None:
    """测试精确匹配牌组名"""
    injections = [
        DeckInjection(
            note_type_name="Basic",
            note_type_id=123,
            deck_configs=[
                DeckFieldConfig(
                    deck_name="日語",
                    fields=[{"name": "Front", "language": "ja"}],
                )
            ],
            injected_at="2026-01-01",
        )
    ]
    
    assert resolve_deck_language(injections, 123, "日語", "Front") == "ja"


def test_resolve_deck_language_child_inherits() -> None:
    """测试子牌组继承父牌组配置"""
    injections = [
        DeckInjection(
            note_type_name="Basic",
            note_type_id=123,
            deck_configs=[
                DeckFieldConfig(
                    deck_name="日語",
                    fields=[{"name": "Front", "language": "ja"}],
                )
            ],
            injected_at="2026-01-01",
        )
    ]
    
    # 子牌组继承
    assert resolve_deck_language(injections, 123, "日語::N1", "Front") == "ja"
    assert resolve_deck_language(injections, 123, "日語::N1::词汇", "Front") == "ja"


def test_resolve_deck_language_no_match() -> None:
    """测试未配置牌组返回 None"""
    injections = [
        DeckInjection(
            note_type_name="Basic",
            note_type_id=123,
            deck_configs=[
                DeckFieldConfig(
                    deck_name="日語",
                    fields=[{"name": "Front", "language": "ja"}],
                )
            ],
            injected_at="2026-01-01",
        )
    ]
    
    # 未配置牌组
    assert resolve_deck_language(injections, 123, "英語", "Front") is None
    # 未配置字段
    assert resolve_deck_language(injections, 123, "日語", "Back") is None
    # 未配置笔记类型
    assert resolve_deck_language(injections, 999, "日語", "Front") is None


def test_resolve_deck_language_deep_nesting() -> None:
    """测试多级子牌组继承"""
    injections = [
        DeckInjection(
            note_type_name="Basic",
            note_type_id=123,
            deck_configs=[
                DeckFieldConfig(
                    deck_name="语言学习",
                    fields=[{"name": "Front", "language": "en"}],
                )
            ],
            injected_at="2026-01-01",
        )
    ]
    
    # 多级继承
    assert resolve_deck_language(injections, 123, "语言学习::日语", "Front") == "en"
    assert resolve_deck_language(injections, 123, "语言学习::日语::N1", "Front") == "en"
    assert resolve_deck_language(injections, 123, "语言学习::日语::N1::词汇", "Front") == "en"
