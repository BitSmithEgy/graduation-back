from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, ChatSession, ChatMessage, SymptomTag
from schemas import ChatSessionOut, ChatSessionCreate
from utils import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
def create_chat_session(
    payload: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new chat session."""
    session = ChatSession(
        user_id=current_user.uuid,
        vendor_llm=payload.vendor_llm
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionOut])
def list_my_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List my chat sessions."""
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.uuid).all()

@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat session details including messages."""
    session = db.query(ChatSession).filter(
        ChatSession.chat_session_id == session_id,
        ChatSession.user_id == current_user.uuid
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session

@router.post("/sessions/{session_id}/messages", status_code=201)
def add_message_to_session(
    session_id: str,
    content: str,
    sender_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a message to a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.chat_session_id == session_id,
        ChatSession.user_id == current_user.uuid
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
        
    message = ChatMessage(
        chat_session_id=session_id,
        sender_role=sender_role,
        message_content=content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
