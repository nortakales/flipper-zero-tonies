import tkinter as tk
from tkinter import ttk, filedialog, Canvas, Frame, Toplevel, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import re
import os
import queue
import shutil
import tempfile
import time
import json
import hashlib
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional, Tuple

LANGUAGE_MAPPING: Dict[str, str] = {
    "de-de": "German",
    "en-gb": "English",
    "en-us": "English",
    "fr-fr": "French"
}

TONIES_JSON_URL: str = "https://raw.githubusercontent.com/toniebox-reverse-engineering/tonies-json/release/tonies.json"

# tonies.json is cached in the temp directory, refetch it once the cache is older than this.
# Without this the tool keeps showing the state of the list from the day it was started for
# the first time, so Tonies that were added or completed upstream later never show up.
CACHE_MAX_AGE_SECONDS: int = 24 * 60 * 60

# downloaded figure pictures are cached here, a series can hold a few hundred figures
# and we do not want to download them again every time the series is selected
PICTURE_CACHE_DIR: str = os.path.join(tempfile.gettempdir(), "tonies_pictures")
DOWNLOAD_THREADS: int = 8

# Max Image Size
MAX_WIDTH: int = 100
MAX_HEIGHT: int = 100
COLS: int = 3  # Count of columns

DEFAULT_LANGUAGE = "en-us"

MISC_SERIES_DIRECTORY = "Other"
FILE_EXTENSION = ".nfc"

