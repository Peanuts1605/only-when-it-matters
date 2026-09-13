"""Export an honest, dependency-light architecture PDF using ReportLab."""

from math import hypot
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
INK = HexColor("#10241f")
QUIET = HexColor("#53695f")
PAPER = HexColor("#f7f5ef")
MINT = HexColor("#dcefe5")
CORAL = HexColor("#ffe0d9")


def build() -> Path:
    target = ROOT / "site" / "architecture.pdf"
    c = canvas.Canvas(str(target), pagesize=(1000, 740), invariant=1)
    c.setTitle("Only When It Matters — implemented architecture")
    c.setAuthor("Only When It Matters")
    c.setFillColor(PAPER)
    c.rect(0, 0, 1000, 740, fill=1, stroke=0)

    def text(x, y, value, size=12, bold=False, color=INK):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, value)

    def box(x, y, w, title, lines, fill=MINT):
        c.setFillColor(fill)
        c.roundRect(x, y, w, 76, 10, fill=1, stroke=0)
        text(x + 14, y + 52, title, 13, True)
        for index, line in enumerate(lines):
            text(x + 14, y + 32 - 15 * index, line, 10, color=QUIET)

    def arrow(x1, y1, x2, y2, dashed=False):
        c.setStrokeColor(QUIET)
        c.setLineWidth(1.6)
        c.setDash(5, 4) if dashed else c.setDash()
        c.line(x1, y1, x2, y2)
        c.setDash()
        length = hypot(x2 - x1, y2 - y1)
        dx, dy = (x2 - x1) / length, (y2 - y1) / length
        path = c.beginPath()
        path.moveTo(x2 - 7 * dx - 4 * dy, y2 - 7 * dy + 4 * dx)
        path.lineTo(x2, y2)
        path.lineTo(x2 - 7 * dx + 4 * dy, y2 - 7 * dy - 4 * dx)
        c.drawPath(path)

    text(42, 697, "ONLY WHEN IT MATTERS", 12, True, QUIET)
    text(42, 653, "One saved decision. No repeated action.", 29, True)
    text(42, 624, "Implemented prototype | September 13, 2026 | No model calls in the public fixture", 13)

    text(42, 579, "VERIFIED FIXTURE PATH", 11, True, QUIET)
    box(42, 482, 205, "Fictional input", ["5 deliveries / 4 unique events", "tests/fixtures.json"])
    box(295, 482, 205, "Direct Python replay", ["cli.run_scenario", "No agent or model invocation"])
    box(550, 482, 205, "Policy + EventStore", ["New ID: classify and save", "Repeat ID: no action"])
    box(805, 482, 155, "SQLite ledger", ["First decision retained", "Unique-event metrics"])
    arrow(247, 520, 295, 520)
    arrow(500, 520, 550, 520)
    arrow(755, 520, 805, 520)

    box(550, 343, 205, "Delivery result", ["Duplicate: interrupt = false", "exact_action = null"])
    box(805, 343, 155, "Static judge page", ["report.json + app.js", "Replay refetches JSON"])
    arrow(650, 482, 650, 419)
    arrow(755, 381, 805, 381)

    text(42, 423, "SEPARATE STRANDS INTEGRATION", 11, True, QUIET)
    box(42, 318, 205, "Local Qwen + Strands", ["Real triage execution verified", "Strict sequence: FAIL"], CORAL)
    box(295, 318, 205, "Registered tools", ["Model called retry twice", "Both retries returned quiet"], CORAL)
    arrow(247, 356, 295, 356, dashed=True)
    arrow(500, 356, 530, 356, dashed=True)
    c.setStrokeColor(QUIET)
    c.setDash(5, 4)
    c.line(530, 356, 530, 462)
    c.line(530, 462, 650, 462)
    c.setDash()
    arrow(650, 462, 650, 482, dashed=True)
    text(42, 288, "Solid: fixture flow. Dashed: separate real-model partial proof; complete sequence not accepted.", 11)

    c.setStrokeColor(HexColor("#bdcac2"))
    c.line(42, 261, 958, 261)
    text(42, 231, "WHAT THE NUMBERS MEAN", 11, True, QUIET)
    text(42, 207, "4 unique events  /  2 quiet decisions  /  2 escalation decisions  /  1 quiet duplicate", 15, True)
    text(42, 183, "These are fixture policy decisions, not delivered notifications, verified wins, or measured time saved.", 12)
    text(42, 143, "TRUST BOUNDARY", 11, True, QUIET)
    text(42, 119, "Event labels and IDs are trusted inputs. No live inbox, sender verification, or final-model-output enforcement.", 12)
    text(42, 98, "One shared store is thread-safe. Separate processes, reused IDs with changed content and expiry need more work.", 12)
    text(42, 53, "Source: github.com/Peanuts1605/only-when-it-matters | MIT | See docs/architecture.md for limits", 11, color=QUIET)
    c.save()
    return target


if __name__ == "__main__":
    print(build())
