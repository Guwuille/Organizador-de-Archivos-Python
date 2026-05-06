"""
Organizador de Documentos v2.0
Mejoras principales:
  - Bug fix: fuzzy matching palabra-a-palabra (no texto completo)
  - UI thread-safe via after()
  - Config persistente en JSON
  - Interfaz con pestañas (Organizar / Categorías / Registro)
  - Modo simulación (dry-run) sin mover archivos
  - Opción copiar vs. mover
  - Slider de tolerancia fuzzy
  - Registro visual con colores + exportar CSV
  - Soporte .txt, .bmp, .tiff, .webp
  - OCR multilenguaje (español + inglés)
  - Arquitectura orientada a objetos
"""

import os
import shutil
import threading
import json
import csv
import warnings
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path

import pytesseract
from PIL import Image
import pdfplumber
from docx import Document

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

warnings.filterwarnings("ignore")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

CONFIG_FILE = "config.json"

DEFAULT_CATEGORIES = {
    "cedula": "Cedulas",
    "dni": "Cedulas",
    "contrato": "Contratos",
    "factura": "Facturas",
    "licencia": "Licencias",
    "titulo": "Titulos",
    "recibo": "Recibos",
    "certificado": "Certificados",
    "nota": "Notas",
    "informe": "Informes",
    "presupuesto": "Presupuestos",
    "declaracion": "Declaraciones",
}

# ─── Extracción de texto ─────────────────────────────────────────────────────

def extract_text_from_image(path: str) -> str:
    try:
        return pytesseract.image_to_string(Image.open(path), lang="spa+eng")
    except Exception:
        return ""

