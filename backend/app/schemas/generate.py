import uuid
from typing import Literal
from pydantic import Field, model_validator, field_validator
from .auth import StrictModel


class GenerateOptions(StrictModel):
    num_flashcards: int = Field(default=10, ge=1, le=30, strict=True)
    num_questions: int = Field(default=5, ge=1, le=15, strict=True)
    difficulty: Literal["high_school", "university", "advanced"] = "university"


class GenerateRequest(StrictModel):
    content: str = Field(min_length=50, max_length=12000)
    options: GenerateOptions = Field(default_factory=GenerateOptions)
    consent_to_provider: Literal[True]

    @field_validator("consent_to_provider", mode="before")
    @classmethod
    def explicit_consent(cls, value):
        if type(value) is not bool or not value:
            raise ValueError("Explicit consent is required")
        return value

    @field_validator("content")
    @classmethod
    def readable_content(cls, value):
        value = value.strip()
        if len(value) < 50:
            raise ValueError("Provide at least 50 readable characters")
        return value


class GeneratedFlashcard(StrictModel):
    term: str = Field(min_length=1, max_length=255)
    definition: str = Field(min_length=1, max_length=3000)


class GeneratedQuestion(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=3000)
    type: Literal["short_answer", "multiple_choice"]
    options: list[str] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def validate_options(self):
        if self.type == "multiple_choice" and (
            not 2 <= len(self.options) <= 6
            or self.answer not in self.options
            or len(set(self.options)) != len(self.options)
            or any(not 1 <= len(s) <= 1000 for s in self.options)
        ):
            raise ValueError(
                "Multiple-choice answers must identify one of 2–6 distinct options"
            )
        if self.type == "short_answer" and self.options:
            raise ValueError("Short-answer questions must not have options")
        return self


class GeneratedConcept(StrictModel):
    term: str = Field(min_length=1, max_length=255)
    related: list[str] = Field(max_length=8)

    @model_validator(mode="after")
    def bounded_related(self):
        if any(not 1 <= len(s) <= 255 for s in self.related):
            raise ValueError("Related concepts must be short terms")
        return self


class StudyMaterial(StrictModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1, max_length=16000)
    flashcards: list[GeneratedFlashcard] = Field(min_length=1, max_length=30)
    questions: list[GeneratedQuestion] = Field(min_length=1, max_length=15)
    concepts: list[GeneratedConcept] = Field(max_length=30)


class GenerateResponse(StudyMaterial):
    generation_id: uuid.UUID
