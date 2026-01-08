from typing import Dict, Optional, Any, Tuple
import math

def flag(value: Optional[float], low: Optional[float], high: Optional[float]) -> str:
    """
    Semáforo:
    green = dentro
    yellow = leve fuera
    red = muy fuera
    gray = N/E
    """
    if value is None:
        return "gray"
    if low is None and high is None:
        return "gray"
    if low is not None and value < low:
        # qué tan lejos
        dist = (low - value) / (abs(low) + 1e-9)
        return "red" if dist > 0.15 else "yellow"
    if high is not None and value > high:
        dist = (value - high) / (abs(high) + 1e-9)
        return "red" if dist > 0.15 else "yellow"
    return "green"

def get(obs: Dict[str, Any], key_contains: str) -> Optional[float]:
    key_contains = key_contains.lower()
    for k, v in obs.items():
        if key_contains in k.lower():
            return getattr(v, "value", None)
    return None

def inflammation_index(obs: Dict[str, Any]) -> int:
    """
    0–100 (menor es mejor). Heurística:
    - PCR (si existe)
    - VSG / eritrosedimentación
    - leucocitos
    """
    esr = get(obs, "eritrosed") or get(obs, "vsg")
    crp = get(obs, "proteína c") or get(obs, "pcr")
    wbc = get(obs, "leucoc")

    score = 0.0
    if esr is not None:
        score += min(60, esr)  # 0–60
    if crp is not None:
        score += min(40, crp * 5)  # PCR 0–8 -> 0–40 aprox
    elif wbc is not None:
        score += max(0, min(40, (wbc - 7) * 6))  # leucocitos altos suben

    return int(max(0, min(100, score)))

def global_health_index(infl: int, red_flags: int) -> int:
    """
    0–100 (más es mejor).
    Penaliza inflamación y banderas rojas.
    """
    base = 90
    base -= int(infl * 0.5)
    base -= int(red_flags * 8)
    return int(max(0, min(100, base)))

def metabolic_age(age: int, obs: Dict[str, Any]) -> int:
    """
    MIRA es propietario; aquí hacemos tu versión:
    suma “años” según riesgo cardiometabólico/renal/inflamatorio.
    Calibrable para que te dé ~42 en el caso LDL alto.
    """
    if age is None:
        return None

    years = 0.0

    ldl = get(obs, "l d l") or get(obs, "ldl")
    tc  = get(obs, "colesterol sérico") or get(obs, "colesterol total")
    hdl = get(obs, "h d l") or get(obs, "hdl")
    a1c = get(obs, "hemoglobina glicosilada") or get(obs, "hba1c")
    tg  = get(obs, "triglic")
    egfr = get(obs, "tfg")  # si viene en el pdf
    crp = get(obs, "pcr") or get(obs, "proteína c")

    # LDL: principal (para que 37 -> ~42 cuando LDL ~174)
    if ldl is not None:
        if ldl >= 190: years += 7
        elif ldl >= 160: years += 5
        elif ldl >= 130: years += 3
        elif ldl >= 100: years += 1

    # Colesterol total
    if tc is not None:
        if tc >= 240: years += 2
        elif tc >= 200: years += 1

    # HDL bajo
    if hdl is not None:
        if hdl < 40: years += 2
        elif hdl < 50: years += 1

    # HbA1c
    if a1c is not None:
        if a1c >= 6.5: years += 6
        elif a1c >= 5.7: years += 3

    # Triglicéridos
    if tg is not None:
        if tg >= 200: years += 2
        elif tg >= 150: years += 1

    # eGFR bajo
    if egfr is not None:
        if egfr < 60: years += 6
        elif egfr < 90: years += 2

    # PCR alta
    if crp is not None:
        if crp > 10: years += 3
        elif crp > 3: years += 1

    return int(round(age + years))

def count_red_flags(obs: Dict[str, Any]) -> int:
    reds = 0
    for k, v in obs.items():
        low = getattr(v, "ref_low", None)
        high = getattr(v, "ref_high", None)
        val = getattr(v, "value", None)
        if flag(val, low, high) == "red":
            reds += 1
    return reds
