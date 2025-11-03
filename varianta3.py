#Framy:
# 1. status_frame - Používa štýl "Status.TFrame"
# 2. main_frame - Je to hlavný rám pod status_frame.
#               - Slúži ako kontajner pre ďalšie dva rámce:
#                                                           -left_frame (navigácia)
#                                                           -right_frame (hlavný obsah)
# 3. left_frame (navigačný panel): Nachádza sa vľavo v hlavnom rámci.
#                                -stýl "Nav.TFrame" – čierne pozadie
#                                   Obsahuje navigačné tlačidlá: btn_settings a btn_dashboard, prepinaju obsah right_frame
# 4. right_frame (hlavná obsahová plocha): Tento rám zobrazuje aktuálny obsah aplikácie.
#                                       -Na začiatku je v ňom “Dashboard” (show_dashboard()), ale keď používateľ klikne na “Settings”, 
#                                       jeho obsah sa vymaže a nahradí novým (pomocou clear_right_frame()

# 4a. settings_frame — vnorený rámec: Vznikne iba po kliknutí na “Settings”.
#                                    -Je vnorený vo right_frame.
#                                       Obsahuje: header (nadpis), ip_entry (pole pre IP adresu), Button “Pripojiť”, Status_label (stavové označenie)



import tkinter as tk
from tkinter import ttk
import asyncio
import telnetlib3
import json
import os

CONFIG_FILE = "config.json"

#switch frames
def show_dashboard():
    clear_right_frame()
    dashboard_label = ttk.Label(right_frame, text="Dashboard", style="Dashboard.TLabel")
    dashboard_label.pack(expand=True, fill="both")

def show_settings():
    global ip_entry, state_label
    clear_right_frame()

    # Vnútorný rám pre všetky widgety Settings
    settings_frame = ttk.Frame(right_frame)
    settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Nadpis
    header = ttk.Label(settings_frame, text="Settings\nZadaj IP adresu AVR:", style="Settings.TLabel")
    header.pack(fill="x", pady=10)

    # IP entry
    ip_entry = ttk.Entry(settings_frame, width=30)
    ip_entry.insert(0, load_last_ip())
    ip_entry.pack(pady=5)

    # Tlačidlo
    ttk.Button(settings_frame, text="Pripojiť", command=on_connect).pack(pady=10)

    # State label (ttk verzia so štýlom)
    state_label = ttk.Label(settings_frame, text="Status", style="Status.TLabel")
    state_label.pack(pady=10, fill="x")


def clear_right_frame():
    for widget in right_frame.winfo_children():
        widget.destroy()

#Ukladanie IP adresy do súboru
def save_ip(ip_address):
    data = {"ip": ip_address}
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

#Načítanie poslednej IP pri štarte
def load_last_ip():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("ip", "192.168.88.110")  # default
    else:
        return "192.168.88.110"

#####
#Settings functions
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

def update_state_label(status: str):
    if status == 'ON':
        state_label.config(text='ON', style="On.TLabel")
    elif status == 'STANDBY':
        state_label.config(text='STANDBY', style="Standby.TLabel")
    elif status == 'UNKNOWN':
        state_label.config(text='NOT AVAILABLE', style="Unknown.TLabel")
    else:
        state_label.config(text='NOT FOUND', style="Error.TLabel")


def on_connect():
    global ip_entry, state_label
    if ip_entry is None or state_label is None:
        print("IP entry or state label not initialized.")
        return

    ip = ip_entry.get()
    save_ip(ip)  # uloženie do súboru
    state_label.config(text='Kontrolujem...', style="Checking.TLabel")
    asyncio.run(run_check(ip))


async def run_check(ip):
    status = await check_denon_status(ip)
    update_state_label(status)

####

# Hlavné okno
window = tk.Tk()
window.title("Receiver control")
window.geometry("800x400")

# Štýly pre ttk widgety
style = ttk.Style()

# Základné štýly pre layout
style.configure("TFrame", background="violet")
style.configure("Status.TFrame", background="brown")
style.configure("Nav.TFrame", background="black")

# Labely - text
style.configure("Dashboard.TLabel", background="green", foreground="white", font=("Arial", 16))
style.configure("Settings.TLabel", background="blue", foreground="white", font=("Arial", 16))

# Tlačítka
style.configure("TButton", font=("Arial", 12))

# Štýly pre state label v settings
style.configure("Status.TLabel", background="lightgray", foreground="black", font=("Arial", 12), anchor="center")
style.configure("Checking.TLabel", background="lightgray", foreground="black", font=("Arial", 12), anchor="center")
style.configure("On.TLabel", background="green", foreground="white", font=("Arial", 12), anchor="center")
style.configure("Standby.TLabel", background="orange", foreground="black", font=("Arial", 12), anchor="center")
style.configure("Unknown.TLabel", background="gray", foreground="white", font=("Arial", 12), anchor="center")
style.configure("Error.TLabel", background="red", foreground="white", font=("Arial", 12), anchor="center")

# Status rám TOP
status_frame = ttk.Frame(window, style="Status.TFrame", height=50)
status_frame.pack(side="top", fill="x")

# Hlavný rám pod statusom
main_frame = ttk.Frame(window)
main_frame.pack(side="top", fill="both", expand=True)

# Ľavý rám (navigácia)
left_frame = ttk.Frame(main_frame, style="Nav.TFrame", width=150)
left_frame.pack(side="left", fill="y")
left_frame.pack_propagate(False)

# Pravý rám (obsah)
right_frame = ttk.Frame(main_frame, style="TFrame")
right_frame.pack(side="left", fill="both", expand=True)

# Tlačidlá v ľavom ráme
btn_settings = ttk.Button(left_frame, text="Settings", width=15, command=show_settings)
btn_settings.pack(side='bottom', padx=5, pady=5)

btn_dashboard = ttk.Button(left_frame, text="Dashboard", width=15, command=show_dashboard)
btn_dashboard.pack(side="bottom", padx=5, pady=5)                                                       # + fill="x" - roztahuje na celu sirku rodicovskeho ramu + ak chcem toto poradie musia byt oba bottom a v opacnom poradi ako ich chcem

# Štart s Dashboardom
show_dashboard()

window.mainloop()
