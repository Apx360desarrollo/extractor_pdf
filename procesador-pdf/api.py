from flask import Flask, request, jsonify
from flask_cors import CORS
from extractor import extract_data_with_spacy, preprocess_text

app = Flask(__name__)
CORS(app)

@app.route('/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty file name"}), 400

    try:
        # Preprocesar el archivo PDF
        text = preprocess_text(file)
        # Extraer datos estructurados
        data = extract_data_with_spacy(text)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
