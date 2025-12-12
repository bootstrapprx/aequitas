"""
Embedding Service for Semantic Search

Provides text embedding generation for semantic matching of accounts.
Uses sentence-transformers for generating embeddings that can be stored
in PostgreSQL using pgvector.

UPDATED: 2025-12-11
- Initial implementation for pgvector integration
- Support for both master accounts and company accounts
"""

from typing import List, Optional, Dict, Any
import numpy as np
from functools import lru_cache

# Optional imports - gracefully handle if not installed
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None


class EmbeddingService:
    """
    Service for generating text embeddings for semantic search.

    Uses sentence-transformers to generate embeddings that can be:
    1. Stored in PostgreSQL with pgvector extension
    2. Used for semantic similarity search
    3. Cached for performance

    Model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    """

    # Default model - lightweight and fast
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding service.

        Args:
            model_name: Name of sentence-transformer model (default: all-MiniLM-L6-v2)

        Raises:
            RuntimeError: If sentence-transformers not installed
        """
        if not EMBEDDINGS_AVAILABLE:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name or self.DEFAULT_MODEL
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the model to avoid loading on import."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.EMBEDDING_DIMENSION

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Replace empty texts with spaces to avoid errors
        texts_cleaned = [t if t and t.strip() else " " for t in texts]

        embeddings = self.model.encode(texts_cleaned, convert_to_numpy=True)
        return embeddings.tolist()

    def generate_account_embedding(self, account_data: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for an account by combining relevant fields.

        Combines:
        - Account description
        - Long description (if available)
        - Tags (if available)
        - Category (if available)

        Args:
            account_data: Dictionary with account fields

        Returns:
            Embedding vector
        """
        text_parts = []

        # Add description (required)
        if account_data.get("description"):
            text_parts.append(account_data["description"])

        # Add long description (optional)
        if account_data.get("long_description"):
            text_parts.append(account_data["long_description"])

        # Add tags (optional)
        if account_data.get("tags") and isinstance(account_data["tags"], list):
            text_parts.extend(account_data["tags"])

        # Add category (optional)
        if account_data.get("category"):
            text_parts.append(account_data["category"])

        # Combine all parts into a single text
        combined_text = " ".join(text_parts)

        return self.generate_embedding(combined_text)

    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between -1 and 1 (higher is more similar)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Handle zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    @staticmethod
    def is_available() -> bool:
        """Check if embeddings are available (dependencies installed)."""
        return EMBEDDINGS_AVAILABLE


# Singleton instance for reuse
_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get singleton instance of EmbeddingService.

    Returns:
        EmbeddingService instance

    Raises:
        RuntimeError: If sentence-transformers not installed
    """
    global _embedding_service_instance

    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()

    return _embedding_service_instance


# Convenience functions
def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text (convenience function)."""
    return get_embedding_service().generate_embedding(text)


def generate_account_embedding(account_data: Dict[str, Any]) -> List[float]:
    """Generate embedding for account (convenience function)."""
    return get_embedding_service().generate_account_embedding(account_data)


def is_embeddings_available() -> bool:
    """Check if embeddings are available."""
    return EmbeddingService.is_available()
