from pydantic import BaseModel, Field
from typing import List, Any
from datetime import datetime
import pytz
from bson import ObjectId
from enum import Enum


class Stage(str, Enum):
    FIRST_GENERATION = "first_generation"
    MODIFY = "modify"
    END = "end"


class Role(str, Enum):
    User = "User"
    Assistant = "Assistant"
    ReasoningStep = "ReasoningStep"