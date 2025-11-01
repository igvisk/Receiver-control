import asyncio
import telnetlib3
import tkinter as tk
from tkinter import ttk

async def check_denon_status(ip_address: str, port: int = 23):
    try:
        reader, writer = await telnetlib3.open_connection(ip_address, port)
        writer.write('PW?\r')  # Power status command
        response = await reader.read(100)
        writer.close()
        await writer.wait_closed()

        if 'PWON' in response:
            return 'ON'
        elif 'PWSTANDBY' in response:
            return 'STANDBY'
        else:
            return 'UNKNOWN'
    except Exception:
        return 'NOT_FOUND'

def update_status_label(status: str):                           #Label color
    if status == 'ON':
        status_label.config(text='ON', background='green', foreground='white')
    elif status == 'STANDBY':
        status_label.config(text='STANDBY', background='orange', foreground='black')
    elif status == 'UNKNOWN':
        status_label.config(text='NOT AVAILABLE', background='gray', foreground='white')
    else:
        status_label.config(text='NOT FOUND', background='red', foreground='white')

def on_connect():
    ip = ip_entry.get()
    status_label.config(text='Kontrolujem...', background='lightgray', foreground='black')
    asyncio.run(run_check(ip))

async def run_check(ip):
    status = await check_denon_status(ip)
    update_status_label(status)

# 🖼️ GUI setup
root = tk.Tk()
root.title("Receiver control")
root.geometry("400x200")
root.resizable(False, False)

ttk.Label(root, text="Zadaj IP adresu Denon AVR:").pack(pady=10)
ip_entry = ttk.Entry(root, width=30)
ip_entry.pack()

ttk.Button(root, text="Pripojiť", command=on_connect).pack(pady=10)

status_label = tk.Label(root, text="Stav zariadenia", width=30, height=2, relief="solid", font=("Arial", 12))
status_label.pack(pady=10)

root.mainloop()
