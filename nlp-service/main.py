# ==========================================
# NLP Service — Python/FastAPI
# ==========================================
import os
import re
import logging
import json
import urllib.request
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

class MetaInfo(BaseModel):
    budget: str
    timeline: str
    domain: str

class TechStack(BaseModel):
    detected: List[str]
    missing: List[str]

class Metric(BaseModel):
    type: str
    label: str
    score: float
    level: str
    reasoning: str
    recommendations: List[str]

class AnalysisResult(BaseModel):
    meta_info: MetaInfo
    executive_summary: str
    tech_stack: TechStack
    metrics: List[Metric]
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

def extract_sentences(text: str) -> List[str]:
    raw_lines = [line.strip() for line in text.split('\n')]
    
    sentences = []
    for line in raw_lines:
        if not line:
            continue
        
        # Split a line into sentences:
        regex = r'(?<!\b\d)(?<!\b[а-яa-z]\.)(?<!\bруб\.)(?<!\bтыс\.)(?<!\bмлн\.)(?<!\bмлрд\.)(?<=\.|\?|!)(?:\s|$)'
        sub_sents = re.split(regex, line, flags=re.IGNORECASE)
        for s in sub_sents:
            s = s.strip()
            if not s:
                continue
            
            # Clean leading/trailing lists, numbers, bullets
            s_clean = re.sub(r'^(?:[-*•+]\s*|\d+(?:\.\d+)*\.?\s*)', '', s)
            s_clean = s_clean.strip()
            
            # Skip short ones
            if len(s_clean) < 15:
                continue
                
            # Skip headers
            if len(s_clean) < 45 and (s_clean.isupper() or len(s_clean.split()) <= 3):
                continue
                
            if not any(c.isalpha() for c in s_clean):
                continue
                
            sentences.append(s_clean)
            
    return sentences

