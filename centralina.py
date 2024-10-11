import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import json
import os
import threading
import time
import sys


import sys
import os


# Funcție care returnează calea completă către fișierele de resurse (devices.txt, imagini etc.)
def resource_path(relative_path):
    """ Returnează calea completă către un fișier de resurse inclus în EXE """
    try:
        # PyInstaller stochează fișierele într-un folder temporar când rulează EXE-ul
        base_path = sys._MEIPASS
    except Exception:
        # În timpul dezvoltării, se folosește directorul curent
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
placeholder_image_path = resource_path("placeholder.jpg")
placeholder_image = Image.open(placeholder_image_path)

# Folosește resource_path pentru a încărca devices.txt
devices_file = resource_path("devices.txt")

# Deschidem fișierul devices.txt și încărcăm datele
try:
    with open(devices_file, 'r') as file:
        data = file.read()
        print(data)  # Sau procesează datele așa cum ai nevoie
except FileNotFoundError:
    print(f"Eroare: Fișierul {devices_file} nu a fost găsit.")

# Lista de dispozitive (se va încărca din fișier)
devices = []

# Offset de fus orar în ore (implicit 0, adică fără schimbare)
timezone_offset = 0

# Variabilă globală pentru dispozitivele filtrate
filtered_devices = devices  # Inițial, toate dispozitivele sunt afișate
# Funcție pentru a salva dispozitivele și comentariile în fișier
def save_devices():
    try:
        # Salvăm toate informațiile relevante despre dispozitive
        devices_to_save = [{"url": device["url"], "comment": device["comment"]} for device in devices]
        with open(devices_file, 'w') as f:
            json.dump(devices_to_save, f, indent=4)  # Folosim indentare pentru a face fișierul mai lizibil
    except Exception as e:
        print(f"Eroare la salvarea dispozitivelor: {e}")


# Funcție pentru a încărca dispozitivele din fișier
def load_devices():
    if os.path.exists(devices_file):
        try:
            with open(devices_file, 'r') as f:
                file_content = f.read().strip()
                if not file_content:
                    print("Fișierul devices.txt este gol. Încărcăm o listă goală.")
                    return []

                loaded_devices = json.loads(file_content)
                for device in loaded_devices:
                    # Asigurăm că fiecare dispozitiv are un comentariu și alte date asociate
                    device.setdefault("comment", "")
                return loaded_devices
        except json.JSONDecodeError:
            print("Eroare: JSON invalid în fișier. Resetăm lista de dispozitive.")
            return []
        except Exception as e:
            print(f"Eroare la citirea fișierului devices.txt: {e}")
            return []
    return []


# Funcție pentru a obține datele de la dispozitiv
def get_device_data(device_url):
    try:
        response = requests.get(f"{device_url}/status", timeout=2)  # Timeout de 5 secunde
        if response.status_code == 200:
            return response.json()  # Returnăm JSON-ul de status al dispozitivului
        else:
            return None
    except Exception as e:
        print(f"Eroare la obținerea datelor de la {device_url}: {e}")
        return None


# Funcție pentru a obține ultima semnalizare de la dispozitiv
def get_last_signal(device_url):
    try:
        response = requests.get(f"{device_url}/last-signal", timeout=5)  # Timeout de 5 secunde
        if response.status_code == 200:
            return response.text  # Returnăm textul răspunsului (ora semnalului)
        else:
            return "Unavailable"
    except Exception as e:
        print(f"Eroare la obținerea ultimei semnalizări de la {device_url}: {e}")
        return "Error"


# Funcție pentru a crea un card pentru fiecare dispozitiv în interfață
def create_device_frame(device, parent_frame, device_number):
    device_frame = tk.Frame(parent_frame, bd=2, relief="groove", padx=10, pady=10)
    device_frame.grid(row=device_number, column=0, sticky="nsew", padx=5, pady=5)

    # Placeholder pentru imaginea dispozitivului (înlocuiește cu imaginea reală)
    placeholder_image_path = resource_path("placeholder.jpg")
    placeholder_image = Image.open(placeholder_image_path)
    placeholder_image = placeholder_image.resize((200, 80), Image.Resampling.LANCZOS)
    img = ImageTk.PhotoImage(placeholder_image)

    # Organizăm imaginea în coloana 0, iar detaliile dispozitivului în coloana 1
    img_label = tk.Label(device_frame, image=img, width=200, height=80, anchor="w")
    img_label.image = img  # Menținem referința pentru a evita ștergerea din memorie
    img_label.grid(row=0, column=0, rowspan=4, padx=10, pady=2, sticky="w")  # Imagine în coloana 0

    # Etichete de status în coloana 1, totul pe același rând
    status_info = tk.Frame(device_frame)  # Un frame pentru a grupa informațiile despre status
    status_info.grid(row=0, column=1, padx=5, pady=2, sticky="w")

    url_label = tk.Label(status_info, text=f"Device {device_number + 1}: {device['url']}", font=("Arial", 10))
    url_label.grid(row=0, column=0, sticky="w")

    status_label = tk.Label(status_info, text="Status: ---", font=("Arial", 10))
    status_label.grid(row=1, column=0, sticky="w")

    rssi_label = tk.Label(status_info, text="RSSI: --- dBm", font=("Arial", 10))
    rssi_label.grid(row=2, column=0, sticky="w")

    time_label = tk.Label(status_info, text="Time: ---", font=("Arial", 10))
    time_label.grid(row=3, column=0, sticky="w")

    last_signal_label = tk.Label(status_info, text="Last Signal Sent: ---", font=("Arial", 10))
    last_signal_label.grid(row=4, column=0, sticky="w")

    # Afișăm Tavola și Inventar extrase din comentariu
    comment_text = device.get('comment', '')
    try:
        parts = comment_text.split(' ')
        tavola = parts[0] if len(parts) > 0 else "N/A"
        inventar = parts[1] if len(parts) > 1 else "N/A"
    except:
        tavola = "N/A"
        inventar = "N/A"

    tavola_label = tk.Label(status_info, text=f"Tavola : {tavola}", font=("Arial", 10))
    tavola_label.grid(row=5, column=0, sticky="w")

    inventar_label = tk.Label(status_info, text=f"Inventar : {inventar}", font=("Arial", 10))
    inventar_label.grid(row=6, column=0, sticky="w")

    # Butoane și secțiunea pentru comentarii pe coloana 2
    comment_label = tk.Label(device_frame, text="Comment:")
    comment_label.grid(row=0, column=2, padx=5, pady=2, sticky="e")

    comment_entry = tk.Entry(device_frame, width=40)
    comment_entry.grid(row=0, column=3, padx=5, pady=2, sticky="e")
    comment_entry.insert(0, comment_text)  # Încarcăm comentariul existent dacă există

    # Buton de salvare a comentariului
    save_comment_button = tk.Button(device_frame, text="Save Comment",
                                    command=lambda d=device, e=comment_entry: save_comment(d, e))
    save_comment_button.grid(row=1, column=3, padx=5, pady=2)

    # Butoane de ajustare a orei
    increase_button = tk.Button(device_frame, text="Increase Hour",
                                command=lambda d=device: increase_hour(d))
    increase_button.grid(row=2, column=3, padx=5, pady=2)

    decrease_button = tk.Button(device_frame, text="Decrease Hour",
                                command=lambda d=device: decrease_hour(d))
    decrease_button.grid(row=3, column=3, padx=5, pady=2)

    # Buton de ștergere a dispozitivului
    delete_button = tk.Button(device_frame, text="Delete Device",
                              command=lambda d=device: delete_device(d, device_frame))
    delete_button.grid(row=4, column=3, padx=5, pady=2)

    # Stocăm etichetele pentru actualizări ulterioare
    device['status_label'] = status_label
    device['rssi_label'] = rssi_label
    device['time_label'] = time_label
    device['last_signal_label'] = last_signal_label
    device['tavola_label'] = tavola_label
    device['inventar_label'] = inventar_label
    device['comment_entry'] = comment_entry


# Funcție pentru a salva comentariul pentru dispozitivul curent selectat
def save_comment(device, comment_entry):
    # Salvăm comentariul din câmpul de text
    comment_text = comment_entry.get()
    device['comment'] = comment_text  # Actualizăm dispozitivul cu noul comentariu
    save_devices()  # Salvăm toate dispozitivele și comentariile în fișier

    # Împărțim comentariul în câmpuri pentru Tavola și Inventar
    try:
        parts = comment_text.split(' ')
        tavola = parts[0] if len(parts) > 0 else "N/A"
        inventar = parts[1] if len(parts) > 1 else "N/A"

        # Setăm valorile în etichetele corespunzătoare
        device['tavola_label'].config(text=f"Tavola : {tavola}")
        device['inventar_label'].config(text=f"Inventar : {inventar}")
    except Exception as e:
        print(f"Eroare la procesarea comentariului: {e}")

    print(f"Comment saved for {device['url']}")


# Funcție pentru a mări offset-ul orei pentru un dispozitiv
def increase_hour(device):
    try:
        response = requests.get(f"{device['url']}/increase-hour", timeout=5)
        if response.status_code == 200:
            print(f"Hour offset increased for {device['url']}")
        else:
            print(f"Failed to increase hour offset for {device['url']}")
    except Exception as e:
        print(f"Error: {e}")


# Funcție pentru a micșora offset-ul orei pentru un dispozitiv
def decrease_hour(device):
    try:
        response = requests.get(f"{device['url']}/decrease-hour", timeout=5)
        if response.status_code == 200:
            print(f"Hour offset decreased for {device['url']}")
        else:
            print(f"Failed to decrease hour offset for {device['url']}")
    except Exception as e:
        print(f"Error: {e}")


# Funcție pentru a șterge un dispozitiv din listă
def delete_device(device, device_frame):
    devices.remove(device)  # Îndepărtăm dispozitivul din listă
    device_frame.destroy()  # Îndepărtăm vizual cardul dispozitivului din UI
    save_devices()  # Salvăm lista actualizată de dispozitive în fișier
    print(f"Device {device['url']} deleted")


# Funcție pentru a actualiza un dispozitiv la un moment dat
def update_single_device(device):
    device_data = get_device_data(device['url'])  # Obținem datele de la dispozitiv
    last_signal = get_last_signal(device['url'])  # Obținem ultima semnalizare

    def update_labels():
        if device_data:
            # Actualizăm etichetele cu informațiile dispozitivului
            device['status_label'].config(text=f"Status: {device_data['status']}")
            device['rssi_label'].config(text=f"RSSI: {device_data['rssi']} dBm")
            device['time_label'].config(text=f"Time: {device_data['time']}")
            device['last_signal_label'].config(text=f"Last Signal Sent: {last_signal}")
        else:
            # Dacă dispozitivul nu răspunde, afișează "Deconectat"
            device['status_label'].config(text="Status: Deconectat")
            device['rssi_label'].config(text="RSSI: N/A")
            device['time_label'].config(text="Time: ---")
            device['last_signal_label'].config(text="Last Signal Sent: ---")

    # Programează actualizarea etichetelor în firul principal
    root.after(0, update_labels)
# Funcție care actualizează dispozitivele unul câte unul pe rând (sequential update)
def update_devices_sequentially():
    global stop_threads

    # Funcție internă pentru a actualiza dispozitivele în paralel
    def update_device_thread(device):
        if not stop_threads:
            update_single_device(device)

    while not stop_threads:  # Continuă doar dacă firele nu au fost oprite
        threads = []
        for device in filtered_devices:
            if stop_threads:
                break  # Oprește execuția dacă se cere închiderea firelor
            thread = threading.Thread(target=update_device_thread, args=(device,))
            threads.append(thread)
            thread.start()

        # Așteaptă ca toate firele să termine înainte de a continua
        for thread in threads:
            thread.join()

        time.sleep(5)  # Pauză de 5 secunde între actualizări
# Funcție pentru a filtra dispozitivele după inventar
def filter_by_inventar(inventar_value):
    global filtered_devices, stop_threads

    # Oprește firele curente
    stop_threads = True
    time.sleep(0.5)  # Pauză pentru a permite oprirea firelor

    # Golește containerul de dispozitive
    for widget in devices_container.winfo_children():
        widget.destroy()

    # Resetează stop_threads pentru a reporni firele
    stop_threads = False

    # Filtrează dispozitivele pe baza inventarului
    filtered_devices = [device for device in devices if inventar_value.lower() in device['comment'].lower()]

    # Afișează doar dispozitivele filtrate
    for idx, device in enumerate(filtered_devices):
        create_device_frame(device, devices_container, idx)

    # Inițializăm actualizarea doar pentru dispozitivele filtrate
    threading.Thread(target=update_devices_sequentially).start()
