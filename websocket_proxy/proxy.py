import asyncio
import threading
import webbrowser
import websockets
import json
import tkinter as tk
from tkinter import ttk

loop = None


def get_saved_settings():
    try:
        from settings import get_settings
        s = get_settings()["ap_websocket_proxy"]
        return {
            "server": str(s.target_server),
            "port": str(int(s.target_port)),
            "local_port": str(int(s.local_port)),
            "url": str(s.open_url),
        }
    except Exception:
        return {
            "server": "archipelago.gg",
            "port": "38281",
            "local_port": "9999",
            "url": "",
        }


def save_settings(config):
    try:
        from settings import get_settings
        s = get_settings()["ap_websocket_proxy"]
        s.target_server = config["server"]
        s.target_port = int(config["port"])
        s.local_port = int(config["local_port"])
        s.open_url = config["url"]
        get_settings().save()
    except Exception as e:
        print(f"[Proxy] Could not save settings: {e}")


def log(window, message):
    window.after(0, lambda m=message: _append(window, m))


def _append(window, message):
    window.log_box.configure(state="normal")
    window.log_box.insert(tk.END, message + "\n")
    window.log_box.see(tk.END)
    window.log_box.configure(state="disabled")


async def proxy(local_ws, window, target):
    log(window, f"[Proxy] Client connected → {target}")
    try:
        async with websockets.connect(target) as remote_ws:
            async def forward(src, dst, label):
                try:
                    async for msg in src:
                        try:
                            parsed = json.loads(msg)
                            for packet in parsed:
                                cmd = packet.get("cmd", "?")
                                if cmd == "PrintJSON":
                                    text = "".join(
                                        part.get("text", "")
                                        for part in packet.get("data", [])
                                    )
                                    log(window, f"[Chat] {text}")
                                else:
                                    log(window, f"[{label}] {cmd}")
                        except (json.JSONDecodeError, Exception):
                            pass
                        await dst.send(msg)
                except websockets.exceptions.ConnectionClosed as e:
                    log(window, f"[{label}] closed: {e.code} {e.reason}")

            await asyncio.gather(
                forward(local_ws, remote_ws, "C→S"),
                forward(remote_ws, local_ws, "S→C"),
            )
    except Exception as e:
        log(window, f"[Proxy] Error: {e}")
    log(window, "[Proxy] Client disconnected.")


async def serve(window, target, local_port, open_url):
    async def handler(local_ws):
        await proxy(local_ws, window, target)

    log(window, f"[Proxy] Listening on ws://localhost:{local_port}")
    log(window, f"[Proxy] Forwarding to {target}")

    if open_url:
        log(window, f"[Proxy] Opening {open_url}")
        webbrowser.open(open_url)

    async with websockets.serve(handler, "localhost", local_port):
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass


def run_async(window, target, local_port, open_url):
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(serve(window, target, local_port, open_url))
    finally:
        loop.close()


class ProxyWindow(tk.Tk):
    def __init__(self, target, local_port, open_url):
        super().__init__()
        self.title("AP WebSocket Proxy")
        self.geometry("620x420")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        top = ttk.Frame(self, padding=(8, 8, 8, 4))
        top.pack(fill="x")

        ttk.Label(top, text=f"ws://localhost:{local_port}  →  {target}").pack(side="left")

        if open_url:
            ttk.Button(top, text="Open in Browser",
                       command=lambda: webbrowser.open(open_url)).pack(side="right")

        text_frame = ttk.Frame(self)
        text_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        self.log_box = tk.Text(
            text_frame, state="disabled", wrap="word",
            font=("Consolas", 9), yscrollcommand=scrollbar.set
        )
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.log_box.yview)

    def on_close(self):
        log(self, "[Proxy] Shutting down...")
        if loop and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        self.destroy()


def ask_config():
    result = {}
    saved = get_saved_settings()

    root = tk.Tk()
    root.title("AP WebSocket Proxy")
    root.resizable(False, False)

    frame = ttk.Frame(root, padding=16)
    frame.grid()

    ttk.Label(frame, text="Target Server:").grid(row=0, column=0, sticky="e", padx=(0, 8), pady=4)
    server_var = tk.StringVar(value=saved["server"])
    ttk.Entry(frame, textvariable=server_var, width=30).grid(row=0, column=1, columnspan=2, pady=4, sticky="ew")

    ttk.Label(frame, text="Target Port:").grid(row=1, column=0, sticky="e", padx=(0, 8), pady=4)
    port_var = tk.StringVar(value=saved["port"])
    ttk.Entry(frame, textvariable=port_var, width=10).grid(row=1, column=1, sticky="w", pady=4)

    ttk.Label(frame, text="Local Port:").grid(row=2, column=0, sticky="e", padx=(0, 8), pady=4)
    local_port_var = tk.StringVar(value=saved["local_port"])
    ttk.Entry(frame, textvariable=local_port_var, width=10).grid(row=2, column=1, sticky="w", pady=4)

    ttk.Label(frame, text="Open URL (optional):").grid(row=3, column=0, sticky="e", padx=(0, 8), pady=4)
    url_var = tk.StringVar(value=saved["url"])
    ttk.Entry(frame, textvariable=url_var, width=40).grid(row=3, column=1, columnspan=2, pady=4, sticky="ew")

    def on_start():
        result["server"] = server_var.get().strip()
        result["port"] = port_var.get().strip()
        result["local_port"] = local_port_var.get().strip()
        result["url"] = url_var.get().strip()
        save_settings(result)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    ttk.Button(frame, text="Start Proxy", command=on_start).grid(
        row=4, column=0, columnspan=3, pady=(12, 0)
    )
    root.bind("<Return>", lambda e: on_start())
    root.mainloop()

    return result if "server" in result else None


def main():
    config = ask_config()
    if config is None:
        return

    target = f"ws://{config['server']}:{config['port']}"
    local_port = int(config["local_port"])
    open_url = config["url"] or None

    window = ProxyWindow(target, local_port, open_url)

    thread = threading.Thread(
        target=run_async, args=(window, target, local_port, open_url), daemon=True
    )
    thread.start()

    window.mainloop()


if __name__ == "__main__":
    main()
