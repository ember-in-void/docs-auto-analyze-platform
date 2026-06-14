# ==========================================
# package-level documentation
# ==========================================
"""
Package main represents the FastAPI entrypoint and router for the NLP microservice.
It coordinates text processing, ruBERT embedding calculations, LLM document analysis,
and structured gap analysis results generation.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Import modules
from schemas import (
    AnalysisRequest,
    AnalysisResult,
    MetaInfo,
    TechStack,
    Metric,
    Entity,
    GapAnalysisResult
)
import embedder
import heuristics
import llm

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("nlp-service")

# --- App Instantiation ---
app = FastAPI(title="NLP Analysis Service")

# ==========================================
# Helper Functions
# ==========================================

def _determine_domain(text: str) -> str:
    """Determine document domain based on keyword presence."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["e-commerce", "интернет-магазин", "ритейл", "торговл", "маркетплейс", "товар"]):
        return "E-commerce / Ритейл"
    elif any(w in text_lower for w in ["финтех", "банк", "платёж", "финанс", "кредит", "транзакц"]):
        return "Финтех / Банки"
    elif any(w in text_lower for w in ["логистик", "доставк", "склад", "транспорт", "груз"]):
        return "Логистика / Транспорт"
    elif any(w in text_lower for w in ["медицин", "здрав", "клиник", "врач", "пациент"]):
        return "Медицина / Здравоохранение"
    return "Не указано"

# ==========================================
# API Endpoints
# ==========================================

