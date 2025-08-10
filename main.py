import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db import Base, engine, SessionLocal
from models import Word
from schemas import WordCreate, WordOut

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
