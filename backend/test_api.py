import requests
import json

BASE_URL = "http://localhost:5000/api"

print("=== Test des nouvelles API ===\n")

# Test Services
try:
    r = requests.get(f"{BASE_URL}/services")
    services = r.json()
    print(f"✅ Services: {len(services)} trouvés")
    for s in services[:2]:
        print(f"   - {s.get('nom', s.get('uri'))}")
except Exception as e:
    print(f"❌ Services: {e}")

# Test Personnes
try:
    r = requests.get(f"{BASE_URL}/personnes")
    personnes = r.json()
    print(f"\n✅ Personnes: {len(personnes)} trouvées")
    for p in personnes:
        print(f"   - {p.get('nom', p.get('uri'))} ({p.get('age', 'N/A')} ans)")
except Exception as e:
    print(f"\n❌ Personnes: {e}")

# Test Nourritures
try:
    r = requests.get(f"{BASE_URL}/nourritures")
    nourritures = r.json()
    print(f"\n✅ Nourritures: {len(nourritures)} trouvées")
    for n in nourritures:
        print(f"   - {n.get('nom', n.get('uri'))}")
except Exception as e:
    print(f"\n❌ Nourritures: {e}")

# Test Equipements
try:
    r = requests.get(f"{BASE_URL}/equipements")
    equipements = r.json()
    print(f"\n✅ Équipements: {len(equipements)} trouvés")
    for e in equipements:
        print(f"   - {e.get('nom', e.get('uri'))}")
except Exception as ex:
    print(f"\n❌ Équipements: {ex}")

# Test Certifications
try:
    r = requests.get(f"{BASE_URL}/certifications")
    certifications = r.json()
    print(f"\n✅ Certifications: {len(certifications)} trouvées")
    for c in certifications:
        print(f"   - {c.get('nom', c.get('uri'))} (Valid: {c.get('dateValidite', 'N/A')})")
except Exception as e:
    print(f"\n❌ Certifications: {e}")
