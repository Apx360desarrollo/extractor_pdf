import pdfplumber
import spacy
import json
import re
import logging

# Cargar modelo spaCy
nlp = spacy.blank("es")

# Configuración del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def preprocess_text(file_path):
    """
    Extrae todo el texto del PDF y lo preprocesa.
    """
    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    return full_text.strip()

def safe_search(pattern, text):
    """
    Función para realizar búsquedas seguras con re.search.
    """
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

def extract_direccion(text, is_moral):
    """
    Extraer la dirección dependiendo de si es persona moral o física.
    """
    direccion = {
        "CodigoPostal": None,
        "TipoVialidad": None,
        "NombreVialidad": None,
        "NumeroExterior": None,
        "NumeroInterior": None,
        "Colonia": None,
        "Localidad": None,
        "Municipio": None,
        "Estado": None,
    }

    if is_moral:
        # Extracción para persona moral
        direccion["CodigoPostal"] = safe_search(r"CódigoPostal:\s*(\d+)", text)
        direccion["TipoVialidad"] = safe_search(r"TipodeVialidad:\s*(.*?)\s*NombredeVialidad:", text)
        direccion["NombreVialidad"] = safe_search(r"NombredeVialidad:\s*(.*?)\s*NúmeroExterior:", text)
        direccion["NumeroExterior"] = safe_search(r"NúmeroExterior:\s*(\d+)", text)
        direccion["NumeroInterior"] = safe_search(r"NúmeroInterior:\s*(.*?)\s*NombredelaColonia:", text)
        direccion["Colonia"] = safe_search(r"NombredelaColonia:\s*(.*?)\s*(NombredelaLocalidad|NombredelMunicipiooDemarcaciónTerritorial):", text)

        # Procesar Localidad
        if "NombredelaLocalidad:" in text:
            localidad_segment = text.split("NombredelaLocalidad:")[1].split("NombredelaEntidadFederativa:")[0].strip()
            if "NombredelMunicipiooDemarcaciónTerritorial:" in localidad_segment:
                localidad_clean = localidad_segment.split("NombredelMunicipiooDemarcaciónTerritorial:")[0].strip()
                direccion["Localidad"] = localidad_clean if localidad_clean else None
            else:
                direccion["Localidad"] = localidad_segment.strip()
        else:
            direccion["Localidad"] = None

        # Procesar Municipio
        direccion["Municipio"] = safe_search(r"NombredelMunicipiooDemarcaciónTerritorial:\s*(.*?)\s*NombredelaEntidadFederativa:", text)

        direccion["Estado"] = safe_search(r"NombredelaEntidadFederativa:\s*(.*?)\s*EntreCalle:", text)

    else:
        # Extracción para persona física
        direccion["CodigoPostal"] = safe_search(r"CódigoPostal:\s*(\d+)", text)
        direccion["TipoVialidad"] = safe_search(r"TipodeVialidad:\s*(.*?)\s*NombredeVialidad:", text)
        direccion["NombreVialidad"] = safe_search(r"NombredeVialidad:\s*(.*?)\s*NúmeroExterior:", text)
        direccion["NumeroExterior"] = safe_search(r"NúmeroExterior:\s*(\d+)", text)
        direccion["NumeroInterior"] = safe_search(r"NúmeroInterior:\s*(.*?)\s*NombredelaColonia:", text)
        direccion["Colonia"] = safe_search(r"NombredelaColonia:\s*(.*?)\s*Nombre del Municipio o Demarcación Territorial:", text)

        # Procesar Localidad
        if "NombredelaLocalidad:" in text:
            localidad_segment = text.split("NombredelaLocalidad:")[1].split("NombredelaEntidadFederativa:")[0].strip()
            if "Nombre del Municipio o Demarcación Territorial:" in localidad_segment:
                localidad_clean = localidad_segment.split("Nombre del Municipio o Demarcación Territorial:")[0].strip()
                direccion["Localidad"] = localidad_clean if localidad_clean else None
            else:
                direccion["Localidad"] = localidad_segment.strip()
        else:
            direccion["Localidad"] = None

        # Procesar Municipio
        direccion["Municipio"] = safe_search(r"Nombre del Municipio o Demarcación Territorial:\s*(.*?)\s*(NombredelaLocalidad|NombredelaEntidadFederativa):", text)

        # Revisar si Localidad tiene datos redundantes y moverlos a Municipio
        if direccion["Localidad"]:
            localidad_lines = direccion["Localidad"].split("\n")
            if len(localidad_lines) > 1:
                # Mover cualquier parte redundante de Localidad al Municipio
                direccion["Localidad"] = localidad_lines[0].strip()
                direccion["Municipio"] = f"{direccion['Municipio']} {localidad_lines[1].strip()}".strip()

        direccion["Estado"] = safe_search(r"NombredelaEntidadFederativa:\s*(.*?)\s*EntreCalle:", text)

    return direccion



