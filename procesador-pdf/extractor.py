import pdfplumber
import json

def extract_pdf_text(file_path):
    """
    Extrae todo el texto del PDF sin procesarlo.
    """
    try:
        # Abrir y leer el archivo PDF con pdfplumber
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"  # Añadir salto de línea entre páginas

        if not full_text.strip():
            return {"error": "El archivo PDF no contiene texto legible."}

        return {"text": full_text.strip()}  # Devolver el texto completo

    except Exception as e:
        return {"error": f"Error al procesar el archivo PDF: {str(e)}"}

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]  # Ruta del PDF
        result = extract_pdf_text(file_path)
        print(json.dumps(result, ensure_ascii=False, indent=4))  # Imprimir en formato JSON
    else:
        print("Por favor, proporciona la ruta al archivo PDF como argumento.")
