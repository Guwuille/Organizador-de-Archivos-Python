import os
import shutil
import threading
import pytesseract
import warnings
from PIL import Image
import pdfplumber
from docx import Document
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from difflib import get_close_matches

warnings.filterwarnings("ignore")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

categorias = {
    "cedula": "Cedulas",
    "dni": "Cedulas",
    "contrato": "Contratos",
    "factura": "Facturas",
    "licencia": "Licencias",
    "titulo": "Titulos",
    "recibo": "Recibos",
    "certificado": "Certificados"
}

def extract_text_from_image(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path))
    except Exception:
        return ""

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass
    return text

def extract_text_from_docx(docx_path):
    text = ""
    try:
        doc = Document(docx_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception:
        pass
    return text

def extract_text(file_path):
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file_path)
    elif file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    return ""

# ✅ Fuzzy matching incluido
def get_client_name(text, keywords_dict, tolerance=0.7):
    text = text.lower()

    # 1. Buscar coincidencia exacta por partes
    for keyword, folder_name in keywords_dict.items():
        parts = keyword.strip().lower().split()
        if all(part in text for part in parts):
            return folder_name

    # 2. Si no hay coincidencia exacta, usar fuzzy matching
    posibles = list(keywords_dict.keys())
    coincidencias = get_close_matches(text, posibles, n=1, cutoff=tolerance)
    if coincidencias:
        return keywords_dict[coincidencias[0]]

    return "Desconocido"

def get_category(text):
    text = text.lower()
    for keyword, category_name in categorias.items():
        if keyword in text:
            return category_name
    return "Otros"

def move_file(file_path, base_dir, client_name, category):
    client_dir = os.path.join(base_dir, client_name)
    category_dir = os.path.join(client_dir, category)
    os.makedirs(category_dir, exist_ok=True)

    destination = os.path.join(category_dir, os.path.basename(file_path))
    if os.path.exists(destination):
        base, ext = os.path.splitext(destination)
        counter = 1
        while os.path.exists(destination):
            destination = f"{base}_{counter}{ext}"
            counter += 1
    shutil.move(file_path, destination)

def parse_keywords(texto):
    lines = texto.strip().split("\n")
    keywords = {}
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            keywords[k.strip().lower()] = v.strip()
    return keywords

def organize_files_gui(source_dir, dest_dir, keywords_dict, status_label, progress_bar, current_file_label):
    all_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            all_files.append(os.path.join(root, file))

    total = len(all_files)
    processed = 0

    for file_path in all_files:
        file_name = os.path.basename(file_path)
        current_file_label.config(text=f"Procesando: {file_name}")
        texto_extraido = extract_text(file_path)
        extracted_text = (file_name + " " + texto_extraido).lower()

        client_name = get_client_name(extracted_text, keywords_dict)
        category = get_category(extracted_text)
        move_file(file_path, dest_dir, client_name, category)

        processed += 1
        progress_bar['value'] = (processed / total) * 100
        status_label.config(text=f"Organizado: {processed}/{total} archivos")

    current_file_label.config(text="Finalizado.")
    status_label.config(text=f"¡Organización completa! Total: {processed} archivos.")
    messagebox.showinfo("Hecho", "¡La organización ha finalizado!")

# ---------------- INTERFAZ ----------------
def start_gui():
    def seleccionar_carpeta(entry):
        ruta = filedialog.askdirectory()
        if ruta:
            entry.delete(0, tk.END)
            entry.insert(0, ruta)

    def iniciar_organizacion():
        origen = entry_origen.get()
        destino = entry_destino.get()
        raw_keywords = txt_keywords.get("1.0", tk.END)
        if not os.path.isdir(origen) or not os.path.isdir(destino):
            messagebox.showerror("Error", "Seleccioná carpetas válidas.")
            return
        keywords_dict = parse_keywords(raw_keywords)
        if not keywords_dict:
            messagebox.showerror("Error", "Ingresá al menos un nombre de cliente.")
            return

        guardar_clientes_txt(raw_keywords)

        progress_bar['value'] = 0
        status_label.config(text="Iniciando...")
        current_file_label.config(text="")
        threading.Thread(target=organize_files_gui, args=(
            origen, destino, keywords_dict, status_label, progress_bar, current_file_label), daemon=True).start()

    def cargar_clientes_txt():
        if os.path.exists("clientes.txt"):
            with open("clientes.txt", "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def guardar_clientes_txt(texto):
        with open("clientes.txt", "w", encoding="utf-8") as f:
            f.write(texto)

    ventana = tk.Tk()
    ventana.title("Organizador de Archivos por Cliente y Tipo de Documento")
    ventana.geometry("650x550")
    ventana.resizable(False, False)

    tk.Label(ventana, text="Carpeta de origen:").pack(pady=5)
    entry_origen = tk.Entry(ventana, width=60)
    entry_origen.pack()
    tk.Button(ventana, text="Buscar origen", command=lambda: seleccionar_carpeta(entry_origen)).pack()

    tk.Label(ventana, text="Carpeta destino:").pack(pady=5)
    entry_destino = tk.Entry(ventana, width=60)
    entry_destino.pack()
    tk.Button(ventana, text="Buscar destino", command=lambda: seleccionar_carpeta(entry_destino)).pack()

    tk.Label(ventana, text="Nombres de clientes (formato: palabra : Carpeta):").pack(pady=5)
    txt_keywords = tk.Text(ventana, height=7, width=70)
    txt_keywords.insert(tk.END, cargar_clientes_txt())
    txt_keywords.pack()

    tk.Button(ventana, text="Iniciar organización", command=iniciar_organizacion, bg="#4CAF50", fg="white").pack(pady=10)

    progress_bar = ttk.Progressbar(ventana, length=400, mode="determinate")
    progress_bar.pack(pady=10)

    current_file_label = tk.Label(ventana, text="", fg="gray")
    current_file_label.pack()

    status_label = tk.Label(ventana, text="Esperando acción...", fg="blue")
    status_label.pack(pady=5)

    ventana.mainloop()

start_gui()
