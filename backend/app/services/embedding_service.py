"""Embedding service for semantic search using MedCPT"""

import logging
from typing import List, Optional
from functools import lru_cache
import numpy as np

logger = logging.getLogger(__name__)

# Lazy import to avoid loading model on module import
_model = None


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Lazy-load and cache the MedCPT embedding model.

    Using sentence-transformers with MedCPT model optimized for
    biomedical and clinical text embeddings.

    Returns 768-dimensional embeddings.
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading MedCPT embedding model...")

            # Try MedCPT first, fall back to biomedical model if unavailable
            try:
                _model = SentenceTransformer('ncbi/MedCPT-Query-Encoder')
                logger.info("✓ Loaded MedCPT-Query-Encoder model")
            except Exception as e:
                logger.warning(f"Could not load MedCPT model ({e}), falling back to all-MiniLM-L6-v2")
                # Fallback to a smaller general-purpose model for development
                # Note: This is 384-dim, not 768-dim. For production, use MedCPT
                _model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.warning("⚠ Using fallback model with 384 dimensions instead of 768")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Could not initialize embedding model: {e}")

    return _model


def generate_embedding(text: str, normalize: bool = True) -> List[float]:
    """
    Generate embedding vector for a single text.

    Args:
        text: Input text to embed
        normalize: Whether to L2-normalize the embedding (recommended for cosine similarity)

    Returns:
        List of float values representing the embedding (768-dim for MedCPT)
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    model = get_embedding_model()

    # Generate embedding
    embedding = model.encode(
        text,
        normalize_embeddings=normalize,
        show_progress_bar=False
    )

    # Convert numpy array to list for JSON serialization
    return embedding.tolist()


def generate_embeddings_batch(
    texts: List[str],
    normalize: bool = True,
    batch_size: int = 32
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently.

    Args:
        texts: List of input texts to embed
        normalize: Whether to L2-normalize the embeddings
        batch_size: Batch size for processing (default 32)

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    # Filter out empty texts
    valid_texts = [t for t in texts if t and t.strip()]
    if not valid_texts:
        raise ValueError("No valid texts to embed")

    model = get_embedding_model()

    # Generate embeddings in batches
    embeddings = model.encode(
        valid_texts,
        normalize_embeddings=normalize,
        batch_size=batch_size,
        show_progress_bar=len(valid_texts) > 100
    )

    # Convert to list of lists
    return [emb.tolist() for emb in embeddings]


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Compute cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Similarity score between -1 and 1 (1 = identical, 0 = orthogonal, -1 = opposite)
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    # Cosine similarity
    similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    return float(similarity)


def find_most_similar(
    query_embedding: List[float],
    candidate_embeddings: List[List[float]],
    top_k: int = 10
) -> List[tuple[int, float]]:
    """
    Find the most similar embeddings to a query embedding.

    Args:
        query_embedding: Query embedding vector
        candidate_embeddings: List of candidate embedding vectors
        top_k: Number of top results to return

    Returns:
        List of tuples (index, similarity_score) sorted by similarity (highest first)
    """
    if not candidate_embeddings:
        return []

    query_vec = np.array(query_embedding)
    candidate_matrix = np.array(candidate_embeddings)

    # Compute cosine similarities
    similarities = np.dot(candidate_matrix, query_vec) / (
        np.linalg.norm(candidate_matrix, axis=1) * np.linalg.norm(query_vec)
    )

    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]

    # Return (index, score) pairs
    return [(int(idx), float(similarities[idx])) for idx in top_indices]


# Warmup function to preload model on startup
def warmup_model():
    """
    Warmup the embedding model by running a test encoding.
    This should be called during application startup to avoid
    latency on first request.
    """
    try:
        logger.info("Warming up embedding model...")
        model = get_embedding_model()
        # Run a test encoding
        test_embedding = generate_embedding("test warmup query")
        logger.info(f"✓ Model warmed up successfully (embedding dim: {len(test_embedding)})")
        return True
    except Exception as e:
        logger.error(f"Failed to warmup model: {e}")
        return False
