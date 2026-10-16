"""Windows launcher: visible taskbar window and local service lifecycle."""
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from urllib.request import urlopen
import webbrowser

APP_NAME = "DNS AI Shield Ultra"
URL = "http://127.0.0.1:8000/dashboard"
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "DNS AI Shield Ultra"


def prepare_data():
    DATA.mkdir(parents=True, exist_ok=True)
    for name in ("dns_ai.db", "ml_model.pkl"):
        target = DATA / name
        if not target.exists():
            shutil.copy2(ROOT / "assets" / name, target)


def server():
    os.environ["DNS_SHIELD_DATA_DIR"] = str(DATA)
    import runpy
    runpy.run_module("app", run_name="__main__")


class Window:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("420x210")
        self.root.resizable(False, False)
        self.root.iconbitmap(str(ROOT / "assets" / "icon.ico"))
        self.process = None
        tk.Label(self.root, text=APP_NAME, font=("Segoe UI", 16, "bold")).pack(pady=(18, 8))
        self.status = tk.StringVar(value="Iniciando...")
        tk.Label(self.root, textvariable=self.status, font=("Segoe UI", 10)).pack(pady=8)
        tk.Button(self.root, text="Abrir painel", command=lambda: webbrowser.open(URL), width=22).pack(pady=8)
        tk.Label(self.root, text="Feche esta janela para encerrar o programa.", font=("Segoe UI", 9)).pack()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self.start)

    def start(self):
        try:
            prepare_data()
            exe = sys.executable if getattr(sys, "frozen", False) else str(Path(__file__).resolve())
            command = [exe, "--server"] if getattr(sys, "frozen", False) else [sys.executable, exe, "--server"]
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            env = os.environ.copy()
            env["DNS_SHIELD_DATA_DIR"] = str(DATA)
            self.process = subprocess.Popen(command, env=env, creationflags=flags,
                                            cwd=str(DATA), stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL)
            threading.Thread(target=self.wait_ready, daemon=True).start()
        except Exception as exc:
            self.status.set("Falha ao iniciar")
            messagebox.showerror(APP_NAME, str(exc))

    def wait_ready(self):
        for _ in range(60):
            if self.process.poll() is not None:
                self.root.after(0, lambda: self.status.set("Falha: porta 8000 ocupada ou servidor indisponível."))
                return
            try:
                with urlopen("http://127.0.0.1:8000/api/status", timeout=0.4) as response:
                    if response.status == 200:
                        self.root.after(0, lambda: (self.status.set("Painel disponível em 127.0.0.1:8000"), webbrowser.open(URL)))
                        return
            except Exception:
                pass
            time.sleep(0.5)
        self.root.after(0, lambda: self.status.set("O painel não respondeu. Verifique as portas 53 e 8000."))

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.root.destroy()


if __name__ == "__main__":
    if "--server" in sys.argv:
        server()
    else:
        Window().root.mainloop()
