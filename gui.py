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

class MovieApp(tk.Tk):
    def __init__(self, data_file="film indonesia.csv"):
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
        style.configure("TButton", foreground="#1d1d1d", font=("Segoe UI", 9))
        style.map("TButton", background=[("active", "#a8dadc")])
        style.configure("Treeview", background="#1a535c", foreground="white", fieldbackground="#1e1e1e", rowheight=24, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#1a535c", foreground="white", font=("Segoe UI", 9, "bold"))
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
                     font=("Segoe UI", 9)).grid(row=0, column=col*2, sticky='w', padx=(8,2))
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

        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=18, pady=4)

        left = ttk.LabelFrame(main_frame, text="Daftar Film", padding=4)
        left.pack(side='left', fill='both', expand='True')

        cols = ("ID", "Judul", "Genre", "Tahun", "Rating")
        col_w = (50, 220, 140, 70,70)
        self.tree = ttk.Treeview(left, columns=cols, show='headings', height=18)
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

    def _do_recommend(self):
        genre = self._genre_var.get().strip()
        year_s = self._year_var.get().strip()
        rate_s = self._rating_var.get().strip()

        if not genre:
            messagebox.showwarning("Input", "Masukkan genre untuk rekomendasi.")
            return
        try:
            min_year = int(year_s) if year_s else 0
        except ValueError:
            messagebox.showerror("Error", "Tahun harus angka."); return
        try:
            min_rating = float(rate_s) if rate_s else 0.0
        except ValueError:
            messagebox.showerror("Error", "Rating harus angka."); return

        result = recommend_movies(self.movies, genre, min_year, min_rating)
        if not result:
            messagebox.showinfo("Hasil", "Tidak ada film yang cocok.")
        self._refresh_table(result)

    def _do_reset(self):
        self._genre_var.set("")
        self._year_var.set("")
        self._rating_var.set("")
        self._refresh_table(self.movies)

    def _sort_rating(self):
        self._refresh_table(quick_sort_rating(self.movies))

    def _sort_year(self):
        self._refresh_table(quick_sort_year(self.movies))

    def _crud_add(self):
        dlg = MovieFormDialog(self, title="Tambah Film Baru")
        if dlg.result is None:
            return
        new_movie = dlg.result
        new_movie.id = generate_id(self.movies)
        self.movies.append(new_movie)
        self._save_to_csv()
        self._refresh_table(self.movies)

        self.crud_undo_stack.push(('add', new_movie))
        self.crud_redo_stack = Stack()

    def _crud_update(self):
        movie = self._selected_movie()
        if not movie:
            messagebox.showwarning("Peringatan", "Pilih film terlebih dahulu.")
            return

        old_snapshot = Movie(movie.id, movie.title, movie.genre,
                             movie.year, movie.rating)

        dlg = MovieFormDialog(self, title="Ubah Film", movie=movie)
        if dlg.result is None:
            return

        edited = dlg.result  # has same id

        movie.title  = edited.title
        movie.genre  = edited.genre
        movie.year   = edited.year
        movie.rating = edited.rating

        self._save_to_csv()
        self._refresh_table(self.movies)

        self.crud_undo_stack.push(('update', old_snapshot, edited))
        self.crud_redo_stack = Stack()

    def _crud_delete(self):
        movie = self._selected_movie()
        if not movie:
            messagebox.showwarning("Peringatan", "Pilih film terlebih dahulu.")
            return

        if not messagebox.askyesno("Konfirmasi",
                                   f"Hapus film '{movie.title}'?"):
            return

        idx = self.movies.index(movie)
        self.movies.remove(movie)
        self._save_to_csv()
        self._refresh_table(self.movies)

        self.crud_undo_stack.push(('delete', movie, idx))
        self.crud_redo_stack = Stack()

    def _crud_undo(self):
        if self.crud_undo_stack.is_empty():
            messagebox.showinfo("Undo", "Tidak ada aksi CRUD untuk dibatalkan.")
            return

        action = self.crud_undo_stack.pop()

        if action[0] == 'add':
            _, movie = action
            if movie in self.movies:
                idx = self.movies.index(movie)
                self.movies.remove(movie)
                self.crud_redo_stack.push(('add', movie, idx))

        elif action[0] == 'update':
            _, old_snap, new_snap = action
            target = next((m for m in self.movies if m.id == old_snap.id), None)
            if target:
                target.title  = old_snap.title
                target.genre  = old_snap.genre
                target.year   = old_snap.year
                target.rating = old_snap.rating
                self.crud_redo_stack.push(('update', old_snap, new_snap))

        elif action[0] == 'delete':
            _, movie, idx = action
            self.movies.insert(min(idx, len(self.movies)), movie)
            self.crud_redo_stack.push(('delete', movie, idx))

        self._save_to_csv()
        self._refresh_table(self.movies)
    
    def _crud_redo(self):
        if self.crud_redo_stack.is_empty():
            messagebox.showinfo("Redo", "Tidak ada aksi CRUD untuk diulang.")
            return

        action = self.crud_redo_stack.pop()

        if action[0] == 'add':
            _, movie, idx = action
            self.movies.insert(min(idx, len(self.movies)), movie)
            self.crud_undo_stack.push(('add', movie))

        elif action[0] == 'update':
            _, old_snap, new_snap = action
            target = next((m for m in self.movies if m.id == new_snap.id), None)
            if target:
                target.title  = new_snap.title
                target.genre  = new_snap.genre
                target.year   = new_snap.year
                target.rating = new_snap.rating
                self.crud_undo_stack.push(('update', old_snap, new_snap))

        elif action[0] == 'delete':
            _, movie, idx = action
            if movie in self.movies:
                self.movies.remove(movie)
                self.crud_undo_stack.push(('delete', movie, idx))

        self._save_to_csv()
        self._refresh_table(self.movies)

    def _wl_add(self):
        movie = self._selected_movie()
        if not movie:
            messagebox.showwarning("Peringatan", "Pilih film terlebih dahulu.")
            return
        self.watchlist.enqueue(movie)
        self._refresh_watchlist()

        self.wl_undo_stack.push(('wl_add', movie))
        self.wl_redo_stack = Stack()

    def _wl_undo(self):
        if self.wl_undo_stack.is_empty():
            messagebox.showinfo("Undo", "Tidak ada aksi watchlist untuk dibatalkan.")
            return
        action = self.wl_undo_stack.pop()
        if action[0] == 'wl_add':
            _, movie = action
            if movie in self.watchlist.items:
                self.watchlist.items.remove(movie)
            self._refresh_watchlist()
            self.wl_redo_stack.push(('wl_add', movie))

    def _wl_redo(self):
        if self.wl_redo_stack.is_empty():
            messagebox.showinfo("Redo", "Tidak ada aksi watchlist untuk diulang.")
            return
        action = self.wl_redo_stack.pop()
        if action[0] == 'wl_add':
            _, movie = action
            self.watchlist.enqueue(movie)
            self._refresh_watchlist()
            self.wl_undo_stack.push(('wl_add', movie))

if __name__ == "__main__":
    app = MovieApp()
    app.mainloop()
