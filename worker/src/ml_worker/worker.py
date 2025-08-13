import os
import sys
import time
import json
import pika
import torch
import soundfile as sf
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer

    ML_MODELS_AVAILABLE = True
except ImportError:
    logger.warning("ML models not available. Running in test mode.")
    ML_MODELS_AVAILABLE = False

# Добавляем путь для импорта моделей БД
sys.path.append('/app')
from database.models import GenerationHistory
from database.enums import Status


class MLWorker:
    def __init__(self, worker_id=None):
        self.worker_id = worker_id or os.getenv('WORKER_ID', 'worker-default')
        self.connection = None
        self.channel = None

        # Инициализация ML моделей
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        self.model = None
        self.tokenizer = None
        self.description_tokenizer = None

        if ML_MODELS_AVAILABLE:
            self._load_ml_models()

        # Настройка подключения к БД
        self.db_engine = self._create_db_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.db_engine)

    def _load_ml_models(self):
        """Загрузка ML моделей"""
        try:
            logger.info("Loading ML models...")
            self.model = ParlerTTSForConditionalGeneration.from_pretrained(
                "parler-tts/parler-tts-mini-multilingual-v1.1"
            ).to(self.device)

            self.tokenizer = AutoTokenizer.from_pretrained(
                "parler-tts/parler-tts-mini-multilingual-v1.1"
            )

            self.description_tokenizer = AutoTokenizer.from_pretrained(
                self.model.config.text_encoder._name_or_path
            )
            logger.info("ML models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            raise

    def _create_db_engine(self):
        """Создание подключения к БД"""
        db_user = os.getenv('POSTGRES_USER', 'myuser')
        db_pass = os.getenv('POSTGRES_PASSWORD', 'mypassword')
        db_host = os.getenv('POSTGRES_HOST', 'db')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'mydatabase')

        database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(database_url)
        logger.info(f"Database engine created for {db_name}")
        return engine

    def connect(self):
        """Connect to RabbitMQ"""
        max_retries = 10
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                logger.info(f"Worker {self.worker_id} attempting to connect (attempt {attempt + 1})")

                credentials = pika.PlainCredentials(
                    os.getenv('RABBITMQ_DEFAULT_USER', 'guest'),
                    os.getenv('RABBITMQ_DEFAULT_PASS', 'guest')
                )

                parameters = pika.ConnectionParameters(
                    host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
                    port=int(os.getenv('RABBITMQ_PORT', '5672')),
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )

                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()

                # Declare exchange
                self.channel.exchange_declare(
                    exchange=os.getenv('EXCHANGE', 'ml_exchange'),
                    exchange_type='fanout',
                    durable=True
                )

                # Declare queue
                self.channel.queue_declare(
                    queue=os.getenv('TASK_QUEUE', 'ml_tasks'),
                    durable=True
                )

                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=os.getenv('EXCHANGE', 'ml_exchange'),
                    queue=os.getenv('TASK_QUEUE', 'ml_tasks')
                )

                # Set QoS
                self.channel.basic_qos(prefetch_count=1)

                logger.info(f"Worker {self.worker_id} connected to RabbitMQ")
                return

            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

    def generate_audio(self, text: str, description: str, generation_id: str):
        """Генерация аудио с использованием ML модели"""
        if not ML_MODELS_AVAILABLE:
            # Test mode - создаем пустой файл
            logger.info(f"Test mode: creating dummy audio for {generation_id}")
            output_path = f"output/{generation_id}.wav"

            # Создаем тестовый WAV файл
            import numpy as np
            sample_rate = 22050
            duration = 2
            t = np.linspace(0, duration, sample_rate * duration)
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz тон
            sf.write(output_path, audio, sample_rate)

            return output_path

        try:
            logger.info(f"Starting audio generation for {generation_id}")

            # Токенизация
            input_ids = self.description_tokenizer(description, return_tensors="pt").input_ids.to(self.device)
            prompt_input_ids = self.tokenizer(text, return_tensors="pt").input_ids.to(self.device)

            # Генерация
            generation = self.model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
            audio_arr = generation.cpu().numpy().squeeze()

            # Создаем директорию если не существует
            os.makedirs("output", exist_ok=True)

            # Сохранение файла
            output_path = f"output/{generation_id}.wav"
            sf.write(output_path, audio_arr, self.model.config.sampling_rate)

            logger.info(f"Audio saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise

    def update_generation_status(self, generation_id: str, status: Status, s3_link: str = None):
        """Обновление статуса генерации в БД"""
        db = self.SessionLocal()
        try:
            generation = db.query(GenerationHistory).filter(
                GenerationHistory.id == generation_id
            ).first()

            if generation:
                generation.status = status
                if s3_link:
                    generation.s3_link = s3_link
                db.commit()
                logger.info(f"Updated generation {generation_id} status to {status}")
            else:
                logger.error(f"Generation {generation_id} not found in database")

        except Exception as e:
            logger.error(f"Failed to update generation status: {e}")
            db.rollback()
        finally:
            db.close()

    def process_message(self, ch, method, properties, body):
        """Process received message"""
        generation_id = None
        try:
            logger.info(f"Worker {self.worker_id} received task")

            # Parse task
            task_data = json.loads(body)
            logger.info(f"Processing task: {task_data}")

            generation_id = task_data.get('generation_id')
            text = task_data.get('text')
            description = task_data.get('description',
                                        "A female speaker delivers a slightly expressive and animated speech with a moderate speed and pitch. The recording is of very high quality, with the speaker's voice sounding clear and very close up.")

            if not generation_id or not text:
                logger.error(f"Invalid task data: generation_id={generation_id}, text={text}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            self.update_generation_status(generation_id, Status.PROCESSING)

            output_path = self.generate_audio(text, description, generation_id)

            self.update_generation_status(generation_id, Status.DONE, output_path)

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Task {generation_id} completed by {self.worker_id}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task JSON: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Error processing task: {e}")

            # Обновляем статус на FAILED
            if generation_id:
                self.update_generation_status(generation_id, Status.FAILED)

            # Reject but don't requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self):
        """Start worker"""
        while True:
            try:
                if not self.connection or self.connection.is_closed:
                    self.connect()

                # Start consuming
                self.channel.basic_consume(
                    queue=os.getenv('TASK_QUEUE', 'ml_tasks'),
                    on_message_callback=self.process_message
                )

                logger.info(f"Worker {self.worker_id} waiting for tasks...")
                self.channel.start_consuming()

            except KeyboardInterrupt:
                logger.info("Shutting down worker...")
                self.stop()
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(5)

    def stop(self):
        """Stop worker"""
        try:
            if self.channel:
                self.channel.stop_consuming()
            if self.connection:
                self.connection.close()
            logger.info(f"Worker {self.worker_id} stopped")
        except Exception as e:
            logger.error(f"Error stopping worker: {e}")


if __name__ == "__main__":
    worker = MLWorker()
    worker.start()


