from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "output" / "pdf" / "SmartSpinner_v0_4_RFQ_Brief_EN.pdf"
HERO = ROOT / "public" / "project-files" / "ticker_spinner_v0_3_partner_color.png"
HANDHELD = ROOT / "public" / "project-files" / "ticker_spinner_v0_3_partner_handheld.png"
DRAWING = ROOT / "public" / "project-files" / "ticker_spinner_v0_3_dimension_drawing.png"

NAVY = colors.HexColor("#10253F")
GREEN = colors.HexColor("#22A06B")
MINT = colors.HexColor("#E9F8F1")
ORANGE = colors.HexColor("#F59E0B")
PALE = colors.HexColor("#F3F6F9")
TEXT = colors.HexColor("#263442")
MUTED = colors.HexColor("#627083")
RED = colors.HexColor("#B42318")


def p(text, style):
    return Paragraph(text, style)


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=31, textColor=colors.white, alignment=TA_LEFT, spaceAfter=5 * mm))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["BodyText"], fontName="Helvetica", fontSize=12, leading=17, textColor=colors.HexColor("#D7E4F3"), spaceAfter=4 * mm))
styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=NAVY, spaceAfter=5 * mm))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=NAVY, spaceBefore=3 * mm, spaceAfter=2 * mm))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13.2, textColor=TEXT, spaceAfter=2.5 * mm))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10.5, textColor=MUTED))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=RED, backColor=colors.HexColor("#FFF1F0"), borderColor=colors.HexColor("#FFCCC7"), borderWidth=0.8, borderPadding=8, spaceBefore=2 * mm, spaceAfter=5 * mm))
styles.add(ParagraphStyle(name="Bulletx", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.8, leading=12.2, textColor=TEXT, leftIndent=5 * mm, firstLineIndent=-3 * mm, bulletIndent=1 * mm, spaceAfter=1.6 * mm))
styles.add(ParagraphStyle(name="Metric", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=GREEN, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="MetricLabel", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.4, leading=9.5, textColor=MUTED, alignment=TA_CENTER))


class NumberedDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, rightMargin=17 * mm, leftMargin=17 * mm, topMargin=18 * mm, bottomMargin=17 * mm, title="SmartSpinner v0.4 RFQ Brief", author="German Klimenko")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self.decorate))

    def decorate(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D8E0E8"))
        canvas.line(17 * mm, 13 * mm, A4[0] - 17 * mm, 13 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(17 * mm, 8.5 * mm, "SmartSpinner v0.4 | Engineering completion and turnkey PCBA RFQ")
        canvas.drawRightString(A4[0] - 17 * mm, 8.5 * mm, f"Page {doc.page}")
        canvas.restoreState()


def bullet(text):
    return p(f"- {text}", styles["Bulletx"])


def metric(value, label):
    return [p(value, styles["Metric"]), p(label, styles["MetricLabel"])]


story = []

# Page 1
cover_box = Table([
    [p("SMARTSPINNER v0.4", styles["CoverTitle"])],
    [p("PCB engineering completion and turnkey PCBA request for quotation", styles["CoverSub"])],
    [p("100 mm four-arm persistence-of-vision display with BLE", styles["CoverSub"])],
], colWidths=[176 * mm])
cover_box.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("LEFTPADDING", (0, 0), (-1, -1), 12 * mm),
    ("RIGHTPADDING", (0, 0), (-1, -1), 12 * mm),
    ("TOPPADDING", (0, 0), (-1, 0), 12 * mm),
    ("BOTTOMPADDING", (0, -1), (-1, -1), 10 * mm),
]))
story += [cover_box, Spacer(1, 7 * mm)]
if HERO.exists():
    story += [Image(str(HERO), width=176 * mm, height=72 * mm, kind="proportional"), Spacer(1, 6 * mm)]
metrics = Table([
    metric("100 mm", "outer diameter"),
    metric("4", "main arms"),
    metric("128", "RGB pixels total"),
    metric("10 sets", "requested lot"),
], colWidths=[44 * mm] * 4)
metrics.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), MINT),
    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B8E6D1")),
    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8E6D1")),
    ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story += [metrics, Spacer(1, 5 * mm), p("RELEASE STATUS: ENGINEERING PACKAGE - NOT FOR FABRICATION", styles["Callout"])]
story += [p("The supplied design is intended for supplier engineering review, layout completion, DFM and quotation. Fabrication may start only after the corrected editable KiCad project, final outputs and zero-error DRC reports have been approved in writing.", styles["Bodyx"])]
story += [Spacer(1, 3 * mm), p("Prepared for supplier review | Project owner: German Klimenko", styles["Smallx"])]
story.append(PageBreak())

# Page 2
story += [p("1. Product and electronics architecture", styles["H1x"])]
if HANDHELD.exists():
    img = Image(str(HANDHELD), width=70 * mm, height=72 * mm, kind="proportional")
    body = [
        p("SmartSpinner is a hand-spun POV display. Radial LEDs form a circular image while vertical tip boards form a cylindrical ticker around the outer edge.", styles["Bodyx"]),
        p("One electronic set", styles["H2x"]),
        bullet("1 four-arm main PCB with 80 top SK6805-EC15 RGB pixels"),
        bullet("4 identical tip PCBs with 12 SK6805-EC10 RGB pixels each"),
        bullet("8 independently controlled LED data streams"),
        bullet("nRF52840 BLE, BMI270 IMU and DRV5033 Hall index sensor"),
        bullet("Protected 1S LiPo input, 3.3 V logic and switched 5 V LED rail"),
    ]
    t = Table([[body, img]], colWidths=[100 * mm, 72 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm)]))
    story += [t]
