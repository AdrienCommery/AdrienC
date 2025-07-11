from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
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
import tempfile
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import json

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
    ca_prime_progress: int  # Changed from float to int (number of vehicles)
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
        ca_prime_progress=vn_livres + vo_livres,  # Total vehicles sold (VN + VO)
        commission_vente=commission_vente,
        commission_financement=commission_financement
    )

@api_router.post("/export-pdf")
async def export_pdf_report(start_date: str = "2025-09-01", end_date: str = "2026-08-31"):
    try:
        # Get data
        stats_data = await get_period_stats(start_date, end_date)
        sales_data = await db.sales.find({
            "date_vente": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).to_list(1000)
        config_data = await db.commission_config.find_one()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            # Create PDF
            doc = SimpleDocTemplate(tmp_file.name, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph("SALESBOARD TPL - Rapport de Commissions", title_style))
            story.append(Spacer(1, 20))
            
            # Period
            period_style = ParagraphStyle(
                'Period',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER
            )
            story.append(Paragraph(f"Période: {start_date} au {end_date}", period_style))
            story.append(Spacer(1, 20))
            
            # Summary table
            summary_data = [
                ['Indicateur', 'Valeur'],
                ['VN Livrés', str(stats_data.vn_livres)],
                ['VO Livrés', str(stats_data.vo_livres)],
                ['Ventes Annulées', str(stats_data.ventes_annulees)],
                ['Taux d\'Annulation', f"{stats_data.taux_annulation}%"],
                ['CA Cumulé', f"{stats_data.ca_cumule:,.0f}€"],
                ['CA Mensuel', f"{stats_data.ca_mensuel:,.0f}€"],
                ['Véhicules ce mois', str(stats_data.vehicules_livres_ce_mois)],
                ['Progress Q1 Prime', f"{stats_data.q1_prime_progress}/35"],
                ['Progress CA Prime', f"{stats_data.ca_prime_progress}/90 véhicules"],
                ['Commission Vente', f"{stats_data.commission_vente:,.0f}€"],
                ['Commission Financement', f"{stats_data.commission_financement:,.0f}€"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Sales details
            story.append(Paragraph("Détail des Ventes", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            if sales_data:
                sales_table_data = [['Client', 'Type', 'Marque', 'Prix', 'Date', 'Statut']]
                for sale in sales_data:
                    status = "Annulée" if sale.get('annulation', False) else "Active"
                    sales_table_data.append([
                        f"{sale['nom']} {sale['prenom']}",
                        sale['type'],
                        f"{sale['marque']} {sale['modele']}",
                        f"{sale['prix_vente']:,.0f}€",
                        sale['date_vente'],
                        status
                    ])
                
                sales_table = Table(sales_table_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
                sales_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(sales_table)
            else:
                story.append(Paragraph("Aucune vente trouvée pour cette période.", styles['Normal']))
            
            # Add page break
            story.append(PageBreak())
            
            # Configuration page
            story.append(Paragraph("Configuration des Commissions", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            if config_data:
                config_table_data = [
                    ['Paramètre', 'Valeur'],
                    ['Taux CAMPING-CAR', f"{config_data.get('camping_car_rate', 0.055)*100}%"],
                    ['Taux FOURGON/VAN', f"{config_data.get('fourgon_van_rate', 0.065)*100}%"],
                    ['Prime Q1 (montant)', f"{config_data.get('q1_prime_amount', 1500)}€"],
                    ['Prime Q1 (objectif)', f"{config_data.get('q1_prime_target', 35)} ventes"],
                    ['', ''],
                    ['Taux Financement', ''],
                    ['0 PC', f"{config_data.get('financing_rates', {}).get('0', 0.005)*100}%"],
                    ['1 PC', f"{config_data.get('financing_rates', {}).get('1', 0.060)*100}%"],
                    ['2 PC', f"{config_data.get('financing_rates', {}).get('2', 0.065)*100}%"],
                    ['3 PC', f"{config_data.get('financing_rates', {}).get('3', 0.075)*100}%"],
                    ['4 PC', f"{config_data.get('financing_rates', {}).get('4', 0.080)*100}%"],
                    ['', ''],
                    ['Seuils Prime CA', ''],
                    ['50 véhicules', f"{config_data.get('ca_prime_thresholds', {}).get('50', 5000)}€"],
                    ['60 véhicules', f"{config_data.get('ca_prime_thresholds', {}).get('60', 6000)}€"],
                    ['70 véhicules', f"{config_data.get('ca_prime_thresholds', {}).get('70', 7000)}€"],
                    ['90 véhicules', f"{config_data.get('ca_prime_thresholds', {}).get('90', 11000)}€"]
                ]
                
                config_table = Table(config_table_data, colWidths=[3*inch, 2*inch])
                config_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(config_table)
            
            # Build PDF
            doc.build(story)
            
            # Return file
            return FileResponse(
                tmp_file.name,
                media_type='application/pdf',
                filename=f"salesboard_report_{start_date}_{end_date}.pdf"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@api_router.get("/commission-rates")
async def get_commission_rates():
    """Get detailed commission rates for the configuration page"""
    config = await db.commission_config.find_one()
    if not config:
        config = CommissionConfig().dict()
    
    return {
        "payplan_rates": {
            "camping_car": config.get('camping_car_rate', 0.055),
            "fourgon_van": config.get('fourgon_van_rate', 0.065)
        },
        "financing_rates": config.get('financing_rates', {
            "0": 0.005,
            "1": 0.060,
            "2": 0.065,
            "3": 0.075,
            "4": 0.080
        }),
        "q1_prime": {
            "amount": config.get('q1_prime_amount', 1500.0),
            "target": config.get('q1_prime_target', 35)
        },
        "ca_prime_thresholds": config.get('ca_prime_thresholds', {
            "50": 5000,
            "60": 6000,
            "70": 7000,
            "90": 11000
        })
    }

@api_router.put("/commission-rates")
async def update_commission_rates(rates: dict):
    """Update commission rates from the configuration page"""
    try:
        # Get current config
        config = await db.commission_config.find_one()
        if not config:
            config = CommissionConfig().dict()
        
        # Update rates
        if 'payplan_rates' in rates:
            config['camping_car_rate'] = rates['payplan_rates'].get('camping_car', 0.055)
            config['fourgon_van_rate'] = rates['payplan_rates'].get('fourgon_van', 0.065)
        
        if 'financing_rates' in rates:
            config['financing_rates'] = rates['financing_rates']
        
        if 'q1_prime' in rates:
            config['q1_prime_amount'] = rates['q1_prime']['amount']
            config['q1_prime_target'] = rates['q1_prime']['target']
        
        if 'ca_prime_thresholds' in rates:
            config['ca_prime_thresholds'] = rates['ca_prime_thresholds']
        
        # Save to database
        await db.commission_config.replace_one(
            {"id": config["id"]},
            config,
            upsert=True
        )
        
        return {"message": "Commission rates updated successfully", "config": config}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating rates: {str(e)}")

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