import pytest
from pydantic import ValidationError

from chatbet_base_models.knowledge_document import (
    KNOWLEDGE_SK_PREFIX,
    KnowledgeDocumentDB,
)


def _valid_item() -> dict:
    pk, sk = KnowledgeDocumentDB.build_keys("bolabet-zm", "a" * 32)
    return {
        "PK": pk,
        "SK": sk,
        "doc_id": "a" * 32,
        "title": "Terms and Conditions",
        "file_name": "terms.docx",
        "file_type": "docx",
        "file_size": 28862,
        "s3_key": "bolabet-zm/knowledge/" + "a" * 32 + ".docx",
        "text": "1. Intro\n1.1 Clause",
        "char_count": 19,
        "status": "ready",
        "uploaded_at": "2026-10-13T10:00:00+00:00",
        "updated_at": "2026-10-13T10:00:00+00:00",
    }


def test_build_keys_follow_the_contract():
    pk, sk = KnowledgeDocumentDB.build_keys("bolabet-zm", "abc")
    assert pk == "company#bolabet-zm"
    assert sk == f"{KNOWLEDGE_SK_PREFIX}abc"
    assert KNOWLEDGE_SK_PREFIX == "knowledge#"


def test_valid_item_defaults_enabled_true_and_error_none():
    item = KnowledgeDocumentDB(**_valid_item())
    assert item.enabled is True
    assert item.error is None


def test_extra_fields_are_forbidden():
    with pytest.raises(ValidationError):
        KnowledgeDocumentDB(**_valid_item(), created_at="2026-10-13T10:00:00+00:00")


@pytest.mark.parametrize("field,value", [("status", "queued"), ("file_type", "txt")])
def test_invalid_enum_values_are_rejected(field: str, value: str):
    data = _valid_item()
    data[field] = value
    with pytest.raises(ValidationError):
        KnowledgeDocumentDB(**data)


def test_model_dump_contains_exactly_the_contract_fields():
    assert set(KnowledgeDocumentDB(**_valid_item()).model_dump()) == {
        "PK", "SK", "doc_id", "title", "file_name", "file_type", "file_size",
        "s3_key", "text", "char_count", "status", "error", "enabled",
        "uploaded_at", "updated_at",
    }