def extract_data_spacy(text):
    """
    Utiliza spaCy para extraer datos estructurados del texto.
    """
    extracted_data = {
        "RFC": None,
        "CURP": None,
        "Nombre": None,
        "DenominacionRazonSocial": None,
        "RegimenCapital": None,
        "FechaInicioOperaciones": None,
        "EstatusPadron": None,
        "FechaUltimoCambioEstado": None,
        "Direccion": {},
        "RegimenFiscal": None,
    }

    # Determinar si es persona moral o física
    is_moral = "Denominación/RazónSocial:" in text

    # Extraer datos básicos
    extracted_data["RFC"] = safe_search(r"RFC:\s*([A-Z0-9]+)", text)
    
    if is_moral:
        # Solo para personas morales
        extracted_data["DenominacionRazonSocial"] = safe_search(r"Denominación/RazónSocial:\s*(.*?)\s*RégimenCapital:", text)
        extracted_data["RegimenCapital"] = safe_search(r"RégimenCapital:\s*(.*?)\s*NombreComercial:", text)
    else:
        # Solo para personas físicas
        extracted_data["CURP"] = safe_search(r"CURP:\s*([A-Z0-9]+)", text)
        nombre = safe_search(r"Nombre\(s\):\s*(.*?)\s*PrimerApellido:", text)
        primer_apellido = safe_search(r"PrimerApellido:\s*(.*?)\s*SegundoApellido:", text)
        segundo_apellido = safe_search(r"SegundoApellido:\s*(.*?)\s*Fechainiciodeoperaciones:", text)
        
        if nombre and primer_apellido and segundo_apellido:
            extracted_data["Nombre"] = f"{nombre} {primer_apellido} {segundo_apellido}"
        else:
            logger.info("Faltan datos para el Nombre Completo en persona física.")
            extracted_data["Nombre"] = None

    # Fecha y estado
    extracted_data["FechaInicioOperaciones"] = safe_search(r"Fechainiciodeoperaciones:\s*(.*?)\s*Estatusenelpadrón:", text)
    extracted_data["EstatusPadron"] = safe_search(r"Estatusenelpadrón:\s*(.*?)\s*Fechadeúltimocambiodeestado:", text)
    extracted_data["FechaUltimoCambioEstado"] = safe_search(r"Fechadeúltimocambiodeestado:\s*(.*?)\s*(NombreComercial|Datos del domicilio registrado)", text)

    # Dirección
    extracted_data["Direccion"] = extract_direccion(text, is_moral)

    # Régimen Fiscal
    regimen_fiscal_match = re.search(r"Regímenes:.*?Régimen\s*(.*?)\s*Obligaciones:", text, re.DOTALL)
    if regimen_fiscal_match:
        regimen_fiscal = regimen_fiscal_match.group(1)
        regimen_fiscal = re.sub(r"\bFecha Inicio Fecha Fin\b", "", regimen_fiscal)
        regimen_fiscal = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", "", regimen_fiscal)  # Eliminar fechas
        extracted_data["RegimenFiscal"] = regimen_fiscal.strip()

    return extracted_data

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        text = preprocess_text(file_path)
        data = extract_data_spacy(text)
        print(json.dumps(data, ensure_ascii=False, indent=4))
    else:
        print("Por favor, proporciona la ruta al archivo PDF como argumento.")
