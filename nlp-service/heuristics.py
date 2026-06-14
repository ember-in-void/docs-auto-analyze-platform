# ==========================================
# heuristics.py — Fallback Segmenters & Heuristics
# ==========================================
import re
import numpy as np
from typing import List, Dict, Any, Optional

def heuristic_ner(text: str) -> List[Dict[str, Any]]:
    """Simple dictionary and regex-based NER for fallback or bootstrapping."""
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
    """Fallback segmenter using heuristic regex and extractive summary when LLM is unavailable."""
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

def generate_fallback_gap_analysis(text: str, detected_techs: List[str], entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate fallback gap analysis structure using regular expressions."""
    text_lower = text.lower()
    
    project_name = None
    document_date = None
    deadline = None
    budget = None
    
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
            
    for ent in entities:
        if ent["type"] == "Budget":
            budget = ent["text"]
        elif ent["type"] == "Deadline":
            deadline = ent["text"]
            
    date_pattern = re.compile(r'\b(\d{1,2}[\s.-]+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|\d{2})[\s.-]+\d{4})\b', re.IGNORECASE)
    date_matches = date_pattern.findall(text)
    if date_matches:
        document_date = date_matches[0]
        
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
        
    status_scores = {"present": 1.0, "partial": 0.5, "missing": 0.0}
    comp_score = (
        status_scores[purpose_status] * 0.2 +
        status_scores[tech_status] * 0.2 +
        status_scores[risk_status] * 0.3 +
        status_scores[econ_status] * 0.3
    ) * 100
    comp_score = round(comp_score, 1)
    
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
    
    # Simple heuristic checks for advanced risk analysis
    integration_complexity = "Low"
    integration_gaps = []
    if any(w in text_lower for w in ["soap", "legacy", "wsdl", "файловый обмен", "xml"]):
        integration_complexity = "High"
        integration_gaps.append("Выявлено использование унаследованных протоколов обмена данными (SOAP/XML/файлы).")
    elif any(w in text_lower for w in ["интеграц", "api", "внешн", "обмен"]):
        integration_complexity = "Medium"
        integration_gaps.append("Требуется интеграция с внешними сервисами через API. Необходимо специфицировать контракты.")

    vendor_lock_risk = "Low"
    opex_infra_warnings = []
    if any(w in text_lower for w in ["oracle", "salesforce", "ms sql", "microsoft sql"]):
        vendor_lock_risk = "High"
        opex_infra_warnings.append("Использование проприетарного стека повышает риск вендор-лока и стоимость лицензий.")
    elif any(w in text_lower for w in ["облак", "aws", "azure", "yandex cloud"]):
        vendor_lock_risk = "Medium"
        opex_infra_warnings.append("Выявлена зависимость от инфраструктуры конкретного облачного провайдера.")

    architecture_suitability = "Suitable"
    if any(w in text_lower for w in ["highload", "нагруз", "миллион"]):
        if not any(t in text_lower for t in ["redis", "кэш", "балансировщик", "nginx"]):
            architecture_suitability = "Underengineered"

    feasibility_timeline = "Realistic"
    if deadline and deadline != "Не указано":
        feasibility_timeline = "Tight"

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
        "clarifying_questions": clarifying_questions,
        "integration_complexity": integration_complexity,
        "integration_gaps": integration_gaps,
        "vendor_lock_risk": vendor_lock_risk,
        "opex_infra_warnings": opex_infra_warnings,
        "architecture_suitability": architecture_suitability,
        "feasibility_timeline": feasibility_timeline
    }
