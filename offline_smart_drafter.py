"""
Offline Smart Legal Drafter & Chronological Case Reconstructor
Specifically designed for High Court Typists:
100% Offline, Zero API Key, Zero Registration required.
Automatically detects page types, re-orders scrambled pages, integrates paper cuttings,
and drafts standard High Court Petitions in Kruti Dev 010/011 and English.
"""
import re
from PIL import Image
from ocr_engine import extract_text_from_image
from legal_corrector import clean_ocr_text, LEGAL_REPLACEMENTS, auto_structure_court_petition

def classify_page(text: str) -> dict:
    """
    Classifies a page into HEADING, FACTS, GROUNDS, PRAYER, or PAPER_CUTTING.
    """
    lower = text.lower()
    
    # Paper cutting / news indicators
    news_keywords = ["दैनिक", "जागरण", "उजाला", "संवाददाता", "ब्यूरो", "समाचार", "हादसा", "घटना", "गिरफ्तार", "अखबार", "न्यूज", "मृतक", "पुलिस ने", "पुलिस द्वारा"]
    news_score = sum(1 for kw in news_keywords if kw in lower)
    
    # Heading indicators
    heading_keywords = ["न्यायालय", "court", "उच्च न्यायालय", "high court", "उपजिलाधिकारी", "बनाम", "versus", "vs", "वाद सं", "मु०अ०सं०", "धारा", "अंतर्गत", "अन्तर्गत"]
    heading_score = sum(1 for kw in heading_keywords if kw in lower)
    
    # Prayer / Footer indicators
    prayer_keywords = ["सादर प्रार्थना", "अतः श्रीमान", "प्रार्थना है कि", "prayer", "प्रार्थी", "petitioner", "अधिवक्ता", "counsel", "दिनांक", "ह०", "हस्ताक्षर", "सत्यापन"]
    prayer_score = sum(1 for kw in prayer_keywords if kw in lower)
    
    # Paragraph numbering detection (1-, 2-, 3- or 1., 2.)
    numbered_paras = re.findall(r'(?:^|\n)\s*(\d+)[\-\.\)]\s*', text)
    para_numbers = [int(p) for p in numbered_paras if int(p) < 50]
    
    cat = "FACTS"
    if news_score >= 2 and heading_score == 0:
        cat = "PAPER_CUTTING"
    elif heading_score >= 2 and len(para_numbers) <= 1:
        cat = "HEADING"
    elif prayer_score >= 2 and len(para_numbers) <= 1:
        cat = "PRAYER"
    elif len(para_numbers) > 0:
        cat = "FACTS"
        
    return {
        "category": cat,
        "news_score": news_score,
        "heading_score": heading_score,
        "prayer_score": prayer_score,
        "para_numbers": para_numbers,
        "text": text
    }

def clean_and_polish_legal_text(raw_text: str) -> str:
    """
    Applies standard High Court corrections to raw text.
    """
    text = raw_text
    for pattern, replacement in LEGAL_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    try:
        from krutidev_converter import normalize_court_text
        text = normalize_court_text(text)
    except Exception:
        pass
    return text

