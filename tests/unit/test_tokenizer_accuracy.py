"""分词准确率测试（占位）。

当前单元测试环境无法直接运行前端分词器（kuromoji/compromise）和词表。
需要在浏览器或具备 JS 运行环境的测试框架中执行准确率评估。
"""

from __future__ import annotations

import pytest


pytest.skip(
    "需要浏览器/JS 环境与 JLPT/COCA 词表资源，当前单元测试无法执行。",
    allow_module_level=True,
)
