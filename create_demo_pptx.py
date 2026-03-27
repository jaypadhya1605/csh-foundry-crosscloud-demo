"""
Generate the CSH Foundry Cross-Cloud Demo PPTX
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ── Color palette ──
BG_DARK     = RGBColor(0x0F, 0x11, 0x1A)
BG_CARD     = RGBColor(0x1A, 0x1D, 0x2E)
ACCENT_BLUE = RGBColor(0x00, 0x78, 0xD4)  # Microsoft blue
ACCENT_CYAN = RGBColor(0x00, 0xBC, 0xD4)
ACCENT_GREEN= RGBColor(0x00, 0xC8, 0x53)
ACCENT_PURP = RGBColor(0x7B, 0x61, 0xFF)
ACCENT_ORG  = RGBColor(0xFF, 0x8C, 0x00)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY  = RGBColor(0xB0, 0xB8, 0xC8)
PASS_GREEN  = RGBColor(0x2E, 0xCC, 0x71)
TEXT_DIM    = RGBColor(0x80, 0x88, 0x9A)


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shape_fill(slide, left, top, width, height, color, radius=0):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_text_box(slide, left, top, width, height, text, font_size=18, color=WHITE, bold=False, align=PP_ALIGN.LEFT, font_name="Segoe UI"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = align
    return txBox


def add_rich_text(slide, left, top, width, height, lines, default_size=16):
    """lines = list of (text, size, color, bold)"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, (text, size, color, bold) in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = text
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.font.name = "Segoe UI"
        p.space_after = Pt(4)
    return txBox


def add_badge(slide, left, top, text, color):
    w, h = Inches(1.1), Inches(0.35)
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(11)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.font.name = "Segoe UI"
    p.alignment = PP_ALIGN.CENTER
    tf.paragraphs[0].space_before = Pt(0)
    tf.paragraphs[0].space_after = Pt(0)
    return shape


def add_pass_badge(slide, left, top):
    return add_badge(slide, left, top, "✓ PASSED", PASS_GREEN)


def add_flow_arrow(slide, left, top, width):
    shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left, top, width, Inches(0.3))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ACCENT_CYAN
    shape.line.fill.background()
    return shape


def add_flow_box(slide, left, top, width, height, text, color):
    shape = add_shape_fill(slide, left, top, width, height, color)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(12)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.font.name = "Segoe UI"
    shape.text_frame.paragraphs[0].space_before = Pt(0)
    return shape


# ═══════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
set_slide_bg(slide, BG_DARK)

# Accent line at top
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_BLUE)

add_text_box(slide, Inches(1), Inches(1.8), Inches(11), Inches(1),
    "CommonSpirit Health × Microsoft", 20, ACCENT_CYAN, False)
add_text_box(slide, Inches(1), Inches(2.4), Inches(11), Inches(1.2),
    "Cross-Cloud Multi-Agent Orchestration", 44, WHITE, True)
add_text_box(slide, Inches(1), Inches(3.5), Inches(11), Inches(0.8),
    "Azure AI Foundry  ·  Microsoft Agent Framework  ·  GCP Cloud Run  ·  BigQuery", 20, LIGHT_GRAY)

# Info badges
add_badge(slide, Inches(1), Inches(4.8), "LIVE DEMO", ACCENT_BLUE)
add_badge(slide, Inches(2.3), Inches(4.8), "March 27", ACCENT_PURP)

add_text_box(slide, Inches(1), Inches(5.8), Inches(11), Inches(0.5),
    "Jay Padhya  ·  Microsoft  ·  Data & AI CSA", 14, TEXT_DIM)

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"Murali, today I'll show you two approaches to the same problem — "
    "how Foundry can orchestrate your GCP-based scheduling agents.\n\n"
    "Part A: Foundry as the platform — headless, event-driven, governed.\n"
    "Part B: Microsoft Agent Framework — code-first, developer-owned, runs anywhere.\n\n"
    "Everything you see is live, terminal-based, no portal needed.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 2 — ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_BLUE)

add_text_box(slide, Inches(0.8), Inches(0.3), Inches(8), Inches(0.6),
    "Architecture Overview", 32, WHITE, True)

# GCP side
add_shape_fill(slide, Inches(0.5), Inches(1.3), Inches(4), Inches(5.5), RGBColor(0x1B, 0x2A, 0x1B))
add_text_box(slide, Inches(0.7), Inches(1.4), Inches(3.5), Inches(0.4),
    "☁  Google Cloud Platform", 16, ACCENT_GREEN, True)

add_flow_box(slide, Inches(0.8), Inches(2.1), Inches(3.3), Inches(0.8),
    "BigQuery\n20 appointments · scheduling data", RGBColor(0x26, 0x73, 0x3B))
add_flow_box(slide, Inches(0.8), Inches(3.2), Inches(3.3), Inches(1.0),
    "Cloud Run Agent\ncsh-scheduling-agent\nFlask + OTel + BigQuery", RGBColor(0x26, 0x73, 0x3B))
add_flow_box(slide, Inches(0.8), Inches(4.6), Inches(3.3), Inches(0.8),
    "OpenTelemetry Exporter\nTraces → Azure App Insights", RGBColor(0x26, 0x73, 0x3B))

# Azure side
add_shape_fill(slide, Inches(5.5), Inches(1.3), Inches(7.3), Inches(5.5), RGBColor(0x14, 0x1E, 0x30))
add_text_box(slide, Inches(5.7), Inches(1.4), Inches(5), Inches(0.4),
    "☁  Microsoft Azure", 16, ACCENT_BLUE, True)

add_flow_box(slide, Inches(5.8), Inches(2.1), Inches(3.3), Inches(1.0),
    "Azure AI Foundry\nOrchestrator Agent\ngpt-5.4-mini", RGBColor(0x00, 0x4E, 0x8C))
add_flow_box(slide, Inches(9.5), Inches(2.1), Inches(3), Inches(1.0),
    "Agent Framework\nCode-first Orchestrator\nPython SDK", RGBColor(0x4B, 0x39, 0xCC))

add_flow_box(slide, Inches(5.8), Inches(3.5), Inches(3.3), Inches(0.7),
    "Azure Storage Queue\nEvent-driven triggers", RGBColor(0x00, 0x4E, 0x8C))
add_flow_box(slide, Inches(9.5), Inches(3.5), Inches(3), Inches(0.7),
    "Agent Catalog\n5 agents · versioned · governed", RGBColor(0x00, 0x4E, 0x8C))

add_flow_box(slide, Inches(5.8), Inches(4.6), Inches(6.7), Inches(0.8),
    "App Insights — Cross-Cloud Observability Dashboard\nGCP + Azure traces · latency · success rates · 100%", RGBColor(0x00, 0x4E, 0x8C))

# Arrows between GCP and Azure
add_flow_arrow(slide, Inches(4.2), Inches(2.5), Inches(1.2))
add_flow_arrow(slide, Inches(4.2), Inches(3.6), Inches(1.2))

# Bottom label
add_text_box(slide, Inches(0.5), Inches(6.0), Inches(4), Inches(0.4),
    "Data stays in GCP — zero migration", 13, ACCENT_GREEN, True)
add_text_box(slide, Inches(5.5), Inches(6.0), Inches(7), Inches(0.4),
    "Orchestration + Governance + Observability in Azure", 13, ACCENT_BLUE, True)

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"Here's the architecture. On the left: your world — GCP, BigQuery, Cloud Run agent. "
    "We didn't move anything. On the right: Azure AI Foundry as the orchestration and governance layer. "
    "Two ways to orchestrate: Foundry platform agents, or the Agent Framework SDK. "
    "All traces from both clouds flow into one App Insights dashboard.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 3 — PART A HEADER
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_BLUE)

add_badge(slide, Inches(1), Inches(2.2), "PART A", ACCENT_BLUE)
add_text_box(slide, Inches(1), Inches(2.8), Inches(11), Inches(1),
    "Foundry Platform", 44, WHITE, True)
add_text_box(slide, Inches(1), Inches(3.8), Inches(11), Inches(0.6),
    "Headless Multi-Agent Orchestration & Governance", 24, ACCENT_CYAN)

lines = [
    ("Step 1    Cross-Cloud Agent Invocation — 3 queries through Foundry → GCP → BigQuery", 16, LIGHT_GRAY, False),
    ("Step 2    Event-Driven Headless Automation — 3 events, zero human interaction", 16, LIGHT_GRAY, False),
    ("Step 3    Agent Catalog & Governance — 5 agents registered, GCP agent visible", 16, LIGHT_GRAY, False),
]
add_rich_text(slide, Inches(1), Inches(4.8), Inches(11), Inches(2), lines)

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"Part A shows Foundry as the platform. The agent is defined in Foundry, "
    "triggered by events, and everything is governed centrally. No code needed on the orchestration side — "
    "just configuration.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 4 — PART A STEP 1: CROSS-CLOUD INVOCATION
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_BLUE)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(8), Inches(0.5),
    "Part A · Step 1 — Cross-Cloud Agent Invocation", 26, WHITE, True)
add_pass_badge(slide, Inches(11.5), Inches(0.35))

# Flow diagram
add_flow_box(slide, Inches(0.5), Inches(1.2), Inches(1.8), Inches(0.6), "User Query", ACCENT_BLUE)
add_flow_arrow(slide, Inches(2.4), Inches(1.35), Inches(0.6))
add_flow_box(slide, Inches(3.1), Inches(1.2), Inches(2.5), Inches(0.6), "Foundry Agent\ngpt-5.4-mini", ACCENT_BLUE)
add_flow_arrow(slide, Inches(5.7), Inches(1.35), Inches(0.6))
add_flow_box(slide, Inches(6.4), Inches(1.2), Inches(2.5), Inches(0.6), "GCP Cloud Run\ncsh-scheduling-agent", ACCENT_GREEN)
add_flow_arrow(slide, Inches(9.0), Inches(1.35), Inches(0.6))
add_flow_box(slide, Inches(9.7), Inches(1.2), Inches(2), Inches(0.6), "BigQuery\n20 appointments", ACCENT_GREEN)

# Results cards
card_top = Inches(2.2)
card_h = Inches(1.5)

# Query 1
c1 = add_shape_fill(slide, Inches(0.3), card_top, Inches(4.1), card_h, BG_CARD)
add_rich_text(slide, Inches(0.5), card_top + Inches(0.1), Inches(3.8), card_h, [
    ("Query 1: Find available Cardiology appointments", 13, ACCENT_CYAN, True),
    ("", 6, WHITE, False),
    ("✓ APT-004 — Dr. Sarah Chen, St. Luke, Mar 25 1:00 PM", 11, PASS_GREEN, False),
    ("✓ APT-010 — Dr. Sarah Chen, St. Luke, Mar 26 11:00 AM", 11, PASS_GREEN, False),
    ("→ 2 slots found via GCP → BigQuery", 11, TEXT_DIM, False),
])

# Query 2
c2 = add_shape_fill(slide, Inches(4.6), card_top, Inches(4.1), card_h, BG_CARD)
add_rich_text(slide, Inches(4.8), card_top + Inches(0.1), Inches(3.8), card_h, [
    ("Query 2: Appointments for patient PAT-003", 13, ACCENT_CYAN, True),
    ("", 6, WHITE, False),
    ("✓ No appointments found for PAT-003", 11, PASS_GREEN, False),
    ("→ GCP agent queried BigQuery, returned 0", 11, TEXT_DIM, False),
])

# Query 3
c3 = add_shape_fill(slide, Inches(8.9), card_top, Inches(4.1), card_h, BG_CARD)
add_rich_text(slide, Inches(9.1), card_top + Inches(0.1), Inches(3.8), card_h, [
    ("Query 3: Cancel appointment APT-005", 13, ACCENT_CYAN, True),
    ("", 6, WHITE, False),
    ("✓ APT-005 already cancelled", 11, PASS_GREEN, False),
    ("→ Agent verified state before acting", 11, TEXT_DIM, False),
])

# Terminal output preview
term_bg = add_shape_fill(slide, Inches(0.3), Inches(4.0), Inches(12.7), Inches(3.2), RGBColor(0x0C, 0x0C, 0x0C))
terminal_text = (
    "PS> python test_new_agent.py\n"
    "============================================================\n"
    "CSH Cross-Cloud Demo: Azure Foundry + GCP Cloud Run + BigQuery\n"
    "============================================================\n"
    "USER: Find available Cardiology appointments\n"
    "  Agent wants 1 tool call(s):\n"
    "     >> Calling GCP agent: action=find_available, params={'specialty': 'Cardiology'}\n"
    "     << GCP returned: 2\n"
    "AGENT RESPONSE:\n"
    "  1. APT-004 — Dr. Sarah Chen, St. Luke Medical Center, Mar 25 1:00 PM\n"
    "  2. APT-010 — Dr. Sarah Chen, St. Luke Medical Center, Mar 26 11:00 AM\n"
    "...\n"
    "DEMO COMPLETE: Cross-cloud flow verified ✓"
)
add_text_box(slide, Inches(0.5), Inches(4.1), Inches(12.3), Inches(3.0),
    terminal_text, 10, ACCENT_GREEN, False, font_name="Cascadia Mono")

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "SCRIPT TO RUN:\n"
    "  cd csh-scheduling-orchestrator\n"
    "  python test_new_agent.py\n\n"
    "TALK TRACK:\n"
    "\"I'm sending natural-language queries to the Foundry orchestrator agent. "
    "Watch the terminal — you'll see it reasons about the query, decides to call the "
    "GCP scheduling agent, which hits BigQuery, and returns real appointment data.\n\n"
    "Query 1 finds 2 Cardiology slots. Query 2 looks up a patient. Query 3 tries to cancel "
    "an already-cancelled appointment — the agent checks the state first.\n\n"
    "Key point: the data never left GCP. Foundry orchestrated the whole thing cross-cloud.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 5 — PART A STEP 2: EVENT-DRIVEN HEADLESS
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_BLUE)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(8), Inches(0.5),
    "Part A · Step 2 — Event-Driven Headless Automation", 26, WHITE, True)
add_pass_badge(slide, Inches(11.5), Inches(0.35))

# Flow
add_flow_box(slide, Inches(0.3), Inches(1.2), Inches(2), Inches(0.6), "EHR / Portal\nCall Center", ACCENT_ORG)
add_flow_arrow(slide, Inches(2.4), Inches(1.35), Inches(0.5))
add_flow_box(slide, Inches(3.0), Inches(1.2), Inches(2.2), Inches(0.6), "Azure Queue\nscheduling-events", ACCENT_BLUE)
add_flow_arrow(slide, Inches(5.3), Inches(1.35), Inches(0.5))
add_flow_box(slide, Inches(5.9), Inches(1.2), Inches(2.2), Inches(0.6), "Foundry Agent\nHeadless", ACCENT_BLUE)
add_flow_arrow(slide, Inches(8.2), Inches(1.35), Inches(0.5))
add_flow_box(slide, Inches(8.8), Inches(1.2), Inches(2), Inches(0.6), "GCP Agent\nBigQuery", ACCENT_GREEN)
add_flow_arrow(slide, Inches(10.9), Inches(1.35), Inches(0.5))
add_flow_box(slide, Inches(11.5), Inches(1.2), Inches(1.5), Inches(0.6), "Result\nAuto-reply", PASS_GREEN)

# Event cards
events_data = [
    ("Event 1: EHR System", "scheduling_request", "Find Cardiology at St. Luke",
     "✓ 2 slots found — APT-004, APT-010", "8.9s"),
    ("Event 2: Patient Portal", "cancellation_request", "Look up patient P-1001 appointments",
     "✓ 2 appointments — APT-001 (booked), APT-011 (no_show)", "12.6s"),
    ("Event 3: Call Center", "scheduling_request", "Find Orthopedics this week",
     "✓ 1 slot found — APT-007, Mercy Hospital", "7.1s"),
]

