"""Knowledge documents: company documents (T&C, FAQ) the bot reads as a knowledge base.

One DynamoDB item per document: PK=company#{company_id}, SK=knowledge#{doc_id}.
The bot reads only items with status == "ready" and enabled == True.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

KNOWLEDGE_SK_PREFIX = "knowledge#"

KnowledgeFileType = Literal["pdf", "docx"]
KnowledgeStatus = Literal["processing", "ready", "failed"]


class KnowledgeDocumentDB(BaseModel):
    """Knowledge document item as stored in DynamoDB."""

    model_config = ConfigDict(extra="forbid")

    PK: str
    SK: str
    doc_id: str
    title: str
    file_name: str
    file_type: KnowledgeFileType
    file_size: int
    s3_key: str
    text: str
    char_count: int
    status: KnowledgeStatus
    error: Optional[str] = None
    enabled: bool = True
    uploaded_at: str
    updated_at: str

    @classmethod
    def build_keys(cls, company_id: str, doc_id: str) -> tuple[str, str]:
        """Return the (PK, SK) pair for a company's document."""
        return f"company#{company_id}", f"{KNOWLEDGE_SK_PREFIX}{doc_id}"
