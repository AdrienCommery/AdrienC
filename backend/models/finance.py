from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class FinanceCalculationCreate(BaseModel):
    montantFinancer: str
    coefficientEmprunteur: str
    coefficientCoEmprunteur: str
    coefficientComplementaire: str
    extensionGarantie: str
    revision: str
    mensualiteEmprunteur: float
    mensualiteCoEmprunteur: float
    complementaire: float
    mensualitesTotales: float

class FinanceCalculation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    montantFinancer: str
    coefficientEmprunteur: str
    coefficientCoEmprunteur: str
    coefficientComplementaire: str
    extensionGarantie: str
    revision: str
    mensualiteEmprunteur: float
    mensualiteCoEmprunteur: float
    complementaire: float
    mensualitesTotales: float
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }