from pydantic import BaseModel, Field
from typing import Literal


# ---- Single Message ----
class ChatMessage(BaseModel):
    ai_message: str = Field(default="You are a helpful assistant. Answer the user's question to the best of your ability.", min_length=1)
    user_message: str = Field(default="What is the capital of France?", min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)