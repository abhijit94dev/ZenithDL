import customtkinter as ctk
from yt_dlp import YoutubeDL
import threading
import os
import re
import webbrowser
import json
import sys
import subprocess
import datetime
import winsound
import requests  # আপডেটের জন্য এটি নতুন
from PIL import Image

# --- ১. অ্যাপ কনফিগারেশন ---
APP_NAME = "ZenithDL"
CURRENT_VERSION = "v1.0"  # গিটহাবে যখন নতুন ভার্সন দেবেন, তখন এটি v1.1 করবেন
GITHUB_REPO = "abhijit94dev/ZenithDL"  # আপনার গিটহাব রিপোজিটরি

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")
QR_IMAGE_PATH = os.path.join(BASE_DIR, "bitcoin_qr.png")
CONFIG_FILE = os.path.join(BASE_DIR, "settings.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.txt")

# --- কালার প্যালেট ---
COLORS = {
    "bg": "#1e272e", "sidebar": "#2f3640", "accent": "#0984e3",
    "success": "#00b894", "danger": "#d63031", "warning": "#e17055",
    "neutral": "#636e72", "text": "#dfe6e9"
}

ALL_QUALITIES = ["Best Video (Auto)", "8K (4320p)", "4K (2160p)", "2K (1440p)", "1080p (Full HD)", "720p (HD)", "480p", "360p", "Audio Only (MP3)"]

