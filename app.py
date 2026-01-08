import streamlit as st
import tempfile
from datetime import datetime

# --- IMPORTS DE TU ENGINE (carpeta /engine) ---
from engine.parse_pdf import read_pdf_text, extract_analytes_from_text
from engine.scores import build_metrics  # Ajusta si tu función se llama distinto

# --- PDF export (sin IA) ---
from weasyprint import HTML  # genera PDF desde HTML


# =========================
# CONFIG
# =========================
APP_NAME = "Interlab IA"
REPORT_TITLE = "Reporte clínico"
USE_LLM = False  # <- IMPORTANTE: deja en False hasta que tengas API estable

st.set_page_config(page_title=f"{APP_NAME} – {REPORT_TITLE}", layout="wide")

st.title(f"🧠 {APP_NAME} – {REPORT_TITLE}")
st.caption("Reporte automatizado basado en resultados de laboratorio. No reemplaza la valoración médica.")


# =========================
# HELPERS VISUALES
# =========================
def badge(color: str, text: str) -> str:
    return f"""
    <span style="
        display:inline-block;
        padding:2px 10px;
        border-radius:999px;
        font-size:12px;
        font-weight:600;
        color:white;
        background:{color};
        ">
        {text}
    </span>
    """

def semaforo(status: str) -> str:
    """
    status esperado: 'ok', 'borderline', 'high', 'low', 'unknown'
    """
    status = (status or "unknown").lower()
    if status == "ok":
        return badge("#16a34a", "Normal")
    if status == "borderline":
        return badge("#f59e0b", "Límite")
    if status in ("high", "low"):
        return badge("#dc2626", "Alterado")
    return badge("#6b7280", "N/E")


