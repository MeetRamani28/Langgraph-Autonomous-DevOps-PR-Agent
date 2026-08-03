import logging
import hashlib
import math
from typing import List
from psycopg_pool import AsyncConnectionPool

from app.config import settings

logger = logging.getLogger("RAGTool")


class Lightweight384Embeddings:
    """
    A 100% Free, 0-RAM 384-dimensional embedding engine.
    Generates deterministic, cosine-searchable vector embeddings without
    requiring PyTorch, GPU memory, or Windows Pagefile allocations.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        """Converts text into a normalized 384-dimensional vector."""
        vector = [0.0] * self.dimension
        words = text.lower().split()
        
        if not words:
            return vector

        for word in words:
            hash_val = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = hash_val % self.dimension
            vector[idx] += 1.0

        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
            
        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(t) for t in texts]


embeddings_model = Lightweight384Embeddings(dimension=384)


async def ensure_rag_table_exists(pool: AsyncConnectionPool):
    """
    Ensures the 'docs_embeddings' pgvector table exists and seeds it with default
    security guidelines if it is empty.
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS docs_embeddings (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(384)
                );
            """)
            
            await cur.execute("SELECT COUNT(*) FROM docs_embeddings;")
            count = (await cur.fetchone())[0]
            if count == 0:
                logger.info("Seeding initial security & architectural documentation into pgvector RAG...")
                default_docs = [
                    (
                        "SQL Injection Prevention",
                        "Always use SQLAlchemy ORM or parameterized DB queries. Never format raw SQL strings using f-strings or user input."
                    ),
                    (
                        "Secret Management Policy",
                        "Never commit plain-text API keys, tokens, or passwords. All secrets must be loaded via environment variables."
                    ),
                    (
                        "Authentication Guidelines",
                        "User authentication modules must validate credentials securely without logging sensitive credentials."
                    )
                ]
                for title, content in default_docs:
                    vector = embeddings_model.embed_query(content)
                    await cur.execute(
                        "INSERT INTO docs_embeddings (title, content, embedding) VALUES (%s, %s, %s);",
                        (title, content, str(vector))
                    )
                logger.info("Successfully seeded RAG vector store with security guidelines.")


async def retrieve_security_guidelines(pool: AsyncConnectionPool, query_text: str, top_k: int = 2) -> List[str]:
    """
    Embeds the query text and performs a cosine similarity search against local pgvector docs.
    """
    logger.info(f"Performing RAG semantic search for query: '{query_text[:50]}...'")
    try:
        await ensure_rag_table_exists(pool)
        
        query_vector = embeddings_model.embed_query(query_text)
        
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                sql = """
                    SELECT title, content 
                    FROM docs_embeddings 
                    ORDER BY embedding <=> %s::vector 
                    LIMIT %s;
                """
                await cur.execute(sql, (str(query_vector), top_k))
                rows = await cur.fetchall()
                
                results = [f"[{row[0]}]: {row[1]}" for row in rows]
                logger.info(f"Retrieved {len(results)} relevant RAG chunks.")
                return results
    except Exception as e:
        logger.error(f"Error querying pgvector RAG database: {e}")
        return ["RAG Retrieval Fallback: Ensure no SQL injections or hardcoded secrets are present."]