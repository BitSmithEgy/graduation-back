from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from database import get_db
from models import User, ChatSession, ChatMessage, SymptomTag
from schemas import ChatSessionOut, ChatSessionCreate
from utils import get_current_user
from pydantic import BaseModel
import requests

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    chat_id: str

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

@router.post("/agent", response_model=Dict[str, str])
def chat_agent(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    url = "https://joelolo.app.n8n.cloud/webhook/f91bbaec-770a-4977-a774-85a1efd864dd"
    
    payload = {
        "message": data.message,
        "chat_id": data.chat_id
    }
    
    try:
        response = requests.post(url, json=payload)
        external = response.json()
        
        return {
            "status": "sent",
            "response": external.get("Response", "")
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }