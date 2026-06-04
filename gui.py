import tkinter as tk
from tkinter import ttk, messagebox

from data_manager import load_movies, save_movies, generate_id
from movie import Movie
from recommendation import recommend_movies
from search import linear_search_genre, linear_search_title
from sorting import quick_sort_rating, quick_sort_year

from stack_history import Stack
from queue_history import Queue


def is_valid_int(text):
    text = text.strip()
    if not text:
        return False
    if text.startswith("-"):
        return text[1:].isdigit()
    return text.isdigit()


def is_valid_float(text):
    text = text.strip()
    if not text:
        return False
    parts = text.split(".")
    if len(parts) == 1:
        return is_valid_int(parts[0])
    if len(parts) == 2:
        left = parts[0] if parts[0] else "0"
        right = parts[1] if parts[1] else "0"
        return is_valid_int(left) and right.isdigit()
    return False


class MovieFormDialog(tk.Toplevel):
    # Dialog modal untuk menambah atau mengubah data film.
    # Setelah dialog ditutup:
    # - self.result berisi objek Movie jika pengguna menyimpan data.
    # - self.result bernilai None jika pengguna membatalkan proses.

    def __init__(self, parent, title="Film", movie=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg="#2b2b2b")
        self.grab_set()          # modal
        self.result = None
        self._movie_id = movie.id if movie else None

        fields = [("Judul", "title"), ("Genre", "genre"),
                  ("Tahun", "year"), ("Rating", "rating")]

        self._vars = {}
        for row, (label, key) in enumerate(fields):
            tk.Label(self, text=label + ":", fg="white", bg="#2b2b2b",
                     font=("Segoe UI", 10)).grid(row=row, column=0,
                                                  sticky='w', padx=14, pady=6)
            var = tk.StringVar()
            if movie:
                var.set(getattr(movie, key))
            entry = ttk.Entry(self, textvariable=var, width=34)
            entry.grid(row=row, column=1, padx=14, pady=6)
            self._vars[key] = var

        btn_frame = tk.Frame(self, bg="#2b2b2b")
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="Simpan", command=self._on_save).pack(
            side='left', padx=8)
        ttk.Button(btn_frame, text="Batal", command=self.destroy).pack(
            side='left', padx=8)

        self.wait_window()

    def _on_save(self):
        title  = self._vars["title"].get().strip()
        genre  = self._vars["genre"].get().strip()
        year   = self._vars["year"].get().strip()
        rating = self._vars["rating"].get().strip()

        if not title:
            messagebox.showerror("Error", "Judul tidak boleh kosong.", parent=self)
            return
        if not genre:
            messagebox.showerror("Error", "Genre tidak boleh kosong.", parent=self)
            return
        if not is_valid_int(year):
            messagebox.showerror("Error", "Tahun harus berupa angka bulat.", parent=self)
            return
        if not is_valid_float(rating):
            messagebox.showerror("Error", "Rating harus berupa angka (0–10).", parent=self)
            return

        mid = self._movie_id if self._movie_id is not None else -1
        self.result = Movie(mid, title, genre, int(year), float(rating))
        self.destroy()

class MoviaApp(tk.Tk):
    def __init__(self, data_file="film indonesia.csv):
        super().__init__()
        self.title("Sistem Rekomendasi Film Indonesia")
        self.geometry("1000x700")
        self.minsize(860, 600)
        self.configure(bg="#2b2b2b")

        self.data_file = data_file
        self.movies    = load_movies(self.data_file)

        self.watchlist     = Queue()
        self.w1_undo_stack = Stack()
        self.w1_redo_stack = Stack()

        self.crud_undo_stack = Stack()
        self.crud_redo_stack = Stack()

        self._build_ui(self)
        self._refresh_table(self.movies)
        self._refresh_watchlist()

    
