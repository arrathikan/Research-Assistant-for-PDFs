"""Small broker envelopes: identities only, never PDF text or provider credentials."""

from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

JobStage = Literal["ingestion", "summary"]
JobStatus = Literal["QUEUED", "RUNNING", "RETRY_WAIT", "COMPLETED", "DEAD_LETTER"]
FailureCode = Literal[
    "PARSING_FAILED",
    "CHUNKING_FAILED",
    "EMBEDDING_FAILED",
    "SUMMARY_FAILED",
    "STORAGE_UNAVAILABLE",
    "SOURCE_BUSY",
    "SOURCE_CHANGED",
    "WORKER_INTERRUPTED",
    "DOCUMENT_MISSING",
    "INVALID_MESSAGE",
    "UNKNOWN_JOB",
    "PROCESSING_FAILED",
]


def job_id(document_id: str) -> str:
    return sha256(f"processing-v1:{document_id}".encode()).hexdigest()


class JobMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1] = 1
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_id: str = Field(pattern=r"^[0-9a-f]{24}$")
    generation: int = Field(default=1, ge=1)
    stage: JobStage = "ingestion"
    attempt: int = Field(default=1, ge=1, le=5)

    @model_validator(mode="after")
    def validate_identity(self) -> "JobMessage":
        if self.job_id != job_id(self.document_id):
            raise ValueError("Job identity does not match its document")
        return self

    def identity(self) -> dict:
        return self.model_dump(include={"job_id", "document_id", "generation", "stage", "attempt"})

    def message_id(self) -> str:
        return sha256(self.model_dump_json().encode()).hexdigest()


class DeadLetter(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1] = 1
    reason: FailureCode
    job: JobMessage | None = None
