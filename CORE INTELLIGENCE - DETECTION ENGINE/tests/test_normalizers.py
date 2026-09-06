"""
Unit tests for entity normalizers.
"""

from fir_intelligence.phase1_extraction.models import EntityType, RawMention
from fir_intelligence.phase1_extraction.normalizers import (
    normalize_address,
    normalize_amount,
    normalize_date,
    normalize_email,
    normalize_mention,
    normalize_person_name,
    normalize_phone,
)


def test_normalize_person_name():
    canonical, display = normalize_person_name("Shri Ramesh Kumar Sharma s/o Suresh")
    assert canonical == "ramesh kumar sharma suresh"
    assert display == "Ramesh Kumar Sharma Suresh"

    canonical, display = normalize_person_name("Advocate Priya Nair Alias Pinky")
    assert canonical == "priya nair pinky"


def test_normalize_phone():
    e164, display = normalize_phone("9876543210")
    assert e164 == "+919876543210"
    
    e164_2, _ = normalize_phone("+91 98765-43210")
    assert e164_2 == "+919876543210"


def test_normalize_email():
    canonical, _ = normalize_email(" SUSPECT.sharma@CyberCrime.ORG ")
    assert canonical == "suspect.sharma@cybercrime.org"


def test_normalize_address():
    canonical, display = normalize_address("Flat 402, Green Park Apt, MG Rd, New Delhi")
    assert "road" in canonical
    assert "apartment" in canonical
    assert "Apartment" in display
    assert "Road" in display


def test_normalize_amount():
    can1, disp1 = normalize_amount("Rs. 5,00,000")
    assert float(can1) == 500000.0
    assert "5,00,000" in disp1

    can2, disp2 = normalize_amount("5 Lakhs")
    assert float(can2) == 500000.0

    can3, disp3 = normalize_amount("₹ 2.5 Crore")
    assert float(can3) == 25000000.0


def test_normalize_date():
    iso1, _ = normalize_date("15/08/2023")
    assert iso1 == "2023-08-15"

    iso2, _ = normalize_date("12-Sep-2023")
    assert iso2 == "2023-09-12"


def test_normalize_mention_dispatcher():
    mention = RawMention(
        entity_type=EntityType.PERSON,
        raw_value="Smt. Sunita Sharma",
        source_FIR_id="FIR-001",
        field_source="complainant_name"
    )
    canonical, display = normalize_mention(mention)
    assert canonical == "sunita sharma"
    assert display == "Sunita Sharma"
