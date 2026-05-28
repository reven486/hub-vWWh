from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
import os

MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "document_collection"
DIMENSION = 1536  # Default OpenAI embedding dimension

def init_milvus():
    try:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        print("Connected to Milvus.")
        
        if not utility.has_collection(COLLECTION_NAME):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="doc_id", dtype=DataType.INT64),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION)
            ]
            schema = CollectionSchema(fields, "Document chunks collection")
            collection = Collection(COLLECTION_NAME, schema)
            
            # Create index
            index_params = {
                "metric_type": "L2",
                "index_type": "HNSW",
                "params": {"M": 8, "efConstruction": 64}
            }
            collection.create_index("embedding", index_params)
            print(f"Collection {COLLECTION_NAME} created.")
        else:
            print(f"Collection {COLLECTION_NAME} already exists.")
            
    except Exception as e:
        print(f"Warning: Failed to connect to Milvus. Is it running? Error: {e}")

def insert_chunks(doc_id: int, chunks: list[str], embeddings: list[list[float]]):
    try:
        collection = Collection(COLLECTION_NAME)
        doc_ids = [doc_id] * len(chunks)
        entities = [
            doc_ids,
            chunks,
            embeddings
        ]
        collection.insert(entities)
        collection.flush()
        print(f"Inserted {len(chunks)} chunks for doc_id {doc_id} into Milvus.")
    except Exception as e:
        print(f"Error inserting chunks into Milvus: {e}")
        raise e

def search_chunks(query_embedding: list[float], doc_id: int = None, limit: int = 3):
    try:
        collection = Collection(COLLECTION_NAME)
        collection.load()
        
        search_params = {
            "metric_type": "L2",
            "params": {"ef": 64}
        }
        
        expr = f"doc_id == {doc_id}" if doc_id else None
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["text", "doc_id"]
        )
        
        retrieved_texts = []
        for hits in results:
            for hit in hits:
                retrieved_texts.append(hit.entity.get("text"))
                
        return retrieved_texts
    except Exception as e:
        print(f"Error searching chunks in Milvus: {e}")
        return []