for i, (title, etype, request, result, duration) in enumerate(events_data):
    top = Inches(2.2) + i * Inches(1.55)
    add_shape_fill(slide, Inches(0.3), top, Inches(12.7), Inches(1.35), BG_CARD)
    add_rich_text(slide, Inches(0.5), top + Inches(0.05), Inches(5), Inches(1.2), [
        (title, 14, ACCENT_CYAN, True),
        (f"Type: {etype}  ·  \"{request}\"", 11, LIGHT_GRAY, False),
    ])
    add_rich_text(slide, Inches(6.5), top + Inches(0.05), Inches(5.5), Inches(1.2), [
        (result, 12, PASS_GREEN, False),
        (f"Processed headlessly in {duration} — zero human interaction", 11, TEXT_DIM, False),
    ])
    add_pass_badge(slide, Inches(12.0), top + Inches(0.15))

# Bottom highlight
add_shape_fill(slide, Inches(0.3), Inches(6.5), Inches(12.7), Inches(0.6), RGBColor(0x13, 0x2B, 0x1A))
add_text_box(slide, Inches(0.5), Inches(6.55), Inches(12), Inches(0.5),
    "3/3 events processed  ·  Zero human interaction  ·  Queue → Agent → GCP → BigQuery → Response", 14, PASS_GREEN, True)

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "SCRIPT TO RUN:\n"
    "  python event_driven_demo.py demo\n\n"
    "TALK TRACK:\n"
    "\"This is the headless workflow you asked for, Murali. Three events arrive in an Azure "
    "Storage Queue — one from the EHR, one from the patient portal, one from a call center.\n\n"
    "No human clicks anything. The processor picks up each event, sends it to the Foundry agent, "
    "the agent reasons about it, calls GCP, queries BigQuery, and returns the result.\n\n"
    "Event 1: finds 2 Cardiology slots. Event 2: looks up patient P-1001's appointments. "
    "Event 3: finds an Orthopedics slot at Mercy Hospital.\n\n"
    "This is exactly the pattern — a message arrives from Pub/Sub or a queue, "
    "an agent kicks off, makes decisions, takes action. No chatbot UI needed.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 6 — PART A STEP 3: AGENT CATALOG
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_BLUE)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(8), Inches(0.5),
    "Part A · Step 3 — Agent Catalog & Governance", 26, WHITE, True)
add_pass_badge(slide, Inches(11.5), Inches(0.35))

# Catalog table
agents = [
    ("csh-scheduling-orchestrator", "prompt", "Azure Foundry orchestrator — routes to GCP", ACCENT_BLUE),
    ("csh-scheduling-gcp-agent", "hosted", "GCP Cloud Run agent — registered in Foundry", ACCENT_GREEN),
    ("foundryiq-demo-agent-001", "prompt", "Demo agent", ACCENT_PURP),
    ("myHealthcare-demo-agent02", "prompt", "Healthcare demo agent", ACCENT_PURP),
    ("myhealthcare-demo-agent01", "prompt", "Healthcare demo agent", ACCENT_PURP),
]

# Header
add_shape_fill(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(0.5), ACCENT_BLUE)
add_text_box(slide, Inches(0.7), Inches(1.32), Inches(4), Inches(0.45), "Agent Name", 13, WHITE, True)
add_text_box(slide, Inches(5.0), Inches(1.32), Inches(1.5), Inches(0.45), "Kind", 13, WHITE, True)
add_text_box(slide, Inches(7.0), Inches(1.32), Inches(5), Inches(0.45), "Description", 13, WHITE, True)

for i, (name, kind, desc, color) in enumerate(agents):
    t = Inches(1.85) + i * Inches(0.6)
    bg_c = BG_CARD if i % 2 == 0 else RGBColor(0x15, 0x18, 0x28)
    add_shape_fill(slide, Inches(0.5), t, Inches(12.3), Inches(0.55), bg_c)
    add_text_box(slide, Inches(0.7), t + Inches(0.05), Inches(4), Inches(0.45), name, 12, WHITE, False, font_name="Cascadia Mono")
    add_badge(slide, Inches(5.0), t + Inches(0.1), kind, color)
    add_text_box(slide, Inches(7.0), t + Inches(0.05), Inches(5), Inches(0.45), desc, 12, LIGHT_GRAY)

# Key callout
add_shape_fill(slide, Inches(0.5), Inches(5.2), Inches(12.3), Inches(1.8), RGBColor(0x13, 0x1E, 0x2B))
add_rich_text(slide, Inches(0.8), Inches(5.3), Inches(11.5), Inches(1.6), [
    ("Governance Capabilities", 16, ACCENT_BLUE, True),
    ("", 6, WHITE, False),
    ("✓  Versioned agents — roll back to any previous version", 13, LIGHT_GRAY, False),
    ("✓  RBAC — control who can invoke, modify, or delete agents", 13, LIGHT_GRAY, False),
    ("✓  Audit trail — every invocation logged in App Insights", 13, LIGHT_GRAY, False),
    ("✓  Cross-cloud — GCP agents registered alongside Azure agents", 13, LIGHT_GRAY, False),
])

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "SCRIPT TO RUN:\n"
    "  python -c \"\n"
    "  import requests\n"
    "  from azure.identity import DefaultAzureCredential\n"
    "  ...(agent catalog listing one-liner)...\n"
    "  \"\n\n"
    "TALK TRACK:\n"
    "\"Here's the single pane of glass you asked for. Five agents registered in one catalog. "
    "Notice csh-scheduling-gcp-agent — that's the GCP Cloud Run agent, registered as 'hosted' in Foundry. "
    "It shows up right next to the Azure-native agents.\n\n"
    "This means: versioning, RBAC, audit trails — all apply to your GCP agent too, "
    "even though it runs on Google Cloud. That's the governance story.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 7 — PART B HEADER
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_PURP)

