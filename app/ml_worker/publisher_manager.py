import threading
from ml_worker.publisher import TaskPublisher
from logger_config import get_logger

logger = get_logger(__name__)


class PublisherManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.publisher = None
        return cls._instance

    def get_publisher(self):
        """Get or create publisher instance"""
        if self.publisher is None:
            self.publisher = TaskPublisher()
        return self.publisher

    def reset_publisher(self):
        """Reset publisher connection"""
        if self.publisher:
            self.publisher.close()
            self.publisher = None


# Глобальный менеджер
publisher_manager = PublisherManager()