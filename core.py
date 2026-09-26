"""
FolderColor Core Engine
Extracts Windows folder icons, performs HLS color transformation,
generates multi-resolution ICO files, compiles resource DLLs, and interfaces
with Windows Shell APIs to apply and reset custom folder icons.
"""

import os
import sys
import struct
import shutil
import ctypes
import subprocess
import colorsys
from ctypes import wintypes
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
from PIL import Image

# Base directory and resource paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
DLL_PATH = os.path.join(BASE_DIR, "FolderColors.dll")
BASE_IMAGE_PATH = os.path.join(BASE_DIR, "base_folder.png")

# Persistent system library path (%LOCALAPPDATA%\FolderColor)
# Used for long-term icon storage so folder icons remain valid even if repository moves
PERMANENT_LIB_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "FolderColor"
)
PERMANENT_DLL_PATH = os.path.join(PERMANENT_LIB_DIR, "FolderColors.dll")
PERMANENT_ICONS_DIR = os.path.join(PERMANENT_LIB_DIR, "icons")

# Default color palette presets (Windows 11 Fluent and common tag colors)
COLOR_PRESETS: List[Dict[str, Any]] = [
    {"key": "folder_red", "name": "Red", "rgb": (235, 60, 60), "hex": "#EB3C3C", "index": 0},
    {"key": "folder_orange", "name": "Orange", "rgb": (245, 130, 32), "hex": "#F58220", "index": 1},
    {"key": "folder_amber", "name": "Amber", "rgb": (255, 175, 20), "hex": "#FFAF14", "index": 2},
    {"key": "folder_yellow", "name": "Yellow", "rgb": (255, 205, 50), "hex": "#FFCD32", "index": 3},
    {"key": "folder_lime", "name": "Lime", "rgb": (140, 215, 40), "hex": "#8CD728", "index": 4},
    {"key": "folder_green", "name": "Green", "rgb": (52, 199, 89), "hex": "#34C759", "index": 5},
    {"key": "folder_mint", "name": "Mint", "rgb": (0, 195, 160), "hex": "#00C3A0", "index": 6},
    {"key": "folder_cyan", "name": "Cyan", "rgb": (30, 180, 230), "hex": "#1EB4E6", "index": 7},
    {"key": "folder_blue", "name": "Blue", "rgb": (0, 122, 255), "hex": "#007AFF", "index": 8},
    {"key": "folder_indigo", "name": "Indigo", "rgb": (88, 86, 214), "hex": "#5856D6", "index": 9},
    {"key": "folder_purple", "name": "Purple", "rgb": (175, 82, 222), "hex": "#AF52DE", "index": 10},
    {"key": "folder_pink", "name": "Pink", "rgb": (255, 45, 115), "hex": "#FF2D73", "index": 11},
    {"key": "folder_brown", "name": "Brown", "rgb": (162, 132, 94), "hex": "#A2845E", "index": 12},
    {"key": "folder_charcoal", "name": "Charcoal", "rgb": (80, 85, 95), "hex": "#50555F", "index": 13},
    {"key": "folder_black", "name": "Black", "rgb": (45, 48, 55), "hex": "#2D3037", "index": 14},
    {"key": "folder_silver", "name": "Silver", "rgb": (185, 190, 200), "hex": "#B9BEC8", "index": 15},
]

# Windows Win32 structures and constants
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]

class SHFOLDERCUSTOMSETTINGS(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwMask", wintypes.DWORD),
        ("pvid", ctypes.c_void_p),
        ("pszWebViewTemplate", wintypes.LPWSTR),
        ("cchWebViewTemplate", wintypes.DWORD),
        ("pszWebViewTemplateVersion", wintypes.LPWSTR),
        ("pszInfoTip", wintypes.LPWSTR),
        ("cchInfoTip", wintypes.DWORD),
        ("pclsid", ctypes.c_void_p),
        ("dwFlags", wintypes.DWORD),
        ("pszIconFile", wintypes.LPWSTR),
        ("cchIconFile", wintypes.DWORD),
        ("iIconIndex", ctypes.c_int),
        ("pszLogo", wintypes.LPWSTR),
        ("cchLogo", wintypes.DWORD),
    ]

