# Windows 資料夾色彩自訂工具 (FolderColor)

[English](./README.md) | [繁體中文](./README.zh-TW.md)

一套專為 Windows 設計的資料夾色彩自訂與管理工具。透過提取 Windows 原生高解析度資料夾圖示，並採用立體光影 HLS 保真演算法，為資料夾換上紅、橘、綠、藍、紫等各式色彩，同時保有 Windows 官方圖示的細緻光影漸層、高光邊條與柔和陰影。

<p align="center">
  <img src="./assets/app_screenshot.png" alt="FolderColor 桌面操作介面" width="720">
</p>

---

## 支援的四種使用方式

### 方式 1：直覺桌面 GUI 介面（推薦）
雙擊本目錄下的 **`launch_gui.bat`**（或執行 `python gui.py`）：
1. 點擊「Browse...」選取目標資料夾（或貼上路徑）。
2. 在色彩調色盤中點選喜歡的顏色（或點擊「Pick Custom Color」選取任意 RGB / Hex 色碼）。
3. 右側即時預覽圖示效果。
4. 點擊「**Apply Color to Folder**」，Windows 檔案總管立即同步變更！
5. 如需復原，點擊「**Restore Default Yellow**」即可秒速恢復。

---

### 方式 2：使用 Windows 原生「變更圖示」對話框
如果您習慣使用 Windows 內建的屬性設定面板：
1. 在任何資料夾上點擊滑鼠右鍵 -> **內容 (Properties)**。
2. 切換到 **自訂 (Customize)** 分頁 -> 點擊 **變更圖示 (Change Icon...)**。
3. 在「**在此檔案中尋找圖示 (Look for icons in this file)**」右方點擊 **瀏覽 (Browse...)**：
   - **選項 A（一次載入所有色彩）**：選擇本專案目錄中的 **`FolderColors.dll`**。下方清單會立即像 `SHELL32.dll` 一樣，陳列出整排不同顏色的資料夾圖示供您點選！
   - **選項 B（單一圖示檔）**：進入本專案的 **`icons/`** 目錄，直接挑選對應顏色的 `.ico` 檔案（例如 `folder_red.ico`、`folder_blue.ico` 等）。
4. 點擊 **確定** -> **套用** 即完成更換。

---

### 方式 3：Windows 檔案總管右鍵快顯功能表
在任何資料夾上按右鍵即可直接換色：
- **啟用方式**：在 GUI 介面下方勾選「**Add 'Folder Color' cascading menu to Explorer context menu**」，或於終端機執行：
  ```cmd
  python cli.py install-menu
  ```
- **使用方式**：在檔案總管的任何資料夾上點右鍵 -> **Folder Color** -> 點選顏色即可無聲套用！
- **移除方式**：在 GUI 中取消勾選，或執行：
  ```cmd
  python cli.py uninstall-menu
  ```
  *(註：寫入於目前使用者登錄檔 `HKEY_CURRENT_USER`，完全不需要系統管理員權限)*

---

### 方式 4：CLI 命令列快速操作
適合腳本自動化或進階開發者：
```cmd
# 完整安裝應用與圖示至常駐目錄並註冊右鍵選單 (推薦，徹底解耦專案路徑)
python cli.py install

# 為資料夾套用紅色
python cli.py apply "C:\MyProject" red

# 為資料夾套用自訂 Hex 色碼
python cli.py apply "C:\MyProject" "#9B51E0"

# 還原為系統預設黃色
python cli.py reset "C:\MyProject"

# 列出所有預設色彩代碼與色碼
python cli.py list

# 重新批次產出所有多規格 ICO 與編譯 FolderColors.dll
python cli.py build

# 解除註冊右鍵選單並清理常駐檔案
python cli.py uninstall --purge
```

---

## 移動專案資料夾的影響與推薦存放位置

### 1. 如果移動專案資料夾會受影響嗎？
在尚未執行常駐安裝前**會受到影響**。
Windows 為資料夾套用圖示時，會在目標資料夾內寫入隱藏的 `desktop.ini`，記錄圖示的絕對路徑。若選單直接指向 Git 倉庫目錄，搬移後路徑會失效。

### 2. 官方推薦存放位置：`%LOCALAPPDATA%\FolderColor`（C 碟）
FolderColor 支援一鍵常駐安裝至使用者的本機應用程式目錄：
`C:\Users\<使用者名稱>\AppData\Local\FolderColor`（即環境變數 `%LOCALAPPDATA%\FolderColor`）

