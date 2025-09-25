# TPL FINANCE - Contrats API et Architecture Backend

## 1. API Contracts

### Base URL
- Backend: `${REACT_APP_BACKEND_URL}/api`

### Endpoints

#### GET /api/calculations
**Description:** Récupère tous les calculs sauvegardés
**Response:**
```json
[
  {
    "id": "string",
    "date": "string", 
    "montantFinancer": "string",
    "coefficientEmprunteur": "string", 
    "coefficientCoEmprunteur": "string",
    "coefficientComplementaire": "string",
    "extensionGarantie": "string",
    "revision": "string",
    "mensualiteEmprunteur": number,
    "mensualiteCoEmprunteur": number,
    "complementaire": number,
    "mensualitesTotales": number,
    "createdAt": "ISO date string"
  }
]
```

#### POST /api/calculations
**Description:** Sauvegarde un nouveau calcul
**Request Body:**
```json
{
  "montantFinancer": "string",
  "coefficientEmprunteur": "string",
  "coefficientCoEmprunteur": "string", 
  "coefficientComplementaire": "string",
  "extensionGarantie": "string",
  "revision": "string",
  "mensualiteEmprunteur": number,
  "mensualiteCoEmprunteur": number,
  "complementaire": number,
  "mensualitesTotales": number
}
```

#### DELETE /api/calculations/:id
**Description:** Supprime un calcul par son ID

## 2. Données Mockées à Remplacer

### Frontend - `/app/frontend/src/utils/mock.js`
- Remplacer `mockCalculations` par des appels API réels
- Supprimer le fichier mock.js après intégration

### Frontend - `/app/frontend/src/components/FinanceCalculator.jsx`
- Remplacer `useEffect(() => { setSavedCalculations(mockCalculations); }, []);`
- Ajouter appel API `GET /api/calculations` au montage du composant
- Remplacer la sauvegarde locale par appel `POST /api/calculations`

## 3. Backend à Implémenter

### Models MongoDB
```python
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
```

### Routes à Créer
1. `GET /api/calculations` - Liste tous les calculs
2. `POST /api/calculations` - Sauvegarde un calcul  
3. `DELETE /api/calculations/{id}` - Supprime un calcul

### Collection MongoDB
- Nom: `finance_calculations`
- Index: `createdAt` (décroissant pour tri chronologique)

## 4. Intégration Frontend-Backend

### Étapes d'intégration:
1. Créer les modèles et routes backend
2. Tester les endpoints avec des données de test
3. Modifier le frontend pour utiliser les vraies APIs:
   - Importer axios pour les appels HTTP
   - Créer des fonctions d'API dans un fichier séparé
   - Remplacer les données mockées
   - Gérer les états de chargement et erreurs

### Fonctions Frontend à créer:
```javascript
// api/calculations.js
const getCalculations = async () => {...}
const saveCalculation = async (data) => {...}
const deleteCalculation = async (id) => {...}
```

### États à ajouter:
- `loading`: boolean pour les états de chargement
- `error`: string pour gérer les erreurs API

## 5. Fonctionnalités Supplémentaires

### Phase 1 (MVP):
- CRUD de base des calculs
- Historique chronologique

### Phase 2 (Améliorations futures possibles):
- Recherche par montant/date
- Export PDF des calculs
- Filtrage par période