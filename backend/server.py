from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class VehicleType(str, Enum):
    CAMPING_CAR = "CAMPING-CAR"
    FOURGON = "FOURGON"
    VAN = "VAN"

# Models
class Sale(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    prenom: str
    type: VehicleType
    marque: str
    modele: str
    date_vente: str  # Changed from date to str
    date_livraison_previsionnelle: str  # Changed from date to str
    prix_vente: float
    montant_financement: float
    nombre_pc: int
    annulation: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SaleCreate(BaseModel):
    nom: str
    prenom: str
    type: VehicleType
    marque: str
    modele: str
    date_vente: str  # Changed from date to str
    date_livraison_previsionnelle: str  # Changed from date to str
    prix_vente: float
    montant_financement: float
    nombre_pc: int
    annulation: bool = False

class CommissionConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camping_car_rate: float = 0.055
    fourgon_van_rate: float = 0.065
    financing_rates: dict = {
        "0": 0.005,
        "1": 0.060,
        "2": 0.065,
        "3": 0.075,
        "4": 0.080
    }
    q1_prime_amount: float = 1500.0
    q1_prime_target: int = 35
    ca_prime_thresholds: dict = {
        "50": 5000,   # 50 véhicules → 5000€
        "60": 6000,   # 60 véhicules → 6000€
        "70": 7000,   # 70 véhicules → 7000€
        "90": 11000   # 90 véhicules → 11000€
    }

class PeriodStats(BaseModel):
    vn_livres: int
    vo_livres: int
    ventes_annulees: int
    taux_annulation: float
    ca_cumule: float
    ca_mensuel: float
    vehicules_livres_ce_mois: int
    q1_prime_progress: int
    ca_prime_progress: float
    commission_vente: float
    commission_financement: float

# Routes
@api_router.get("/")
async def root():
    return {"message": "SALESBOARD TPL API"}

@api_router.post("/sales", response_model=Sale)
async def create_sale(sale: SaleCreate):
    sale_dict = sale.dict()
    sale_obj = Sale(**sale_dict)
    # Convert the pydantic model to dict and ensure datetime is serializable
    sale_data = sale_obj.dict()
    sale_data['created_at'] = sale_data['created_at'].isoformat()
    await db.sales.insert_one(sale_data)
    return sale_obj

@api_router.get("/sales", response_model=List[Sale])
async def get_sales():
    sales = await db.sales.find().to_list(1000)
    return [Sale(**sale) for sale in sales]

@api_router.put("/sales/{sale_id}", response_model=Sale)
async def update_sale(sale_id: str, sale: SaleCreate):
    sale_dict = sale.dict()
    result = await db.sales.update_one(
        {"id": sale_id},
        {"$set": sale_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    updated_sale = await db.sales.find_one({"id": sale_id})
    return Sale(**updated_sale)

@api_router.delete("/sales/{sale_id}")
async def delete_sale(sale_id: str):
    result = await db.sales.delete_one({"id": sale_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sale not found")
    return {"message": "Sale deleted successfully"}

@api_router.get("/config", response_model=CommissionConfig)
async def get_commission_config():
    config = await db.commission_config.find_one()
    if not config:
        # Create default config
        default_config = CommissionConfig()
        config_data = default_config.dict()
        await db.commission_config.insert_one(config_data)
        return default_config
    return CommissionConfig(**config)

@api_router.put("/config", response_model=CommissionConfig)
async def update_commission_config(config: CommissionConfig):
    config_dict = config.dict()
    await db.commission_config.replace_one(
        {"id": config.id},
        config_dict,
        upsert=True
    )
    return config

@api_router.get("/stats")
async def get_period_stats(start_date: str = "2025-09-01", end_date: str = "2026-08-31"):
    try:
        # Validate date format
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get sales in period
    sales = await db.sales.find({
        "date_vente": {
            "$gte": start_date,
            "$lte": end_date
        }
    }).to_list(1000)
    
    # Get commission config
    config = await db.commission_config.find_one()
    if not config:
        config = CommissionConfig().dict()
    
    # Calculate stats
    total_sales = len(sales)
    cancelled_sales = len([s for s in sales if s.get('annulation', False)])
    non_cancelled_sales = [s for s in sales if not s.get('annulation', False)]
    
    # Count vehicle types
    vn_livres = len([s for s in non_cancelled_sales if s['type'] == 'CAMPING-CAR'])
    vo_livres = len([s for s in non_cancelled_sales if s['type'] in ['FOURGON', 'VAN']])
    
    # Calculate CA
    ca_cumule = sum(s['prix_vente'] for s in non_cancelled_sales)
    
    # Current month stats
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_sales = [s for s in non_cancelled_sales 
                    if datetime.strptime(s['date_vente'], "%Y-%m-%d").month == current_month 
                    and datetime.strptime(s['date_vente'], "%Y-%m-%d").year == current_year]
    
    ca_mensuel = sum(s['prix_vente'] for s in monthly_sales)
    vehicules_livres_ce_mois = len(monthly_sales)
    
    # Q1 progress (Sept 1 - Dec 31, 2025)
    q1_end = datetime(2025, 12, 31)
    q1_sales = [s for s in non_cancelled_sales 
                if datetime.strptime(s['date_vente'], "%Y-%m-%d") <= q1_end]
    q1_progress = len(q1_sales)
    
    # Commission calculations
    commission_vente = 0
    commission_financement = 0
    
    for sale in non_cancelled_sales:
        # Sales commission
        if sale['type'] == 'CAMPING-CAR':
            commission_vente += sale['prix_vente'] * config.get('camping_car_rate', 0.055)
        else:
            commission_vente += sale['prix_vente'] * config.get('fourgon_van_rate', 0.065)
        
        # Financing commission
        pc_count = str(min(sale['nombre_pc'], 4))  # Max 4 PC
        financing_rate = config.get('financing_rates', {}).get(pc_count, 0.005)
        commission_financement += sale['montant_financement'] * financing_rate
    
    # Calculate rates
    taux_annulation = (cancelled_sales / total_sales * 100) if total_sales > 0 else 0
    
    return PeriodStats(
        vn_livres=vn_livres,
        vo_livres=vo_livres,
        ventes_annulees=cancelled_sales,
        taux_annulation=round(taux_annulation, 2),
        ca_cumule=ca_cumule,
        ca_mensuel=ca_mensuel,
        vehicules_livres_ce_mois=vehicules_livres_ce_mois,
        q1_prime_progress=q1_progress,
        ca_prime_progress=ca_cumule,
        commission_vente=commission_vente,
        commission_financement=commission_financement
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()