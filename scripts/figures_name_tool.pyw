import tkinter as tk
from tkinter import ttk, filedialog, Canvas, Frame, Toplevel, messagebox
from PIL import Image, ImageTk
from collections import Counter
import requests
from io import BytesIO
import re
import os
import shutil
import tempfile
import json
from typing import Dict, List, Any, Optional

LANGUAGE_MAPPING: Dict[str, str] = {
    "de-de": "German",
    "en-gb": "English",
    "en-us": "English",
    "fr-fr": "French"
}

TONIES_JSON_URL: str = "https://raw.githubusercontent.com/toniebox-reverse-engineering/tonies-json/release/tonies.json"

# Max Image Size
MAX_WIDTH: int = 100
MAX_HEIGHT: int = 100
COLS: int = 3  # Count of columns

DEFAULT_LANGUAGE = "en-us"

MISC_SERIES_DIRECTORY = "Other"
FILE_EXTENSION = ".nfc"

# The directory of this script, will be used to find relative paths for copying files
# this allows us to reference the script location regardless of the current working directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class TonieNameTool:
    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.root.title("Tonie Name Tool")
        self.root.geometry("400x500")
        
        self.file_path: str = ""
        self.data: List[Dict[str, Any]] = {}
        self.canvas: Optional[Canvas] = None
        self.scroll_frame: Optional[Frame] = None
        self.selected_language: tk.StringVar = tk.StringVar()
        self.selected_series: tk.StringVar = tk.StringVar()
        self.dropdown_series: Optional[ttk.Combobox] = None
        # added: var to display currently selected file
        self.file_label_var: tk.StringVar = tk.StringVar(value="No file selected")

    def get_language_name(self, language_code: str) -> str:
        """returns the folder name for the selected language"""
        return LANGUAGE_MAPPING.get(language_code, language_code)

    def generate_valid_filename(self, name: str, max_length: int = 255) -> str | None:
        """Generate a valid filename by removing invalid characters and replacing umlauts"""

        if not name:
            return None

        # remove invalid characters
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", name)
        
        name = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
        # remove leading/trailing whitespaces
        name = name.strip()

        # truncate to max_length
        if len(name) > max_length:
            name = name[:max_length]

        return name

    def load_new_file(self) -> None:
        """function to load a new file"""
        self.file_path = filedialog.askopenfilename(filetypes=[("NFC-File", "*.nfc")])
        if not self.file_path:
            return

        # show selected file to the user
        self.file_label_var.set(self.file_path)

        # Update the dropdowns
        self.choose_language_show_series()

    def choose_language_show_series(self, *args: Any) -> None:
        """function to show the series of the selected language"""
        lang = self.selected_language.get()
        language_series = [entry for entry in self.data if entry.get("language") == lang and (entry["hash"] or (entry["episodes"] is not None and entry["episodes"].find("Set") >= 0))]
        unique_series = sorted(set(entry.get("series") for entry in language_series), reverse=False)
        self.dropdown_series["values"] = unique_series
        self.dropdown_series["state"] = "readonly" if unique_series else "disabled"
        self.selected_series.set("")

    def show_episode_details(self, entry: Dict[str, Any]) -> None:
        """shows the choosen episode in a detail window"""
        details_window = Toplevel(self.root)
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

        def on_ok() -> None:
            """function to copy the file to the selected folder"""
            lang = self.selected_language.get()
            series = self.selected_series.get()
            episode = entry["episodes"]
            # unused at the moment, but maybe needed in the future
            # it seems it was used for audio_id 
            # selected_data: List[Dict[str, Any]] = [entry for entry in self.data if entry["language"] == lang and entry["series"] == series and entry["episodes"] == episode]
             #audio_id = [entry["audio_id"] for entry in selected_data]

            # generate valid folder and file names
            language_folder = self.generate_valid_filename(self.get_language_name(lang))
            if not language_folder:
                messagebox.showinfo("Error", "Invalid language folder name.")
                return
            
            series_folder = self.generate_valid_filename(series)
            if not series_folder:
                messagebox.showinfo("Error", "Invalid series folder name.")
                return
            
            # this is a tad hacky, but some episodes have no valid name
            # in this scenario we will put them in the other folder
            # the series_folder will be used as file name
            file_name = self.generate_valid_filename(episode)

            if not file_name:
                print("No valid episode name, using series name as file name and 'Other' as series folder")
                file_name = series_folder
                series_folder = MISC_SERIES_DIRECTORY

            details_window.destroy()

            # destination is relative to the script directory
            destination_path = os.path.join(SCRIPT_DIR, "..", language_folder, series_folder)
            os.makedirs(destination_path, exist_ok=True)

            export_file_path = os.path.abspath(os.path.join(destination_path, file_name + FILE_EXTENSION))
            print(f"Copying file to {export_file_path}")
            try:
                shutil.copy(self.file_path, export_file_path)
            except shutil.SameFileError:
                messagebox.showinfo("Error", f"The file {file_name} already exists in {language_folder}/{series_folder}")
                return
            messagebox.showinfo("Selection confirmed", f"The Tonie is stored under {language_folder}/{series_folder}/{file_name}")

        # Add OK-Button
        tk.Button(details_window, text="OK", command=on_ok).pack(pady=10)
        # Add Close-Button
        tk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=5)

    def choose_series_show_episodes(self, *args: Any) -> None:
        """function to show the episodes of the selected series"""
        lang = self.selected_language.get()
        series = self.selected_series.get()
        
        # reset the scroll frame
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # filter the data
        episodes = [entry for entry in self.data if entry["language"] == lang and entry["series"] == series and (entry["hash"] or (entry["episodes"] is not None and entry["episodes"].find("Set") >= 0))]

        filtered_episodes = []
        for entry in episodes:

            # skip entries without episodes, 
            # for example "Curious George" has no episodes, it is the series itself in this context
            if entry["episodes"] and entry["episodes"].find("Set") >= 0 and "tracks" in entry:
                for track in entry["tracks"]:
                    new_entry = entry.copy()
                    new_entry["episodes"] = track
                    filtered_episodes.append(new_entry)
            else:
                filtered_episodes.append(entry)

        # create the grid
        row = 0
        col = 0
        for entry in filtered_episodes:
            # load the image from the url
            response = requests.get(entry["pic"])
            img_data = Image.open(BytesIO(response.content))
            
            # scale image
            img_data.thumbnail((MAX_WIDTH, MAX_HEIGHT))
            img = ImageTk.PhotoImage(img_data)
            
            # Show Image
            img_button = tk.Button(self.scroll_frame, image=img, command=lambda e=entry: self.show_episode_details(e))
            img_button.image = img
            img_button.grid(row=row, column=col, padx=10, pady=10)
            
            # episode-title
            episode_label = tk.Label(self.scroll_frame, text=entry["episodes"], wraplength=100, justify="center")
            episode_label.grid(row=row + 1, column=col, padx=10, pady=5)
        
            col += 1
            if col >= COLS:
                col = 0
                row += 2
        
        # Scrollbar update
        self.scroll_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    @staticmethod
    def get_tonies_json_data() -> Dict[str, Any]:
        """Get json payload of all tonies, use local cached file if exists"""

        # get system temp directory
        temp_dir = tempfile.gettempdir()
        cache_file_path = os.path.join(temp_dir, TONIES_JSON_URL.split("/")[-1])

        # check if cache file exists
        if os.path.exists(cache_file_path):
            with open(cache_file_path, "r") as f:
                return json.load(f)

        try:
            response = requests.get(TONIES_JSON_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Save to cache file
            with open(cache_file_path, "w") as f:
                json.dump(data, f)
            return data
        except requests.RequestException as e:
            print(f"Error while loading the data: {e}")
        return {}

    def setup_ui(self) -> None:
        """Setup the user interface"""
        # Buttons and Dropdowns
        tk.Button(self.root, text="Choose new file", command=self.load_new_file).pack(pady=10)

        # display the selected file path under the button
        tk.Label(self.root, textvariable=self.file_label_var, wraplength=380, justify="left", foreground="black").pack(pady=(0,10))

        # Dropdown language
        tk.Label(self.root, text="Choose a language:").pack(pady=5)
        sorted_languages = self._get_sorted_languages()
        dropdown_language = ttk.Combobox(self.root, textvariable=self.selected_language, values=sorted_languages, state="readonly", width=50)
        dropdown_language.pack(pady=5)

        # Dropdown series
        tk.Label(self.root, text="Choose a series:").pack(pady=5)
        self.dropdown_series = ttk.Combobox(self.root, textvariable=self.selected_series, state="disabled", width=50)
        self.dropdown_series.pack(pady=5)

        # Frame for Scrollbar
        self.canvas = Canvas(self.root)
        self.scroll_frame = Frame(self.canvas)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        # Event-listener for the language change
        self.selected_language.trace_add("write", self.choose_language_show_series)
        # Event-listener for the series change
        self.selected_series.trace_add("write", self.choose_series_show_episodes)

        # set default language if available (will trigger choose_language_show_series via trace)
        if sorted_languages:
            if DEFAULT_LANGUAGE in sorted_languages:
                self.selected_language.set(DEFAULT_LANGUAGE)
            else:
                self.selected_language.set(sorted_languages[0])

    def _get_sorted_languages(self) -> List[str]:
        """Helper method to get sorted languages"""
        languages = [entry.get("language") for entry in self.data if entry.get("hash") and entry.get("episodes") is not None]
        filtered_languages = [lang for lang in languages if isinstance(lang, str)]
        language_counts = Counter(filtered_languages)
        return sorted(language_counts.keys(), key=lambda x: language_counts[x], reverse=True)

    def run(self) -> None:
        """Main function to start the GUI"""
        self.data = self.get_tonies_json_data()
        if not self.data:
            messagebox.showerror("Error", "Could not load tonies data.")
            return

        self.setup_ui()
        self.root.mainloop()


def main() -> None:
    """Main entry point"""
    root = tk.Tk()
    app = TonieNameTool(root)
    app.run()


if __name__ == "__main__":
    main()