# ==========================================
# NLP Service — Python/FastAPI
# ==========================================
import os
import re
import logging
import numpy as np
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("nlp-service")

app = FastAPI(title="NLP Analysis Service")

# --- Models Initialization ---
try:
    logger.info("Loading NLP models (this may take a while)...")
    MODEL_NAME = "cointegrated/rubert-tiny2"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    logger.info("✓ Models loaded successfully")
except Exception as e:
    logger.error(f"Error loading models: {e}")
    tokenizer = None
    model = None

# ==========================================
# Schemas
# ==========================================

class AnalysisRequest(BaseModel):
    text: str

class Entity(BaseModel):
    text: str
    type: str
    start: int
    end: int

class AnalysisResult(BaseModel):
    profitability: float
    risk: float
    relevance: float
    keywords: List[str]
    summary: str
    entities: List[Entity]

# ==========================================
# Helper Functions
# ==========================================

def get_embedding(text: str) -> np.ndarray:
    """Get sentence embedding using rubert-tiny2"""
    if model is None or tokenizer is None:
        return np.zeros((1, 312)) # fallback
    
    t = tokenizer(text, padding=True, truncation=True, return_tensors='pt', max_length=512)
    with torch.no_grad():
        model_output = model(**{k: v.to(model.device) for k, v in t.items()})
    embeddings = model_output.last_hidden_state[:, 0, :]
    embeddings = torch.nn.functional.normalize(embeddings)
    return embeddings[0].cpu().numpy()

def heuristic_ner(text: str) -> List[Dict[str, Any]]:
    """Simple dictionary and regex-based NER for MVP."""
    entities = []
    
    # --- Technology ---
    techs = ["React", "Golang", "PostgreSQL", "Docker", "Kubernetes", "Vue", "Python", "FastAPI", "Salesforce", "AWS", "Azure", "GCP", "Redis"]
    for t in techs:
        for match in re.finditer(r'\b' + re.escape(t.lower()) + r'\b', text.lower()):
            start = match.start()
            end = match.end()
            # use original case from text
            entities.append({"text": text[start:end], "type": "Technology", "start": start, "end": end})

    # --- Budget ---
    # Matches patterns like "2.5 млн рублей", "500 тыс. руб", "1000000 руб"
    budget_pattern = re.compile(r'\b(\d+(?:\.\d+)?\s*(?:млн|тыс\.|миллионов|тысяч)?\s*(?:рублей|руб\.|руб|usd|долларов))\b', re.IGNORECASE)
    for match in budget_pattern.finditer(text):
        entities.append({"text": match.group(0), "type": "Budget", "start": match.start(), "end": match.end()})

    # --- Deadline ---
    deadline_pattern = re.compile(r'\b(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})\b', re.IGNORECASE)
    for match in deadline_pattern.finditer(text):
        entities.append({"text": match.group(0), "type": "Deadline", "start": match.start(), "end": match.end()})

    # --- Organization ---
    org_pattern = re.compile(r'\b(?:ООО|АО|ЗАО|ПАО)\s+"[^"]+"', re.IGNORECASE)
    for match in org_pattern.finditer(text):
        entities.append({"text": match.group(0), "type": "Organization", "start": match.start(), "end": match.end()})

    # Remove overlaps by prioritizing longer entities
    entities.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
    final_entities = []
    last_end = -1
    for e in entities:
        if e["start"] >= last_end:
            final_entities.append(e)
            last_end = e["end"]

    return final_entities

def extractive_summary(text: str, n_sentences: int = 3) -> str:
    """Generate extractive summary using embeddings."""
    # Split by simple punctuation
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    if len(sentences) <= n_sentences:
        return " ".join(sentences) + "."
    
    # Calculate embeddings for all sentences
    sent_embs = np.array([get_embedding(s) for s in sentences])
    # Document embedding is average of sentence embeddings
    doc_emb = np.mean(sent_embs, axis=0).reshape(1, -1)
    
    # Compute similarity to document embedding
    sims = cosine_similarity(sent_embs, doc_emb).flatten()
    
    # Get top N indices, then sort by original order to keep flow
    top_indices = sims.argsort()[-n_sentences:]
    top_indices.sort()
    
    return " ".join([sentences[i] for i in top_indices]) + "."

# ==========================================
# Handlers
# ==========================================

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}

@app.post("/analyze", response_model=AnalysisResult)
async def analyze(req: AnalysisRequest, request: Request):
    logger.info(f"Incoming analysis request from {request.client.host}")
    if not req.text or len(req.text.strip()) < 10:
        logger.warning("Short text received, skipping full analysis")
        return AnalysisResult(
            profitability=0.5,
            risk=0.5,
            relevance=0.1,
            keywords=[],
            summary="Недостаточно текста для анализа.",
            entities=[]
        )

    # 1. Generate Summary
    summary = extractive_summary(req.text, n_sentences=2)

    # 2. Extract Entities
    entities = heuristic_ner(req.text)
    
    # 3. Calculate Risk and Profitability using Embeddings
    # Compute embedding of the whole text (truncated for speed)
    text_emb = get_embedding(req.text[:2000]).reshape(1, -1)
    
    # Anchor vectors
    risk_anchors = ["ошибка", "сбой", "задержка", "риск", "убыток", "уязвимость", "проблема"]
    profit_anchors = ["прибыль", "эффективность", "успех", "рост", "монетизация", "оптимизация", "выгода"]
    
    risk_emb = np.mean([get_embedding(w) for w in risk_anchors], axis=0).reshape(1, -1)
    profit_emb = np.mean([get_embedding(w) for w in profit_anchors], axis=0).reshape(1, -1)
    
    # Similarity
    sim_risk = cosine_similarity(text_emb, risk_emb)[0][0]
    sim_profit = cosine_similarity(text_emb, profit_emb)[0][0]
    
    # Map from [-1, 1] to [0, 1] and add baseline
    risk_score = min(0.95, max(0.1, 0.3 + sim_risk * 0.7))
    profit_score = min(0.95, max(0.1, 0.4 + sim_profit * 0.6))

    # 4. Relevance Heuristic
    it_terms = ["интеграция", "разработка", "архитектура", "система", "данные", "интерфейс", "проект"]
    found_terms = list(set([t for t in it_terms if t in req.text.lower()]))
    relevance = min(0.95, 0.3 + (len(found_terms) * 0.1) + (len(req.text) / 5000))

    return AnalysisResult(
        profitability=round(profit_score * 100, 2), # Return as percentage 0-100
        risk=round(risk_score * 100, 2), # Return as percentage 0-100
        relevance=round(relevance * 100, 2), # Return as percentage 0-100
        keywords=found_terms[:5],
        summary=summary,
        entities=entities
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
