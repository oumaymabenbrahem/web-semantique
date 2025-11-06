# Backend API - Tourisme Éco-responsable

API REST Flask avec RDFLib pour gérer l'ontologie de tourisme éco-responsable.

## Installation

```bash
pip install -r requirements.txt
```

## Démarrage

```bash
python app.py
```

L'API sera disponible sur `http://localhost:5000`

## Endpoints disponibles

### GET /api/health
Vérifier l'état de l'API

### GET /api/ontology/stats
Obtenir les statistiques de l'ontologie (nombre de classes, propriétés, individus)

### GET /api/destinations
Récupérer toutes les destinations

### GET /api/hebergements
Récupérer tous les hébergements avec leurs certifications

### GET /api/activites
Récupérer toutes les activités touristiques

### GET /api/transports
Récupérer tous les moyens de transport

### POST /api/query
Exécuter une requête SPARQL personnalisée

Body:
```json
{
  "query": "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
}
```

### POST /api/nl-query
Poser une question en langage naturel

Body:
```json
{
  "question": "Quelles sont toutes les destinations ?"
}
```

## Exemples de questions

- "Quelles sont toutes les destinations ?"
- "Quels hébergements ont une certification ?"
- "Quelles activités ont une faible empreinte carbone ?"
- "Quels sont les transports écologiques ?"
