import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from app.core.config import get_settings


async def get_producer() -> AIOKafkaProducer:
    settings = get_settings()
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    await producer.start()
    return producer


async def send_parse_task(doc_id: str, kb_id: str):
    settings = get_settings()
    producer = await get_producer()
    try:
        await producer.send_and_wait(
            settings.kafka.parse_topic,
            {"doc_id": doc_id, "kb_id": kb_id},
        )
    finally:
        await producer.stop()


async def get_consumer() -> AIOKafkaConsumer:
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        settings.kafka.parse_topic,
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=settings.kafka.consumer_group,
        auto_offset_reset=settings.kafka.auto_offset_reset,
        value_deserializer=lambda v: json.loads(v.decode()),
        enable_auto_commit=False,
    )
    await consumer.start()
    return consumer
