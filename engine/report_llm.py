from openai import OpenAI

SYSTEM_PROMPT = """
Eres un generador de reportes clínicos para Interlab IA.

REGLAS:
- Usa SOLO datos presentes en el JSON.
- NO inventes analitos, valores, unidades ni diagnósticos.
- Si falta info, escribe N/E.
- Da interpretación educativa (no diagnóstico).
- Incluye semáforo 🟢🟡🔴 basado en flags ya calculados.
- Finaliza con: 3-5 próximos pasos + 4-6 FAQ personalizadas.
"""

def generate_report_with_gpt(metrics_json: dict, api_key: str, model: str = "gpt-4o-mini") -> str:
    if not api_key:
        return "N/E: Falta OPENAI_API_KEY. Configura Secrets en Streamlit para habilitar IA."

    client = OpenAI(api_key=api_key)

    user_prompt = f"""
Genera un reporte clínico en español estilo Interlab IA, con secciones:

1) Datos del paciente
2) Índice de urgencia clínica (U0–U3) + explicación breve
3) Resumen ejecutivo: índice global, inflamación, edad metabólica
4) Riesgo por sistema (si falta info, N/E)
5) Hallazgos destacados con semáforos y valores
6) Interpretación general (sin diagnosticar)
7) Próximos pasos (3–5)
8) FAQ (4–6)

JSON (usa SOLO esto):
{metrics_json}
"""
    r = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return r.choices[0].message.content
