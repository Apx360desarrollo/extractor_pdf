import pdfplumber
import spacy
from spacy.matcher import Matcher
import json

def preprocess_text(file_path):
    """
    Extrae todo el texto del PDF y lo preprocesa.
    """
    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    return full_text.strip()

def extract_data_with_spacy(text):
    """
    Utiliza spaCy para extraer datos estructurados del texto.
    """
    # Inicializar el diccionario con todos los campos
    extracted_data = {
        "RFC": None,
        "CURP": None,
        "Nombre": None,
        "FechaInicioOperaciones": None,
        "EstatusPadron": None,
        "FechaUltimoCambioEstado": None,
        "Direccion": {
            "CodigoPostal": None,
            "TipoVialidad": None,
            "NombreVialidad": None,
            "NumeroExterior": None,
            "NumeroInterior": None,
            "Colonia": None,
            "Municipio": None,
            "Localidad": None,
            "Estado": None
        },
        "RegimenFiscal": None
    }

    # Normalizar el texto
    normalized_text = " ".join(text.split())

    # Extraer RFC y CURP
    try:
        if "RFC:" in normalized_text:
            extracted_data["RFC"] = normalized_text.split("RFC:")[1].split("CURP:")[0].strip()
        if "CURP:" in normalized_text:
            extracted_data["CURP"] = normalized_text.split("CURP:")[1].split("Nombre(s):")[0].strip()
    except Exception as e:
        print(f"Error al extraer RFC o CURP: {e}")

    # Extraer Nombre Completo
    try:
        nombre = normalized_text.split("Nombre(s):")[1].split("PrimerApellido:")[0].strip()
        primer_apellido = normalized_text.split("PrimerApellido:")[1].split("SegundoApellido:")[0].strip()
        segundo_apellido = normalized_text.split("SegundoApellido:")[1].split("Fechainiciodeoperaciones:")[0].strip()
        extracted_data["Nombre"] = f"{nombre} {primer_apellido} {segundo_apellido}"
    except Exception as e:
        print(f"Error al extraer Nombre Completo: {e}")

    # Extraer Fecha de Inicio de Operaciones y Estatus
    try:
        if "Fechainiciodeoperaciones:" in normalized_text:
            extracted_data["FechaInicioOperaciones"] = normalized_text.split("Fechainiciodeoperaciones:")[1].split("Estatusenelpadrón:")[0].strip()
        if "Estatusenelpadrón:" in normalized_text:
            extracted_data["EstatusPadron"] = normalized_text.split("Estatusenelpadrón:")[1].split("Fechadeúltimocambiodeestado:")[0].strip()
        if "Fechadeúltimocambiodeestado:" in normalized_text:
            extracted_data["FechaUltimoCambioEstado"] = normalized_text.split("Fechadeúltimocambiodeestado:")[1].split("NombreComercial:")[0].strip()
    except Exception as e:
        print(f"Error al extraer Fechas o Estatus: {e}")

    # Extraer Dirección
    try:
        direccion = extracted_data["Direccion"]
        if "CódigoPostal:" in normalized_text:
            direccion["CodigoPostal"] = normalized_text.split("CódigoPostal:")[1].split("TipodeVialidad:")[0].strip()
        if "TipodeVialidad:" in normalized_text:
            direccion["TipoVialidad"] = normalized_text.split("TipodeVialidad:")[1].split("NombredeVialidad:")[0].strip()
        if "NombredeVialidad:" in normalized_text:
            direccion["NombreVialidad"] = normalized_text.split("NombredeVialidad:")[1].split("NúmeroExterior:")[0].strip()
        if "NúmeroExterior:" in normalized_text:
            direccion["NumeroExterior"] = normalized_text.split("NúmeroExterior:")[1].split("NúmeroInterior:")[0].strip()
        if "NúmeroInterior:" in normalized_text:
            direccion["NumeroInterior"] = normalized_text.split("NúmeroInterior:")[1].split("NombredelaColonia:")[0].strip()
        if "NombredelaColonia:" in normalized_text:
            direccion["Colonia"] = normalized_text.split("NombredelaColonia:")[1].split("Nombre del Municipio o Demarcación Territorial:")[0].strip()
        if "Nombre del Municipio o Demarcación Territorial:" in normalized_text:
            direccion["Municipio"] = normalized_text.split("Nombre del Municipio o Demarcación Territorial:")[1].split("NombredelaLocalidad:")[0].strip()
        if "NombredelaLocalidad:" in normalized_text:
            direccion["Localidad"] = normalized_text.split("NombredelaLocalidad:")[1].split("NombredelaEntidadFederativa:")[0].strip()
        if "NombredelaEntidadFederativa:" in normalized_text:
            direccion["Estado"] = normalized_text.split("NombredelaEntidadFederativa:")[1].split("EntreCalle:")[0].strip()
    except Exception as e:
        print(f"Error al extraer Dirección: {e}")

    # Extraer Régimen Fiscal
    try:
        if "Regímenes:" in normalized_text:
            # Obtener la parte relevante del texto después de "Regímenes:"
            regimen_part = normalized_text.split("Regímenes:")[1].strip()
            
        # Buscar la posición de "Régimen" y capturar las palabras posteriores
        if "Régimen de" in regimen_part:
            # Extraer desde "Régimen de" hasta el siguiente marcador
            regimen_fiscal = regimen_part.split("Régimen de", 1)[1]
            # Detenernos antes de una palabra clave que no forme parte del régimen
            regimen_fiscal = regimen_fiscal.split("Obligaciones")[0].strip()
            # Detenernos antes de una palabra clave que no forme parte del régimen
            for stop_word in ["Fecha", "Obligaciones", ":", "Vencimiento"]:
                if stop_word in regimen_fiscal:
                    regimen_fiscal = regimen_fiscal.split(stop_word)[0].strip()
                    break  # Detenemos más búsqueda al encontrar el primer marcador
            # Eliminar cualquier patrón de fecha (formato dd/mm/aaaa)
            import re
            regimen_fiscal = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", "", regimen_fiscal).strip()    
            # Limpiar texto redundante
            extracted_data["RegimenFiscal"] = f"Régimen de {regimen_fiscal}"
    except Exception as e:
        print(f"Error al extraer Régimen Fiscal: {e}")

    return extracted_data


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]  # Ruta del PDF
        # Preprocesar texto del PDF
        text = preprocess_text(file_path)
        # Extraer datos estructurados con spaCy
        structured_data = extract_data_with_spacy(text)
        # Imprimir los datos extraídos en formato JSON
        print(json.dumps(structured_data, ensure_ascii=False, indent=4))
    else:
        print("Por favor, proporciona la ruta al archivo PDF como argumento.")
