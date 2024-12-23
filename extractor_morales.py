import pdfplumber
import json
import re

def preprocess_text(file_path):
    """
    Extrae todo el texto del PDF y lo preprocesa.
    """
    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    return full_text.strip()

def extract_data(text):
    """
    Extrae datos estructurados del texto procesado.
    """
    extracted_data = {
        "RFC": None,
        "DenominacionRazonSocial": None,
        "RegimenCapital": None,
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
            "Localidad": None,
            "Municipio": None,
            "Estado": None
        },
        "RegimenFiscal": None
    }

    # Normalizar el texto
    normalized_text = " ".join(text.split())

    try:
        if "RFC:" in normalized_text:
            extracted_data["RFC"] = normalized_text.split("RFC:")[1].split("Denominación/RazónSocial:")[0].strip()
        if "Denominación/RazónSocial:" in normalized_text:
            extracted_data["DenominacionRazonSocial"] = normalized_text.split("Denominación/RazónSocial:")[1].split("RégimenCapital:")[0].strip()
        if "RégimenCapital:" in normalized_text:
            extracted_data["RegimenCapital"] = normalized_text.split("RégimenCapital:")[1].split("NombreComercial:")[0].strip()
        if "Fechainiciodeoperaciones:" in normalized_text:
            extracted_data["FechaInicioOperaciones"] = normalized_text.split("Fechainiciodeoperaciones:")[1].split("Estatusenelpadrón:")[0].strip()
        if "Estatusenelpadrón:" in normalized_text:
            extracted_data["EstatusPadron"] = normalized_text.split("Estatusenelpadrón:")[1].split("Fechadeúltimocambiodeestado:")[0].strip()
        if "Fechadeúltimocambiodeestado:" in normalized_text:
            extracted_data["FechaUltimoCambioEstado"] = normalized_text.split("Fechadeúltimocambiodeestado:")[1].split("Datos del domicilio registrado")[0].strip()

        # Dirección
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
        # Extraer Localidad
        if "NombredelaLocalidad:" in normalized_text:
            localidad_segment = normalized_text.split("NombredelaLocalidad:")[1].split("NombredelaEntidadFederativa:")[0].strip()
            if "NombredelMunicipiooDemarcaciónTerritorial:" not in localidad_segment:
                extracted_data["Direccion"]["Localidad"] = localidad_segment
            else:
                localidad_clean = localidad_segment.split("NombredelMunicipiooDemarcaciónTerritorial:")[0].strip()
                extracted_data["Direccion"]["Localidad"] = localidad_clean if localidad_clean else None
            print(f"DEBUG - Localidad procesada: {extracted_data['Direccion']['Localidad']}")
        else:
            print("DEBUG - NombredelaLocalidad no encontrado.")
            extracted_data["Direccion"]["Localidad"] = None

        # Extraer Colonia
        if "NombredelaColonia:" in normalized_text:
            colonia_segment = normalized_text.split("NombredelaColonia:")[1].split("NombredelMunicipiooDemarcaciónTerritorial:")[0].strip()
            colonia_clean = colonia_segment.split("NombredelaLocalidad:")[0].strip()
            extracted_data["Direccion"]["Colonia"] = colonia_clean
            print(f"DEBUG - Colonia procesada: {extracted_data['Direccion']['Colonia']}")

        # Extraer Municipio
        if "NombredelMunicipiooDemarcaciónTerritorial:" in normalized_text:
            municipio_segment = normalized_text.split("NombredelMunicipiooDemarcaciónTerritorial:")[1].split("NombredelaEntidadFederativa:")[0].strip()
            extracted_data["Direccion"]["Municipio"] = municipio_segment
            print(f"DEBUG - Municipio procesado: {extracted_data['Direccion']['Municipio']}")

        # Extraer Estado
        if "NombredelaEntidadFederativa:" in normalized_text:
            estado_segment = normalized_text.split("NombredelaEntidadFederativa:")[1].split("EntreCalle:")[0].strip()
            extracted_data["Direccion"]["Estado"] = estado_segment

        # Extraer Régimen Fiscal
        if "Regímenes:" in normalized_text:
            regimen_part = normalized_text.split("Regímenes:")[1].strip()
            if "Régimen" in regimen_part:
                regimen_fiscal = regimen_part.split("Régimen", 1)[1]
                regimen_fiscal = regimen_fiscal.replace("Fecha Inicio Fecha Fin", "").strip()
                for stop_word in ["Obligaciones", "Descripción", "Susdatos"]:
                    if stop_word in regimen_fiscal:
                        regimen_fiscal = regimen_fiscal.split(stop_word)[0].strip()
                        break
                regimen_fiscal = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", "", regimen_fiscal).strip()
                extracted_data["RegimenFiscal"] = regimen_fiscal
    except Exception as e:
        print(f"Error al extraer datos: {e}")

    return extracted_data

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        text = preprocess_text(file_path)
        data = extract_data(text)
        print(json.dumps(data, ensure_ascii=False, indent=4))
    else:
        print("Por favor, proporciona la ruta al archivo PDF como argumento.")
