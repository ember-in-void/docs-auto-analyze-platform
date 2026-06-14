# ==========================================
# package-level documentation
# ==========================================
"""
Package embedder provides ruBERT embedding generation.
It implements sliding window mean-pooling for long documents
and supports automatic CUDA (GPU) acceleration if available.
"""

import logging
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger("nlp-service.embedder")

# ==========================================
# Constants
# ==========================================
MODEL_NAME = "cointegrated/rubert-tiny2"

RISK_ANCHORS = ["ошибка", "сбой", "задержка", "риск", "убыток", "уязвимость", "проблема", "угроза", "взлом", "утечка"]
PROFIT_ANCHORS = ["прибыль", "эффективность", "успех", "рост", "монетизация", "оптимизация", "выгода", "рентабельность", "окупаемость"]
TECH_ANCHORS = ["архитектура", "разработка", "база данных", "интеграция", "микросервис", "технологический стек"]

# ==========================================
# Model Loading & Initialization
# ==========================================
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f"Using device for ruBERT: {device}")

try:
    logger.info(f"Loading tokenizer and model: {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME).to(device)
    logger.info("✓ ruBERT models loaded successfully")
except Exception as e:
    logger.error(f"Failed to load ruBERT models: {e}")
    tokenizer = None
    model = None

# ==========================================
# Embedding Caches
# ==========================================
risk_emb_cache = None
profit_emb_cache = None
tech_emb_cache = None

# ==========================================
# Service Functions
# ==========================================

def get_embedding(text: str) -> np.ndarray:
    """
    Generate a normalized embedding vector for the given text.
    Implements sliding window mean-pooling if text exceeds ruBERT's max length of 512 tokens.
    
    Args:
        text: Input string to embed.
        
    Returns:
        1D numpy array representing the normalized embedding vector of size 312.
    """
    if model is None or tokenizer is None or not text.strip():
        return np.zeros(312, dtype=np.float32)

    try:
        # Tokenize without special tokens to determine total size
        tokens = tokenizer(text, add_special_tokens=False, return_tensors='pt')
        input_ids = tokens['input_ids'][0]
        total_tokens = len(input_ids)

        if total_tokens <= 510:
            # Fit inside a single window (512 including CLS/SEP)
            t = tokenizer(text, padding=True, truncation=True, return_tensors='pt', max_length=512)
            with torch.no_grad():
                model_output = model(**{k: v.to(device) for k, v in t.items()})
            embeddings = model_output.last_hidden_state[:, 0, :]
            embeddings = torch.nn.functional.normalize(embeddings)
            return embeddings[0].cpu().numpy()

        # Sliding window chunking
        chunk_size = 384
        overlap = 64
        step = chunk_size - overlap

        chunk_embs = []
        for i in range(0, total_tokens, step):
            chunk_ids = input_ids[i:i + chunk_size]
            if len(chunk_ids) == 0:
                break

            # Add CLS and SEP tokens properly
            chunk_ids_list = chunk_ids.tolist()
            input_ids_with_special = tokenizer.build_inputs_with_special_tokens(chunk_ids_list)
            chunk_tensor = torch.tensor([input_ids_with_special]).to(device)
            attention_mask = torch.ones_like(chunk_tensor).to(device)

            with torch.no_grad():
                model_output = model(input_ids=chunk_tensor, attention_mask=attention_mask)
            
            # Extract CLS token embedding (index 0) and normalize it
            cls_emb = model_output.last_hidden_state[:, 0, :]
            cls_emb = torch.nn.functional.normalize(cls_emb)
            chunk_embs.append(cls_emb[0].cpu().numpy())

        if not chunk_embs:
            return np.zeros(312, dtype=np.float32)

        # Mean pool of all chunk CLS embeddings
        mean_emb = np.mean(chunk_embs, axis=0)
        norm = np.linalg.norm(mean_emb)
        if norm > 0:
            mean_emb = mean_emb / norm
        return mean_emb
    except Exception as e:
        logger.error(f"Error in get_embedding: {e}")
        return np.zeros(312, dtype=np.float32)


def precompute_anchors() -> None:
    """Precompute and cache mean embeddings for risk, profit and tech anchor word lists."""
    global risk_emb_cache, profit_emb_cache, tech_emb_cache
    if model is None or tokenizer is None:
        logger.warning("Models not loaded. Cannot precompute anchors.")
        return

    try:
        logger.info("Precomputing anchor embeddings...")
        risk_embs = [get_embedding(w) for w in RISK_ANCHORS]
        profit_embs = [get_embedding(w) for w in PROFIT_ANCHORS]
        tech_embs = [get_embedding(w) for w in TECH_ANCHORS]

        risk_emb_cache = np.mean(risk_embs, axis=0).reshape(1, -1)
        profit_emb_cache = np.mean(profit_embs, axis=0).reshape(1, -1)
        tech_emb_cache = np.mean(tech_embs, axis=0).reshape(1, -1)
        logger.info("✓ Anchor embeddings precomputed successfully")
    except Exception as e:
        logger.error(f"Failed to precompute anchor embeddings: {e}")

# Automatically precompute anchors if model loading succeeded
if model is not None:
    precompute_anchors()
