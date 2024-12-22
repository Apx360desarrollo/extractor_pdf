from flask import Flask, request, jsonify
from flask_cors import CORS
from extractor import extract_data_with_spacy, preprocess_text
import logging

# Configurar logging para debug y producción
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar la aplicación Flask
app = Flask(__name__)

# Configurar CORS para permitir solo solicitudes desde dominios específicos
CORS(app, resources={r"/*": {"origins": "https://tusitio.com"}})

@app.route('/extract', methods=['POST'])
def extract():
    logger.info("Solicitud recibida en el endpoint /extract")

    # Verificar si el archivo fue enviado
    if 'file' not in request.files:
        logger.warning("No se encontró ningún archivo en la solicitud")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("El nombre del archivo está vacío")
        return jsonify({"error": "Empty file name"}), 400

    # Validar que el archivo sea un PDF
    if not file.filename.lower().endswith('.pdf'):
        logger.warning("El archivo no es un PDF válido")
        return jsonify({"error": "Invalid file type. Only PDFs are allowed"}), 400

    try:
        # Preprocesar el archivo PDF
        logger.info("Procesando el archivo PDF")
        text = preprocess_text(file)
        logger.debug(f"Texto extraído: {text[:100]}...")  # Solo muestra los primeros 100 caracteres

        # Extraer datos estructurados
        data = extract_data_with_spacy(text)
        logger.info("Datos extraídos correctamente")
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Ocurrió un error durante el procesamiento: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # No se debe usar en producción, usa Gunicorn
    app.run(debug=False)