def extract_text_from_pdf(path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception:
        pass
    return text

def extract_text_from_docx(path: str) -> str:
    try:
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

def extract_text_from_txt(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

# Mapeo extensión → función extractora
_EXTRACTORS = {
    frozenset({".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}): extract_text_from_image,
    frozenset({".pdf"}):  extract_text_from_pdf,
    frozenset({".docx"}): extract_text_from_docx,
    frozenset({".txt"}):  extract_text_from_txt,
}

def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    for exts, fn in _EXTRACTORS.items():
        if ext in exts:
            return fn(file_path)
    return ""

# ─── Clasificación ──────────────────────────────────────────────────────────

def get_client_name(text: str, keywords: dict, tolerance: float = 0.75) -> str:
    """
    Busca el cliente en el texto.
    1. Coincidencia exacta multi-palabra (prioridad por longitud descendente).
    2. Fuzzy matching palabra a palabra sobre el texto.
    """
    text_lower = text.lower()

    # 1. Coincidencia exacta (keywords más largas primero para evitar falsos positivos)
    for keyword, folder in sorted(keywords.items(), key=lambda x: -len(x[0])):
        parts = keyword.strip().lower().split()
        if all(part in text_lower for part in parts):
            return folder

    # 2. Fuzzy: comparar cada palabra del texto contra la lista de keywords
    candidates = list(keywords.keys())
    for word in text_lower.split():
        if len(word) < 4:
            continue
        matches = get_close_matches(word, candidates, n=1, cutoff=tolerance)
        if matches:
            return keywords[matches[0]]

    return "Desconocido"

def get_category(text: str, categories: dict) -> str:
    text_lower = text.lower()
    for keyword, cat in categories.items():
        if keyword in text_lower:
            return cat
    return "Otros"

# ─── Operaciones de archivo ─────────────────────────────────────────────────

def unique_path(destination: str) -> str:
    """Resuelve colisiones de nombre añadiendo _1, _2, ..."""
    if not os.path.exists(destination):
        return destination
    base, ext = os.path.splitext(destination)
    counter = 1
    while os.path.exists(destination):
        destination = f"{base}_{counter}{ext}"
        counter += 1
    return destination

def transfer_file(file_path: str, base_dir: str, client: str,
                  category: str, copy_mode: bool) -> str:
    target_dir = os.path.join(base_dir, client, category)
    os.makedirs(target_dir, exist_ok=True)
    dest = unique_path(os.path.join(target_dir, os.path.basename(file_path)))
    if copy_mode:
        shutil.copy2(file_path, dest)
    else:
        shutil.move(file_path, dest)
    return dest

# ─── Config / helpers ────────────────────────────────────────────────────────

def parse_kv(text: str) -> dict:
    """Parsea formato 'clave : Valor' línea por línea."""
    result = {}
    for line in text.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k, v = k.strip().lower(), v.strip()
            if k and v:
                result[k] = v
    return result

def load_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_config(data: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── Worker (hilo secundario) ─────────────────────────────────────────────

def organize_files(source_dir: str, dest_dir: str,
                   keywords: dict, categories: dict,
                   copy_mode: bool, dry_run: bool,
                   tolerance: float, callbacks: dict):
    """
    callbacks esperados:
      on_progress(processed, total, filename)
      on_file_done(src, dest, client, category)
      on_error(filepath, error_msg)
      on_done(processed, errors, log)
    """
    all_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(source_dir)
        for f in files
    ]

    total = len(all_files)
    processed = 0
    errors = 0
    log = []

    for file_path in all_files:
        filename = os.path.basename(file_path)
        callbacks["on_progress"](processed, total, filename)

        try:
            extracted = extract_text(file_path)
            combined  = (filename + " " + extracted).lower()

            client   = get_client_name(combined, keywords, tolerance)
            category = get_category(combined, categories)

            dest = os.path.join(dest_dir, client, category, filename)
            if not dry_run:
                dest = transfer_file(file_path, dest_dir, client, category, copy_mode)

            log.append({"archivo": filename, "cliente": client,
                        "categoria": category, "destino": dest, "estado": "OK"})
            callbacks["on_file_done"](file_path, dest, client, category)

        except Exception as exc:
            errors += 1
            log.append({"archivo": filename, "cliente": "?",
                        "categoria": "?", "destino": "", "estado": f"ERROR: {exc}"})
            callbacks["on_error"](file_path, str(exc))

        processed += 1

    callbacks["on_done"](processed, errors, log)

# ─── Interfaz gráfica ────────────────────────────────────────────────────────

class OrganizerApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Organizador de Documentos v2.0")
        self.geometry("780x680")
        self.minsize(640, 540)
        self.configure(bg="#f0f0f0")

        self._config = load_config()
        self._log    = []
        self._running = False

        self._apply_styles()
        self._build_ui()
        self._load_saved_data()

    # ── Estilos ──────────────────────────────────────────────

    def _apply_styles(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("TFrame", background="#f0f0f0")
        st.configure("TLabel", background="#f0f0f0", font=("Segoe UI", 9))
        st.configure("TLabelframe", background="#f0f0f0")
        st.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))
        st.configure("TNotebook.Tab", font=("Segoe UI", 9, "bold"), padding=[10, 4])
        st.configure("Action.TButton",
                     font=("Segoe UI", 10, "bold"),
                     foreground="white", background="#2e7d32",
                     padding=[12, 6])
        st.map("Action.TButton",
               background=[("active", "#1b5e20"), ("disabled", "#a5d6a7")])
        st.configure("Danger.TButton",
                     font=("Segoe UI", 9),
                     foreground="white", background="#c62828", padding=[8, 4])

    # ── Construcción de UI ────────────────────────────────────

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._tab_main = ttk.Frame(nb, padding=12)
        self._tab_cats = ttk.Frame(nb, padding=12)
        self._tab_log  = ttk.Frame(nb, padding=12)

        nb.add(self._tab_main, text="  📁 Organizar  ")
        nb.add(self._tab_cats, text="  🏷️ Categorías  ")
        nb.add(self._tab_log,  text="  📋 Registro  ")

        self._build_tab_main()
        self._build_tab_cats()
        self._build_tab_log()

    def _build_tab_main(self):
        f = self._tab_main
        p = dict(padx=6, pady=4, sticky="ew")

        # Carpetas
        dirs_frame = ttk.LabelFrame(f, text="Carpetas")
        dirs_frame.pack(fill="x", pady=(0, 8))
        dirs_frame.columnconfigure(1, weight=1)

        ttk.Label(dirs_frame, text="Origen:").grid(row=0, column=0, **p)
        self._e_origen = ttk.Entry(dirs_frame, width=55)
        self._e_origen.grid(row=0, column=1, **p)
        ttk.Button(dirs_frame, text="📂",
                   command=lambda: self._pick_dir(self._e_origen)).grid(row=0, column=2, **p)

        ttk.Label(dirs_frame, text="Destino:").grid(row=1, column=0, **p)
        self._e_destino = ttk.Entry(dirs_frame, width=55)
        self._e_destino.grid(row=1, column=1, **p)
        ttk.Button(dirs_frame, text="📂",
                   command=lambda: self._pick_dir(self._e_destino)).grid(row=1, column=2, **p)

        # Clientes
        cli_frame = ttk.LabelFrame(f, text="Clientes  (palabra : NombreCarpeta — una por línea)")
        cli_frame.pack(fill="x", pady=(0, 8))

        self._txt_clients = tk.Text(cli_frame, height=8, width=70,
                                    font=("Consolas", 9), relief="flat",
                                    highlightthickness=1, highlightbackground="#ccc")
        scroll_c = ttk.Scrollbar(cli_frame, command=self._txt_clients.yview)
        self._txt_clients.configure(yscrollcommand=scroll_c.set)
        self._txt_clients.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        scroll_c.pack(side="left", fill="y", pady=6)

        # Opciones
        opts = ttk.LabelFrame(f, text="Opciones")
        opts.pack(fill="x", pady=(0, 8))

        self._var_copy   = tk.BooleanVar(value=False)
        self._var_dryrun = tk.BooleanVar(value=False)
        self._var_tol    = tk.DoubleVar(value=0.75)

        ttk.Checkbutton(opts, text="Copiar (no mover)", variable=self._var_copy
                        ).pack(side="left", padx=12, pady=6)
        ttk.Checkbutton(opts, text="Modo simulación (sin tocar archivos)",
                        variable=self._var_dryrun
                        ).pack(side="left", padx=12)

        ttk.Label(opts, text="Tolerancia fuzzy:").pack(side="left", padx=(20, 4))
        ttk.Scale(opts, from_=0.5, to=1.0, variable=self._var_tol,
                  length=110, orient="horizontal").pack(side="left")
        self._lbl_tol = ttk.Label(opts, text="0.75", width=4)
        self._lbl_tol.pack(side="left")
        self._var_tol.trace_add("write",
            lambda *_: self._lbl_tol.config(text=f"{self._var_tol.get():.2f}"))

        # Botón iniciar
        btn_frame = ttk.Frame(f)
        btn_frame.pack(fill="x", pady=4)
        self._btn_start = ttk.Button(btn_frame, text="▶  Iniciar organización",
                                     style="Action.TButton", command=self._start)
        self._btn_start.pack(pady=4)

        # Progreso
        self._progress = ttk.Progressbar(f, length=500, mode="determinate")
        self._progress.pack(fill="x", pady=(4, 2))

        self._lbl_current = ttk.Label(f, text="", foreground="#666")
        self._lbl_current.pack()

        self._lbl_status = ttk.Label(f, text="Esperando acción...",
                                     foreground="#1565c0",
                                     font=("Segoe UI", 9, "bold"))
        self._lbl_status.pack(pady=4)

    def _build_tab_cats(self):
        f = self._tab_cats
        ttk.Label(f, text="Palabras clave de categorías  (palabra : NombreCarpeta — una por línea)",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))

        frame = ttk.Frame(f)
        frame.pack(fill="both", expand=True)

        self._txt_cats = tk.Text(frame, font=("Consolas", 9), relief="flat",
                                 highlightthickness=1, highlightbackground="#ccc")
        scroll = ttk.Scrollbar(frame, command=self._txt_cats.yview)
        self._txt_cats.configure(yscrollcommand=scroll.set)
        self._txt_cats.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        ttk.Label(f, text="Los cambios se guardan automáticamente al iniciar.",
                  foreground="#888").pack(pady=6)

        ttk.Button(f, text="Restaurar categorías por defecto",
                   command=self._reset_cats).pack()

    def _build_tab_log(self):
        f = self._tab_log
        cols = ("Archivo", "Cliente", "Categoría", "Destino", "Estado")
        self._tree = ttk.Treeview(f, columns=cols, show="headings",
                                  height=18, selectmode="browse")

        widths = {"Archivo": 160, "Cliente": 120, "Categoría": 110,
                  "Destino": 240, "Estado": 80}
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=widths[col], minwidth=60)

        self._tree.tag_configure("ok",  foreground="#2e7d32")
        self._tree.tag_configure("err", foreground="#c62828")
        self._tree.tag_configure("sim", foreground="#e65100")

        vsb = ttk.Scrollbar(f, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(f, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=6)
        ttk.Button(btn_frame, text="💾 Exportar CSV",
                   command=self._export_csv).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑 Limpiar",
                   command=self._clear_log).pack(side="left", padx=6)

    # ── Helpers ──────────────────────────────────────────────

    def _pick_dir(self, entry: ttk.Entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def _reset_cats(self):
        self._txt_cats.delete("1.0", tk.END)
        default_text = "\n".join(f"{k} : {v}" for k, v in DEFAULT_CATEGORIES.items())
        self._txt_cats.insert(tk.END, default_text)

    def _load_saved_data(self):
        self._txt_clients.insert(tk.END, self._config.get("clients", ""))

        cats_saved = self._config.get("categories", "")
        if cats_saved:
            self._txt_cats.insert(tk.END, cats_saved)
        else:
            self._reset_cats()

        if "last_origen" in self._config:
            self._e_origen.insert(0, self._config["last_origen"])
        if "last_destino" in self._config:
            self._e_destino.insert(0, self._config["last_destino"])

    def _save_config(self):
        self._config.update({
            "clients":      self._txt_clients.get("1.0", tk.END).strip(),
            "categories":   self._txt_cats.get("1.0", tk.END).strip(),
            "last_origen":  self._e_origen.get(),
            "last_destino": self._e_destino.get(),
        })
        save_config(self._config)

    def _clear_log(self):
        self._tree.delete(*self._tree.get_children())
        self._log = []

    # ── Inicio de organización ────────────────────────────────

    def _start(self):
        if self._running:
            messagebox.showwarning("En proceso", "Ya hay una organización en curso.")
            return

        origen  = self._e_origen.get().strip()
        destino = self._e_destino.get().strip()

        if not os.path.isdir(origen) or not os.path.isdir(destino):
            messagebox.showerror("Error", "Seleccioná carpetas válidas para origen y destino.")
            return

        keywords = parse_kv(self._txt_clients.get("1.0", tk.END))
        if not keywords:
            messagebox.showerror("Error", "Ingresá al menos un cliente en el formato  'palabra : Carpeta'.")
            return

        categories = parse_kv(self._txt_cats.get("1.0", tk.END)) or DEFAULT_CATEGORIES

        self._save_config()
        self._clear_log()

        self._progress["value"] = 0
        self._lbl_status.config(text="Iniciando...")
        self._lbl_current.config(text="")
        self._btn_start.config(state="disabled")
        self._running = True

        callbacks = {
            "on_progress":  self._cb_progress,
            "on_file_done": self._cb_file_done,
            "on_error":     self._cb_error,
            "on_done":      self._cb_done,
        }

        threading.Thread(
            target=organize_files,
            args=(origen, destino, keywords, categories,
                  self._var_copy.get(), self._var_dryrun.get(),
                  self._var_tol.get(), callbacks),
            daemon=True
        ).start()

    # ── Callbacks thread-safe (via after) ─────────────────────

    def _cb_progress(self, processed: int, total: int, filename: str):
        def _update():
            pct = (processed / total * 100) if total else 0
            self._progress["value"] = pct
            self._lbl_current.config(text=f"⏳ {filename}")
            self._lbl_status.config(text=f"Progreso: {processed}/{total}  ({pct:.0f}%)")
        self.after(0, _update)

    def _cb_file_done(self, src: str, dest: str, client: str, category: str):
        def _update():
            tag = "sim" if self._var_dryrun.get() else "ok"
            icon = "🔵" if self._var_dryrun.get() else "✔"
            self._tree.insert("", "end", tags=(tag,),
                values=(os.path.basename(src), client, category, dest, icon + " OK"))
        self.after(0, _update)

    def _cb_error(self, filepath: str, msg: str):
        def _update():
            self._tree.insert("", "end", tags=("err",),
                values=(os.path.basename(filepath), "?", "?", "", f"✘ {msg}"))
        self.after(0, _update)

    def _cb_done(self, processed: int, errors: int, log: list):
        self._log = log
        def _update():
            self._progress["value"] = 100
            self._lbl_current.config(text="✅ Completado.")
            self._btn_start.config(state="normal")
            self._running = False
            mode = "[SIMULACIÓN] " if self._var_dryrun.get() else ""
            summary = f"{mode}Finalizó: {processed} archivos, {errors} errores."
            self._lbl_status.config(text=summary)
            icon = "ℹ️" if self._var_dryrun.get() else "✅"
            messagebox.showinfo("Listo", f"{icon} {summary}")
        self.after(0, _update)

    # ── Exportar CSV ──────────────────────────────────────────

    def _export_csv(self):
        if not self._log:
            messagebox.showwarning("Sin datos", "No hay registro para exportar.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f, fieldnames=["archivo", "cliente", "categoria", "destino", "estado"])
            writer.writeheader()
            writer.writerows(self._log)
        messagebox.showinfo("Exportado", f"CSV guardado en:\n{path}")


if __name__ == "__main__":
    app = OrganizerApp()
    app.mainloop()
