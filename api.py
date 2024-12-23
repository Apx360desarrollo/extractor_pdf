from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from extract_pdf import preprocess_text, extract_data_spacy

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Crear la aplicación Flask
app = Flask(__name__)

# Configurar CORS para permitir solicitudes desde dominios específicos
CORS(app, resources={r"/*": {"origins": "https://bbygoodies.com"}})

@app.route('/extract', methods=['POST'])
def extract():
    """
    Endpoint para procesar un archivo PDF y extraer datos estructurados.
    """
    logger.info("Solicitud recibida en el endpoint /extract")

    # Verificar si el archivo está presente en la solicitud
    if 'file' not in request.files:
        logger.warning("No se encontró ningún archivo en la solicitud.")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("El nombre del archivo está vacío.")
        return jsonify({"error": "Empty file name"}), 400

    # Validar que el archivo sea un PDF
    if not file.filename.lower().endswith('.pdf'):
        logger.warning("El archivo no es un PDF válido.")
        return jsonify({"error": "Invalid file type. Only PDFs are allowed"}), 400

    try:
        logger.info("Procesando el archivo PDF.")
        text = preprocess_text(file)

        if not text.strip():
            logger.error("El texto extraído del PDF está vacío. Verifica el archivo.")
            return jsonify({"error": "El PDF no contiene texto legible"}), 400

        logger.debug(f"Texto extraído: {text[:500]}...")  # Mostrar un fragmento del texto extraído

        # Extraer datos usando el extractor
        data = extract_data_spacy(text)

        logger.info("Datos extraídos correctamente.")
        return jsonify(data), 200

    except ValueError as ve:
        logger.error(f"Error de valor: {ve}")
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        logger.error(f"Ocurrió un error inesperado: {e}")
        return jsonify({"error": "Ocurrió un error inesperado. Intenta nuevamente más tarde."}), 500

# Nota: No incluir app.run() aquí ya que Railway maneja la ejecución mediante Gunicorn.
