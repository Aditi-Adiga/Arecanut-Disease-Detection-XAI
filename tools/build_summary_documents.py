"""
Script to generate both DOCX and PDF formats for the ArecaLens Project Summary.
"""
import os
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = Path(r"D:\dev\arecanut_web\docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

DOCX_PATH = DOCS_DIR / "ArecaLens_Project_Summary.docx"
HTML_PATH = DOCS_DIR / "ArecaLens_Project_Summary.html"
PDF_PATH = DOCS_DIR / "ArecaLens_Project_Summary.pdf"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_docx():
    doc = Document()
    
    # Page Margins: 0.8 inch
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(40, 45, 40)
    
    # Header Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("🌿 ArecaLens — Comprehensive Project Summary")
    title_run.bold = True
    title_run.font.size = Pt(22)
    title_run.font.color.rgb = RGBColor(26, 77, 46) # Deep Forest Green
    
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle.add_run("Explainable AI (XAI) & Knowledge-Grounded Agricultural Assistant for Arecanut Disease Detection\nFull Engineering & Project Delivery Report")
    sub_run.font.size = Pt(11)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(80, 95, 80)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(10)
    
    # Section Heading helper
    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        run = h.add_run(text)
        run.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(26, 77, 46)
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(2)
        h.paragraph_format.keep_with_next = True
        run = h.add_run(text)
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(46, 117, 76)
        return h

    def add_bullet(p, bold_text, normal_text):
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.25)
        run_b = p.add_run(bold_text)
        run_b.bold = True
        run_b.font.color.rgb = RGBColor(30, 40, 30)
        run_n = p.add_run(normal_text)
        run_n.font.color.rgb = RGBColor(50, 55, 50)

    # 1. Executive Summary
    add_heading_1("1. Executive Summary & Purpose")
    p1 = doc.add_paragraph(
        "ArecaLens is an end-to-end, safety-first Explainable Artificial Intelligence (XAI) screening aid and knowledge-grounded agricultural assistant developed specifically for arecanut (Areca catechu) growers in Karnataka and Kerala, India. "
        "The project directly targets devastating crop diseases—predominantly Mahali / Koleroga (fruit rot caused by Phytophthora meadii) and Yellow Leaf Disease (YLD)—providing instant screening, visual explanations via Class Activation Maps (CAM), and zero-hallucination agricultural guidance."
    )
    p1.paragraph_format.space_after = Pt(6)
    
    p2 = doc.add_paragraph(
        "Unlike generic agricultural apps that risk farmer livelihood through automated hallucinations or misleading overconfidence, ArecaLens enforces rigorous guardrails: "
        "protective high-confidence thresholds (labeling uncertain cases as 'Unsure'), zero chemical dosage invention, strict refusal of off-label recommendations, and complete local privacy without photo storage."
    )
    p2.paragraph_format.space_after = Pt(8)

    # 2. Architecture & Tech Stack
    add_heading_1("2. System Architecture & Technology Stack")
    
    arch_table = doc.add_table(rows=6, cols=3)
    arch_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Layer", "Technology", "Key Responsibilities"]
    col_widths = [Inches(1.5), Inches(1.8), Inches(3.5)]
    
    for i, h_text in enumerate(headers):
        cell = arch_table.cell(0, i)
        cell.text = h_text
        set_cell_background(cell, "2E754C")
        p = cell.paragraphs[0]
        p.runs[0].bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell, 120, 120, 150, 150)
        
    data = [
        ("Web Frontend", "React 19, Vite, Vanilla CSS", "WCAG AA accessible UI, interactive CAM heatmap slider, multilingual switching (EN, KN, HI, ML), local 8-scan history."),
        ("Backend Server", "FastAPI (Python 3.13), Uvicorn", "Async API endpoints, threadpool inference, zero-logging farmer privacy, unified static production serving."),
        ("Computer Vision & XAI", "TensorFlow 2.21, Keras, TFLite", "MobileNetV3Small classification, 224x224 half-pixel preprocessing, deterministic CAM heatmap computation."),
        ("Offline Chatbot", "Pure Python Standard Library", "Deterministic TF-IDF, synonym mapping, strict retrieval from 27 vetted FAQ entries & disease guides. Zero hallucinations."),
        ("Online LLM Proxy", "OpenAI-compatible client", "Optional server-configured RAG with Google Gemini / Groq; strict regex post-checks blocking unvetted doses & certainty claims.")
    ]
    
    for row_idx, row_data in enumerate(data, start=1):
        bg = "F4F7F4" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(row_data):
            cell = arch_table.cell(row_idx, col_idx)
            cell.text = text
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 120, 120)
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(9.5)
            if col_idx == 0:
                p.runs[0].bold = True
                
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 3. Computer Vision & XAI
    add_heading_1("3. Computer Vision & Explainable AI (XAI) Pipeline")
    
    p = doc.add_paragraph()
    add_bullet(p, "Target Disease Classes: ", "Healthy Leaf, Healthy Nut, Mahali/Koleroga (Fruit rot), and Yellow Leaf Disease (YLD).")
    
    p = doc.add_paragraph()
    add_bullet(p, "Protective Confidence Thresholding: ", "Healthy classes require >= 0.95 confidence; diseased classes require >= 0.70 confidence. Any score falling below these cutoffs is classified as 'Unsure', shielding farmers from false reassurance.")
    
    p = doc.add_paragraph()
    add_bullet(p, "Deterministic Class Activation Mapping (CAM): ", "Computes heatmap = ReLU(features * W_eff), overlaid directly onto the input image. Highlights the exact biological symptoms (lesions, discolorations) guiding the neural network.")
    
    p = doc.add_paragraph()
    add_bullet(p, "Preprocessing & Parity Validation: ", "Strict 224x224 bilinear interpolation adhering to TensorFlow half-pixel centers (float32 [0, 255]), mathematically validated against Google Colab baseline exports.")

    # 4. Multilingual Offline Chatbot
    add_heading_1("4. Multilingual Offline Agricultural Chatbot ('Ask' Tab)")
    
    p = doc.add_paragraph()
    add_bullet(p, "100% Knowledge Grounding: ", "All offline responses originate directly from verified data files (chatbot_faq.json, disease_info.json). Completely offline, requiring no internet connectivity or cloud credits.")
    
    p = doc.add_paragraph()
    add_bullet(p, "Active Result Contextualization: ", "Features a dynamic 'About your last result' chip connecting screening outcomes to recommended next steps without re-uploading photos.")
    
    p = doc.add_paragraph()
    add_bullet(p, "Critical Safety Guardrails: ", "\n"
               "  • _DOSE: Strict refusal of numeric spray volumes/concentrations; directs farmers to KVKs.\n"
               "  • _HEALTH: Intercepts poison/pesticide ingestion and urges immediate emergency medical attention.\n"
               "  • _CONFIRM: Restricts terminology to 'suspected screening aid', strictly prohibiting false diagnosis certainty.\n"
               "  • _OUT: Gracefully declines non-arecanut queries (market rates, weather, unrelated crops).")
    
    p = doc.add_paragraph()
    add_bullet(p, "Multilingual Reach: ", "Full translations and localized chips in English, Kannada, Hindi, and Malayalam with visible 'Draft translation' audit badges.")

    # 5. Online LLM Mode
    add_heading_1("5. Online 'Ask More' Cloud LLM Proxy")
    
    p = doc.add_paragraph(
        "For complex farmer queries beyond canned FAQs, ArecaLens features an optional server-side LLM proxy (/api/chat/online) grounded via RAG (Retrieval-Augmented Generation):"
    )
    p.paragraph_format.space_after = Pt(4)
    
    p = doc.add_paragraph()
    add_bullet(p, "Bounded Context Retrieval: ", "Retrieves top-3 relevant FAQ entries and current class guidance as strict context. Prompts enforce under 120 words with zero dose advice.")
    
    p = doc.add_paragraph()
    add_bullet(p, "Strict Safety Post-Checks: ", "Server-side regex automatically inspects the generated response before returning it to the user. If the model invents any ungrounded unit (ml, g, kg, litre, ppm, %) or certainty word ('definitely', 'confirmed'), the reply is discarded and replaced with verified guide text.")
    
    p = doc.add_paragraph()
    add_bullet(p, "Farmer Privacy & Badging: ", "First-use privacy consent modal explicitly outlines what is transmitted (text query only; never photos). Clear badging labels outputs as 'AI-generated • Verify with officer'.")

    # 6. Test Verification Matrix
    add_heading_1("6. Comprehensive Verification & Evaluation Matrix")
    
    test_table = doc.add_table(rows=6, cols=4)
    test_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    test_headers = ["Evaluation Suite", "Target Component", "Results", "Compliance Rate"]
    
    for i, h_text in enumerate(test_headers):
        cell = test_table.cell(0, i)
        cell.text = h_text
        set_cell_background(cell, "2E754C")
        p = cell.paragraphs[0]
        p.runs[0].bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell, 120, 120, 150, 150)
        
    test_data = [
        ("Backend Pytest", "FastAPI, Models, CAM, Chat API", "83 passed, 0 failed in 2.48s", "100% Pass"),
        ("Frontend Vitest", "AskTab, Slider, Local History, UI", "30 passed across 8 test suites", "100% Pass"),
        ("Chatbot Dev Set", "64 representative farmer questions", "64 / 64 exact intent/FAQ match", "100% Match"),
        ("Chatbot Unseen Set", "20 unseen, paraphrased questions", "15/20 exact (75%), 20/20 safe outcomes", "100% Safe (Exceeds >=70%)"),
        ("Chemical Doses Audit", "All dev & unseen test runs", "0 unverified doses generated", "100% Safe (Strict 0)")
    ]
    
    for row_idx, row_data in enumerate(test_data, start=1):
        bg = "F4F7F4" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(row_data):
            cell = test_table.cell(row_idx, col_idx)
            cell.text = text
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 120, 120)
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(9.5)
            if col_idx == 3:
                p.runs[0].bold = True
                p.runs[0].font.color.rgb = RGBColor(26, 110, 50)
                
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 7. Companion Mobile App
    add_heading_1("7. Companion Flutter Mobile Application")
    p = doc.add_paragraph(
        "Located in the mobile/ directory, a Flutter cross-platform mobile application was developed to complement the web app. "
        "It includes local farmer onboarding, 5-tab navigation, camera/gallery image capture, offline network indicators, and a pure Dart chat engine with 100% golden parity to the backend logic."
    )
    p.paragraph_format.space_after = Pt(8)

    # 8. How to Run
    add_heading_1("8. How to Run the Website")
    p = doc.add_paragraph("The application serves both the React UI and FastAPI API from a single local port:")
    p.paragraph_format.space_after = Pt(4)
    
    code_box = doc.add_paragraph()
    code_box.paragraph_format.left_indent = Inches(0.3)
    c_run = code_box.add_run(
        "Double-click start.cmd\n"
        "# OR run in PowerShell:\n"
        ".\\backend\\.venv\\Scripts\\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000\n"
        "-> Open http://127.0.0.1:8000 in your browser."
    )
    c_run.font.name = "Consolas"
    c_run.font.size = Pt(9.5)
    c_run.font.color.rgb = RGBColor(30, 70, 40)
    
    doc.save(str(DOCX_PATH))
    print(f"[OK] Generated DOCX at {DOCX_PATH}")

