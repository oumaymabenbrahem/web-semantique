from flask import Flask, request, jsonify
from flask_cors import CORS
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL, XSD
from rdflib.plugins.sparql import prepareQuery
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
import re
import requests
from types import SimpleNamespace

# Forcer l'encodage UTF-8 pour la console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration Google Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Utiliser Gemini 2.5 Flash (rapide et gratuit)
        gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
        print("✅ Google Gemini AI configurée avec succès! (modèle: gemini-2.5-flash)")
    except Exception as e:
        gemini_model = None
        print(f"⚠️ Erreur configuration Gemini: {e}")
else:
    gemini_model = None
    print("⚠️ ATTENTION: Clé API Gemini non configurée. L'IA ne sera pas disponible.")

# Namespace de l'ontologie
NS = Namespace("http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#")

# Configuration Fuseki
FUSEKI_ENDPOINT = "http://localhost:3030/tourisme/sparql"
USE_FUSEKI = os.getenv('USE_FUSEKI', 'false').lower() == 'true'

# Vérifier si Fuseki est disponible
fuseki_available = False
if USE_FUSEKI:
    try:
        response = requests.get("http://localhost:3030", timeout=2)
        fuseki_available = response.status_code == 200
        if fuseki_available:
            print("✅ Fuseki détecté et actif sur http://localhost:3030")
            sparql_wrapper = SPARQLWrapper(FUSEKI_ENDPOINT)
            sparql_wrapper.setReturnFormat(JSON)
        else:
            print("⚠️ Fuseki configuré mais non accessible")
    except:
        print("⚠️ Fuseki non disponible, utilisation de RDFLib en mémoire")
        USE_FUSEKI = False

# Charger l'ontologie RDF en mémoire (toujours comme fallback)
print("📚 Chargement de l'ontologie en mémoire avec RDFLib...")
g = Graph()
g.parse("../ws.rdf", format="xml")
print("✅ Ontologie chargée avec succès!")

def reload_graph():
    """Recharger le graphe RDF depuis ws.rdf"""
    global g
    try:
        temp_graph = Graph()
        temp_graph.parse("../ws.rdf", format="xml")
        
        # Remplacer le graphe global
        g = temp_graph
        
        # Réenregistrer les namespaces
        g.bind("default1", NS)
        g.bind("rdf", RDF)
        g.bind("rdfs", RDFS)
        g.bind("owl", OWL)
        g.bind("xsd", XSD)
        
        # Log simplifie sans caracteres speciaux
        triplet_count = len(g)
        return True
    except Exception as e:
        print(f"[ERROR] Erreur lors du rechargement: {e}")
        return False

def execute_sparql(query):
    """Exécute une requête SPARQL sur Fuseki ou RDFLib et retourne un format uniforme"""
    if USE_FUSEKI and fuseki_available:
        try:
            sparql_wrapper.setQuery(query)
            results = sparql_wrapper.query().convert()
            # Convertir format Fuseki JSON en objets similaires à RDFLib
            bindings = results.get("results", {}).get("bindings", [])
            return [SimpleNamespace(**{k: v.get("value") for k, v in binding.items()}) 
                    for binding in bindings]
        except Exception as e:
            print(f"❌ Erreur Fuseki: {e}, fallback vers RDFLib")
            return g.query(query)
    else:
        return g.query(query)

@app.route('/api/health', methods=['GET'])
def health():
    """Vérifier l'état de l'API"""
    return jsonify({"status": "ok", "message": "API en ligne"})

