# ==========================================
# NLP Service — Python/FastAPI
# ==========================================
import os
import re
import logging
import json
import urllib.request
import numpy as np
from typing import List, Dict, Any, Optional
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

# --- Anchors ---
risk_anchors = ["ошибка", "сбой", "задержка", "риск", "убыток", "уязвимость", "проблема", "угроза", "взлом", "утечка"]
profit_anchors = ["прибыль", "эффективность", "успех", "рост", "монетизация", "оптимизация", "выгода", "рентабельность", "окупаемость"]
tech_anchors = ["архитектура", "разработка", "база данных", "интеграция", "микросервис", "технологический стек"]

risk_emb_cache = None
profit_emb_cache = None
tech_emb_cache = None

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

# --- Gap Analysis Schemas ---
class GapMetadata(BaseModel):
    project_name: Optional[str] = None
    document_date: Optional[str] = None
    deadline: Optional[str] = None
    budget: Optional[str] = None

class GapPurposeSection(BaseModel):
    status: str
    extracted_text: Optional[str] = None
    gaps: List[str] = []

class GapTechStackSection(BaseModel):
    status: str
    extracted_technologies: List[str] = []
    architecture_description: Optional[str] = None
    gaps: List[str] = []

class GapRiskItem(BaseModel):
    text: Optional[str] = None
    category: Optional[str] = None

class GapRisksSection(BaseModel):
    status: str
    extracted_risks: List[GapRiskItem] = []
    gaps: List[str] = []

class GapMetricItem(BaseModel):
    metric: Optional[str] = None
    value: Optional[str] = None

class GapEconomicsSection(BaseModel):
    status: str
    extracted_metrics: List[GapMetricItem] = []
    gaps: List[str] = []

class GapSections(BaseModel):
    purpose: GapPurposeSection
    tech_stack: GapTechStackSection
    risks: GapRisksSection
    economics: GapEconomicsSection

class GapAnalysisResult(BaseModel):
    metadata: GapMetadata
    sections: GapSections
    completeness_score: float
    clarifying_questions: List[str] = []

class AnalysisResult(BaseModel):
    meta_info: MetaInfo
    executive_summary: str
    tech_stack: TechStack
    metrics: List[Metric]
    entities: List[Entity]
    gap_analysis: Optional[GapAnalysisResult] = None

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

def precompute_anchors():
    global risk_emb_cache, profit_emb_cache, tech_emb_cache
    if model is None or tokenizer is None:
        return
    try:
        logger.info("Precomputing anchor embeddings...")
        risk_emb_cache = np.mean([get_embedding(w) for w in risk_anchors], axis=0).reshape(1, -1)
        profit_emb_cache = np.mean([get_embedding(w) for w in profit_anchors], axis=0).reshape(1, -1)
        tech_emb_cache = np.mean([get_embedding(w) for w in tech_anchors], axis=0).reshape(1, -1)
        logger.info("✓ Anchor embeddings precomputed")
    except Exception as e:
        logger.error(f"Error precomputing anchors: {e}")

# Trigger precomputing of anchors immediately if model is loaded
if model is not None:
    precompute_anchors()

