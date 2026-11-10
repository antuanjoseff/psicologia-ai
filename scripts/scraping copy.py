import json
import urllib.request
import urllib.error
import time
import os

# ==========================================
# 1. CONFIGURACIÓ
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash-lite"

URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

# ==========================================
# 2. CONSTRUCCIÓ DEL PROMPT
# ==========================================

prompt = """
Utilitza l'eina de cerca de Google per trobar 5 serveis, clíniques o professionals de psicologia reals i verificats a la província de Girona.
Extreu les seves dades reals de contacte (telèfon i web oficial) directament dels resultats de cerca. No t'inventis cap dada.

Retorna exclusivament un JSON vàlid que sigui una llista d'objectes (array de JSON), on cada objecte tingui exactament aquests camps:
- nom
- telefon
- url
- descripcio

Si d'algun servei no trobes la URL oficial o el telèfon als resultats de cerca, posa null en aquell camp.
Respon NOMÉS amb el JSON pur, sense text introductori ni explicacions.
"""


payload = {
    "contents": [{
        "parts": [{
            "text": prompt
        }]
    }],
    "tools": [
        {"googleSearch": {}}
    ],
    "generationConfig": {
        "temperature": 0.1
    }
}

headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": API_KEY
}

# ==========================================
# 3. PREPARACIÓ DE LA PETICIÓ
# ==========================================

dades_bytes = json.dumps(payload).encode("utf-8")

req = urllib.request.Request(
    URL,
    data=dades_bytes,
    headers=headers,
    method="POST"
)

# ==========================================
# 4. EXECUCIÓ AMB REINTENTS
# ==========================================

print("=" * 50)
print(" CERCA DE SERVEIS DE PSICOLOGIA AMB GEMINI")
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

            resposta_ia = (
                resultat["candidates"][0]
                ["content"]["parts"][0]["text"]
            )

            inici_json = resposta_ia.find("[")
            fi_json = resposta_ia.rfind("]") + 1
            resposta_ia = resposta_ia[inici_json:fi_json]

            # Convertim la resposta de Gemini en JSON Python
            dades_extretes = json.loads(resposta_ia)


            print("\n" + "=" * 50)
            print(f" SERVEIS TROBATS")
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
