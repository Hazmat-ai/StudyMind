import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..models.studyset import StudySet, Flashcard, Question
from ..schemas.studyset import StudySetCreate, StudySetDisplay, StudySetListDisplay
from .auth import get_current_user

router = APIRouter()

@router.post("", response_model=StudySetDisplay, status_code=status.HTTP_201_CREATED)
def create_studyset(
    studyset_in: StudySetCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    new_studyset = StudySet(
        user_id=current_user.id,
        title=studyset_in.title,
        source_text=studyset_in.source_text,
        summary=studyset_in.summary,
        concepts=studyset_in.concepts
    )
    db.add(new_studyset)
    db.flush() # flush to get the id

    for fc in studyset_in.flashcards:
        db.add(Flashcard(
            study_set_id=new_studyset.id,
            term=fc.term,
            definition=fc.definition,
            order_index=fc.order_index
        ))
        
    for q in studyset_in.questions:
        db.add(Question(
            study_set_id=new_studyset.id,
            question=q.question,
            answer=q.answer,
            question_type=q.question_type,
            options=q.options,
            order_index=q.order_index
        ))

    db.commit()
    db.refresh(new_studyset)
    return new_studyset

@router.get("", response_model=List[StudySetListDisplay])
def get_user_studysets(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    studysets = db.query(StudySet).filter(StudySet.user_id == current_user.id).order_by(StudySet.created_at.desc()).all()
    return studysets

@router.get("/{studyset_id}", response_model=StudySetDisplay)
def get_studyset(
    studyset_id: uuid.UUID,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    studyset = db.query(StudySet).filter(StudySet.id == studyset_id, StudySet.user_id == current_user.id).first()
    if not studyset:
        raise HTTPException(status_code=404, detail="StudySet not found")
    return studyset

@router.delete("/{studyset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_studyset(
    studyset_id: uuid.UUID,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    studyset = db.query(StudySet).filter(StudySet.id == studyset_id, StudySet.user_id == current_user.id).first()
    if not studyset:
        raise HTTPException(status_code=404, detail="StudySet not found")
    
    db.delete(studyset)
    db.commit()
    return None