def heuristic_ner(text: str) -> List[Dict[str, Any]]:
    """Simple dictionary and regex-based NER for MVP."""
    entities = []
    
    # --- Technology ---
    techs = [
        "React", "Golang", "PostgreSQL", "Docker", "Kubernetes", "Vue", "Python", "FastAPI", "Salesforce", "AWS", "Azure", "GCP", "Redis",
        "Kafka", "RabbitMQ", "ActiveMQ", "Memcached", "Kong", "Nginx", "Elasticsearch", "OpenSearch", "Sphinx",
        "Yandex Maps", "Google Maps", "OpenStreetMap", "Prometheus", "Grafana", "ELK", "Loki", "Jenkins", "GitLab", "GitHub", "Go"
    ]
    for t in techs:
        for match in re.finditer(r'\b' + re.escape(t.lower()) + r'\b', text.lower()):
            start = match.start()
            end = match.end()
            entities.append({"text": text[start:end], "type": "Technology", "start": start, "end": end})

    # --- Budget ---
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
        
        regex = r'(?<!\b\d)(?<!\b[а-яa-z]\.)(?<!\bруб\.)(?<!\bтыс\.)(?<!\bмлн\.)(?<!\bмлрд\.)(?<=\.|\?|!)(?:\s|$)'
        sub_sents = re.split(regex, line, flags=re.IGNORECASE)
        for s in sub_sents:
            s = s.strip()
            if not s:
                continue
            
            s_clean = re.sub(r'^(?:[-*•+]\s*|\d+(?:\.\d+)*\.?\s*)', '', s)
            s_clean = s_clean.strip()
            
            if len(s_clean) < 15:
                continue
                
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
    
    def rate_goal(s: str) -> float:
        s_lower = s.lower()
        score = 0
        if any(w in s_lower for w in ["создани", "разработ", "внедр", "задач"]):
            score += 3
        if any(w in s_lower for w in ["платформ", "систем", "решени"]):
            score += 2
        if any(w in s_lower for w in ["цель"]):
            score += 1
        if any(s_lower.startswith(w) for w in ["техническое задание", "архитектурный документ", "журнал инцидентов", "требования к", "отчет по", "финальный отчёт"]):
            score -= 6
        if len(s) > 50:
            score += 1
        if len(s) > 100:
            score += 1
        if any(w in s_lower for w in ["рентабельност", "прибыл", "доход", "окупаемост", "%", "руб"]):
            score -= 4
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
            
    goal_candidates.sort(key=lambda x: -x[0])
    tech_candidates.sort(key=lambda x: -x[0])
    risk_candidates.sort(key=lambda x: -x[0])
    profit_candidates.sort(key=lambda x: -x[0])
    
    used_sentences = set()
    
    goal_str = ""
    if goal_candidates:
        goal_str = goal_candidates[0][1]
        used_sentences.add(goal_str.lower())
    else:
        goal_str = sentences[0] if sentences else "Суть проекта не определена."
        used_sentences.add(goal_str.lower())
    if not goal_str.endswith('.'):
        goal_str += '.'
        
    techs_found = [t for t in tech_list if re.search(r'\b' + re.escape(t.lower()) + r'\b', text.lower())]
    if "Golang" in techs_found and "Go" in techs_found:
        techs_found.remove("Go")
        
    tech_str = ""
    if techs_found:
        tech_str = f"Используемые технологии: {', '.join(techs_found)}."
        filtered_tech = [t[1] for t in tech_candidates if t[1].lower() not in used_sentences]
        if filtered_tech:
            arch_sent = filtered_tech[0]
            if not arch_sent.endswith('.'):
                arch_sent += '.'
            tech_str += " " + arch_sent
            used_sentences.add(arch_sent.lower())
    elif tech_candidates:
        tech_str = tech_candidates[0][1]
        if not tech_str.endswith('.'):
            tech_str += '.'
        used_sentences.add(tech_str.lower())
    else:
        tech_str = "Технологический стек не описан детально."
        
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
        
    filtered_profit = [p[1] for p in profit_candidates if p[1].lower() not in used_sentences]
    profit_str = ""
    if filtered_profit:
        profit_str = filtered_profit[0]
        if not profit_str.endswith('.'):
            profit_str += '.'
    else:
        all_profit = [p[1] for p in profit_candidates]
        if all_profit:
            profit_str = all_profit[0]
            if not profit_str.endswith('.'):
                profit_str += '.'
        else:
            profit_str = "Финансовые показатели или потенциал окупаемости не описаны."
            
    return goal_str, tech_str, risk_str, profit_str

def fallback_segmentation(text: str) -> Dict[str, Any]:
    """Fallback segmenter using heuristic regex and extractive summary when Llama 3 is unavailable."""
    entities = heuristic_ner(text)
    
    budget_val = "Не указано"
    deadline_val = "Не указано"
    for ent in entities:
        if ent["type"] == "Budget" and budget_val == "Не указано":
            budget_val = ent["text"]
        elif ent["type"] == "Deadline" and deadline_val == "Не указано":
            deadline_val = ent["text"]

    domain_val = "Не указано"
    text_lower = text.lower()
    if any(w in text_lower for w in ["e-commerce", "интернет-магазин", "ритейл", "торговл", "маркетплейс", "товар"]):
        domain_val = "E-commerce / Ритейл"
    elif any(w in text_lower for w in ["финтех", "банк", "платёж", "финанс", "кредит", "транзакц"]):
        domain_val = "Финтех / Банки"
    elif any(w in text_lower for w in ["логистик", "доставк", "склад", "транспорт", "груз"]):
        domain_val = "Логистика / Транспорт"
    elif any(w in text_lower for w in ["медицин", "здрав", "клиник", "врач", "пациент"]):
        domain_val = "Медицина / Здравоохранение"

    goal_str, tech_str, risk_str, profit_str = extractive_summary(text, n_sentences=2)

    return {
        "meta_info": {
            "budget": budget_val,
            "timeline": deadline_val,
            "domain": domain_val
        },
        "sections": {
            "summary": goal_str,
            "architecture_and_tech": tech_str,
            "risks_and_security": risk_str,
            "business_and_finance": profit_str
        }
    }

def perform_gap_analysis(domain: str, detected_tech: List[str]) -> Dict[str, Any]:
    """Perform structural gap analysis comparing detected techs with domain best practices."""
    detected_lower = {t.lower() for t in detected_tech}
    
    missing_techs = []
    relevance_recs = []
    risk_recs = []
    
    dom = domain.lower()
    
    # Check general infrastructure (for all domains)
    if not any(t in detected_lower for t in ["docker", "kubernetes", "k8s", "контейнер"]):
        missing_techs.append("Docker")
        relevance_recs.append("Внедрить контейнеризацию (Docker) для обеспечения переносимости и изоляции сервисов.")
        
    if not any(t in detected_lower for t in ["ci/cd", "jenkins", "gitlab", "github", "автоматическ сборк"]):
        missing_techs.append("CI/CD Pipeline")
        relevance_recs.append("Настроить автоматизированный CI/CD пайплайн для стабильного развертывания и тестирования.")

    if not any(t in detected_lower for t in ["prometheus", "grafana", "elk", "loki", "логирования", "мониторинг"]):
        missing_techs.append("Monitoring (Prometheus/Grafana)")
        risk_recs.append("Отсутствуют инструменты мониторинга и логирования. Рекомендуется развернуть Prometheus и Grafana для контроля состояния системы.")

    # Domain specific gaps
    if "финтех" in dom or "банк" in dom:
        if not any(t in detected_lower for t in ["postgresql", "postgres", "oracle", "mysql", "mssql", "бд", "база данных"]):
            missing_techs.append("PostgreSQL")
            relevance_recs.append("Для транзакционных данных Финтех-платформы необходима надежная реляционная СУБД с поддержкой ACID (рекомендуется PostgreSQL).")
            
        if not any(t in detected_lower for t in ["kafka", "rabbitmq", "activemq", "брокер", "очеред"]):
            missing_techs.append("Kafka")
            relevance_recs.append("Для асинхронного межсервисного взаимодействия и обработки транзакций рекомендуется внедрить брокер сообщений Apache Kafka.")
            
        if not any(t in detected_lower for t in ["redis", "memcached", "кэш"]):
            missing_techs.append("Redis")
            relevance_recs.append("Использовать Redis для кэширования сессий пользователей и снижения нагрузки на основную базу данных.")
            
        if not any(t in detected_lower for t in ["api gateway", "kong", "nginx", "шлюз"]):
            missing_techs.append("API Gateway")
            relevance_recs.append("Внедрить API Gateway (например, Kong или Nginx) для авторизации, маршрутизации и защиты API от перегрузок.")
            
        if not any(t in detected_lower for t in ["ssl", "tls", "aes", "шифрован", "pci-dss", "cryptography"]):
            risk_recs.append("Критический риск безопасности: не описаны стандарты шифрования данных. Рекомендуется внедрить шифрование трафика (TLS) и конфиденциальных данных (AES) согласно стандарту PCI-DSS.")
            
    elif "e-commerce" in dom or "ритейл" in dom or "торговл" in dom or "маркетплейс" in dom:
        if not any(t in detected_lower for t in ["redis", "memcached", "кэш"]):
            missing_techs.append("Redis")
            relevance_recs.append("Для высоконагруженного интернет-магазина критически важно кэширование каталога товаров (рекомендуется Redis).")
            
        if not any(t in detected_lower for t in ["elasticsearch", "opensearch", "sphinx", "поиск"]):
            missing_techs.append("Elasticsearch")
            relevance_recs.append("Для быстрого и полнотекстового поиска по каталогу товаров рекомендуется интегрировать Elasticsearch.")
            
        if not any(t in detected_lower for t in ["kafka", "rabbitmq", "брокер", "очеред"]):
            missing_techs.append("RabbitMQ")
            relevance_recs.append("Рекомендуется использовать брокер сообщений (например, RabbitMQ) для асинхронной обработки заказов и уведомлений.")
            
        if not any(t in detected_lower for t in ["waf", "firewall", "ddos", "защит"]):
            risk_recs.append("Выявлен риск уязвимости к DDoS-атакам. Рекомендуется подключить Web Application Firewall (WAF) и защиту от DDoS-атак.")
            
    elif "логистик" in dom or "доставк" in dom or "транспорт" in dom:
        if not any(t in detected_lower for t in ["kafka", "rabbitmq", "брокер", "очеред"]):
            missing_techs.append("Kafka")
            relevance_recs.append("Для обработки потоков гео-координат и статусов доставки в реальном времени рекомендуется внедрить Apache Kafka.")
            
        if not any(t in detected_lower for t in ["maps", "карты", "гео", "osm", "openstreetmap"]):
            missing_techs.append("Yandex/OSM Maps API")
            relevance_recs.append("Для расчета маршрутов и визуализации курьеров необходима интеграция с картографическими сервисами (Yandex Maps API или OpenStreetMap).")
            
        if not any(t in detected_lower for t in ["redis", "кэш"]):
            missing_techs.append("Redis")
            relevance_recs.append("Рекомендуется кэшировать промежуточные гео-данные и частые маршруты в Redis.")
            
    elif "медицин" in dom or "здрав" in dom or "клиник" in dom:
        if not any(t in detected_lower for t in ["152-фз", "152 фз", "персональные данные", "шифрован", "защит"]):
            risk_recs.append("Критический риск несоответствия законодательству: не описаны меры защиты персональных данных согласно 152-ФЗ. Необходимо спроектировать защищенный контур ИСПДн.")
            
        if not any(t in detected_lower for t in ["postgresql", "postgres", "mysql", "oracle"]):
            missing_techs.append("PostgreSQL")
            relevance_recs.append("Для хранения медицинских карт и истории приемов необходима надежная СУБД (рекомендуется PostgreSQL) с включенным логированием изменений.")
            
        if not any(t in detected_lower for t in ["егисз", "интеграц", "api gateway"]):
            missing_techs.append("EGISZ Integration API")
            relevance_recs.append("Рекомендуется предусмотреть шлюз интеграции с государственной системой ЕГИСЗ.")

    unique_missing = []
    for m in missing_techs:
        if m.lower() not in detected_lower and m not in unique_missing:
            unique_missing.append(m)
            
    if not unique_missing:
        unique_missing = ["Redis", "Message Broker"]
        
    return {
        "missing_techs": unique_missing[:4],
        "relevance_recs": relevance_recs,
        "risk_recs": risk_recs
    }