**優勢**：
- **徹底解耦**：所有執行腳本、右鍵選單註冊與資料夾圖示設定皆直接錨定於 C 碟 `%LOCALAPPDATA%`，Git 專案就算從 E 碟搬移到其他磁碟、更名甚至刪除，所有右鍵功能與已改色的資料夾圖示依然 100% 正常運作。
- **免管理員權限**：完全鎖定在目前使用者空間，不需要 UAC 系統管理員權限。
- **支援 Windows 環境變數**：在 Windows 原生「變更圖示」視窗中，可直接在檔案路徑輸入 `%LOCALAPPDATA%\FolderColor\FolderColors.dll`。

### 3. 如何一鍵安裝至常駐目錄？
- **CLI 方式**：執行 `python cli.py install`。
- **GUI 方式**：開啟桌面換色介面，點擊視窗右下角 **「Install to %LocalAppData% (Permanent)」**。

---

## 預設色彩清單

本工具內建 16 種調色盤色彩，均包含 16x16、24x24、32x32、48x48、64x64、128x128、256x256 完整高低解析度規格：

| 代碼 | 名稱 | 色彩代表 | 圖示檔案 |
| :--- | :--- | :--- | :--- |
| `red` | Red | `#EB3C3C` | `icons/folder_red.ico` |
| `orange` | Orange | `#F58220` | `icons/folder_orange.ico` |
| `amber` | Amber | `#FFAF14` | `icons/folder_amber.ico` |
| `yellow` | Yellow (Default) | `#FFCD32` | `icons/folder_yellow.ico` |
| `lime` | Lime | `#8CD728` | `icons/folder_lime.ico` |
| `green` | Green | `#34C759` | `icons/folder_green.ico` |
| `mint` | Mint | `#00C3A0` | `icons/folder_mint.ico` |
| `cyan` | Cyan | `#1EB4E6` | `icons/folder_cyan.ico` |
| `blue` | Blue | `#007AFF` | `icons/folder_blue.ico` |
| `indigo` | Indigo | `#5856D6` | `icons/folder_indigo.ico` |
| `purple` | Purple | `#AF52DE` | `icons/folder_purple.ico` |
| `pink` | Pink | `#FF2D73` | `icons/folder_pink.ico` |
| `brown` | Brown | `#A2845E` | `icons/folder_brown.ico` |
| `charcoal`| Charcoal | `#50555F` | `icons/folder_charcoal.ico` |
| `black` | Black | `#2D3037` | `icons/folder_black.ico` |
| `silver` | Silver | `#B9BEC8` | `icons/folder_silver.ico` |

---

## 專案架構說明

```
FolderColor/
│
├── core.py                   # 核心邏輯 (圖示擷取、HLS 光影轉換、ICO/DLL 編譯、Shell API 調用)
├── gui.py                    # 現代化桌面視覺介面 (Tkinter + 支援 High-DPI 螢幕縮放)
├── cli.py                    # 命令列終端操作介面
├── context_menu.py           # Windows 檔案總管右鍵快捷選單管理模組
├── launch_gui.bat            # 雙擊直接啟動 GUI
├── FolderColors.dll          # 包含 16 種圖示資源的 DLL 檔案 (可直接在 Windows 瀏覽對話框載入)
├── base_folder.png           # 256x256 Windows 原生母版圖示快取
├── icons/                    # 存放所有產出的多規格 .ico 檔案 (16~256px)
├── assets/                   # 介面截圖與視覺資源
├── README.md                 # 英文說明文件
└── README.zh-TW.md           # 繁體中文說明文件
```

---

## 底層技術原理

1. **立體光影 HLS 保真重繪**：
   一般的換色程式若直接做色彩疊加，會使反光與陰影失真。本工具將原版 Windows 圖示拆解為 HLS 通道，在置換目標色相與飽和度的同時，依亮度曲線保留了背蓋深淺層次、正面漸層與頂部白色反光線條。
2. **多規格 ICO 規格支援**：
   每個 `.ico` 檔案皆壓製了 7 種尺寸規格（從 16px 至 256px）。無論在檔案總管切換為「超大圖示」、「大圖示」、「中等圖示」或「詳細資料清單」，都不會發生模糊或鋸齒狀失真。
3. **Windows 資源庫 DLL 打包技術**：
   利用 Windows 內建的 .NET 編譯機制，將多個圖示組裝為二進位 `FolderColors.dll`。當在 Windows 原生屬性視窗的「瀏覽...」指向該 DLL 時，Windows 就會如同讀取 `SHELL32.dll` 一般，在選單格點中直接展開所有彩色的資料夾圖示。
4. **Shell API 即時廣播刷新**：
   呼叫 Windows Shell 原生 API `SHGetSetFolderCustomSettings` 與 `SHChangeNotify(SHCNE_UPDATEITEM, ...)`，在配置 `desktop.ini` 與系統唯讀屬性的瞬間通知檔案總管刷新，無須重啟系統或重新啟動檔案總管。