add_badge(slide, Inches(1), Inches(2.2), "PART B", ACCENT_PURP)
add_text_box(slide, Inches(1), Inches(2.8), Inches(11), Inches(1),
    "Microsoft Agent Framework", 44, WHITE, True)
add_text_box(slide, Inches(1), Inches(3.8), Inches(11), Inches(0.6),
    "Code-First Orchestration — Same Flow, Developer-Owned", 24, ACCENT_CYAN)

lines = [
    ("Step 4    Agent Framework Orchestrator — typed tools, streaming, session management", 16, LIGHT_GRAY, False),
    ("Step 5    Cross-Cloud Observability — GCP traces in Azure App Insights", 16, LIGHT_GRAY, False),
]
add_rich_text(slide, Inches(1), Inches(4.8), Inches(11), Inches(1.5), lines)

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"Part B shows the same cross-cloud flow, but now the orchestrator is built "
    "with the Microsoft Agent Framework SDK. This is code you own, version in Git, "
    "unit test, and deploy anywhere — a laptop, a container, Azure Functions.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 8 — PART B STEP 4: AGENT FRAMEWORK DEMO
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_PURP)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(8), Inches(0.5),
    "Part B · Step 4 — Agent Framework Orchestrator", 26, WHITE, True)
add_pass_badge(slide, Inches(11.5), Inches(0.35))

# Code snippet (left side)
add_shape_fill(slide, Inches(0.3), Inches(1.1), Inches(6.2), Inches(3.8), RGBColor(0x0C, 0x0C, 0x0C))
add_text_box(slide, Inches(0.4), Inches(1.0), Inches(3), Inches(0.3),
    "  agent_framework_demo.py", 10, TEXT_DIM, False, font_name="Cascadia Mono")
code_text = (
    "from agent_framework.azure import AzureAIClient\n"
    "from azure.identity.aio import DefaultAzureCredential\n"
    "\n"
    "# Typed tool — LLM reads this signature\n"
    "def find_available_appointments(\n"
    "    specialty: Annotated[str | None, \"e.g. Cardiology\"] = None,\n"
    "    location: Annotated[str | None, \"Facility\"] = None,\n"
    ") -> str:\n"
    "    return _call_gcp_sync(\"find_available\", params)\n"
    "\n"
    "async with AzureAIClient(\n"
    "    project_endpoint=PROJECT_ENDPOINT,\n"
    "    model_deployment_name=\"gpt-5.4-mini\",\n"
    "    credential=credential,\n"
    ").as_agent(\n"
    "    name=\"csh-scheduling-orchestrator\",\n"
    "    instructions=AGENT_INSTRUCTIONS,\n"
    "    tools=[find_available, cancel, rebook],\n"
    ") as agent:\n"
    "    stream = agent.run(query, stream=True)"
)
add_text_box(slide, Inches(0.5), Inches(1.35), Inches(5.8), Inches(3.5),
    code_text, 10, ACCENT_GREEN, False, font_name="Cascadia Mono")

# Results (right side)
add_shape_fill(slide, Inches(6.8), Inches(1.1), Inches(6.2), Inches(3.8), BG_CARD)
add_text_box(slide, Inches(7.0), Inches(1.15), Inches(5.5), Inches(0.3),
    "Live Output", 14, ACCENT_CYAN, True)

results_text = (
    "USER: Find available Cardiology appointments\n"
    "  >> [GCP Tool Call] action=find_available\n"
    "  << [GCP Response] count=2\n"
    "AGENT: APT-004 Dr. Sarah Chen, Mar 25 1:00 PM\n"
    "       APT-010 Dr. Sarah Chen, Mar 26 11:00 AM\n"
    "\n"
    "USER: Show appointments for patient PAT-003\n"
    "  >> [GCP Tool Call] action=patient_appointments\n"
    "  << [GCP Response] count=0\n"
    "AGENT: No appointments found for PAT-003\n"
    "\n"
    "USER: Cancel appointment APT-005\n"
    "  >> [GCP Tool Call] action=cancel\n"
    "  << [GCP Response] already cancelled\n"
    "AGENT: APT-005 is already cancelled\n"
    "\n"
    "DEMO COMPLETE — Agent Framework + Foundry + GCP ✓"
)
add_text_box(slide, Inches(7.0), Inches(1.5), Inches(5.8), Inches(3.3),
    results_text, 10, PASS_GREEN, False, font_name="Cascadia Mono")

# Comparison row
comp_data = [
    ("AzureAIClient", "Code-first client\nnot portal config", ACCENT_PURP),
    ("Typed Tools", "Python functions\nwith Annotated[]", ACCENT_PURP),
    ("Streaming", "agent.run()\nstream=True", ACCENT_PURP),
    ("Session", "Multi-turn context\npersisted", ACCENT_PURP),
    ("Portable", "Runs anywhere\nlaptop/ACA/Functions", ACCENT_PURP),
]
for i, (title, desc, color) in enumerate(comp_data):
    left = Inches(0.3) + i * Inches(2.6)
    add_shape_fill(slide, left, Inches(5.2), Inches(2.4), Inches(1.0), RGBColor(0x2A, 0x22, 0x50))
    add_rich_text(slide, left + Inches(0.15), Inches(5.25), Inches(2.2), Inches(0.9), [
        (title, 13, ACCENT_CYAN, True),
        (desc, 10, LIGHT_GRAY, False),
    ])