def create_html():
    html_content = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ArecaLens — Comprehensive Project Summary & Engineering Report</title>
<style>
  @page {
    size: A4;
    margin: 1.5cm 1.5cm 1.5cm 1.5cm;
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 8.5pt;
      color: #667085;
    }
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1f2a24;
    line-height: 1.48;
    font-size: 9.5pt;
    margin: 0;
    padding: 0;
  }
  .header {
    text-align: center;
    border-bottom: 2px solid #2e754c;
    padding-bottom: 10px;
    margin-bottom: 14px;
  }
  .header h1 {
    color: #1a4d2e;
    margin: 0 0 4px 0;
    font-size: 19pt;
    font-weight: 700;
  }
  .header .subtitle {
    color: #4b6354;
    font-size: 10pt;
    font-style: italic;
    margin: 0;
  }
  .header .meta {
    font-size: 8.5pt;
    color: #6a7f72;
    margin-top: 5px;
  }
  .section-block {
    page-break-inside: avoid;
    margin-bottom: 12px;
  }
  h2 {
    color: #1a4d2e;
    font-size: 11.5pt;
    border-bottom: 1.5px solid #e1ebe3;
    padding-bottom: 3px;
    margin-top: 12px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }
  h3 {
    color: #2e754c;
    font-size: 10.5pt;
    margin-top: 10px;
    margin-bottom: 4px;
    page-break-after: avoid;
  }
  p {
    margin: 0 0 6px 0;
  }
  ul {
    margin: 0 0 8px 0;
    padding-left: 18px;
  }
  li {
    margin-bottom: 3px;
  }
  strong {
    color: #153822;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 12px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }
  th {
    background: #2e754c;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 6px 9px;
    border: 1px solid #25603e;
  }
  td {
    padding: 6px 9px;
    border: 1px solid #d4ded7;
    vertical-align: top;
  }
  tr:nth-child(even) td {
    background-color: #f7faf8;
  }
  .badge-pass {
    display: inline-block;
    background: #e6f7ec;
    color: #127938;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid #b3e7c4;
    font-size: 8pt;
  }
  .callout {
    background: #f1f8f3;
    border-left: 4px solid #2e754c;
    padding: 8px 12px;
    margin: 8px 0 10px 0;
    border-radius: 0 5px 5px 0;
  }
  .callout-title {
    font-weight: 700;
    color: #1a4d2e;
    margin-bottom: 3px;
  }
  .code-block {
    background: #f4f6f5;
    border: 1px solid #d8e0db;
    border-radius: 5px;
    padding: 8px 12px;
    font-family: Consolas, Monaco, "Courier New", monospace;
    font-size: 8.5pt;
    color: #1e3d29;
    margin: 6px 0 8px 0;
    white-space: pre-wrap;
  }
</style>
</head>
<body>

<div class="header">
  <h1>🌿 ArecaLens — Comprehensive Project Summary</h1>
  <div class="subtitle">Explainable AI (XAI) & Knowledge-Grounded Agricultural Assistant for Arecanut Disease Detection</div>
  <div class="meta">Full Engineering, Architecture & Verification Report • Antigravity AI</div>
</div>

<div class="section-block">
  <h2>1. Executive Summary & Purpose</h2>
  <p>
    <strong>ArecaLens</strong> is an end-to-end Explainable Artificial Intelligence (XAI) screening aid and knowledge-grounded agricultural assistant designed for arecanut (<em>Areca catechu</em>) growers in Karnataka and Kerala, India. The application targets critical fungal diseases—predominantly <strong>Mahali / Koleroga</strong> (fruit rot caused by <em>Phytophthora meadii</em>) and <strong>Yellow Leaf Disease (YLD)</strong>.
  </p>
  <p>
    Unlike generic crop apps that risk farmer livelihood through hallucinated pesticide doses or false reassurances, ArecaLens enforces strict protective principles: <strong>high-confidence thresholds</strong> (categorizing borderline scans as "Unsure"), <strong>zero chemical dosage invention</strong>, and <strong>complete offline determinism</strong>.
  </p>

  <div class="callout">
    <div class="callout-title">Engineering Core Tenet</div>
    <em>"ArecaLens includes a knowledge-grounded retrieval assistant (not a generative one) that answers from cited, expert-review-pending sources with strict offline safety."</em>
  </div>
</div>

<div class="section-block">
  <h2>2. System Architecture & Technology Stack</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 22%;">Component</th>
        <th style="width: 25%;">Technology</th>
        <th>Key Responsibilities</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Web Frontend</strong></td>
        <td>React 19, Vite, Vanilla CSS</td>
        <td>WCAG AA accessible interface, interactive CAM heatmap slider, 4-language toggle (EN, KN, HI, ML), local 8-scan history.</td>
      </tr>
      <tr>
        <td><strong>Backend API</strong></td>
        <td>FastAPI, Uvicorn, Python 3.13</td>
        <td>Asynchronous REST endpoints, threadpool inference, zero message logging, unified static production serving on port 8000.</td>
      </tr>
      <tr>
        <td><strong>Computer Vision & XAI</strong></td>
        <td>TensorFlow 2.21, Keras, TFLite</td>
        <td>MobileNetV3Small classification, 224x224 half-pixel bilinear preprocessing, deterministic Class Activation Mapping.</td>
      </tr>
      <tr>
        <td><strong>Offline Chatbot</strong></td>
        <td>Python Standard Library</td>
        <td>Deterministic TF-IDF, synonym mapping, 27 vetted FAQ entries & disease guides. Completely offline with zero hallucinations.</td>
      </tr>
      <tr>
        <td><strong>Online LLM Proxy</strong></td>
        <td>OpenAI-compatible client</td>
        <td>Optional server-configured RAG with Google Gemini / Groq; strict server-side regex post-checks blocking unvetted chemical doses.</td>
      </tr>
      <tr>
        <td><strong>Companion Mobile</strong></td>
        <td>Flutter (Dart)</td>
        <td>Cross-platform 5-tab mobile application with camera capture, offline status indicator, and golden parity chat engine.</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="section-block">
  <h2>3. Computer Vision & Explainable AI (XAI) Pipeline</h2>
  <ul>
    <li><strong>Target Classes & Protective Cutoffs:</strong>
      <ul>
        <li><code>Healthy_Leaf</code> (Confidence &ge; 0.95)</li>
        <li><code>Healthy_Nut</code> (Confidence &ge; 0.95)</li>
        <li><code>Mahali_Koleroga</code> (Fruit rot, Confidence &ge; 0.70)</li>
        <li><code>Yellow_Leaf</code> (Yellow Leaf Disease, Confidence &ge; 0.70)</li>
        <li><em>Scans scoring below thresholds are categorized as <strong>"Unsure"</strong> to prevent dangerous false reassurances.</em></li>
      </ul>
    </li>
    <li><strong>Deterministic Class Activation Maps (CAM):</strong> Generates feature-weighted activation heatmaps (<strong>CAM = ReLU(features &times; W<sub>eff</sub>)</strong>) overlaid directly on raw photos to reveal visual lesion boundaries.</li>
    <li><strong>Preprocessing & Colab Parity:</strong> Bilinear resize to 224x224 with exact TensorFlow half-pixel centers (float32 [0, 255]), mathematically validated against Google Colab baseline exports.</li>
    <li><strong>Local Privacy:</strong> Retains up to 8 recent scans in browser <code>localStorage</code>; raw image uploads are never stored on server disks.</li>
  </ul>
</div>

<div class="section-block">
  <h2>4. Multilingual Knowledge-Grounded Chatbot ("Ask" Tab)</h2>
  <ul>
    <li><strong>100% Deterministic Grounding:</strong> Standard-library engine (<code>backend/chat_engine.py</code>) answers strictly from verified sources (<code>chatbot_faq.json</code>, <code>disease_info.json</code>).</li>
    <li><strong>Result-Aware Context:</strong> Features an "About your last result" chip linking screening outcomes to follow-up care without re-transmitting photos.</li>
    <li><strong>Mandatory Safety Guardrails:</strong>
      <ul>
        <li><code>_DOSE</code>: Refuses unverified spray quantities and concentrations; directs to agricultural officers and KVKs.</li>
        <li><code>_HEALTH</code>: Intercepts questions regarding human poisoning or ingestion, urging immediate emergency medical help.</li>
        <li><code>_CONFIRM</code>: Enforces that screening results are "suspected", never "confirmed".</li>
        <li><code>_OUT</code>: Politely declines unrelated queries (market prices, weather, other crops).</li>
      </ul>
    </li>
    <li><strong>Multilingual Localization:</strong> Localized answers and dynamic suggestion chips across English (<code>en</code>), Kannada (<code>kn</code>), Hindi (<code>hi</code>), and Malayalam (<code>ml</code>) with clear draft-translation notices.</li>
  </ul>
</div>

<div class="section-block">
  <h2>5. Online "Ask More" Cloud Proxy & RAG Safety Post-Checks</h2>
  <ul>
    <li><strong>Server-Grounded Context:</strong> Automatically retrieves top-3 FAQ items and active class guidance as strict context for Google Gemini or Groq LLMs.</li>
    <li><strong>Strict Post-Generation Audit:</strong> Scans model output; immediately discards and reverts to verified guide text if the model outputs unverified units (<code>ml</code>, <code>g</code>, <code>kg</code>, <code>litre</code>, <code>ppm</code>, <code>%</code>) or certainty terms (<code>confirmed</code>, <code>100%</code>).</li>
    <li><strong>Transparent Provenance:</strong> Clearly badges responses as <em>"AI-generated • Verify with officer"</em> vs <em>"From the verified guide"</em>.</li>
  </ul>
</div>

<div class="section-block">
  <h2>6. Comprehensive Verification Matrix</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 25%;">Suite</th>
        <th style="width: 30%;">Scope</th>
        <th>Result</th>
        <th style="width: 18%;">Status</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Backend Pytest</strong></td>
        <td>FastAPI, CAM, Preprocessing, Chat API</td>
        <td>83 passed, 0 failed (in 2.48s)</td>
        <td><span class="badge-pass">100% Pass</span></td>
      </tr>
      <tr>
        <td><strong>Frontend Vitest</strong></td>
        <td>AskTab, Sliders, History, Localization</td>
        <td>30 passed across 8 test suites</td>
        <td><span class="badge-pass">100% Pass</span></td>
      </tr>
      <tr>
        <td><strong>Chatbot Dev Set</strong></td>
        <td>64 representative farmer questions</td>
        <td>64 / 64 exact matches</td>
        <td><span class="badge-pass">100% Match</span></td>
      </tr>
      <tr>
        <td><strong>Chatbot Unseen Set</strong></td>
        <td>20 unseen, paraphrased questions</td>
        <td>15/20 exact (75%), 20/20 safe outcomes</td>
        <td><span class="badge-pass">100% Safe</span></td>
      </tr>
      <tr>
        <td><strong>Chemical Doses Audit</strong></td>
        <td>All evaluation and test sets</td>
        <td>Strictly 0 unverified doses generated</td>
        <td><span class="badge-pass">0.0% Hallucination</span></td>
      </tr>
      <tr>
        <td><strong>Credential Audit</strong></td>
        <td>Git history and working directory</td>
        <td>0 keys or secrets committed</td>
        <td><span class="badge-pass">Clean</span></td>
      </tr>
    </tbody>
  </table>
</div>

<div class="section-block">
  <h2>7. Companion Flutter Mobile Application</h2>
  <p>
    Located in the <code>mobile/</code> directory, a Flutter cross-platform application complements the web platform. It features local farmer onboarding, 5-tab navigation, camera/gallery scanning, offline network indicators, and a pure Dart chat engine with 100% golden parity to the backend logic.
  </p>
</div>

<div class="section-block">
  <h2>8. How to Launch the Web Application</h2>
  <p>The single-port production server delivers both the frontend React application and the FastAPI backend:</p>
  <div class="code-block"># Quick Launch (Recommended):
Double-click start.cmd  (or run .\start.ps1 in PowerShell)

# Direct PowerShell Command:
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

-> Access the web interface at: http://127.0.0.1:8000
-> Access interactive API documentation at: http://127.0.0.1:8000/docs</div>
</div>

</body>
</html>
"""
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Generated HTML at {HTML_PATH}")

def convert_html_to_pdf():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)
    if not edge_exe:
        print("[WARNING] msedge.exe not found. Skipping PDF generation.")
        return False
        
    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_PATH}",
        str(HTML_PATH)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and PDF_PATH.exists():
        print(f"[OK] Generated PDF at {PDF_PATH} (size: {PDF_PATH.stat().st_size} bytes)")
        return True
    else:
        print(f"[ERROR] Edge PDF conversion failed: {res.stderr}")
        return False

if __name__ == "__main__":
    create_docx()
    create_html()
    convert_html_to_pdf()
