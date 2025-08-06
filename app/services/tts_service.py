from fastapi import Depends

from database.dependency import get_db
from database.models import GenerationHistory
from database.schema import CreateGenerationSchema, GenerationHistorySchema, CreateTransactionSchema
from sqlalchemy.orm import Session
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf
import uuid

from services.transaction_service import process_transaction, create_transaction

device = "cuda:0" if torch.cuda.is_available() else "cpu"

model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler-tts-mini-multilingual-v1.1").to(device)
tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-multilingual-v1.1")
description_tokenizer = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)


def count_tokens(text: str) -> int:
    """Count tokens for input text"""
    tokens = tokenizer(text, return_tensors="pt")
    return tokens.input_ids.shape[1]


def create_prediction(user_id: uuid.UUID, tokens_spent: int, generation_data: CreateGenerationSchema,
                      db: Session = Depends(get_db)) -> GenerationHistorySchema:
    transaction_schema = CreateTransactionSchema(user_id=user_id, transaction_type='DEBIT', amount=tokens_spent)
    created_transaction_schema = create_transaction(transaction_schema, db)
    process_transaction(transaction_id=created_transaction_schema.id, db=db)
    generation_id = uuid.uuid4()
    generate(generation_data.text, generation_id=generation_id)
    db_generation_history = GenerationHistory(id=generation_id, s3_link=f'output/{generation_id}.wav',
                                              text=generation_data.text, user_id=user_id, tokens_spent=tokens_spent)
    db.add(db_generation_history)
    db.commit()
    db.refresh(db_generation_history)
    generation_schema = GenerationHistorySchema(id=db_generation_history.id, user_id=user_id, tokens_spent=tokens_spent,
                                                s3_link=db_generation_history.s3_link, text=db_generation_history.text,
                                                timestamp=db_generation_history.timestamp)
    return generation_schema


def generate(text: str, generation_id: uuid.UUID):
    description = "A female speaker delivers a slightly expressive and animated speech with a moderate speed and pitch. The recording is of very high quality, with the speaker's voice sounding clear and very close up."

    input_ids = description_tokenizer(description, return_tensors="pt").input_ids.to(device)
    prompt_input_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)

    generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
    audio_arr = generation.cpu().numpy().squeeze()
    sf.write(f"output/{generation_id}.wav", audio_arr, model.config.sampling_rate)
