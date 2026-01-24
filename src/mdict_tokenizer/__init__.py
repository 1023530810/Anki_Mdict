"""MDict 分词-辞典插件入口"""

from __future__ import annotations

from typing import Optional

try:
    from aqt import mw, gui_hooks
    from aqt.qt import QAction, QMenu
    from aqt.utils import showInfo, showWarning
except Exception:  # pragma: no cover - 在非 Anki 环境下跳过
    mw = None
    gui_hooks = None
    QAction = None
    QMenu = None
    showInfo = None
    showWarning = None

from .config import ensure_config, get_media_dir_from_mw


def on_profile_loaded() -> None:
    """配置加载后初始化"""
    if mw is None:
        return
    media_dir = get_media_dir_from_mw(mw)
    ensure_config(media_dir)


def show_dict_manager_dialog() -> None:
    """显示辞典管理对话框"""
    if mw is None:
        return
    from .ui.dict_manager_dialog import DictManagerDialog

    dialog = DictManagerDialog(mw)
    dialog.exec()


def show_tokenizer_config_dialog() -> None:
    """显示分词配置对话框"""
    if mw is None:
        return
    from .ui.tokenizer_config_dialog import TokenizerConfigDialog

    dialog = TokenizerConfigDialog(mw)
    dialog.exec()


def show_template_inject_dialog() -> None:
    """显示模板注入对话框"""
    if mw is None:
        return
    from .ui.template_inject_dialog import TemplateInjectDialog

    dialog = TemplateInjectDialog(mw)
    dialog.exec()


def check_environment() -> None:
    """检查运行环境"""
    if mw is None or showInfo is None or showWarning is None:
        return
    from .mdx_processor import check_mdx_dependencies

    available, info = check_mdx_dependencies()
    if available:
        showInfo(f"✅ MDX 依赖可用\n{info}")
    else:
        showWarning(f"❌ MDX 依赖不可用\n{info}")


def setup_menu() -> None:
    """设置菜单"""
    if mw is None or QMenu is None or QAction is None:
        return

    menu = QMenu("MDict", mw)

    dict_action = QAction("辞典管理...", mw)
    dict_action.triggered.connect(show_dict_manager_dialog)
    menu.addAction(dict_action)

    tokenizer_action = QAction("分词配置...", mw)
    tokenizer_action.triggered.connect(show_tokenizer_config_dialog)
    menu.addAction(tokenizer_action)

    template_action = QAction("模板注入...", mw)
    template_action.triggered.connect(show_template_inject_dialog)
    menu.addAction(template_action)

    menu.addSeparator()

    check_action = QAction("检查环境", mw)
    check_action.triggered.connect(check_environment)
    menu.addAction(check_action)

    mw.form.menuTools.addMenu(menu)


if gui_hooks is not None:
    gui_hooks.profile_did_open.append(on_profile_loaded)
    gui_hooks.main_window_did_init.append(setup_menu)
