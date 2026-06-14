# ==========================================
# package-level documentation
# ==========================================
"""
Package llm provides access to the local Ollama LLM service.
It manages document segmentation, metadata extraction, gap analysis,
named entity recognition (NER), and programmatic offset recovery.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger("nlp-service.llm")

# ==========================================
# Constants
# ==========================================
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434").rstrip("/")

# ==========================================
# Helper Functions
# ==========================================

async def get_best_available_model(client: httpx.AsyncClient) -> str:
    """
    Query Ollama's tags endpoint to choose the best available model.
    Prioritizes lightweight models suited for CPU/low-end GPU hosting.
    """
    url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        response = await client.get(url, timeout=3.0)
        if response.status_code == 200:
            data = response.json()
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
                        logger.info(f"Selected Ollama model: {m}")
                        return m
            if models:
                logger.info(f"Using first available model: {models[0]}")
                return models[0]
    except Exception as e:
        logger.warning(f"Ollama tags check failed: {e}. Defaulting to 'llama3'.")
    return "llama3"


def sanitize_parsed_json(data: Any) -> Any:
    """Recursively clean up placeholder strings (like 'string | null') from LLM response."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, str):
                v_strip = v.strip().lower()
                if v_strip in ["string | null", "string", "null", "<string>", "[string]"]:
                    cleaned[k] = None
                elif v_strip == "present | partial | missing":
                    cleaned[k] = "missing"
                else:
                    cleaned[k] = v
            else:
                cleaned[k] = sanitize_parsed_json(v)
        return cleaned
    elif isinstance(data, list):
        cleaned = []
        for item in data:
            if isinstance(item, str):
                item_strip = item.strip().lower()
                if item_strip in ["string", "string | null", "null", "<string>", "название технологии", "строка с описанием пробела", "строка с вопросом"]:
                    continue
                cleaned.append(item)
            elif isinstance(item, dict):
                # Defensive parsing: if LLM returned dictionary instead of plain string inside list
                if "question" in item and isinstance(item["question"], str):
                    cleaned.append(item["question"])
                elif "text" in item and "category" not in item and isinstance(item["text"], str):
                    cleaned.append(item["text"])
                else:
                    cleaned.append(sanitize_parsed_json(item))
            else:
                cleaned.append(sanitize_parsed_json(item))
        return cleaned
    return data

# ==========================================
# Offset Recovery
# ==========================================

