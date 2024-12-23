from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import pdfplumber  # Asegúrate de que `pdfplumber` esté instalado
from extractor_fisicas import extract_data as extract_data_fisicas
from extractor_morales import extract_data as extract_data_morales

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurar CORS
CORS(app, resources={r"/*": {"origins": "https://bbygoodies.com"}})

def preprocess_text(file):
    """
    Extrae todo el texto del PDF.
    """
    with pdfplumber.open(file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    return full_text.strip()

def determine_type(text):
    """
    Determina si el PDF es de una persona física o moral.
    """
    return "moral" if "Denominación/RazónSocial:" in text else "fisica"

@app.route('/extract', methods=['POST'])
def extract():
    logger.info("Solicitud recibida en el endpoint /extract")

    # Verificar archivo en la solicitud
    if 'file' not in request.files:
        logger.warning("No se encontró ningún archivo en la solicitud")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("El nombre del archivo está vacío")
        return jsonify({"error": "Empty file name"}), 400

    # Validar tipo de archivo
    if not file.filename.lower().endswith('.pdf'):
        logger.warning("El archivo no es un PDF válido")
        return jsonify({"error": "Invalid file type. Only PDFs are allowed"}), 400

    try:
        logger.info("Procesando el archivo PDF")
        text = preprocess_text(file)
        logger.debug(f"Texto extraído: {text[:100]}...")

        # Determinar si es persona física o moral
        tipo = determine_type(text)
        logger.info(f"Tipo determinado: {tipo}")

        # Llamar al extractor correspondiente
        if tipo == "moral":
            data = extract_data_morales(text)
        else:
            data = extract_data_fisicas(text)

        logger.info("Datos extraídos correctamente")
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Ocurrió un error durante el procesamiento: {e}")
        return jsonify({"error": str(e)}), 500

# No incluir app.run() aquí; Railway utiliza Gunicorn para ejecutar la aplicación
