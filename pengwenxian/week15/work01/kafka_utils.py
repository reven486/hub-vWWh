import json
import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "document_processing"

producer = None

async def init_kafka_producer():
    global producer
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        print("Kafka producer started.")
    except Exception as e:
        print(f"Warning: Failed to start Kafka producer. Is Kafka running? Error: {e}")

async def close_kafka_producer():
    global producer
    if producer:
        await producer.stop()

async def send_document_message(doc_id: int, file_path: str):
    global producer
    if not producer:
        print("Kafka producer not initialized. Skipping sending message.")
        return
        
    message = {
        "doc_id": doc_id,
        "file_path": file_path
    }
    await producer.send_and_wait(KAFKA_TOPIC, message)
    print(f"Message sent to Kafka for doc_id: {doc_id}")

async def consume_messages():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="doc_processor_group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest'
    )
    
    try:
        await consumer.start()
        print("Kafka consumer started.")
    except Exception as e:
        print(f"Warning: Failed to start Kafka consumer. Error: {e}")
        return

    try:
        async for msg in consumer:
            data = msg.value
            doc_id = data.get("doc_id")
            file_path = data.get("file_path")
            
            print(f"Received message from Kafka for doc_id: {doc_id}")
            
            from processor import process_document
            # Run processing in background
            asyncio.create_task(process_document(doc_id, file_path))
    finally:
        await consumer.stop()