# Funcție pentru a afișa toate dispozitivele (fără filtru) și a le actualiza
def display_all_devices():
    global filtered_devices, stop_threads

    # Oprește firele curente
    stop_threads = True
    time.sleep(0.5)  # Pauză pentru a permite oprirea firelor

    # Golește containerul de dispozitive
    for widget in devices_container.winfo_children():
        widget.destroy()

    # Resetează stop_threads pentru a reporni firele
    stop_threads = False

    # Resetează lista de dispozitive filtrate la toate dispozitivele
    filtered_devices = devices

    # Afișează toate dispozitivele
    for idx, device in enumerate(devices):
        create_device_frame(device, devices_container, idx)

    # Repornește actualizarea pentru toate dispozitivele
    threading.Thread(target=update_devices_sequentially).start()
def add_device():
    device_url = f"http://{ip_entry.get()}"

    # Încearcă să obții date de la dispozitiv pentru a verifica dacă IP-ul este accesibil
    device_data = get_device_data(device_url)

    if device_data:  # Dacă dispozitivul răspunde
        if device_url not in [d['url'] for d in devices]:  # Verificăm dacă URL-ul este nou
            new_device = {"url": device_url, "comment": ""}
            devices.append(new_device)

            # Cream frame-ul grafic pentru noul dispozitiv
            create_device_frame(new_device, devices_container, len(devices))

            save_devices()  # Salvăm dispozitivul nou în fișier
        error_label.config(text="")  # Resetează mesajul de eroare dacă IP-ul este accesibil
    else:  # Dacă IP-ul nu este accesibil
        error_label.config(text="IP-ul nu poate fi accesat. Încearcă din nou.", fg="red")


# Crearea ferestrei principale
root = tk.Tk()
root.title("Device Monitor")
root.geometry("1024x600")

# Crearea unei pânze cu scrollbar
canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Scrollbar
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

canvas.configure(yscrollcommand=scrollbar.set)

# Crearea unui frame pentru conținutul pânzei
devices_container = tk.Frame(canvas)

# Adăugarea frame-ului în pânză
canvas.create_window((0, 0), window=devices_container, anchor="nw")

# Redimensionarea automată a pânzei când este modificat conținutul
devices_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Frame pentru filtrarea dispozitivelor după inventar
filter_frame = tk.Frame(root)
filter_frame.pack(pady=10)

filter_label = tk.Label(filter_frame, text="Filter by Inventar:")
filter_label.pack(side="left", padx=5)

filter_entry = tk.Entry(filter_frame)
filter_entry.pack(side="left", padx=5)

filter_button = tk.Button(filter_frame, text="Apply Filter", command=lambda: filter_by_inventar(filter_entry.get()))
filter_button.pack(side="left", padx=5)

clear_filter_button = tk.Button(filter_frame, text="Clear Filter", command=lambda: display_all_devices())
clear_filter_button.pack(side="left", padx=5)

# Frame pentru adăugarea dispozitivelor
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

ip_label = tk.Label(input_frame, text="Enter Device IP:")
ip_label.pack(side="left", padx=5)

ip_entry = tk.Entry(input_frame)
ip_entry.pack(side="left", padx=5)

connect_button = tk.Button(input_frame, text="Connect", command=add_device)
connect_button.pack(side="left", padx=5)

# Etichetă pentru mesajul de eroare
error_label = tk.Label(root, text="", font=("Arial", 10))
error_label.pack(pady=10)

# Încărcăm dispozitivele din fișier și le afișăm în interfață
devices = load_devices()

filtered_devices = devices

for idx, device in enumerate(devices):
    create_device_frame(device, devices_container, idx)

# Inițializăm actualizarea dispozitivelor pe rând
threading.Thread(target=update_devices_sequentially).start()
def close_program():
    global stop_threads
    stop_threads = True  # Setează indicatorul pentru a opri firele
    root.destroy()  # Închide fereastra și oprește complet aplicația
# Rulează interfața grafică
# Rulează interfața grafică
root.mainloop()