@app.get("/health")
def health() -> Dict[str, Any]:
    """Check NLP model load status and service health."""
    return {
        "status": "ok",
        "model_loaded": embedder.model is not None
    }


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(req: AnalysisRequest, request: Request) -> AnalysisResult:
    """
    Endpoint for performing document analysis, extracting entities,
    performing gap analysis, and computing risk/profitability/relevance scores.
    """
    logger.info(f"Incoming analysis request from {request.client.host}")
    
    if not req.text or len(req.text.strip()) < 10:
        logger.warning("Short text received, skipping full analysis")
        return AnalysisResult(
            meta_info=MetaInfo(budget="Не указано", timeline="Не указано", domain="Не указано"),
            executive_summary="Недостаточно текста для анализа.",
            tech_stack=TechStack(detected=[], missing=["Redis", "Message Broker"]),
            metrics=[
                Metric(type="risk", label="Уровень риска", score=50.0, level="Средний", reasoning="Недостаточно текста для анализа", recommendations=[]),
                Metric(type="profitability", label="Потенциал окупаемости", score=50.0, level="Средний", reasoning="Недостаточно текста для анализа", recommendations=[]),
                Metric(type="relevance", label="Соответствие требованиям", score=50.0, level="Средний", reasoning="Недостаточно текста для анализа", recommendations=[])
            ],
            entities=[]
        )

    # 1. Phase 1: Preprocessing / Segmentation & NER
    is_llama = False
    gap_analysis_data = None
    entity_objects = []
    
    try:
        logger.info("Attempting Llama 3 analysis via Ollama...")
        norm_doc = await llm.query_ollama_template(req.text)
        logger.info("✓ Llama 3 successfully parsed the document into template!")
        is_llama = True
        gap_analysis_data = norm_doc
        
        # Recover entities and offsets
        raw_entities = norm_doc.get("entities", [])
        entities = llm.recover_entity_offsets(req.text, raw_entities)
        entity_objects = [
            Entity(text=ent["text"], type=ent["type"], start=ent["start"], end=ent["end"])
            for ent in entities
        ]
        detected_techs = sorted(list(set(ent.text for ent in entity_objects if ent.type == "Technology")))
        
        budget_val = norm_doc.get("metadata", {}).get("budget") or "Не указано"
        timeline_val = norm_doc.get("metadata", {}).get("deadline") or "Не указано"
        domain_val = _determine_domain(req.text)
        
        summary_text = norm_doc.get("sections", {}).get("purpose", {}).get("extracted_text") or ""
        arch_text = norm_doc.get("sections", {}).get("tech_stack", {}).get("architecture_description") or ""
        
        risk_list = norm_doc.get("sections", {}).get("risks", {}).get("extracted_risks", [])
        risk_text = " ".join([r.get("text", "") for r in risk_list if isinstance(r, dict)])
        
        econ_list = norm_doc.get("sections", {}).get("economics", {}).get("extracted_metrics", [])
        profit_text = " ".join([f"{e.get('metric', '')}: {e.get('value', '')}" for e in econ_list if isinstance(e, dict)])
        
    except Exception as e:
        logger.warning(f"Llama 3 template parsing failed or timed out: {e}. Falling back to heuristic segmentation.")
        
        # Fallback NER
        raw_entities = heuristics.heuristic_ner(req.text)
        entity_objects = [
            Entity(text=ent["text"], type=ent["type"], start=ent["start"], end=ent["end"])
            for ent in raw_entities
        ]
        detected_techs = sorted(list(set(ent.text for ent in entity_objects if ent.type == "Technology")))
        
        norm_doc = heuristics.fallback_segmentation(req.text)
        meta_data = norm_doc.get("meta_info", {})
        budget_val = meta_data.get("budget", "Не указано") or "Не указано"
        timeline_val = meta_data.get("timeline", "Не указано") or "Не указано"
        domain_val = meta_data.get("domain", "Не указано") or "Не указано"

        sections = norm_doc.get("sections", {})
        summary_text = sections.get("summary", "") or ""
        arch_text = sections.get("architecture_and_tech", "") or ""
        risk_text = sections.get("risks_and_security", "") or ""
        profit_text = sections.get("business_and_finance", "") or ""
        
        # Build gap analysis via heuristics
        gap_analysis_data = heuristics.generate_fallback_gap_analysis(req.text, detected_techs, raw_entities)

    if not summary_text.strip():
        summary_text = req.text[:500]

    # 2. Phase 2: ruBERT Semantic Analysis & Scoring
    words = req.text.lower().split()
    word_count = max(len(words), 1)

    # Ensure precomputed anchors are ready
    if embedder.risk_emb_cache is None or embedder.profit_emb_cache is None or embedder.tech_emb_cache is None:
        embedder.precompute_anchors()

    # -- Risk Metric Scoring --
    risk_score = 0.5
    if risk_text.strip() and embedder.risk_emb_cache is not None:
        risk_text_emb = embedder.get_embedding(risk_text[:2000]).reshape(1, -1)
        sim_risk = cosine_similarity(risk_text_emb, embedder.risk_emb_cache)[0][0]
        risk_hits = sum(req.text.lower().count(w) for w in ["риск", "угроз", "проблем", "сбой", "ошибк", "уязвимост", "штраф", "санкци", "убыт", "утек"])
        risk_factor = min(0.5, (risk_hits / word_count) * 20)
        risk_score = 0.2 + (sim_risk * 0.4) + risk_factor
        
        risk_sec_lower = risk_text.lower()
        if "не обнаруж" in risk_sec_lower or "отсутствуют" in risk_sec_lower or "нет рисков" in risk_sec_lower or len(risk_sec_lower.strip()) < 15:
            risk_score = 0.15
            risk_pct = round(min(0.95, max(0.10, risk_score)) * 100, 2)
            risk_reasoning = "Критические технические и операционные риски не обнаружены."
        else:
            risk_pct = round(min(0.95, max(0.10, risk_score)) * 100, 2)
            risk_reasoning = f"Риски оценены на основе семантического анализа раздела угроз. Выявлено сходство с понятиями сбоев и уязвимостей ({risk_pct}%)."
    else:
        risk_pct = round(min(0.95, max(0.10, risk_score)) * 100, 2)
        risk_reasoning = "Оценка риска выполнена по базовому контенту."
    
    # -- Profitability Metric Scoring --
    profit_score = 0.5
    if profit_text.strip() and embedder.profit_emb_cache is not None:
        profit_text_emb = embedder.get_embedding(profit_text[:2000]).reshape(1, -1)
        sim_profit = cosine_similarity(profit_text_emb, embedder.profit_emb_cache)[0][0]
        
        profit_hits = sum(req.text.lower().count(w) for w in ["прибыл", "доход", "выгод", "рентабельност", "эффективност", "успех", "экономия", "окупаемост"])
        profit_factor = min(0.5, (profit_hits / word_count) * 20)
        profit_score = 0.25 + (sim_profit * 0.4) + profit_factor

        profit_sec_lower = profit_text.lower()
        if "не описан" in profit_sec_lower or "нет данных" in profit_sec_lower or len(profit_sec_lower.strip()) < 15:
            profit_score = 0.35
            profit_pct = round(min(0.95, max(0.15, profit_score)) * 100, 2)
            profit_reasoning = "Экономический потенциал и финансовые показатели слабо отражены в документации."
        else:
            profit_pct = round(min(0.95, max(0.15, profit_score)) * 100, 2)
            profit_reasoning = f"Потенциал окупаемости оценен по финансовому разделу. Сходство с концептами коммерческой эффективности: {profit_pct}%."
    else:
        profit_pct = round(min(0.95, max(0.15, profit_score)) * 100, 2)
        profit_reasoning = "Оценка доходности выполнена по базовому контенту."

    # -- Relevance Metric Scoring --
    relevance_score = 0.5
    if arch_text.strip() and embedder.tech_emb_cache is not None:
        tech_text_emb = embedder.get_embedding(arch_text[:2000]).reshape(1, -1)
        sim_relevance = cosine_similarity(tech_text_emb, embedder.tech_emb_cache)[0][0]
        
        it_terms = ["интеграция", "разработка", "архитектура", "система", "данные", "интерфейс", "проект"]
        found_terms = list(set([t for t in it_terms if t in req.text.lower()]))
        
        relevance_score = 0.3 + (sim_relevance * 0.3) + (len(found_terms) * 0.05) + (len(detected_techs) * 0.03)
        relevance_pct = round(min(0.95, max(0.10, relevance_score)) * 100, 2)
        relevance_reasoning = f"Соответствие требованиям оценено по архитектурному разделу. Степень зрелости стека и архитектурного описания: {relevance_pct}%."
    else:
        relevance_pct = round(min(0.95, max(0.10, relevance_score)) * 100, 2)
        relevance_reasoning = "Оценка соответствия выполнена по базовому контенту."

    # Determine levels
    risk_level = "Высокий" if risk_pct > 70 else ("Низкий" if risk_pct < 40 else "Средний")
    profit_level = "Высокий" if profit_pct > 70 else ("Низкий" if profit_pct < 40 else "Средний")
    relevance_level = "Высокий" if relevance_pct > 70 else ("Низкий" if relevance_pct < 40 else "Средний")

    # 3. Detailed Gap Analysis Recommendations
    gap_result = heuristics.perform_gap_analysis(domain_val, detected_techs)
    missing_techs = gap_result["missing_techs"]
    
    risk_recs = []
    profit_recs = []
    relevance_recs = []

    if risk_level == "Низкий":
        risk_recs = ["Регулярный мониторинг прогресса проекта", "Проведение стандартного код-ревью"]
    elif risk_level == "Средний":
        risk_recs = ["Детализировать требования к интеграциям", "Провести аудит архитектуры на ранних этапах", "Заложить резерв времени на тестирование"]
    else:
        risk_recs = ["Разработать план снижения рисков (Risk Mitigation Plan)", "Провести фасилитационную сессию с заказчиком для уточнения требований", "Привлечь внешних экспертов для аудита архитектурных решений"]

    if profit_level == "Низкий":
        profit_recs = ["Пересмотреть бизнес-модель проекта", "Провести дополнительный анализ рынка и целевой аудитории"]
    elif profit_level == "Средний":
        profit_recs = ["Оптимизировать операционные затраты", "Разработать детальный план поэтапной монетизации"]
    else:
        profit_recs = ["Ускорить запуск MVP для более быстрого возврата инвестиций", "Масштабировать успешные каналы привлечения клиентов после запуска"]

    if relevance_level == "Низкий":
        relevance_recs = ["Актуализировать технологический стек", "Изучить современные аналоги и решения конкурентов"]
    elif relevance_level == "Средний":
        relevance_recs = ["Рассмотреть внедрение дополнительных современных инструментов", "Провести обучение команды новым практикам"]
    else:
        relevance_recs = ["Продолжать использование выбранных практик", "Поделиться архитектурным кейсом с сообществом"]

    # Append Gap-specific recommendations
    relevance_recs.extend(gap_result["relevance_recs"])
    risk_recs.extend(gap_result["risk_recs"])

    metrics = [
        Metric(type="risk", label="Уровень риска", score=risk_pct, level=risk_level, reasoning=risk_reasoning, recommendations=risk_recs),
        Metric(type="profitability", label="Потенциал окупаемости", score=profit_pct, level=profit_level, reasoning=profit_reasoning, recommendations=profit_recs),
        Metric(type="relevance", label="Соответствие требованиям", score=relevance_pct, level=relevance_level, reasoning=relevance_reasoning, recommendations=relevance_recs)
    ]

    exec_summary = summary_text.strip()

    return AnalysisResult(
        meta_info=MetaInfo(budget=budget_val, timeline=timeline_val, domain=domain_val),
        executive_summary=exec_summary,
        tech_stack=TechStack(detected=detected_techs, missing=missing_techs),
        metrics=metrics,
        entities=entity_objects,
        gap_analysis=gap_analysis_data
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