# Bottom
add_text_box(slide, Inches(0.5), Inches(6.5), Inches(12), Inches(0.5),
    "Same cross-cloud flow  ·  Same GCP agent  ·  Same BigQuery data  ·  Developer-owned orchestration", 13, TEXT_DIM, True)

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "SCRIPT TO RUN:\n"
    "  python agent_framework_demo.py\n\n"
    "TALK TRACK:\n"
    "\"Now the same demo, but with the Microsoft Agent Framework SDK. "
    "On the left, you can see the code — AzureAIClient, typed Python tool functions "
    "with Annotated types, async/await, streaming.\n\n"
    "The LLM reads these function signatures to decide which tool to call. "
    "Same 3 queries, same GCP agent, same BigQuery data — but now your developer owns the logic.\n\n"
    "This is versionable in Git, unit testable, deployable as a container or Azure Function. "
    "You're not locked into a portal configuration.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 9 — PART B STEP 5: OBSERVABILITY
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_PURP)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(8), Inches(0.5),
    "Part B · Step 5 — Cross-Cloud Observability", 26, WHITE, True)
add_pass_badge(slide, Inches(11.5), Inches(0.35))

# Dashboard sections
sections = [
    ("1. GCP Cloud Run — Request Traces", "5 requests · 100% success · avg 874ms", "csh-scheduling-agent spans via OTel"),
    ("2. GCP Agent — BigQuery Calls", "10 spans · BigQuery.job.begin · getQueryResults", "Sub-operation visibility"),
    ("3. Azure Foundry — Agent & LLM Calls", "10 spans · invoke_agent + chat gpt-5.4-mini", "Foundry-native telemetry"),
    ("4. Performance Summary", "4 components · 100% success · P95 < 1.5s", "Single-pane cross-cloud metrics"),
    ("5. Errors & Failures", "No errors in last 24h", "Clean production run"),
    ("6. Cross-Cloud Trace IDs", "5 trace IDs · W3C Trace Context", "End-to-end correlation"),
]

for i, (title, metric, detail) in enumerate(sections):
    col = i % 3
    row = i // 3
    left = Inches(0.3) + col * Inches(4.3)
    top = Inches(1.1) + row * Inches(1.8)

    add_shape_fill(slide, left, top, Inches(4.1), Inches(1.6), BG_CARD)
    add_rich_text(slide, left + Inches(0.15), top + Inches(0.1), Inches(3.8), Inches(1.4), [
        (title, 12, ACCENT_CYAN, True),
        ("", 4, WHITE, False),
        (metric, 14, WHITE, True),
        (detail, 10, TEXT_DIM, False),
    ])

# Summary bar
add_shape_fill(slide, Inches(0.3), Inches(5.0), Inches(12.7), Inches(0.7), RGBColor(0x13, 0x2B, 0x1A))
summary_items = [
    ("GCP → Azure", "CONNECTED", Inches(0.5)),
    ("Foundry → Azure", "NATIVE", Inches(3.5)),
    ("Success Rate", "100%", Inches(6.5)),
    ("Components", "4 monitored", Inches(9.5)),
]
for label, value, left in summary_items:
    add_rich_text(slide, left, Inches(5.05), Inches(2.5), Inches(0.6), [
        (label, 10, TEXT_DIM, False),
        (value, 16, PASS_GREEN, True),
    ])

# App Insights trace view description
add_shape_fill(slide, Inches(0.3), Inches(5.9), Inches(12.7), Inches(1.3), RGBColor(0x14, 0x1E, 0x30))
add_rich_text(slide, Inches(0.5), Inches(6.0), Inches(12), Inches(1.1), [
    ("Portal: End-to-End Transaction View (App Insights → Search)", 13, ACCENT_BLUE, True),
    ("", 4, WHITE, False),
    ("POST /invoke → agent_invoke → find_available_appointments → BigQuery.job.begin → BigQuery.getQueryResults", 11, LIGHT_GRAY, False),
    ("Full waterfall trace showing GCP Cloud Run spans inside Azure App Insights — proves cross-cloud observability", 11, TEXT_DIM, False),
])

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "SCRIPT TO RUN:\n"
    "  python observability_dashboard.py\n\n"
    "THEN SHOW IN PORTAL:\n"
    "  App Insights → Search → click any request → End-to-end transaction details\n\n"
    "TALK TRACK:\n"
    "\"This is the single pane of glass. Our dashboard pulls from App Insights using KQL. "
    "6 sections: GCP request traces, BigQuery sub-operations, Foundry agent invocations, "
    "performance summary, errors, and cross-cloud trace IDs.\n\n"
    "100% success rate. GCP traces flowing into Azure via OpenTelemetry. "
    "P95 latency under 1.5 seconds.\n\n"
    "If I flip to the portal — here's an end-to-end transaction: "
    "POST /invoke → agent_invoke → find_available_appointments → BigQuery.job.begin → getQueryResults. "
    "One trace, two clouds, full visibility.\n\n"
    "This is what 'I don't have a single pane of dashboard' looks like when it's solved.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 10 — COMPARISON: PLATFORM vs FRAMEWORK
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_CYAN)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.5),
    "Two Approaches — Complementary, Not Competing", 28, WHITE, True)

