"""
FolderColor GUI
Windows folder color customization desktop application.
Features live lighting preview, 16 presets, custom color picker,
instant application, one-click reset, and Windows Explorer context menu integration.
"""

import os
import sys
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import Optional, Tuple
from PIL import Image, ImageTk

import core
import context_menu

# Enable Windows High-DPI scaling awareness for crisp rendering
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class FolderColorApp(tk.Tk):
    def __init__(self, initial_folder: Optional[str] = None):
        super().__init__()

        self.title("Windows Folder Color Customizer - FolderColor")
        self.geometry("820x680")
        self.minsize(780, 640)
        self.configure(bg="#F3F4F6")

        # Try setting window icon
        try:
            ico_app = os.path.join(core.ICONS_DIR, "folder_blue.ico")
            if os.path.exists(ico_app):
                self.iconbitmap(ico_app)
        except Exception:
            pass

        # State variables
        self.base_folder_img = core.get_base_folder_image()
        self.selected_folder_var = tk.StringVar()
        self.selected_color_name = tk.StringVar(value="Red")
        self.selected_hex = tk.StringVar(value="#EB3C3C")
        self.selected_rgb = (235, 60, 60)
        self.selected_ico_path = os.path.join(core.ICONS_DIR, "folder_red.ico")
        self.context_menu_var = tk.BooleanVar(value=context_menu.is_context_menu_installed())
        self.status_var = tk.StringVar(value="Ready. Select a folder and a color to apply.")

        # Pre-load preset thumbnails for palette buttons
        self.preset_thumbs = {}
        self._load_preset_thumbnails()

        # Initial folder selection
        if initial_folder and os.path.isdir(initial_folder):
            self.selected_folder_var.set(os.path.abspath(initial_folder))
        else:
            self.selected_folder_var.set(core.BASE_DIR)

        # Build UI
        self._setup_styles()
        self._build_ui()
        self._update_preview()
        self._check_current_folder_status()

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure("TFrame", background="#F3F4F6")
        self.style.configure("Card.TFrame", background="#FFFFFF", relief="flat")
        self.style.configure(
            "Header.TLabel",
            background="#FFFFFF",
            foreground="#1F2937",
            font=("Segoe UI", 13, "bold"),
        )
        self.style.configure(
            "SubHeader.TLabel",
            background="#FFFFFF",
            foreground="#4B5563",
            font=("Segoe UI", 9),
        )
        self.style.configure(
            "Status.TLabel",
            background="#F3F4F6",
            foreground="#4B5563",
            font=("Segoe UI", 9),
        )

    def _load_preset_thumbnails(self):
        """Generate 22x22 thumbnails for palette buttons."""
        for item in core.COLOR_PRESETS:
            ico_file = os.path.join(core.ICONS_DIR, f"{item['key']}.ico")
            if os.path.exists(ico_file):
                try:
                    img = Image.open(ico_file).resize((22, 22), Image.Resampling.LANCZOS)
                    self.preset_thumbs[item["key"]] = ImageTk.PhotoImage(img)
                    continue
                except Exception:
                    pass
            # Fallback: dynamic recolor
            colored = core.recolor_folder(self.base_folder_img, item["rgb"])
            thumb = colored.resize((22, 22), Image.Resampling.LANCZOS)
            self.preset_thumbs[item["key"]] = ImageTk.PhotoImage(thumb)

    def _build_ui(self):
        # Main layout container
        container = tk.Frame(self, bg="#F3F4F6", padx=16, pady=12)
        container.pack(fill="both", expand=True)

        # === Top: Folder selection card ===
        folder_card = tk.Frame(container, bg="#FFFFFF", padx=16, pady=12, highlightthickness=1, highlightbackground="#E5E7EB")
        folder_card.pack(fill="x", pady=(0, 10))

        tk.Label(
            folder_card,
            text="Target Folder",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1F2937",
        ).pack(anchor="w")

        f_row = tk.Frame(folder_card, bg="#FFFFFF")
        f_row.pack(fill="x", pady=(6, 4))

        self.folder_entry = tk.Entry(
            f_row,
            textvariable=self.selected_folder_var,
            font=("Segoe UI", 9),
            bg="#F9FAFB",
            relief="solid",
            bd=1,
            fg="#111827",
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)
        self.folder_entry.bind("<KeyRelease>", lambda e: self._check_current_folder_status())

        btn_browse = tk.Button(
            f_row,
            text="Browse...",
            command=self._on_browse_folder,
            bg="#E5E7EB",
            fg="#1F2937",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            font=("Segoe UI", 9),
        )
        btn_browse.pack(side="right", padx=(0, 0))

        btn_curr = tk.Button(
            f_row,
            text="Current Directory",
            command=self._on_set_current_workspace,
            bg="#E5E7EB",
            fg="#1F2937",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            font=("Segoe UI", 9),
        )
        btn_curr.pack(side="right", padx=(0, 6))

        # Folder status info line
        self.folder_status_lbl = tk.Label(
            folder_card,
            text="Status: Detecting...",
            font=("Segoe UI", 8),
            bg="#FFFFFF",
            fg="#6B7280",
        )
        self.folder_status_lbl.pack(anchor="w")

        # === Middle section: Palette (left) + Preview & Action (right) ===
        mid_row = tk.Frame(container, bg="#F3F4F6")
        mid_row.pack(fill="both", expand=True, pady=(0, 10))

        # Left: Palette card
        palette_card = tk.Frame(mid_row, bg="#FFFFFF", padx=16, pady=12, highlightthickness=1, highlightbackground="#E5E7EB")
        palette_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(
            palette_card,
            text="Color Palette",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1F2937",
        ).pack(anchor="w", pady=(0, 8))

        # 4x4 Color grid
        grid_frame = tk.Frame(palette_card, bg="#FFFFFF")
        grid_frame.pack(fill="both", expand=True)

        for i in range(4):
            grid_frame.columnconfigure(i, weight=1)

        for idx, item in enumerate(core.COLOR_PRESETS):
            row = idx // 4
            col = idx % 4

            thumb = self.preset_thumbs.get(item["key"])
            btn = tk.Button(
                grid_frame,
                text=f" {item['name']}",
                image=thumb,
                compound="left",
                command=lambda p=item: self._select_preset_color(p),
                bg="#F9FAFB",
                fg="#374151",
                activebackground="#E5E7EB",
                relief="solid",
                bd=1,
                padx=4,
                pady=6,
                font=("Segoe UI", 8),
                cursor="hand2",
                anchor="w",
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)

        # Custom color row
        custom_row = tk.Frame(palette_card, bg="#FFFFFF")
        custom_row.pack(fill="x", pady=(10, 0))

        btn_custom = tk.Button(
            custom_row,
            text="Pick Custom Color (RGB / Hex)...",
            command=self._on_choose_custom_color,
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=12,
            pady=6,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        btn_custom.pack(side="left", fill="x", expand=True)

        # Right: Live preview and action card
        preview_card = tk.Frame(mid_row, bg="#FFFFFF", padx=16, pady=12, highlightthickness=1, highlightbackground="#E5E7EB", width=290)
        preview_card.pack(side="right", fill="both", padx=(0, 0))
        preview_card.pack_propagate(False)

        tk.Label(
            preview_card,
            text="Live Preview",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1F2937",
        ).pack(anchor="w")

        # Preview icon display
        self.preview_canvas = tk.Label(
            preview_card,
            bg="#FFFFFF",
            relief="flat",
            height=140,
        )
        self.preview_canvas.pack(fill="x", pady=(8, 4))

        self.color_info_lbl = tk.Label(
            preview_card,
            text="Color: Red (#EB3C3C)",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#111827",
        )
        self.color_info_lbl.pack(anchor="center")

        # Action button frame
        action_frame = tk.Frame(preview_card, bg="#FFFFFF")
        action_frame.pack(fill="x", pady=(12, 0))

        btn_apply = tk.Button(
            action_frame,
            text="Apply Color to Folder",
            command=self._on_apply_color,
            bg="#059669",
            fg="#FFFFFF",
            activebackground="#047857",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            pady=8,
            cursor="hand2",
        )
        btn_apply.pack(fill="x", pady=(0, 6))

        btn_reset = tk.Button(
            action_frame,
            text="Restore Default Yellow",
            command=self._on_reset_folder,
            bg="#F3F4F6",
            fg="#4B5563",
            activebackground="#E5E7EB",
            font=("Segoe UI", 9),
            relief="solid",
            bd=1,
            pady=5,
            cursor="hand2",
        )
        btn_reset.pack(fill="x", pady=(0, 6))

        btn_open_icons = tk.Button(
            action_frame,
            text="Open Icons Folder (.ico / .dll)",
            command=self._on_open_icons_folder,
            bg="#F9FAFB",
            fg="#6B7280",
            activebackground="#E5E7EB",
            font=("Segoe UI", 8),
            relief="flat",
            pady=3,
            cursor="hand2",
        )
        btn_open_icons.pack(fill="x")

        # === Bottom: System integration and status bar ===
        bottom_bar = tk.Frame(container, bg="#FFFFFF", padx=14, pady=8, highlightthickness=1, highlightbackground="#E5E7EB")
        bottom_bar.pack(fill="x")

        chk_menu = tk.Checkbutton(
            bottom_bar,
            text="Add 'Folder Color' cascading menu to Explorer context menu",
            variable=self.context_menu_var,
            command=self._on_toggle_context_menu,
            bg="#FFFFFF",
            fg="#1F2937",
            activebackground="#FFFFFF",
            font=("Segoe UI", 9),
            cursor="hand2",
        )
        chk_menu.pack(side="left")

        btn_rebuild = tk.Button(
            bottom_bar,
            text="Rebuild DLL",
            command=self._on_rebuild_dll,
            bg="#F3F4F6",
            fg="#4B5563",
            relief="flat",
            padx=8,
            pady=2,
            font=("Segoe UI", 8),
            cursor="hand2",
        )
        btn_rebuild.pack(side="right")

        btn_install_perm = tk.Button(
            bottom_bar,
            text="Install to %LocalAppData% (Permanent)",
            command=self._on_install_permanent,
            bg="#EFF6FF",
            fg="#1D4ED8",
            relief="flat",
            padx=8,
            pady=2,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        )
        btn_install_perm.pack(side="right", padx=(0, 6))

        # Bottom status text
        status_lbl = tk.Label(
            container,
            textvariable=self.status_var,
            font=("Segoe UI", 8),
            bg="#F3F4F6",
            fg="#4B5563",
            anchor="w",
        )
        status_lbl.pack(fill="x", pady=(4, 0))

    def _select_preset_color(self, preset: dict):
        self.selected_color_name.set(preset["name"])
        self.selected_hex.set(preset["hex"])
        self.selected_rgb = preset["rgb"]
        self.selected_ico_path = core.get_icon_path(preset["key"])
        self._update_preview()
        self.status_var.set(f"Selected color: {preset['name']} ({preset['hex']})")

    def _on_choose_custom_color(self):
        chosen = colorchooser.askcolor(
            color=self.selected_hex.get(),
            title="Pick Custom Color (RGB / Hex)",
        )
        if chosen and chosen[0] and chosen[1]:
            rgb = tuple(int(c) for c in chosen[0])
            hex_code = chosen[1].upper()
            self.selected_color_name.set(f"Custom ({hex_code})")
            self.selected_hex.set(hex_code)
            self.selected_rgb = rgb

            # Generate and cache custom ico
            custom_name = f"custom_{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}.ico"
            target_dir = core.PERMANENT_ICONS_DIR if os.path.exists(core.PERMANENT_ICONS_DIR) else core.ICONS_DIR
            custom_path = os.path.join(target_dir, custom_name)
            if not os.path.exists(custom_path):
                colored_img = core.recolor_folder(self.base_folder_img, rgb)
                core.save_multisize_ico(colored_img, custom_path)
            self.selected_ico_path = custom_path

            self._update_preview()
            self.status_var.set(f"Selected custom color: {hex_code}")

    def _update_preview(self):
        """Dynamically render preview based on selected color."""
        try:
            colored = core.recolor_folder(self.base_folder_img, self.selected_rgb)
            preview_img = colored.resize((120, 120), Image.Resampling.LANCZOS)
            self.current_preview_photo = ImageTk.PhotoImage(preview_img)
            self.preview_canvas.configure(image=self.current_preview_photo)
            self.color_info_lbl.configure(
                text=f"{self.selected_color_name.get()}  {self.selected_hex.get()}"
            )
        except Exception as e:
            self.status_var.set(f"Preview rendering error: {e}")

    def _check_current_folder_status(self):
        folder = self.selected_folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            self.folder_status_lbl.configure(text="Status: Please select a valid directory", fg="#DC2626")
            return

        icon_info = core.get_current_folder_icon(folder)
        if icon_info:
            icon_file, icon_idx = icon_info
            file_name = os.path.basename(icon_file)
            self.folder_status_lbl.configure(
                text=f"Status: Custom icon active ({file_name}, index {icon_idx})",
                fg="#059669",
            )
        else:
            self.folder_status_lbl.configure(
                text="Status: Windows default yellow folder",
                fg="#4B5563",
            )

    def _on_browse_folder(self):
        initial = self.selected_folder_var.get()
        if not os.path.isdir(initial):
            initial = core.BASE_DIR
        chosen = filedialog.askdirectory(
            title="Select Target Folder to Recolor",
            initialdir=initial,
        )
        if chosen:
            self.selected_folder_var.set(os.path.abspath(chosen))
            self._check_current_folder_status()
            self.status_var.set(f"Selected folder: {chosen}")

    def _on_set_current_workspace(self):
        self.selected_folder_var.set(core.BASE_DIR)
        self._check_current_folder_status()
        self.status_var.set(f"Set to current directory: {core.BASE_DIR}")

    def _on_apply_color(self):
        folder = self.selected_folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Path Error", "Please specify a valid target directory path!")
            return

        # Ensure target ICO exists
        if not os.path.exists(self.selected_ico_path):
            colored_img = core.recolor_folder(self.base_folder_img, self.selected_rgb)
            core.save_multisize_ico(colored_img, self.selected_ico_path)

        try:
            success = core.apply_folder_icon(folder, self.selected_ico_path, 0)
            if success:
                self._check_current_folder_status()
                self.status_var.set(f"Applied color {self.selected_color_name.get()} successfully.")
                messagebox.showinfo(
                    "Applied Successfully",
                    f"Successfully applied custom icon to:\n\n{folder}\n\nWindows Explorer has been notified to refresh immediately.",
                )
            else:
                messagebox.showwarning("Warning", "Windows Shell API returned non-zero code. Check folder permissions.")
        except Exception as e:
            messagebox.showerror("Failed", f"Exception during application:\n{e}")

    def _on_reset_folder(self):
        folder = self.selected_folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Path Error", "Please specify a valid target directory path!")
            return

        try:
            core.reset_folder_icon(folder)
            self._check_current_folder_status()
            self.status_var.set("Restored to default yellow folder.")
            messagebox.showinfo("Restored", f"Successfully restored to Windows default folder icon:\n\n{folder}")
        except Exception as e:
            messagebox.showerror("Failed", f"Exception during reset:\n{e}")

    def _on_open_icons_folder(self):
        if os.path.exists(core.ICONS_DIR):
            os.startfile(core.ICONS_DIR)
        else:
            messagebox.showinfo("Info", "Icons directory does not exist yet.")

    def _on_rebuild_dll(self):
        try:
            core.generate_all_presets()
            self._load_preset_thumbnails()
            self.status_var.set("Rebuilt FolderColors.dll and all multi-size ICO files successfully.")
            messagebox.showinfo("Rebuild Complete", "Icon library and FolderColors.dll have been regenerated.")
        except Exception as e:
            messagebox.showerror("Build Error", f"Error during rebuild:\n{e}")

    def _on_install_permanent(self):
        try:
            dest = core.install_app_to_permanent_location()
            if self.context_menu_var.get():
                context_menu.install_context_menu(dest)
            self.status_var.set(f"Installed app and library to persistent directory: {dest}")
            messagebox.showinfo(
                "Installed to %LocalAppData%",
                f"Successfully installed FolderColor to persistent system location:\n\n"
                f"{dest}\n\n"
                f"Features:\n"
                f"1. Context menu and custom folder icons are now completely decoupled from this repository.\n"
                f"2. You can safely relocate or delete the git repository without breaking folder icons or right-click menus.",
            )
        except Exception as e:
            messagebox.showerror("Installation Failed", f"Error copying to persistent directory:\n{e}")

    def _on_toggle_context_menu(self):
        try:
            if self.context_menu_var.get():
                context_menu.install_context_menu()
                self.status_var.set("Enabled Windows Explorer right-click context menu.")
            else:
                context_menu.uninstall_context_menu()
                self.status_var.set("Disabled Windows Explorer right-click context menu.")
        except Exception as e:
            messagebox.showerror("Context Menu Error", f"Failed to update context menu:\n{e}")
            self.context_menu_var.set(context_menu.is_context_menu_installed())


def main():
    initial_folder = None
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if os.path.isdir(candidate):
            initial_folder = candidate

    app = FolderColorApp(initial_folder)
    app.mainloop()


if __name__ == "__main__":
    main()
