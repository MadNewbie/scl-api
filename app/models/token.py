from ..database import Base
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    secret = Column(String, nullable=False)
    token = Column(String,nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())