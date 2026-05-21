import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# We use AsyncOpenAI to avoid blocking the event loop
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy_key"))

async def get_embedding(text: str) -> list[float]:
    """
    Get text embedding using OpenAI's API.
    """
    try:
        response = await client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Warning: Error getting embedding (using dummy embedding): {e}")
        # For testing without a real key, return a dummy vector of correct dimension
        return [0.0] * 1536

async def generate_answer(query: str, context: list[str]) -> str:
    """
    Generate an answer using LLM based on retrieved context.
    """
    try:
        context_str = "\n".join(context)
        prompt = f"Based on the following document context, answer the user's question.\n\nContext:\n{context_str}\n\nQuestion: {query}\nAnswer:"
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions strictly based on the provided document context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Warning: Error generating answer: {e}")
        return "I'm sorry, I encountered an error while generating the answer. Please check your API key or connection."
