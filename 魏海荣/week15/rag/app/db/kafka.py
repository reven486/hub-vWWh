from typing import Optional, Callable
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from app.core.config import config


class KafkaClient:
    _instance: Optional["KafkaClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_producer()
        return cls._instance

    def _init_producer(self):
        kafka_config = config.kafka
        self._bootstrap_servers = kafka_config.get("bootstrap_servers", "localhost:9092")
        self._producer = KafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            value_serializer=lambda v: str(v).encode("utf-8")
        )

    def send_parse_task(self, document_id: str):
        topic = config.kafka.get("topic_parse", "document_parse")
        self._producer.send(topic, value=document_id)
        self._producer.flush()

    def create_consumer(self, topic: Optional[str] = None, group_id: Optional[str] = None) -> KafkaConsumer:
        kafka_config = config.kafka
        return KafkaConsumer(
            topic or kafka_config.get("topic_parse", "document_parse"),
            bootstrap_servers=self._bootstrap_servers,
            group_id=group_id or kafka_config.get("consumer_group", "document_parser"),
            value_deserializer=lambda v: v.decode("utf-8"),
            auto_offset_reset="earliest"
        )


kafka_client = KafkaClient()