def extractive_summary(text: str, n_sentences: int = 3) -> str:
    """Generate structured summary with objective assessment points."""
    sentences = extract_sentences(text)
    
    tech_list = ["React", "Golang", "PostgreSQL", "Docker", "Kubernetes", "Python", "FastAPI", "Vue", "TypeScript", "ClickHouse", "Redis", "Kafka", "Go"]
    
    # Rating functions
    def rate_goal(s: str) -> float:
        s_lower = s.lower()
        score = 0
        if any(w in s_lower for w in ["создани", "разработ", "внедр", "задач"]):
            score += 3
        if any(w in s_lower for w in ["платформ", "систем", "решени"]):
            score += 2
        if any(w in s_lower for w in ["цель"]):
            score += 1
        
        # Penalize document titles/headings
        if any(s_lower.startswith(w) for w in ["техническое задание", "архитектурный документ", "журнал инцидентов", "требования к", "отчет по", "финальный отчёт"]):
            score -= 6
            
        # Prefer longer, descriptive sentences
        if len(s) > 50:
            score += 1
        if len(s) > 100:
            score += 1

        # Subtract if it has financial metrics (better for profit/economic potential)
        if any(w in s_lower for w in ["рентабельност", "прибыл", "доход", "окупаемост", "%", "руб"]):
            score -= 4
        # Subtract if it's too technical
        if any(w in s_lower for w in ["postgres", "clickhouse", "kafka", "redis", "kubernetes"]):
            score -= 2
        return score

    def rate_tech(s: str) -> float:
        s_lower = s.lower()
        score = 0
        found_techs = [t for t in tech_list if re.search(r'\b' + re.escape(t.lower()) + r'\b', s_lower)]
        score += len(found_techs) * 3
        if any(w in s_lower for w in ["технолог", "стек", "разработк", "архитектур", "микросервис", "сервис", "база данных", "бд"]):
            score += 2
        return score

    def rate_risk(s: str) -> float:
        s_lower = s.lower()
        score = 0
        if any(w in s_lower for w in ["риск", "угроз", "уязвимост", "опасност"]):
            score += 4
        if any(w in s_lower for w in ["проблем", "сбой", "ошибк", "задержк", "убыт", "инцидент", "деградаци"]):
            score += 2
        return score

    def rate_profit(s: str) -> float:
        s_lower = s.lower()
        score = 0
        if any(w in s_lower for w in ["прибыл", "доход", "выгод", "рентабельност", "эффективност", "экономия", "окупаемост", "стоимост", "бюджет"]):
            score += 4
        if any(w in s_lower for w in ["%", "рост", "снижени", "увеличени", "повышени", "млн", "тыс"]):
            score += 2
        return score

    # Classify sentences
    goal_candidates = []
    tech_candidates = []
    risk_candidates = []
    profit_candidates = []
    
    for s in sentences:
        g_sc = rate_goal(s)
        t_sc = rate_tech(s)
        r_sc = rate_risk(s)
        p_sc = rate_profit(s)
        
        if g_sc > 0:
            goal_candidates.append((g_sc, s))
        if t_sc > 0:
            tech_candidates.append((t_sc, s))
        if r_sc > 0:
            risk_candidates.append((r_sc, s))
        if p_sc > 0:
            profit_candidates.append((p_sc, s))
            
    # Sort candidates
    goal_candidates.sort(key=lambda x: -x[0])
    tech_candidates.sort(key=lambda x: -x[0])
    risk_candidates.sort(key=lambda x: -x[0])
    profit_candidates.sort(key=lambda x: -x[0])
    
    # 1. Goal
    goal_str = ""
    used_sentences = set()
    if goal_candidates:
        goal_str = goal_candidates[0][1]
        used_sentences.add(goal_str.lower())
    else:
        goal_str = sentences[0] if sentences else "Суть проекта не определена."
        used_sentences.add(goal_str.lower())
        
    if not goal_str.endswith('.'):
        goal_str += '.'
        
    # 2. Tech
    # Scan the whole text for known tech terms first
    techs_found = [t for t in tech_list if re.search(r'\b' + re.escape(t.lower()) + r'\b', text.lower())]
    if "Golang" in techs_found and "Go" in techs_found:
        techs_found.remove("Go")
        
    tech_str = ""
    if techs_found:
        tech_str = f"Используемые технологии: {', '.join(techs_found)}."
        # Append top technical sentence that isn't the goal sentence
        filtered_tech = [t[1] for t in tech_candidates if t[1].lower() not in used_sentences]
        if filtered_tech:
            arch_sent = filtered_tech[0]
            if not arch_sent.endswith('.'):
                arch_sent += '.'
            tech_str += " " + arch_sent
            # Mark it used if it's high scoring
            used_sentences.add(arch_sent.lower())
    elif tech_candidates:
        tech_str = tech_candidates[0][1]
        if not tech_str.endswith('.'):
            tech_str += '.'
        used_sentences.add(tech_str.lower())
    else:
        tech_str = "Технологический стек не описан детально."
        
    # 3. Risks
    filtered_risks = [r[1] for r in risk_candidates if r[1].lower() not in used_sentences]
    risk_str = ""
    if filtered_risks:
        seen = set()
        unique_risks = []
        for r in filtered_risks[:2]:
            if r.lower() not in seen:
                seen.add(r.lower())
                if not r.endswith('.'):
                    r += '.'
                unique_risks.append(r)
                used_sentences.add(r.lower())
        risk_str = " ".join(unique_risks)
    else:
        risk_str = "Критические риски в тексте документации не обнаружены."
        
    # 4. Profit
    filtered_profit = [p[1] for p in profit_candidates if p[1].lower() not in used_sentences]
    profit_str = ""
    if filtered_profit:
        profit_str = filtered_profit[0]
        if not profit_str.endswith('.'):
            profit_str += '.'
    else:
        # If no unused profit sentence, check if we had any profit candidates at all
        all_profit = [p[1] for p in profit_candidates]
        if all_profit:
            profit_str = all_profit[0]
            if not profit_str.endswith('.'):
                profit_str += '.'
        else:
            profit_str = "Финансовые показатели или потенциал окупаемости не описаны."
            
    return goal_str, tech_str, risk_str, profit_str

# ==========================================
# Handlers
# ==========================================

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}

