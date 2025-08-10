from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class GenerationTask(BaseModel):
    """Модель задачи для генерации аудио"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generation_id: str  # ID записи в БД
    user_id: str
    text: str
    tokens_spent: int
    description: Optional[
        str] = "A female speaker delivers a slightly expressive and animated speech with a moderate speed and pitch. The recording is of very high quality, with the speaker's voice sounding clear and very close up."
    created_at: datetime = Field(default_factory=datetime.now)

    def json(self) -> str:
        """Serialize to JSON string"""
        return self.model_dump_json()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }