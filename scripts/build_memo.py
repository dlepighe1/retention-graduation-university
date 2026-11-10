"""Build memo/findings.pdf from the numbers the notebooks saved. Run from the repo root after notebooks 01-03."""
import json
from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

t = json.loads(Path("notebooks/trends_numbers.json").read_text())
r = json.loads(Path("notebooks/regression_numbers.json").read_text())
ret, g4, g6 = (t["latest"][k] for k in ("First-year retention", "4-year graduation", "6-year graduation"))
gaps = t["trend"]["First-year retention"]
m1 = r["models"][0]
u = r["uiuc"]

# Prefer the Tableau export when it exists, as the plan asks.
tableau_chart = Path("dashboard/view1.png")
chart = tableau_chart if tableau_chart.exists() else Path("dashboard/preview/view1_gies_vs_campus.png")

INK = HexColor("#222222")
body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.6, leading=12.6, textColor=INK, alignment=TA_LEFT, spaceAfter=3.5)
head = ParagraphStyle("head", parent=body, fontName="Helvetica-Bold", fontSize=10.2, spaceBefore=6, spaceAfter=2.5)
title = ParagraphStyle("title", parent=body, fontName="Helvetica-Bold", fontSize=13.5, leading=17, spaceAfter=3)
small = ParagraphStyle("small", parent=body, fontSize=7.8, leading=9.6, textColor=HexColor("#5A5A5A"))
bullet = ParagraphStyle("bullet", parent=body, leftIndent=10, bulletIndent=0)

story = [
    Paragraph(f"Gies students stay and graduate at the highest rates at Illinois: {g6['Gies']:.1f}% finish within six years, "
              f"{g6['gap_pts']:.1f} points above campus", title),
    Paragraph("Findings memo for a program director, November 2026", small),
    Paragraph("What the numbers show", head),
    Paragraph(f"<b>Gies leads the campus at every stage.</b> Of the 11 undergraduate entering units, Gies ranks first on first-year "
              f"retention ({ret['Gies']:.1f}% vs {ret['All campus']:.1f}% for campus, fall 2025 entrants), four-year graduation and "
              f"six-year graduation (fall 2020 entrants). <i>Source: DAIR.</i>", bullet, bulletText="•"),
    Paragraph(f"<b>The biggest advantage is finishing on time, and it is holding steady.</b> {g4['Gies']:.1f}% of Gies students who started in "
              f"fall 2020 graduated in four years, vs {g4['All campus']:.1f}% for campus. That {g4['gap_pts']:.1f}-point gap has stayed "
              f"between {t['trend']['4-year graduation']['smallest_gap']:.1f} and {t['trend']['4-year graduation']['largest_gap']:.1f} points across five entering classes. "
              f"The first-year retention gap moves around more, from {gaps['smallest_gap']:.1f} to {gaps['largest_gap']:.1f} points, with no clear direction. <i>Source: DAIR.</i>",
              bullet, bulletText="•"),
    Paragraph(f"<b>Illinois as a whole graduates about what its first-year retention would predict.</b> Across {r['n']} public research "
              f"universities, each extra point of first-year retention goes with about {m1['slope']:.1f} extra points of six-year graduation, "
              f"and retention alone accounts for about {100 * m1['r_squared']:.0f}% of the differences between schools. At {u['retention_rate']:.0f}% retention, "
              f"Illinois would be expected to graduate {u['predicted']:.1f}%. It actually graduates {u['grad_rate_6yr']:.1f}%, just {u['residual']:.1f} points above, "
              f"which is effectively on the line. <i>Source: IPEDS, {r['year']} data files.</i>", bullet, bulletText="•"),
    Spacer(1, 3),
    Image(str(chart), width=7.0 * inch, height=2.1 * inch),
    Paragraph("Gies vs all campus by entering class. First-time, full-time, degree-seeking undergraduates; the vertical scales differ by panel. "
              "Source: UIUC DAIR, downloaded Nov 2, 2026.", small),
    Paragraph("What to keep in mind", head),
    Paragraph("<b>This shows a pattern, not a cause.</b> Gies admits a strong entering class, so these numbers do not show how much of the lead comes from the "
              "college itself. Likewise, the link between retention and graduation is a comparison of schools. It does not promise that raising retention "
              "at one school would raise its graduation rate.", bullet, bulletText="•"),
    Paragraph("<b>The retention and graduation figures describe different students.</b> Graduation takes six years to measure, so the newest graduation "
              "class entered in 2020, while the newest retention class entered in 2025.", bullet, bulletText="•"),
    Paragraph(f"<b>One year is not a trend.</b> The {ret['gap_pts']:.1f}-point retention gap for fall 2025 is wider than in the three years before it, "
              "but the gap has swung like this before.", bullet, bulletText="•"),
    Paragraph("A next question", head),
    Paragraph(f"About {100 - g4['Gies']:.0f}% of Gies students who started in 2020 needed more than four years or left without a degree. With student-level records, the team "
              "could ask who those students are and when they went off track, for example whether first-year course outcomes or a change of major explain "
              "most of the delay.", body),
    Spacer(1, 2),
    Paragraph("Independent project using public data; not affiliated with the Gies College of Business or DAIR. Public IPEDS rates are rounded, and the 2023 files were the "
              "latest NCES release at download.", small),
]
doc = SimpleDocTemplate("memo/findings.pdf", pagesize=letter, leftMargin=.75 * inch, rightMargin=.75 * inch,
                        topMargin=.55 * inch, bottomMargin=.45 * inch, title="Gies retention and graduation findings", author="")
doc.build(story)