def query_ollama(text: str) -> Dict[str, Any]:
    """Query local Llama 3 via Ollama on the host machine to get structured audit analysis."""
    url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434") + "/api/generate"
    
    system_prompt = (
        "Ты — старший технический аналитик (CTO). Твоя задача — проанализировать неструктурированную ИТ-документацию "
        "и извлечь из нее данные строго по заданному корпоративному стандарту.\n"
        "Даже если текст написан хаотично, найди нужные смыслы и заполни следующие секции:\n"
        "1. meta_info (бюджет, сроки/timeline, доменная область проекта/domain).\n"
        "2. executive_summary (один связный абзац резюме проекта, технологий, рисков и окупаемости).\n"
        "3. tech_stack (detected - список упомянутых в тексте технологий; missing - список критически рекомендуемых технологий, которых не хватает в тексте, например Redis, Message Broker, Docker и др.).\n"
        "4. metrics (массив из 3 метрик с type 'risk', 'profitability', 'relevance'; для каждой укажи label (название), score (число 0-100), level ('Низкий', 'Средний' или 'Высокий'), reasoning (обоснование оценки) и рекомендации/recommendations (массив строк)).\n"
        "Верни ответ СТРОГО в формате JSON без разметки markdown: \n"
        "{\n"
        "  \"meta_info\": {\"budget\": \"...\", \"timeline\": \"...\", \"domain\": \"...\"},\n"
        "  \"executive_summary\": \"...\",\n"
        "  \"tech_stack\": {\"detected\": [\"...\"], \"missing\": [\"...\"]},\n"
        "  \"metrics\": [\n"
        "    {\n"
        "      \"type\": \"risk\",\n"
        "      \"label\": \"Уровень риска\",\n"
        "      \"score\": 0.0,\n"
        "      \"level\": \"...\",\n"
        "      \"reasoning\": \"...\",\n"
        "      \"recommendations\": [\"...\"]\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"profitability\",\n"
        "      \"label\": \"Потенциал окупаемости\",\n"
        "      \"score\": 0.0,\n"
        "      \"level\": \"...\",\n"
        "      \"reasoning\": \"...\",\n"
        "      \"recommendations\": [\"...\"]\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"relevance\",\n"
        "      \"label\": \"Соответствие требованиям\",\n"
        "      \"score\": 0.0,\n"
        "      \"level\": \"...\",\n"
        "      \"reasoning\": \"...\",\n"
        "      \"recommendations\": [\"...\"]\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    prompt = f"Системная инструкция:\n{system_prompt}\n\nАнализируемый документ:\n{text}"
    
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req, timeout=60) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        response_text = res_data.get("response", "")
        return json.loads(response_text)

