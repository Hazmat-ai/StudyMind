from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
from ..models.studyset import QuestionType

class FlashcardBase(BaseModel):
    term: str
    definition: str
    order_index: int

class FlashcardDisplay(FlashcardBase):
    id: uuid.UUID
    
    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question: str
    answer: str
    question_type: QuestionType
    options: Optional[dict] = None
    order_index: int

class QuestionDisplay(QuestionBase):
    id: uuid.UUID
    
    class Config:
        from_attributes = True

class StudySetBase(BaseModel):
    title: str
    summary: str
    source_text: str
    concepts: Optional[dict] = None

class StudySetCreate(BaseModel):
    title: str
    summary: str
    source_text: str
    concepts: Optional[dict] = None
    flashcards: List[FlashcardBase]
    questions: List[QuestionBase]

class StudySetDisplay(StudySetBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    flashcards: List[FlashcardDisplay]
    questions: List[QuestionDisplay]

    class Config:
        from_attributes = True

class StudySetListDisplay(StudySetBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Omitting nested full arrays for the list endpoint
    
    class Config:
        from_attributes = True
