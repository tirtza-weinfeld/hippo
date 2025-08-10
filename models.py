from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from db import Base

class Word(Base):
    __tablename__ = "words"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    word: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    definition: Mapped[str] = mapped_column(Text)
    example: Mapped[str | None] = mapped_column(Text, nullable=True)
