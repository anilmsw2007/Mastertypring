"""
High Court Lucknow Court Document (.docx) Generator
Generates ready-to-print Microsoft Word files formatted in Kruti Dev 010, Kruti Dev 011, Times New Roman, or Mangal.
Complies strictly with Lucknow High Court / UP Revenue Court filing norms, with fully customizable formatting.
"""
import os
import re
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from krutidev_converter import unicode_to_krutidev, normalize_court_text

def set_font_properties(run, font_name="Kruti Dev 010", size_pt=14, bold=False, italic=False, underline=False, color_rgb=None):
    """
    Applies font name, size, styling and explicit XML bindings for Word.
    Supports red font color for doubtful/uncertain text.
    """
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    run.font.underline = underline
    if color_rgb is not None:
        run.font.color.rgb = color_rgb
    
    # Crucial for non-Unicode legacy fonts like Kruti Dev:
    # Word requires ascii, hAnsi, and cs to be set in w:rFonts
    rPr = run._r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    rPr.append(rFonts)

DOUBT_TAG_PATTERN = re.compile(
    r'(<doubt>.*?</doubt>|<red>.*?</red>|\[\[.*?\]\]|\(अस्पष्ट[:\-]?\s*.*?\)|(?:\(संदिग्ध[:\-]?\s*.*?\))|\(\?\)|\(अस्पष्ट\)|\(संदिग्ध\))',
    re.IGNORECASE
)

def split_doubt_segments(line: str) -> list:
    """
    Splits text into tuples of (clean_text, is_doubt_red).
    Extracts text inside <doubt>...</doubt>, <red>...</red>, [[...]], (अस्पष्ट: ...), etc.
    """
    segments = []
    last_idx = 0
    for m in DOUBT_TAG_PATTERN.finditer(line):
        start, end = m.span()
        if start > last_idx:
            segments.append((line[last_idx:start], False))
        raw_tag = m.group(0)
        clean = re.sub(
            r'^<doubt>|</doubt>$|^<red>|</red>$|^\[\[|\]\]$|^\(अस्पष्ट[:\-]?\s*|^\(संदिग्ध[:\-]?\s*|\)$',
            '',
            raw_tag,
            flags=re.IGNORECASE
        ).strip()
        if not clean:
            clean = raw_tag
        segments.append((clean, True))
        last_idx = end
    if last_idx < len(line):
        segments.append((line[last_idx:], False))
    return segments