def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class ZenithDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} | {CURRENT_VERSION} | Ultimate Downloader")
        self.geometry("1150x780")
        self.total_success = 0
        self.is_cancelled = False
        
        # সেটিংস লোড
        self.default_config = {
            "path": os.path.join(BASE_DIR, "downloads"),
            "quality": "Best Video (Auto)", "theme": "Dark",
            "thumbnail": True, "sound": True, "metadata": True, "subtitles": False
        }
        self.settings = self.load_settings()
        
        ctk.set_appearance_mode(self.settings["theme"])
        ctk.set_default_color_theme("dark-blue")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        self.frames = {}
        self.init_pages()
        self.apply_global_settings()
        
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "w") as f: f.write("--- Download History ---\n")

        self.show_frame("single")

        # --- অ্যাপ চালু হওয়ার ৩ সেকেন্ড পর আপডেট চেক করবে ---
        self.after(3000, self.check_for_updates)

    # --- ৩. অটো আপডেট লজিক (NEW) ---
    def check_for_updates(self):
        """গিটহাব থেকে লেটেস্ট রিলিজ চেক করা"""
        def thread_check():
            try:
                api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
                response = requests.get(api_url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    latest_version = data['tag_name'] # e.g., v1.1
                    download_url = data['html_url']

                    # ভার্সন তুলনা করা
                    if latest_version != CURRENT_VERSION:
                        self.after(0, lambda: self.show_update_popup(latest_version, download_url))
            except Exception as e:
                print(f"Update check failed: {e}")

        threading.Thread(target=thread_check, daemon=True).start()

    def show_update_popup(self, version, url):
        """আপডেট পপ-আপ উইন্ডো"""
        update_win = ctk.CTkToplevel(self)
        update_win.title("Update Available! 🚀")
        update_win.geometry("400x250")
        update_win.attributes("-topmost", True)
        
        ctk.CTkLabel(update_win, text="New Version Found!", font=("Arial", 20, "bold"), text_color=COLORS["success"]).pack(pady=(20, 5))
        ctk.CTkLabel(update_win, text=f"Current: {CURRENT_VERSION}  ➜  New: {version}", font=("Arial", 14)).pack(pady=5)
        
        ctk.CTkLabel(update_win, text="A new version with better features is available.", text_color="gray").pack(pady=5)

        ctk.CTkButton(update_win, text="DOWNLOAD UPDATE", height=45, fg_color=COLORS["accent"], 
                      command=lambda: webbrowser.open(url)).pack(pady=20)

    # --- বাকি সব ফাংশন আগের মতোই ---
    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    for key, val in self.default_config.items():
                        if key not in data: data[key] = val
                    return data
            except: return self.default_config
        return self.default_config

    def save_settings(self):
        self.settings["quality"] = self.combo_quality.get()
        self.settings["theme"] = self.combo_theme.get()
        self.settings["thumbnail"] = self.switch_thumb.get()
        self.settings["sound"] = self.switch_sound.get()
        self.settings["metadata"] = self.switch_meta.get()
        self.settings["subtitles"] = self.switch_sub.get()
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(self.settings, f)
            ctk.set_appearance_mode(self.settings["theme"])
            self.apply_global_settings()
            self.lbl_save_status.configure(text="Settings Applied! ✅", text_color=COLORS["success"])
        except Exception as e: self.lbl_save_status.configure(text=f"Error: {e}", text_color="red")

    def apply_global_settings(self):
        q = self.settings["quality"]
        if hasattr(self, 'res_combo_s'): self.res_combo_s.set(q)
        if hasattr(self, 'res_combo_p'): self.res_combo_p.set(q)
        if hasattr(self, 'res_combo_l'): self.res_combo_l.set(q)

    def log_history(self, title):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {title}\n"
        try:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f: f.write(entry)
            if hasattr(self, 'history_box'):
                self.history_box.configure(state="normal"); self.history_box.insert("end", entry); self.history_box.configure(state="disabled"); self.history_box.see("end")
        except: pass

    def load_history_ui(self):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f: return f.read()
        except: return "No history found."
    def clear_history(self):
        with open(HISTORY_FILE, "w") as f: f.write("--- Download History ---\n")
        self.history_box.configure(state="normal"); self.history_box.delete("1.0", "end"); self.history_box.insert("end", "--- Download History ---\n"); self.history_box.configure(state="disabled")

    def update_core(self):
        self.lbl_update_status.configure(text="Updating Core... Please wait", text_color="orange")
        def run_update():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
                self.after(0, lambda: self.lbl_update_status.configure(text="Update Successful! Restart App.", text_color=COLORS["success"]))
            except Exception as e: self.after(0, lambda: self.lbl_update_status.configure(text=f"Update Failed: {e}", text_color="red"))
        threading.Thread(target=run_update, daemon=True).start()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="ZENITH DL", font=("Impact", 35), text_color=COLORS["text"]).pack(pady=(40, 20))
        self.add_nav_btn("Single Video", "single"); self.add_nav_btn("Playlist Mode", "playlist"); self.add_nav_btn("List Downloader", "list"); self.add_nav_btn("📜 History", "history"); self.add_nav_btn("⚙ Settings", "settings")
        self.bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent"); self.bottom_frame.pack(side="bottom", fill="x", pady=20)
        ctk.CTkButton(self.bottom_frame, text="❤ Donate", fg_color=COLORS["warning"], hover_color="#fab1a0", text_color="black", command=self.show_about_dialog).pack(pady=5, padx=20)
        self.count_lbl = ctk.CTkLabel(self.bottom_frame, text=f"Total Success: {self.total_success}", font=("Arial", 12)); self.count_lbl.pack(pady=(10, 0))

    def add_nav_btn(self, text, frame_name):
        btn = ctk.CTkButton(self.sidebar, text=text, height=45, corner_radius=8, fg_color="transparent", border_width=1, border_color="gray", command=lambda: self.show_frame(frame_name))
        btn.pack(pady=10, padx=20, fill="x")

    def init_pages(self):
        f_sets = ctk.CTkFrame(self.main_area, fg_color="transparent")
        ctk.CTkLabel(f_sets, text="Pro Settings", font=("Arial", 28, "bold")).pack(pady=10)
        card = ctk.CTkFrame(f_sets, fg_color=COLORS["sidebar"], corner_radius=15); card.pack(pady=20, padx=20, fill="both", expand=True)
        ctk.CTkLabel(card, text="Download Path:", font=("Arial", 14, "bold")).pack(anchor="w", padx=30, pady=(15, 5))
        path_frame = ctk.CTkFrame(card, fg_color="transparent"); path_frame.pack(fill="x", padx=30)
        self.entry_path = ctk.CTkEntry(path_frame, height=40); self.entry_path.insert(0, self.settings["path"]); self.entry_path.configure(state="readonly"); self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(path_frame, text="Browse", width=80, height=40, fg_color=COLORS["accent"], command=self.select_folder).pack(side="left")
        grid_frame = ctk.CTkFrame(card, fg_color="transparent"); grid_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(grid_frame, text="Default Quality:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_quality = ctk.CTkComboBox(grid_frame, width=200, values=ALL_QUALITIES); self.combo_quality.set(self.settings["quality"]); self.combo_quality.grid(row=1, column=0, sticky="w", padx=(0, 20))
        ctk.CTkLabel(grid_frame, text="Theme:").grid(row=0, column=1, sticky="w", pady=5)
        self.combo_theme = ctk.CTkComboBox(grid_frame, width=200, values=["Dark", "Light", "System"]); self.combo_theme.set(self.settings["theme"]); self.combo_theme.grid(row=1, column=1, sticky="w")
        ctk.CTkLabel(card, text="Advanced Features:", font=("Arial", 14, "bold")).pack(anchor="w", padx=30, pady=(10, 5))
        self.switch_meta = ctk.CTkSwitch(card, text="Embed Metadata (Cover Art)", onvalue=True, offvalue=False, progress_color=COLORS["success"]); 
        if self.settings["metadata"]: self.switch_meta.select()
        self.switch_meta.pack(anchor="w", padx=30, pady=5)
        self.switch_sub = ctk.CTkSwitch(card, text="Download Subtitles (CC)", onvalue=True, offvalue=False, progress_color=COLORS["success"]); 
        if self.settings["subtitles"]: self.switch_sub.select()
        self.switch_sub.pack(anchor="w", padx=30, pady=5)
        self.switch_thumb = ctk.CTkSwitch(card, text="Save Thumbnail Image", onvalue=True, offvalue=False, progress_color=COLORS["success"]); 
        if self.settings["thumbnail"]: self.switch_thumb.select()
        self.switch_thumb.pack(anchor="w", padx=30, pady=5)
        self.switch_sound = ctk.CTkSwitch(card, text="Sound Notification", onvalue=True, offvalue=False, progress_color=COLORS["success"]); 
        if self.settings["sound"]: self.switch_sound.select()
        self.switch_sound.pack(anchor="w", padx=30, pady=5)
        btn_row = ctk.CTkFrame(card, fg_color="transparent"); btn_row.pack(side="bottom", pady=20, fill="x")
        ctk.CTkButton(btn_row, text="SAVE SETTINGS", height=45, fg_color=COLORS["success"], command=self.save_settings).pack(pady=5)
        self.lbl_save_status = ctk.CTkLabel(btn_row, text="", font=("Arial", 12)); self.lbl_save_status.pack()
        ctk.CTkButton(btn_row, text="UPDATE CORE ENGINE", height=30, fg_color=COLORS["neutral"], command=self.update_core).pack(pady=(15,0))
        self.lbl_update_status = ctk.CTkLabel(btn_row, text="Version: Stable", font=("Arial", 10), text_color="gray"); self.lbl_update_status.pack()
        self.frames["settings"] = f_sets

        f_hist = ctk.CTkFrame(self.main_area, fg_color="transparent")
        ctk.CTkLabel(f_hist, text="Download History", font=("Arial", 28, "bold")).pack(pady=10)
        self.history_box = ctk.CTkTextbox(f_hist, width=700, height=500, font=("Consolas", 12)); self.history_box.insert("1.0", self.load_history_ui()); self.history_box.configure(state="disabled"); self.history_box.pack(pady=10, fill="both", expand=True)
        ctk.CTkButton(f_hist, text="CLEAR HISTORY", fg_color=COLORS["danger"], command=self.clear_history).pack(pady=10)
        self.frames["history"] = f_hist

        self.create_page("single", "Single Video Download", "Paste Video URL...", True)
        self.create_page("playlist", "Bulk Playlist Downloader", "Paste Playlist URL...", True)
        self.create_page("list", "Bulk List Downloader", "Paste Links (One per line)", False)

    def create_page(self, mode, title, placeholder, has_input_row):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        ctk.CTkLabel(f, text=title, font=("Arial", 28, "bold")).pack(pady=10)
        if has_input_row:
            inp = ctk.CTkFrame(f, fg_color="transparent"); inp.pack(pady=20)
            entry = ctk.CTkEntry(inp, width=500, height=45, placeholder_text=placeholder); entry.pack(side="left", padx=(0, 10))
            ctk.CTkButton(inp, text="PASTE", width=100, height=45, fg_color=COLORS["neutral"], command=lambda: self.paste_text(entry)).pack(side="left")
            if mode == "single": self.url_s = entry
            else: self.url_p = entry
        else:
            self.list_box = ctk.CTkTextbox(f, width=600, height=200, border_width=1); self.list_box.pack(pady=10)
            ctk.CTkButton(f, text="PASTE CLIPBOARD", fg_color=COLORS["neutral"], command=lambda: self.list_box.insert("end", self.clipboard_get()+"\n")).pack(pady=5)
        ctk.CTkLabel(f, text="Format & Quality:").pack()
        combo = ctk.CTkComboBox(f, width=250, values=ALL_QUALITIES); combo.pack(pady=10)
        prog = ctk.CTkProgressBar(f, width=600, height=15, progress_color=COLORS["success"]); prog.set(0); prog.pack(pady=20)
        stat = ctk.CTkLabel(f, text="Ready", text_color="gray"); stat.pack()
        btns = ctk.CTkFrame(f, fg_color="transparent"); btns.pack(pady=20)
        btn_start = ctk.CTkButton(btns, text="DOWNLOAD", width=150, height=50, fg_color=COLORS["success"], command=lambda: self.start_thread(mode)); btn_start.pack(side="left", padx=10)
        btn_stop = ctk.CTkButton(btns, text="STOP", width=150, height=50, fg_color=COLORS["danger"], state="disabled", command=self.stop_download); btn_stop.pack(side="left", padx=10)
        ctk.CTkButton(btns, text="CLEAR", width=100, height=50, fg_color=COLORS["neutral"], command=lambda: self.clear_all(mode)).pack(side="left", padx=10)
        if mode == "single": self.res_combo_s=combo; self.prog_s=prog; self.status_s=stat; self.btn_start_s=btn_start; self.btn_stop_s=btn_stop
        elif mode == "playlist": self.res_combo_p=combo; self.prog_p=prog; self.status_p=stat; self.btn_start_p=btn_start; self.btn_stop_p=btn_stop
        elif mode == "list": self.res_combo_l=combo; self.prog_l=prog; self.status_l=stat; self.btn_start_l=btn_start; self.btn_stop_l=btn_stop
        self.frames[mode] = f

    def run_engine(self, mode):
        self.is_cancelled = False
        self.after(0, lambda: self.toggle_buttons(mode, "start"))
        self.after(0, lambda: self.start_loading_animation(mode))
        urls = []
        fmt = "Best Video (Auto)"
        if mode == "single": urls=[self.url_s.get().strip()]; fmt=self.res_combo_s.get(); lbl=self.status_s
        elif mode == "playlist": urls=[self.url_p.get().strip()]; fmt=self.res_combo_p.get(); lbl=self.status_p
        elif mode == "list": urls=[u.strip() for u in self.list_box.get("1.0", "end-1c").splitlines() if u.strip()]; fmt=self.res_combo_l.get(); lbl=self.status_l
        if not urls or not urls[0]:
            self.after(0, lambda: self.toggle_buttons(mode, "stop"))
            self.after(0, lambda: lbl.configure(text="Please enter URLs!", text_color="red"))
            return
        out_path = self.settings["path"]
        if not os.path.exists(out_path): os.makedirs(out_path)
        template = f"{out_path}/%(title)s.%(ext)s" if mode != "playlist" else f"{out_path}/%(playlist_title)s/%(title)s.%(ext)s"
        ydl_opts = {
            'progress_hooks': [lambda d: self.progress_hook(d, mode)],
            'ffmpeg_location': FFMPEG_PATH, 'nocolors': True, 'outtmpl': template,
            'noplaylist': True if mode == "single" else False,
            'ignoreerrors': True, 'no_warnings': True,
            'writethumbnail': self.settings["thumbnail"], 'writesubtitles': self.settings["subtitles"],
            'subtitleslangs': ['en', 'auto'], 'addmetadata': self.settings["metadata"],
        }
        if fmt == "Audio Only (MP3)":
            ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}, {'key': 'EmbedThumbnail'}, {'key': 'FFmpegMetadata'}]})
        else:
            h = None
            if "8K" in fmt: h=4320
            elif "4K" in fmt: h=2160
            elif "2K" in fmt: h=1440
            elif "1080p" in fmt: h=1080
            elif "720p" in fmt: h=720
            elif "480p" in fmt: h=480
            elif "360p" in fmt: h=360
            if h: ydl_opts['format'] = f"bestvideo[height<={h}]+bestaudio/best"
            else: ydl_opts['format'] = "bestvideo+bestaudio/best"
            ydl_opts['merge_output_format'] = 'mp4'
        try:
            with YoutubeDL(ydl_opts) as ydl: ydl.download(urls)
            if self.winfo_exists():
                self.after(0, lambda: lbl.configure(text="Download Complete! ✅", text_color=COLORS["success"]))
                if self.settings["sound"]: winsound.MessageBeep()
                self.log_history(f"{mode.upper()} Download: {urls[0]}")
        except Exception as e:
            if self.winfo_exists():
                msg = "Stopped by User 🛑" if "User Cancelled" in str(e) else "Error Occurred ❌"
                self.after(0, lambda: lbl.configure(text=msg, text_color="red"))
        finally: self.after(0, lambda: self.toggle_buttons(mode, "stop"))

    # --- Helper Functions (Boilerplate) ---
    def show_frame(self, name):
        for f in self.frames.values(): f.pack_forget()
        self.frames[name].pack(fill="both", expand=True)
    def select_folder(self):
        folder = ctk.filedialog.askdirectory()
        if folder: self.settings["path"] = folder; self.entry_path.configure(state="normal"); self.entry_path.delete(0, "end"); self.entry_path.insert(0, folder); self.entry_path.configure(state="readonly")
    def start_thread(self, mode): threading.Thread(target=self.run_engine, args=(mode,), daemon=True).start()
    def toggle_buttons(self, mode, state):
        if not self.winfo_exists(): return
        if mode == "single":
            if state == "start": self.btn_start_s.configure(state="disabled", text="Running..."); self.btn_stop_s.configure(state="normal"); self.start_loading_animation("single")
            else: self.btn_start_s.configure(state="normal", text="DOWNLOAD"); self.btn_stop_s.configure(state="disabled"); self.stop_loading_animation("single")
        elif mode == "playlist":
            if state == "start": self.btn_start_p.configure(state="disabled", text="Running..."); self.btn_stop_p.configure(state="normal"); self.start_loading_animation("playlist")
            else: self.btn_start_p.configure(state="normal", text="DOWNLOAD ALL"); self.btn_stop_p.configure(state="disabled"); self.stop_loading_animation("playlist")
        elif mode == "list":
            if state == "start": self.btn_start_l.configure(state="disabled", text="Running..."); self.btn_stop_l.configure(state="normal"); self.start_loading_animation("list")
            else: self.btn_start_l.configure(state="normal", text="DOWNLOAD LIST"); self.btn_stop_l.configure(state="disabled"); self.stop_loading_animation("list")
    def start_loading_animation(self, mode):
        if mode == "single": self.prog_s.configure(mode="indeterminate"); self.prog_s.start(); self.status_s.configure(text="Fetching...", text_color=COLORS["accent"])
        elif mode == "playlist": self.prog_p.configure(mode="indeterminate"); self.prog_p.start(); self.status_p.configure(text="Processing...", text_color=COLORS["accent"])
        elif mode == "list": self.prog_l.configure(mode="indeterminate"); self.prog_l.start(); self.status_l.configure(text="Processing...", text_color=COLORS["accent"])
    def stop_loading_animation(self, mode):
        if mode == "single": self.prog_s.stop(); self.prog_s.configure(mode="determinate")
        elif mode == "playlist": self.prog_p.stop(); self.prog_p.configure(mode="determinate")
        elif mode == "list": self.prog_l.stop(); self.prog_l.configure(mode="determinate")
    def stop_download(self): self.is_cancelled = True
    def progress_hook(self, d, mode):
        if self.is_cancelled: raise Exception("User Cancelled")
        if d['status'] == 'downloading':
            try:
                self.after(0, lambda: self.stop_loading_animation(mode))
                percent_str = clean_ansi(d.get('_percent_str', '0%')); speed_str = clean_ansi(d.get('_speed_str', 'N/A'))
                downloaded = d.get('downloaded_bytes', 0); total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                pl_idx = d.get('playlist_index', 0); pl_total = d.get('playlist_count') or d.get('n_entries', 0)
                if total > 0:
                    val = downloaded / total
                    self.after(0, lambda: self.safe_update_ui(mode, val, percent_str, speed_str, pl_idx, pl_total))
            except: pass
        if d['status'] == 'finished':
            self.total_success += 1
            if self.winfo_exists(): self.after(0, lambda: self.count_lbl.configure(text=f"Total Success: {self.total_success}"))
    def safe_update_ui(self, mode, val, p_str, s_str, pl_idx, pl_total):
        if not self.winfo_exists(): return
        if mode == "single": self.prog_s.set(val); self.status_s.configure(text=f"Downloading: {p_str} | Speed: {s_str}", text_color=COLORS["success"])
        elif mode == "playlist": self.prog_p.set(val); remaining = pl_total - pl_idx if pl_total else 0; self.status_p.configure(text=f"Video: {pl_idx}/{pl_total} | Left: {remaining} | Speed: {s_str}", text_color=COLORS["success"])
        elif mode == "list": self.prog_l.set(val); self.status_l.configure(text=f"Processing... | Speed: {s_str}", text_color=COLORS["success"])
    def show_about_dialog(self):
        about_window = ctk.CTkToplevel(self); about_window.title("Support Developer"); about_window.geometry("400x550"); about_window.attributes("-topmost", True)
        ctk.CTkLabel(about_window, text="Developed By", font=("Arial", 12), text_color="gray").pack(pady=(20, 0))
        ctk.CTkLabel(about_window, text="Abhijit Das", font=("Arial", 22, "bold"), text_color="#3498db").pack(pady=5)
        link = ctk.CTkLabel(about_window, text="github.com/abhijit94dev", font=("Arial", 12, "underline"), text_color="#1abc9c", cursor="hand2")
        link.pack(pady=5); link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/abhijit94dev"))
        ctk.CTkFrame(about_window, height=2, fg_color="gray").pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(about_window, text="☕ Support me with Bitcoin", font=("Arial", 16, "bold"), text_color="#f1c40f").pack(pady=5)
        try:
            if os.path.exists(QR_IMAGE_PATH):
                pil_img = Image.open(QR_IMAGE_PATH); qr_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(150, 150)); ctk.CTkLabel(about_window, image=qr_img, text="").pack(pady=10)
            else: ctk.CTkLabel(about_window, text="[QR Image Missing]", text_color="orange").pack(pady=20)
        except: pass
        btc_address = "bc1q92p4xzrqxz6znwgyt03jdwcr0uac073s6ueyq7"
        addr_entry = ctk.CTkEntry(about_window, width=300, justify="center"); addr_entry.insert(0, btc_address); addr_entry.configure(state="readonly"); addr_entry.pack(pady=5)
        ctk.CTkButton(about_window, text="Copy Address", fg_color="#27ae60", hover_color="#2ecc71", command=lambda: self.copy_to_clipboard(btc_address, about_window)).pack(pady=10)
    def copy_to_clipboard(self, text, window): self.clipboard_clear(); self.clipboard_append(text); window.title("Copied! ✅"); self.after(2000, lambda: window.title("Support Developer"))
    def open_folder(self):
        path = self.settings["path"]
        if not os.path.exists(path): os.makedirs(path)
        os.startfile(os.path.realpath(path))
    def paste_text(self, entry_widget):
        try: entry_widget.delete(0, "end"); entry_widget.insert(0, self.clipboard_get())
        except: pass
    def clear_all(self, mode):
        if mode == "single": self.url_s.delete(0, 'end'); self.prog_s.set(0); self.status_s.configure(text="Ready", text_color="gray")
        elif mode == "playlist": self.url_p.delete(0, 'end'); self.prog_p.set(0); self.status_p.configure(text="Ready", text_color="gray")
        elif mode == "list": self.list_box.delete("1.0", "end"); self.prog_l.set(0); self.status_l.configure(text="Ready", text_color="gray")

    # --- 3. AUTO UPDATE LOGIC (NEW) ---
    def check_for_updates(self):
        def thread_check():
            try:
                # আপনার গিটহাব রিপোজিটরির নাম দিন
                repo = "abhijit94dev/ZenithDL"
                url = f"https://api.github.com/repos/{repo}/releases/latest"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    latest_tag = data['tag_name']
                    download_url = data['html_url']
                    
                    if latest_tag != CURRENT_VERSION:
                        self.after(0, lambda: self.show_update_popup(latest_tag, download_url))
            except: pass
        threading.Thread(target=thread_check, daemon=True).start()

    def show_update_popup(self, version, url):
        up_win = ctk.CTkToplevel(self)
        up_win.title("Update Available!")
        up_win.geometry("400x200")
        up_win.attributes("-topmost", True)
        ctk.CTkLabel(up_win, text=f"New Version Found: {version}", font=("Arial", 18, "bold"), text_color=COLORS["success"]).pack(pady=20)
        ctk.CTkButton(up_win, text="Download Update", fg_color=COLORS["accent"], command=lambda: webbrowser.open(url)).pack(pady=10)

if __name__ == "__main__":
    app = ZenithDLApp()
    app.mainloop()