# Table header
add_shape_fill(slide, Inches(0.5), Inches(1.2), Inches(3.5), Inches(0.5), RGBColor(0x33, 0x33, 0x44))
add_text_box(slide, Inches(0.7), Inches(1.22), Inches(3), Inches(0.45), "Dimension", 13, TEXT_DIM, True)
add_shape_fill(slide, Inches(4.1), Inches(1.2), Inches(4.3), Inches(0.5), ACCENT_BLUE)
add_text_box(slide, Inches(4.3), Inches(1.22), Inches(4), Inches(0.45), "Part A: Foundry Platform", 13, WHITE, True)
add_shape_fill(slide, Inches(8.5), Inches(1.2), Inches(4.3), Inches(0.5), ACCENT_PURP)
add_text_box(slide, Inches(8.7), Inches(1.22), Inches(4), Inches(0.45), "Part B: Agent Framework", 13, WHITE, True)

rows = [
    ("Agent defined in", "Foundry portal / API", "Python code"),
    ("Who owns logic", "Platform managed", "Developer owned"),
    ("Governance", "Built-in (catalog, RBAC, audit)", "Register via Foundry API"),
    ("Event-driven", "Queue → Foundry agent → auto", "Build your own triggers"),
    ("Deployment", "Foundry managed infra", "Anywhere: laptop, ACA, Functions"),
    ("Best for", "Ops teams, governed workflows", "Dev teams, custom logic, CI/CD"),
    ("Cross-cloud", "Same — routes to GCP", "Same — routes to GCP"),
    ("Observability", "Same — App Insights", "Same — App Insights"),
]

for i, (dim, platform, framework) in enumerate(rows):
    t = Inches(1.75) + i * Inches(0.55)
    bg_c = BG_CARD if i % 2 == 0 else RGBColor(0x15, 0x18, 0x28)
    add_shape_fill(slide, Inches(0.5), t, Inches(3.5), Inches(0.5), bg_c)
    add_text_box(slide, Inches(0.7), t + Inches(0.03), Inches(3), Inches(0.45), dim, 12, ACCENT_CYAN, True)
    add_shape_fill(slide, Inches(4.1), t, Inches(4.3), Inches(0.5), bg_c)
    add_text_box(slide, Inches(4.3), t + Inches(0.03), Inches(4), Inches(0.45), platform, 12, LIGHT_GRAY)
    add_shape_fill(slide, Inches(8.5), t, Inches(4.3), Inches(0.5), bg_c)
    add_text_box(slide, Inches(8.7), t + Inches(0.03), Inches(4), Inches(0.45), framework, 12, LIGHT_GRAY)

# Bottom message
add_shape_fill(slide, Inches(0.5), Inches(6.2), Inches(12.3), Inches(0.8), RGBColor(0x13, 0x2A, 0x2A))
add_text_box(slide, Inches(0.7), Inches(6.3), Inches(11.8), Inches(0.6),
    "Build with Agent Framework  →  Govern with Foundry  →  Observe in App Insights", 18, ACCENT_CYAN, True, PP_ALIGN.CENTER)

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"So which one should you use? Both. They're complementary.\n\n"
    "Foundry Platform is for ops teams who want governed, event-driven workflows "
    "without writing orchestration code.\n\n"
    "Agent Framework is for dev teams who want full control — code-first, "
    "unit testable, deployable anywhere.\n\n"
    "Both route to GCP. Both show up in App Insights. Both are governed.\n\n"
    "The message: build with the Agent Framework, govern with Foundry, observe in App Insights.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 11 — ALL STEPS PASSED SUMMARY
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), PASS_GREEN)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
    "Demo Results — All Steps Passed", 32, WHITE, True)

steps = [
    ("Part A", "Step 1", "Cross-Cloud Foundry Invocation", "3 queries → GCP → BigQuery", "PASSED"),
    ("Part A", "Step 2", "Event-Driven Headless Automation", "3 events, zero human interaction", "PASSED"),
    ("Part A", "Step 3", "Agent Catalog & Governance", "5 agents, GCP visible as hosted", "PASSED"),
    ("Part B", "Step 4", "Agent Framework Orchestrator", "3 queries, code-first, streaming", "PASSED"),
    ("Part B", "Step 5", "Cross-Cloud Observability", "100% success, GCP traces in Azure", "PASSED"),
]

for i, (part, step, title, result, status) in enumerate(steps):
    t = Inches(1.3) + i * Inches(0.95)
    add_shape_fill(slide, Inches(0.5), t, Inches(12.3), Inches(0.8), BG_CARD)
    add_badge(slide, Inches(0.7), t + Inches(0.2), part, ACCENT_BLUE if part == "Part A" else ACCENT_PURP)
    add_text_box(slide, Inches(2.0), t + Inches(0.05), Inches(1.5), Inches(0.35), step, 12, TEXT_DIM, True)
    add_text_box(slide, Inches(2.0), t + Inches(0.38), Inches(5), Inches(0.35), title, 16, WHITE, True)
    add_text_box(slide, Inches(7.0), t + Inches(0.2), Inches(4), Inches(0.4), result, 13, LIGHT_GRAY)
    add_pass_badge(slide, Inches(11.5), t + Inches(0.2))

