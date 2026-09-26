# AGENTS.md - FolderColor Architecture & Engineering Guidelines

This document serves as the primary system context, architecture blueprint, and engineering guide for AI agents and developers working on the **FolderColor** repository.

---

## 1. Project Overview

**FolderColor** is a lightweight, zero-dependency Windows desktop tool and CLI utility designed to customize Windows folder icon colors. It achieves authentic Windows Fluent design fidelity through an HLS lighting preservation algorithm, multi-resolution icon generation, and native Windows Shell integration.

### Core Value Proposition
- **Authentic Visual Quality**: Rather than flat tint overlays, FolderColor decomposes the native Windows 10/11 folder icon into HLS channels to shift hue and saturation while strictly preserving the authentic lighting gradient, edge highlights, backplate shading, and alpha translucency.
- **Native Windows Explorer Experience**: Integrates directly with Windows Explorer via Win32 Shell APIs (`SHGetSetFolderCustomSettings` and `SHChangeNotify`), triggering immediate icon refresh without restarting `explorer.exe` or corrupting shell icon caches.
- **Resource DLL Packaging**: Compiles all color presets into a single native Win32 resource library (`FolderColors.dll`), enabling users to browse colors directly inside the Windows built-in "Change Icon" dialog.
- **Zero Administrator Elevation**: All operations—including Explorer right-click cascading menus and persistent storage—target `HKEY_CURRENT_USER` and `%LOCALAPPDATA%`, requiring zero UAC prompts or administrative privileges.

---

## 2. Technology Stack & Dependencies

- **Runtime**: Python 3.8+ (Windows 10 / 11 64-bit)
- **External Dependencies**:
  - `Pillow` (PIL): Image manipulation, resizing, and ICO multi-resolution container export.
  - `numpy`: Fast vectorized matrix computations for HLS color channel manipulation.
- **Standard Library & System Components**:
  - `ctypes` / `ctypes.wintypes`: Native Win32 API calls (`shell32.dll`, `user32.dll`, `gdi32.dll`, `kernel32.dll`).
  - `winreg`: Registry reading, writing, and recursive deletion for Windows Explorer context menu management.
  - `colorsys`: Bidirectional RGB <-> HLS conversions.
  - `tkinter` & `ttk`: Desktop GUI with per-monitor DPI awareness.
  - `csc.exe` (Microsoft .NET Framework 4.0): Compiles Win32 `.res` icon groups into `FolderColors.dll`.

---

## 3. Project Structure & Module Responsibilities

```
FolderColor/
│
├── core.py                   # Core engine: icon extraction, HLS recoloring, ICO/DLL compilation, Shell APIs
├── gui.py                    # Modern desktop GUI (Tkinter with High-DPI support)
├── cli.py                    # Terminal command-line interface
├── context_menu.py           # Explorer right-click cascading menu registry manager
├── launch_gui.bat            # Silent desktop launcher (runs pythonw.exe)
├── FolderColors.dll          # Pre-compiled Win32 DLL containing 16 icon resources
├── base_folder.png           # 256x256 Windows base folder template cache
├── icons/                    # Directory containing all multi-size .ico files (16px - 256px)
├── README.md                 # Primary English documentation
├── README.zh-TW.md           # Traditional Chinese documentation
├── AGENTS.md                 # Comprehensive AI agent & developer guidelines (this file)
├── LICENSE                   # MIT License
└── .gitignore                # Git ignore configuration
```

### Module Breakdown

#### `core.py`
The engine of the system. Contains all low-level Win32 calls and image processing routines:
- `_hicon_to_image(hIcon, size)`: Copies Windows DIB section from GDI device context into RGBA buffer. Handles GDI object cleanup.
- `get_base_folder_image()`: Retrieves the 256x256 folder icon from `shell32.dll` (index 3) via `PrivateExtractIconsW`. Caches to `base_folder.png`.
- `recolor_folder(base_img, target_rgb)`: Vectorized HLS recoloring. Differentiates between chromatic tones (shifts H and scales S) and achromatic tones (grayscale/black/white where S < 0.05).
- `save_multisize_ico(img, output_path)`: Exports multi-resolution ICO containing 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, and 256x256 bitmaps.
- `build_icon_res(ico_files, output_res_path)`: Generates Win32 binary resource files (`RT_ICON` = 3, `RT_GROUP_ICON` = 14) with proper 4-byte padding and entry offset headers.
- `compile_icon_dll(ico_files, output_dll_path)`: Invokes Windows built-in `csc.exe` with `/win32res` to compile `FolderColors.dll`.
- `install_library_to_permanent_location()`: Copies DLL and icons to `%LOCALAPPDATA%\FolderColor` to prevent broken paths if repo is relocated.
- `apply_folder_icon(folder_path, icon_source_path, icon_index)`: Uses `SHGetSetFolderCustomSettings` with `FCS_FORCEWRITE` and broadcasts `SHCNE_UPDATEITEM` + `SHCNE_ASSOCCHANGED`.
- `reset_folder_icon(folder_path)`: Clears folder settings via Shell API, removes `desktop.ini`, removes `ReadOnly` and `System` folder attributes, and broadcasts refresh notifications.
- `get_current_folder_icon(folder_path)`: Reads active icon path and index via `SHGetSetFolderCustomSettings(..., FCS_READ)`.

