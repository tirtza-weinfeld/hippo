import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db import Base, engine, SessionLocal
from models import Word
from schemas import WordCreate, WordOut, WordUpdate

app = FastAPI(title="Hippo API")

# CORS for your site + local dev
origins = [o for o in os.getenv("ALLOWED_ORIGINS","").split(",") if o]
app.add_middleware(
    CORSMiddleware, allow_origins=origins or ["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# DB init (simple: create tables if missing)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.post("/words", response_model=WordOut, status_code=201)
def create_word(payload: WordCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Word).where(Word.word == payload.word)):
        raise HTTPException(status_code=409, detail="word already exists")
    row = Word(word=payload.word, definition=payload.definition, example=payload.example)
    db.add(row); db.commit(); db.refresh(row)
    return row

@app.get("/words", response_model=list[WordOut])
def list_words(db: Session = Depends(get_db)):
    return db.scalars(select(Word).order_by(Word.id.desc())).all()

@app.get("/words/random", response_model=WordOut)
def random_word(db: Session = Depends(get_db)):
    row = db.scalar(select(Word).order_by(func.random()).limit(1))
    if not row: raise HTTPException(status_code=404, detail="no words yet")
    return row

@app.delete("/words/{word_id}", status_code=204)
def delete_word(word_id: int, db: Session = Depends(get_db)):
    row = db.get(Word, word_id)
    if not row:
        raise HTTPException(status_code=404, detail="word not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)

@app.delete("/words/by-word/{word}", status_code=204)
def delete_word_by_word(word: str, db: Session = Depends(get_db)):
    row = db.scalar(select(Word).where(Word.word == word))
    if not row:
        raise HTTPException(status_code=404, detail="word not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)

@app.patch("/words/{word_id}", response_model=WordOut)
def update_word(word_id: int, payload: WordUpdate, db: Session = Depends(get_db)):
    row = db.get(Word, word_id)
    if not row:
        raise HTTPException(status_code=404, detail="word not found")

    # Enforce unique word if changing the word
    if payload.word is not None and payload.word != row.word:
        existing = db.scalar(select(Word).where(Word.word == payload.word))
        if existing:
            raise HTTPException(status_code=409, detail="word already exists")

    if payload.word is not None:
        row.word = payload.word
    if payload.definition is not None:
        row.definition = payload.definition
    # Allow explicit clearing of example when the client sends example=null
    if payload.example is not None or payload.model_fields_set.__contains__('example'):
        row.example = payload.example

    db.add(row)
    db.commit()
    db.refresh(row)
    return row
