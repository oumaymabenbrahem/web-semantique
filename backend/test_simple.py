import requests
import json
import time

# Attendre que le serveur soit prêt
print("⏳ Attente du démarrage du serveur...")
time.sleep(3)

# Test simple
url = "http://localhost:5001/api/nl-query"

print("\n" + "="*60)
print("🧪 TEST: Ajout d'une personne")
print("="*60)

question = "Ajoute une personne Sophie qui a 25 ans"
print(f"\n❓ Question: {question}")

try:
    response = requests.post(
        url,
        json={"question": question},
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n📦 Réponse complète:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("success"):
            print("\n✅ SUCCÈS!")
            if result.get("action"):
                print(f"🔧 Action: {result['action'].upper()}")
                print(f"📝 Message: {result['message']}")
        else:
            print(f"\n❌ ÉCHEC: {result.get('error')}")
    else:
        print(f"\n❌ Erreur HTTP: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ Impossible de se connecter à http://localhost:5001")
    print("   Le serveur est-il démarré?")
except Exception as e:
    print(f"\n❌ Erreur: {str(e)}")

print("\n" + "="*60)
