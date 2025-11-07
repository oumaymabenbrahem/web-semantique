import requests
import json
import sys

# Test natural language query
url = "http://localhost:5000/api/nl-query"
headers = {"Content-Type": "application/json; charset=utf-8"}

questions = [
    "Quelles sont toutes les personnes ?",
    "Liste tous les services",
    "Quelles sont les certifications ?",
    "Quels sont les équipements ?",
    "Quelle nourriture est disponible ?"
]

print("🧪 Test des requêtes en langage naturel\n")
print("=" * 60)

for question in questions:
    print(f"\n❓ Question: {question}")
    print("-" * 60)
    
    try:
        response = requests.post(url, headers=headers, json={"question": question}, timeout=10)
        result = response.json()
        
        if result.get("success"):
            print(f"✅ Succès!")
            if "results" in result:
                print(f"📊 Résultats trouvés: {len(result['results'])}")
                for i, res in enumerate(result['results'][:3], 1):  # Show first 3
                    print(f"   {i}. {res}")
        else:
            print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au backend sur http://localhost:5000")
        print("   Veuillez redémarrer le backend avec: cd backend; python app.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")

print("\n" + "=" * 60)
print("✅ Tests terminés!")
