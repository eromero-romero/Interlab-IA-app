from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def render_pdf_from_template(context: dict) -> bytes:
    env = Environment(loader=FileSystemLoader("templates"))
    tpl = env.get_template("report.html")
    html_str = tpl.render(**context)
    pdf_bytes = HTML(string=html_str).write_pdf()
    return pdf_bytes
