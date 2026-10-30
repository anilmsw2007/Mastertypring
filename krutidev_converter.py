"""
High-Precision Offline Bidirectional Converter: Unicode (Mangal) <--> Kruti Dev 010 / 011
Engineered specifically for Lucknow High Court & UP District/Revenue Courts typing standards.
"""
import re

def normalize_court_text(text: str) -> str:
    """
    Cleans and standardizes court punctuation, legal abbreviations, dates, and bullet numbers
    so they map cleanly to High Court / UP typing standards without visual artifacts (e.g., ण्, ध्, रू).
    """
    if not text:
        return ""
    
    # Strip markdown symbols
    text = re.sub(r'#+\s*', '', text)
    text = text.replace('**', '').replace('*', '')
    text = text.replace('---', ' ')
    text = text.replace('```', '')

    # Deduplicate signature and consecutive duplicate words (e.g. 'हस्ताक्षर हस्ताक्षर', 'ह० हस्ताक्षर')
    text = re.sub(r'ह[०0\.]\s*हस्ताक्षर', 'हस्ताक्षर', text)
    text = re.sub(r'(हस्ताक्षर)\s*[:\-]?\s*[\(\[]?\s*हस्ताक्षर\s*[\)\]]?', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(हस्ताक्षर|प्रार्थी|अधिवक्ता|श्रीमान|बनाम|दिनांक|न्यायालय)\s*[:\-]?\s*\1\b', r'\1', text)

    # Strip any meta headers or 'क्या है' lines from typing output
    text = re.sub(r'(^|\n)\s*(दस्तावेज़|दस्तावेज)\s*(की\s*प्रकृति|का\s*प्रकार|क्या\s*है|का\s*विवरण)\s*[:\-][^\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(^|\n)\s*(यह\s*(दस्तावेज़|दस्तावेज)\s*क्या\s*है|प्रस्तुत\s*(दस्तावेज़|दस्तावेज)|प्रकृति|प्रकार|क्या\s*है)\s*[:\-][^\n]*', '', text, flags=re.IGNORECASE)

    # Brackets: In Kruti Dev 010, '[' renders as आधा ख (ख्) and ']' renders as comma (])!
    # Convert all square brackets and curly braces to round brackets to prevent unwanted आधा ख.
    text = text.replace('[', '(').replace(']', ')')
    text = text.replace('{', '(').replace('}', ')')

    # 1. Dates: '20.02.2026' or '20/02/2026' -> '20-02-2026' (hyphen displays cleanly in Kruti Dev & English)
    text = re.sub(r'\b(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{2,4})\b', r'\1-\2-\3', text)

    # 2. Numbered paragraphs/bullets: '1.' or '1)' or '1ण्' -> '1- ' (High Court standard)
    # (?!\d) ensures decimal areas like 0.2530 or 1.50 are NEVER converted into '0- 2530'!
    text = re.sub(r'(^|\n)\s*(\d+)[\.\)ण्]\s*(?!\d)', r'\1\2- ', text)
    text = re.sub(r'(\s+)(\d+)[\.\)ण्]\s*(?!\d)', r'\1\2- ', text)

    # 3. Trailing dot on common legal words: 'संख्या.' -> 'संख्या ', 'धारा.' -> 'धारा '
    text = re.sub(r'संख्या\.\s*', 'संख्या ', text)
    text = re.sub(r'धारा\.\s*', 'धारा ', text)
    text = re.sub(r'तहसील\.\s*', 'तहसील ', text)
    text = re.sub(r'थाना\.\s*', 'थाना ', text)
    text = re.sub(r'जिला\.\s*', 'जिला ', text)
    text = re.sub(r'ग्राम\.\s*', 'ग्राम ', text)
    text = re.sub(r'परगना\.\s*', 'परगना ', text)
    text = re.sub(r'विषय\.\s*', 'विषय: ', text)

    # 4. Standard Hindi legal abbreviations (convert dot to laghav zero '0'):
    # e.g., यू.पी. -> यू0पी0, मु.अ.सं. -> मु0अ0सं0, सं. -> सं0, दि. -> दि0, ता. -> ता0
    text = re.sub(r'(^|[\s\(])([\u0900-\u097F]{1,2})\.', r'\g<1>\g<2>0', text)
    text = re.sub(r'0([\u0900-\u097F]{1,2})\.', r'0\g<1>0', text)
    text = re.sub(r'0([\u0900-\u097F]{1,2})\.', r'0\g<1>0', text)

    # 5. Sentence ending dot in Hindi text: 'थी.' -> 'थी।', 'हुआ.' -> 'हुआ।'
    text = re.sub(r'([\u0900-\u097F]+)\s*\.\s*(?=[\n\r]|$)', r'\1।', text)
    text = re.sub(r'([\u0900-\u097F]{2,})\s*\.\s+(?=[\u0900-\u097F])', r'\1। ', text)

    # 6. Any other stray dot after Hindi character: drop or convert
    text = re.sub(r'([\u0900-\u097F])\.(?=\s|$)', r'\1', text)

    # 7. Word-final halant cleanup (Fixes 'श्रीमान्' -> 'श्रीमान', 'एवम्' -> 'एवं', 'अर्थात्' -> 'अर्थात')
    # In Kruti Dev 010, word-final halants render as truncated half-consonants (e.g. half न 'U', half म 'E').
    # Court typing requires full 'श्रीमान' ('Jheku') and 'एवं' (',oa').
    text = text.replace('श्रीमान्', 'श्रीमान')
    text = text.replace('एवम्', 'एवं')
    text = text.replace('अर्थात्', 'अर्थात')
    text = text.replace('विद्वान्', 'विद्वान')
    text = text.replace('भगवान्', 'भगवान')
    text = text.replace('संवत्', 'संवत')
    text = text.replace('पश्चात्', 'पश्चात')
    text = text.replace('बनाम्', 'बनाम')
    text = text.replace('प्रथम्', 'प्रथम')
    text = text.replace('किन्तु्', 'किन्तु')
    text = text.replace('परन्तु्', 'परन्तु')
    # Convert trailing halant m to anusvara or full m
    text = re.sub(r'([\u0900-\u097F]+)म्(?=[\s\.,।\?!\)\]\"\'\:\;\-]|$)', r'\1ं', text)
    # Strip any trailing halant on consonants before spaces or punctuation
    text = re.sub(r'([\u0915-\u0939])\u094d(?=[\s\.,।\?!\)\]\"\'\:\;\-]|$)', r'\1', text)

    # Standard court abbreviation zero
    text = text.replace("०", "0")

    return text

def unicode_to_krutidev(text: str) -> str:
    """
    Converts Hindi Unicode (Mangal/Devanagari) text into Kruti Dev 010 / 011 ASCII text.
    """
    if not text:
        return ""

    # Normalize court text first
    modified_text = normalize_court_text(text)


    # Step 1: Handle Reph (र्) - moves to end of the consonant cluster + vowel matra
    # e.g., र् + थ + ी -> थ + ी + Z (र्थी -> FkhZ)
    reph_pattern = re.compile(r'\u0930\u094d((?:[\u0915-\u0939]\u093c?\u094d)*[\u0915-\u0939]\u093c?[\u093e-\u094c\u0902\u0901]*)')
    modified_text = reph_pattern.sub(r'\1Z', modified_text)

    # Step 2: Handle Chhoti Ee (ि) matra - moves BEFORE the consonant cluster
    # Allows nukta (e.g. कड़ियां -> dfM+;ka)
    ee_pattern = re.compile(r'((?:[\u0915-\u0939]\u093c?\u094d)*[\u0915-\u0939]\u093c?)\u093f')
    modified_text = ee_pattern.sub(r'f\1', modified_text)

    # Step 3: Exact Character Replacements (Ordered from longest combinations to single characters)
    replacements = [
        # Punctuation & symbols
        ("‘", "^"), ("’", "*"), ("“", "Þ"), ("”", "ß"),
        ("(", "¼"), (")", "½"), ("{", "¿"), ("}", "À"),
        ("=", "¾"), ("।", "A"), ("?", "\\"), ("॰", "Œ"),
        (",", "]"),
        (":", "%"),   # Colon maps to % (Visarga ः in Kruti Dev) so it displays as two dots : and not as 'रू'
        (";", ";"),
        ("-", "-"),   # Keep hyphen as hyphen so it does not turn into '६'
        ("&", " o "), # Ampersand maps to 'व' so it does not turn into '६'

        
        # Devanagari Digits
        ("०", "å"), ("१", "ƒ"), ("२", "„"), ("३", "…"), ("४", "†"),
        ("५", "‡"), ("६", "ˆ"), ("७", "‰"), ("८", "Š"), ("९", "‹"),
        
        # Nukta conjuncts
        ("फ़्", "¶"), ("क़", "d"), ("ख़", "[k"), ("ग़", "x"),
        ("ज़्", "T"), ("ज़", "t"), ("ड़", "M+"), ("ढ़", "<+"),
        ("फ़", "Q"), ("य़", ";"), ("ऱ", "j"), ("ऩ", "u"),
        
        # Special conjuncts
        ("त्त्", "Ù"), ("त्त", "Ùk"), ("क्त", "Dr"), ("दृ", "n`"), ("कृ", "d`"),
        ("ह्न", "à"), ("ह्य", "á"), ("हृ", "â"), ("ह्म", "ã"), ("ह्र", "ºz"), ("ह्", "º"),
        ("द्द", "í"), ("क्ष्", "{"), ("क्ष", "{k"), ("त्र्", "«"), ("त्र", "="), ("ज्ञ", "K"),
        ("छ्य", "Nî"), ("ट्य", "Vî"), ("ठ्य", "Bî"), ("ड्य", "Mî"), ("ढ्य", "<î"),
        ("द्य", "|"), ("द्व", "}"),
        ("श्र", "J"), ("ट्र", "Vª"), ("ड्र", "Mª"), ("ढ्र", "<ªª"), ("छ्र", "Nª"),
        ("क्र", "Ø"), ("फ्र", "Ý"), ("द्र", "æ"), ("प्र", "iz"), ("ग्र", "xz"),
        ("रु", "#"), ("रू", ":"),
        ("्र", "z"),

        # Independent vowels
        ("ओ", "vks"), ("औ", "vkS"), ("आ", "vk"), ("अ", "v"),
        ("ई", "bZ"), ("इ", "b"), ("उ", "m"), ("ऊ", "Å"),
        ("ऐ", ",s"), ("ए", ","), ("ऋ", "_"),

        # Consonants with virama (half) and full
        ("क्क", "ô"), ("क्", "D"), ("क", "d"),
        ("ख्", "["), ("ख", "[k"),
        ("ग्", "X"), ("ग", "x"),
        ("घ्", "?"), ("घ", "?k"),
        ("ङ", "³"),
        ("चै", "pkS"), ("च्", "P"), ("च", "p"),
        ("छ", "N"),
        ("ज्", "T"), ("ज", "t"),
        ("झ्", "÷"), ("झ", ">"),
        ("ञ", "¥"),
        ("ट्ट", "ê"), ("ट्ठ", "ë"), ("ट", "V"),
        ("ठ", "B"),
        ("ड्ड", "ì"), ("ड्ढ", "ï"), ("ड", "M"),
        ("ढ", "<"),
        ("ण्", "."), ("ण", ".k"),
        ("त्", "R"), ("त", "r"),
        ("थ्", "F"), ("थ", "Fk"),
        ("द्ध", ")"), ("द", "n"),
        ("ध्", "/"), ("ध", "/k"),
        ("न्", "U"), ("न", "u"),
        ("प्", "I"), ("प", "i"),
        ("फ्", "¶"), ("फ", "Q"),
        ("ब्", "C"), ("ब", "c"),
        ("भ्", "H"), ("भ", "Hk"),
        ("म्", "E"), ("म", "e"),
        ("य्", "¸"), ("य", ";"),
        ("र", "j"),
        ("ल्", "Y"), ("ल", "y"),
        ("ळ", "G"),
        ("व्", "O"), ("व", "o"),
        ("श्", "'"), ("श", "'k"),
        ("ष्", "\""), ("ष", "\"k"),
        ("स्", "L"), ("स", "l"),
        ("ह", "g"),

        # Dependent vowel signs (matras)
        ("ऑ", "v‚"), ("ॉ", "‚"),
        ("ो", "ks"), ("ौ", "kS"), ("ा", "k"), ("ी", "h"),
        ("ु", "q"), ("ू", "w"), ("ृ", "`"), ("े", "s"), ("ै", "S"),
        ("ं", "a"), ("ँ", "¡"), ("ः", "%"), ("ॅ", "W"), ("ऽ", "·"),
        ("् ", "~ "), ("्", "~")
    ]

    for uni, kd in replacements:
        modified_text = modified_text.replace(uni, kd)

    return modified_text


def krutidev_to_unicode(text: str) -> str:
    """
    Converts Kruti Dev 010 / 011 ASCII text into Hindi Unicode (Mangal/Devanagari) text.
    """
    if not text:
        return ""

    modified_text = text

    # Move 'f' to correct position (after consonant cluster)
    # in Kruti Dev 'f' is placed before consonant cluster
    array_half = ["D", "[", "X", "?", "P", "T", "R", "F", "/", "U", "I", "C", "H", "E", "Y", "O", "'", "\"", "L", "~"]
    
    pos_f = modified_text.rfind("f")
    while pos_f != -1:
        # find what character comes after f
        next_idx = pos_f + 1
        # scan forward through cluster
        while next_idx < len(modified_text) and modified_text[next_idx] in array_half:
            next_idx += 1
        # skip main consonant
        if next_idx < len(modified_text):
            next_idx += 1
            # if consonant has two letters like [k, ?k, /k, Fk, Hk, 'k, "k, .k
            if next_idx < len(modified_text) and modified_text[next_idx] == 'k' and modified_text[next_idx-1] in "[?/FH'\".":
                next_idx += 1
        
        modified_text = modified_text[:pos_f] + modified_text[pos_f+1:next_idx] + "f" + modified_text[next_idx:]
        pos_f = modified_text.rfind("f", 0, pos_f - 1)

    modified_text = modified_text.replace("f", "ि")

    # Move 'Z' (reph) to before the cluster
    pos_z = modified_text.find("Z")
    matras = ["‚", "ks", "kS", "k", "h", "q", "w", "`", "s", "S", "a", "¡", "%", "W", "·", "~ ", "~"]
    while pos_z != -1:
        modified_text = modified_text.replace("Z", "", 1)
        # scan backwards
        idx = pos_z - 1
        while idx > 0 and (modified_text[idx] in matras or modified_text[idx] in "k"):
            idx -= 1
        # scan back before half chars
        while idx > 0 and modified_text[idx] in array_half:
            idx -= 1
        modified_text = modified_text[:idx] + "र्" + modified_text[idx:]
        pos_z = modified_text.find("Z")

    replacements = [
        ("ñ", "॰"), ("Q+Z", "QZ+"), ("sas", "sa"), ("aa", "a"), (")Z", "र्द्ध"),
        ("å", "०"), ("ƒ", "१"), ("„", "२"), ("…", "३"), ("†", "४"),
        ("‡", "५"), ("ˆ", "६"), ("‰", "७"), ("Š", "८"), ("‹", "९"),
        ("¶+", "फ़्"), ("d+", "क़"), ("[+k", "ख़"), ("[+", "ख़्"), ("x+", "ग़"),
        ("T+", "ज़्"), ("t+", "ज़"), ("M+", "ड़"), ("<+", "ढ़"), ("Q+", "फ़"),
        (";+", "य़"), ("j+", "ऱ"), ("u+", "ऩ"),
        ("Ùk", "त्त"), ("Ù", "त्त्"), ("Dr", "क्त"), ("–", "दृ"), ("—", "कृ"),
        ("à", "ह्न"), ("á", "ह्य"), ("â", "हृ"), ("ã", "ह्म"), ("ºz", "ह्र"), ("º", "ह्"),
        ("í", "द्द"), ("{k", "क्ष"), ("{", "क्ष्"), ("=", "त्र"), ("«", "त्र्"),
        ("Nî", "छ्य"), ("Vî", "ट्य"), ("Bî", "ठ्य"), ("Mî", "ड्य"), ("<î", "ढ्य"),
        ("|", "द्य"), ("K", "ज्ञ"), ("}", "द्व"),
        ("J", "श्र"), ("Vª", "ट्र"), ("Mª", "ड्र"), ("<ªª", "ढ्र"), ("Nª", "छ्र"),
        ("Ø", "क्र"), ("Ý", "फ्र"), ("æ", "द्र"), ("ç", "प्र"), ("iz", "प्र"), ("xz", "ग्र"),
        ("#", "रु"), (":", "रू"),
        ("vks", "ओ"), ("vkS", "औ"), ("vk", "आ"), ("v", "अ"),
        ("bZ", "ई"), ("b", "इ"), ("m", "उ"), ("Å", "ऊ"), (",s", "ऐ"), (",", "ए"), ("_", "ऋ"),
        ("ô", "क्क"), ("Dk", "क"), ("D", "क्"), ("d", "क"),
        ("[k", "ख"), ("[", "ख्"),
        ("Xk", "ग"), ("X", "ग्"), ("x", "ग"),
        ("Ä", "घ"), ("?k", "घ"), ("?", "घ्"), ("³", "ङ"),
        ("pkS", "चै"), ("Pk", "च"), ("P", "च्"), ("p", "च"),
        ("N", "छ"),
        ("Tk", "ज"), ("T", "ज्"), ("t", "ज"),
        (">", "झ"), ("÷", "झ्"), ("¥", "ञ"),
        ("ê", "ट्ट"), ("ë", "ट्ठ"), ("V", "ट"), ("B", "ठ"),
        ("ì", "ड्ड"), ("ï", "ड्ढ"), ("M", "ड"), ("<", "ढ"),
        (".k", "ण"), (".", "ण्"),
        ("Rk", "त"), ("R", "त्"), ("r", "त"),
        ("Fk", "थ"), ("F", "थ्"),
        (")", "द्ध"), ("n", "द"),
        ("èk", "ध"), ("/k", "ध"), ("/", "ध्"),
        ("Uk", "न"), ("U", "न्"), ("u", "न"),
        ("Ik", "प"), ("I", "प्"), ("i", "प"),
        ("¶", "फ्"), ("Q", "फ"),
        ("Ck", "ब"), ("C", "ब्"), ("c", "ब"),
        ("Hk", "भ"), ("H", "भ्"),
        ("Ek", "म"), ("E", "म्"), ("e", "म"),
        ("¸", "य्"), (";", "य"),
        ("j", "र"),
        ("Yk", "ल"), ("Y", "ल्"), ("y", "ल"),
        ("G", "ळ"),
        ("Ok", "व"), ("O", "व्"), ("o", "व"),
        ("'k", "श"), ("'", "श्"),
        ("\"k", "ष"), ("\"", "ष्"),
        ("Lk", "स"), ("L", "स्"), ("l", "स"),
        ("g", "ह"),
        ("z", "्र"),
        ("‚", "ॉ"), ("ks", "ो"), ("kS", "ौ"), ("k", "ा"), ("h", "ी"),
        ("q", "ु"), ("w", "ू"), ("`", "ृ"), ("s", "े"), ("S", "ै"),
        ("a", "ं"), ("¡", "ँ"), ("%", "ः"), ("W", "ॅ"), ("·", "ऽ"),
        ("~ ", "् "), ("~", "्"),
        ("^", "‘"), ("*", "’"), ("Þ", "“"), ("ß", "”"),
        ("¼", "("), ("½", ")"), ("¿", "{"), ("À", "}"), ("¾", "="),
        ("A", "।"), ("\\", "?"), ("&", "-"), ("Œ", "॰"), ("]", ","),
        ("0", "०")
    ]

    for kd, uni in replacements:
        modified_text = modified_text.replace(kd, uni)

    return modified_text

if __name__ == "__main__":
    tests = [
        "न्यायालय चकबन्दी अधिकारी उच्चौलिया खीरी",
        "प्रकीर्ण वाद सं० 01/08",
        "अधिकारी",
        "निम्नलिखित",
        "उप जिलाधिकारी महोदय",
        "प्रार्थी",
        "निर्णय"
    ]
    for t in tests:
        kd = unicode_to_krutidev(t)
        print(f"Unicode : {t}")
        print(f"KrutiDev: {kd}")
        back = krutidev_to_unicode(kd)
        print(f"Back    : {back}\n")
