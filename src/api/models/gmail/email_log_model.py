from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from src.database import Base

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    thread_id = Column(String)
    subject = Column(String)
    sender = Column(String)
    ai_response = Column(Text)
    success = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    response_time = Column(Integer)  # Response time in milliseconds