FCSM_ICON = 0x00000010
FCS_READ = 0x00000001
FCS_FORCEWRITE = 0x00000002

SHCNE_UPDATEITEM = 0x00002000
SHCNE_ASSOCCHANGED = 0x08000000
SHCNF_PATHW = 0x0005
SHCNF_IDLIST = 0x0000

FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_HIDDEN = 0x00000002
FILE_ATTRIBUTE_SYSTEM = 0x00000004
FILE_ATTRIBUTE_NORMAL = 0x00000080


def _hicon_to_image(hIcon, size: int = 256) -> Image.Image:
    """Convert a Windows HICON handle into a PIL Image with an alpha channel."""
    hdc = ctypes.windll.user32.GetDC(0)
    memdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = size
    bmi.biHeight = -size  # Top-down DIB
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    hbmp = ctypes.windll.gdi32.CreateDIBSection(
        hdc, ctypes.byref(bmi), 0, ctypes.byref(ctypes.c_void_p()), 0, 0
    )
    oldbmp = ctypes.windll.gdi32.SelectObject(memdc, hbmp)
    ctypes.windll.user32.DrawIconEx(memdc, 0, 0, hIcon, size, size, 0, 0, 3)

    buf = (ctypes.c_byte * (size * size * 4))()
    ctypes.windll.gdi32.GetDIBits(
        memdc, hbmp, 0, size, ctypes.byref(buf), ctypes.byref(bmi), 0
    )

    ctypes.windll.gdi32.SelectObject(memdc, oldbmp)
    ctypes.windll.gdi32.DeleteObject(hbmp)
    ctypes.windll.gdi32.DeleteDC(memdc)
    ctypes.windll.user32.ReleaseDC(0, hdc)

    return Image.frombuffer("RGBA", (size, size), buf, "raw", "BGRA", 0, 1)


def get_base_folder_image() -> Image.Image:
    """
    Retrieve the standard Windows folder icon (256x256 high-resolution).
    Attempts extraction from local shell32.dll first; falls back to cached base_folder.png.
    """
    if os.path.exists(BASE_IMAGE_PATH):
        try:
            return Image.open(BASE_IMAGE_PATH).convert("RGBA")
        except Exception:
            pass

    # Extract icon index 3 (standard Windows folder) from shell32.dll
    phicon = (wintypes.HICON * 1)()
    piconid = (wintypes.UINT * 1)()
    res = ctypes.windll.user32.PrivateExtractIconsW(
        r"C:\Windows\System32\shell32.dll", 3, 256, 256, phicon, piconid, 1, 0
    )
    if res > 0 and phicon[0]:
        img = _hicon_to_image(phicon[0], 256)
        ctypes.windll.user32.DestroyIcon(phicon[0])
        try:
            img.save(BASE_IMAGE_PATH)
        except Exception:
            pass
        return img

    raise RuntimeError("Failed to extract default folder icon from Windows shell32.dll")


def recolor_folder(base_img: Image.Image, target_rgb: Tuple[int, int, int]) -> Image.Image:
    """
    Recolor folder icon to target color using HLS color space.
    Preserves lighting gradients, top edge highlights, backplate shading, and alpha shadows.
    """
    tr, tg, tb = [c / 255.0 for c in target_rgb]
    th, tl, ts = colorsys.rgb_to_hls(tr, tg, tb)

    arr = np.array(base_img, dtype=np.float32)
    r = arr[:, :, 0] / 255.0
    g = arr[:, :, 1] / 255.0
    b = arr[:, :, 2] / 255.0
    alpha = arr[:, :, 3]

    flat_r, flat_g, flat_b = r.flatten(), g.flatten(), b.flatten()
    hls = [colorsys.rgb_to_hls(x, y, z) for x, y, z in zip(flat_r, flat_g, flat_b)]
    orig_h = np.array([x[0] for x in hls]).reshape(r.shape)
    orig_l = np.array([x[1] for x in hls]).reshape(r.shape)
    orig_s = np.array([x[2] for x in hls]).reshape(r.shape)

    ref_l, ref_s = 0.74, 0.95

    if ts < 0.05:
        # Monochrome and grayscale handling
        new_h = np.zeros_like(orig_h)
        new_s = np.zeros_like(orig_s)
        l_factor = tl / ref_l
        new_l = np.clip(orig_l * l_factor, 0.0, 1.0)
    else:
        # Color tone handling
        new_h = np.full_like(orig_h, th)
        s_factor = ts / ref_s
        new_s = np.clip(orig_s * s_factor, 0.0, 1.0)
        l_factor = tl / ref_l
        new_l = np.clip(orig_l * l_factor, 0.0, 1.0)

    flat_nh, flat_nl, flat_ns = new_h.flatten(), new_l.flatten(), new_s.flatten()
    new_rgb = [colorsys.hls_to_rgb(x, y, z) for x, y, z in zip(flat_nh, flat_nl, flat_ns)]

    out_arr = np.zeros_like(arr)
    out_arr[:, :, 0] = np.array([x[0] * 255.0 for x in new_rgb]).reshape(r.shape)
    out_arr[:, :, 1] = np.array([x[1] * 255.0 for x in new_rgb]).reshape(r.shape)
    out_arr[:, :, 2] = np.array([x[2] * 255.0 for x in new_rgb]).reshape(r.shape)
    out_arr[:, :, 3] = alpha

    return Image.fromarray(np.uint8(np.clip(out_arr, 0, 255)))