def safe_get(d: dict, path: list, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


# =========================
# GENERADOR HTML DEL REPORTE
# =========================
def render_report_html(metrics: dict) -> str:
    patient_age = safe_get(metrics, ["patient", "age"], "N/E")
    patient_sex = safe_get(metrics, ["patient", "sex"], "N/E")
    urgency = safe_get(metrics, ["urgency"], "N/E")

    idx_global = safe_get(metrics, ["indices", "global_health"], "N/E")
    idx_inflam = safe_get(metrics, ["indices", "inflammation"], "N/E")
    metabolic_age = safe_get(metrics, ["indices", "metabolic_age"], "N/E")

    # Analitos (si tu metrics los incluye)
    # Esperado: metrics["analytes"] = [{"name": "...", "value":..., "unit":"...", "ref":"...", "flag":"ok/high/low/borderline/unknown"}]
    analytes = safe_get(metrics, ["analytes"], []) or []

    # Risk score por sistema (si lo tienes)
    system_scores = safe_get(metrics, ["system_scores"], {}) or {}

    def fmt(v):
        return "N/E" if v is None else str(v)

    # tabla analitos
    analyte_rows = ""
    for a in analytes:
        name = a.get("name", "N/E")
        value = a.get("value", None)
        unit = a.get("unit", "")
        ref = a.get("ref", "N/E")
        flag = a.get("flag", "unknown")
        analyte_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;">{name}</td>
          <td style="padding:10px;border-bottom:1px solid #eee;">{fmt(value)} {unit}</td>
          <td style="padding:10px;border-bottom:1px solid #eee;">{ref}</td>
          <td style="padding:10px;border-bottom:1px solid #eee;">{semaforo(flag)}</td>
        </tr>
        """

    # tabla systems
    system_rows = ""
    for k, v in system_scores.items():
        system_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;">{k}</td>
          <td style="padding:10px;border-bottom:1px solid #eee;">{v}</td>
        </tr>
        """

    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        body {{ font-family: Arial, sans-serif; color:#111827; }}
        .header {{
          background:#7a0f2b;
          color:white;
          padding:18px 22px;
          border-radius:14px;
          display:flex;
          justify-content:space-between;
          align-items:center;
        }}
        .card {{
          background:#ffffff;
          border:1px solid #eee;
          border-radius:14px;
          padding:16px 18px;
          margin-top:14px;
        }}
        h2 {{ margin:0 0 10px 0; font-size:18px; }}
        .grid {{
          display:grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap:12px;
        }}
        .kpi {{
          border:1px solid #eee;
          border-radius:14px;
          padding:12px 14px;
        }}
        .kpi .label {{ font-size:12px; color:#6b7280; }}
        .kpi .value {{ font-size:22px; font-weight:800; margin-top:6px; }}
        table {{ width:100%; border-collapse:collapse; }}
        .muted {{ color:#6b7280; font-size:12px; }}
      </style>
    </head>
    <body>
      <div class="header">
        <div>
          <div style="font-size:22px;font-weight:800;">🧠 {APP_NAME} – {REPORT_TITLE}</div>
          <div style="opacity:0.9;font-size:12px;">Generado: {today}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-weight:700;">Reporte clínico</div>
          <div style="font-size:12px;opacity:0.9;">Generado automáticamente</div>
        </div>
      </div>

      <div class="card">
        <h2>👤 Datos del paciente</h2>
        <div class="grid">
          <div class="kpi">
            <div class="label">Edad</div>
            <div class="value">{patient_age}</div>
          </div>
          <div class="kpi">
            <div class="label">Sexo</div>
            <div class="value">{patient_sex}</div>
          </div>
          <div class="kpi">
            <div class="label">Urgencia</div>
            <div class="value">{urgency}</div>
          </div>
        </div>
        <div class="muted" style="margin-top:10px;">
          Este informe no sustituye consulta médica. Correlacionar con síntomas e historia clínica.
        </div>
      </div>

      <div class="card">
        <h2>📌 Resumen ejecutivo</h2>
        <div class="grid">
          <div class="kpi">
            <div class="label">Índice global</div>
            <div class="value">{idx_global}</div>
          </div>
          <div class="kpi">
            <div class="label">Inflamación</div>
            <div class="value">{idx_inflam}</div>
          </div>
          <div class="kpi">
            <div class="label">Edad metabólica</div>
            <div class="value">{metabolic_age}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>🧪 Resultados (con semáforo)</h2>
        <table>
          <thead>
            <tr>
              <th style="text-align:left;padding:10px;border-bottom:2px solid #111827;">Analito</th>
              <th style="text-align:left;padding:10px;border-bottom:2px solid #111827;">Resultado</th>
              <th style="text-align:left;padding:10px;border-bottom:2px solid #111827;">Referencia</th>
              <th style="text-align:left;padding:10px;border-bottom:2px solid #111827;">Estado</th>
            </tr>
          </thead>
          <tbody>
            {analyte_rows if analyte_rows else "<tr><td colspan='4' style='padding:10px;'>No se detectaron analitos estructurados (revisar parser).</td></tr>"}
          </tbody>
        </table>
      </div>

      <div class="card">
        <h2>🧩 Risk score por sistema</h2>
        <table>
          <thead>
            <tr>
              <th style="text-align:left;padding:10px;border-bottom:2px solid #111827;">Sistema</th>
              <th style="text-align:left;padding:10px;border-bottom:2px solid #111827;">Score</th>
            </tr>
          </thead>
          <tbody>
            {system_rows if system_rows else "<tr><td colspan='2' style='padding:10px;'>N/E</td></tr>"}
          </tbody>
        </table>
      </div>

      <div class="card">
        <h2>✅ Próximos pasos sugeridos</h2>
        <ul>
          <li>Correlacionar resultados con clínica y antecedentes.</li>
          <li>Repetir/confirmar pruebas alteradas según criterio médico.</li>
          <li>Control de factores de riesgo (dieta, actividad física, etc.) según hallazgos.</li>
        </ul>
      </div>

      <div class="card">
        <h2>❓ FAQ</h2>
        <ul>
          <li><b>¿Esto es un diagnóstico?</b> No. Es una interpretación automatizada orientativa.</li>
          <li><b>¿Qué hago si hay valores alterados?</b> Consultar con tu médico para definir conducta.</li>
          <li><b>¿Por qué aparece N/E?</b> Porque ese dato no estaba en el PDF o no se pudo extraer con seguridad.</li>
          <li><b>¿Puedo usar esto para tratamiento?</b> No. Es apoyo informativo, no prescriptivo.</li>
        </ul>
        <div class="muted">© {APP_NAME}. Uso interno / informativo.</div>
      </div>

    </body>
    </html>
    """
    return html


def html_to_pdf_bytes(html: str) -> bytes:
    return HTML(string=html).write_pdf()


# =========================
# UI PRINCIPAL
# =========================
pdf = st.file_uploader("📄 Subir PDF de laboratorio", type=["pdf"])

raw_text = ""
if pdf:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf.read())
        pdf_path = tmp.name

    raw_text = read_pdf_text(pdf_path)
    st.success("PDF leído correctamente")

    if st.button("🚀 Generar reporte"):
        # 1) Extraer analitos del texto
        obs = extract_analytes_from_text(raw_text)

        # 2) Construir métricas con tu motor (SIN IA)
        metrics = build_metrics(obs)  # <- aquí es donde pones tu lógica científica

        # Auditoría
        with st.expander("🔎 Datos analizados (auditoría)", expanded=False):
            st.json(metrics)

        # 3) Render HTML (bonito)
        html_report = render_report_html(metrics)

        st.subheader("🧾 Vista previa del reporte")
        st.components.v1.html(html_report, height=900, scrolling=True)

        # 4) Descargar PDF
        pdf_bytes = html_to_pdf_bytes(html_report)
        st.download_button(
            "⬇️ Descargar reporte en PDF",
            data=pdf_bytes,
            file_name="reporte_interlab_ia.pdf",
            mime="application/pdf",
        )
else:
    st.info("Sube un PDF para comenzar.")
