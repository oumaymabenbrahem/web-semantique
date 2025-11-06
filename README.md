# Projet Web Sémantique - Tourisme Éco-Responsable

Application web complète utilisant une ontologie OWL pour le tourisme éco-responsable, avec une architecture moderne basée sur Angular, Flask et RDFLib.

## 🏗️ Architecture

```
Frontend (Angular)
    ↓
API REST
    ↓
Backend (Python + Flask + RDFLib)
    ↓
Ontologie OWL (ws.rdf)
    ↓ (Optionnel)
Apache Jena Fuseki
```

## 📁 Structure du Projet

```
web semantique/
├── ws.rdf                    # Ontologie OWL
├── backend/                  # Backend Python + Flask
│   ├── app.py               # API REST
│   ├── requirements.txt     # Dépendances Python
│   └── README.md
├── frontend/                 # Frontend Angular
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── dashboard/   # Tableau de bord
│   │   │   │   └── query/       # Interface de requêtage
│   │   │   └── services/
│   │   │       └── ontology.service.ts
│   │   └── ...
│   └── package.json
└── README.md                 # Ce fichier
```

## 🚀 Installation et Démarrage

### Prérequis

- **Node.js** (v18+) et npm
- **Python** (v3.8+)
- **Angular CLI** (installé automatiquement)

### 1. Backend Python

```powershell
# Se placer dans le dossier backend
cd backend

# Installer les dépendances Python
pip install -r requirements.txt

# Démarrer le serveur backend
python app.py
```

Le backend sera disponible sur `http://localhost:5000`

### 2. Frontend Angular

```powershell
# Ouvrir un nouveau terminal
# Se placer dans le dossier frontend
cd frontend

# Installer les dépendances npm
npm install

# Démarrer le serveur de développement
npm start
```

Le frontend sera disponible sur `http://localhost:4200`

### 3. Ouvrir l'application

Ouvrez votre navigateur et allez sur `http://localhost:4200`

## 📊 Ontologie

L'ontologie `ws.rdf` décrit le domaine du **tourisme éco-responsable** avec :

### Classes principales
- **Destination** : Destinations touristiques (urbaine, rurale, côtière, insulaire, montagneuse)
- **Hébergement** : Types d'hébergement (hôtel, camping, maison d'hôtes, village vacances)
- **ActivitéTouristique** : Activités (randonnée, camping écologique, visites de musées, etc.)
- **Transport** : Moyens de transport (train, taxi, vélo)
- **CertificationÉco** : Certifications écologiques (ISO14001, etc.)
- **EmpreinteCarbone** : Mesure de l'impact environnemental
- **Personne** : Voyageurs, guides, chauffeurs, organisateurs

### Propriétés d'objet
- `choisitDestination`, `séjourneDans`, `participeÀ`
- `utilise`, `propose`, `contient`
- `possèdeCertification`, `aEmpreinteCarbone`

### Propriétés de données
- `nomDestination`, `nomHebergement`, `nomActivité`
- `empreinte` (float), `duree` (integer)
- `age`, `nomVoyageur`

## 🔧 Fonctionnalités

### Tableau de bord
- Statistiques de l'ontologie (classes, propriétés, individus)
- Liste des destinations
- Liste des hébergements avec certifications
- Liste des activités touristiques avec empreintes carbone
- Liste des transports

### Interface de requêtage
- Poser des questions en langage naturel
- Questions prédéfinies disponibles
- Affichage de la requête SPARQL générée
- Présentation des résultats sous forme de tableau

### Questions exemples
- "Quelles sont toutes les destinations ?"
- "Quels hébergements ont une certification ?"
- "Quelles activités ont une faible empreinte carbone ?"
- "Quels sont les transports écologiques ?"

## 🔌 API Endpoints

### GET `/api/health`
Vérifier l'état de l'API

### GET `/api/ontology/stats`
Statistiques de l'ontologie

### GET `/api/destinations`
Liste toutes les destinations

### GET `/api/hebergements`
Liste tous les hébergements

### GET `/api/activites`
Liste toutes les activités touristiques

### GET `/api/transports`
Liste tous les moyens de transport

### POST `/api/query`
Exécute une requête SPARQL personnalisée

Body:
```json
{
  "query": "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
}
```

### POST `/api/nl-query`
Convertit une question en langage naturel en requête SPARQL

Body:
```json
{
  "question": "Quelles sont toutes les destinations ?"
}
```

## 🎨 Technologies Utilisées

### Frontend
- **Angular 19** - Framework web moderne
- **TypeScript** - Langage typé
- **RxJS** - Programmation réactive
- **CSS3** - Styles personnalisés

### Backend
- **Flask** - Framework web Python
- **RDFLib** - Manipulation d'ontologies RDF/OWL
- **Flask-CORS** - Gestion des requêtes cross-origin
- **SPARQLWrapper** - Exécution de requêtes SPARQL

### Ontologie
- **OWL** - Web Ontology Language
- **RDF/XML** - Format de sérialisation
- **SPARQL** - Langage de requête

## 📝 Notes

- L'ontologie est chargée directement depuis le fichier `ws.rdf`
- Le backend utilise RDFLib pour parser et interroger l'ontologie
- Les requêtes SPARQL sont exécutées en mémoire
- Possibilité d'intégrer Apache Jena Fuseki pour des performances accrues

## 🚀 Prochaines étapes

1. **Intégration Fuseki** : Déployer l'ontologie sur Apache Jena Fuseki
2. **NLP avancé** : Améliorer la conversion langage naturel → SPARQL
3. **Visualisations** : Ajouter des graphes et visualisations interactives
4. **Inférences** : Utiliser un raisonneur OWL pour déduire de nouvelles connaissances
5. **Interface d'édition** : Permettre l'ajout/modification de données dans l'ontologie

## 📄 Licence

Projet académique - Web Sémantique

## 👥 Auteur

Projet créé pour démonstrer l'utilisation des technologies du web sémantique dans une application réelle.
