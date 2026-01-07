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

    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        st.error("Falta OPENAI_API_KEY en Secrets de Streamlit")
        st.stop()

    report = generate_report_with_gpt(metrics, api_key)

    st.subheader("🧾 Reporte generado")
    st.markdown(report)

    st.download_button("⬇️ Descargar reporte", data=report, file_name="reporte_interlab_ia.txt")
