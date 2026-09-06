"""
Canonicalization and normalization functions per entity type.
Transforms messy raw string mentions into clean, standard canonical and display representations.
"""

from datetime import datetime
import re
from typing import Tuple
from .models import EntityType, RawMention


# Honorifics to strip for Person name canonical form
PERSON_HONORIFICS = re.compile(
    r'\b(?:shri|smt|mr|mrs|ms|dr|advocate|adv|alias|aka|s/o|d/o|w/o|c/o|son of|daughter of|wife of)\b\.?',
    re.IGNORECASE
)

# Common Indian address abbreviations mapping
ADDRESS_ABBREVIATIONS = {
    r'\brd\b\.?': 'Road',
    r'\bst\b\.?': 'Street',
    r'\bnag\b\.?': 'Nagar',
    r'\bapt\b\.?': 'Apartment',
    r'\bapts\b\.?': 'Apartments',
    r'\bflt\b\.?': 'Flat',
    r'\bps\b\.?': 'Police Station',
    r'\bdist\b\.?': 'District',
    r'\bnr\b\.?': 'Near',
    r'\bopp\b\.?': 'Opposite',
    r'\bh\.no\b\.?': 'House No',
    r'\bhno\b\.?': 'House No',
    r'\bplt\b\.?': 'Plot',
    r'\bsec\b\.?': 'Sector',
    r'\bcol\b\.?': 'Colony',
    r'\bmrg\b\.?': 'Marg',
}


def normalize_person_name(raw: str) -> Tuple[str, str]:
    """
    Canonical form: lowercase, honorifics stripped, punctuation removed, whitespace collapsed.
    Display form: Title-cased cleaned name without honorifics.
    """
    if not raw:
        return "", ""
    
    # Strip honorifics
    cleaned = PERSON_HONORIFICS.sub(' ', raw)
    # Remove special chars except spaces
    cleaned = re.sub(r'[^a-zA-Z\s]', ' ', cleaned)
    # Collapse whitespace
    words = [w for w in cleaned.split() if w]
    
    if not words:
        # Fallback if all words were honorifics/special chars
        words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', raw).split() if w]
        
    canonical = " ".join(words).lower()
    display = " ".join(words).title()
    return canonical, display


def normalize_phone(raw: str) -> Tuple[str, str]:
    """
    Normalizes phone numbers to E.164 format (+91XXXXXXXXXX for Indian numbers).
    """
    digits = re.sub(r'\D', '', raw)
    
    # Handle Indian country code / 10-digit cases
    if len(digits) == 10:
        e164 = f"+91{digits}"
    elif len(digits) == 11 and digits.startswith('0'):
        e164 = f"+91{digits[1:]}"
    elif len(digits) == 12 and digits.startswith('91'):
        e164 = f"+{digits}"
    elif len(digits) > 5:
        e164 = f"+{digits}"
    else:
        e164 = raw.strip()
        
    display = e164
    return e164, display


def normalize_email(raw: str) -> Tuple[str, str]:
    """
    Normalizes email addresses (lowercased, trimmed).
    """
    cleaned = raw.strip().lower()
    return cleaned, cleaned


def normalize_address(raw: str) -> Tuple[str, str]:
    """
    Tokenizes address, expands common abbreviations (Rd -> Road, St -> Street, etc.),
    normalizes punctuation and whitespace.
    """
    if not raw:
        return "", ""
        
    text = raw.strip()
    
    # Apply abbreviation expansions
    for pattern, replacement in ADDRESS_ABBREVIATIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
    # Collapse multiple commas / spaces
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r',\s*,', ',', text).strip(' ,')
    
    # Canonical: lowercase with clean single spaces
    canonical = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    canonical = " ".join(canonical.split())
    
    # Display: clean formatted address
    display = text.title()
    return canonical, display


def normalize_amount(raw: str) -> Tuple[str, str]:
    """
    Normalizes monetary amounts (₹, Rs, INR, Lakh, Crore notation).
    Returns numerical value string as canonical, formatted INR string for display.
    """
    if not raw:
        return "0", "₹0"
        
    text = raw.strip().lower()
    
    multiplier = 1.0
    if 'crore' in text or 'cr' in text:
        multiplier = 10000000.0
    elif 'lakh' in text or 'lac' in text:
        multiplier = 10000.0 if 'lac' in text and 'lakh' not in text else 100000.0
    elif 'k' in text or 'thousand' in text:
        multiplier = 1000.0
        
    # Extract numerical portion
    nums = re.findall(r'[\d,]+(?:\.\d+)?', text)
    if not nums:
        return raw.strip(), raw.strip()
        
    num_str = nums[0].replace(',', '')
    try:
        val = float(num_str) * multiplier
        canonical = f"{val:.2f}"
        
        # Indian number formatting for display (e.g. 5,00,000)
        display = format_indian_currency(val)
        return canonical, display
    except ValueError:
        return raw.strip(), raw.strip()


def format_indian_currency(amount: float) -> str:
    """Helper to format float currency in Indian currency notation (₹ X,XX,XXX.XX)."""
    s, *d = f"{amount:.2f}".split('.')
    r = []
    if len(s) > 3:
        r.append(s[-3:])
        s = s[:-3]
        while len(s) > 2:
            r.append(s[-2:])
            s = s[:-2]
        if s:
            r.append(s)
        formatted_int = ",".join(reversed(r))
    else:
        formatted_int = s
        
    if d and d[0] != '00':
        return f"₹{formatted_int}.{d[0]}"
    return f"₹{formatted_int}"


def normalize_date(raw: str) -> Tuple[str, str]:
    """
    Normalizes varied date formats into ISO 8601 (YYYY-MM-DD).
    """
    if not raw:
        return "", ""
        
    raw_clean = raw.strip()
    
    # Common date formats
    date_formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%d-%b-%Y",
        "%m/%d/%Y"
    ]
    
    # Clean ordinal suffixes (15th -> 15)
    cleaned_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', raw_clean, flags=re.IGNORECASE)
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(cleaned_str, fmt)
            iso = dt.strftime("%Y-%m-%d")
            return iso, iso
        except ValueError:
            continue
            
    # Fallback if unparseable
    return raw_clean.lower(), raw_clean


def normalize_ip(raw: str) -> Tuple[str, str]:
    """Normalizes IP address."""
    ip = raw.strip().lower()
    return ip, ip


def normalize_case_ref(raw: str) -> Tuple[str, str]:
    """Normalizes Case/FIR reference number."""
    ref = re.sub(r'\s+', ' ', raw.strip().upper())
    return ref, ref


def normalize_mention(mention: RawMention) -> Tuple[str, str]:
    """
    Unified normalizer dispatcher for any RawMention.
    Returns (canonical_value, display_value).
    """
    val = mention.raw_value
    t = mention.entity_type
    
    if t == EntityType.PERSON:
        return normalize_person_name(val)
    elif t == EntityType.PHONE:
        return normalize_phone(val)
    elif t == EntityType.EMAIL:
        return normalize_email(val)
    elif t == EntityType.LOCATION:
        return normalize_address(val)
    elif t == EntityType.TRANSACTION:
        return normalize_amount(val)
    elif t == EntityType.EVENT:
        return normalize_date(val)
    elif t == EntityType.IP:
        return normalize_ip(val)
    elif t == EntityType.CASE_REF:
        return normalize_case_ref(val)
    else:
        cleaned = val.strip()
        return cleaned.lower(), cleaned
