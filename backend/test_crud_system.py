"""
Script de test pour le système CRUD complet
Teste les opérations CREATE, READ, UPDATE, DELETE via l'endpoint nl-query
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_nl_query(question):
    """Teste une requête en langage naturel"""
    print(f"\n{'='*60}")
    print(f"❓ Question: {question}")
    print('-'*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/nl-query",
            json={"question": question},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        result = response.json()
        
        if result.get("success"):
            print(f"✅ Succès!")
            
            if result.get("action"):
                # C'est une opération CRUD
                print(f"🔧 Action: {result['action'].upper()}")
                print(f"📝 Message: {result['message']}")
                
                if result.get("entity"):
                    print(f"📦 Entité:")
                    print(f"   Type: {result['entity'].get('type')}")
                    print(f"   URI: {result['entity'].get('uri')}")
                    print(f"   Attributs: {result['entity'].get('attributes')}")
            else:
                # C'est une requête SELECT
                print(f"📊 Résultats: {len(result.get('results', []))} trouvés")
                for i, res in enumerate(result.get('results', [])[:3], 1):
                    print(f"   {i}. {res}")
                    
            return True
        else:
            print(f"❌ Erreur: {result.get('error')}")
            if result.get('suggestion'):
                print(f"💡 Suggestion: {result['suggestion']}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au backend!")
        print("   Assurez-vous que le backend est démarré: cd backend; python app.py")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("🧪 TEST DU SYSTÈME CRUD COMPLET")
    print("="*60)
    
    tests = [
        # Test 1: Lire les personnes existantes
        ("READ", "Quelles sont toutes les personnes ?"),
        
        # Test 2: Créer une nouvelle personne
        ("CREATE", "Ajoute une personne Paul qui a 28 ans"),
        
        # Test 3: Vérifier que la personne est bien créée
        ("READ", "Quelles sont toutes les personnes ?"),
        
        # Test 4: Modifier l'âge de Paul
        ("UPDATE", "Modifie l'âge de Paul à 30 ans"),
        
        # Test 5: Vérifier la modification
        ("READ", "Quelles sont toutes les personnes ?"),
        
        # Test 6: Créer une destination
        ("CREATE", "Crée une destination Madagascar dans le pays Madagascar"),
        
        # Test 7: Lire toutes les destinations
        ("READ", "Quelles sont toutes les destinations ?"),
        
        # Test 8: Supprimer Paul
        ("DELETE", "Supprime la personne Paul"),
        
        # Test 9: Vérifier la suppression
        ("READ", "Quelles sont toutes les personnes ?"),
        
        # Test 10: Ajouter un service
        ("CREATE", "Ajoute un service Guide Touristique à 50 euros"),
        
        # Test 11: Lire tous les services
        ("READ", "Liste tous les services"),
    ]
    
    results = []
    for test_type, question in tests:
        time.sleep(1)  # Pause entre les tests
        success = test_nl_query(question)
        results.append((test_type, question, success))
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    
    for test_type, question, success in results:
        status = "✅" if success else "❌"
        print(f"{status} [{test_type}] {question[:50]}...")
    
    print("\n" + "="*60)
    print(f"🎯 Résultat: {passed}/{total} tests réussis ({passed*100//total}%)")
    print("="*60)
    
    if passed == total:
        print("🎉 Tous les tests sont passés! Le système CRUD fonctionne parfaitement!")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les logs ci-dessus.")
    
    print("\n💡 Prochaine étape: Testez dans l'interface web!")
    print("   1. Ouvrez http://localhost:52076")
    print("   2. Allez dans 'Poser une question'")
    print("   3. Essayez: 'Ajoute une personne Sophie qui a 25 ans'")
    print("   4. Retournez au tableau de bord pour voir le résultat!")

if __name__ == "__main__":
    main()
