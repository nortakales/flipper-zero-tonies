import tkinter as tk
from tkinter import ttk, filedialog, Canvas, Frame, Toplevel, messagebox
from PIL import Image, ImageTk
from collections import Counter
import requests
from io import BytesIO
import re
import os
import shutil

LANGUAGE_MAPPING = {
    "de-de": "German",
    "en-gb": "English",
    "en-us": "English",
    "fr-fr": "French"
}

# Max Image Size
MAX_WIDTH = 100
MAX_HEIGHT = 100
COLS = 3  # Count of columns
file_path = ""

# GUI erstellen
root = tk.Tk()
root.title("Tonie Name Tool")
root.geometry("400x500") 

def get_language_name(language_code):
    """returns the folder name for the selected language"""
    return LANGUAGE_MAPPING.get(language_code, language_code)  # default to the lang_code if no mapping exists

def generate_valid_filename(name, max_length=255):
    # remove invalid characters
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", name)
    name = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss") # replace umlauts
    # remove leading/trailing whitespaces
    name = name.strip()

    # truncate to max_length
    if len(name) > max_length:
        name = name[:max_length]

    return name

def load_new_file():
    """ fuction to load a new file """
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("NFC-File", "*.nfc")])
    if not file_path:
        return  # No file selected

    # Update the dropdowns
    choose_language_show_series()

def choose_language_show_series(*args):
    """ function to show the series of the selected language """
    lang = selected_language.get()
    language_series = [entry for entry in data if entry.get("language") == lang and (entry["hash"] or (entry["episodes"] is not None and entry["episodes"].find("Set") >= 0))]
    unique_series = sorted(set(entry.get("series") for entry in language_series), reverse=False)
    dropdown_series["values"] = unique_series
    dropdown_series["state"] = "readonly" if unique_series else "disabled"
    selected_series.set("")  # reset the series

def show_episode_details(entry):
    """ shows the choosen episode in a detail window """
    details_window = Toplevel(root)
    details_window.title("Episode details")

    # title
    tk.Label(details_window, text=entry["episodes"], font=("Arial", 14, "bold")).pack(pady=10)

    # load image from url
    try:
        response = requests.get(entry["pic"])
        img_data = Image.open(BytesIO(response.content))

        # scale image to fit into the window
        img_data.thumbnail((400, 400))
        img = ImageTk.PhotoImage(img_data)

        img_label = tk.Label(details_window, image=img)
        img_label.image = img
        img_label.pack(pady=10)
    except Exception as e:
        print(f"Error while loading the image {e}")

    def on_ok():
        """ function to copy the file to the selected folder """
        global file_path
        lang = selected_language.get()
        series = selected_series.get()
        episode = entry["episodes"]
        selected_data = [entry for entry in data if entry["language"] == lang and entry["series"] == series and entry["episodes"] == episode]
        #audio_id = [entry["audio_id"] for entry in selected_data]
        language_folder = generate_valid_filename(get_language_name(lang))
        series_folder = generate_valid_filename(series)
        file_name = generate_valid_filename(episode)
        details_window.destroy()  # close the window
        destination_path = os.path.join(language_folder, series_folder,)
        os.makedirs(destination_path, exist_ok=True) # create the folder if it does not exist
        shutil.copy(file_path, os.path.join(destination_path, file_name + ".nfc"))
        messagebox.showinfo("Selection confirmed", f"The Tonie is stored under {language_folder}/{series_folder}/{file_name}")

    # Add OK-Button
    tk.Button(details_window, text="OK", command=on_ok).pack(pady=10)
    # Add Close-Button
    tk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=5)

def choose_series_show_episodes(*args):
    """ function to show the episodes of the selected series """
    lang = selected_language.get()
    series = selected_series.get()
    
    # reset the scroll frame
    for widget in scroll_frame.winfo_children():
        widget.destroy()
    
    # filter the data
    episodes = [entry for entry in data if entry["language"] == lang and entry["series"] == series and (entry["hash"] or (entry["episodes"] is not None and entry["episodes"].find("Set") >= 0))]

    filtered_episodes = []
    for entry in episodes:
        if entry["episodes"].find("Set") >= 0 and "tracks" in entry:
            for track in entry["tracks"]:
                 new_entry = entry.copy()
                 new_entry["episodes"] = track
                 filtered_episodes.append(new_entry)
        else:
             filtered_episodes.append(entry)

    # create the grid
    row , col = 0, 0
    for entry in filtered_episodes:
        # load the image from the url
        response = requests.get(entry["pic"])
        img_data = Image.open(BytesIO(response.content))
        
        # scale image
        img_data.thumbnail((MAX_WIDTH, MAX_HEIGHT))  # Automatically scale to fit the frame
        img = ImageTk.PhotoImage(img_data)
        
        # Show Image
        # Image-Button with function
        img_button = tk.Button(scroll_frame, image=img, command=lambda e=entry: show_episode_details(e))
        img_button.image = img
        img_button.grid(row=row, column=col, padx=10, pady=10)
        
        # episode-title
        episode_label = tk.Label(scroll_frame, text=entry["episodes"], wraplength=100, justify="center")
        episode_label.grid(row=row + 1, column=col, padx=10, pady=5)
    
        col += 1
        if col >= COLS:  # Max 3 Columns
            col = 0
            row += 2
    
    # Scrollbar update
    scroll_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

# get the full data from the json file
url="https://raw.githubusercontent.com/toniebox-reverse-engineering/tonies-json/release/tonies.json"
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
except requests.RequestException as e:
    print(f"Error while loading the data: {e}")
    data = []

# filter the data by all languages containing figures
languages = [entry.get("language") for entry in data if entry.get("hash") and entry.get("episodes") is not None]
filtered_languages = [lang for lang in languages if isinstance(lang, str)]
language_counts = Counter(filtered_languages)
sorted_languages = sorted(language_counts.keys(), key=lambda x: language_counts[x], reverse=True)

# Buttons and Dropdowns
tk.Button(root, text="Choose new file", command=load_new_file).pack(pady=10)

# Dropdown language
tk.Label(root, text="Choose a language:").pack(pady=5)
selected_language = tk.StringVar()
dropdown_language = ttk.Combobox(root, textvariable=selected_language, values=sorted_languages, state="readonly", width=50)
dropdown_language.pack(pady=5)

# Dropdown series
tk.Label(root, text="Choose a series:").pack(pady=5)
selected_series = tk.StringVar()
dropdown_series = ttk.Combobox(root, textvariable=selected_series, state="disabled", width=50)
dropdown_series.pack(pady=5)

# Frame for Scrollbar
canvas = Canvas(root)
scroll_frame = Frame(canvas)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)
canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

# Event-listener for the language change
selected_language.trace_add("write", choose_language_show_series)
# Event-listener for the series change
selected_series.trace_add("write", choose_series_show_episodes)

root.mainloop()