def offline_smart_draft(
    image_list: list,
    case_type: str = "ऑटो-पहचान (Auto-Detect)",
    advocate_notes: str = "",
    target_lang: str = "Hindi",
    progress_callback=None
) -> dict:
    """
    100% Offline Smart Case Drafter:
    Processes all pages, extracts text, re-orders them logically,
    integrates paper cuttings, and returns a polished High Court draft.
    """
    total = len(image_list)
    page_data = []

    # 1. OCR Extraction per page
    for idx, img in enumerate(image_list):
        if progress_callback:
            progress_callback(idx / total, f"पेज {idx+1} का विश्लेषण किया जा रहा है...")
        raw_txt, cleaned_txt, _ = extract_text_from_image(img, rotation=0, apply_enhancement=True)
        analysis = classify_page(cleaned_txt)
        analysis["page_index"] = idx + 1
        page_data.append(analysis)

    if progress_callback:
        progress_callback(1.0, "पेजों का क्रमबद्ध संयोजन किया जा रहा है...")

    # 2. Segregate by Category
    headings = [p for p in page_data if p["category"] == "HEADING"]
    facts = [p for p in page_data if p["category"] == "FACTS"]
    cuttings = [p for p in page_data if p["category"] == "PAPER_CUTTING"]
    prayers = [p for p in page_data if p["category"] == "PRAYER"]

    # Fallback if no heading found: use first page as heading
    if not headings and page_data:
        headings = [page_data[0]]
        facts = [p for p in page_data[1:] if p["category"] != "PAPER_CUTTING" and p["category"] != "PRAYER"]

    # Fallback if no prayer found: check last page
    if not prayers and len(page_data) > 1:
        if page_data[-1] not in headings and page_data[-1] not in cuttings:
            prayers = [page_data[-1]]
            facts = [p for p in facts if p["page_index"] != page_data[-1]["page_index"]]

    # Sort facts by detected paragraph numbers if available
    def get_first_para(p):
        return p["para_numbers"][0] if p["para_numbers"] else 999
    facts.sort(key=get_first_para)

    # 3. Build Detected Sequence Explanation
    order_summary_parts = []
    if headings:
        order_summary_parts.append(f"न्यायालय व शीर्षक: फोटो {[p['page_index'] for p in headings]}")
    if facts:
        order_summary_parts.append(f"घटनाक्रम व तथ्य: फोटो {[p['page_index'] for p in facts]}")
    if cuttings:
        order_summary_parts.append(f"अख़बार/पेपर कटिंग: फोटो {[p['page_index'] for p in cuttings]}")
    if prayers:
        order_summary_parts.append(f"अंतिम प्रेयर व हस्ताक्षर: फोटो {[p['page_index'] for p in prayers]}")

    detected_order_str = " -> ".join(order_summary_parts) if order_summary_parts else f"कुल {total} पेजों का क्रमबद्ध संयोजन पूर्ण।"

    # 4. Construct Structured High Court Petition
    draft_sections = []

    # A. Heading / Cause Title
    heading_text = "\n".join([p["text"] for p in headings]).strip()
    if not heading_text or len(heading_text) < 15:
        if "English" in target_lang:
            heading_text = "IN THE HIGH COURT OF JUDICATURE AT ALLAHABAD\nBENCH AT LUCKNOW\n\nWRIT - C / BAIL APPLICATION No. ............. of 2026\n\n.................................. Petitioner / Applicant\nVERSUS\nState of U.P. and Others .......... Opposite Parties"
        else:
            court_title = "माननीय उच्च न्यायालय इलाहाबाद, लखनऊ खण्डपीठ, लखनऊ" if "उच्च न्यायालय" in case_type or "रिट" in case_type else "न्यायालय श्रीमान सक्षम प्राधिकारी महोदय"
            heading_text = f"{court_title}\n\nमु०अ०सं० / वाद सं० ................. सन् 2026\n\n........................................ प्रार्थी / याची\n               बनाम               \nउत्तर प्रदेश राज्य व अन्य ................ विपक्षी"

    draft_sections.append(clean_and_polish_legal_text(heading_text))

    # B. Subject / Matter
    if case_type and "ऑटो" not in case_type:
        draft_sections.append(f"\nप्रार्थना पत्र बाबत: {case_type}")

    # C. Advocate Verbal Instructions (if any)
    if advocate_notes:
        draft_sections.append(f"\n[निर्देशानुसार मुख्य आधार: {advocate_notes}]")

    # D. Chronological Facts
    facts_header = "\nश्रीमान जी,\n     प्रार्थी निम्नलिखित सादर निवेदन करता है:-\n" if "Hindi" in target_lang else "\nMost Respectfully Showeth:-\n"
    draft_sections.append(facts_header)

    fact_body_texts = []
    for f in facts:
        cleaned_f = clean_and_polish_legal_text(f["text"])
        fact_body_texts.append(cleaned_f)

    if fact_body_texts:
        draft_sections.append("\n\n".join(fact_body_texts))
    else:
        draft_sections.append("1. यह कि प्रार्थी निर्दोष है तथा उसे उक्त मामले में रंजिशन फंसाया गया है।\n2. यह कि प्रकरण के समस्त तथ्य पत्रावली पर संलग्न हैं।")

    # E. Integration of Paper Cutting / News Clipping
    if cuttings:
        cutting_texts = []
        for c in cuttings:
            cleaned_c = clean_and_polish_legal_text(c["text"])
            cutting_texts.append(cleaned_c)
        
        cutting_section = (
            "\n\n[संलग्न समाचार पत्र / घटना प्रकाशन का विवरण]:\n"
            "यह कि उक्त घटना के संबंध में प्रकाशित समाचार के मुख्य तथ्य निम्नवत् हैं:-\n" +
            "\n".join(cutting_texts)
        )
        draft_sections.append(cutting_section)

    # F. Prayer & Signatures
    prayer_text = "\n".join([p["text"] for p in prayers]).strip()
    if not prayer_text or len(prayer_text) < 15:
        if "English" in target_lang:
            prayer_text = "\nPRAYER:\nWherefore, it is most respectfully prayed that this Hon'ble Court may graciously be pleased to allow this application in the interest of justice.\n\nDate: ..............\nPlace: Lucknow\n\nCounsel for the Petitioner"
        else:
            prayer_text = "\nअतः श्रीमान जी से सादर प्रार्थना है कि प्रार्थी के उपरोक्त प्रार्थना पत्र पर सहानुभूतिपूर्वक विचार करते हुए न्यायहित में उचित आदेश पारित करने की कृपा की जाय।\n\nदिनांक: ..............\nस्थान: लखनऊ\n\nप्रार्थी\nह० अधिवक्ता"

    draft_sections.append(clean_and_polish_legal_text(prayer_text))

    final_draft = "\n\n".join(draft_sections)

    case_summary = f"कुल {total} पृष्ठों का विश्लेषण पूर्ण। "
    if cuttings:
        case_summary += f"{len(cuttings)} अख़बार की कटिंग पहचानी गई और ड्राफ्ट में शामिल की गई। "
    case_summary += f"तथ्यों को कालक्रमानुसार लखनऊ उच्च न्यायालय के मानक प्रारूप में ढाला गया।"

    return {
        "detected_order_summary": detected_order_str,
        "case_highlights": case_summary,
        "draft_text": final_draft
    }
