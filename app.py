import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tempfile
import streamlit as st

from engine.parse_pdf import read_pdf_text, extract_analytes_from_text
from engine.scores import build_metrics
from engine.report_llm import generate_report_with_gpt


st.set_page_config(page_title="Interlab IA – Reporte clínico", layout="wide")
st.title("🧠 Interlab IA – Reporte clínico")
st.caption("Reporte automatizado basado en resultados de laboratorio. No reemplaza la valoración médica.")

pdf = st.file_uploader("📄 Subir PDF de laboratorio", type=["pdf"])
raw_text = ""

if pdf:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf.read())
        pdf_path = tmp.name
    raw_text = read_pdf_text(pdf_path)
    st.success("PDF leído correctamente")

if st.button("🚀 Generar reporte"):
    if not raw_text.strip():
        st.error("Primero sube un PDF")
        st.stop()

    obs = extract_analytes_from_text(raw_text)
    metrics = build_metrics(obs)

    st.subheader("🔎 Datos analizados (auditoría)")
    st.json(metrics)

    report = generate_report_with_gpt(metrics)
    st.markdown(report)
    from engine.pdf_html import render_pdf_from_template

def urgency_badge(code: str):
    code = (code or "U1").upper().strip()
    if code == "U0":
        return ("ok", "sin urgencia")
    if code == "U1":
        return ("warn", "consulta programable")
    if code == "U2":
        return ("warn", "consulta prioritaria")
    return ("bad", "valoración urgente")

# Contexto para plantilla
u_code = metrics.get("urgency", {}).get("code", "U1")
u_text = metrics.get("urgency", {}).get("text", "N/E")
u_class, u_label = urgency_badge(u_code)

context = {
    "name": metrics.get("patient", {}).get("name", "N/E"),
    "age": metrics.get("patient", {}).get("age", "N/E"),
    "sex": metrics.get("patient", {}).get("sex", "N/E"),

    "global_score": metrics.get("scores", {}).get("global", "N/E"),
    "inflam_score": metrics.get("scores", {}).get("inflammation", "N/E"),
    "metabolic_age": metrics.get("scores", {}).get("metabolic_age", "N/E"),

    "urgency_code": u_code,
    "urgency_label": u_label,
    "urgency_class": u_class,
    "urgency_text": u_text,

    "systems": [
        {"system": "Cardiometabólico", "score": metrics.get("scores", {}).get("cardio", "N/E")},
        {"system": "Renal", "score": metrics.get("scores", {}).get("renal", "N/E")},
        {"system": "Hepático", "score": metrics.get("scores", {}).get("hepatic", "N/E")},
        {"system": "Hematológico e inflamatorio", "score": metrics.get("scores", {}).get("hemo_inflam", "N/E")},
    ],

    "interpretation": metrics.get("narrative", {}).get("interpretation", report),
    "next_steps": metrics.get("narrative", {}).get("next_steps", []),
    "faqs": metrics.get("narrative", {}).get("faqs", []),
}

pdf_bytes = render_pdf_from_template(context)

st.download_button(
    "⬇️ Descargar PDF (Interlab IA)",
    data=pdf_bytes,
    file_name="reporte_interlab_ia.pdf",
    mime="application/pdf",
)