@app.route('/api/ontology/stats', methods=['GET'])
def get_ontology_stats():
    """Obtenir les statistiques de l'ontologie"""
    query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT (COUNT(DISTINCT ?class) as ?classes) 
           (COUNT(DISTINCT ?prop) as ?properties) 
           (COUNT(DISTINCT ?ind) as ?individuals)
    WHERE {
        {?class a owl:Class}
        UNION {?prop a owl:ObjectProperty}
        UNION {?prop a owl:DatatypeProperty}
        UNION {?ind a ?type . ?type a owl:Class}
    }
    """
    results = g.query(query)
    for row in results:
        return jsonify({
            "classes": int(row.classes) if row.classes else 0,
            "properties": int(row.properties) if row.properties else 0,
            "individuals": int(row.individuals) if row.individuals else 0
        })

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    """Récupérer toutes les destinations"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
    SELECT DISTINCT ?destination ?nom
    WHERE {
        ?destination rdf:type ns:Destination .
        OPTIONAL { ?destination ns:nomDestination ?nom }
    }
    """
    results = execute_sparql(query)
    # Utiliser un dictionnaire pour dédupliquer par URI
    destinations_dict = {}
    for row in results:
        uri = str(getattr(row, 'destination', ''))
        if uri not in destinations_dict:
            destinations_dict[uri] = {
                "uri": uri,
                "nom": str(getattr(row, 'nom', '')) if getattr(row, 'nom', None) else None,
                "type": "Destination"
            }
    return jsonify(list(destinations_dict.values()))

@app.route('/api/hebergements', methods=['GET'])
def get_hebergements():
    """Récupérer tous les hébergements"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    
    SELECT DISTINCT ?hebergement ?nom ?certification
    WHERE {
        {
            ?hebergement rdf:type ns:Hébergement .
        } UNION {
            ?hebergement rdf:type ?subclass .
            ?subclass rdfs:subClassOf ns:Hébergement .
        }
        OPTIONAL { ?hebergement ns:nomHebergement ?nom }
        OPTIONAL { ?hebergement ns:possèdeCertification ?cert .
                   ?cert ns:nomCertification ?certification }
    }
    """
    results = execute_sparql(query)
    # Dédupliquer par URI
    hebergements_dict = {}
    for row in results:
        uri = str(getattr(row, 'hebergement', ''))
        if uri not in hebergements_dict:
            hebergements_dict[uri] = {
                "uri": uri,
                "nom": str(getattr(row, 'nom', '')) if getattr(row, 'nom', None) else None,
                "type": "Hébergement",
                "certification": str(getattr(row, 'certification', '')) if getattr(row, 'certification', None) else None
            }
    return jsonify(list(hebergements_dict.values()))

@app.route('/api/activites', methods=['GET'])
def get_activites():
    """Récupérer toutes les activités touristiques"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?activite ?nom ?duree ?empreinte
    WHERE {
        {
            ?activite rdf:type ns:ActivitéTouristique .
        } UNION {
            ?activite rdf:type ?subclass .
            ?subclass rdfs:subClassOf ns:ActivitéTouristique .
        }
        OPTIONAL { ?activite ns:nomActivité ?nom }
        OPTIONAL { ?activite ns:duree ?duree }
        OPTIONAL { ?activite ns:aEmpreinteCarbone ?ec .
                   ?ec ns:empreinte ?empreinte }
    }
    """
    results = execute_sparql(query)
    # Dédupliquer par URI
    activites_dict = {}
    for row in results:
        uri = str(getattr(row, 'activite', ''))
        if uri not in activites_dict:
            duree_val = getattr(row, 'duree', None)
            empreinte_val = getattr(row, 'empreinte', None)
            activites_dict[uri] = {
                "uri": uri,
                "nom": str(getattr(row, 'nom', '')) if getattr(row, 'nom', None) else None,
                "duree": int(duree_val) if duree_val else None,
                "empreinte": float(empreinte_val) if empreinte_val else None,
                "type": "Activité Touristique"
            }
    return jsonify(list(activites_dict.values()))

@app.route('/api/transports', methods=['GET'])
def get_transports():
    """Récupérer tous les moyens de transport"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?transport ?empreinte
    WHERE {
        ?transport rdf:type ns:Transport .
        OPTIONAL { ?transport ns:aEmpreinteCarbone ?ec .
                   ?ec ns:empreinte ?empreinte }
    }
    """
    results = execute_sparql(query)
    # Dédupliquer par URI
    transports_dict = {}
    for row in results:
        uri = str(getattr(row, 'transport', ''))
        if uri not in transports_dict:
            empreinte_val = getattr(row, 'empreinte', None)
            transports_dict[uri] = {
                "uri": uri,
                "type": "Transport",
                "empreinte": float(empreinte_val) if empreinte_val else None
            }
    return jsonify(list(transports_dict.values()))

@app.route('/api/services', methods=['GET'])
def get_services():
    """Récupérer tous les services"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?service ?nom ?prix
    WHERE {
        {
            ?service rdf:type ns:Services .
        } UNION {
            ?service rdf:type ?subclass .
            ?subclass rdfs:subClassOf ns:Services .
        }
        OPTIONAL { ?service ns:nomService ?nom }
        OPTIONAL { ?service ns:prix ?prix }
    }
    """
    results = execute_sparql(query)
    services_dict = {}
    for row in results:
        uri = str(getattr(row, 'service', ''))
        if uri not in services_dict:
            prix_val = getattr(row, 'prix', None)
            services_dict[uri] = {
                "uri": uri,
                "nom": str(getattr(row, 'nom', '')) if getattr(row, 'nom', None) else None,
                "prix": float(prix_val) if prix_val else None
            }
    return jsonify(list(services_dict.values()))

@app.route('/api/nourritures', methods=['GET'])
def get_nourritures():
    """Récupérer toutes les nourritures"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?nourriture ?nom
    WHERE {
        {
            ?nourriture rdf:type ns:Nourriture .
        } UNION {
            ?nourriture rdf:type ?subclass .
            ?subclass rdfs:subClassOf ns:Nourriture .
        }
        OPTIONAL { ?nourriture ns:nomNourriture ?nom }
    }
    """
    results = execute_sparql(query)
    nourritures_dict = {}
    for row in results:
        uri = str(getattr(row, 'nourriture', ''))
        if uri not in nourritures_dict:
            nourritures_dict[uri] = {
                "uri": uri,
                "nom": str(getattr(row, 'nom', '')) if getattr(row, 'nom', None) else None
            }
    return jsonify(list(nourritures_dict.values()))

@app.route('/api/equipements', methods=['GET'])
def get_equipements():
    """Récupérer tous les équipements"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?equipement ?nom
    WHERE {
        {
            ?equipement rdf:type ns:Equipement .
        } UNION {
            ?equipement rdf:type ?subclass .
            ?subclass rdfs:subClassOf ns:Equipement .
        }
        OPTIONAL { ?equipement ns:nomEquipement ?nom }
    }
    """
    results = execute_sparql(query)
    equipements_dict = {}
    for row in results:
        uri = str(getattr(row, 'equipement', ''))
        if uri not in equipements_dict:
            equipements_dict[uri] = {
                "uri": uri,
                "nom": str(getattr(row, 'nom', '')) if getattr(row, 'nom', None) else None
            }
    return jsonify(list(equipements_dict.values()))

@app.route('/api/personnes', methods=['GET'])
def get_personnes():
    """Récupérer toutes les personnes"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?personne ?nom ?age
    WHERE {
        {
            ?personne rdf:type ns:Personne .
        } UNION {
            ?personne rdf:type ?subclass .
            ?subclass rdfs:subClassOf ns:Personne .
        }
        OPTIONAL { ?personne ns:nomVoyageur ?nom }
        OPTIONAL { ?personne ns:age ?age }
    }
    """
    results = execute_sparql(query)
    personnes_dict = {}
    for row in results:
        uri = str(getattr(row, 'personne', ''))
        if uri not in personnes_dict:
            age_val = getattr(row, 'age', None)
            personnes_dict[uri] = {
                "uri": uri,
                "nom": str(getattr(row, 'nom', '')) if getattr(row, 'nom', None) else None,
                "age": int(age_val) if age_val else None
            }
    return jsonify(list(personnes_dict.values()))

@app.route('/api/certifications', methods=['GET'])
def get_certifications():
    """Récupérer toutes les certifications"""
    query = """
    PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?certification ?nom ?date
    WHERE {
        {
            ?certification rdf:type ns:CertificationÉco .
        } UNION {
            ?certification rdf:type ?subclass .
            ?subclass rdfs:subClassOf ns:CertificationÉco .
        }
        OPTIONAL { ?certification ns:nomCertification ?nom }
        OPTIONAL { ?certification ns:dateValidite ?date }
    }
    """
    results = execute_sparql(query)
    certifications_dict = {}
    for row in results:
        uri = str(getattr(row, 'certification', ''))
        if uri not in certifications_dict:
            certifications_dict[uri] = {
                "uri": uri,
                "nom": str(getattr(row, 'nom', '')) if getattr(row, 'nom', None) else None,
                "dateValidite": str(getattr(row, 'date', '')) if getattr(row, 'date', None) else None
            }
    return jsonify(list(certifications_dict.values()))

@app.route('/api/query', methods=['POST'])
def execute_query():
    """Exécuter une requête SPARQL personnalisée"""
    data = request.json
    sparql_query = data.get('query', '')
    
    try:
        results = execute_sparql(sparql_query)
        result_list = []
        for row in results:
            result_dict = {}
            for var in results.vars:
                result_dict[str(var)] = str(row[var]) if row[var] else None
            result_list.append(result_dict)
        return jsonify({
            "success": True,
            "results": result_list,
            "count": len(result_list)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

def generate_sparql_with_gemini(question):
    """Utilise Google Gemini pour convertir une question en requête SPARQL"""
    if not gemini_model:
        return None
    
    prompt = f"""Tu es un expert en SPARQL et en ontologies OWL.
    
