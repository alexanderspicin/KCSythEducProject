# ml_worker/publisher.py
from os import getenv
import time
import json
import pika
from pika.exceptions import AMQPConnectionError, StreamLostError
import threading

from logger_config import setup_logging, get_logger

setup_logging(log_level="INFO", log_to_file=True)
logger = get_logger(__name__)


class TaskPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self._lock = threading.Lock()

    def ensure_connection(self):
        """Ensure connection is established"""
        with self._lock:
            if not self.connection or self.connection.is_closed:
                self.connect()

    def connect(self):
        """Connect to RabbitMQ"""
        max_retries = 5
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                logger.info(f"Publisher connecting to RabbitMQ (attempt {attempt + 1})")

                credentials = pika.PlainCredentials(
                    getenv('RABBITMQ_DEFAULT_USER', 'guest'),
                    getenv('RABBITMQ_DEFAULT_PASS', 'guest')
                )

                parameters = pika.ConnectionParameters(
                    host=getenv('RABBITMQ_HOST', 'rabbitmq'),
                    port=int(getenv('RABBITMQ_PORT', '5672')),
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                    connection_attempts=3,
                    retry_delay=2
                )

                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()

                # Declare exchange
                self.channel.exchange_declare(
                    exchange=getenv('EXCHANGE', 'ml_exchange'),
                    exchange_type='fanout',
                    durable=True
                )

                # Declare queue
                self.channel.queue_declare(
                    queue=getenv('TASK_QUEUE', 'ml_tasks'),
                    durable=True
                )

                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=getenv('EXCHANGE', 'ml_exchange'),
                    queue=getenv('TASK_QUEUE', 'ml_tasks')
                )

                logger.info("Publisher connected to RabbitMQ")
                return True

            except Exception as e:
                logger.error(f"Publisher connection failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return False

    def publish_task(self, task):
        """Publish task to queue"""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                self.ensure_connection()

                # Serialize task to JSON
                if hasattr(task, 'json'):
                    body = task.json()
                elif hasattr(task, 'model_dump_json'):
                    body = task.model_dump_json()
                elif isinstance(task, dict):
                    body = json.dumps(task)
                else:
                    body = str(task)

                # Publish to exchange
                self.channel.basic_publish(
                    exchange=getenv('EXCHANGE', 'ml_exchange'),
                    routing_key='',
                    body=body,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent
                        content_type='application/json'
                    )
                )

                logger.info(f"Task published successfully")
                return True

            except (StreamLostError, AMQPConnectionError) as e:
                logger.error(f"Publish attempt {attempt + 1} failed: {e}")
                self.connection = None
                if attempt < max_attempts - 1:
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Failed to publish task: {e}")
                return False

        return False

    def close(self):
        """Close connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("Publisher connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
