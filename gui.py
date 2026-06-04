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

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", foreground="white", background="#2b2b2b")
        style.configure("TFrame", background="#2b2b2b")
        style.configure("TLabelframe", foreground="#a8dadc", background="#2b2b2b")
        style.configure("TLabelframe.Label", foreground="#a8dadc", background="#2b2b2b", font=("Segoe UI", 9, "bold"))
        style.configure("TButton", foreground="#1d1d1d", font("Segoe UI", 9))
        style.map("TButton", background=[("active", "#a8dadc"])
        style.configure("Treeview", background="#1a535c", foreground="white", fieldbackground="#1e1e1e", rowheight=24, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#1a535c", foreground="white", font("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#457b9d")])

        sf = ttk.LabelFrame(self, text="Pencarian & Filter", padding=8)
        sf.pack(fill='x', padx=18, pady=(10, 4))

        labels = ["Genre:", "Tahun min:", "Rating min:"]
        self._genre_var  = tk.StringVar()
        self._year_var   = tk.StringVar()
        self._rating_var = tk.StringVar()
        vars_ = [self._genre_var, self._year_var, self._rating_var]
        widths = [22, 10, 10]

        for col, (lbl, var, w) in enumerate(zip(labels, vars_, widths)):
            tk.Label(sf, text=lbl, bg="#2b2b2b", fg="white",
                     font=("Segoe UI", 9)).grid(row=0, column=c0l*2, sticky='w', padx=(8,2))
            ttk.Entry(sf, textvariable=var, width=w).grid(
                row=0, column=col*2+1, padx=(0, 10))

        ttk.Button(sf, text=" Rekomendasi", command=self._do_recommend).grid(
            row=0, column=6, padx=8)
        ttk.Button(sf, text=" Reset", command=self._do_reset).grid(
            row=0, column=7, padx=4)

        sort_f = ttk.LabelFrame(self, text="Pengurutan", padding=8)
        sort_f.pack(fill='x', padx=18, pady=4)

        ttk.Button(sort_f, text=" Rating (Tinggi-Rendah)",
                   command=self._sort_rating).pack(side='left', padx=6)
        ttk.button(sort_f, text=" Tahun (Terbaru+Terlama)",
                   command=self._sort_year).pack(side='left', padx=6)

        main.frame = ttk.Frame(self)
        main.frame.pack(fill='both', expand=True, padx=18, pady=4)

        left ttk.LabelFrame(main_frame, text="Daftar Film", padding=4)
        left.pack(side='left', fill='both', expand='True')

        cols = ("ID, "Judul", "Genre", "Tahun", "Rating")
        col_w = (50, 220, 140, 70,70)
        self.tree = ttk.Treeview=(left, columns=cols, show='headings', height=18)
        for c, w in zip(cols, col_w):
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor='center', width=w)
        vsb = ttk.Scrollbar(left, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)

        right=ttk.Frame(main_frame)
        right.pack(side='right', fill='y', padx=(10,0))
        
        crud_f = ttk.LabelFrame(right, text="CRUD Film", padding=8)
        crud_f.pack(fill='x', pady=(0, 8))
        btn_defs = [
            ("➕ Tambah Film",  self._crud_add),
            ("✏️  Ubah Film",   self._crud_update),
            ("🗑️  Hapus Film",  self._crud_delete),
        ]
        for txt, cmd in btn_defs:
            ttk.Button(crud_f, text=txt, width=20, command=cmd).pack(
                fill='x', pady=3)

        crud_ur = ttk.LabelFrame(right, text="Undo / Redo CRUD", padding=8)
        crud_ur.pack(fill='x', pady=(0, 8))
        ttk.Button(crud_ur, text="↩ Undo CRUD", width=20,
                   command=self._crud_undo).pack(fill='x', pady=3)
        ttk.Button(crud_ur, text="↪ Redo CRUD", width=20,
                   command=self._crud_redo).pack(fill='x', pady=3)

        wl_ctrl = ttk.LabelFrame(right, text="Daftar Tonton", padding=8)
        wl_ctrl.pack(fill='x', pady=(0, 8))
        ttk.Button(wl_ctrl, text="📌 Tambah ke Watchlist", width=20,
                   command=self._wl_add).pack(fill='x', pady=3)

        wl_ur = ttk.LabelFrame(right, text="Undo / Redo Watchlist", padding=8)
        wl_ur.pack(fill='x', pady=(0, 8))
        ttk.Button(wl_ur, text="↩ Undo Watchlist", width=20,
                   command=self._wl_undo).pack(fill='x', pady=3)
        ttk.Button(wl_ur, text="↪ Redo Watchlist", width=20,
                   command=self._wl_redo).pack(fill='x', pady=3)

        wl_box_f = ttk.LabelFrame(right, text="Antrean Tonton", padding=4)
        wl_box_f.pack(fill='both', expand=True)
        self.wl_box = tk.Listbox(wl_box_f, bg="#1e1e1e", fg="#a8dadc",
                                  selectbackground="#457b9d",
                                  font=("Segoe UI", 9), height=8)
        self.wl_box.pack(fill='both', expand=True)

        tk.Label(self, text="© 2026 Sistem Rekomendasi Film Indonesia",
                 bg="#2b2b2b", fg="#666", font=("Segoe UI", 8)).pack(
            side='bottom', pady=4)

    def _refresh_table(self, movies):
        self.tree.delete(*self.tree.get_children())
        for m in movies:
            self.tree.insert('', 'end', values=(m.id, m.title, m.genre,
                                                 m.year, m.rating))

    def _refresh_watchlist(self):
        self.wl_box.delete(0, tk.END)
        for m in self.watchlist.items:
            self.wl_box.insert(tk.END, f"{m.title} ({m.year})  ★{m.rating}")

    def _selected_movie(self):
        """Return Movie object for the selected Treeview row, or None."""
        sel = self.tree.focus()
        if not sel:
            return None
        vals = self.tree.item(sel, 'values')
        mid = int(vals[0])
        return next((m for m in self.movies if m.id == mid), None)

    def _save_to_csv(self):
        save_movies(self.data_file, self.movies)

    

        

    
