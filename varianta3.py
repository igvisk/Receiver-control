import tkinter as tk
from tkinter import ttk
import asyncio
import telnetlib3
import json
import os

CONFIG_FILE = "config.json"

class ReceiverApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Receiver control")
        self.geometry("800x400")
        self.controller = AVRController()
        self._setup_styles()
        self._create_frames()
        self.show_control()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background="violet")
        style.configure("Status.TFrame", background="brown")
        style.configure("Nav.TFrame", background="black")
        style.configure("Control.TLabel", background="green", foreground="white", font=("Arial", 16))
        style.configure("Settings.TLabel", background="blue", foreground="white", font=("Arial", 16))
        style.configure("TButton", font=("Arial", 12))
        style.configure("Status.TLabel", background="lightgray", foreground="black", font=("Arial", 12), anchor="center")
        style.configure("Checking.TLabel", background="lightgray", foreground="black", font=("Arial", 12), anchor="center")
        style.configure("On.TLabel", background="green", foreground="white", font=("Arial", 12), anchor="center")
        style.configure("Standby.TLabel", background="orange", foreground="black", font=("Arial", 12), anchor="center")
        style.configure("Unknown.TLabel", background="gray", foreground="white", font=("Arial", 12), anchor="center")
        style.configure("Error.TLabel", background="red", foreground="white", font=("Arial", 12), anchor="center")

    def _create_frames(self):
        self.status_frame = ttk.Frame(self, style="Status.TFrame", height=50)
        self.status_frame.pack(side="top", fill="x")

        self.state_label = ttk.Label(self.status_frame, text="AVR state", style="Status.TLabel")
        self.state_label.pack(pady=10, padx=10, side="right")

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(side="top", fill="both", expand=True)

        self.left_frame = ttk.Frame(self.main_frame, style="Nav.TFrame", width=150)
        self.left_frame.pack(side="left", fill="y")
        self.left_frame.pack_propagate(False)

        self.right_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.right_frame.pack(side="left", fill="both", expand=True)

        ttk.Button(self.left_frame, text="Settings", width=15, command=self.show_settings).pack(side="bottom", padx=5, pady=5)
        ttk.Button(self.left_frame, text="Control", width=15, command=self.show_control).pack(side="bottom", padx=5, pady=5)
        ttk.Button(self.status_frame, text="Power", width=15, command=self.turn_power).pack(side="left", padx=5, pady=5)

    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    def show_control(self):
        self.clear_right_frame()
        ControlPanel(self.right_frame).pack(fill="both", expand=True)

    def show_settings(self):
        self.clear_right_frame()
        SettingsPanel(self.right_frame, self.controller, self.state_label).pack(fill="both", expand=True)

    def turn_power(self):
        ip = self.controller.load_last_ip()
        if not ip:
            self.controller.update_state_label(self.state_label, 'NOT_FOUND')
            return
        self.controller.update_state_label(self.state_label, 'Prepínam stav...')
        asyncio.run(self.controller.toggle_power(ip, self.state_label))

class ControlPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        label = ttk.Label(self, text="Control", style="Control.TLabel")
        label.pack(expand=True, fill="both")

class SettingsPanel(ttk.Frame):
    def __init__(self, parent, controller, state_label):
        super().__init__(parent)
        self.controller = controller
        self.state_label = state_label

        self.pack(fill="both", expand=True, padx=20, pady=20)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        header = ttk.Label(self, text="Settings\nZadaj IP adresu AVR:", style="Settings.TLabel")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.ip_entry = ttk.Entry(self, width=30)
        self.ip_entry.insert(0, self.controller.load_last_ip())
        self.ip_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=5)

        verify_btn = ttk.Button(self, text="Overiť stav", command=self.on_connect)
        verify_btn.grid(row=1, column=1, sticky="ew", pady=5)

    def on_connect(self):
        ip = self.ip_entry.get()
        self.controller.save_ip(ip)
        self.controller.update_state_label(self.state_label, 'Kontrolujem...')
        asyncio.run(self.controller.check_and_update(ip, self.state_label))

class AVRController:
    def save_ip(self, ip_address):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"ip": ip_address}, f)

    def load_last_ip(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("ip", "")
        return "192.168.88.110"

    def update_state_label(self, label, status):
        styles = {
            'ON': "On.TLabel",
            'STANDBY': "Standby.TLabel",
            'UNKNOWN': "Unknown.TLabel",
            'NOT_FOUND': "Error.TLabel",
            'Kontrolujem...': "Checking.TLabel",
            'Prepínam stav...': "Checking.TLabel"
        }
        label.config(text=status, style=styles.get(status, "Status.TLabel"))

    async def check_state(self, ip, port=23):
        try:
            reader, writer = await telnetlib3.open_connection(ip, port)
            writer.write('PW?\r')
            response = await reader.read(100)
            writer.close()
            await writer.wait_closed()
            if 'PWON' in response:
                return 'ON'
            elif 'PWSTANDBY' in response:
                return 'STANDBY'
            return 'UNKNOWN'
        except Exception:
            return 'NOT_FOUND'

    async def check_and_update(self, ip, label):
        status = await self.check_state(ip)
        self.update_state_label(label, status)

    async def toggle_power(self, ip, label, port=23):
        try:
            reader, writer = await telnetlib3.open_connection(ip, port)
            writer.write('PW?\r')
            response = await reader.read(100)
            if 'PWON' in response:
                writer.write('PWSTANDBY\r')
            elif 'PWSTANDBY' in response:
                writer.write('PWON\r')
            else:
                self.update_state_label(label, 'UNKNOWN')
                writer.close()
                await writer.wait_closed()
                return
            await asyncio.sleep(0.5)
            writer.write('PW?\r')
            response = await reader.read(100)
            writer.close()
            await writer.wait_closed()
            if 'PWON' in response:
                self.update_state_label(label, 'ON')
            elif 'PWSTANDBY' in response:
                self.update_state_label(label, 'STANDBY')
            else:
                self.update_state_label(label, 'UNKNOWN')
        except Exception:
            self.update_state_label(label, 'NOT_FOUND')

if __name__ == "__main__":
    app = ReceiverApp()
    app.mainloop()