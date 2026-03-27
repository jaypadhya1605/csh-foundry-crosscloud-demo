"""
Insert a numbered cross-cloud flow diagram slide into the existing PPTX
between slide 2 (Architecture) and slide 3 (Part A Header).
Uses Azure blue for Microsoft components, green/yellow for GCP.
"""
import copy
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from lxml import etree

INPUT  = r"c:\Users\jaypadhya\OneDrive - Microsoft\Desktop\CommonSpirit\use case 1\CSH_Foundry_CrossCloud_Demo.pptx"
OUTPUT = r"c:\Users\jaypadhya\OneDrive - Microsoft\Desktop\CommonSpirit\use case 1\CSH_Foundry_CrossCloud_Demo.pptx"

prs = Presentation(INPUT)

# ── Colors ──
BG_DARK      = RGBColor(0x0F, 0x11, 0x1A)
AZURE_BLUE   = RGBColor(0x00, 0x78, 0xD4)
AZURE_DARK   = RGBColor(0x00, 0x4E, 0x8C)
AZURE_PURPLE = RGBColor(0x7B, 0x61, 0xFF)
GCP_GREEN    = RGBColor(0x34, 0xA8, 0x53)
GCP_YELLOW   = RGBColor(0xFB, 0xBC, 0x04)
GCP_DARK_GRN = RGBColor(0x1E, 0x8E, 0x3E)
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY   = RGBColor(0xB0, 0xB8, 0xC8)
ACCENT_CYAN  = RGBColor(0x00, 0xBC, 0xD4)
ARROW_CYAN   = RGBColor(0x00, 0xBC, 0xD4)
NUMBER_BG    = RGBColor(0xFF, 0xFF, 0xFF)
TEXT_DIM     = RGBColor(0x80, 0x88, 0x9A)
CARD_BG      = RGBColor(0x1A, 0x1D, 0x2E)

# ── Helpers ──

def set_slide_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_shape(slide, left, top, width, height, color, shape_type=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape_type, left, top, width, height)
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    s.shadow.inherit = False
    return s

def add_textbox(slide, left, top, width, height, text, size=18, color=WHITE, bold=False, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = "Segoe UI"
    p.alignment = align
    return tb

def add_number_circle(slide, left, top, number, bg_color=AZURE_BLUE):
    """Add a numbered circle (step indicator)."""
    size = Inches(0.45)
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, size, size)
    s.fill.solid()
    s.fill.fore_color.rgb = bg_color
    s.line.fill.background()
    tf = s.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = str(number)
    p.font.size = Pt(16)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.font.name = "Segoe UI"
    p.alignment = PP_ALIGN.CENTER
    tf.paragraphs[0].space_before = Pt(0)
    tf.paragraphs[0].space_after = Pt(0)
    return s

def add_flow_box(slide, left, top, width, height, title, subtitle, color):
    """Box with title and subtitle text."""
    s = add_shape(slide, left, top, width, height, color)
    tf = s.text_frame
    tf.word_wrap = True
    # Title
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(13)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.font.name = "Segoe UI"
    p.alignment = PP_ALIGN.CENTER
    p.space_after = Pt(2)
    # Subtitle
    p2 = tf.add_paragraph()
    p2.text = subtitle
    p2.font.size = Pt(10)
    p2.font.color.rgb = LIGHT_GRAY
    p2.font.bold = False
    p2.font.name = "Segoe UI"
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(0)
    return s

def add_arrow(slide, left, top, width, color=ARROW_CYAN, direction="right"):
    shape_type = MSO_SHAPE.RIGHT_ARROW if direction == "right" else MSO_SHAPE.DOWN_ARROW
    h = Inches(0.25) if direction == "right" else width
    w = width if direction == "right" else Inches(0.25)
    s = slide.shapes.add_shape(shape_type, left, top, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    s.shadow.inherit = False
    return s

def add_return_arrow(slide, left, top, width, color=ACCENT_CYAN):
    """Left-pointing return arrow."""
    s = slide.shapes.add_shape(MSO_SHAPE.LEFT_ARROW, left, top, width, Inches(0.2))
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    s.shadow.inherit = False
    return s


# ═══════════════════════════════════════════════════════════════
# BUILD THE FLOW DIAGRAM SLIDE
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
set_slide_bg(slide, BG_DARK)

# Top accent bar
add_shape(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), AZURE_BLUE)

# Title
add_textbox(slide, Inches(0.6), Inches(0.2), Inches(10), Inches(0.5),
            "Cross-Cloud Request Flow", 30, WHITE, True)