def recover_entity_offsets(text: str, extracted_entities: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Finds start and end character offsets for entities extracted by the LLM.
    Uses case-insensitive substring matching and prevents overlaps.
    
    Args:
        text: The original document text.
        extracted_entities: List of dicts with keys 'text' and 'type'.
        
    Returns:
        List of dicts with keys 'text', 'type', 'start', 'end'.
    """
    if not text or not extracted_entities:
        return []
        
    # Remove duplicates from extracted entities
    seen_entities = set()
    unique_entities = []
    for ent in extracted_entities:
        t = ent.get("text", "").strip()
        t_type = ent.get("type", "").strip()
        if not t or not t_type:
            continue
        key = (t.lower(), t_type.lower())
        if key not in seen_entities:
            seen_entities.add(key)
            unique_entities.append({"text": t, "type": t_type})
            
    # Sort by length descending to match longer entities first
    unique_entities.sort(key=lambda x: len(x["text"]), reverse=True)
    
    recovered = []
    occupied_spans = [] # list of (start, end)
    
    def is_overlapping(start: int, end: int) -> bool:
        for o_start, o_end in occupied_spans:
            if not (end <= o_start or start >= o_end):
                return True
        return False

    for ent in unique_entities:
        ent_text = ent["text"]
        ent_type = ent["type"]
        
        # Try case-sensitive first, then case-insensitive
        matches = list(re.finditer(re.escape(ent_text), text))
        if not matches:
            matches = list(re.finditer(re.escape(ent_text), text, re.IGNORECASE))
            
        found = False
        for match in matches:
            start = match.start()
            end = match.end()
            if not is_overlapping(start, end):
                recovered.append({
                    "text": text[start:end],
                    "type": ent_type,
                    "start": start,
                    "end": end
                })
                occupied_spans.append((start, end))
                found = True
                break
                
        # Fallback to whitespace normalization if exact match not found
        if not found:
            clean_ent_text = re.sub(r'\s+', ' ', ent_text).strip()
            words = [re.escape(w) for w in clean_ent_text.split() if w]
            if words:
                pattern = r'\s+'.join(words)
                try:
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                    for match in matches:
                        start = match.start()
                        end = match.end()
                        if not is_overlapping(start, end):
                            recovered.append({
                                "text": text[start:end],
                                "type": ent_type,
                                "start": start,
                                "end": end
                            })
                            occupied_spans.append((start, end))
                            found = True
                            break
                except Exception:
                    pass

    recovered.sort(key=lambda x: x["start"])
    return recovered

# ==========================================
# Core LLM Query Logic
# ==========================================

async def query_ollama_template(text: str) -> Dict[str, Any]:
    """
    Query local LLM via Ollama to get structured document segments and extracted entities.
    
    Args:
        text: Original document text.
        
    Returns:
        A dictionary containing the parsed templates, completeness scores, and extracted entities.
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        model_name = await get_best_available_model(client)
        logger.info(f"Ollama analysis using model: {model_name}")
        
        system_prompt = (
            "Ты — модуль анализа технической документации ИТ-проектов в составе платформы DocuAudit AI.\n"
            "Твоя задача — извлечь структурированные данные из произвольного текста документа, "
            "сопоставить их с эталонным шаблоном ТЗ, выявить пробелы (gaps), извлечь именованные сущности (NER), "
            "а также выполнить глубокий анализ архитектуры, интеграций и инфраструктурных затрат.\n\n"
            "Эталонная структура (целевой шаблон) покрывает 4 раздела:\n"
            "1. Суть проекта и цели (purpose) — маркеры: цель проекта, создание платформы, разработка системы.\n"
            "2. Технологический стек (tech_stack) — конкретные технологии + описание архитектуры.\n"
            "3. Ключевые риски (risks) — маркеры: риск, угроза, проблема, сбой, задержка интеграции.\n"
            "4. Экономический потенциал (economics) — маркеры: числовые показатели с %, окупаемость, выгоды.\n\n"
            "Дополнительные метаданные: название проекта, дата документа, дедлайн, бюджет (нормализуй в формат 'число + оригинальная валюта из текста', например '5000000 руб', ни в коем случае не конвертируй в доллары автоматически!).\n\n"
            "Именованные сущности (NER) для извлечения:\n"
            "- Technology: Названия языков программирования, баз данных, фреймворков, облачных провайдеров (например, React, Golang, PostgreSQL, Docker, Kubernetes).\n"
            "- Budget: Суммы финансирования, стоимости работ, бюджеты проектов (например, '5 млн рублей', '10 000 000 руб', '$150,000').\n"
            "- Deadline: Даты сдачи, сроки этапов работ, дедлайны (например, '15 декабря 2026', '30.11.2026').\n"
            "- Organization: Названия компаний, заказчиков, исполнителей (например, 'ООО \"Ромашка\"', 'ПАО \"Сбербанк\"').\n\n"
            "Проведи экспертный аудит рисков и затрат:\n"
            "- integration_complexity: Оцени сложность интеграции с внешними/legacy системами (Low если нет интеграций, Medium если есть стандартные API, High если есть унаследованные системы, закрытые протоколы, SOAP, файлы).\n"
            "- integration_gaps: Список найденных проблем интеграции (например, отсутствие описания API, отсутствие схем данных, использование старых протоколов).\n"
            "- vendor_lock_risk: Оцени риск вендор-лока (Low если стек на Open Source, Medium если есть облачные зависимости, High при использовании Oracle DB, MS SQL Server, Salesforce, 1С без возможности миграции).\n"
            "- opex_infra_warnings: Выяви предупреждения по скрытым затратам на инфраструктуру, лицензии, облака и поддержку (например, платные лицензии на БД, необходимость SLA 99.9% с дорогими серверами, платный трафик).\n"
            "- architecture_suitability: Соответствие стека масштабу проекта (Suitable — соответствует, Overengineered — стек слишком сложен для простых целей, Underengineered — стек не выдержит заявленную нагрузку или не покрывает функционал).\n"
            "- feasibility_timeline: Реалистичность сроков (Realistic — сроки адекватны, Tight — сроки сжатые, есть риск задержки, Unrealistic — сроки невыполнимы для заявленного объема работ).\n\n"
            "Правила:\n"
            "- Не выдумывай данные, которых нет в тексте. Если информация отсутствует, указывай null.\n"
            "- Числовые показатели извлекай точно, без округления.\n"
            "- Вердикт и gaps формулируй на русском языке.\n"
            "- Расчет completeness_score (от 0.0 до 100.0) = (вес каждого раздела * степень заполненности) * 100.\n"
            "  Веса: Суть=0.2, Стек=0.2, Риски=0.3, Экономика=0.3. Степень заполненности: present=1.0, partial=0.5, missing=0.0.\n"
            "- Сформулируй 1-3 конкретных уточняющих вопроса для пользователя, чтобы закрыть самые критичные пробелы "
            "(приоритет — разделы Риски и Экономика).\n\n"
            "Верни ответ СТРОГО в формате JSON без разметки markdown:\n"
            "{\n"
            "  \"metadata\": {\n"
            "    \"project_name\": null,\n"
            "    \"document_date\": null,\n"
            "    \"deadline\": null,\n"
            "    \"budget\": null\n"
            "  },\n"
            "  \"sections\": {\n"
            "    \"purpose\": {\n"
            "      \"status\": \"present | partial | missing\",\n"
            "      \"extracted_text\": null,\n"
            "      \"gaps\": [\"строка с описанием пробела\"]\n"
            "    },\n"
            "    \"tech_stack\": {\n"
            "      \"status\": \"present | partial | missing\",\n"
            "      \"extracted_technologies\": [\"название технологии\"],\n"
            "      \"architecture_description\": null,\n"
            "      \"gaps\": [\"строка с описанием пробела\"]\n"
            "    },\n"
            "    \"risks\": {\n"
            "      \"status\": \"present | partial | missing\",\n"
            "      \"extracted_risks\": [\n"
            "        {\"text\": \"текст риска\", \"category\": null}\n"
            "      ],\n"
            "      \"gaps\": [\"строка с описанием пробела\"]\n"
            "    },\n"
            "    \"economics\": {\n"
            "      \"status\": \"present | partial | missing\",\n"
            "      \"extracted_metrics\": [\n"
            "        {\"metric\": \"название показателя\", \"value\": \"значение\"}\n"
            "      ],\n"
            "      \"gaps\": [\"строка с описанием пробела\"]\n"
            "    }\n"
            "  },\n"
            "  \"completeness_score\": 0.0,\n"
            "  \"clarifying_questions\": [\"строка с вопросом\"],\n"
            "  \"entities\": [\n"
            "    {\"text\": \"текст сущности\", \"type\": \"Technology | Budget | Deadline | Organization\"}\n"
            "  ],\n"
            "  \"integration_complexity\": \"Low | Medium | High\",\n"
            "  \"integration_gaps\": [\"описание проблемы\"],\n"
            "  \"vendor_lock_risk\": \"Low | Medium | High\",\n"
            "  \"opex_infra_warnings\": [\"описание предупреждения\"],\n"
            "  \"architecture_suitability\": \"Suitable | Overengineered | Underengineered\",\n"
            "  \"feasibility_timeline\": \"Realistic | Tight | Unrealistic\"\n"
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
        
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Ollama request failed with status {response.status_code}: {response.text}")
            
        res_data = response.json()
        response_text = res_data.get("response", "")
        parsed = json.loads(response_text)
        return sanitize_parsed_json(parsed)
