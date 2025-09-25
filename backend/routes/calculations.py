from fastapi import APIRouter, HTTPException, Depends
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.finance import FinanceCalculation, FinanceCalculationCreate
from database import get_database
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calculations", tags=["calculations"])

@router.get("/", response_model=List[FinanceCalculation])
async def get_calculations(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Récupère tous les calculs de financement triés par date de création (plus récent en premier)"""
    try:
        calculations = await db.finance_calculations.find().sort("createdAt", -1).to_list(1000)
        return [FinanceCalculation(**calc) for calc in calculations]
    except Exception as e:
        logger.error(f"Error fetching calculations: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des calculs")

@router.post("/", response_model=FinanceCalculation)
async def create_calculation(
    calculation_data: FinanceCalculationCreate, 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Sauvegarde un nouveau calcul de financement"""
    try:
        calculation = FinanceCalculation(**calculation_data.dict())
        calculation_dict = calculation.dict()
        
        # Insert into MongoDB
        result = await db.finance_calculations.insert_one(calculation_dict)
        
        if result.inserted_id:
            logger.info(f"New calculation saved with ID: {calculation.id}")
            return calculation
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
            
    except Exception as e:
        logger.error(f"Error creating calculation: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du calcul")

@router.delete("/{calculation_id}")
async def delete_calculation(
    calculation_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Supprime un calcul de financement par son ID"""
    try:
        result = await db.finance_calculations.delete_one({"id": calculation_id})
        
        if result.deleted_count == 1:
            logger.info(f"Calculation {calculation_id} deleted successfully")
            return {"message": "Calcul supprimé avec succès"}
        else:
            raise HTTPException(status_code=404, detail="Calcul non trouvé")
            
    except Exception as e:
        logger.error(f"Error deleting calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression du calcul")