#### `gui.py`
Desktop front-end built on Tkinter:
- Sets Windows High-DPI awareness (`SetProcessDpiAwareness`).
- Presents a 4x4 preset palette grid with pre-rendered 22x22 button thumbnails.
- Provides real-time preview of recolored icons using PIL image resizing and `ImageTk.PhotoImage`.
- Integrates native OS color chooser (`colorchooser.askcolor`) with dynamic on-demand ICO generation for custom Hex colors.
- Provides toggle switch for Windows Explorer right-click menu integration.

#### `cli.py`
Command-line interface exposing core functions through subcommands:
- `apply <folder> <color>`: Resolves color (preset name or `#RRGGBB` / `RRGGBB` hex) and applies icon.
- `reset <folder>`: Cleans folder customizations and restores default yellow icon.
- `list`: Displays tabular list of built-in presets and hex codes.
- `build`: Re-runs batch recoloring and rebuilds `FolderColors.dll`.
- `install-lib`: Syncs icon library to `%LOCALAPPDATA%\FolderColor`.
- `install-menu` / `uninstall-menu`: Manages Explorer context menu registry entries.

#### `context_menu.py`
Windows Explorer context menu integration:
- Operates under `HKEY_CURRENT_USER\Software\Classes\Directory\shell\FolderColor` and `...\Directory\Background\shell\FolderColor`.
- Utilizes `ExtendedSubCommandsKey` pointing to itself. *Critical rule: never write an empty `SubCommands` value, which causes Windows 10/11 to search `CommandStore` and renders submenus empty.*
- Launches `cli.py` silently via `pythonw.exe` for seamless background execution.

---

## 4. Key Architectural Contracts & Invariants

1. **HLS Preservation**:
   Never replace HLS conversion with a flat RGB multiply or alpha blend. The luminance curve of the base folder image must be retained to preserve highlights, gradients, and natural drop-shadows.

2. **Windows Shell Invalidation**:
   Whenever `desktop.ini` or folder icon properties are modified or cleared:
   - Always call `SHChangeNotify(SHCNE_UPDATEITEM, SHCNF_PATHW, folder_path, None)`
   - Always call `SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)`
   Failing to broadcast both notifications causes Windows Explorer to show stale cached icons.

3. **GDI & ctypes Memory Safety**:
   When extracting or drawing HICONs in `core.py`:
   - Every `GetDC` must be matched by `ReleaseDC`.
   - Every `CreateCompatibleDC` must be matched by `DeleteDC`.
   - Every `CreateDIBSection` must be unselected and deleted via `DeleteObject`.
   - Every `HICON` extracted via `PrivateExtractIconsW` must be freed with `DestroyIcon`.

4. **Zero-Admin HKCU Scoping**:
   Do NOT attempt to write to `HKEY_CLASSES_ROOT` directly (which requires elevation). Always target `HKEY_CURRENT_USER\Software\Classes`.

5. **Code & Comments Language**:
   All internal codebase elements—variable names, docstrings, inline comments, log output, and CLI argument help—must remain in **English**. User-facing localization (such as Traditional Chinese documentation) is maintained in companion files (`README.zh-TW.md`).

---

## 5. Development & Testing Commands

```cmd
# Check syntax
python -m py_compile core.py cli.py context_menu.py gui.py

# Run CLI help
python cli.py --help

# List color presets
python cli.py list

# Rebuild all presets & compile DLL
python cli.py build

# Launch desktop GUI
python gui.py
```
