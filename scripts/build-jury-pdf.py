from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "CDR_Jury_Presentation.pdf"

NAVY = colors.HexColor("#090d18")
PANEL = colors.HexColor("#121a2b")
CYAN = colors.HexColor("#67e8f9")
GREEN = colors.HexColor("#6ee7b7")
MUTED = colors.HexColor("#a5b4c7")
WHITE = colors.HexColor("#f8fafc")
AMBER = colors.HexColor("#fcd34d")


def paragraph(text, style):
    return Paragraph(text, style)


def build():
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "SlideTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=28,
        leading=32, textColor=WHITE, spaceAfter=16,
    )
    subtitle = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=15,
        leading=21, textColor=MUTED, spaceAfter=14,
    )
    body = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Helvetica", fontSize=14,
        leading=20, textColor=WHITE, spaceAfter=9,
    )
    small = ParagraphStyle(
        "Small", parent=body, fontSize=10, leading=14, textColor=MUTED,
    )
    metric = ParagraphStyle(
        "Metric", parent=body, fontName="Helvetica-Bold", fontSize=23,
        leading=27, textColor=GREEN, alignment=1,
    )
    metric_label = ParagraphStyle(
        "MetricLabel", parent=small, alignment=1, textColor=WHITE,
    )
    bullet = ParagraphStyle(
        "Bullet", parent=body, leftIndent=18, firstLineIndent=-12,
    )

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=landscape(letter), rightMargin=0.55 * inch,
        leftMargin=0.55 * inch, topMargin=0.45 * inch, bottomMargin=0.4 * inch,
        title="Chaos-Driven Refactoring - Jury Presentation",
        author="CDR team",
    )
    story = []

    def slide(heading, kicker=None):
        if story:
            story.append(PageBreak())
        if kicker:
            story.append(paragraph(kicker.upper(), ParagraphStyle(
                "Kicker", parent=small, textColor=CYAN, fontName="Helvetica-Bold",
                fontSize=10, leading=12, spaceAfter=8,
            )))
        story.append(paragraph(heading, title))

    def bullets(items):
        for item in items:
            story.append(paragraph("- " + item, bullet))

    def panel(content, width=9.8 * inch):
        table = Table([[content]], colWidths=[width])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#263550")),
            ("LEFTPADDING", (0, 0), (-1, -1), 18),
            ("RIGHTPADDING", (0, 0), (-1, -1), 18),
            ("TOPPADDING", (0, 0), (-1, -1), 15),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
        ]))
        story.append(table)

    slide("Chaos-Driven Refactoring", "IBM Bob 2.0 Hackathon")
    story.append(paragraph("Break the system on purpose. Ship the architecture that survives it.", subtitle))
    panel(paragraph(
        "CDR closes the APM-to-code gap: it injects a real fault, captures the physical collapse, "
        "has IBM Bob read and repair the affected repository, then reruns the identical experiment "
        "to verify resilience.", body
    ))
    story.append(Spacer(1, 18))
    story.append(paragraph("A complete chaos -> diagnosis -> code change -> verification loop.", subtitle))

    slide("The problem: diagnosis stops before the code", "Why this matters")
    bullets([
        "Chaos engineering can reproduce the failure, but does not repair the business logic.",
        "APM and logs can localize symptoms, but the fix still depends on a human expert.",
        "Coding agents can edit code, but normally do not see the physical failure that motivated the change.",
        "CDR connects these steps and refuses to call a patch successful until the same fault is survived.",
    ])
    panel(paragraph(
        "Target users: SRE, DevOps and platform teams protecting checkout, payment and other high-value paths.", body
    ))

    slide("One application, four observable phases", "The product flow")
    data = [
        [paragraph("01<br/><b>Inject chaos</b><br/><font color='#a5b4c7'>k6 + Toxiproxy</font>", body),
         paragraph("02<br/><b>Classify</b><br/><font color='#a5b4c7'>telemetry + evidence</font>", body),
         paragraph("03<br/><b>Let Bob rewrite it</b><br/><font color='#a5b4c7'>real repository diff</font>", body),
         paragraph("04<br/><b>Prove it survives</b><br/><font color='#a5b4c7'>same experiment again</font>", body)],
    ]
    table = Table(data, colWidths=[2.45 * inch] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL), ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#263550")),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#263550")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15), ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
    ]))
    story.append(table)
    story.append(Spacer(1, 18))
    story.append(paragraph("Every phase streams to the control room through Supabase, with a deterministic mock mode for rehearsals and a live mode for evidence.", subtitle))

    slide("IBM Bob is part of the runtime repair loop", "Application of technology")
    bullets([
        "The worker shallow-clones the submitted repository at the requested commit.",
        "IBM Bob Shell runs in agent mode inside that clone and reads the actual source code.",
        "Bob applies the minimal resilience change; the runner extracts the real git diff.",
        "The patch, changed files, Bob task ID and Bobcoin cost are stored and shown in the dashboard.",
        "Live verification fails closed unless the patch source is IBM Bob and the expected service was changed.",
    ])
    panel(paragraph(
        "Fallbacks exist for mock development, but live mode requires Bob. This makes the evaluation claim auditable rather than cosmetic.", body
    ))

    slide("Architecture: control plane + data plane", "How it works")
    bullets([
        "Control plane: Next.js dashboard on Vercel, Supabase queue, run history and realtime progress.",
        "Data plane: local Python worker, Docker Compose lab, k6 load, Toxiproxy fault injection and Bob Shell.",
        "The runner rebuilds the Bob-patched checkoutservice container before the after measurement.",
        "The same scenario, load profile and fault are executed before and after the repair.",
    ])
    panel(paragraph(
        "Vercel hosts the control room. Docker, k6 and Bob remain on the runner machine where the target repository and live lab are available.", body
    ))

    slide("Measured live result", "Evidence from the real lab")
    metrics = [
        [paragraph("24.8%", metric), paragraph("27.3%", metric), paragraph("30 s -> none", metric), paragraph("0.083248", metric)],
        [paragraph("p95 latency improvement", metric_label), paragraph("throughput increase", metric_label), paragraph("collapse eliminated", metric_label), paragraph("Bobcoins consumed", metric_label)],
    ]
    table = Table(metrics, colWidths=[2.45 * inch] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL), ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#263550")),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#263550")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(table)
    story.append(Spacer(1, 18))
    bullets([
        "Run: run-2738beb5 | 200 virtual users | 120 seconds | 800 ms emailservice latency.",
        "Bob added a 200 ms child context around the optional confirmation-email RPC.",
        "The order response remained successful; payment and shipping semantics were preserved.",
    ])

    slide("The jury demo: one screen, one story", "Suggested walkthrough")
    bullets([
        "Open the dashboard and submit the pinned Online Boutique scenario in live mode.",
        "Show the timeline: physical collapse -> classification -> Bob task attribution -> verification.",
        "Open the diagnosis card to show the task ID, Bobcoins and identified source file.",
        "Open the generated patch to show the real diff, not a generic template.",
        "Compare before/after charts and end on LIVE EVIDENCE with no collapse after the same fault.",
    ])
    panel(paragraph(
        "Demo command: python -m cdr run --scenario scenarios/checkout-latency-cascade.yaml --mode live --sink all", body
    ))

    slide("Why CDR is different", "Closing pitch")
    bullets([
        "It does not stop at an AI explanation: it produces a repository-level change.",
        "It does not trust the change blindly: it rebuilds the affected service and reruns the fault.",
        "It makes IBM Bob measurable through task IDs, cost attribution and a real git diff.",
        "It turns resilience work from a manual incident investigation into a repeatable engineering loop.",
    ])
    panel(paragraph(
        "CDR: from physical failure to verified resilience, with IBM Bob in the critical path.", body
    ))
    story.append(Spacer(1, 16))
    story.append(paragraph("Evidence: docs/LIVE_EVIDENCE.md | Runtime integration: docs/BOB_USAGE.md | Demo: docs/DEMO_SCRIPT.md", small))

    def background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, landscape(letter)[0], landscape(letter)[1], fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#1b2942"))
        canvas.rect(0, 0, landscape(letter)[0], 0.12 * inch, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(landscape(letter)[0] - 0.55 * inch, 0.18 * inch, f"CDR | {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=background, onLaterPages=background)
    print(OUTPUT)


if __name__ == "__main__":
    build()
