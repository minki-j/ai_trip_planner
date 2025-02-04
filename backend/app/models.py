from pydantic import BaseModel, Field
from typing import List, Any
from datetime import datetime
import pytz
from bson import ObjectId
from enum import Enum

class ResponseType(str, Enum):
    CORRECTION = "correction"
    VOCABULARY = "vocabulary"
    BREAKDOWN = "breakdown"
    GENERAL = "general"

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: Any) -> Any:
        field_schema.update(type="string")
        return field_schema

class CorrectionItem(BaseModel):
    correction: str
    explanation: str

class ExtraQuestion(BaseModel):
    question: str
    answer: str

class BaseResponseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    type: ResponseType
    userId: str
    input: str
    extraQuestions: List[ExtraQuestion] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('US/Eastern')), frozen=True)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class Correction(BaseResponseModel):
    type: ResponseType = ResponseType.CORRECTION
    correctedText: str = Field(default="")
    corrections: List[CorrectionItem] = Field(default_factory=list)

class Vocabulary(BaseResponseModel):
    type: ResponseType = ResponseType.VOCABULARY
    definition: str = Field(default="")
    translated_vocabulary: str = Field(default="")
    examples: List[str] = Field(default_factory=list)

class Breakdown(BaseResponseModel):
    type: ResponseType = ResponseType.BREAKDOWN
    paraphrase: str = Field(default="")
    breakdown: str = Field(default="")

class General(BaseResponseModel):
    type: ResponseType = ResponseType.GENERAL
    answer: str = Field(default="")
