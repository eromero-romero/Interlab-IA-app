import streamlit as st
import tempfile
from engine.parse_pdf import read_pdf_text, extract_patient, extract_analytes
from engine.scores import inflammation_index, count_red_flags, global_health_index, metabolic_age, flag
from engine.report_llm import generate_report_with_gpt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def build_metrics(patient, obs):
    infl = inflammation_index(obs)
    reds = count_red_flags(obs)
    ghi = global_health_index(infl, reds)
    met_age = metabolic_age(patient.get("age"), obs)

    # urgencia simple (heurística): red flags -> U2/U3, si no -> U0/U1
    if reds >= 3:
        urg = "U2 - consulta prioritaria"
    elif reds >= 1:
        urg = "U1 - consulta programable"
    else:
        urg = "U0 - sin urgencia"

    # analitos listos para tabla
    analytes = []
    for k, v in obs.items():
        analytes.append({
            "name": k,
            "value": v.value,
            "unit": v.unit,
            "ref": v.ref_text,
            "flag": flag(v.value, v.ref_low, v.ref_high),
        })

    return {
        "patient": patient,
        "indices": {
            "global_health": ghi,
            "inflammation": infl,
            "metabolic_age": met_age,
        },
        "urgency": urg,
        "analytes": analytes,
    }

def make_pdf_bytes(title: str, report_text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    y = h - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, title)
    y -= 30
    c.setFont("Helvetica", 10)

    for line in report_text.splitlines():
        if y < 60:
            c.showPage()
            y = h - 50
            c.setFont("Helvetica", 10)
        c.drawString(40, y, line[:110])
        y -= 14

    c.save()
    return buf.getvalue()

st.set_page_config(page_title="Interlab IA - Reporte clínico", layout="wide")
st.title("🧠 Interlab IA – Reporte clínico")
st.caption("Reporte automatizado basado en resultados de laboratorio. No reemplaza valoración médica.")

pdf = st.file_uploader("📄 Subir PDF de laboratorio", type=["pdf"])

if pdf:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf.read())
        pdf_path = tmp.name

    raw_text = read_pdf_text(pdf_path)
    patient = extract_patient(raw_text)
    obs = extract_analytes(raw_text)

    metrics = build_metrics(patient, obs)

    st.success("PDF leído correctamente")

    st.subheader("🔎 Datos analizados (auditoría)")
    st.json({
        "patient": metrics["patient"],
        "indices": metrics["indices"],
        "urgency": metrics["urgency"],
        "analytes_count": len(metrics["analytes"]),
    })

    if st.button("🚀 Generar reporte"):
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        model = st.secrets.get("OPENAI_MODEL", "gpt-4o-mini")

        report = generate_report_with_gpt(metrics, api_key=api_key, model=model)

        st.subheader("📄 Reporte Interlab IA")
        st.write(report)

        pdf_bytes = make_pdf_bytes("Interlab IA - Reporte clínico", report)

        st.download_button(
            "⬇️ Descargar reporte en PDF",
            data=pdf_bytes,
            file_name="Interlab_IA_reporte.pdf",
            mime="application/pdf",
        )