Contexte: Ontologie de tourisme éco-responsable avec les classes suivantes:
- Destination (DestinationUrbaine, DestinationRurale, DestinationCotière, DestinationInsulaire, DestinationMontagneuse)
- Hébergement (Hôtel, Camping, Maison_d'hôtes, Village_vacances)
- ActivitéTouristique (Randonnée, Camping_écologique, Visite_de_musées, Excursions_en_montagne, Excursions_en_désert)
- Transport (Train, Taxi, Vélo)
- Personne (Voyageur, GuideTouristique, Chauffeur, Organisateur)
- Services (AgenceVoyage, GuideTouristique, AssuranceVoyage, ServiceAdditionnel)
- Nourriture (PetitDejeuner, Diner, Buffet, Snack, FastFood, cafeteria)
- Equipement (Valise, Material_de_camping, EquipementSecurite)
- CertificationÉco (CertificationISO14001, CertificationInternationale, CertificationLocale, Certificationnationale, CertificationSectorielle)
- EmpreinteCarbone

Propriétés d'objet:
- choisitDestination, séjourneDans, participeÀ, utilise, fournit, consomme, possèdeEquipement
- propose, contient, estSituéÀ, aPourLieu
- possèdeCertification, aEmpreinteCarbone, nécessite, estAttribuéeÀ

Propriétés de données:
- nomDestination, nomHebergement, nomActivité, nomVoyageur, nomService, nomNourriture, nomEquipement, nomCertification
- empreinte (float), duree (integer), age (integer), prix (float), capacite (integer), typeTransport (string), dateValidite (date)

Namespace: PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
Préfixes à utiliser: PREFIX rdf:, PREFIX rdfs:, PREFIX owl:

Question utilisateur: {question}

IMPORTANT: Génère UNIQUEMENT une requête SPARQL SELECT pour interroger les données.
Ne génère JAMAIS de requête INSERT, DELETE ou UPDATE.

La requête doit:
1. Être une requête SELECT uniquement
2. Utiliser le préfixe ns: pour l'ontologie
3. Utiliser rdf:type/rdfs:subClassOf* pour les classes
4. Être syntaxiquement correcte
5. Répondre précisément à la question"""

    try:
        response = gemini_model.generate_content(prompt)
        sparql_query = response.text.strip()
        
        # Nettoyer la réponse pour extraire uniquement le SPARQL
        # Chercher le code entre ```sparql et ``` ou juste le texte
        if '```sparql' in sparql_query:
            sparql_query = re.search(r'```sparql\n(.*?)```', sparql_query, re.DOTALL).group(1)
        elif '```' in sparql_query:
            sparql_query = re.search(r'```\n?(.*?)```', sparql_query, re.DOTALL).group(1)
        
        return sparql_query.strip()
    except Exception as e:
        print(f"Erreur Gemini: {e}")
        return None

@app.route('/api/nl-query', methods=['POST'])
def natural_language_query():
    """Convertir une question en langage naturel en requête SPARQL avec IA Gemini OU gérer opérations CRUD"""
    data = request.json
    question = data.get('question', '')
    use_ai = data.get('use_ai', True)  # Par défaut, utiliser l'IA
    
    question_lower = question.lower()
    
    # ========================================
    # DÉTECTION D'INTENTIONS CRUD
    # ========================================
    
    # Détecter les relations EN PREMIER (avant "ajouter" pour éviter confusion avec "Ajoute une relation X possede Y")
    if any(word in question_lower for word in [' va à ', ' va a ', ' visite ', ' choisit ', ' séjourne dans ', ' utilise ', 'possede', 'possède', ' a la certification', ' a une certification']):
        # RECHARGER LE GRAPHE AVANT DE TRAITER LA RELATION
        print("[DEBUG] RELOAD avant traitement relation")
        reload_graph()
        print(f"[DEBUG] Graphe recharge - {len(g)} triplets en memoire")
        try:
            if gemini_model:
                prompt = f"""
Extrais les informations de cette demande de relation entre entités:
Question: "{question}"

Tu dois retourner UNIQUEMENT un objet JSON avec:
- sujet_type: le type du sujet parmi (Personne, Destination, Hébergement, ActivitéTouristique, Transport, Services, Nourriture, Equipement, CertificationÉco)
- sujet_nom: le nom du sujet
- relation: la propriété de relation (choisitDestination, séjourneDans, utilise, possèdeCertification, etc.)
- objet_type: le type de l'objet parmi (Personne, Destination, Hébergement, ActivitéTouristique, Transport, Services, Nourriture, Equipement, CertificationÉco)
- objet_nom: le nom de l'objet

TYPES D'ENTITES:
- Personne: voyageurs, touristes
- Destination: pays, villes, lieux
- Hébergement: hôtels, auberges
- ActivitéTouristique: surf, randonnée, plongée, ski, kayak, escalade, etc.
- Transport: bus, taxi, bateau, jet-ski, téléphérique, train, etc.
- Services: wifi, spa, restaurant
- Nourriture: plats, boissons
- Equipement: matériel, outils
- CertificationÉco: labels écologiques

Exemples:
"oumayma va à la Tunisie" -> {{"sujet_type": "Personne", "sujet_nom": "oumayma", "relation": "choisitDestination", "objet_type": "Destination", "objet_nom": "Tunisie"}}
"Jean séjourne dans Hotel Paris" -> {{"sujet_type": "Personne", "sujet_nom": "Jean", "relation": "séjourneDans", "objet_type": "Hébergement", "objet_nom": "Hotel Paris"}}
"Hotel Keops possede la certification ISO 2027" -> {{"sujet_type": "Hébergement", "sujet_nom": "Hotel Keops", "relation": "possèdeCertification", "objet_type": "CertificationÉco", "objet_nom": "ISO 2027"}}
"Surf utilise Jet-Ski" -> {{"sujet_type": "ActivitéTouristique", "sujet_nom": "Surf", "relation": "utilise", "objet_type": "Transport", "objet_nom": "Jet-Ski"}}

Réponds UNIQUEMENT avec le JSON.
"""
                response = gemini_model.generate_content(prompt)
                json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
                print(f"[DEBUG] Gemini JSON brut: {json_str}")
                relation_data = json.loads(json_str)
                print(f"[DEBUG] Relation parsed: {relation_data}")
                
                # Mapping des propriétés nom
                name_property_map = {
                    'Personne': 'nomVoyageur',
                    'Destination': 'nomDestination',
                    'Hébergement': 'nomHebergement',
                    'ActivitéTouristique': 'nomActivité',
                    'Transport': 'nomTransport',
                    'Services': 'nomService',
                    'Nourriture': 'nomNourriture',
                    'Equipement': 'nomEquipement',
                    'CertificationÉco': 'nomCertification'
                }
                
                # Trouver le sujet
                sujet_uri = None
                sujet_type = relation_data['sujet_type']
                sujet_nom = relation_data['sujet_nom'].lower()
                
                if sujet_type in name_property_map:
                    name_prop = NS[name_property_map[sujet_type]]
                    type_uri = NS[sujet_type]
                    print(f"[DEBUG] Recherche sujet: type={sujet_type}, nom={sujet_nom}")
                    for s, p, o in g.triples((None, RDF.type, type_uri)):
                        for _, _, nom in g.triples((s, name_prop, None)):
                            print(f"[DEBUG] Compare: '{str(nom).lower()}' == '{sujet_nom}' ?")
                            if str(nom).lower() == sujet_nom:
                                sujet_uri = s
                                print(f"[DEBUG] TROUVE sujet: {s}")
                                break
                        if sujet_uri:
                            break
                
                if not sujet_uri:
                    return jsonify({
                        "success": False,
                        "error": f"Entité sujet '{relation_data['sujet_nom']}' non trouvée"
                    }), 404
                
                # Trouver l'objet
                objet_uri = None
                objet_type = relation_data['objet_type']
                objet_nom = relation_data['objet_nom'].lower()
                
                if objet_type in name_property_map:
                    name_prop = NS[name_property_map[objet_type]]
                    type_uri = NS[objet_type]
                    for s, p, o in g.triples((None, RDF.type, type_uri)):
                        for _, _, nom in g.triples((s, name_prop, None)):
                            if str(nom).lower() == objet_nom:
                                objet_uri = s
                                break
                        if objet_uri:
                            break
                
                if not objet_uri:
                    return jsonify({
                        "success": False,
                        "error": f"Entité objet '{relation_data['objet_nom']}' non trouvée"
                    }), 404
                
                # Ajouter la relation
                relation_prop = NS[relation_data['relation']]
                g.add((sujet_uri, relation_prop, objet_uri))
                
                # Sauvegarder
                print(f"[DEBUG] AVANT save_rdf_to_file() - Relation {relation_data.get('sujet_nom')} -> {relation_data.get('objet_nom')}")
                if save_rdf_to_file():
                    return jsonify({
                        "success": True,
                        "action": "add_relation",
                        "message": f"✅ Relation ajoutée: '{relation_data['sujet_nom']}' {relation_data['relation']} '{relation_data['objet_nom']}'",
                        "relation": {
                            "sujet": {"type": sujet_type, "nom": relation_data['sujet_nom'], "uri": str(sujet_uri)},
                            "propriete": relation_data['relation'],
                            "objet": {"type": objet_type, "nom": relation_data['objet_nom'], "uri": str(objet_uri)}
                        }
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Relation ajoutée en mémoire mais erreur de sauvegarde"
                    }), 500
                    
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Impossible d'ajouter la relation: {str(e)}",
                "suggestion": "Essayez: '[personne] va à [destination]' ou '[personne] séjourne dans [hébergement]'"
            }), 400
    
    # Détecter "ajouter/créer"
    elif any(word in question_lower for word in ['ajouter', 'ajoute', 'créer', 'crée', 'nouveau', 'nouvelle']):
        try:
            # Utiliser Gemini pour extraire les informations structurées
            if gemini_model:
                prompt = f"""
Extrais les informations de cette demande de création d'entité:
Question: "{question}"

Tu dois retourner UNIQUEMENT un objet JSON valide avec:
- type: le type d'entité (Personne, Destination, Hébergement, ActivitéTouristique, Transport, Services, Nourriture, Equipement, ou CertificationÉco)
- attributes: un objet avec les attributs extraits (nom OBLIGATOIRE, et autres comme age, prix, pays, etc.)

Exemple pour "Ajoute une personne Jean qui a 25 ans":
{{"type": "Personne", "attributes": {{"nom": "Jean", "age": 25}}}}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après.
"""
                response = gemini_model.generate_content(prompt)
                json_str = response.text.strip()
                # Nettoyer la réponse (enlever markdown si présent)
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                
                entity_data = json.loads(json_str)
                
                # Créer l'entité directement ici
                entity_type = entity_data.get('type')
                attributes = entity_data.get('attributes', {})
                
                if not entity_type or not attributes.get('nom'):
                    return jsonify({
                        "success": False,
                        "error": "Type d'entité et nom requis"
                    }), 400
                
                # Générer URI unique
                entity_uri = generate_uri(entity_type, attributes['nom'])
                
                # Vérifier si l'entité existe déjà
                if (entity_uri, None, None) in g:
                    return jsonify({
                        "success": False,
                        "error": f"Une entité avec le nom '{attributes['nom']}' existe déjà"
                    }), 400
                
                # Ajouter le type (rdf:type)
                class_uri = NS[entity_type]
                g.add((entity_uri, RDF.type, class_uri))
                
                # Mapping des propriétés par type d'entité
                property_mappings = {
                    'Personne': {'nom': 'nomVoyageur', 'age': 'age'},
                    'Destination': {'nom': 'nomDestination', 'pays': 'pays'},
                    'Hébergement': {'nom': 'nomHebergement', 'prix': 'prix', 'capacite': 'capacite', 'type': 'typeHebergement'},
                    'ActivitéTouristique': {'nom': 'nomActivité', 'prix': 'prix', 'duree': 'duree'},
                    'Transport': {'nom': 'nomTransport', 'type': 'typeTransport'},
                    'Services': {'nom': 'nomService', 'prix': 'prix'},
                    'Nourriture': {'nom': 'nomNourriture'},
                    'Equipement': {'nom': 'nomEquipement'},
                    'CertificationÉco': {'nom': 'nomCertification', 'date': 'dateValidite'}
                }
                
                # Ajouter les propriétés de données
                if entity_type in property_mappings:
                    for attr_key, attr_value in attributes.items():
                        if attr_key in property_mappings[entity_type]:
                            property_name = property_mappings[entity_type][attr_key]
                            property_uri = NS[property_name]
                            
                            # Déterminer le type de littéral
                            if attr_key in ['age', 'prix', 'capacite', 'duree']:
                                if attr_key == 'prix':
                                    literal = Literal(float(attr_value), datatype=XSD.float)
                                else:
                                    literal = Literal(int(attr_value), datatype=XSD.integer)
                            else:
                                literal = Literal(attr_value)
                            
                            g.add((entity_uri, property_uri, literal))
                
                # Sauvegarder dans ws.rdf
                print(f"[DEBUG] AVANT save_rdf_to_file() - Creation de {attributes.get('nom', 'UNKNOWN')}")
                if save_rdf_to_file():
                    return jsonify({
                        "success": True,
                        "action": "create",
                        "message": f"✅ {entity_type} '{attributes['nom']}' créé avec succès et sauvegardé dans ws.rdf!",
                        "entity": {
                            "type": entity_type,
                            "uri": str(entity_uri),
                            "attributes": attributes
                        }
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Entité créée en mémoire mais erreur de sauvegarde dans ws.rdf"
                    }), 500
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Impossible d'extraire les informations de création: {str(e)}",
                "suggestion": "Essayez: 'Ajoute une personne [nom] qui a [age] ans'"
            }), 400
    
    # Détecter "supprimer/effacer"
    elif any(word in question_lower for word in ['supprimer', 'supprime', 'effacer', 'efface', 'retirer', 'retire']):
        try:
            if gemini_model:
                prompt = f"""
Extrais les informations de cette demande de suppression:
Question: "{question}"

Tu dois retourner UNIQUEMENT un objet JSON avec:
- type: le type d'entité (Personne, Destination, etc.)
- nom: le nom de l'entité à supprimer

Exemple pour "Supprime la personne Jean":
{{"type": "Personne", "nom": "Jean"}}

Réponds UNIQUEMENT avec le JSON.
"""
                response = gemini_model.generate_content(prompt)
                json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
                delete_data = json.loads(json_str)
                
                # Mapping des propriétés pour trouver l'attribut nom
                name_property_map = {
                    'Personne': 'nomVoyageur',
                    'Destination': 'nomDestination',
                    'Hébergement': 'nomHebergement',
                    'ActivitéTouristique': 'nomActivité',
                    'Transport': 'nomTransport',
                    'Services': 'nomService',
                    'Nourriture': 'nomNourriture',
                    'Equipement': 'nomEquipement',
                    'CertificationÉco': 'nomCertification'
                }
                
                # Trouver l'entité en cherchant par nom (insensible à la casse)
                entity_type = delete_data['type']
                search_name = delete_data['nom'].lower()
                entity_uri = None
                
                if entity_type in name_property_map:
                    name_property = name_property_map[entity_type]
                    name_property_uri = NS[name_property]
                    
                    # Chercher toutes les entités de ce type
                    type_uri = NS[entity_type]
                    for s, p, o in g.triples((None, RDF.type, type_uri)):
                        # Vérifier si le nom correspond (insensible à la casse)
                        for _, _, nom in g.triples((s, name_property_uri, None)):
                            if str(nom).lower() == search_name:
                                entity_uri = s
                                break
                        if entity_uri:
                            break
                
                # Vérifier que l'entité existe
                if not entity_uri or (entity_uri, None, None) not in g:
                    return jsonify({
                        "success": False,
                        "error": f"Entité '{delete_data['nom']}' de type {delete_data['type']} non trouvée"
                    }), 404
                
                # Supprimer tous les triplets où l'entité est sujet
                g.remove((entity_uri, None, None))
                
                # Supprimer tous les triplets où l'entité est objet
                g.remove((None, None, entity_uri))
                
                # Sauvegarder
                if save_rdf_to_file():
                    return jsonify({
                        "success": True,
                        "action": "delete",
                        "message": f"✅ {delete_data['type']} '{delete_data['nom']}' supprimé avec succès de ws.rdf!"
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Entité supprimée en mémoire mais erreur de sauvegarde"
                    }), 500
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Impossible de supprimer: {str(e)}",
                "suggestion": "Essayez: 'Supprime [type] [nom]'"
            }), 400
    
    # Détecter "modifier/changer"
    elif any(word in question_lower for word in ['modifier', 'modifie', 'changer', 'change', 'mettre à jour', 'update']):
        try:
            if gemini_model:
                prompt = f"""
Extrais les informations de cette demande de modification:
Question: "{question}"

Tu dois retourner UNIQUEMENT un objet JSON avec:
- type: le type d'entité
- nom: le nom de l'entité à modifier
- attributes: les nouveaux attributs à modifier

Exemple pour "Modifie l'âge de Jean à 30 ans":
{{"type": "Personne", "nom": "Jean", "attributes": {{"age": 30}}}}

Réponds UNIQUEMENT avec le JSON.
"""
                response = gemini_model.generate_content(prompt)
                json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
                update_data = json.loads(json_str)
                
                # Mapping des propriétés pour trouver l'attribut nom
                name_property_map = {
                    'Personne': 'nomVoyageur',
                    'Destination': 'nomDestination',
                    'Hébergement': 'nomHebergement',
                    'ActivitéTouristique': 'nomActivité',
                    'Transport': 'nomTransport',
                    'Services': 'nomService',
                    'Nourriture': 'nomNourriture',
                    'Equipement': 'nomEquipement',
                    'CertificationÉco': 'nomCertification'
                }
                
                # Trouver l'entité en cherchant par nom (insensible à la casse)
                entity_type = update_data['type']
                search_name = update_data['nom'].lower()
                entity_uri = None
                
                if entity_type in name_property_map:
                    name_property = name_property_map[entity_type]
                    name_property_uri = NS[name_property]
                    
                    # Chercher toutes les entités de ce type
                    type_uri = NS[entity_type]
                    for s, p, o in g.triples((None, RDF.type, type_uri)):
                        # Vérifier si le nom correspond (insensible à la casse)
                        for _, _, nom in g.triples((s, name_property_uri, None)):
                            if str(nom).lower() == search_name:
                                entity_uri = s
                                break
                        if entity_uri:
                            break
                
                # Vérifier que l'entité existe
                if not entity_uri or (entity_uri, None, None) not in g:
                    return jsonify({
                        "success": False,
                        "error": f"Entité '{update_data['nom']}' non trouvée"
                    }), 404
                
                # Mapping des propriétés
                property_mappings = {
                    'Personne': {'nom': 'nomVoyageur', 'age': 'age'},
                    'Destination': {'nom': 'nomDestination', 'pays': 'pays'},
                    'Hébergement': {'nom': 'nomHebergement', 'prix': 'prix', 'capacite': 'capacite', 'type': 'typeHebergement'},
                    'ActivitéTouristique': {'nom': 'nomActivité', 'prix': 'prix', 'duree': 'duree'},
                    'Transport': {'nom': 'nomTransport', 'type': 'typeTransport'},
                    'Services': {'nom': 'nomService', 'prix': 'prix'},
                    'Nourriture': {'nom': 'nomNourriture'},
                    'Equipement': {'nom': 'nomEquipement'},
                    'CertificationÉco': {'nom': 'nomCertification', 'date': 'dateValidite'}
                }
                
                # Supprimer les anciennes valeurs et ajouter les nouvelles
                entity_type = update_data['type']
                attributes = update_data.get('attributes', {})
                
                if entity_type in property_mappings:
                    for attr_key, attr_value in attributes.items():
                        if attr_key in property_mappings[entity_type]:
                            property_name = property_mappings[entity_type][attr_key]
                            property_uri = NS[property_name]
                            
                            # Supprimer l'ancienne valeur
                            g.remove((entity_uri, property_uri, None))
                            
                            # Ajouter la nouvelle valeur
                            if attr_key in ['age', 'prix', 'capacite', 'duree']:
                                if attr_key == 'prix':
                                    literal = Literal(float(attr_value), datatype=XSD.float)
                                else:
                                    literal = Literal(int(attr_value), datatype=XSD.integer)
                            else:
                                literal = Literal(attr_value)
                            
                            g.add((entity_uri, property_uri, literal))
                
                # Sauvegarder
                if save_rdf_to_file():
                    return jsonify({
                        "success": True,
                        "action": "update",
                        "message": f"✅ {entity_type} '{update_data['nom']}' modifié avec succès dans ws.rdf!",
                        "entity": {
                            "type": entity_type,
                            "uri": str(entity_uri),
                            "attributes": attributes
                        }
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Entité mise à jour en mémoire mais erreur de sauvegarde"
                    }), 500
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Impossible de modifier: {str(e)}",
                "suggestion": "Essayez: 'Modifie [attribut] de [nom] à [nouvelle valeur]'"
            }), 400
    
    # ========================================
    # REQUÊTES DE LECTURE (SELECT)
    # ========================================
    # Note: si on arrive ici, ce n'est ni CREATE, ni UPDATE, ni DELETE, ni RELATION
    # donc c'est une vraie requête de consultation
    
    sparql_query = None
    method_used = "fallback"
    
    # Essayer d'abord avec Gemini AI (seulement pour les requêtes SELECT, pas les CRUD)
    if use_ai and gemini_model:
        sparql_query = generate_sparql_with_gemini(question)
        if sparql_query:
            method_used = "gemini-ai"
    
    # Fallback: Mapping simple de questions vers requêtes SPARQL
    if not sparql_query:
        method_used = "keyword-matching"
        
        if "destination" in question_lower and ("toutes" in question_lower or "liste" in question_lower):
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?destination ?nom
            WHERE {
                ?destination rdf:type/rdfs:subClassOf* ns:Destination .
                OPTIONAL { ?destination ns:nomDestination ?nom }
            }
            """
        elif "hébergement" in question_lower and "certification" in question_lower:
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?hebergement ?nom ?certification
            WHERE {
                ?hebergement rdf:type/rdfs:subClassOf* ns:Hébergement .
                ?hebergement ns:possèdeCertification ?cert .
                ?cert ns:nomCertification ?certification .
                OPTIONAL { ?hebergement ns:nomHebergement ?nom }
            }
            """
        elif "activité" in question_lower and ("écologique" in question_lower or "empreinte" in question_lower):
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?activite ?nom ?empreinte
            WHERE {
                ?activite rdf:type/rdfs:subClassOf* ns:ActivitéTouristique .
                ?activite ns:aEmpreinteCarbone ?ec .
                ?ec ns:empreinte ?empreinte .
                OPTIONAL { ?activite ns:nomActivité ?nom }
            }
            ORDER BY ?empreinte
            """
        elif "transport" in question_lower and "écologique" in question_lower:
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            
            SELECT DISTINCT ?transport ?type ?empreinte
            WHERE {
                ?transport rdf:type ns:Vélo .
                OPTIONAL { ?transport ns:aEmpreinteCarbone ?ec .
                           ?ec ns:empreinte ?empreinte }
            }
            """
        elif "personne" in question_lower or "voyageur" in question_lower or "qui" in question_lower:
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?personne ?nom ?age
            WHERE {
                {
                    ?personne rdf:type ns:Personne .
                } UNION {
                    ?personne rdf:type ?subclass .
                    ?subclass rdfs:subClassOf ns:Personne .
                }
                OPTIONAL { ?personne ns:nomVoyageur ?nom }
                OPTIONAL { ?personne ns:age ?age }
            }
            """
        elif "service" in question_lower:
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?service ?nom ?prix
            WHERE {
                {
                    ?service rdf:type ns:Services .
                } UNION {
                    ?service rdf:type ?subclass .
                    ?subclass rdfs:subClassOf ns:Services .
                }
                OPTIONAL { ?service ns:nomService ?nom }
                OPTIONAL { ?service ns:prix ?prix }
            }
            """
        elif "certification" in question_lower:
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?certification ?nom ?date
            WHERE {
                {
                    ?certification rdf:type ns:CertificationÉco .
                } UNION {
                    ?certification rdf:type ?subclass .
                    ?subclass rdfs:subClassOf ns:CertificationÉco .
                }
                OPTIONAL { ?certification ns:nomCertification ?nom }
                OPTIONAL { ?certification ns:dateValidite ?date }
            }
            """
        elif "nourriture" in question_lower or "repas" in question_lower or "manger" in question_lower:
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?nourriture ?nom
            WHERE {
                {
                    ?nourriture rdf:type ns:Nourriture .
                } UNION {
                    ?nourriture rdf:type ?subclass .
                    ?subclass rdfs:subClassOf ns:Nourriture .
                }
                OPTIONAL { ?nourriture ns:nomNourriture ?nom }
            }
            """
        elif "équipement" in question_lower or "equipement" in question_lower or "matériel" in question_lower:
            sparql_query = """
            PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?equipement ?nom
            WHERE {
                {
                    ?equipement rdf:type ns:Equipement .
                } UNION {
                    ?equipement rdf:type ?subclass .
                    ?subclass rdfs:subClassOf ns:Equipement .
                }
                OPTIONAL { ?equipement ns:nomEquipement ?nom }
            }
            """
        else:
            return jsonify({
                "success": False,
                "error": "Question non comprise. Essayez des questions sur les destinations, hébergements, activités, transports, personnes, services, nourritures, équipements ou certifications.",
                "ai_available": gemini_model is not None
            }), 400
    
    # Exécuter la requête SPARQL
    if not sparql_query:
        return jsonify({
            "success": False,
            "error": "Impossible de générer une requête SPARQL pour cette question.",
            "ai_available": gemini_model is not None
        }), 400
    
    try:
        results = g.query(sparql_query)
        result_list = []
        for row in results:
            result_dict = {}
            for var in results.vars:
                result_dict[str(var)] = str(row[var]) if row[var] else None
            result_list.append(result_dict)
        
        return jsonify({
            "success": True,
            "question": question,
            "sparql": sparql_query,
            "method": method_used,
            "ai_available": gemini_model is not None,
            "results": result_list,
            "count": len(result_list)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# ========================================
# CRUD OPERATIONS - Création/Modification/Suppression
# ========================================

def save_rdf_to_file():
    """Sauvegarder le graphe RDF dans ws.rdf et recharger"""
    print(">>> DEBUT save_rdf_to_file()")
    global g
    # Sauvegarder
    g.serialize(destination="../ws.rdf", format="xml", encoding="utf-8")
    print("SAVE: ws.rdf sauvegarde OK")
    
    # Recharger IMMÉDIATEMENT dans un nouveau graphe
    new_graph = Graph()
    new_graph.parse("../ws.rdf", format="xml")
    g = new_graph
    print(f"RELOAD: Graphe recharge OK - {len(g)} triplets")
    
    return True

def generate_uri(class_name, name):
    """Générer un URI unique pour une nouvelle instance"""
    # Nettoyer le nom pour l'URI
    clean_name = name.replace(" ", "_").replace("'", "").replace("é", "e").replace("è", "e")
    return NS[f"{clean_name}"]

@app.route('/api/entity/create', methods=['POST'])
def create_entity():
    """Créer une nouvelle entité dans l'ontologie"""
    try:
        data = request.json
        entity_type = data.get('type')  # ex: "Personne", "Destination", etc.
        attributes = data.get('attributes', {})  # dict des propriétés
        
        if not entity_type or not attributes.get('nom'):
            return jsonify({
                "success": False,
                "error": "Type d'entité et nom requis"
            }), 400
        
        # Générer URI unique
        entity_uri = generate_uri(entity_type, attributes['nom'])
        
        # Vérifier si l'entité existe déjà
        if (entity_uri, None, None) in g:
            return jsonify({
                "success": False,
                "error": f"Une entité avec le nom '{attributes['nom']}' existe déjà"
            }), 400
        
        # Ajouter le type (rdf:type)
        class_uri = NS[entity_type]
        g.add((entity_uri, RDF.type, class_uri))
        
        # Mapping des propriétés par type d'entité
        property_mappings = {
            'Personne': {'nom': 'nomVoyageur', 'age': 'age'},
            'Destination': {'nom': 'nomDestination', 'pays': 'pays'},
            'Hébergement': {'nom': 'nomHebergement', 'prix': 'prix', 'capacite': 'capacite', 'type': 'typeHebergement'},
            'ActivitéTouristique': {'nom': 'nomActivité', 'prix': 'prix', 'duree': 'duree'},
            'Transport': {'nom': 'nomTransport', 'type': 'typeTransport'},
            'Services': {'nom': 'nomService', 'prix': 'prix'},
            'Nourriture': {'nom': 'nomNourriture'},
            'Equipement': {'nom': 'nomEquipement'},
            'CertificationÉco': {'nom': 'nomCertification', 'date': 'dateValidite'}
        }
        
        # Ajouter les propriétés de données
        if entity_type in property_mappings:
            for attr_key, attr_value in attributes.items():
                if attr_key in property_mappings[entity_type]:
                    property_name = property_mappings[entity_type][attr_key]
                    property_uri = NS[property_name]
                    
                    # Déterminer le type de littéral
                    if attr_key in ['age', 'prix', 'capacite', 'duree']:
                        if attr_key == 'prix':
                            literal = Literal(float(attr_value), datatype=XSD.float)
                        else:
                            literal = Literal(int(attr_value), datatype=XSD.integer)
                    else:
                        literal = Literal(attr_value)
                    
                    g.add((entity_uri, property_uri, literal))
        
        # Sauvegarder dans ws.rdf
        if save_rdf_to_file():
            return jsonify({
                "success": True,
                "message": f"{entity_type} '{attributes['nom']}' créé avec succès",
                "uri": str(entity_uri)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Entité créée en mémoire mais erreur de sauvegarde"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la création: {str(e)}"
        }), 500

@app.route('/api/entity/update', methods=['PUT'])
def update_entity():
    """Mettre à jour une entité existante"""
    try:
        data = request.json
        entity_uri_str = data.get('uri')
        attributes = data.get('attributes', {})
        
        if not entity_uri_str:
            return jsonify({
                "success": False,
                "error": "URI de l'entité requise"
            }), 400
        
        entity_uri = URIRef(entity_uri_str)
        
        # Vérifier que l'entité existe
        if (entity_uri, None, None) not in g:
            return jsonify({
                "success": False,
                "error": "Entité non trouvée"
            }), 404
        
        # Supprimer les anciennes valeurs et ajouter les nouvelles
        for attr_key, attr_value in attributes.items():
            # Trouver la propriété correspondante
            property_uri = None
            for prop in [NS.nomVoyageur, NS.age, NS.nomDestination, NS.pays, 
                        NS.nomHebergement, NS.prix, NS.capacite, NS.typeHebergement,
                        NS.nomActivité, NS.duree, NS.nomTransport, NS.typeTransport,
                        NS.nomService, NS.nomNourriture, NS.nomEquipement, 
                        NS.nomCertification, NS.dateValidite]:
                if str(prop).split('#')[1] == attr_key or str(prop).split('#')[1].startswith('nom'):
                    property_uri = prop
                    break
            
            if property_uri:
                # Supprimer l'ancienne valeur
                g.remove((entity_uri, property_uri, None))
                
                # Ajouter la nouvelle valeur
                if attr_key in ['age', 'prix', 'capacite', 'duree']:
                    if attr_key == 'prix':
                        literal = Literal(float(attr_value), datatype=XSD.float)
                    else:
                        literal = Literal(int(attr_value), datatype=XSD.integer)
                else:
                    literal = Literal(attr_value)
                
                g.add((entity_uri, property_uri, literal))
        
        # Sauvegarder
        if save_rdf_to_file():
            return jsonify({
                "success": True,
                "message": "Entité mise à jour avec succès"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Entité mise à jour en mémoire mais erreur de sauvegarde"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la mise à jour: {str(e)}"
        }), 500

@app.route('/api/entity/delete', methods=['DELETE'])
def delete_entity():
    """Supprimer une entité de l'ontologie"""
    try:
        data = request.json
        entity_uri_str = data.get('uri')
        
        if not entity_uri_str:
            return jsonify({
                "success": False,
                "error": "URI de l'entité requise"
            }), 400
        
        entity_uri = URIRef(entity_uri_str)
        
        # Vérifier que l'entité existe
        if (entity_uri, None, None) not in g:
            return jsonify({
                "success": False,
                "error": "Entité non trouvée"
            }), 404
        
        # Supprimer tous les triplets où l'entité est sujet
        g.remove((entity_uri, None, None))
        
        # Supprimer tous les triplets où l'entité est objet
        g.remove((None, None, entity_uri))
        
        # Sauvegarder
        if save_rdf_to_file():
            return jsonify({
                "success": True,
                "message": "Entité supprimée avec succès"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Entité supprimée en mémoire mais erreur de sauvegarde"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la suppression: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Désactiver le reloader en mode debug pour éviter les redémarrages constants
    import os
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Démarrage du serveur CRUD sur le port {port}...")
    print(f"📝 Toutes les opérations seront sauvegardées dans ws.rdf")
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
