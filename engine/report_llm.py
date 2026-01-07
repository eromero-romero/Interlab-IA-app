from openai import OpenAI

SYSTEM_PROMPT = """
Eres un generador de reportes clínicos tipo MIRA.

REGLAS:
- Usa SOLO los datos presentes en el JSON.
- NO inventes analitos, valores, unidades ni diagnósticos.
- Si falta información, indica N/E.
- No reemplaza consulta médica; sugiere correlación clínica.
- Estilo: claro, estructurado, con semáforos 🟢🟡🔴.
"""

def generate_report_with_gpt(metrics_json: dict, api_key: str, model: str = "gpt-4o-mini") -> str:
    client = OpenAI(api_key=api_key)

    user_prompt = f"""
Genera un reporte estilo MIRA basado ÚNICAMENTE en este JSON:

{metrics_json}

Secciones:
1) Datos del paciente
2) Índice de urgencia clínica (U0–U3) + explicación breve
3) Resumen ejecutivo: índice global, inflamación, edad metabólica
4) Risk score por sistema (si es N/E, explicarlo)
5) Interpretación general (sin diagnosticar)
6) Próximos pasos (3–5)
7) FAQ (4 preguntas)
"""

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )
    return response.output_text
