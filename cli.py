"""
FolderColor CLI
Command-line interface for folder recoloring, icon resetting, library compilation,
and Explorer context menu management.
"""

import os
import sys
import argparse
import re
from typing import Optional, Tuple

import core
import context_menu

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def parse_hex_color(hex_str: str) -> Optional[Tuple[int, int, int]]:
    """Parse #RRGGBB or RRGGBB hexadecimal color value."""
    hex_clean = hex_str.strip().lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{6}", hex_clean):
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        return (r, g, b)
    return None


def resolve_color_to_ico(color_input: str) -> Tuple[str, int]:
    """
    Resolve user color input (preset name or hex code) to ICO file path and icon index.
    Returns (ico_path, icon_index).
    """
    # 1. Match against existing presets
    key_norm = color_input.lower().replace(" ", "_")
    for item in core.COLOR_PRESETS:
        if (
            key_norm == item["key"]
            or key_norm == item["key"].replace("folder_", "")
            or key_norm in item["name"].lower()
        ):
            ico_path = os.path.join(core.ICONS_DIR, f"{item['key']}.ico")
            if not os.path.exists(ico_path):
                core.generate_all_presets()
            return (ico_path, 0)

    # 2. Match against custom Hex code
    rgb = parse_hex_color(color_input)
    if rgb:
        custom_name = f"custom_{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}.ico"
        custom_path = os.path.join(core.ICONS_DIR, custom_name)
        if not os.path.exists(custom_path):
            base_img = core.get_base_folder_image()
            colored_img = core.recolor_folder(base_img, rgb)
            core.save_multisize_ico(colored_img, custom_path)
        return (custom_path, 0)

    raise ValueError(
        f"Unrecognized color name or hex code: '{color_input}'. Please use a preset name or #RRGGBB code."
    )


def cmd_apply(args):
    folder_path = os.path.abspath(args.folder)
    if not os.path.isdir(folder_path):
        print(f"Error: Directory not found: '{folder_path}'")
        sys.exit(1)

    try:
        ico_path, icon_index = resolve_color_to_ico(args.color)
        success = core.apply_folder_icon(folder_path, ico_path, icon_index)
        if success:
            print(f"Successfully applied folder color: {folder_path}")
            print(f"Icon source: {ico_path}")
        else:
            print("Failed to apply: Windows Shell rejected the change.")
            sys.exit(1)
    except Exception as e:
        print(f"Error occurred during execution: {e}")
        sys.exit(1)


def cmd_reset(args):
    folder_path = os.path.abspath(args.folder)
    if not os.path.isdir(folder_path):
        print(f"Error: Directory not found: '{folder_path}'")
        sys.exit(1)

    try:
        core.reset_folder_icon(folder_path)
        print(f"Successfully restored Windows default yellow icon: {folder_path}")
    except Exception as e:
        print(f"Error occurred during reset: {e}")
        sys.exit(1)


def cmd_list(args):
    print("=== Available Preset Colors ===")
    print(f"{'Key':<15} {'Color Name':<20} {'Hex Code':<10} {'Icon File'}")
    print("-" * 65)
    for p in core.COLOR_PRESETS:
        short_key = p["key"].replace("folder_", "")
        ico_name = f"{p['key']}.ico"
        print(f"{short_key:<15} {p['name']:<20} {p['hex']:<10} {ico_name}")
    print("\nTip: You can also specify any custom Hex color directly (e.g. '#FF0055' or '00A86B').")


def cmd_build(args):
    print("Generating all preset icons and compiling FolderColors.dll...")
    core.generate_all_presets()
    print("Build complete! All icons generated in 'icons/' and 'FolderColors.dll' updated.")


def cmd_install_menu(args):
    context_menu.install_context_menu()
    print("Successfully registered Windows Explorer right-click context menu!")


def cmd_uninstall_menu(args):
    context_menu.uninstall_context_menu()
    print("Successfully unregistered Windows Explorer right-click context menu!")


def cmd_install_lib(args):
    dest = core.install_library_to_permanent_location()
    print(f"Successfully installed FolderColors.dll and icon library to persistent location:")
    print(f"Path: {dest}")
    print("Folder icons will remain valid even if the repository source is moved or removed.")


def main():
    parser = argparse.ArgumentParser(
        description="Windows Folder Color Customization Tool (FolderColor CLI)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # apply
    parser_apply = subparsers.add_parser("apply", help="Apply custom icon color to specified folder")
    parser_apply.add_argument("folder", help="Target folder path")
    parser_apply.add_argument("color", help="Color preset name (e.g. red, blue, green) or Hex code (#EB3C3C)")
    parser_apply.set_defaults(func=cmd_apply)

    # reset
    parser_reset = subparsers.add_parser("reset", help="Restore folder icon to Windows default")
    parser_reset.add_argument("folder", help="Target folder path")
    parser_reset.set_defaults(func=cmd_reset)

    # list
    parser_list = subparsers.add_parser("list", help="List all available preset colors")
    parser_list.set_defaults(func=cmd_list)

    # build
    parser_build = subparsers.add_parser("build", help="Batch generate all ICO files and compile FolderColors.dll")
    parser_build.set_defaults(func=cmd_build)

    # install-lib
    parser_lib = subparsers.add_parser("install-lib", help="Install library to %%LOCALAPPDATA%% permanent path (Recommended)")
    parser_lib.set_defaults(func=cmd_install_lib)

    # install-menu
    parser_inst = subparsers.add_parser("install-menu", help="Add 'Folder Color' cascading menu to Explorer context menu")
    parser_inst.set_defaults(func=cmd_install_menu)

    # uninstall-menu
    parser_uninst = subparsers.add_parser("uninstall-menu", help="Remove 'Folder Color' from Explorer context menu")
    parser_uninst.set_defaults(func=cmd_uninstall_menu)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