@app.post("/analyze", response_model=AnalysisResult)
async def analyze(req: AnalysisRequest, request: Request):
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

    # 1. Extract Entities
    entities = heuristic_ner(req.text)

    # Try Llama 3 via Ollama
    try:
        logger.info("Attempting Llama 3 analysis via Ollama...")
        llama_data = query_ollama(req.text)
        logger.info("✓ Llama 3 analysis successful!")
        
        return AnalysisResult(
            meta_info=MetaInfo(
                budget=llama_data.get("meta_info", {}).get("budget", "Не указано"),
                timeline=llama_data.get("meta_info", {}).get("timeline", "Не указано"),
                domain=llama_data.get("meta_info", {}).get("domain", "Не указано")
            ),
            executive_summary=llama_data.get("executive_summary", ""),
            tech_stack=TechStack(
                detected=llama_data.get("tech_stack", {}).get("detected", []),
                missing=llama_data.get("tech_stack", {}).get("missing", [])
            ),
            metrics=[
                Metric(
                    type=m.get("type", "risk"),
                    label=m.get("label", "Показатель"),
                    score=float(m.get("score", 50.0)),
                    level=m.get("level", "Средний"),
                    reasoning=m.get("reasoning", ""),
                    recommendations=m.get("recommendations", [])
                )
                for m in llama_data.get("metrics", [])
            ],
            entities=entities
        )
    except Exception as e:
        logger.warning(f"Llama 3 analysis failed or timed out: {e}. Falling back to ruBERT + heuristics.")

    # 2. Generate Summary Parts
    goal_str, tech_str, risk_str, profit_str = extractive_summary(req.text, n_sentences=2)
    
    # Construct clean single paragraph executive summary
    goal_clean = goal_str.strip().rstrip('.')
    tech_clean = tech_str.strip().rstrip('.')
    risk_clean = risk_str.strip().rstrip('.')
    profit_clean = profit_str.strip().rstrip('.')
    
    exec_summary_parts = []
    if goal_clean:
        exec_summary_parts.append(f"Проект направлен на решение следующей задачи: {goal_clean}.")
    if tech_clean:
        if tech_clean.startswith("Используемые технологии:"):
            exec_summary_parts.append(f"{tech_clean}.")
        else:
            exec_summary_parts.append(f"Технологический стек проекта: {tech_clean}.")
    if risk_clean:
        if risk_clean.startswith("Критические риски"):
            exec_summary_parts.append(f"{risk_clean}.")
        else:
            exec_summary_parts.append(f"В ходе анализа выявлены следующие риски: {risk_clean}.")
    if profit_clean:
        if profit_clean.startswith("Финансовые показатели"):
            exec_summary_parts.append(f"{profit_clean}.")
        else:
            exec_summary_parts.append(f"Экономический потенциал: {profit_clean}.")
            
    executive_summary = " ".join(exec_summary_parts)
    executive_summary = re.sub(r'\.+', '.', executive_summary)
    executive_summary = re.sub(r'\s+', ' ', executive_summary).strip()

    # 3. Extract Meta Info (Budget and Timeline)
    budget_val = "Не указано"
    deadline_val = "Не указано"
    for ent in entities:
        if ent["type"] == "Budget" and budget_val == "Не указано":
            budget_val = ent["text"]
        elif ent["type"] == "Deadline" and deadline_val == "Не указано":
            deadline_val = ent["text"]

    # Domain heuristic detection
    domain_val = "Не указано"
    text_lower = req.text.lower()
    if any(w in text_lower for w in ["e-commerce", "интернет-магазин", "ритейл", "торговл", "маркетплейс", "товар"]):
        domain_val = "E-commerce / Ритейл"
    elif any(w in text_lower for w in ["финтех", "банк", "платёж", "финанс", "кредит", "транзакц"]):
        domain_val = "Финтех / Банки"
    elif any(w in text_lower for w in ["логистик", "доставк", "склад", "транспорт", "груз"]):
        domain_val = "Логистика / Транспорт"
    elif any(w in text_lower for w in ["медицин", "здрав", "клиник", "врач", "пациент"]):
        domain_val = "Медицина / Здравоохранение"

    meta_info = MetaInfo(budget=budget_val, timeline=deadline_val, domain=domain_val)

    # 4. Tech Stack Gap Analysis
    detected_techs = sorted(list(set(ent["text"] for ent in entities if ent["type"] == "Technology")))
    potential_missing = ["Redis", "RabbitMQ", "Kafka", "Docker", "Kubernetes", "PostgreSQL", "Nginx", "CI/CD Pipeline"]
    detected_lower = {t.lower() for t in detected_techs}
    missing_techs = [m for m in potential_missing if m.lower() not in detected_lower][:2]
    if not missing_techs:
        missing_techs = ["Message Broker", "Redis"]

    tech_stack = TechStack(detected=detected_techs, missing=missing_techs)

    # 5. Calculate Risk, Profitability, Relevance
    words = text_lower.split()
    word_count = max(len(words), 1)

    risk_hits = sum(text_lower.count(w) for w in ["риск", "угроз", "проблем", "сбой", "ошибк", "уязвимост", "штраф", "санкци", "убыт"])
    profit_hits = sum(text_lower.count(w) for w in ["прибыл", "доход", "выгод", "рентабельност", "эффективност", "успех", "экономия", "окупаемост"])

    text_emb = get_embedding(req.text[:2000]).reshape(1, -1)
    
    risk_anchors = ["ошибка", "сбой", "задержка", "риск", "убыток", "уязвимость", "проблема"]
    profit_anchors = ["прибыль", "эффективность", "успех", "рост", "монетизация", "оптимизация", "выгода"]
    
    risk_emb = np.mean([get_embedding(w) for w in risk_anchors], axis=0).reshape(1, -1)
    profit_emb = np.mean([get_embedding(w) for w in profit_anchors], axis=0).reshape(1, -1)
    
    sim_risk = cosine_similarity(text_emb, risk_emb)[0][0]
    sim_profit = cosine_similarity(text_emb, profit_emb)[0][0]
    
    risk_factor = min(0.5, (risk_hits / word_count) * 20)
    profit_factor = min(0.5, (profit_hits / word_count) * 20)

    risk_score = 0.2 + (sim_risk * 0.4) + risk_factor
    profit_score = 0.25 + (sim_profit * 0.4) + profit_factor

    risk_score = min(0.95, max(0.10, risk_score))
    profit_score = min(0.95, max(0.15, profit_score))

    it_terms = ["интеграция", "разработка", "архитектура", "система", "данные", "интерфейс", "проект"]
    found_terms = list(set([t for t in it_terms if t in req.text.lower()]))
    relevance_val = min(0.95, 0.3 + (len(found_terms) * 0.1) + (len(req.text) / 5000))

    risk_pct = round(risk_score * 100, 2)
    profit_pct = round(profit_score * 100, 2)
    relevance_pct = round(relevance_val * 100, 2)

    # Risk level heuristics
    if risk_pct < 40:
        risk_level = "Низкий"
        risk_reasoning = "Технические риски минимальны. Стек технологий стандартный, требования описаны корректно."
        risk_recs = ["Регулярный мониторинг прогресса проекта", "Проведение стандартного код-ревью"]
    elif risk_pct < 70:
        risk_level = "Средний"
        risk_reasoning = "Присутствуют умеренные риски интеграции и управления сроками. Требуется дополнительное проектирование."
        risk_recs = ["Детализировать требования к интеграциям", "Провести аудит архитектуры на ранних этапах", "Заложить резерв времени на тестирование"]
    else:
        risk_level = "Высокий"
        risk_reasoning = "Выявлены критические риски: высокая сложность архитектуры, неопределенность в требованиях или отсутствие описания ключевых компонентов."
        risk_recs = ["Разработать план снижения рисков (Risk Mitigation Plan)", "Провести фасилитационную сессию с заказчиком для уточнения требований", "Привлечь внешних экспертов для аудита архитектурных решений"]

    # Profitability level heuristics
    if profit_pct < 40:
        profit_level = "Низкий"
        profit_reasoning = "Финансовые показатели проекта выражены слабо. Низкий потенциал окупаемости на основе текущих данных."
        profit_recs = ["Пересмотреть бизнес-модель проекта", "Провести дополнительный анализ рынка и целевой аудитории"]
    elif profit_pct < 70:
        profit_level = "Средний"
        profit_reasoning = "Проект обладает умеренным экономическим потенциалом. Ожидается стандартная окупаемость инвестиций."
        profit_recs = ["Оптимизировать операционные затраты", "Разработать детальный план поэтапной монетизации"]
    else:
        profit_level = "Высокий"
        profit_reasoning = "Высокий коммерческий потенциал проекта. Выявлены явные точки роста эффективности и сокращения издержек."
        profit_recs = ["Ускорить запуск MVP для более быстрого возврата инвестиций", "Масштабировать успешные каналы привлечения клиентов после запуска"]

    # Relevance level heuristics
    if relevance_pct < 40:
        relevance_level = "Низкий"
        relevance_reasoning = "Содержание документации слабо соответствует современным IT-стандартам и лучшим практикам."
        relevance_recs = ["Актуализировать технологический стек", "Изучить современные аналоги и решения конкурентов"]
    elif relevance_pct < 70:
        relevance_level = "Средний"
        relevance_reasoning = "Проект соответствует основным текущим трендам и требованиям рынка."
        relevance_recs = ["Рассмотреть внедрение дополнительных современных инструментов", "Провести обучение команды новым практикам"]
    else:
        relevance_level = "Высокий"
        relevance_reasoning = "Высокая актуальность проекта. Применяются современные подходы, стек технологий отвечает передовым стандартам."
        relevance_recs = ["Продолжать использование выбранных практик", "Поделиться архитектурным кейсом с сообществом"]

    metrics = [
        Metric(type="risk", label="Уровень риска", score=risk_pct, level=risk_level, reasoning=risk_reasoning, recommendations=risk_recs),
        Metric(type="profitability", label="Потенциал окупаемости", score=profit_pct, level=profit_level, reasoning=profit_reasoning, recommendations=profit_recs),
        Metric(type="relevance", label="Соответствие требованиям", score=relevance_pct, level=relevance_level, reasoning=relevance_reasoning, recommendations=relevance_recs)
    ]

    return AnalysisResult(
        meta_info=meta_info,
        executive_summary=executive_summary,
        tech_stack=tech_stack,
        metrics=metrics,
        entities=entities
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
