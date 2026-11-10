import json
import urllib.request
import urllib.error
import time
import os
from ddgs import DDGS

# ==========================================
# 1. CONFIGURACIÓ
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("Error: Falta definir la variable d'entorn GEMINI_API_KEY")

MODEL = "gemini-3.5-flash-lite"

URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

# ==========================================
# 2. CERCA REAL A INTERNET AMB DDGS
# ==========================================

print("=" * 50)
print(" CERCANT RESULTATS REALS AMB DUCKDUCKGO...")
print("=" * 50)

consulta_web = (
    f'psicòlegs psicologia blanes Girona contacte '
    f'-site:doctoralia.es -site:topdoctors.es -site:paginasamarillas.es -site:mundo-psicologos.com'
)
resultats_web = []

try:
    with DDGS() as ddgs:
        resultats_web = list(ddgs.text(consulta_web, region="es-es", max_results=12))
except Exception as e:
    print(f"Error fent la cerca amb DDGS: {e}")

if not resultats_web:
    print("No s'han obtingut resultats de cerca web. S'atura l'execució.")
    exit(1)

text_resultats = "\n".join(
    f"- Títol: {r.get('title', '')} | URL: {r.get('href', '')} | Resum: {r.get('body', '')}"
    for r in resultats_web
)

print(f"S'han recuperat {len(resultats_web)} resultats reals de la web.")

# ==========================================
# 3. CONSTRUCCIÓ DEL PROMPT I PAYLOAD
# ==========================================

prompt = f"""
Extreu un llistat de fins a 5 serveis, clíniques o professionals de psicologia reals i verificats a la província de Girona ÚNICAMENT a partir dels següents resultats de cerca web.
No inventis cap dada que no aparegui explícitament al text proporcionat.

RESULTATS DE CERCA WEB:
{text_resultats}

Retorna exclusivament un JSON vàlid que sigui una llista d'objectes (array de JSON), on cada objecte tingui exactament aquests camps:
- nom
- telefon (només si apareix al text, sinó posa null)
- url (la URL real extreta dels resultats)
- descripcio (breu resum basat en el text)

Respon NOMÉS amb el JSON pur, sense text introductori ni explicacions.
"""

payload = {
    "contents": [{
        "parts": [{
            "text": prompt
        }]
    }],
    "generationConfig": {
        "temperature": 0.1,
        "responseMimeType": "application/json"
    }
}

headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": API_KEY
}

# ==========================================
# 4. PREPARACIÓ DE LA PETICIÓ
# ==========================================

dades_bytes = json.dumps(payload).encode("utf-8")

req = urllib.request.Request(
    URL,
    data=dades_bytes,
    headers=headers,
    method="POST"
)

# ==========================================
# 5. EXECUCIÓ AMB REINTENTS
# ==========================================

print("=" * 50)
print(" ESTRUCTURANT DADES AMB GEMINI")
print("=" * 50)

for intent in range(4):

    try:
        print(f"\nIntent {intent + 1}/4...")
        print("Demanant dades a Gemini...")

        inici = time.time()

        with urllib.request.urlopen(req, timeout=30) as response:

            resultat = json.loads(
                response.read().decode("utf-8")
            )

            temps = round(time.time() - inici, 2)

            candidat = next(iter(resultat["candidates"]))
            part = next(iter(candidat["content"]["parts"]))
            resposta_ia = part["text"]

            inici_json = resposta_ia.find("[")
            fi_json = resposta_ia.rfind("]") + 1
            resposta_ia = resposta_ia[inici_json:fi_json]

            # Convertim la resposta de Gemini en JSON Python
            dades_extretes = json.loads(resposta_ia)

            print("\n" + "=" * 50)
            print(" SERVEIS TROBATS")
            print("=" * 50)

            print(json.dumps(
                dades_extretes,
                indent=4,
                ensure_ascii=False
            ))

            print("\nTemps de resposta:", temps, "segons")
            print("\nANÀLISI COMPLETADA CORRECTAMENT")

            break

    except urllib.error.HTTPError as e:

        missatge = e.read().decode("utf-8")

        print("\nERROR HTTP:", e.code)
        print(missatge)

        if e.code not in (429, 500, 502, 503, 504):
            break

        if intent < 3:
            espera = 5 * (2 ** intent)

            print(f"Nou intent en {espera} segons...")
            time.sleep(espera)

    except json.JSONDecodeError as e:

        print("\nERROR: Gemini no ha retornat un JSON vàlid.")
        print(repr(e))
        break

    except Exception as e:

        print("\nERROR INESPERAT:")
        print(repr(e))
        break

print("\nFinal del programa.")
