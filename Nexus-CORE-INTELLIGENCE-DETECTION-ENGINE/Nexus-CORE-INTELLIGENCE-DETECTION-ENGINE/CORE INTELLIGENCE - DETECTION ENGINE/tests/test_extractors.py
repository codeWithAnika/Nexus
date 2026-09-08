"""
Unit tests for rule and regex-based extractors.
"""

import pytest
from fir_intelligence.phase1_extraction.extractors import (
    extract_all_mentions,
    extract_amounts,
    extract_case_refs,
    extract_dates,
    extract_emails,
    extract_ips,
    extract_phones,
)
from fir_intelligence.phase1_extraction.models import EntityType, RawFIR


def test_extract_phones():
    text = "Contact me at +91 9876543210 or 09988776655 or 98765-43210. Invalid: 12345."
    phones = extract_phones(text)
    assert len(phones) >= 2
    assert any("9876543210" in p for p in phones)
    assert any("9988776655" in p for p in phones)


def test_extract_phones_empty():
    assert extract_phones("") == []
    assert extract_phones(None) == []


def test_extract_emails():
    text = "Send reports to suspect@cyber.org and admin@police.gov.in."
    emails = extract_emails(text)
    assert len(emails) == 2
    assert "suspect@cyber.org" in emails
    assert "admin@police.gov.in" in emails


def test_extract_dates():
    text = "Incident occurred on 15/08/2023, reported on 2023-08-20 and 12-Sep-2023."
    dates = extract_dates(text)
    assert len(dates) == 3
    assert "15/08/2023" in dates
    assert "2023-08-20" in dates


def test_extract_amounts():
    text = "Extorted Rs. 5,00,000 upfront and 5 Lakhs later. Also ₹ 2.5 Crore."
    amounts = extract_amounts(text)
    assert len(amounts) >= 2
    assert any("5,00,000" in a for a in amounts)
    assert any("Crore" in a for a in amounts)


def test_extract_case_refs():
    text = "Ref FIR No. 123/2023 and Crime No. 45-MUM-2024."
    refs = extract_case_refs(text)
    assert len(refs) == 2


def test_extract_ips():
    text = "Attacker IP 192.168.1.100 and server 10.0.0.45."
    ips = extract_ips(text)
    assert len(ips) == 2
    assert "192.168.1.100" in ips
    assert "10.0.0.45" in ips


def test_extract_all_mentions_structured_and_unstructured():
    fir = RawFIR(
        case_ref="FIR-2023-TEST-001",
        complainant_name="Shri Rajesh Verma",
        complainant_address="MG Rd, New Delhi",
        accused_name="Ramesh Kumar",
        narrative_text="Call from +919876543210 demanding Rs 50,000.",
        phone_numbers_mentioned=["+919876543210"],
        amounts_mentioned=["Rs 50,000"]
    )
    mentions = extract_all_mentions(fir)
    assert len(mentions) > 0
    
    # Check source_FIR_id provenance on all mentions
    for m in mentions:
        assert m.source_FIR_id == "FIR-2023-TEST-001"
        assert m.field_source is not None

    types = {m.entity_type for m in mentions}
    assert EntityType.PERSON in types
    assert EntityType.LOCATION in types
    assert EntityType.PHONE in types
    assert EntityType.TRANSACTION in types
