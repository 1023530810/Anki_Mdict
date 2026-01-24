"""全流程集成测试（占位）。

需要在 Anki 桌面环境或可加载 aqt 的测试环境中执行，
涵盖导入辞典、配置分词、模板注入与卡片查词的完整流程。
"""

from __future__ import annotations

import pytest


pytest.skip(
    "需要 Anki/aqt 环境与媒体目录真实交互，当前集成测试暂不执行。",
    allow_module_level=True,
)
