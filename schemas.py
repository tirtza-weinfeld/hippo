from pydantic import BaseModel, Field, ConfigDict

class WordCreate(BaseModel):
    word: str = Field(min_length=1, max_length=64)
    definition: str
    example: str | None = None

class WordOut(WordCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class WordUpdate(BaseModel):
    word: str | None = Field(default=None, min_length=1, max_length=64)
    definition: str | None = None
    # Provide None explicitly to clear the example
    example: str | None = None