# Bottom stats
stats = [
    ("Total Queries", "9"),
    ("Events Processed", "3"),
    ("Success Rate", "100%"),
    ("Agents Registered", "5"),
    ("Clouds Connected", "2"),
]
for i, (label, value) in enumerate(stats):
    left = Inches(0.5) + i * Inches(2.5)
    add_shape_fill(slide, left, Inches(6.2), Inches(2.3), Inches(0.9), RGBColor(0x13, 0x2B, 0x1A))
    add_rich_text(slide, left + Inches(0.15), Inches(6.25), Inches(2), Inches(0.8), [
        (value, 24, PASS_GREEN, True),
        (label, 11, TEXT_DIM, False),
    ])

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"Every step passed. 9 queries across both approaches, 3 headless events, "
    "100% success rate, 5 agents in the catalog, 2 clouds connected.\n\n"
    "This is what we built together in a matter of days — "
    "not a slide deck, not a mock, but a working cross-cloud system.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 12 — MURALI'S 6 ASKS MAPPED
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_BLUE)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
    "Mapping to Murali's Requirements", 28, WHITE, True)

asks = [
    ("1", "Unified multi-agent orchestration platform", "Foundry as central orchestrator, Agent Framework for code-first", "✓ Demonstrated"),
    ("2", "Event-driven headless workflows", "Queue → Foundry → GCP — zero human interaction", "✓ Demonstrated"),
    ("3", "Cross-cloud GCP/BigQuery integration", "Data stays in GCP, Foundry orchestrates cross-cloud", "✓ Demonstrated"),
    ("4", "Governance & observability across all agents", "Agent catalog + App Insights with GCP OTel traces", "✓ Demonstrated"),
    ("5", "Practical business use cases", "Scheduling: find, cancel, rebook, patient lookup", "✓ Demonstrated"),
    ("6", "Sandbox with network constraints", "Full demo runs in terminal — no ai.azure.com needed", "✓ Demonstrated"),
]

for i, (num, ask, how, status) in enumerate(asks):
    t = Inches(1.2) + i * Inches(0.95)
    add_shape_fill(slide, Inches(0.5), t, Inches(12.3), Inches(0.8), BG_CARD)

    # Number circle
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.7), t + Inches(0.15), Inches(0.5), Inches(0.5))
    circle.fill.solid()
    circle.fill.fore_color.rgb = ACCENT_BLUE
    circle.line.fill.background()
    tf = circle.text_frame
    tf.paragraphs[0].text = num
    tf.paragraphs[0].font.size = Pt(16)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    add_text_box(slide, Inches(1.4), t + Inches(0.05), Inches(5), Inches(0.35), ask, 14, WHITE, True)
    add_text_box(slide, Inches(1.4), t + Inches(0.4), Inches(5.5), Inches(0.35), how, 11, TEXT_DIM)
    add_pass_badge(slide, Inches(11.5), t + Inches(0.2))

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"Murali, let me map what you saw to your 6 asks from our last call.\n\n"
    "1. Unified platform — check. Foundry + Agent Framework.\n"
    "2. Headless workflows — check. Queue-driven, zero clicks.\n"
    "3. Cross-cloud GCP — check. Data stayed in BigQuery.\n"
    "4. Governance + observability — check. Catalog + App Insights.\n"
    "5. Business use cases — check. Real scheduling operations.\n"
    "6. Network constraints — check. Everything ran in the terminal.\n\n"
    "All six asks addressed in one demo.\""
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 13 — NEXT STEPS
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_shape_fill(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), ACCENT_BLUE)

add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
    "Next Steps", 32, WHITE, True)

next_items = [
    ("Prioritize Use Cases", "Murali to confirm priority: denials & appeals, revenue cycle, or scheduling expansion", ACCENT_ORG),
    ("Expand Scheduling Agents", "Add triage agent, booking confirmation, no-show follow-up — full multi-agent workflow", ACCENT_BLUE),
    ("Sandbox Access", "Set up Foundry project accessible from CSH network (CLI/SDK based, no portal dependency)", ACCENT_PURP),
    ("Production Architecture", "Connect to real EHR triggers (HL7/FHIR), production BigQuery datasets", ACCENT_GREEN),
]

for i, (title, desc, color) in enumerate(next_items):
    t = Inches(1.3) + i * Inches(1.3)
    # Number
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.7), t + Inches(0.1), Inches(0.55), Inches(0.55))
    circle.fill.solid()
    circle.fill.fore_color.rgb = color
    circle.line.fill.background()
    tf = circle.text_frame
    tf.paragraphs[0].text = str(i + 1)
    tf.paragraphs[0].font.size = Pt(18)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    add_shape_fill(slide, Inches(1.5), t, Inches(11.3), Inches(0.9), BG_CARD)
    add_text_box(slide, Inches(1.7), t + Inches(0.05), Inches(10.8), Inches(0.4), title, 18, WHITE, True)
    add_text_box(slide, Inches(1.7), t + Inches(0.45), Inches(10.8), Inches(0.4), desc, 13, LIGHT_GRAY)

notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"For next steps:\n\n"
    "1. You mentioned denials & appeals and scheduling — let us know which to prioritize.\n"
    "2. We can expand this to a full multi-agent workflow — triage, booking, follow-up.\n"
    "3. We'll set up a sandbox that works within your network constraints — all CLI/SDK.\n"
    "4. When ready, we connect to real EHR triggers and production BigQuery.\n\n"
    "What we showed today is a working prototype. The path to production is clear.\""
)


# ═══════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════
output_path = r"c:\Users\jaypadhya\OneDrive - Microsoft\Desktop\CommonSpirit\use case 1\CSH_Foundry_CrossCloud_Demo.pptx"
prs.save(output_path)
print(f"PPTX saved to: {output_path}")
print(f"Slides: {len(prs.slides)}")