def add_smart_runs(paragraph, line: str, font_choice: str = "Kruti Dev 010", size_pt: int = 14, bold: bool = False, italic: bool = False, underline: bool = False, color_rgb=None):
    """
    Intelligently adds runs to a paragraph:
    - Normalizes dates, numbered lists (1-, 2-), and legal abbreviations.
    - Slashes in case numbers, dates, and English terms are styled in Latin.
    - Any sentence or word with low confidence / doubtful match (<doubt>, [[...]]) is rendered in RED!
    - Hindi text is converted and styled with the selected Kruti Dev font.
    """
    if not line:
        return

    is_kruti = "Kruti" in font_choice
    segments = split_doubt_segments(line)

    token_pattern = re.compile(
        r'('
        r'\b\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4}\b|'    # Dates
        r'\b\d+\.\d+\b|'                                 # Decimal numbers (0.2530, 1.50)
        r'[A-Za-z][A-Za-z0-9_\-\.]*|'                  # English words & abbreviations
        r'\b\d+[\.\)\-]\b|'                               # Numbers with punctuation
        r'\/'                                            # Forward slash (rendered in Latin to prevent आधा ध 'ध्')
        r')'
    )

    for seg_text, is_doubt in segments:
        if not seg_text:
            continue
        seg_color = RGBColor(220, 20, 60) if is_doubt else color_rgb

        if not is_kruti:
            run = paragraph.add_run(seg_text)
            set_font_properties(run, font_choice, size_pt=size_pt, bold=bold, italic=italic, underline=underline, color_rgb=seg_color)
            continue

        # For Kruti Dev, normalize court text inside segment
        norm_seg = normalize_court_text(seg_text)

        parts = []
        last_end = 0
        for m in token_pattern.finditer(norm_seg):
            start, end = m.span()
            if start > last_end:
                parts.append(('HINDI', norm_seg[last_end:start]))
            parts.append(('LATIN', norm_seg[start:end]))
            last_end = end
        if last_end < len(norm_seg):
            parts.append(('HINDI', norm_seg[last_end:]))

        for kind, chunk in parts:
            if not chunk:
                continue
            if kind == 'LATIN':
                run = paragraph.add_run(chunk)
                set_font_properties(run, "Times New Roman", size_pt=size_pt, bold=bold, italic=italic, underline=underline, color_rgb=seg_color)
            else:
                kruti_txt = unicode_to_krutidev(chunk)
                run = paragraph.add_run(kruti_txt)
                set_font_properties(run, font_choice, size_pt=size_pt, bold=bold, italic=italic, underline=underline, color_rgb=seg_color)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    """Sets cell padding in twips/dxa"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex="F2F2F2"):
    """Sets background shading color for cell"""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)

def set_table_borders(table, color="555555", sz="6", val="single"):
    """Applies neat XML borders to table cells"""
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), val)
        border.set(qn('w:sz'), sz)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tblBorders.append(border)
    tblPr.append(tblBorders)

def is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith('|') and s.endswith('|') and len(s) > 2

def is_separator_row(line: str) -> bool:
    s = line.strip().replace(' ', '').replace('|', '').replace('-', '').replace(':', '')
    return len(s) == 0

def parse_table_cells(line: str) -> list:
    raw = line.strip()
    if raw.startswith('|'):
        raw = raw[1:]
    if raw.endswith('|'):
        raw = raw[:-1]
    return [c.replace('**', '').replace('*', '').strip() for c in raw.split('|')]

def add_court_table(doc, table_rows: list, font_choice: str = "Kruti Dev 010", base_size: int = 12):
    """
    Creates a professionally bordered Word table for land/revenue details.
    """
    cleaned_rows = []
    for r in table_rows:
        if is_separator_row(r):
            continue
        cells = parse_table_cells(r)
        if any(c for c in cells):
            cleaned_rows.append(cells)
            
    if not cleaned_rows:
        return None

    max_cols = max(len(r) for r in cleaned_rows)
    for r in cleaned_rows:
        while len(r) < max_cols:
            r.append("")

    table = doc.add_table(rows=len(cleaned_rows), cols=max_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="555555", sz="6")

    tbl_font_size = max(10, base_size - 1)

    for r_idx, row_data in enumerate(cleaned_rows):
        is_header = (r_idx == 0)
        row = table.rows[r_idx]
        for c_idx, cell_value in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)

            if is_header:
                set_cell_shading(cell, "EAEAEA")

            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_header or c_idx == 0 or len(cell_value) < 12) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_smart_runs(p, cell_value, font_choice=font_choice, size_pt=tbl_font_size, bold=is_header)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)

    return table

def add_plot_shape_grid(doc, plot_shapes_data: list, font_choice: str = "Kruti Dev 010", base_size: int = 12):
    """
    Renders 100% editable native Microsoft Word shape boxes for each plot.
    Each shape box displays the plot number in the center and exact dimensions
    on North (Top), South (Bottom), East (Right), West (Left).
    """
    if not plot_shapes_data:
        return

    # Section Heading
    p_hdr = doc.add_paragraph()
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_hdr.paragraph_format.space_before = Pt(12)
    p_hdr.paragraph_format.space_after = Pt(6)
    add_smart_runs(p_hdr, "गाटावार डिजिटल आकृतियां एवं माप (Editable Plot Shapes):", font_choice, size_pt=base_size + 1, bold=True, underline=True)

    cols_count = 2
    rows_count = (len(plot_shapes_data) + cols_count - 1) // cols_count
    
    container_tbl = doc.add_table(rows=rows_count, cols=cols_count)
    container_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(container_tbl, color="D0D0D0", sz="4", val="single")

    for idx, pinfo in enumerate(plot_shapes_data):
        r_idx = idx // cols_count
        c_idx = idx % cols_count
        cell = container_tbl.cell(r_idx, c_idx)
        set_cell_margins(cell, top=100, bottom=120, left=100, right=100)

        gata, shape_type, north, south, east, west = pinfo[:6]

        p_title = cell.paragraphs[0]
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_before = Pt(2)
        p_title.paragraph_format.space_after = Pt(3)
        add_smart_runs(p_title, f"गाटा सं० {gata} ({shape_type})", font_choice, size_pt=base_size, bold=True)

        shape_tbl = cell.add_table(rows=3, cols=3)
        shape_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(shape_tbl, color="222222", sz="8", val="single")

        # Row 0: North
        c_top = shape_tbl.cell(0, 0)
        c_top.merge(shape_tbl.cell(0, 1)).merge(shape_tbl.cell(0, 2))
        c_top.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_shading(c_top, "EEF2F5")
        set_cell_margins(c_top, top=60, bottom=60, left=60, right=60)
        p0 = c_top.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_after = Pt(1)
        add_smart_runs(p0, f"उत्तर: {north if north else '—'}", font_choice, size_pt=base_size - 1, bold=True)

        # Row 1, Col 0: West
        c_w = shape_tbl.cell(1, 0)
        c_w.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(c_w, top=80, bottom=80, left=60, right=60)
        p_w = c_w.paragraphs[0]
        p_w.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_w.paragraph_format.space_after = Pt(1)
        add_smart_runs(p_w, f"पश्चिम:\n{west if west else '—'}", font_choice, size_pt=base_size - 1, bold=True)

        # Row 1, Col 1: Center
        c_c = shape_tbl.cell(1, 1)
        c_c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_shading(c_c, "FFF9C4")
        set_cell_margins(c_c, top=100, bottom=100, left=60, right=60)
        p_c = c_c.paragraphs[0]
        p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_c.paragraph_format.space_after = Pt(1)
        add_smart_runs(p_c, f"【 {gata} 】\n({shape_type})", font_choice, size_pt=base_size, bold=True)

        # Row 1, Col 2: East
        c_e = shape_tbl.cell(1, 2)
        c_e.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(c_e, top=80, bottom=80, left=60, right=60)
        p_e = c_e.paragraphs[0]
        p_e.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_e.paragraph_format.space_after = Pt(1)
        add_smart_runs(p_e, f"पूरब:\n{east if east else '—'}", font_choice, size_pt=base_size - 1, bold=True)

        # Row 2: South
        c_bot = shape_tbl.cell(2, 0)
        c_bot.merge(shape_tbl.cell(2, 1)).merge(shape_tbl.cell(2, 2))
        c_bot.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_shading(c_bot, "EEF2F5")
        set_cell_margins(c_bot, top=60, bottom=60, left=60, right=60)
        p2 = c_bot.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_after = Pt(1)
        add_smart_runs(p2, f"दक्षिण: {south if south else '—'}", font_choice, size_pt=base_size - 1, bold=True)

        sp = cell.add_paragraph()
        sp.paragraph_format.space_after = Pt(4)

    p_end = doc.add_paragraph()
    p_end.paragraph_format.space_after = Pt(6)

def add_nazri_naksha_box(doc, title: str, north: str, south: str, east: str, west: str, center_info: str = "", font_choice: str = "Kruti Dev 010", base_size: int = 12):
    """
    Creates a visual 3x3 court site sketch / field boundary diagram box (नजरी नक्शा / स्थल रेखाचित्र)
    """
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(4)
    add_smart_runs(p_title, title or "नजरी नक्शा / स्थल रेखाचित्र (चौहद्दी विवरण)", font_choice=font_choice, size_pt=base_size + 1, bold=True, underline=True)

    table = doc.add_table(rows=3, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="333333", sz="8")

    tbl_font_size = max(10, base_size - 1)

    # Row 0: North across cols 0, 1, 2
    cell_top = table.cell(0, 0)
    cell_top.merge(table.cell(0, 1)).merge(table.cell(0, 2))
    cell_top.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_margins(cell_top, top=140, bottom=140, left=140, right=140)
    set_cell_shading(cell_top, "F4F6F7")
    p0 = cell_top.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_after = Pt(2)
    add_smart_runs(p0, f"उत्तर: {north if north else 'रास्ता / चक'}", font_choice=font_choice, size_pt=tbl_font_size, bold=True)

    # Row 1, Col 0: West
    cell_west = table.cell(1, 0)
    cell_west.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_margins(cell_west, top=140, bottom=140, left=140, right=140)
    set_cell_shading(cell_west, "FAFAFA")
    p_w = cell_west.paragraphs[0]
    p_w.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_w.paragraph_format.space_after = Pt(2)
    add_smart_runs(p_w, f"पश्चिम:\n{west if west else 'अन्य काश्तकार'}", font_choice=font_choice, size_pt=tbl_font_size, bold=True)

    # Row 1, Col 1: Center (Disputed Land / Field details)
    cell_center = table.cell(1, 1)
    cell_center.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_margins(cell_center, top=180, bottom=180, left=140, right=140)
    set_cell_shading(cell_center, "FFF9C4")
    p_c = cell_center.paragraphs[0]
    p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_c.paragraph_format.space_after = Pt(2)
    center_txt = center_info if center_info else "विवादित स्थल / आराजी\n(स्थल रेखाचित्र)"
    add_smart_runs(p_c, f"【 {center_txt} 】", font_choice=font_choice, size_pt=tbl_font_size, bold=True)

    # Row 1, Col 2: East
    cell_east = table.cell(1, 2)
    cell_east.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_margins(cell_east, top=140, bottom=140, left=140, right=140)
    set_cell_shading(cell_east, "FAFAFA")
    p_e = cell_east.paragraphs[0]
    p_e.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_e.paragraph_format.space_after = Pt(2)
    add_smart_runs(p_e, f"पूरब:\n{east if east else 'पक्की सड़क / रास्ता'}", font_choice=font_choice, size_pt=tbl_font_size, bold=True)

    # Row 2: South across cols 0, 1, 2
    cell_bottom = table.cell(2, 0)
    cell_bottom.merge(table.cell(2, 1)).merge(table.cell(2, 2))
    cell_bottom.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_margins(cell_bottom, top=140, bottom=140, left=140, right=140)
    set_cell_shading(cell_bottom, "F4F6F7")
    p2 = cell_bottom.paragraphs[0]
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(2)
    add_smart_runs(p2, f"दक्षिण: {south if south else 'नाला व अन्य खेत'}", font_choice=font_choice, size_pt=tbl_font_size, bold=True)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)
    return table

def parse_directional_info(lines: list):
    """
    Extracts north, south, east, west and center details from directional lines.
    """
    north, south, east, west, center_info = "", "", "", "", ""
    for l in lines:
        s = l.strip()
        s = re.sub(r'^[\-\*\•]\s*', '', s)
        if re.search(r'^(उत्तर|North)\s*[:\-]', s, re.IGNORECASE):
            north = re.sub(r'^(उत्तर|North)\s*[:\-]\s*', '', s, flags=re.IGNORECASE).strip()
        elif re.search(r'^(दक्षिण|South)\s*[:\-]', s, re.IGNORECASE):
            south = re.sub(r'^(दक्षिण|South)\s*[:\-]\s*', '', s, flags=re.IGNORECASE).strip()
        elif re.search(r'^(पूरब|पूर्व|East)\s*[:\-]', s, re.IGNORECASE):
            east = re.sub(r'^(पूरब|पूर्व|East)\s*[:\-]\s*', '', s, flags=re.IGNORECASE).strip()
        elif re.search(r'^(पश्चिम|West)\s*[:\-]', s, re.IGNORECASE):
            west = re.sub(r'^(पश्चिम|West)\s*[:\-]\s*', '', s, flags=re.IGNORECASE).strip()
        elif any(k in s for k in ["विवादित", "आराजी", "गाटा", "खेत", "रकबा"]):
            clean_c = re.sub(r'^(विवादित स्थल|विवादित भूमि|आराजी)\s*[:\-]\s*', '', s)
            center_info = (center_info + "\n" + clean_c).strip()
    return north, south, east, west, center_info

def build_court_docx(
    data,
    output_path: str,
    font_choice: str = "Kruti Dev 010",
    page_size: str = "Legal",
    left_margin: float = 1.75,
    right_margin: float = 1.0,
    top_margin: float = 1.0,
    bottom_margin: float = 1.0,
    line_spacing: float = 1.35,
    body_font_size: int = 14,
    title_font_size: int = 16,
    first_line_indent: float = 0.5,
    sketch_images: list = None
):
    """
    Builds a beautifully styled, 100% customizable Word document.
    data can be a dictionary with structured fields, or a multiline string.
    Supports native Word Tables, 3x3 Nazri Naksha diagram boxes, and embedded field sketch images.
    """
    doc = docx.Document()
    
    # Court Standard Page Setup
    for sec in doc.sections:
        sec.top_margin = Inches(top_margin)
        sec.bottom_margin = Inches(bottom_margin)
        sec.left_margin = Inches(left_margin)
        sec.right_margin = Inches(right_margin)
        
        # Paper Size: Legal vs A4 vs Letter
        if "legal" in page_size.lower():
            sec.page_width = Inches(8.5)
            sec.page_height = Inches(14.0)
        elif "letter" in page_size.lower():
            sec.page_width = Inches(8.5)
            sec.page_height = Inches(11.0)
        else: # Default A4
            sec.page_width = Inches(8.27)
            sec.page_height = Inches(11.69)

    if isinstance(data, dict):
        # 1. Court Title / Header (Centered, Bold)
        if data.get("court_header"):
            lines = data["court_header"].split("\n")
            for cl in lines:
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = line_spacing
                if "सेवा में" in cl or "lsok esa" in cl:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.space_after = Pt(2)
                    add_smart_runs(p, cl, font_choice, size_pt=body_font_size, bold=True)
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_after = Pt(4)
                    add_smart_runs(p, cl, font_choice, size_pt=title_font_size, bold=True)
                    
        # 2. Case Number / Jurisdiction (Centered, Bold)
        if data.get("case_no"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = line_spacing
            add_smart_runs(p, data["case_no"], font_choice, size_pt=body_font_size, bold=True)

        # 3. Parties (Centered / Justified, Bold)
        if data.get("parties"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.line_spacing = line_spacing
            add_smart_runs(p, data["parties"], font_choice, size_pt=body_font_size, bold=True)

        # 4. Subject (Left aligned / Justified, Bold)
        if data.get("subject"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.line_spacing = line_spacing
            add_smart_runs(p, data["subject"], font_choice, size_pt=body_font_size, bold=True)

        # 5. Salutation (Left aligned, Bold)
        if data.get("salutation"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = line_spacing
            add_smart_runs(p, data["salutation"], font_choice, size_pt=body_font_size, bold=True)

        # 6. Body Paragraphs (Justified, Customizable spacing and first line indent)
        body_list = data.get("body_paragraphs", [])
        if isinstance(body_list, str):
            body_list = [p.strip() for p in body_list.split("\n\n") if p.strip()]
            
        for bp in body_list:
            if not bp.strip():
                continue
            if is_table_row(bp.strip()):
                t_rows = [l.strip() for l in bp.split("\n") if is_table_row(l)]
                add_court_table(doc, t_rows, font_choice=font_choice, base_size=body_font_size)
                continue
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = line_spacing
            p.paragraph_format.first_line_indent = Inches(first_line_indent)
            add_smart_runs(p, bp.strip(), font_choice, size_pt=body_font_size, bold=False)

        # 7. Prayer / Relief (Justified)
        if data.get("prayer"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(14)
            p.paragraph_format.line_spacing = line_spacing
            p.paragraph_format.first_line_indent = Inches(first_line_indent)
            add_smart_runs(p, data["prayer"], font_choice, size_pt=body_font_size, bold=False)

        # 8. Applicant / Signature (Right aligned, Bold)
        if data.get("applicant"):
            lines = data["applicant"].split("\n")
            for al in lines:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = line_spacing
                add_smart_runs(p, al.strip(), font_choice, size_pt=body_font_size, bold=True)

    else:
        def clean_md_line(s):
            # Preserve table rows
            if is_table_row(s):
                return s.replace('**', '').replace('*', '').strip()
            s = re.sub(r'^#+\s*', '', s.strip())
            s = s.replace('**', '').replace('*', '')
            if re.match(r'^[\-\=\_]{3,}$', s):
                return ""
            return s.strip()

        def is_new_para_starter(line):
            l = line.strip()
            if re.match(r'^(\d+[\.\-\)]|\(\d+\)|\[\d+\]|[क-ह][\.\-\)]|\([क-ह]\)|पहला|दूसरा|तीसरा|चौथा)', l):
                return True
            if re.match(r'^(यह\s*कि|कि\s*यह\s*कि|कि\s*प्रार्थी)', l):
                return True
            return False

        def is_court_standalone(line):
            l = line.strip()
            if not l:
                return False
            if is_table_row(l):
                return True
            if re.match(r'^[\-\*\•]?\s*(उत्तर|दक्षिण|पूरब|पूर्व|पश्चिम|North|South|East|West)\s*[:\-]', l):
                return True
            if is_new_para_starter(l):
                return False
            if any(k in l for k in ['न्यायालय', 'Court', 'उच्च न्यायालय', 'IN THE HIGH COURT', 'वाद सं', 'मुकदमा सं', 'Case No', 'बनाम', 'VERSUS']):
                return True
            if any(l.startswith(k) for k in ['सेवा में', 'विषय:', 'श्रीमान', 'महोदय', 'प्रार्थना:', 'Prayer:']):
                return True
            if re.match(r'^(हस्ताक्षर|प्रार्थी|आवेदक|अधिवक्ता|Counsel|Advocate|दिनांक|Date)\s*[:\-]', l):
                return True
            if l in ['हस्ताक्षर', 'प्रार्थी', 'आवेदक', 'हस्ताक्षर प्रार्थी', 'अधिवक्ता', 'हस्ताक्षर अधिवक्ता']:
                return True
            return False

        # Intelligently assemble lines into true court paragraphs
        cleaned_source_lines = [clean_md_line(l) for l in str(data).split("\n")]
        raw_lines = []
        curr_para_lines = []

        for l in cleaned_source_lines:
            if not l:
                if curr_para_lines:
                    raw_lines.append(" ".join(curr_para_lines))
                    curr_para_lines = []
                continue
            if is_court_standalone(l):
                if curr_para_lines:
                    raw_lines.append(" ".join(curr_para_lines))
                    curr_para_lines = []
                raw_lines.append(l)
            elif is_new_para_starter(l):
                if curr_para_lines:
                    raw_lines.append(" ".join(curr_para_lines))
                    curr_para_lines = []
                curr_para_lines.append(l)
            else:
                curr_para_lines.append(l)

        if curr_para_lines:
            raw_lines.append(" ".join(curr_para_lines))

        remaining_sketches = list(sketch_images) if sketch_images else []

        def embed_sketch_picture(simg):
            try:
                if isinstance(simg, str) and os.path.exists(simg):
                    img_path = simg
                elif hasattr(simg, 'save'):
                    import tempfile
                    t_f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    simg.save(t_f.name)
                    t_f.close()
                    img_path = t_f.name
                else:
                    return
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(6)
                p_img.paragraph_format.space_after = Pt(8)
                p_img.paragraph_format.first_line_indent = Inches(0)
                p_img.add_run().add_picture(img_path, width=Inches(5.5))
            except Exception:
                pass

        i = 0
        n = len(raw_lines)
        while i < n:
            line = raw_lines[i]

            # 1. Table Block Detection
            if is_table_row(line):
                tbl_lines = []
                while i < n and is_table_row(raw_lines[i]):
                    tbl_lines.append(raw_lines[i])
                    i += 1
                add_court_table(doc, tbl_lines, font_choice=font_choice, base_size=body_font_size)
                continue

            # 2. Nazri Naksha / Directional Boundary Block Detection
            has_dir_start = bool(re.match(r'^[\-\*\•]?\s*(उत्तर|दक्षिण|पूरब|पूर्व|पश्चिम|North|South|East|West)\s*[:\-]', line))

            if has_dir_start:
                naksha_lines = [line]
                peek_i = i + 1
                found_dirs = 1
                while peek_i < n and peek_i <= i + 8:
                    peek_l = raw_lines[peek_i]
                    if is_table_row(peek_l):
                        break
                    is_dir = bool(re.match(r'^[\-\*\•]?\s*(उत्तर|दक्षिण|पूरब|पूर्व|पश्चिम|North|South|East|West|विवादित|आराजी|खेत|रकबा)\s*[:\-]', peek_l))
                    if is_dir:
                        found_dirs += 1
                        naksha_lines.append(peek_l)
                        peek_i += 1
                    else:
                        break

                if found_dirs >= 3:
                    title = "चौहद्दी विवरण (Boundaries)"
                    north, south, east, west, center_info = parse_directional_info(naksha_lines)
                    add_nazri_naksha_box(
                        doc, title=title, north=north, south=south, east=east, west=west,
                        center_info=center_info, font_choice=font_choice, base_size=body_font_size
                    )
                    i = peek_i
                    continue

            # 3. Regular Paragraph Formatting
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = line_spacing
            
            lower_line = line.lower()
            if i == 0 and any(k in line for k in ["न्यायालय", "Court", "चैबन्दी", "चकबन्दी", "उच्च", "IN THE HIGH COURT", "IN THE COURT"]):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_smart_runs(p, line, font_choice, size_pt=title_font_size, bold=True)
            elif any(k in line for k in ["वाद सं", "मुकदमा सं", "बनाम", "VERSUS", "PETITIONER", "APPLICANT", "WRIT", "CRIMINAL MISC", "CIVIL MISC", "APPLICATION NO"]):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_smart_runs(p, line, font_choice, size_pt=body_font_size, bold=True)
            elif line.startswith("सेवा में") or line.startswith("विषय:") or line.startswith("श्रीमान") or line.startswith("महोदय") or lower_line.startswith("subject:") or lower_line.startswith("to,") or "most respectfully showeth" in lower_line:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                add_smart_runs(p, line, font_choice, size_pt=body_font_size, bold=True)
            elif line.startswith("दिनांक:") or line.startswith("Date:"):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                add_smart_runs(p, line, font_choice, size_pt=body_font_size, bold=True)
            elif line.startswith("प्रार्थना:") or lower_line.startswith("prayer:"):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                add_smart_runs(p, line, font_choice, size_pt=body_font_size, bold=True)
            elif (i >= n - 4 and any(k in line for k in ["प्रार्थी", "आवेदक", "अधिवक्ता", "Counsel", "Advocate", "Petitioner", "Applicant"]) and len(line) < 60 and not line.startswith("अतः")) or "counsel for" in lower_line or line.startswith("हस्ताक्षर"):
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                add_smart_runs(p, line, font_choice, size_pt=body_font_size, bold=True)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.first_line_indent = Inches(first_line_indent)
                add_smart_runs(p, line, font_choice, size_pt=body_font_size, bold=False)

            i += 1

        # If any sketch images were explicitly selected to attach, attach at document end
        if remaining_sketches:
            p_att = doc.add_paragraph()
            p_att.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_att.paragraph_format.space_before = Pt(14)
            p_att.paragraph_format.space_after = Pt(4)
            add_smart_runs(p_att, "संलग्नक (Attached Document)", font_choice, size_pt=title_font_size, bold=True, underline=True)
            for sk in remaining_sketches:
                embed_sketch_picture(sk)
            remaining_sketches.clear()

    doc.save(output_path)
    return output_path

def open_document_in_word(file_path: str):
    """
    Directly opens the generated document in Microsoft Word on Windows.
    """
    if os.path.exists(file_path):
        os.startfile(os.path.abspath(file_path))
        return True
    return False
