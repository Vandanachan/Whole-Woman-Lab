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


_UNICODE_ASCII_MAP = {
    "—": "-",   # em dash
    "–": "-",   # en dash
    "‘": "'",   # left single quote
    "’": "'",   # right single quote / apostrophe
    "“": '"',   # left double quote
    "”": '"',   # right double quote
    "…": "...", # ellipsis
    " ": " ",   # non-breaking space
}


def _t(s) -> str:
    """Latin-1-safe text for the core PDF fonts. Smart punctuation (em/en
    dashes, curly quotes, ellipses) is normalised to plain ASCII first so it
    renders correctly instead of falling back to '?' under latin-1 encoding."""
    text = str(s)
    for uni, ascii_eq in _UNICODE_ASCII_MAP.items():
        text = text.replace(uni, ascii_eq)
    return text.encode("latin-1", "replace").decode("latin-1")


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


def _h3(pdf: _Report, text: str) -> None:
    pdf.ln(1.5)
    pdf.set_text_color(*BRAND)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5.5, _t(text), new_x="LMARGIN", new_y="NEXT")


def _h4(pdf: _Report, text: str) -> None:
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "BI", 9)
    pdf.cell(0, 4.8, _t(text), new_x="LMARGIN", new_y="NEXT")


def _para(pdf: _Report, text: str, size: float = 9, color=INK, italic: bool = False) -> None:
    pdf.set_text_color(*color)
    pdf.set_font("Helvetica", "I" if italic else "", size)
    pdf.multi_cell(0, 4.6, _t(text))


def _bullet(pdf: _Report, lead: str, rest: str = "", size: float = 8.7) -> None:
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "B", size)
    if rest:
        pdf.write(4.4, _t(f"-  {lead}: "))
        pdf.set_font("Helvetica", "", size)
        pdf.set_text_color(*MUTED)
        pdf.write(4.4, _t(rest))
        pdf.ln(4.6)
    else:
        pdf.set_font("Helvetica", "", size)
        pdf.multi_cell(0, 4.4, _t(f"-  {lead}"))


def _conf_bar(pdf: _Report, x: float, y: float, w: float, pct: float, color) -> None:
    pdf.set_fill_color(*BAR_BG)
    pdf.rect(x, y, w, 3.2, style="F")
    pdf.set_fill_color(*color)
    pdf.rect(x, y, max(0.6, w * pct), 3.2, style="F")


def _category_label(key: str) -> str:
    return key.replace("_", " ").title()


def _render_narrative(pdf: _Report, plan: dict) -> None:
    pdf.add_page()
    _h2(pdf, "Your Treatment Plan, Explained")
    _para(pdf, plan.get("narrative", ""))


def _render_glossary(pdf: _Report, plan: dict) -> None:
    glossary = plan.get("glossary", {})
    if not glossary:
        return
    pdf.add_page()
    _h2(pdf, "Understanding Tastes & Properties")
    how = glossary.get("how_to_read")
    if how:
        _para(pdf, how, italic=True, color=MUTED)
        pdf.ln(1)
    _h3(pdf, "The Six Tastes")
    for name, g in glossary.get("tastes", {}).items():
        _h4(pdf, f"{name.title()}" + (f"  ({g['also_called']})" if g.get("also_called") else ""))
        _para(pdf, g.get("description", ""))
        _bullet(pdf, "Action", g.get("action", ""))
        _bullet(pdf, "Helpful when", g.get("when_helpful", ""))
        _bullet(pdf, "Harmful when", g.get("when_harmful", ""))
        ex = g.get("example_foods_herbs", [])
        if ex:
            _bullet(pdf, "Examples", ", ".join(ex))
        pdf.ln(1)
    _h3(pdf, "Thermal Properties")
    for name, g in glossary.get("thermal_properties", {}).items():
        _h4(pdf, name.replace("_", " ").title())
        _para(pdf, g.get("description", ""))
        _bullet(pdf, "Action", g.get("action", ""))
        _bullet(pdf, "Helpful when", g.get("when_helpful", ""))
        _bullet(pdf, "Harmful when", g.get("when_harmful", ""))
        ex = g.get("examples", [])
        if ex:
            _bullet(pdf, "Examples", ", ".join(ex))
        pdf.ln(1)


def _render_favor_food(pdf: _Report, f: dict) -> None:
    if not isinstance(f, dict):
        _bullet(pdf, str(f))
        return
    tags = []
    if f.get("taste"):
        tags.append("taste: " + ", ".join(f["taste"]))
    if f.get("thermal"):
        tags.append("thermal: " + f["thermal"])
    tag_str = f" ({'; '.join(tags)})" if tags else ""
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "B", 8.7)
    pdf.write(4.3, _t(f"-  {f.get('food','')}{tag_str}: "))
    pdf.set_font("Helvetica", "", 8.7)
    pdf.set_text_color(*MUTED)
    pdf.write(4.3, _t(f.get("why", "")))
    pdf.ln(4.5)