def save_multisize_ico(img: Image.Image, output_path: str):
    """
    Save multi-resolution ICO file adhering to Windows icon specifications.
    Includes 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, and 256x256 dimensions.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(output_path, format="ICO", sizes=sizes)


def build_icon_res(ico_files: List[Tuple[int, str]], output_res_path: str):
    """
    Pack multiple multi-size ICO files into a Win32 binary .res resource file.
    """
    res_data = bytearray()
    # Root null header (32 bytes)
    res_data += struct.pack("<IIHHHH IHHII", 0, 32, 0xFFFF, 0x0000, 0xFFFF, 0x0000, 0, 0, 0, 0, 0)

    def _add_resource(res_type, res_name, data):
        while len(res_data) % 4 != 0:
            res_data.append(0)
        header = struct.pack(
            "<IIHHHH IHHII",
            len(data),
            32,
            0xFFFF,
            res_type,
            0xFFFF,
            res_name,
            0,
            0x1030,
            0,
            0,
            0,
        )
        res_data.extend(header)
        res_data.extend(data)
        while len(res_data) % 4 != 0:
            res_data.append(0)

    RT_ICON = 3
    RT_GROUP_ICON = 14
    current_icon_id = 1

    for group_id, ico_path in ico_files:
        with open(ico_path, "rb") as f:
            ico_bytes = f.read()
        idReserved, idType, idCount = struct.unpack("<HHH", ico_bytes[:6])
        entries = []
        offset = 6
        for _ in range(idCount):
            w, h, c, r, planes, bpp, bytes_in_res, img_offset = struct.unpack(
                "<BBBBHHII", ico_bytes[offset : offset + 16]
            )
            entries.append((w, h, c, r, planes, bpp, bytes_in_res, img_offset))
            offset += 16
        grp_data = bytearray(struct.pack("<HHH", idReserved, idType, idCount))
        for entry in entries:
            w, h, c, r, planes, bpp, bytes_in_res, img_offset = entry
            icon_id = current_icon_id
            current_icon_id += 1
            icon_data = ico_bytes[img_offset : img_offset + bytes_in_res]
            _add_resource(RT_ICON, icon_id, icon_data)
            grp_data.extend(
                struct.pack("<BBBBHHIH", w, h, c, r, planes, bpp, bytes_in_res, icon_id)
            )
        _add_resource(RT_GROUP_ICON, group_id, grp_data)

    with open(output_res_path, "wb") as f:
        f.write(res_data)


def compile_icon_dll(ico_files: List[Tuple[int, str]], output_dll_path: str) -> bool:
    """
    Compile resource file into FolderColors.dll containing all icon presets via Windows built-in csc.exe.
    Allows listing all color variants in the native Windows 'Change Icon' dialog like SHELL32.dll.
    """
    csc_candidates = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
    ]
    csc_path = next((p for p in csc_candidates if os.path.exists(p)), None)
    if not csc_path:
        return False

    temp_res = os.path.join(BASE_DIR, "_temp_icons.res")
    temp_cs = os.path.join(BASE_DIR, "_temp_dummy.cs")
    try:
        build_icon_res(ico_files, temp_res)
        with open(temp_cs, "w", encoding="utf-8") as f:
            f.write("class FolderIconsLib {}")

        cmd = [
            csc_path,
            "/nologo",
            "/target:library",
            f"/win32res:{temp_res}",
            f"/out:{output_dll_path}",
            temp_cs,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0 and os.path.exists(output_dll_path)
    finally:
        if os.path.exists(temp_res):
            try: os.remove(temp_res)
            except Exception: pass
        if os.path.exists(temp_cs):
            try: os.remove(temp_cs)
            except Exception: pass


def generate_all_presets():
    """
    Batch generate all preset ICO files and recompile FolderColors.dll.
    """
    os.makedirs(ICONS_DIR, exist_ok=True)
    base_img = get_base_folder_image()

    ico_list = []
    for item in COLOR_PRESETS:
        ico_path = os.path.join(ICONS_DIR, f"{item['key']}.ico")
        colored_img = recolor_folder(base_img, item["rgb"])
        save_multisize_ico(colored_img, ico_path)
        ico_list.append((item["index"] + 1, ico_path))

    compile_icon_dll(ico_list, DLL_PATH)


def get_icon_path(key: str) -> str:
    """
    Get icon path, preferring persistent %LOCALAPPDATA% directory if available,
    otherwise falling back to repository ICONS_DIR.
    """
    perm_path = os.path.join(PERMANENT_ICONS_DIR, f"{key}.ico")
    if os.path.exists(perm_path):
        return perm_path
    return os.path.join(ICONS_DIR, f"{key}.ico")


def get_dll_path() -> str:
    """
    Get FolderColors.dll path, preferring persistent %LOCALAPPDATA% directory if available,
    otherwise falling back to repository DLL_PATH.
    """
    if os.path.exists(PERMANENT_DLL_PATH):
        return PERMANENT_DLL_PATH
    return DLL_PATH


def install_app_to_permanent_location() -> str:
    """
    Install the complete FolderColor application and icon library to Windows user local app data
    (%LOCALAPPDATA%\\FolderColor).
    This decouples system integration (context menu, customized folders) from the source repository location.
    """
    os.makedirs(PERMANENT_LIB_DIR, exist_ok=True)
    os.makedirs(PERMANENT_ICONS_DIR, exist_ok=True)

    # Ensure local DLL exists
    if not os.path.exists(DLL_PATH):
        generate_all_presets()

    # Core scripts and assets to copy
    app_files = [
        "core.py",
        "cli.py",
        "gui.py",
        "context_menu.py",
        "base_folder.png",
        "FolderColors.dll",
    ]
    for fname in app_files:
        src_path = os.path.join(BASE_DIR, fname)
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(PERMANENT_LIB_DIR, fname))

    # Copy icons directory
    if os.path.exists(ICONS_DIR):
        for fname in os.listdir(ICONS_DIR):
            src_file = os.path.join(ICONS_DIR, fname)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, os.path.join(PERMANENT_ICONS_DIR, fname))

    return PERMANENT_LIB_DIR


def install_library_to_permanent_location() -> str:
    """
    Backward-compatible alias for install_app_to_permanent_location.
    """
    return install_app_to_permanent_location()


def apply_folder_icon(folder_path: str, icon_source_path: str, icon_index: int = 0) -> bool:
    """
    Apply icon to target folder using Windows Shell API (SHGetSetFolderCustomSettings)
    and broadcast change notifications to refresh Windows Explorer immediately.
    """
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        raise ValueError(f"Target directory does not exist: {folder_path}")

    icon_source_path = os.path.abspath(icon_source_path)
    if not os.path.exists(icon_source_path):
        raise ValueError(f"Target icon file does not exist: {icon_source_path}")

    fcs = SHFOLDERCUSTOMSETTINGS()
    fcs.dwSize = ctypes.sizeof(SHFOLDERCUSTOMSETTINGS)
    fcs.dwMask = FCSM_ICON
    fcs.pszIconFile = icon_source_path
    fcs.cchIconFile = 0
    fcs.iIconIndex = icon_index

    hr = ctypes.windll.shell32.SHGetSetFolderCustomSettings(
        ctypes.byref(fcs), folder_path, FCS_FORCEWRITE
    )

    # Notify Windows Explorer to refresh
    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEITEM, SHCNF_PATHW, folder_path, None)
    ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)

    return (hr & 0xFFFFFFFF) == 0


def reset_folder_icon(folder_path: str) -> bool:
    """
    Clear custom icon settings on target folder and restore default Windows yellow folder.
    """
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        raise ValueError(f"Target directory does not exist: {folder_path}")

    # 1. Write empty settings via Shell API to flush shell memory cache
    try:
        fcs = SHFOLDERCUSTOMSETTINGS()
        fcs.dwSize = ctypes.sizeof(SHFOLDERCUSTOMSETTINGS)
        fcs.dwMask = FCSM_ICON
        fcs.pszIconFile = ""
        fcs.cchIconFile = 0
        fcs.iIconIndex = 0
        ctypes.windll.shell32.SHGetSetFolderCustomSettings(
            ctypes.byref(fcs), folder_path, FCS_FORCEWRITE
        )
    except Exception:
        pass

    # 2. Remove desktop.ini file
    ini_path = os.path.join(folder_path, "desktop.ini")
    if os.path.exists(ini_path):
        try:
            ctypes.windll.kernel32.SetFileAttributesW(ini_path, FILE_ATTRIBUTE_NORMAL)
            os.remove(ini_path)
        except Exception:
            pass

    # 3. Clear ReadOnly and System folder attribute flags
    attrs = ctypes.windll.kernel32.GetFileAttributesW(folder_path)
    if attrs != -1 and (attrs & (FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_SYSTEM)):
        ctypes.windll.kernel32.SetFileAttributesW(
            folder_path, attrs & ~(FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_SYSTEM)
        )

    # 4. Notify Windows Explorer to refresh
    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEITEM, SHCNF_PATHW, folder_path, None)
    ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)

    return True


def get_current_folder_icon(folder_path: str) -> Optional[Tuple[str, int]]:
    """
    Retrieve custom icon path and index configured in target folder.
    Returns None if not set or if desktop.ini does not exist.
    """
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        return None

    ini_path = os.path.join(folder_path, "desktop.ini")
    if not os.path.isfile(ini_path):
        return None

    fcs = SHFOLDERCUSTOMSETTINGS()
    fcs.dwSize = ctypes.sizeof(SHFOLDERCUSTOMSETTINGS)
    fcs.dwMask = FCSM_ICON
    buf = ctypes.create_unicode_buffer(512)
    fcs.pszIconFile = ctypes.cast(buf, wintypes.LPWSTR)
    fcs.cchIconFile = 512

    hr = ctypes.windll.shell32.SHGetSetFolderCustomSettings(
        ctypes.byref(fcs), folder_path, FCS_READ
    )
    if (hr & 0xFFFFFFFF) == 0 and buf.value:
        return (buf.value, fcs.iIconIndex)
    return None
