# 🗃️ Organizador de Archivos en Python / Python File Organizer

🇪🇸 Aplicación de escritorio desarrollada en **Python** que organiza automáticamente archivos (PDF, Word e imágenes) por **cliente** y **tipo de documento**.  
Usa **OCR con Tesseract** para leer texto dentro de imágenes y documentos, y cuenta con una **interfaz gráfica amigable** creada con Tkinter.

🇬🇧 Desktop application built in **Python** that automatically organizes files (PDF, Word, and images) by **client** and **document type**.  
It uses **OCR with Tesseract** to read text inside images and documents, and includes a simple **Tkinter graphical interface**.

---

## 🚀 Características / Features

🇪🇸
- Clasifica archivos por nombre de cliente.
- Detecta el tipo de documento (facturas, cédulas, contratos, etc.).
- Usa OCR para leer texto dentro de imágenes o PDFs escaneados.
- Guarda los clientes definidos para futuros usos.
- Interfaz con barra de progreso y estados.

🇬🇧
- Sorts files automatically by client name.
- Detects document type (invoices, IDs, contracts, etc.).
- Uses OCR to extract text from scanned images or PDFs.
- Saves client definitions for later use.
- Includes a progress bar and status display.

---

## 🧠 Requisitos / Requirements

1. **Python 3.10+**
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   
3. Install Tesseract OCR

Download from: https://github.com/tesseract-ocr/tesseract

Update the path in the script if necessary:

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

💡 Uso / Usage

🇪🇸

Ejecutá el script:

python Organizador9.py


Seleccioná la carpeta de origen (archivos desordenados).

Seleccioná la carpeta de destino.

Ingresá los clientes en el formato:

palabra : Carpeta
juan perez : Cliente Juan Perez
empresa xyz : Empresa XYZ


Presioná Iniciar organización.

Los archivos se moverán automáticamente a las carpetas correspondientes:

Destino/
├── Cliente Juan Perez/
│   └── Facturas/
└── Empresa XYZ/
    └── Cedulas/


🇬🇧

Run the script:

python Organizador9.py


Choose the source folder (where unorganized files are located).

Choose the destination folder.

Enter client names in the following format:

keyword : Folder
john doe : Client John Doe
xyz company : Company XYZ


Click Start organization.

Files will be automatically moved into folders like:

Destination/
├── Client John Doe/
│   └── Invoices/
└── Company XYZ/
    └── IDs/

🧰 Tecnologías / Technologies

Python 3

Tkinter (GUI)

Pytesseract (OCR)

PdfPlumber

Python-docx

Pillow

🧑‍💻 Autor / Author

🇵🇾 Desarrollado por Guille Ruiz (Guwusoft)
💻 guwusoft.com

🇬🇧 Developed by Guille Ruiz (Guwusoft)
💻 guwusoft.com

