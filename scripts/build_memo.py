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
test = t["ztest"]
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
    Paragraph(f"<b>Gies led the 11 entering units in four-year graduation.</b> For fall 2020 entrants, "
              f"{g4['Gies']:.1f}% graduated in four years, vs. {g4['All campus']:.1f}% for all campus. That gap "
              f"ranged from {t['trend']['4-year graduation']['smallest_gap']:.1f} to "
              f"{t['trend']['4-year graduation']['largest_gap']:.1f} points across five cohorts.", bullet, bulletText="•"),
    Paragraph(f"<b>Gies retention was {test['diff_pts']:.2f} points above the rest of campus.</b> Of fall 2025 entrants, "
              f"{test['gies_pct']:.2f}% of Gies students returned (n = {test['n_gies']:,}), vs. "
              f"{test['rest_of_campus_pct']:.2f}% of other entrants (n = {test['n_rest']:,}). "
              f"A two-proportion z-test gave a 95% confidence interval of {test['ci_low']:.2f} to {test['ci_high']:.2f} points. "
              f"The chart uses all campus, which includes Gies: {ret['All campus']:.2f}%, a {ret['gap_pts']:.2f}-point gap.",
              bullet, bulletText="•"),
    Paragraph(f"<b>Illinois as a whole graduates about what its first-year retention would predict.</b> Across {r['n']} public research "
              f"universities, each extra point of first-year retention goes with about {m1['slope']:.1f} extra points of six-year graduation, "
              f"and retention alone accounts for about {100 * m1['r_squared']:.0f}% of the differences between schools. At {u['retention_rate']:.0f}% retention, "
              f"Illinois would be expected to graduate {u['predicted']:.1f}%. It actually graduates {u['grad_rate_6yr']:.1f}%, just {u['residual']:.1f} points above, "
              f"which is effectively on the line. <i>Source: IPEDS, {r['year']} data files.</i>", bullet, bulletText="•"),
    Spacer(1, 3),
    Image(str(chart), width=7.0 * inch, height=2.1 * inch),
    Paragraph("Gies vs. all campus by entering cohort; vertical scales differ by panel. "
              '<link href="https://dair.illinois.edu/access-data/retention-and-graduation-rates/" color="#214E6A">DAIR</link>'
              " measures first-year retention at the campus level: the share of first-time, full-time, degree-seeking undergraduates "
              "who return to UIUC the next fall, grouped by their college at entry.", small),
    Paragraph("What to keep in mind", head),
    Paragraph("<b>This shows a pattern, not a cause.</b> Gies admits a strong entering class, so these numbers do not show how much of the lead comes from the "
              "college itself. Likewise, the link between retention and graduation is a comparison of schools. It does not promise that raising retention "
              "at one school would raise its graduation rate.", bullet, bulletText="•"),
    Paragraph("<b>The two series cover different entering cohorts.</b> DAIR graduation uses fall 2016-2020 entrants; "
              "retention uses fall 2021-2025 entrants. "
              f"The retention gap vs. all campus ranged from {gaps['smallest_gap']:.1f} to {gaps['largest_gap']:.1f} points.",
              bullet, bulletText="•"),
    Paragraph("A next question", head),
    Paragraph(f"About {100 - g4['Gies']:.0f}% of Gies students who started in 2020 needed more than four years or left without a degree. With student-level records, the team "
              "could ask who those students are and when they went off track, for example whether first-year course outcomes or a change of major explain "
              "most of the delay.", body),
    Spacer(1, 2),
    Paragraph("Independent project using public data; not affiliated with Gies or DAIR. Sources: UIUC DAIR and NCES IPEDS, downloaded Nov 2, 2026.", small),
]
doc = SimpleDocTemplate("memo/findings.pdf", pagesize=letter, leftMargin=.75 * inch, rightMargin=.75 * inch,
                        topMargin=.55 * inch, bottomMargin=.45 * inch, title="Gies retention and graduation findings", author="")
doc.build(story)
