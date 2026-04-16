from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from ..models.studyset import QuestionType
import uuid

class GenerateOptions(BaseModel):
    num_flashcards: int = Field(default=10, ge=1, le=50)
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="university")

class GenerateRequest(BaseModel):
    content: str = Field(..., min_length=10)
    options: GenerateOptions = GenerateOptions()

class GeneratedFlashcard(BaseModel):
    term: str
    definition: str

class GeneratedQuestion(BaseModel):
    question: str
    answer: str
    type: QuestionType

class GeneratedConcept(BaseModel):
    term: str
    related: List[str]

class GenerateResponse(BaseModel):
    title: str
    summary: str
    flashcards: List[GeneratedFlashcard]
    questions: List[GeneratedQuestion]
    concepts: List[GeneratedConcept]
