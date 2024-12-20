from flask import Flask, request, jsonify
from flask_cors import CORS
from pdfminer.high_level import extract_text
import os

app = Flask(__name__)
CORS(app)  # Permitir solicitudes de otros dominios para pruebas o integración.

def extract_pdf_data(file_path):
    """
    Extrae el texto completo de un archivo PDF.
    """
    try:
        # Extraer texto del PDF
        pdf_text = extract_text(file_path)
        if not pdf_text:
            return {"error": "El archivo PDF no contiene texto legible."}

        # Devolver el texto completo
        return {"text": pdf_text}

    except Exception as e:
        return {"error": f"Error al procesar el archivo PDF: {str(e)}"}

@app.route('/extract', methods=['POST'])
def extract():
    """
    Endpoint para procesar un archivo PDF enviado como POST.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró ningún archivo PDF.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo PDF.'}), 400

    # Guardar el archivo temporalmente en la carpeta /tmp
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)

    # Procesar el archivo y extraer datos
    app.logger.info(f"Archivo recibido: {file_path}")
    result = extract_pdf_data(file_path)
    os.remove(file_path)  # Eliminar el archivo temporal
    return jsonify(result)
    
    # Eliminar el archivo temporal para evitar acumular basura
    os.remove(file_path)
    
    # Devolver el resultado en formato JSON
    return jsonify(result)

if __name__ == '__main__':
    # Configurar el servidor para escuchar en todas las interfaces (localhost y red local)
    app.run(host='0.0.0.0', port=5000)
