import os
import json
import urllib.request
import urllib.error
import time

# ==========================================
# 1. CONFIGURACIÓ
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")

MODEL = "gemini-3.1-flash-lite"
# gemini-3.6-flash   Model Flash general
# gemini-3.5-flash   Alternativa Flash
# gemini-3.5-flash-lite    Lleuger i ràpid
# gemini-3.1-flash-lite  Alternativa lleugera

URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

# ==========================================
# 2. TEXT PSICOLÒGIC
# ==========================================

text_psico = (
    "Vull anar del campus de montilivi fins a maçanet els dilluns al matí"
)

# ==========================================
# 3. CONSTRUCCIÓ DEL PROMPT
# ==========================================

prompt = f"""
Extreu la informació del text següent.

Retorna exclusivament un JSON vàlid amb aquests camps:
- municipi destí
- campus origen
- dia o dies de la setmana
- franja horària

No inventis informació.
Si algun camp no apareix al text, retorna null.

TEXT:
{text_psico}
"""

payload = {
    "contents": [{
        "parts": [{
            "text": prompt
        }]
    }],
    "generationConfig": {
        "temperature": 0,
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
print(" ANÀLISI DE TEXT PSICOLÒGIC AMB GEMINI")
print("=" * 50)

for intent in range(4):

    try:
        print(f"\nIntent {intent + 1}/4...")
        print("Enviant text a Gemini...")

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

            # Convertim la resposta de Gemini en JSON Python
            dades_extretes = json.loads(resposta_ia)

            print("\n" + "=" * 50)
            print(" INFORMACIÓ EXTRETA")
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
