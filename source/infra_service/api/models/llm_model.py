from pydantic import BaseModel, Field


# ---- Single ----
class ChatRequest(BaseModel):
    ai_message: str = Field(
        default="You are a helpful assistant. Answer the user's question to the best of your ability.",
        min_length=1,
    )
    user_message: str = Field(
        default="What is the capital of France?",
        min_length=1,
    )
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)


class ChatResponse(BaseModel):
    response: str


# ---- Batch Item ----
class BatchChatItemResponse(BaseModel):
    response: str


# ---- Batch Request ----
class BatchChatRequest(BaseModel):
    messages: list[ChatRequest]


# ---- Batch Response ----
class BatchChatResponse(BaseModel):
    results: list[BatchChatItemResponse]
    count: int