# ==========================================
# Handlers
# ==========================================

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}

def generate_fallback_gap_analysis(text: str, detected_techs: List[str], entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    text_lower = text.lower()
    
    # 1. Metadata extraction
    project_name = None
    document_date = None
    deadline = None
    budget = None
    
    # Look for Project Name
    proj_patterns = [
        r"(?:название проекта|проект|система|платформа)\s*:\s*\"?([^\n\"]+)\"?",
        r"(?:разработка|создание)\s+(?:платформы|системы|сервиса)\s+([^\n.]+)"
    ]
    for p in proj_patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            project_name = match.group(1).strip()
            break
    if not project_name:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines and len(lines[0]) < 60 and not any(w in lines[0].lower() for w in ["тз", "техническое задание", "документ"]):
            project_name = lines[0]
            
    # Extract deadline and budget from entities
    for ent in entities:
        if ent["type"] == "Budget":
            budget = ent["text"]
        elif ent["type"] == "Deadline":
            deadline = ent["text"]
            
    # Look for dates
    date_pattern = re.compile(r'\b(\d{1,2}[\s.-]+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|\d{2})[\s.-]+\d{4})\b', re.IGNORECASE)
    date_matches = date_pattern.findall(text)
    if date_matches:
        document_date = date_matches[0]
        
    # Budget normalization (e.g. "10 млн рублей" -> "10000000 руб")
    if budget:
        budget_clean = budget.strip()
        num_match = re.search(r'(\d+(?:\.\d+)?)', budget_clean)
        if num_match:
            num = float(num_match.group(1))
            val = ""
            if "млн" in budget_clean or "миллион" in budget_clean:
                num = int(num * 1000000)
            elif "тыс" in budget_clean or "тысяч" in budget_clean:
                num = int(num * 1000)
            else:
                num = int(num)
            
            if any(w in budget_clean.lower() for w in ["руб", "₽"]):
                val = "руб"
            elif any(w in budget_clean.lower() for w in ["usd", "$", "доллар"]):
                val = "USD"
            else:
                val = "руб"
            budget = f"{num} {val}"
            
    # 2. Sections Classification & Statuses
    sentences = extract_sentences(text)
    
    purpose_text_sents = []
    architecture_text_sents = []
    risks_text_sents = []
    economics_text_sents = []
    
    for sent in sentences:
        s_lower = sent.lower()
        if any(w in s_lower for w in ["цель проекта", "создание платформы", "разработка системы", "назначение системы", "цели проекта", "разрабатываемая система"]):
            purpose_text_sents.append(sent)
        if any(w in s_lower for w in ["архитектура", "стек", "база данных", "бд", "интеграция", "микросервис", "разработк"]):
            architecture_text_sents.append(sent)
        if any(w in s_lower for w in ["риск", "угроз", "проблем", "сбой", "задержка", "уязвимост", "ошибк", "убыт"]):
            risks_text_sents.append(sent)
        if any(w in s_lower for w in ["окупаемость", "выгода", "эффективность", "прибыль", "доход", "бюджет", "затраты", "%", "стоимость"]):
            economics_text_sents.append(sent)
            
    # --- Purpose Section ---
    purpose_status = "missing"
    purpose_extracted = None
    purpose_gaps = []
    if purpose_text_sents:
        purpose_extracted = " ".join(purpose_text_sents[:3])
        if len(purpose_extracted) > 100:
            purpose_status = "present"
        else:
            purpose_status = "partial"
            purpose_gaps.append("Суть проекта описана слишком кратко, требуется детализация основных бизнес-целей.")
    else:
        purpose_gaps.append("Отсутствует явное описание целей и назначения разрабатываемой системы.")
        
    # --- Tech Stack Section ---
    tech_status = "missing"
    tech_gaps = []
    arch_desc = None
    if architecture_text_sents:
        arch_desc = " ".join(architecture_text_sents[:3])
        
    if detected_techs and arch_desc:
        tech_status = "present"
    elif detected_techs or arch_desc:
        tech_status = "partial"
        if not detected_techs:
            tech_gaps.append("Не указаны конкретные используемые технологии (языки, СУБД, фреймворки).")
        if not arch_desc:
            tech_gaps.append("Отсутствует описание архитектуры взаимодействия компонентов системы.")
    else:
        tech_gaps.append("Не описан стек технологий и архитектура взаимодействия компонентов.")
        
    # --- Risks Section ---
    risk_status = "missing"
    extracted_risks = []
    risk_gaps = []
    if risks_text_sents:
        risk_status = "partial"
        for r_sent in risks_text_sents[:4]:
            category = "Технический"
            r_lower = r_sent.lower()
            if any(w in r_lower for w in ["безопасн", "уязвим", "утек", "взлом"]):
                category = "Информационная безопасность"
            elif any(w in r_lower for w in ["интеграц", "внешн", "api", "api gateway"]):
                category = "Интеграционный"
            elif any(w in r_lower for w in ["окупаем", "бюджет", "убыт", "финанс"]):
                category = "Финансовый"
            extracted_risks.append({"text": r_sent, "category": category})
            
        if len(extracted_risks) >= 3:
            risk_status = "present"
        else:
            risk_gaps.append("Указаны отдельные риски, но отсутствует системная оценка вероятности и последствий сбоев.")
    else:
        risk_gaps.append("Критический пробел: в документе полностью отсутствуют риски, угрозы ИБ или возможные сбои.")
        
    # --- Economics Section ---
    econ_status = "missing"
    extracted_metrics = []
    econ_gaps = []
    if economics_text_sents:
        econ_status = "partial"
        for e_sent in economics_text_sents[:4]:
            pct_match = re.search(r'(\b\d+(?:\.\d+)?\s*%)', e_sent)
            val_match = re.search(r'(\b\d+(?:\.\d+)?\s*(?:млн|тыс\.)?\s*(?:руб|usd|\$))', e_sent, re.IGNORECASE)
            
            metric_name = "Показатель эффективности"
            metric_val = "Не определено"
            
            if "окупаем" in e_sent.lower():
                metric_name = "Срок окупаемости"
            elif "прибыль" in e_sent.lower() or "доход" in e_sent.lower():
                metric_name = "Ожидаемый доход/прибыль"
            elif "бюджет" in e_sent.lower():
                metric_name = "Бюджет проекта"
                
            if pct_match:
                metric_val = pct_match.group(1)
            elif val_match:
                metric_val = val_match.group(1)
            else:
                metric_val = e_sent[:40] + "..."
                
            extracted_metrics.append({"metric": metric_name, "value": metric_val})
            
        if len(extracted_metrics) >= 2 and budget:
            econ_status = "present"
        else:
            econ_gaps.append("Указаны финансовые маркеры, но отсутствует детальный расчет окупаемости и бизнес-выгод.")
    else:
        econ_gaps.append("Критический пробел: в документе не описана экономическая целесообразность, окупаемость или коммерческий потенциал.")
        
    # 3. Completeness score
    status_scores = {"present": 1.0, "partial": 0.5, "missing": 0.0}
    comp_score = (
        status_scores[purpose_status] * 0.2 +
        status_scores[tech_status] * 0.2 +
        status_scores[risk_status] * 0.3 +
        status_scores[econ_status] * 0.3
    ) * 100
    comp_score = round(comp_score, 1)
    
    # 4. Clarifying questions
    clarifying_questions = []
    if risk_status == "missing":
        clarifying_questions.append("Какие ключевые технические, интеграционные и операционные риски вы видите на проекте?")
    elif risk_status == "partial":
        clarifying_questions.append("Опишите меры по снижению рисков и планы восстановления системы после возможных сбоев.")
        
    if econ_status == "missing":
        clarifying_questions.append("Каков планируемый коммерческий эффект, срок окупаемости и ROI от внедрения системы?")
    elif econ_status == "partial":
        clarifying_questions.append("Уточните целевые экономические показатели (окупаемость, прибыльность) и структуру бюджета проекта.")
        
    if tech_status == "missing" or tech_status == "partial":
        if len(clarifying_questions) < 3:
            clarifying_questions.append("Опишите планируемую архитектуру взаимодействия микросервисов и требования к стеку технологий.")
            
    if purpose_status == "missing" or purpose_status == "partial":
        if len(clarifying_questions) < 3:
            clarifying_questions.append("Можете ли вы подробнее описать основную цель проекта и потребности его целевой аудитории?")
            
    clarifying_questions = clarifying_questions[:3]
    
    return {
        "metadata": {
            "project_name": project_name,
            "document_date": document_date,
            "deadline": deadline,
            "budget": budget
        },
        "sections": {
            "purpose": {
                "status": purpose_status,
                "extracted_text": purpose_extracted,
                "gaps": purpose_gaps
            },
            "tech_stack": {
                "status": tech_status,
                "extracted_technologies": detected_techs,
                "architecture_description": arch_desc,
                "gaps": tech_gaps
            },
            "risks": {
                "status": risk_status,
                "extracted_risks": extracted_risks,
                "gaps": risk_gaps
            },
            "economics": {
                "status": econ_status,
                "extracted_metrics": extracted_metrics,
                "gaps": econ_gaps
            }
        },
        "completeness_score": comp_score,
        "clarifying_questions": clarifying_questions
    }

def get_best_available_model() -> str:
    """Query the Ollama api/tags endpoint to dynamically choose the best available model."""
    base_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
    url = base_url.rstrip("/") + "/api/tags"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            logger.info(f"Available local Ollama models: {models}")
            
            # Prioritized list of models
            priority_list = [
                "qwen2.5:1.5b", "qwen2.5:1.5b-instruct",
                "qwen2.5:0.5b", "qwen2.5:0.5b-instruct",
                "qwen2.5:3b",
                "llama3.1:8b", "llama3.1",
                "llama3:8b", "llama3",
                "qwen2.5:7b",
                "gemma2:9b", "gemma2:2b",
                "mistral:7b", "phi3"
            ]
            for p_model in priority_list:
                for m in models:
                    if m == p_model or m.startswith(p_model + ":") or p_model.startswith(m + ":"):
                        logger.info(f"Selected Ollama model based on priority: {m}")
                        return m
            if models:
                logger.info(f"No prioritized model found. Using first available: {models[0]}")
                return models[0]
    except Exception as e:
        logger.warning(f"Ollama dynamic model check failed: {e}. Defaulting to 'llama3'.")
    return "llama3"

def query_ollama_template(text: str) -> Dict[str, Any]:
    """Query local Llama 3 via Ollama on the host machine to get structured document segments."""
    base_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
    url = base_url.rstrip("/") + "/api/generate"
    
    # Choose model dynamically
    model_name = get_best_available_model()
    logger.info(f"Ollama analysis using model: {model_name}")
    
    system_prompt = (
        "Ты — модуль анализа технической документации ИТ-проектов в составе платформы DocuAudit AI.\n"
        "Твоя задача — извлечь структурированные данные из произвольного текста документа, "
        "сопоставить их с эталонным шаблоном ТЗ и выявить пробелы (gaps), которые могут "
        "повлиять на оценку рисков и прибыльности проекта.\n\n"
        "Эталонная структура (целевой шаблон) покрывает 4 раздела:\n"
        "1. Суть проекта и цели (purpose) — маркеры: цель проекта, создание платформы, разработка системы.\n"
        "2. Технологический стек (tech_stack) — конкретные технологии + описание архитектуры.\n"
        "3. Ключевые риски (risks) — маркеры: риск, угроза, проблема, сбой, задержка интеграции.\n"
        "4. Экономический потенциал (economics) — маркеры: числовые показатели с %, окупаемость, выгоды.\n\n"
        "Дополнительные метаданные: название проекта, дата документа, дедлайн, бюджет (нормализуй в формат 'число + валюта').\n\n"
        "Правила:\n"
        "- Определяй принадлежность фрагментов по смыслу.\n"
        "- Не выдумывай данные, которых нет в тексте. Если информация отсутствует, указывай null или \"missing\".\n"
        "- Числовые показатели извлекай точно, без округления.\n"
        "- Вердикт и gaps формулируй на русском языке.\n"
        "- Расчет completeness_score (от 0.0 до 100.0) = (вес каждого раздела * степень заполненности) * 100.\n"
        "  Веса: Суть=0.2, Стек=0.2, Риски=0.3, Экономика=0.3. Степень заполненности: present=1.0, partial=0.5, missing=0.0.\n"
        "- Сформулируй 1-3 конкретных уточняющих вопроса для пользователя, чтобы закрыть самые критичные пробелы "
        "(приоритет — разделы Риски и Экономика).\n\n"
        "Верни ответ СТРОГО в формате JSON без разметки markdown:\n"
        "{\n"
        "  \"metadata\": {\n"
        "    \"project_name\": \"string | null\",\n"
        "    \"document_date\": \"string | null\",\n"
        "    \"deadline\": \"string | null\",\n"
        "    \"budget\": \"string | null\"\n"
        "  },\n"
        "  \"sections\": {\n"
        "    \"purpose\": {\n"
        "      \"status\": \"present | partial | missing\",\n"
        "      \"extracted_text\": \"string | null\",\n"
        "      \"gaps\": [\"string\"]\n"
        "    },\n"
        "    \"tech_stack\": {\n"
        "      \"status\": \"present | partial | missing\",\n"
        "      \"extracted_technologies\": [\"string\"],\n"
        "      \"architecture_description\": \"string | null\",\n"
        "      \"gaps\": [\"string\"]\n"
        "    },\n"
        "    \"risks\": {\n"
        "      \"status\": \"present | partial | missing\",\n"
        "      \"extracted_risks\": [\n"
        "        {\"text\": \"string\", \"category\": \"string | null\"}\n"
        "      ],\n"
        "      \"gaps\": [\"string\"]\n"
        "    },\n"
        "    \"economics\": {\n"
        "      \"status\": \"present | partial | missing\",\n"
        "      \"extracted_metrics\": [\n"
        "        {\"metric\": \"string\", \"value\": \"string\"}\n"
        "      ],\n"
        "      \"gaps\": [\"string\"]\n"
        "    }\n"
        "  },\n"
        "  \"completeness_score\": 0.0,\n"
        "  \"clarifying_questions\": [\"string\"]\n"
        "}"
    )

    # Truncate text to 20,000 characters to prevent Ollama timeouts and OOMs
    truncated_text = text[:20000]
    prompt = f"Системная инструкция:\n{system_prompt}\n\nАнализируемый документ:\n{truncated_text}"
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048,
            "num_ctx": 8192
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    # Increase HTTP read timeout to 90 seconds in Python as well, to allow slow inference
    with urllib.request.urlopen(req, timeout=90) as response:
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
    detected_techs = sorted(list(set(ent["text"] for ent in entities if ent["type"] == "Technology")))

    # 2. Phase 1: Preprocessing / Segmentation
    is_llama = False
    norm_doc = None
    gap_analysis_data = None
    try:
        logger.info("Attempting Llama 3 analysis via Ollama...")
        norm_doc = query_ollama_template(req.text)
        logger.info("✓ Llama 3 successfully parsed the document into template!")
        is_llama = True
        gap_analysis_data = norm_doc
        
        # Populate the old fields for ruBERT scoring
        budget_val = norm_doc.get("metadata", {}).get("budget") or "Не указано"
        timeline_val = norm_doc.get("metadata", {}).get("deadline") or "Не указано"
        
        # Determine domain
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
            
        summary_text = norm_doc.get("sections", {}).get("purpose", {}).get("extracted_text") or ""
        arch_text = norm_doc.get("sections", {}).get("tech_stack", {}).get("architecture_description") or ""
        
        risk_list = norm_doc.get("sections", {}).get("risks", {}).get("extracted_risks", [])
        risk_text = " ".join([r.get("text", "") for r in risk_list if isinstance(r, dict)])
        
        econ_list = norm_doc.get("sections", {}).get("economics", {}).get("extracted_metrics", [])
        profit_text = " ".join([f"{e.get('metric', '')}: {e.get('value', '')}" for e in econ_list if isinstance(e, dict)])
    except Exception as e:
        logger.warning(f"Llama 3 template parsing failed or timed out: {e}. Falling back to heuristic segmentation.")
        norm_doc = fallback_segmentation(req.text)
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
        gap_analysis_data = generate_fallback_gap_analysis(req.text, detected_techs, entities)

    # Ensure we fall back to raw sentences if Llama returned empty strings
    if not summary_text.strip():
        summary_text = req.text[:500]

    # 3. Phase 2: ruBERT Semantic Analysis & Scoring
    words = req.text.lower().split()
    word_count = max(len(words), 1)

    # Ensure precomputed anchors are ready
    global risk_emb_cache, profit_emb_cache, tech_emb_cache
    if risk_emb_cache is None or profit_emb_cache is None or tech_emb_cache is None:
        precompute_anchors()

    # -- Compute raw scores and clamp to get final percentages --
    # Risk
    risk_score = 0.5
    if risk_text.strip() and risk_emb_cache is not None:
        risk_text_emb = get_embedding(risk_text[:2000]).reshape(1, -1)
        sim_risk = cosine_similarity(risk_text_emb, risk_emb_cache)[0][0]
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
    if profit_text.strip() and profit_emb_cache is not None:
        profit_text_emb = get_embedding(profit_text[:2000]).reshape(1, -1)
        sim_profit = cosine_similarity(profit_text_emb, profit_emb_cache)[0][0]
        
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
    detected_techs = sorted(list(set(ent["text"] for ent in entities if ent["type"] == "Technology")))
    
    if arch_text.strip() and tech_emb_cache is not None:
        tech_text_emb = get_embedding(arch_text[:2000]).reshape(1, -1)
        sim_relevance = cosine_similarity(tech_text_emb, tech_emb_cache)[0][0]
        
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

    # 4. Phase 3: Detailed Gap Analysis
    gap_result = perform_gap_analysis(domain_val, detected_techs)
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

    # Append Gap Analysis specific recommendations
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
        entities=entities,
        gap_analysis=gap_analysis_data
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