def _render_pattern_plan(pdf: _Report, p: dict) -> None:
    pdf.add_page()
    _h2(pdf, f"Nutrition & Herb Plan — {p['pattern']} ({p['role']}, {p['confidence']*100:.0f}%)")
    _para(pdf, p.get("overview", ""))

    favor = p.get("favor", {})
    if favor:
        _h3(pdf, "Foods To Favour")
        for cat, foods in favor.items():
            if not isinstance(foods, list) or not foods:
                continue
            _h4(pdf, _category_label(cat))
            for f in foods:
                _render_favor_food(pdf, f)
            pdf.ln(0.5)

    avoid = p.get("avoid", [])
    if avoid:
        _h3(pdf, "Foods To Avoid & Why")
        for a in avoid:
            if isinstance(a, dict):
                pdf.set_text_color(*WARN)
                pdf.set_font("Helvetica", "B", 8.7)
                pdf.write(4.3, _t(f"-  {a.get('food','')}: "))
                pdf.set_font("Helvetica", "", 8.7)
                pdf.set_text_color(*INK)
                pdf.write(4.3, _t(a.get("why", "")))
                pdf.ln(4.5)
            else:
                _bullet(pdf, str(a))

    cooking = p.get("cooking_methods", {})
    if cooking:
        _h3(pdf, "Cooking Methods")
        if cooking.get("favor"):
            _bullet(pdf, "Favour", ", ".join(cooking["favor"]))
        if cooking.get("avoid"):
            _bullet(pdf, "Avoid", ", ".join(cooking["avoid"]))

    if p.get("meal_rhythm"):
        _h3(pdf, "Meal Rhythm & Timing")
        _para(pdf, p["meal_rhythm"])

    sample = p.get("sample_day", {})
    if sample:
        _h3(pdf, "Sample Day")
        for meal, desc in sample.items():
            _bullet(pdf, meal.title(), desc)

    herbs = p.get("herbs_detail", [])
    if herbs:
        _h3(pdf, "Herbs & Formulas")
        for h in herbs:
            pdf.set_text_color(*INK)
            pdf.set_font("Helvetica", "B", 8.7)
            trad = f" ({h['tradition']})" if h.get("tradition") else ""
            pdf.write(4.3, _t(f"-  {h.get('name','')}{trad}: "))
            pdf.set_font("Helvetica", "", 8.7)
            pdf.set_text_color(*MUTED)
            pdf.write(4.3, _t(h.get("action", "")))
            pdf.ln(4.5)
            if h.get("note"):
                pdf.set_text_color(*MUTED)
                pdf.set_font("Helvetica", "I", 8)
                pdf.multi_cell(0, 4, _t(f"     {h['note']}"))

    lifestyle = p.get("lifestyle", [])
    if lifestyle:
        _h3(pdf, "Lifestyle")
        for item in lifestyle:
            _bullet(pdf, item)

    if p.get("caution"):
        pdf.ln(1)
        pdf.set_text_color(*WARN)
        pdf.set_font("Helvetica", "B", 8.8)
        pdf.multi_cell(0, 4.6, _t(f"Caution: {p['caution']}"))


def _render_reconciliation(pdf: _Report, plan: dict) -> None:
    notes = plan.get("reconciliation_notes", [])
    sequencing = plan.get("sequencing")
    if not notes and not sequencing:
        return
    pdf.add_page()
    _h2(pdf, "Cross-Pattern Reconciliation & Sequencing")
    if sequencing:
        _h3(pdf, "How To Sequence This Plan")
        _para(pdf, sequencing)
    if notes:
        _h3(pdf, "Where Patterns Interact")
        for n in notes:
            _bullet(pdf, n)
            pdf.ln(0.8)


def _render_master_avoid(pdf: _Report, plan: dict) -> None:
    items = plan.get("master_avoid", [])
    if not items:
        return
    pdf.add_page()
    _h2(pdf, "Quick Reference — Everything To Avoid")
    _para(pdf, "A single consolidated list drawn from every confirmed pattern above, for a fast "
               "at-a-glance check while grocery shopping or planning meals.", italic=True, color=MUTED)
    pdf.ln(1)
    for it in items:
        pdf.set_text_color(*WARN)
        pdf.set_font("Helvetica", "B", 8.7)
        pats = ", ".join(it["patterns"])
        pdf.write(4.3, _t(f"-  {it['food']}  [{pats}]: "))
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*INK)
        pdf.write(4.3, _t(" / ".join(it["why"])))
        pdf.ln(4.5)


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

    # elaborate treatment plan: narrative, glossary, per-pattern nutrition/herbs/
    # lifestyle, cross-pattern reconciliation, and a quick-reference avoid list
    plan = report.get("treatment_plan")
    if plan:
        _render_narrative(pdf, plan)
        _render_glossary(pdf, plan)
        for p in plan.get("by_pattern", []):
            _render_pattern_plan(pdf, p)
        _render_reconciliation(pdf, plan)
        _render_master_avoid(pdf, plan)

    # disclaimer
    pdf.ln(3)
    pdf.set_draw_color(*LINE)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 4, _t(report.get("disclaimer", "")))

    out = pdf.output()
    return bytes(out)
