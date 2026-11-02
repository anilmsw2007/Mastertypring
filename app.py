"""
⌨️ Typist Studio (टाइपिस्ट स्टूडियो - Hindi & English)
सरल 5-चरणीय कार्यप्रवाह:
1. Input (फोटो/PDF)
2. Select Language (हिन्दी / English)
3. Select Font (Kruti Dev 010 / Mangal / Times New Roman)
4. Select Type (केवल टाइपिंग या अर्जी/ड्राफ्ट तैयार करना)
5. Result Download (Word DOCX - 100% Legal Page, Justified, लाल रंग संदिग्ध हाइलाइट सहित)
"""

import os
import sys
import tempfile
import socket
import json
import streamlit as st
import cv2
import numpy as np
from PIL import Image

# Import typing modules
from krutidev_converter import unicode_to_krutidev, krutidev_to_unicode
from legal_corrector import clean_ocr_text, auto_structure_court_petition
from ocr_engine import extract_text_from_image, preprocess_image
from docx_generator import build_court_docx, open_document_in_word
from court_templates import TEMPLATES

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(data):
    try:
        cur = load_config()
        cur.update(data)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def is_online(host="8.8.8.8", port=53, timeout=1.2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        pass
    try:
        import urllib.request
        urllib.request.urlopen("https://www.google.com", timeout=2)
        return True
    except Exception:
        return False

# Page configuration
st.set_page_config(
    page_title="Typist Studio | Kruti Dev & English DOCX",
    page_icon="⌨️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling for Typist UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 16px 22px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .step-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .step-header {
        font-size: 17px;
        font-weight: 700;
        color: #1e3c72;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .red-alert-box {
        background-color: #fff5f5;
        border-left: 5px solid #e53935;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 14px;
        color: #b71c1c;
        font-size: 14px;
        line-height: 1.5;
    }
    .stTextArea textarea {
        font-size: 16px !important;
        line-height: 1.6 !important;
        font-family: 'Consolas', 'Mangal', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

config = load_config()
online_status = is_online()
secrets_key = ""
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        secrets_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass
gemini_key = st.session_state.get("gemini_key", "") or config.get("gemini_api_key", "") or os.environ.get("GEMINI_API_KEY", "") or secrets_key

# Header
st.markdown(f"""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h2 style="margin: 0; padding: 0; font-size: 24px;">⌨️ टाइपिस्ट स्टूडियो (Typist Studio)</h2>
            <p style="margin: 4px 0 0 0; opacity: 0.92; font-size: 14px;">
                हस्तलिखित व टंकित कागज़ात से <b>Kruti Dev 010</b> एवं <b>Times New Roman</b> Word (.DOCX) | <b>Legal पेज (8.5×14)</b>, <b>1.75" बायां मार्जिन</b>, <b>Justified पैराग्राफ</b>
            </p>
        </div>
        <div style="margin-top: 6px;">
            <span style="background-color: {'#2e7d32' if online_status else '#e65100'}; color: white; padding: 5px 14px; border-radius: 16px; font-size: 13px; font-weight: bold;">
                {'🌐 AI ऑनलाइन सक्रिय' if online_status else '📴 ऑफ़लाइन मोड'}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar (Minimal settings only, not cluttered)
with st.sidebar:
    st.subheader("⚙️ सिस्टम सेटिंग्स")
    with st.expander("🔑 AI API Key सेटिंग्स", expanded=not bool(gemini_key)):
        new_key = st.text_input("Gemini API Key:", value=gemini_key, type="password")
        if new_key and new_key != gemini_key:
            save_config({"gemini_api_key": new_key})
            st.success("API Key सुरक्षित सेव हो गई!")
            st.rerun()
    st.caption("नोट: मुख्य विंडो में दिया गया 5-चरणीय कार्यप्रवाह उपयोग करें।")

if not gemini_key:
    st.warning("⚠️ **Google Gemini AI Key दर्ज नहीं है!**\n\nमोबाइल से AI टाइपिंग शुरू करने के लिए कृपया अपनी Gemini API Key यहाँ डालें:")
    quick_api_key = st.text_input("Gemini API Key:", type="password", key="quick_key_box", placeholder="AIzaSy...")
    if quick_api_key:
        save_config({"gemini_api_key": quick_api_key})
        st.session_state["gemini_key"] = quick_api_key
        st.success("✅ API Key सक्रिय हो गई!")
        st.rerun()

# Session state initialization with versioning to prevent stale data
if "doc_version" not in st.session_state:
    st.session_state["doc_version"] = 0
if "extracted_text" not in st.session_state:
    st.session_state["extracted_text"] = ""
if "order_analysis" not in st.session_state:
    st.session_state["order_analysis"] = ""
if "case_highlights" not in st.session_state:
    st.session_state["case_highlights"] = ""
if "sketch_images" not in st.session_state:
    st.session_state["sketch_images"] = []

# Main Container Layout: 5 Simple Steps
main_col1, main_col2 = st.columns([1, 1], gap="large")

with main_col1:
    # STEP 1: INPUT
    st.markdown('<div class="step-header">📁 स्टेप 1: इनपुट (Input - फोटो या मोबाइल PDF)</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "फोटो या मोबाइल PDF यहाँ अपलोड करें (एक या अधिक पेज):",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        accept_multiple_files=True,
        help="मोबाइल से खींची गई फोटो अथवा स्कैनर (CamScanner, Kaagaz, Adobe Scan) से बनी PDF सीधे लोड करें।"
    )

    # Detect file change - CLEAR ALL STALE RESULTS INSTANTLY on new file upload!
    current_file_sig = tuple(
        (getattr(uf, "name", ""), getattr(uf, "size", 0)) for uf in uploaded_files
    ) if uploaded_files else ()

    if st.session_state.get("_last_uploaded_sig") != current_file_sig:
        st.session_state["_last_uploaded_sig"] = current_file_sig
        st.session_state["extracted_text"] = ""
        st.session_state["doc_version"] = st.session_state.get("doc_version", 0) + 1
        st.session_state["order_analysis"] = ""
        st.session_state["case_highlights"] = ""
        st.session_state["sketch_images"] = []
        # Clear any stored editor text widgets from previous runs
        for k in list(st.session_state.keys()):
            if k.startswith("editor_text_"):
                del st.session_state[k]
        st.rerun()

    image_list = []
    pdf_details = []
    if uploaded_files:
        import fitz
        import io
        for uf in uploaded_files:
            fname = getattr(uf, "name", "").lower()
            uf.seek(0)
            if fname.endswith(".pdf"):
                try:
                    pdf_bytes = uf.read()
                    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    p_count = len(pdf_doc)
                    pdf_details.append(f"{uf.name} ({p_count} पेज)")
                    for pno in range(p_count):
                        page = pdf_doc[pno]
                        pix = page.get_pixmap(dpi=150)
                        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                        image_list.append(img)
                except Exception as e:
                    st.error(f"PDF लोड करने में त्रुटि: {e}")
            else:
                try:
                    img = Image.open(uf).convert("RGB")
                    image_list.append(img)
                except Exception as e:
                    st.error(f"फोटो लोड करने में त्रुटि: {e}")

    if image_list:
        st.success(f"✅ कुल {len(image_list)} पेज सफलतापूर्वक लोड हो गए!")
        # Quick preview
        with st.expander(f"👁️ लोड किए गए पेजों का प्रीव्यू देखें ({len(image_list)} पेज)", expanded=False):
            p_idx = st.selectbox("पेज चुनें:", [f"पेज {i+1}" for i in range(len(image_list))], index=0)
            chosen_p = int(p_idx.replace("पेज ", "")) - 1
            st.image(image_list[chosen_p], caption=f"पेज {chosen_p+1}", use_container_width=True)

    st.divider()

    # STEP 2: SELECT LANGUAGE
    st.markdown('<div class="step-header">🌐 स्टेप 2: भाषा चुनें (Select Language)</div>', unsafe_allow_html=True)
    sel_lang = st.radio(
        "भाषा चुनें:",
        ["हिन्दी (Hindi)", "English"],
        horizontal=True,
        index=0,
        label_visibility="collapsed"
    )

    st.divider()

    # STEP 3: SELECT FONT
    st.markdown('<div class="step-header">🔤 स्टेप 3: फॉन्ट चुनें (Select Font)</div>', unsafe_allow_html=True)
    if "हिन्दी" in sel_lang:
        sel_font = st.radio(
            "फॉन्ट चुनें:",
            ["Kruti Dev 010 (मानक फॉन्ट - डिफ़ॉल्ट)", "Kruti Dev 011", "Mangal (यूनीकोड)"],
            horizontal=True,
            index=0,
            label_visibility="collapsed"
        )
    else:
        sel_font = st.radio(
            "फॉन्ट चुनें:",
            ["Times New Roman (मानक फॉन्ट - डिफ़ॉल्ट)", "Arial"],
            horizontal=True,
            index=0,
            label_visibility="collapsed"
        )

    st.divider()

    # STEP 4: SELECT TYPE (TYPING YA ARZI TAIYAR KARNA)
    st.markdown('<div class="step-header">⚖️ स्टेप 4: कार्य का प्रकार चुनें (Select Type)</div>', unsafe_allow_html=True)
    work_type = st.radio(
        "कार्य का प्रकार चुनें:",
        [
            "📝 केवल टाइपिंग (Exact Typing - जैसा कागज़ पर लिखा है हूबहू 100% वैसा ही टाइप करें)",
            "📄 अर्जी / ड्राफ्ट तैयार करना (Arzi / Draft - तथ्यों के आधार पर व्यवस्थित प्रारूप तैयार करें)"
        ],
        index=0,
        label_visibility="collapsed"
    )

    advocate_note = ""
    case_cat = "ऑटो-पहचान (Auto-Detect)"
    if "अर्जी" in work_type or "ड्राफ्ट" in work_type:
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            case_cat = st.selectbox(
                "दस्तावेज़ / प्रारूप का प्रकार:",
                [
                    "ऑटो-पहचान (Auto-Detect)",
                    "प्रार्थना पत्र (Application)",
                    "शपथ पत्र (Affidavit)",
                    "शिकायत / आख्या (Complaint / Report)",
                    "जमानत प्रार्थना पत्र (Bail Application)",
                    "दीवानी वाद पत्र (Plaint)",
                    "स्थगन प्रार्थना पत्र (Stay Application)"
                ]
            )
        with c_col2:
            advocate_note = st.text_input("विशेष निर्देश (वैकल्पिक):", placeholder="उदा० मुख्य बिंदु या तारीख आदि")

    st.write("")
    start_btn = st.button(
        "🚀 टाइपिंग / ड्राफ्ट शुरू करें (Start Now)",
        type="primary",
        use_container_width=True
    )

    # Process execution
    if start_btn:
        if not image_list:
            st.warning("⚠️ कृपया पहले स्टेप 1 में कोई फोटो या PDF अपलोड करें!")
        else:
            if not gemini_key and (online_status or sys.platform != "win32"):
                st.error("⚠️ AI टाइपिंग के लिए कृपया ऊपर अपनी Google Gemini API Key दर्ज करें!")
                st.stop()

            is_drafting = "अर्जी" in work_type or "ड्राफ्ट" in work_type
            use_ai = bool(gemini_key and online_status)

            if is_drafting:
                if use_ai:
                    with st.spinner("🧠 AI द्वारा तथ्यों का विश्लेषण कर व्यवस्थित ड्राफ्ट तैयार किया जा रहा है..."):
                        try:
                            from gemini_vision import smart_draft_case_with_ai
                            t_lang = "English" if "English" in sel_lang else "Hindi"
                            draft_res = smart_draft_case_with_ai(
                                image_list,
                                case_type=case_cat,
                                advocate_notes=advocate_note,
                                target_language=t_lang,
                                api_key=gemini_key
                            )
                            st.session_state["doc_version"] = st.session_state.get("doc_version", 0) + 1
                            ver = st.session_state["doc_version"]
                            st.session_state["extracted_text"] = draft_res["draft_text"]
                            st.session_state[f"editor_text_{ver}"] = draft_res["draft_text"]
                            st.session_state["order_analysis"] = draft_res.get("detected_order_summary", "")
                            st.session_state["case_highlights"] = draft_res.get("case_highlights", "")
                            st.success("✅ प्रारूप सफलतापूर्वक तैयार हो गया!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"ड्राफ्टिंग त्रुटि: {e}")
                else:
                    with st.spinner("ऑफ़लाइन इंजन द्वारा ड्राफ्ट तैयार किया जा रहा है..."):
                        try:
                            from offline_smart_drafter import offline_smart_draft
                            t_lang = "English" if "English" in sel_lang else "Hindi"
                            draft_res = offline_smart_draft(
                                image_list,
                                case_type=case_cat,
                                advocate_notes=advocate_note,
                                target_lang=t_lang
                            )
                            st.session_state["doc_version"] = st.session_state.get("doc_version", 0) + 1
                            ver = st.session_state["doc_version"]
                            st.session_state["extracted_text"] = draft_res["draft_text"]
                            st.session_state[f"editor_text_{ver}"] = draft_res["draft_text"]
                            st.session_state["order_analysis"] = draft_res.get("detected_order_summary", "")
                            st.session_state["case_highlights"] = draft_res.get("case_highlights", "")
                            st.success("✅ प्रारूप तैयार हो गया!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"ऑफ़लाइन त्रुटि: {e}")
            else:
                # Direct Exact Typing
                if use_ai:
                    with st.spinner(f"⚡ AI द्वारा सभी {len(image_list)} पेजों की शुद्ध लिखावट टाइप की जा रही है..."):
                        try:
                            from gemini_vision import extract_handwriting_with_ai
                            raw_out = extract_handwriting_with_ai(image_list, api_key=gemini_key)
                            st.session_state["doc_version"] = st.session_state.get("doc_version", 0) + 1
                            ver = st.session_state["doc_version"]
                            st.session_state["extracted_text"] = raw_out
                            st.session_state[f"editor_text_{ver}"] = raw_out
                            st.success("✅ सभी पेज 99% शुद्धता के साथ टाइप हो गए!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"टाइपिंग त्रुटि: {e}")
                else:
                    with st.spinner(f"लोकल ऑफ़लाइन OCR से {len(image_list)} पेजों की टाइपिंग की जा रही है..."):
                        try:
                            texts = []
                            for p_im in image_list:
                                _, clean_t, _ = extract_text_from_image(p_im)
                                texts.append(clean_t)
                            merged_text = "\n\n".join(texts)
                            st.session_state["doc_version"] = st.session_state.get("doc_version", 0) + 1
                            ver = st.session_state["doc_version"]
                            st.session_state["extracted_text"] = merged_text
                            st.session_state[f"editor_text_{ver}"] = merged_text
                            st.success("✅ ऑफ़लाइन टाइपिंग पूर्ण!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"OCR त्रुटि: {e}")

with main_col2:
    # STEP 5: RESULT & DOWNLOAD
    st.markdown('<div class="step-header">📥 स्टेप 5: परिणाम व डाउनलोड (Result & Download)</div>', unsafe_allow_html=True)

    # Red Font Security Notice
    st.markdown("""
    <div class="red-alert-box">
        🔴 <b>लाल रंग (RED Text) सुरक्षा सुविधा:</b> यदि कोई शब्द या संख्या कागज़ पर कटी-फटी, धुंधली या 100% स्पष्ट नहीं थी, तो बनने वाली <b>Word (.docx) फाइल में उसका रंग लाल (Red)</b> रहेगा। इससे आप उस शब्द को मूल कागज़ से देखकर तुरंत सही कर सकते हैं और फिर Word में उसका रंग सामान्य (काला) कर सकते हैं।
    </div>
    """, unsafe_allow_html=True)

    ver = st.session_state.get("doc_version", 0)
    current_extracted = st.session_state.get("extracted_text", "")

    edited_text = st.text_area(
        "टाइप किया गया टेक्स्ट (यहाँ सीधे देखकर सुधार भी सकते हैं):",
        value=current_extracted,
        key=f"editor_text_{ver}",
        height=380,
        placeholder="फोटो या PDF लोड करके 'टाइपिंग शुरू करें' बटन दबाएं..."
    )

    if edited_text.strip():
        # Clean font name choice
        if "Kruti Dev 010" in sel_font:
            clean_font = "Kruti Dev 010"
        elif "Kruti Dev 011" in sel_font:
            clean_font = "Kruti Dev 011"
        elif "Times New Roman" in sel_font:
            clean_font = "Times New Roman"
        elif "Arial" in sel_font:
            clean_font = "Arial"
        else:
            clean_font = "Mangal"

        # Generate fresh versioned DOCX in Legal, 1.75" Left Margin, 1.35x Spacing, Justified
        temp_dir = tempfile.gettempdir()
        file_suffix = clean_font.replace(" ", "_")
        out_docx_path = os.path.join(temp_dir, f"Document_{file_suffix}_v{ver}.docx")

        build_court_docx(
            edited_text,
            out_docx_path,
            font_choice=clean_font,
            page_size="Legal",
            left_margin=1.75,
            right_margin=1.0,
            top_margin=1.0,
            bottom_margin=1.0,
            line_spacing=1.35,
            body_font_size=14,
            title_font_size=16,
            first_line_indent=0.5
        )

        with open(out_docx_path, "rb") as f:
            fresh_docx_bytes = f.read()

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label=f"📥 Word (.docx) फाइल डाउनलोड करें",
                data=fresh_docx_bytes,
                file_name=f"Document_{file_suffix}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                key=f"dl_btn_{ver}",
                use_container_width=True
            )
        with d_col2:
            if sys.platform == "win32":
                if st.button("🚀 सीधे Microsoft Word में खोलें व एडिट करें", key=f"open_btn_{ver}", use_container_width=True):
                    open_document_in_word(out_docx_path)
                    st.success("Word में खुल गया! आप इसे अभी एडिट कर सकते हैं।")

        # Preview tabs
        with st.expander("👁️ फॉन्ट कोड प्रिव्यू (Kruti Dev / Unicode)", expanded=False):
            if "Kruti" in clean_font:
                kruti_preview = unicode_to_krutidev(edited_text)
                st.caption("Word में यह टेक्स्ट Kruti Dev 010 फॉन्ट में खुलेगा:")
                st.code(kruti_preview, language="text")
            else:
                st.text(edited_text)
    else:
        st.info("💡 टाइपिंग होने के बाद यहाँ पर आपका नया टेक्स्ट, डाउनलोड बटन व सीधे Word में खोलने का बटन उपलब्ध होगा।")

st.write("")
st.divider()

# ========================================================
# OPTIONAL EXTRA TOOLS (TUCKED NEATLY IN EXPANDERS AT BOTTOM)
# ========================================================
with st.expander("📂 अतिरिक्त टूल्स (तैयार प्रारूप टेम्पलेट्स, कनवर्टर, कीबोर्ड शॉर्टकट गाइड)", expanded=False):
    t_tab1, t_tab2, t_tab3 = st.tabs([
        "📄 तैयार प्रारूप (Templates)",
        "🔄 यूनीकोड ⇋ कृतिदेव कनवर्टर",
        "⌨️ टाइपिंग कीबोर्ड शॉर्टकट (Cheatsheet)"
    ])

    with t_tab1:
        st.write("अक्सर इस्तेमाल होने वाले प्रारूप चुनें और सीधे Word में डाउनलोड करें:")
        t_name = st.selectbox("प्रारूप चुनें:", list(TEMPLATES.keys()))
        t_data = TEMPLATES[t_name]
        t_is_eng = t_data.get("lang") == "English"

        tmpl_body = "\n\n".join(t_data.get("body", []))
        st.text_area("प्रारूप सामग्री:", value=tmpl_body, height=180, key="tmpl_prev")

        t_struct = {
            "court_header": t_data.get("title", ""),
            "case_no": t_data.get("case_no", ""),
            "parties": t_data.get("parties", ""),
            "subject": t_data.get("subject", ""),
            "salutation": t_data.get("salutation", ""),
            "body_paragraphs": tmpl_body,
            "applicant": t_data.get("applicant", "")
        }
        t_font = "Times New Roman" if t_is_eng else "Kruti Dev 010"
        t_path = os.path.join(tempfile.gettempdir(), f"Template_{t_name[:15]}.docx")
        build_court_docx(t_struct, t_path, font_choice=t_font)

        tc1, tc2 = st.columns(2)
        with tc1:
            with open(t_path, "rb") as f:
                st.download_button(
                    label=f"📥 टेम्पलेट DOCX डाउनलोड करें ({t_font})",
                    data=f,
                    file_name=f"{t_name[:25]}_{t_font}.docx",
                    use_container_width=True
                )
        with tc2:
            if sys.platform == "win32":
                if st.button("🚀 सीधे Word में खोलें (Template)", use_container_width=True):
                    open_document_in_word(t_path)
                    st.success("Word में खुल गया!")

    with t_tab2:
        st.write("यूनीकोड (Mangal) ⇋ कृतिदेव 010 टेक्स्ट कनवर्टर:")
        conv_dir = st.radio("दिशा:", ["यूनीकोड ➔ कृतिदेव 010", "कृतिदेव 010 ➔ यूनीकोड"], horizontal=True)
        cin, cout = st.columns(2)
        with cin:
            tin = st.text_area("इनपुट टेक्स्ट यहाँ डालें:", height=180, key="cin_box")
        with cout:
            if conv_dir.startswith("यूनीकोड"):
                tout = unicode_to_krutidev(tin)
            else:
                tout = krutidev_to_unicode(tin)
            st.text_area("कनवर्टेड आउटपुट:", value=tout, height=180, key="cout_box")

    with t_tab3:
        st.write("टाइपिस्टों के लिए जरूरी विशेष अक्षर कोड:")
        ck1, ck2, ck3 = st.columns(3)
        with ck1:
            st.markdown("""
            **सामान्य विशेष अक्षर:**
            - **प्र** = `iz` या `ç`
            - **क्र** = `Ø`
            - **त्र** = `=`
            - **श्र** = `J`
            - **ज्ञ** = `K`
            - **क्ष** = `{k`
            - **द्व** = `}`
            - **द्य** = `|`
            """)
        with ck2:
            st.markdown("""
            **रेफ एवं आधा र:**
            - **र् (कर्म)** = `deZ` (Shift + Z)
            - **्र (ट्र)** = `Vª` (Shift + 3)
            - **ड्र** = `Mª`
            - **हृ** = `â`
            - **ह्र** = `ºz`
            """)
        with ck3:
            st.markdown("""
            **Alt कोड्स:**
            - **सं० (लाघव)** = `Alt + 0144`
            - **“ (उद्धरण)** = `Alt + 0147`
            - **” (उद्धरण)** = `Alt + 0148`
            - **रू** = `Shift + :`
            - **रु** = `Shift + #`
            """)
