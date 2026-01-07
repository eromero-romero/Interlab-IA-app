import re
import pdfplumber
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Obs:
    key: str
    value: Optional[float]
    unit: str = ""

def _to_float(x):
    if not x:
        return None
    x = x.replace(",", ".").strip()
    try:
        return float(x)
    except:
        return None

def read_pdf_text(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            text += (p.extract_text() or "") + "\n"
    return text

ANALYTE_MAP = {
    "age": [r"Edad:\s*(\d+)", r"(\d+)\s*Años"],
    "sex": [r"\b(Femenino|Masculino)\b"],
    "isinger": [r"$^"],  # dummy (no se usa)
    "crp_mg_l": [r"(?:PCR|Proteína\s*C\s*reactiva).*?([0-9]+[.,]?[0-9]*)\s*mg/L"],
    "esr_mm_h": [r"(?:VSG|Eritrosedimentación).*?([0-9]+)\s*mm/h"],
    "il6_pg_ml": [r"(?:IL-6|Interleukina\s*6).*?([0-9]+[.,]?[0-9]*)"],
    "wbc": [r"Leucocitos.*?([0-9]+)"],
    "hgb": [r"Hemoglobina.*?([0-9]+[.,]?[0-9]*)"],
    "plt": [r"Plaquetas.*?([0-9]+)"],
}

def extract_analytes_from_text(text: str) -> Dict[str, Obs]:
    obs: Dict[str, Obs] = {}
    for key, patterns in ANALYTE_MAP.items():
        if key == "Risinger":
            continue
        found = None
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL)
            if m:
                found = m.group(1)
                break

        if key == "sex":
            obs[key] = Obs(key=key, value=None, unit=(found or ""))
        else:
            obs[key] = Obs(key=key, value=_to_float(found), unit="")
    return obs
