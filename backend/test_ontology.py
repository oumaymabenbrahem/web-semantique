from rdflib import Graph, Namespace

# Charger l'ontologie
g = Graph()
g.parse('../ws.rdf', format='xml')
print(f'✅ Ontologie chargée: {len(g)} triples')

NS = Namespace('http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#')

# Test Hébergements
query_heb = """
PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?hebergement ?nom
WHERE {
    {
        ?hebergement rdf:type ns:Hébergement .
    } UNION {
        ?hebergement rdf:type ?subclass .
        ?subclass rdfs:subClassOf ns:Hébergement .
    }
    OPTIONAL { ?hebergement ns:nomHebergement ?nom }
}
"""
results_heb = list(g.query(query_heb))
print(f'\n🏨 Hébergements trouvés: {len(results_heb)}')
for r in results_heb:
    print(f"  - {r.hebergement} => {r.nom if r.nom else 'sans nom'}")

# Test Activités
query_act = """
PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?activite ?nom
WHERE {
    {
        ?activite rdf:type ns:ActivitéTouristique .
    } UNION {
        ?activite rdf:type ?subclass .
        ?subclass rdfs:subClassOf ns:ActivitéTouristique .
    }
    OPTIONAL { ?activite ns:nomActivité ?nom }
}
"""
results_act = list(g.query(query_act))
print(f'\n🎯 Activités trouvées: {len(results_act)}')
for r in results_act:
    print(f"  - {r.activite} => {r.nom if r.nom else 'sans nom'}")

# Test Destinations
query_dest = """
PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?destination ?nom
WHERE {
    ?destination rdf:type ns:Destination .
    OPTIONAL { ?destination ns:nomDestination ?nom }
}
"""
results_dest = list(g.query(query_dest))
print(f'\n🌍 Destinations trouvées: {len(results_dest)}')
for r in results_dest:
    print(f"  - {r.destination} => {r.nom if r.nom else 'sans nom'}")

# Test Transports
query_trans = """
PREFIX ns: <http://www.semanticweb.org/lenovo/ontologies/2025/9/untitled-ontology-2#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?transport ?type
WHERE {
    {
        ?transport rdf:type ns:Transport .
    } UNION {
        ?transport rdf:type ?subclass .
        ?subclass rdfs:subClassOf ns:Transport .
    }
    OPTIONAL { ?transport ns:typeTransport ?type }
}
"""
results_trans = list(g.query(query_trans))
print(f'\n🚗 Transports trouvés: {len(results_trans)}')
for r in results_trans:
    print(f"  - {r.transport} => {r.type if r.type else 'sans type'}")