add_textbox(slide, Inches(0.6), Inches(0.65), Inches(10), Inches(0.4),
            "How a single question flows from VS Code → Azure Foundry → GCP → BigQuery and back", 13, TEXT_DIM)

# ── ZONE BACKGROUNDS ──

# Left zone: YOU (neutral dark)
add_shape(slide, Inches(0.3), Inches(1.3), Inches(2.0), Inches(5.5), CARD_BG)
add_textbox(slide, Inches(0.4), Inches(1.35), Inches(1.8), Inches(0.3),
            "VS CODE", 11, LIGHT_GRAY, True, PP_ALIGN.CENTER)

# Middle zone: AZURE (blue tint)
add_shape(slide, Inches(2.6), Inches(1.3), Inches(4.8), Inches(5.5), RGBColor(0x0C, 0x1A, 0x30))
add_textbox(slide, Inches(2.7), Inches(1.35), Inches(4.6), Inches(0.3),
            "MICROSOFT AZURE", 11, AZURE_BLUE, True, PP_ALIGN.CENTER)

# Right zone: GCP (green tint)
add_shape(slide, Inches(7.7), Inches(1.3), Inches(5.3), Inches(5.5), RGBColor(0x14, 0x26, 0x14))
add_textbox(slide, Inches(7.8), Inches(1.35), Inches(5.1), Inches(0.3),
            "GOOGLE CLOUD PLATFORM", 11, GCP_GREEN, True, PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════
# STEP 1 — User asks question in VS Code
# ═══════════════════════════════════════════════════════════════
y_row1 = Inches(2.0)

add_number_circle(slide, Inches(0.45), y_row1, 1, AZURE_BLUE)
add_flow_box(slide, Inches(0.45), Inches(2.5), Inches(1.7), Inches(1.0),
             "User Question", "\"Find me a cardiology\nappointment\"", CARD_BG)

# Arrow 1→2
add_arrow(slide, Inches(2.2), Inches(2.85), Inches(0.55))

# ═══════════════════════════════════════════════════════════════
# STEP 2 — Foundry Agent receives + reasons
# ═══════════════════════════════════════════════════════════════
add_number_circle(slide, Inches(2.85), y_row1, 2, AZURE_BLUE)
add_flow_box(slide, Inches(2.85), Inches(2.5), Inches(2.0), Inches(1.0),
             "Azure AI Foundry", "GPT-4o-mini reasons:\n\"I need scheduling data\"", AZURE_DARK)

# ═══════════════════════════════════════════════════════════════
# STEP 3 — Foundry decides to call GCP tool
# ═══════════════════════════════════════════════════════════════
add_number_circle(slide, Inches(5.1), y_row1, 3, AZURE_BLUE)
add_flow_box(slide, Inches(5.1), Inches(2.5), Inches(2.0), Inches(1.0),
             "Tool Decision", "Foundry selects:\ncall_gcp_agent()", AZURE_PURPLE)

# Arrow 2→3
add_arrow(slide, Inches(4.9), Inches(2.85), Inches(0.3))

# Arrow 3→4 (cross-cloud)
add_arrow(slide, Inches(7.15), Inches(2.85), Inches(0.65), GCP_YELLOW)

# ═══════════════════════════════════════════════════════════════
# STEP 4 — GCP Cloud Run receives the call
# ═══════════════════════════════════════════════════════════════
add_number_circle(slide, Inches(7.95), y_row1, 4, GCP_GREEN)
add_flow_box(slide, Inches(7.95), Inches(2.5), Inches(2.2), Inches(1.0),
             "GCP Cloud Run", "csh-scheduling-agent\nreceives /invoke", GCP_DARK_GRN)

# ═══════════════════════════════════════════════════════════════
# STEP 5 — BigQuery query
# ═══════════════════════════════════════════════════════════════
add_number_circle(slide, Inches(10.5), y_row1, 5, GCP_GREEN)
add_flow_box(slide, Inches(10.5), Inches(2.5), Inches(2.2), Inches(1.0),
             "BigQuery", "SELECT * FROM\nappointments\nWHERE specialty=...", GCP_DARK_GRN)

# Arrow 4→5
add_arrow(slide, Inches(10.2), Inches(2.85), Inches(0.35), GCP_YELLOW)


# ═══════════════════════════════════════════════════════════════
# RETURN PATH (Row 2) — Steps 6, 7, 8
# ═══════════════════════════════════════════════════════════════
y_row2 = Inches(4.0)

# Step 6 — BigQuery returns data
add_number_circle(slide, Inches(10.5), y_row2, 6, GCP_YELLOW)
add_flow_box(slide, Inches(10.5), Inches(4.5), Inches(2.2), Inches(0.9),
             "Query Results", "2 cardiology slots\nAPT-004, APT-010", GCP_DARK_GRN)

# Down arrow from step 5 to step 6
add_arrow(slide, Inches(11.45), Inches(3.55), Inches(0.45), GCP_YELLOW, "down")

# Return arrow 6→7
add_return_arrow(slide, Inches(7.95), Inches(4.8), Inches(2.5), GCP_YELLOW)

# Step 7 — GCP returns to Foundry
add_number_circle(slide, Inches(5.1), y_row2, 7, AZURE_BLUE)
add_flow_box(slide, Inches(5.1), Inches(4.5), Inches(2.6), Inches(0.9),
             "Foundry Formats", "GPT-4o-mini writes\nfriendly response", AZURE_DARK)

# Return arrow 7→8
add_return_arrow(slide, Inches(2.2), Inches(4.8), Inches(2.85), AZURE_BLUE)

# Step 8 — User sees response
add_number_circle(slide, Inches(0.45), y_row2, 8, AZURE_BLUE)
add_flow_box(slide, Inches(0.45), Inches(4.5), Inches(1.7), Inches(0.9),
             "Response", "\"APT-004 with\nDr. Sarah Chen\nat 1:00 PM\"", CARD_BG)


# ═══════════════════════════════════════════════════════════════
# OBSERVABILITY STRIP (bottom)
# ═══════════════════════════════════════════════════════════════
y_obs = Inches(5.8)

# Observability bar spanning full width
add_shape(slide, Inches(0.3), y_obs, Inches(12.7), Inches(0.75), RGBColor(0x12, 0x14, 0x20))

add_textbox(slide, Inches(0.5), Inches(5.85), Inches(2), Inches(0.35),
            "OBSERVABILITY", 10, ACCENT_CYAN, True)

add_textbox(slide, Inches(0.5), Inches(6.1), Inches(4), Inches(0.35),
            "Every step traced in Foundry Portal + GCP Cloud Trace", 10, LIGHT_GRAY)

# Trace badges
obs_y = Inches(5.88)
add_flow_box(slide, Inches(5.5), obs_y, Inches(2.5), Inches(0.6),
             "Foundry Tracing", "ai.azure.com → Tracing", AZURE_DARK)
add_flow_box(slide, Inches(8.3), obs_y, Inches(2.5), Inches(0.6),
             "GCP Cloud Trace", "console.cloud.google.com", GCP_DARK_GRN)
add_flow_box(slide, Inches(11.1), obs_y, Inches(1.8), Inches(0.6),
             "BigQuery Logs", "Job History", GCP_DARK_GRN)


# ── Legend ──
add_textbox(slide, Inches(0.3), Inches(6.7), Inches(5), Inches(0.35),
            "■ Azure (blue)    ■ GCP (green)    → Forward    ← Return", 10, TEXT_DIM)

# ── Speaker notes ──
notes = slide.notes_slide
notes.notes_text_frame.text = (
    "TALK TRACK:\n"
    "\"Let me walk you through what happens when I type a question in VS Code.\n"
    "Step 1: I ask 'Find me a cardiology appointment' — this goes to Azure Foundry.\n"
    "Step 2: Foundry's GPT-4o-mini reads the question and reasons about what to do.\n"
    "Step 3: It decides to call the GCP scheduling agent — that's a cross-cloud tool call.\n"
    "Step 4: GCP Cloud Run receives the /invoke request.\n"
    "Step 5: Cloud Run queries BigQuery for available cardiology slots.\n"
    "Step 6: BigQuery returns 2 results — APT-004 and APT-010.\n"
    "Step 7: Data flows back to Foundry, which formats a friendly answer.\n"
    "Step 8: I see the response in VS Code.\n\n"
    "Every step is traced — in Foundry Portal AND GCP Cloud Trace. Same request, visible on both clouds.\""
)

# ═══════════════════════════════════════════════════════════════
# MOVE THE NEW SLIDE from position last → position 3 (between slide 2 and 3)
# ═══════════════════════════════════════════════════════════════
# python-pptx doesn't have a built-in slide move, so we manipulate the XML
slide_list = prs.slides._sldIdLst
slide_ids = list(slide_list)
# The new slide is the last one
new_slide_elem = slide_ids[-1]
# Remove from end
slide_list.remove(new_slide_elem)
# Insert at index 2 (0-based), which is after slide 2
slide_list.insert(2, new_slide_elem)

prs.save(OUTPUT)
print(f"Saved → {OUTPUT}")
print("New slide 3: 'Cross-Cloud Request Flow' (8-step numbered diagram)")
print("Slides: 1-Title, 2-Architecture, 3-FLOW DIAGRAM (NEW), 4-Part A Header, ...")