# Series that are named differently in tonies.json than the directory this repo
# already uses for them, either because the spelling differs ("Dr. Seuss" -> "Dr Seuss",
# "?" cannot be part of a path) or because this repo keeps several series together in
# one directory ("Trolls" -> "DreamWorks/Trolls"). A value containing "/" points into a
# sub directory. Without an entry the series name from tonies.json is used as it is.
SERIES_DIRECTORY_OVERRIDES: Dict[str, Dict[str, str]] = {
    "English": {
        "All Engines Go": "Story Time/All Engines Go",
        "Ask the StoryBots": "Ask the Storybots",
        "Brave": "Disney and Pixar",
        "Cars": "Disney and Pixar",
        "Coco": "Disney and Pixar",
        "Cocomelon": "CoComelon",
        "Daniel Tiger's Neighborhood": "Daniel Tigers Neighborhood",
        "Disney The Muppets": "Disney the Muppets",
        "Dr. Seuss": "Dr Seuss",
        "Favorite Children's Songs": "Tonies Originals",
        "Favorite Children’s Songs": "Tonies Originals",
        "Finding Dory": "Disney and Pixar",
        "Gabby's Dollhouse": "DreamWorks/Gabbys Dollhouse",
        "How to Train Your Dragon": "DreamWorks",
        "How to train your Dragon": "DreamWorks",
        "Inside Out": "Disney and Pixar",
        "Kung Fu Panda": "DreamWorks",
        "Marvel's Spidey and His Amazing Friends": "Marvels Spidey and His Amazing Friends",
        "Monsters, Inc.": "Disney and Pixar",
        "Nap Time": "Tonies Originals",
        "PAW Patrol": "Paw Patrol",
        "Potty Training": "Tonies Originals",
        "Ratatouille": "Disney and Pixar",
        "Shrek": "DreamWorks",
        "Sleepy Bear": "Sleepy Time",
        "Sleepy Crocodile": "Sleepy Time",
        "Sleepy Duck": "Sleepy Time",
        "Sleepy Friends": "Sleepy Time",
        "Sleepy Jaguar": "Sleepy Time",
        "Sleepy Octopus": "Sleepy Time",
        "Sleepy Penguin": "Sleepy Time",
        "Sleepy Rabbit": "Sleepy Time",
        "Sleepy Sheep": "Sleepy Time",
        "Sleepy Toucan": "Sleepy Time",
        "Sleepy Whale": "Sleepy Time",
        "The Incredibles": "Disney and Pixar",
        "tonies® Original": "Tonies Originals",
        "Toy Story": "Disney and Pixar",
        "Trolls": "DreamWorks/Trolls",
    },
    "German": {
        "ADAC": "Clever Tonies/ADAC",
        "Affenzahn Utopia": "Affenzahn",
        "Batman": "DC",
        "Bauernhof Set": "My First Tonies",
        "BiBiBiber hat da mal 'ne Frage": "BiBiBiber hat da mal ne Frage",
        "Conni & Co": "Book Tonies/Conni",
        "Das kleine Böse Buch": "Das kleine boese Buch",
        'DC: Batwheels': 'DC',
        "Der zauberhafte Wunschbuchladen": "Book Tonies/Der zauberhafte Wunschbuchladen",
        "Die (un)langweiligste Schule der Welt": "Book Tonies/Die (un)langweiligste Schule der Welt",
        "Die drei !!!": "Die drei Ausrufezeichen",
        "Die drei ???": "Die drei Fragezeichen",
        "Die drei ??? Kids": "Die drei Fragezeichen Kids",
        "Die Sendung mit dem Elefanten": "Die Sendung mit der Maus & dem Elefanten",
        "Drachenzähmen leicht gemacht": "Dreamworks",
        "Dschungel Set": "My First Tonies",
        "Ein Mädchen namens Willow": "Book Tonies/Ein Maedchen namens Willow",
        "Elmer": "Elmar",
        "Emmi & Einschwein": "Book Tonies/Emmi & Einschwein",
        "Frau Honig": "Book Tonies/Frau Honig",
        "Gabby's Dollhouse": "Gabbys Dollhouse",
        "GEOlino": "Clever Tonies/GEOlino",
        "Gregs Tagebuch": "Greg's Tagebuch",
        "GROßE EXPERTEN": "GROSSE EXPERTEN",
        "Gus, der klitzekleine Ritter": "Gus",
        "herrH": "Emma die Ente",
        'Jurassic World: Neue Abenteuer': 'Jurassic World',
        "Kannawoniwasein": "Book Tonies/Kannawoniwasein",
        "KoboldKroniken": "Book Tonies/KoboldKroniken",
        "Kung Fu Panda": "Dreamworks",
        "Kurt, Einhorn wider Willen": "Book Tonies/Kurt, Einhorn wider Willen",
        "Käpt'n Blaubär": "Kaeptn Blaubaer",
        "Käpt'n Sharky": "Kaptn Sharky",
        "Leo's Tag": "Leos Tag",
        "Lieblings-Literatur": "Book Tonies/Lieblings-Literatur",
        "Little People - Big Dreams": "Clever Tonies",
        "Madagascar": "Dreamworks",
        "MARVEL Spidey und seine Super-Freunde": "Marvel Spidey und seine Super-Freunde",
        "Maus": "Die Sendung mit der Maus & dem Elefanten",
        "Micky Maus & Freunde": "Disney Micky Maus & Freunde",
        "Reise Set": "My First Tonies",
        "School of Talents": "Book Tonies/School of Talents",
        "School of Talents 4": "Book Tonies/School of Talents",
        "School of Talents 5": "Book Tonies/School of Talents",
        "Sendung mit der Maus zum hören": "Die Sendung mit der Maus & dem Elefanten",
        "Shaun das Schaf": "Schaun das Schaf",
        "Shrek": "Dreamworks",
        "Spenden Fuchs": "Die Gluecksfuechse",
        "Spider-Man": "Marvel",
        "Trolls": "Dreamworks",
        "Weihnachtsmann & Co. KG": "Weihnachtsmann und Co.KG",
        "Wie man 13 wird": "Book Tonies/Wie man 13 wird",
        "Wieso? Weshalb? Warum? junior": "Wieso Weshalb Warum Junior",
        "Wieso? Weshalb? Warum? Profiwissen - Set": "Wieso Weshalb Warum",
        "Wundervolle Welt der Dinosaurier und der Urzeit": "Clever Tonies",
        "Zippel": "Book Tonies/Zippel, das wirklich wahre Schlossgespenst",
        "Zippel, das wirklich wahre Schlossgespenst": "Book Tonies/Zippel, das wirklich wahre Schlossgespenst",
    },
    "French": {
    },
}

# scripts/validate_files.sh only accepts these characters in a file name,
# directory names may additionally contain an apostrophe (e.g. "Greg's Tagebuch")
ALLOWED_FILENAME_CHARACTERS = re.compile(r"[^A-Za-z0-9().,!%&+ -]")
ALLOWED_DIRNAME_CHARACTERS = re.compile(r"[^A-Za-z0-9().,!%&+' -]")

# characters with a well known replacement, everything that is left after this
# is transliterated by stripping the accents (e.g. "é" -> "e")
TRANSLITERATIONS: Dict[str, str] = {
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
    "ß": "ss",
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...",
}

# The directory of this script, will be used to find relative paths for copying files
# this allows us to reference the script location regardless of the current working directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class TonieNameTool:
    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.root.title("Tonie Name Tool")
        self.root.geometry("400x500")

        self.file_path: str = ""
        self.data: List[Dict[str, Any]] = []
        self.canvas: Optional[Canvas] = None
        self.scroll_frame: Optional[Frame] = None
        self.selected_language: tk.StringVar = tk.StringVar()
        self.selected_series: tk.StringVar = tk.StringVar()
        self.dropdown_series: Optional[ttk.Combobox] = None
        # added: var to display currently selected file
        self.file_label_var: tk.StringVar = tk.StringVar(value="No file selected")

        # the pictures are downloaded in background threads and handed over to the
        # main thread through this queue, tkinter itself is not thread safe
        self.image_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS)
        self.image_queue: "queue.Queue[Tuple[int, tk.Button, str, Optional[bytes]]]" = queue.Queue()
        self.image_cache: Dict[str, ImageTk.PhotoImage] = {}
        self.placeholder_image: Optional[ImageTk.PhotoImage] = None
        # increased on every series change, so late downloads of the previous series are dropped
        self.render_token: int = 0

    def get_language_name(self, language_code: str) -> str:
        """returns the folder name for the selected language"""
        return LANGUAGE_MAPPING.get(language_code, language_code)

    @staticmethod
    def get_display_name(entry: Dict[str, Any]) -> str:
        """name of an entry as it is shown in the UI

        Not every Tonie in tonies.json has an episode name, for example "Gracie's Corner"
        or "Curious George" are a single figure without separate episodes. For those the
        series name is the name of the figure.
        """
        episode = (entry.get("episodes") or "").strip()
        if episode:
            return episode
        return (entry.get("series") or "").strip()

    @staticmethod
    def is_selectable(entry: Dict[str, Any]) -> bool:
        """checks if an entry can be offered in the UI

        All this tool needs is a name and a language that has a directory in this repo.
        Entries are deliberately not filtered by their hash: the hash is only known for
        figures somebody has already dumped and it is not used by this tool, filtering
        on it hides about three quarters of all Tonies.
        """
        if entry.get("language") not in LANGUAGE_MAPPING:
            return False
        return bool(TonieNameTool.get_display_name(entry))

    @staticmethod
    def get_series_name(entry: Dict[str, Any]) -> str:
        """the series an entry is listed under, single figures are listed under their own name"""
        return (entry.get("series") or "").strip() or TonieNameTool.get_display_name(entry)

    def transliterate(self, name: str) -> str:
        """replaces umlauts and other non ascii characters with their ascii counterpart"""
        for character, replacement in TRANSLITERATIONS.items():
            name = name.replace(character, replacement)

        # strip the accents of everything that is left, e.g. "é" -> "e"
        decomposed = unicodedata.normalize("NFKD", name)
        return "".join(character for character in decomposed if not unicodedata.combining(character))

    def generate_valid_name(self, name: str, pattern: Any, max_length: int = 255) -> str | None:
        """Generate a valid file or directory name that is accepted by validate_files.sh"""

        if not name:
            return None

        name = self.transliterate(name)

        # remove everything that is not allowed and collapse the whitespace that is left over
        name = pattern.sub("", name)
        name = re.sub(r"\s+", " ", name).strip()

        # a trailing dot is not allowed on windows
        name = name.rstrip(".").strip()

        if not name:
            return None

        # truncate to max_length
        if len(name) > max_length:
            name = name[:max_length].strip()

        return name

    def generate_valid_filename(self, name: str, max_length: int = 255) -> str | None:
        """Generate a valid filename by removing invalid characters and replacing umlauts"""
        return self.generate_valid_name(name, ALLOWED_FILENAME_CHARACTERS, max_length)

    def generate_valid_dirname(self, name: str, max_length: int = 255) -> str | None:
        """Generate a valid directory name by removing invalid characters and replacing umlauts"""
        return self.generate_valid_name(name, ALLOWED_DIRNAME_CHARACTERS, max_length)

    def get_series_directory(self, language_folder: str, series: str) -> str | None:
        """directory of a series inside the language directory

        Most series are stored under their own name, the ones listed in
        SERIES_DIRECTORY_OVERRIDES under the name this repo already uses.
        """
        override = SERIES_DIRECTORY_OVERRIDES.get(language_folder, {}).get(series)
        if not override:
            return self.generate_valid_dirname(series)

        # an override may point into a sub directory, e.g. "DreamWorks/Trolls"
        parts = [self.generate_valid_dirname(part) for part in override.split("/")]
        if not all(parts):
            return None
        return os.path.join(*parts)

    def load_new_file(self) -> None:
        """function to load a new file"""
        self.file_path = filedialog.askopenfilename(filetypes=[("NFC-File", "*.nfc")])
        if not self.file_path:
            return

        # show selected file to the user
        self.file_label_var.set(self.file_path)

        # Update the dropdowns
        self.choose_language_show_series()

    def get_entries_for_language(self, language: str) -> List[Dict[str, Any]]:
        """all selectable entries of the given language"""
        return [entry for entry in self.data if entry.get("language") == language and self.is_selectable(entry)]

    def choose_language_show_series(self, *args: Any) -> None:
        """function to show the series of the selected language"""
        lang = self.selected_language.get()
        language_series = self.get_entries_for_language(lang)
        unique_series = sorted({self.get_series_name(entry) for entry in language_series}, key=str.casefold)
        self.dropdown_series["values"] = unique_series
        self.dropdown_series["state"] = "readonly" if unique_series else "disabled"
        self.selected_series.set("")

    def show_episode_details(self, entry: Dict[str, Any]) -> None:
        """shows the choosen episode in a detail window"""
        details_window = Toplevel(self.root)
        details_window.title("Episode details")

        # title
        tk.Label(details_window, text=self.get_display_name(entry), font=("Arial", 14, "bold")).pack(pady=10)

        # load image from url
        try:
            content = self.get_picture_bytes(entry.get("pic"))
            if content:
                img_data = Image.open(BytesIO(content))

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
            if not self.file_path:
                messagebox.showinfo("Error", "No file selected.")
                return

            lang = self.selected_language.get()
            series = self.selected_series.get()
            episode = (entry.get("episodes") or "").strip()
            # unused at the moment, but maybe needed in the future
            # it seems it was used for audio_id
            # selected_data: List[Dict[str, Any]] = [entry for entry in self.data if entry["language"] == lang and entry["series"] == series and entry["episodes"] == episode]
             #audio_id = [entry["audio_id"] for entry in selected_data]

            # generate valid folder and file names
            language_folder = self.generate_valid_dirname(self.get_language_name(lang))
            if not language_folder:
                messagebox.showinfo("Error", "Invalid language folder name.")
                return

            series_folder = self.get_series_directory(self.get_language_name(lang), series)
            if not series_folder:
                messagebox.showinfo("Error", "Invalid series folder name.")
                return

            # this is a tad hacky, but some episodes have no valid name
            # in this scenario we will put them in the other folder
            # the series name will be used as file name
            file_name = self.generate_valid_filename(episode)

            if not file_name:
                print("No valid episode name, using series name as file name and 'Other' as series folder")
                file_name = self.generate_valid_filename(series)
                series_folder = MISC_SERIES_DIRECTORY

            if not file_name:
                messagebox.showinfo("Error", "Invalid file name.")
                return

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

        # reset the scroll frame, pictures that are still on their way belong to the previous series
        self.render_token += 1
        token = self.render_token
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not series:
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            return

        # filter the data
        episodes = [entry for entry in self.get_entries_for_language(lang) if self.get_series_name(entry) == series]

        filtered_episodes = []
        seen_names = set()
        for entry in episodes:

            # a "Set" holds several episodes on one figure, offer every track of it
            episode_name = (entry.get("episodes") or "").strip()
            if episode_name and episode_name.find("Set") >= 0 and entry.get("tracks"):
                expanded = []
                for track in entry["tracks"]:
                    new_entry = entry.copy()
                    new_entry["episodes"] = track
                    expanded.append(new_entry)
            else:
                # entries without episodes are shown under their series name,
                # for example "Curious George" is the figure itself in this context
                expanded = [entry]

            # the same episode can be listed more than once, for example for a re-release
            for new_entry in expanded:
                name = self.get_display_name(new_entry).casefold()
                if name in seen_names:
                    continue
                seen_names.add(name)
                filtered_episodes.append(new_entry)

        filtered_episodes.sort(key=lambda item: self.get_display_name(item).casefold())

        # create the grid
        row = 0
        col = 0
        placeholder = self.get_placeholder_image()
        for entry in filtered_episodes:
            # the picture is downloaded in the background, start with the placeholder
            img_button = tk.Button(self.scroll_frame, image=placeholder, command=lambda e=entry: self.show_episode_details(e))
            img_button.image = placeholder
            img_button.grid(row=row, column=col, padx=10, pady=10)
            self.request_picture(entry.get("pic"), img_button, token)

            # episode-title
            episode_label = tk.Label(self.scroll_frame, text=self.get_display_name(entry), wraplength=100, justify="center")
            episode_label.grid(row=row + 1, column=col, padx=10, pady=5)

            col += 1
            if col >= COLS:
                col = 0
                row += 2

        # Scrollbar update
        self.scroll_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_placeholder_image(self) -> ImageTk.PhotoImage:
        """grey box that is shown until the picture of a figure has been downloaded"""
        if self.placeholder_image is None:
            self.placeholder_image = ImageTk.PhotoImage(Image.new("RGB", (MAX_WIDTH, MAX_HEIGHT), (220, 220, 220)))
        return self.placeholder_image

    @staticmethod
    def get_picture_bytes(url: Optional[str]) -> Optional[bytes]:
        """downloads the picture of a figure, cached on disk

        Not every entry has a picture and a series can hold a few hundred figures,
        so a missing picture must not break the grid.
        """
        if not url:
            return None

        cache_file_path = os.path.join(PICTURE_CACHE_DIR, hashlib.sha1(url.encode("utf-8")).hexdigest())

        if os.path.exists(cache_file_path):
            try:
                with open(cache_file_path, "rb") as f:
                    return f.read()
            except OSError as e:
                print(f"Error while reading the cached image: {e}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error while loading the image {url}: {e}")
            return None

        try:
            os.makedirs(PICTURE_CACHE_DIR, exist_ok=True)
            with open(cache_file_path, "wb") as f:
                f.write(response.content)
        except OSError as e:
            print(f"Error while caching the image: {e}")

        return response.content

    def request_picture(self, url: Optional[str], img_button: tk.Button, token: int) -> None:
        """loads the picture for a button, either from the cache or in a background thread"""
        if not url:
            return

        cached = self.image_cache.get(url)
        if cached is not None:
            img_button.configure(image=cached)
            img_button.image = cached
            return

        self.image_pool.submit(lambda: self.image_queue.put((token, img_button, url, self.get_picture_bytes(url))))

    def process_image_queue(self) -> None:
        """hands the downloaded pictures over to the widgets, runs in the main thread"""
        while True:
            try:
                token, img_button, url, content = self.image_queue.get_nowait()
            except queue.Empty:
                break

            # the user already switched to another series
            if token != self.render_token or not content:
                continue

            try:
                img = self.image_cache.get(url)
                if img is None:
                    img_data = Image.open(BytesIO(content))

                    # scale image
                    img_data.thumbnail((MAX_WIDTH, MAX_HEIGHT))
                    img = ImageTk.PhotoImage(img_data)
                    self.image_cache[url] = img

                # the button may have been destroyed in the meantime
                if img_button.winfo_exists():
                    img_button.configure(image=img)
                    img_button.image = img
            except Exception as e:
                print(f"Error while loading the image {e}")

        self.root.after(100, self.process_image_queue)

    @staticmethod
    def get_tonies_json_data() -> List[Dict[str, Any]]:
        """Get json payload of all tonies, use local cached file if it is still recent"""

        # get system temp directory
        temp_dir = tempfile.gettempdir()
        cache_file_path = os.path.join(temp_dir, TONIES_JSON_URL.split("/")[-1])

        def read_cache() -> Optional[List[Dict[str, Any]]]:
            try:
                with open(cache_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Error while reading the cache file: {e}")
            return None

        # check if the cache file exists and is not outdated
        if os.path.exists(cache_file_path) and time.time() - os.path.getmtime(cache_file_path) < CACHE_MAX_AGE_SECONDS:
            cached = read_cache()
            if cached:
                return cached

        try:
            response = requests.get(TONIES_JSON_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Save to cache file
            with open(cache_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return data
        except requests.RequestException as e:
            print(f"Error while loading the data: {e}")

        # keep working with the outdated cache file if there is one
        if os.path.exists(cache_file_path):
            return read_cache() or []
        return []

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

        # a series can hold a few hundred figures, so scrolling with the wheel should work
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Event-listener for the language change
        self.selected_language.trace_add("write", self.choose_language_show_series)
        # Event-listener for the series change
        self.selected_series.trace_add("write", self.choose_series_show_episodes)

        # stop the download threads when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # set default language if available (will trigger choose_language_show_series via trace)
        if sorted_languages:
            if DEFAULT_LANGUAGE in sorted_languages:
                self.selected_language.set(DEFAULT_LANGUAGE)
            else:
                self.selected_language.set(sorted_languages[0])

    def on_close(self) -> None:
        """shut down the download threads and close the window"""
        self.render_token += 1
        self.image_pool.shutdown(wait=False)
        self.root.destroy()

    def _on_mousewheel(self, event: tk.Event) -> None:
        """scroll the grid with the mouse wheel"""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _get_sorted_languages(self) -> List[str]:
        """Helper method to get the languages this repo has a directory for, most Tonies first"""
        counts: Dict[str, int] = {}
        for entry in self.data:
            if self.is_selectable(entry):
                counts[entry["language"]] = counts.get(entry["language"], 0) + 1
        return sorted(counts.keys(), key=lambda x: counts[x], reverse=True)

    def run(self) -> None:
        """Main function to start the GUI"""
        self.data = self.get_tonies_json_data()
        if not self.data:
            messagebox.showerror("Error", "Could not load tonies data.")
            return

        self.setup_ui()
        self.process_image_queue()
        self.root.mainloop()


def main() -> None:
    """Main entry point"""
    root = tk.Tk()
    app = TonieNameTool(root)
    app.run()


if __name__ == "__main__":
    main()
