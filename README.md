# 🗃️ Organizador de Documentos v2.0

> Aplicación de escritorio en Python que organiza automáticamente archivos por **cliente** y **tipo de documento**, con OCR integrado y una interfaz gráfica con pestañas.

> Desktop Python app that automatically organizes files by **client** and **document type**, with built-in OCR and a tabbed graphical interface.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white">
  <img alt="Tkinter" src="https://img.shields.io/badge/GUI-Tkinter-orange">
  <img alt="OCR" src="https://img.shields.io/badge/OCR-Tesseract-green">
  <img alt="Version" src="https://img.shields.io/badge/version-2.0-blue">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-lightgrey">
</p>

---

## ✨ Novedades v2.0 / What's New in v2.0

| # | Mejora / Improvement |
|---|---|
| 🐛 | **Bug fix:** fuzzy matching corregido — ahora compara palabra a palabra, no texto completo |
| 🔒 | **Thread-safe UI** — sin freezes ni crashes al procesar muchos archivos |
| 🧪 | **Modo simulación** — previsualiza qué haría el programa antes de mover nada |
| 📋 | **Registro en vivo** — tabla con colores (OK / Error / Simulación) + exportar a CSV |
| 🏷️ | **Categorías editables** — configurables desde la interfaz, sin tocar el código |
| ⚙️ | **Config persistente** — guarda clientes, categorías y carpetas en `config.json` |
| 📁 | **Copiar vs. mover** — opción para preservar los archivos originales |
| 🎚️ | **Slider de tolerancia** — ajustás cuán "flexible" es la búsqueda fuzzy (0.5–1.0) |
| 📄 | **Más formatos** — suma `.txt`, `.bmp`, `.tiff`, `.webp` a los ya soportados |
| 🌐 | **OCR bilingüe** — reconocimiento en español e inglés simultáneamente |

---

## 🚀 Características / Features

### 🇪🇸 Español
- Clasifica archivos por nombre de cliente (coincidencia exacta + fuzzy).
- Detecta el tipo de documento: facturas, cédulas, contratos, recibos, etc.
- Usa OCR (Tesseract) para leer texto en imágenes y PDFs escaneados.
- Interfaz con tres pestañas: **Organizar**, **Categorías**, **Registro**.
- Modo simulación para revisar antes de ejecutar.
- Log exportable a `.csv` compatible con Excel.
- Configuración guardada automáticamente en `config.json`.

### 🇬🇧 English
- Sorts files by client name using exact and fuzzy text matching.
- Detects document type: invoices, IDs, contracts, receipts, and more.
- Uses OCR (Tesseract) to read text from scanned images and PDFs.
- Three-tab interface: **Organize**, **Categories**, **Log**.
- Dry-run / simulation mode to preview actions before executing.
- Log exportable to Excel-compatible `.csv`.
- Settings auto-saved to `config.json`.

---

## 📁 Formatos soportados / Supported Formats

| Tipo / Type | Extensiones |
|---|---|
| Imágenes / Images | `.png` `.jpg` `.jpeg` `.bmp` `.tiff` `.webp` |
| Documentos / Documents | `.pdf` `.docx` `.txt` |

---

## 🧠 Requisitos / Requirements

- **Python 3.10+**
- **Tesseract OCR** instalado en el sistema

### Instalar dependencias / Install dependencies

```bash
pip install pytesseract pillow pdfplumber python-docx
```

### Instalar Tesseract

- **Windows:** descargá el instalador desde [github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)
- **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-spa`
- **macOS:** `brew install tesseract`

> Si Tesseract está instalado en una ruta distinta, editá esta línea en el script:
> ```python
> pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
> ```

---

## 💡 Uso / Usage

### 🇪🇸 Pasos

1. Ejecutá el script:
   ```bash
   python organizador_v2.py
   ```

2. En la pestaña **Organizar**:
   - Seleccioná la **carpeta de origen** (archivos desordenados).
   - Seleccioná la **carpeta de destino**.
   - Ingresá los clientes en el formato:
     ```
     palabra : NombreDeCarpeta
     juan perez : Cliente Juan Perez
     empresa xyz : Empresa XYZ
     ```

3. Configurá las **opciones**:
   - ☑ `Copiar` para no mover los originales.
   - ☑ `Modo simulación` para probar sin mover nada.
   - Ajustá el slider de **tolerancia fuzzy** según qué tan estricto querés el matching.

4. En la pestaña **Categorías** podés personalizar las palabras clave de cada tipo de documento.

5. Presioná **▶ Iniciar organización**.

6. Revisá el resultado en la pestaña **Registro** y exportá el log si necesitás.

### 🇬🇧 Steps

1. Run the script:
   ```bash
   python organizador_v2.py
   ```

2. In the **Organize** tab:
   - Select the **source folder** (unorganized files).
   - Select the **destination folder**.
   - Enter client names in this format:
     ```
     keyword : FolderName
     john doe : Client John Doe
     xyz company : Company XYZ
     ```

3. Configure **options**:
   - ☑ `Copy` to keep original files untouched.
   - ☑ `Simulation mode` to preview without moving anything.
   - Adjust the **fuzzy tolerance** slider to control matching strictness.

4. In the **Categories** tab, customize keyword → folder mappings for document types.

5. Click **▶ Start organization**.

6. Review results in the **Log** tab and export as CSV if needed.

---

## 📂 Estructura de salida / Output Structure

```
Destino/
├── Cliente Juan Perez/
│   ├── Facturas/
│   │   └── factura_enero.pdf
│   └── Contratos/
│       └── contrato_2024.docx
├── Empresa XYZ/
│   └── Cedulas/
│       └── cedula_frente.jpg
└── Desconocido/
    └── Otros/
        └── archivo_sin_match.png
```

---

## ⚙️ Configuración / Configuration

Al iniciar la organización, el programa guarda automáticamente un archivo `config.json`:

```json
{
  "clients": "juan perez : Cliente Juan Perez\nempresa xyz : Empresa XYZ",
  "categories": "factura : Facturas\ncontrato : Contratos",
  "last_origen": "C:/Documentos/Desordenados",
  "last_destino": "C:/Documentos/Organizados"
}
```

Este archivo se recarga cada vez que abrís la app.

---

## 🧰 Tecnologías / Technologies

| Librería | Uso |
|---|---|
| `tkinter` | Interfaz gráfica con pestañas |
| `pytesseract` | OCR — lectura de texto en imágenes |
| `pdfplumber` | Extracción de texto en PDFs |
| `python-docx` | Lectura de archivos `.docx` |
| `Pillow` | Procesamiento de imágenes |
| `difflib` | Fuzzy matching de nombres de clientes |
| `threading` | Procesamiento en segundo plano |
| `json` / `csv` | Config persistente y exportación de logs |

---

## 🧑‍💻 Autor / Author

Desarrollado por **Guwusoft** — [guwusoft.com](https://guwusoft.com) 🇵🇾  
Developed by **Guwusoft** — [guwusoft.com](https://guwusoft.com)
