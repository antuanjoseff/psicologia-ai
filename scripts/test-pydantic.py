import json
import urllib.request
import urllib.error
import urllib.parse
import time
import os
from typing import Optional
from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator

# ==========================================
# 1. CONFIGURACIÓ
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("Error: Falta definir la variable d'entorn GEMINI_API_KEY")

MODEL = "gemini-3.1-flash-lite"

URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

# ==========================================
# 2. MODELS PYDANTIC DE VALIDACIÓ
# ==========================================

class ServeiPsicologia(BaseModel):
    nom: str = Field(..., min_length=1)
    adreca: Optional[str] = None
    poblacio: Optional[str] = None
    telefon: Optional[str] = None
    url: Optional[str] = None
    descripcio: str = Field(..., min_length=1)
    # Pydantic rebutjarà automàticament qualsevol coordenada fora de la província de Girona
    latitud: Optional[float] = Field(None, ge=41.6, le=42.5)
    longitud: Optional[float] = Field(None, ge=1.7, le=3.4)

    @field_validator("adreca", "poblacio", "telefon", "url", mode="before")
    @classmethod
    def netejar_nuls(cls, valor):
        if isinstance(valor, str) and valor.strip().lower() in ("", "null", "none", "n/a"):
            return None
        return valor


# TypeAdapter permet validar directament una llista d'objectes sense embolcallar-la
LlistaServeisAdapter = TypeAdapter(list[ServeiPsicologia])

class PartResposta(BaseModel):
    text: str

class ContingutResposta(BaseModel):
    parts: list[PartResposta]

class CandidatResposta(BaseModel):
    content: ContingutResposta

class RespostaAPI(BaseModel):
    candidates: list[CandidatResposta]


# ==========================================
# 3. CONSTRUCCIÓ DEL PROMPT
# ==========================================

prompt = """
Genera un llistat de 5 serveis, clíniques o professionals de psicologia reals a la província de Girona.
Busca informació real i extreu les dades de contacte i ubicació.

Retorna exclusivament un JSON vàlid que sigui una llista d'objectes (array de JSON), on cada objecte tingui exactament aquests camps:
- nom
- adreca
- poblacio
- telefon
- url
- descripcio
- latitud
- longitud

Regles estrictes:
- latitud i longitud: Han de ser números decimals (float) en format WGS84 (EPSG:4326) corresponents a l'adreça o municipi del servei dins la província de Girona (exemple: 41.9794, 2.8214). Si no saps situar-lo, posa null.
- Si d'algun servei no trobes la URL oficial, el telèfon o l'adreça, posa null en aquell camp, però prioritza serveis reals dels quals tinguis tota la informació.
No afegeixis text de benvinguda, ni explicacions, ni blocs de codi markdown (com ```json). Només el text del JSON.
"""



payload = {
    "contents": [{
        "parts": [{
            "text": prompt
        }]
    }],
    "generationConfig": {
        "temperature": 0.2,
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
print(" CERCA DE SERVEIS DE PSICOLOGIA AMB GEMINI")
print("=" * 50)

for intent in range(4):

    try:
        print(f"\nIntent {intent + 1}/4...")
        print("Demanant dades a Gemini...")

        inici = time.time()

        with urllib.request.urlopen(req, timeout=30) as response:

            resposta_crua = response.read().decode("utf-8")
            temps = round(time.time() - inici, 2)

            # Validem l'estructura de la resposta de Google amb Pydantic
            resposta_google = RespostaAPI.model_validate_json(resposta_crua)
            primer_candidat = next(iter(resposta_google.candidates))
            primera_part = next(iter(primer_candidat.content.parts))
            resposta_ia = primera_part.text


            # Pydantic valida tota la llista, incloses les coordenades, en un sol pas
            serveis_validats = LlistaServeisAdapter.validate_json(resposta_ia)
            dades_extretes = [s.model_dump() for s in serveis_validats]



            print("\n" + "=" * 50)
            print(f" SERVEIS TROBATS ({len(dades_extretes)})")
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

    except ValidationError as e:

        print("\nERROR: Les dades de Gemini no compleixen l'esquema esperat.")
        print(e.json(indent=2))
        break

    except json.JSONDecodeError as e:

        print("\nERROR: Gemini no ha retornat un JSON vàlid.")
        print(repr(e))
        break

    except Exception as e:

        print("\nERROR INESPERAT:")
        print(repr(e))
        break

print("\nFinal del programa.")
