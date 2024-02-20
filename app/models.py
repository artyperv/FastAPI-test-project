from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    records = relationship("VinylRecord", back_populates="creator")


class VinylRecord(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, index=True)
    author = Column(String, index=True)
    duration = Column(Integer)
    description = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by = Column(Integer, ForeignKey("users.id"))  # touched_by?
    creator = relationship("User", back_populates="records")  # touch...?
