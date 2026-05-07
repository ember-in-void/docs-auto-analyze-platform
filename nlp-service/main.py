# ==========================================
# NLP Service — Python/FastAPI
# ==========================================
import os
import logging
from typing import List
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from transformers import pipeline

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
    sentiment_pipe = pipeline(
        "sentiment-analysis", 
        model="blanchefort/rubert-base-cased-sentiment"
    )
    logger.info("✓ Models loaded successfully")
except Exception as e:
    logger.error(f"Error loading models: {e}")
    sentiment_pipe = None

# ==========================================
# Schemas
# ==========================================

class AnalysisRequest(BaseModel):
    text: str

class AnalysisResult(BaseModel):
    profitability: float
    risk: float
    relevance: float
    keywords: List[str]
    summary: str

# ==========================================
# Handlers
# ==========================================

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": sentiment_pipe is not None}

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
            summary="Недостаточно текста для анализа."
        )

    # 1. Sentiment Analysis
    # Labels: NEUTRAL, POSITIVE, NEGATIVE
    sentiment = sentiment_pipe(req.text[:512])[0]
    label = sentiment['label']
    score = sentiment['score']

    # Map sentiment to project metrics
    # Neutral is baseline 0.5
    profitability = 0.5
    risk = 0.5

    if label == 'POSITIVE':
        profitability = 0.5 + (score * 0.45)
        risk = 0.5 - (score * 0.3)
    elif label == 'NEGATIVE':
        risk = 0.5 + (score * 0.4)
        profitability = 0.5 - (score * 0.4)
    
    # 2. Relevance Heuristic
    # Based on text length and some common IT terms
    it_terms = ["интеграция", "разработка", "архитектура", "система", "данные", "интерфейс"]
    found_terms = [t for t in it_terms if t in req.text.lower()]
    relevance = min(0.95, 0.3 + (len(found_terms) * 0.1) + (len(req.text) / 5000))

    # 3. Dummy Keyword Extraction (Placeholder for more complex logic)
    # In real app use RAKE or KeyBERT
    words = req.text.lower().split()
    unique_words = sorted(list(set([w for w in words if len(w) > 5 and w.isalpha()])))[:10]

    return AnalysisResult(
        profitability=round(profitability, 3),
        risk=round(risk, 3),
        relevance=round(relevance, 3),
        keywords=found_terms + unique_words[:5],
        summary=f"Анализ завершен. Тональность текста: {label}. Проект оценен как {label.lower()} на базе семантического разбора."
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
