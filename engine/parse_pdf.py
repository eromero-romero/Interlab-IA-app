import re
import pdfplumber
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any, List

@dataclass
class Obs:
    key: str
    value: Optional[float]
    unit: str = ""
    ref_text: str = ""   # referencia como texto original
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None

def _to_float(x: str) -> Optional[float]:
    if x is None:
        return None
    x = x.strip()
    if not x:
        return None
    x = x.replace(",", ".")
    # quita miles tipo 4 590 000
    x = re.sub(r"(?<=\d)\s(?=\d{3}\b)", "", x)
    try:
        return float(x)
    except:
        return None

def _parse_range(ref: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Intenta sacar rangos tipo:
    '4.10 - 5.10'
    '0.00 - 30.00'
    'Hasta:4.50'
    '< 200'
    """
    if not ref:
        return None, None
    ref = ref.replace(",", ".")
    m = re.search(r"(-?\d+(\.\d+)?)\s*-\s*(-?\d+(\.\d+)?)", ref)
    if m:
        return _to_float(m.group(1)), _to_float(m.group(3))
    m = re.search(r"Hasta:?\s*(-?\d+(\.\d+)?)", ref, re.IGNORECASE)
    if m:
        return None, _to_float(m.group(1))
    m = re.search(r"<\s*(-?\d+(\.\d+)?)", ref)
    if m:
        return None, _to_float(m.group(1))
    m = re.search(r">=\s*(-?\d+(\.\d+)?)", ref)
    if m:
        return _to_float(m.group(1)), None
    return None, None

def read_pdf_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join([(p.extract_text() or "") for p in pdf.pages])

def extract_patient(text: str) -> Dict[str, Any]:
    # Nombre
    name = None
    m = re.search(r"Paciente:\s*([A-ZÁÉÍÓÚÑ,\s]+)\s+Identificación:", text)
    if m:
        name = m.group(1).strip()

    # Edad/Sexo (toma el primero que encuentre)
    age = None
    sex = None
    m = re.search(r"Edad:\s*(\d+)\s*Años\s+Sexo:\s*([A-Za-zÁÉÍÓÚÑ]+)", text)
    if m:
        age = int(m.group(1))
        sex = m.group(2).strip()
    return {"name": name, "age": age, "sex": sex}

def extract_analytes(text: str) -> Dict[str, Obs]:
    """
    Parser robusto para líneas tipo:
    'Colesterol Sérico 243 mg/dl ...'
    'Hematíes 4590000 mm3 4100000 - 5100000'
    'TSH 1.0947 µUI/mL 0.35 - 4.94'
    """
    obs: Dict[str, Obs] = {}

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        # Ignora encabezados
        if ln.upper().startswith("NOMBRE DE ESTUDIO"):
            continue

        # Caso con rango final numérico "a - b"
        m = re.match(r"^(.*?)[\s:]+([-+]?\d[\d\s.,]*)\s+([^\d\s]+(?:/[^\s]+)?)\s+(.+)$", ln)
        if not m:
            continue

        name = m.group(1).strip(" .:-")
        value = _to_float(m.group(2))
        unit = m.group(3).strip()
        ref_text = m.group(4).strip()

        # Filtra “name” demasiado largo basura
        if len(name) < 2 or value is None:
            continue

        ref_low, ref_high = _parse_range(ref_text)
        key = name

        obs[key] = Obs(
            key=key,
            value=value,
            unit=unit,
            ref_text=ref_text,
            ref_low=ref_low,
            ref_high=ref_high,
        )

    return obs
