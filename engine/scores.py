from typing import Dict, Optional
from .parse_pdf import Obs

def cap01(x: float) -> float:
    return max(0.0, min(1.0, x))

def pick(obs: Dict[str, Obs], k: str) -> Optional[float]:
    o = obs.get(k)
    return None if o is None else o.value

def inflammation_index(obs: Dict[str, Obs]) -> Optional[int]:
    crp = pick(obs, "crp_mg_l")
    il6 = pick(obs, "il6_pg_ml")
    esr = pick(obs, "esr_mm_h")

    if crp is None and il6 is None and esr is None:
        return None

    p = cap01((crp or 0.0) / 5.0)
    i = cap01((il6 or 0.0) / 6.5)
    e = cap01((esr or 0.0) / 30.0)

    # MIRA-like: VSG pesa menos
    score = round(100 * (0.45*p + 0.45*i + 0.10*e))
    return int(max(0, min(100, score)))

def global_health_index(infl: Optional[int]) -> int:
    infl = infl or 0
    # Global simple por ahora (luego lo ampliamos)
    return int(max(0, min(100, round(100 - 0.6*infl))))

def urgency_level(infl: Optional[int]) -> str:
    s = infl or 0
    if s >= 80:
        return "U2 – consulta prioritaria"
    if s >= 60:
        return "U1 – consulta programable"
    return "U0 – sin urgencia"

def metabolic_age_conservative(age: Optional[float], infl: Optional[int]) -> Optional[int]:
    if age is None:
        return None
    # Conservador: igual a edad cronológica salvo inflamación muy alta
    return int(round(age + (2 if (infl or 0) >= 80 else 0)))

def build_metrics(obs: Dict[str, Obs]) -> dict:
    age = pick(obs, "age")
    sex = obs.get("sex").unit if obs.get("sex") else ""

    infl = inflammation_index(obs)
    global_idx = global_health_index(infl)
    urg = urgency_level(infl)
    met_age = metabolic_age_conservative(age, infl)

    return {
        "patient": {"age": age, "sex": sex},
        "indices": {
            "global_health": global_idx,
            "inflammation": infl,
            "metabolic_age": met_age
        },
        "system_scores": {
            "cardiometabolic": "N/E",
            "renal": "N/E",
            "hepatic": "N/E",
            "hematologic_inflammatory": "N/E"
        },
        "urgency": urg
    }
