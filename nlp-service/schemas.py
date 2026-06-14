# ==========================================
# schemas.py — Pydantic Schemas
# ==========================================
from typing import List, Optional, Any
from pydantic import BaseModel

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
    integration_complexity: Optional[str] = None
    integration_gaps: List[str] = []
    vendor_lock_risk: Optional[str] = None
    opex_infra_warnings: List[str] = []
    architecture_suitability: Optional[str] = None
    feasibility_timeline: Optional[str] = None

class AnalysisResult(BaseModel):
    meta_info: MetaInfo
    executive_summary: str
    tech_stack: TechStack
    metrics: List[Metric]
    entities: List[Entity]
    gap_analysis: Optional[GapAnalysisResult] = None
