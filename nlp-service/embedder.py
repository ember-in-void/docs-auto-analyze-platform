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

        input_ids_list = []
        for i in range(0, total_tokens, step):
            chunk_ids = input_ids[i:i + chunk_size]
            if len(chunk_ids) == 0:
                break
            
            chunk_ids_list = chunk_ids.tolist()
            input_ids_with_special = tokenizer.build_inputs_with_special_tokens(chunk_ids_list)
            input_ids_list.append(input_ids_with_special)

        if not input_ids_list:
            return np.zeros(312, dtype=np.float32)

        # Pad all lists in input_ids_list to the maximum length among them
        max_len = max(len(ids) for ids in input_ids_list)
        padded_input_ids = []
        padded_attention_masks = []
        
        pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0

        for ids in input_ids_list:
            padding_len = max_len - len(ids)
            padded_ids = ids + [pad_token_id] * padding_len
            padded_mask = [1] * len(ids) + [0] * padding_len
            padded_input_ids.append(padded_ids)
            padded_attention_masks.append(padded_mask)

        # Create tensors and move to device
        batch_input_ids = torch.tensor(padded_input_ids).to(device)
        batch_attention_mask = torch.tensor(padded_attention_masks).to(device)

        with torch.no_grad():
            model_output = model(input_ids=batch_input_ids, attention_mask=batch_attention_mask)

        # Extract normalized CLS token embeddings (index 0) for all chunks in the batch
        cls_embeddings = model_output.last_hidden_state[:, 0, :]
        cls_embeddings = torch.nn.functional.normalize(cls_embeddings)
        
        # Mean pool the embeddings across chunks and re-normalize
        mean_emb_tensor = torch.mean(cls_embeddings, dim=0)
        mean_emb_tensor = torch.nn.functional.normalize(mean_emb_tensor, dim=0)
        
        return mean_emb_tensor.cpu().numpy()
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
