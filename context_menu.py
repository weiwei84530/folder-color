"""
FolderColor Context Menu Manager
Manages Windows Explorer right-click context menu shortcuts (registers to HKEY_CURRENT_USER without admin privileges).
Uses Windows native ExtendedSubCommandsKey mechanism to provide clean cascading submenus.
"""

import os
import sys
import winreg
from typing import List, Tuple, Optional

import core

MENU_PARENT_PATH = r"Software\Classes\Directory\shell\FolderColor"
SUBCOMMANDS_REF = r"Directory\shell\FolderColor"

# Support right-clicking empty space inside a folder
BACKGROUND_PARENT_PATH = r"Software\Classes\Directory\Background\shell\FolderColor"
BACKGROUND_SUBCOMMANDS_REF = r"Directory\Background\shell\FolderColor"


def _get_pythonw_path() -> str:
    """Retrieve pythonw.exe path for silent, non-blocking execution."""
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return sys.executable


def is_context_menu_installed() -> bool:
    """Check if the context menu is currently registered in HKCU."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, MENU_PARENT_PATH, 0, winreg.KEY_READ):
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def _delete_reg_key_recursive(root_key, subkey_path: str):
    """Recursively delete Windows registry keys."""
    try:
        with winreg.OpenKey(root_key, subkey_path, 0, winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    sub_sub = winreg.EnumKey(key, 0)
                    _delete_reg_key_recursive(root_key, f"{subkey_path}\\{sub_sub}")
                except OSError:
                    break
        winreg.DeleteKey(root_key, subkey_path)
    except FileNotFoundError:
        pass


def install_context_menu(target_dir: Optional[str] = None):
    r"""
    Register standard cascading context menu under HKCU:
    - Main key sets ExtendedSubCommandsKey pointing to Directory\shell\FolderColor
    - Avoids empty SubCommands to prevent broken/empty submenus on Windows 10/11
    - Sub-items are placed under Shell\... with MUIVerb, Icon, and command
    - Installs to %LOCALAPPDATA%\FolderColor by default to decouple from repository location
    """
    if target_dir is None:
        target_dir = core.install_app_to_permanent_location()

    pythonw = _get_pythonw_path()
    cli_path = os.path.join(target_dir, "cli.py")
    gui_path = os.path.join(target_dir, "gui.py")
    icons_dir = os.path.join(target_dir, "icons")
    dll_path = os.path.join(target_dir, "FolderColors.dll")

    # Clean previous registry entries first
    uninstall_context_menu()

    # 1. Submenu for right-clicking on a folder (target %1)
    sub_items_folder: List[Tuple[str, str, str, str]] = [
        ("01_red", "Red", os.path.join(icons_dir, "folder_red.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_red'),
        ("02_orange", "Orange", os.path.join(icons_dir, "folder_orange.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_orange'),
        ("03_amber", "Amber", os.path.join(icons_dir, "folder_amber.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_amber'),
        ("04_green", "Green", os.path.join(icons_dir, "folder_green.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_green'),
        ("05_mint", "Mint", os.path.join(icons_dir, "folder_mint.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_mint'),
        ("06_blue", "Blue", os.path.join(icons_dir, "folder_blue.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_blue'),
        ("07_purple", "Purple", os.path.join(icons_dir, "folder_purple.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_purple'),
        ("08_pink", "Pink", os.path.join(icons_dir, "folder_pink.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_pink'),
        ("09_charcoal", "Charcoal", os.path.join(icons_dir, "folder_charcoal.ico"), f'"{pythonw}" "{cli_path}" apply "%1" folder_charcoal'),
        ("10_reset", "Restore Default Yellow", os.path.join(icons_dir, "folder_yellow.ico"), f'"{pythonw}" "{cli_path}" reset "%1"'),
        ("11_custom", "More Colors & Settings...", f"{dll_path},3", f'"{pythonw}" "{gui_path}" "%1"'),
    ]

    _create_cascading_menu(MENU_PARENT_PATH, SUBCOMMANDS_REF, sub_items_folder, dll_path)

    # 2. Submenu for right-clicking inside folder empty background (target %V)
    sub_items_bg: List[Tuple[str, str, str, str]] = [
        ("01_red", "Red", os.path.join(icons_dir, "folder_red.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_red'),
        ("02_orange", "Orange", os.path.join(icons_dir, "folder_orange.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_orange'),
        ("03_amber", "Amber", os.path.join(icons_dir, "folder_amber.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_amber'),
        ("04_green", "Green", os.path.join(icons_dir, "folder_green.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_green'),
        ("05_mint", "Mint", os.path.join(icons_dir, "folder_mint.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_mint'),
        ("06_blue", "Blue", os.path.join(icons_dir, "folder_blue.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_blue'),
        ("07_purple", "Purple", os.path.join(icons_dir, "folder_purple.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_purple'),
        ("08_pink", "Pink", os.path.join(icons_dir, "folder_pink.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_pink'),
        ("09_charcoal", "Charcoal", os.path.join(icons_dir, "folder_charcoal.ico"), f'"{pythonw}" "{cli_path}" apply "%V" folder_charcoal'),
        ("10_reset", "Restore Default Yellow", os.path.join(icons_dir, "folder_yellow.ico"), f'"{pythonw}" "{cli_path}" reset "%V"'),
        ("11_custom", "More Colors & Settings...", f"{dll_path},3", f'"{pythonw}" "{gui_path}" "%V"'),
    ]

    _create_cascading_menu(BACKGROUND_PARENT_PATH, BACKGROUND_SUBCOMMANDS_REF, sub_items_bg, dll_path)


def _create_cascading_menu(parent_path: str, subcommands_ref: str, items: List[Tuple[str, str, str, str]], dll_path: str):
    """Create cascading submenu structure following Windows Shell specifications."""
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, parent_path) as main_key:
        winreg.SetValueEx(main_key, "MUIVerb", 0, winreg.REG_SZ, "Folder Color")
        winreg.SetValueEx(main_key, "Icon", 0, winreg.REG_SZ, f"{dll_path},0")
        winreg.SetValueEx(main_key, "ExtendedSubCommandsKey", 0, winreg.REG_SZ, subcommands_ref)

    shell_sub_path = f"{parent_path}\\Shell"
    for key_id, title, icon, cmd in items:
        item_path = f"{shell_sub_path}\\{key_id}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, item_path) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, title)
            winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, title)
            winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon)

        cmd_path = f"{item_path}\\command"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_path) as ck:
            winreg.SetValueEx(ck, "", 0, winreg.REG_SZ, cmd)


def uninstall_context_menu():
    """
    Remove Windows Explorer context menu registry entries from HKCU.
    """
    _delete_reg_key_recursive(winreg.HKEY_CURRENT_USER, MENU_PARENT_PATH)
    _delete_reg_key_recursive(winreg.HKEY_CURRENT_USER, BACKGROUND_PARENT_PATH)
    _delete_reg_key_recursive(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\ContextMenus\FolderColor")