story += [p("Mechanical envelope", styles["H2x"])]
story += [bullet("100 mm outer diameter; four symmetric arms; 608 center bearing"), bullet("Target enclosure thickness approximately 16 mm in v0.3 mechanics"), bullet("Main PCB up to approximately 96 mm envelope, target 1.0 mm four-layer construction"), bullet("Tip PCB target thickness approximately 0.6 mm; supplier to confirm manufacturability")]
story += [p("Critical design principle", styles["H2x"]), p("Heavy components and batteries remain close to the center. Mass distribution must stay four-way symmetric. Component substitutions and copper changes must not create a meaningful imbalance between arms.", styles["Bodyx"])]
story.append(PageBreak())

# Page 3
story += [p("2. Requested supplier engineering work", styles["H1x"])]
steps = [
    ("01", "Audit", "Review the architecture, supplied PCB sources, DRC reports, power budget and mechanical constraints."),
    ("02", "Complete", "Close every open connection and complete charge, boost, switching, protection and decoupling details."),
    ("03", "Verify", "Check exact MPN footprints, pin-1 orientation, RF keep-out, stack-up, clearances and sourcing."),
    ("04", "Return", "Provide editable KiCad sources, zero-error DRC, final Gerber/drill, BOM, CPL, drawings and DFM report."),
]
rows = [[p("Step", styles["Smallx"]), p("Deliverable", styles["Smallx"]), p("Required work", styles["Smallx"])]]
for no, title, desc in steps:
    rows.append([p(no, styles["Metric"]), p(title, styles["H2x"]), p(desc, styles["Bodyx"])])
t = Table(rows, colWidths=[18 * mm, 34 * mm, 120 * mm], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E0E8")),
    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
]))
story += [t, Spacer(1, 5 * mm)]
story += [p("Known status", styles["H2x"])]
status = Table([
    [p("Main PCB", styles["H2x"]), p("68 unconnected items", styles["Bodyx"])],
    [p("Tip PCB", styles["H2x"]), p("4 unconnected items", styles["Bodyx"])],
    [p("Gerbers", styles["H2x"]), p("Review-only; regenerate after design approval", styles["Bodyx"])],
    [p("Footprints", styles["H2x"]), p("Verify against exact selected manufacturer parts", styles["Bodyx"])],
], colWidths=[42 * mm, 130 * mm])
status.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), PALE), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E0E8")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
story += [status, Spacer(1, 4 * mm), p("Fabrication gate", styles["H2x"]), p("Both board types must reach zero copper errors and zero unconnected items. Every remaining ERC/DRC waiver and DFM deviation must be documented and accepted before purchase approval.", styles["Callout"])]
story.append(PageBreak())

# Page 4
story += [p("3. Quotation and first-article plan", styles["H1x"])]
story += [p("Please quote engineering and manufacturing as separate commercial stages.", styles["Bodyx"])]
quote_rows = [
    ["Stage", "Requested quantity / result", "Supplier response"],
    ["Engineering", "Editable KiCad, DRC=0, final outputs, DFM", "Price + lead time + revision rounds"],
    ["First article", "1 main PCB + 4 tip PCBs, assembled and tested", "Price + lead time + test coverage"],
    ["Remaining lot", "9 main PCBs + 36 tip PCBs", "Price + lead time after approval"],
    ["Alternatives", "5, 10 and 25 complete-set breaks", "Unit and total prices"],
    ["Optional", "Programming and functional test", "NRE + unit price"],
    ["Shipping", "Moscow, Russia; no LiPo batteries", "Method + price + delivery estimate"],
]
t = Table([[p(c, styles["Smallx"]) for c in row] for row in quote_rows], colWidths=[34 * mm, 87 * mm, 51 * mm], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E0E8")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
]))
story += [t, Spacer(1, 5 * mm)]
story += [p("Required first-article checks", styles["H2x"]), bullet("AOI and visual inspection"), bullet("Battery, 3.3 V and 5 V rail short-circuit checks"), bullet("Charging, boost and switched LED rail verification with laboratory current limiting"), bullet("MCU programming, BLE, Hall and IMU verification"), bullet("All eight LED streams tested at limited brightness"), bullet("Current, temperature, mechanical fit and static balance recorded")]
story += [p("Approval rule", styles["H2x"]), p("Do not assemble the remaining units until German Klimenko has reviewed the revised design files and accepted the first-article results in writing.", styles["Callout"])]
story += [Spacer(1, 3 * mm), p("Project website: https://germanklimenko.github.io/smartspinner/", styles["Smallx"]), p("Repository: https://github.com/GermanKlimenko/smartspinner", styles["Smallx"])]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc = NumberedDocTemplate(str(OUTPUT))
doc.build(story)
print(OUTPUT)

