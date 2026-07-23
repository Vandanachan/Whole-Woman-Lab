"""Deterministic PDF report builder (fpdf2, pure-Python, no system deps).

Consumes the structured ``report`` dict produced by Engine 1 and lays out a
clean, branded, practitioner-ready PDF. It performs no reasoning — it only
formats what the engine already decided.
"""
from __future__ import annotations

from fpdf import FPDF

BRAND = (58, 111, 95)       # deep green
INK = (34, 34, 34)
MUTED = (110, 110, 110)
PRESENT = (184, 64, 43)     # red
WARN_BG = (253, 238, 231)
WARN = (184, 64, 43)
LINE = (222, 226, 222)
BAR_BG = (232, 235, 232)


def _t(s) -> str:
    """Latin-1-safe text for the core PDF fonts."""
    return str(s).encode("latin-1", "replace").decode("latin-1")


class _Report(FPDF):
    def header(self) -> None:
        self.set_fill_color(*BRAND)
        self.rect(0, 0, self.w, 22, style="F")
        self.set_xy(16, 6)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 8, _t("Whole Woman Lab  |  Clinical Report"), align="L")
        self.set_xy(16, 14)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 4, _t("Deterministic clinical-reasoning output - for practitioner review"), align="L")
        self.set_y(28)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_draw_color(*LINE)
        self.line(16, self.get_y(), self.w - 16, self.get_y())
        self.set_y(-11)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.cell(0, 4, _t(f"Not a medical diagnosis - confirm with full examination.   Page {self.page_no()}"),
                  align="C")

    def multi_cell(self, *args, **kwargs):
        # Always render full-width from the left margin so consecutive
        # multi_cell calls never collapse to zero available width.
        kwargs.setdefault("new_x", "LMARGIN")
        kwargs.setdefault("new_y", "NEXT")
        self.set_x(self.l_margin)
        return super().multi_cell(*args, **kwargs)


def _h2(pdf: _Report, text: str) -> None:
    pdf.ln(3)
    pdf.set_text_color(*BRAND)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, _t(text), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*LINE)
    pdf.line(16, pdf.get_y(), pdf.w - 16, pdf.get_y())
    pdf.ln(2)


def _conf_bar(pdf: _Report, x: float, y: float, w: float, pct: float, color) -> None:
    pdf.set_fill_color(*BAR_BG)
    pdf.rect(x, y, w, 3.2, style="F")
    pdf.set_fill_color(*color)
    pdf.rect(x, y, max(0.6, w * pct), 3.2, style="F")


def build_pdf(report: dict, client: dict | None = None) -> bytes:
    pdf = _Report(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(16, 16, 16)
    pdf.add_page()

    # client line
    pdf.set_text_color(*MUTED)
    pdf.set_font("Helvetica", "", 9)
    c = client or {}
    who = " | ".join([str(v) for v in [c.get("name"), c.get("sex"),
                                       f"age {c.get('age')}" if c.get("age") else None] if v]) or "Client"
    pdf.cell(0, 5, _t(who), new_x="LMARGIN", new_y="NEXT")

    # headline
    pdf.ln(1)
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 5.5, _t(report.get("headline", "")))

    # confirmed diagnoses
    _h2(pdf, "Diagnostic Picture")
    diags = report.get("diagnoses", [])
    if not diags:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 5, _t("No pattern reached the diagnosis threshold. Gather more objective "
                                "signs (tongue & pulse) and re-run."))
    for d in diags:
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 6, _t(f"{d['pattern']}  ({d['role']})"), new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        _conf_bar(pdf, 16, y + 0.5, 70, float(d["confidence"]), PRESENT)
        pdf.set_xy(90, y - 1)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, _t(f"{d['confidence']*100:.0f}% ({d['band']})   priority: {d['priority']}"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.6, _t(f"Principle: {d['principle']}"))
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 4.6, _t(f"Formulas: {', '.join(d['formulas'])}"))
        if d.get("caution"):
            pdf.set_text_color(*WARN)
            pdf.multi_cell(0, 4.6, _t(f"Caution tag: {d['caution']}"))
        pdf.ln(1.5)

    # safety guardrails
    safety = report.get("safety", [])
    if safety:
        _h2(pdf, "Treatment Guardrails")
        for s in safety:
            top = pdf.get_y()
            pdf.set_fill_color(*WARN_BG)
            pdf.set_draw_color(*WARN)
            pdf.set_text_color(*WARN)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.multi_cell(0, 4.6, _t(f"[{s['severity'].upper()}]"), new_x="LMARGIN", new_y="NEXT",
                           fill=True, border="L")
            pdf.set_text_color(*INK)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 4.6, _t(s["message"]), fill=True, border="L")
            pdf.ln(1.5)

    # root / branch / progression
    prog = report.get("progression", {})
    _h2(pdf, "Root, Branch & Progression")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*INK)
    pdf.multi_cell(0, 4.8, _t(f"Roots: {', '.join(prog.get('roots', [])) or '-'}"))
    pdf.multi_cell(0, 4.8, _t(f"Branches: {', '.join(prog.get('branches', [])) or '-'}"))
    pdf.multi_cell(0, 4.8, _t(f"Heading toward: {', '.join(prog.get('projected_next', [])) or '-'}"
                              f"   ({prog.get('reversibility','')})"))
    for mrow in prog.get("mechanisms", [])[:6]:
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 4.4, _t(f"- {mrow['from']} -> {mrow['to']}: {mrow['mechanism']}"))

    # differential
    _h2(pdf, "Differential (ranked)")
    pdf.set_font("Helvetica", "", 9)
    for i in report.get("differential", []):
        pdf.set_text_color(*INK)
        pdf.cell(0, 4.8, _t(f"{i['rank']}. {i['pattern']}  -  {i['status']}  ({i['confidence']*100:.0f}%)"),
                 new_x="LMARGIN", new_y="NEXT")

    # disclaimer
    pdf.ln(3)
    pdf.set_draw_color(*LINE)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 4, _t(report.get("disclaimer", "")))

    out = pdf.output()
    return bytes(out)
