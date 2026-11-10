import os
import json
import time
import random
import urllib.request
import urllib.error
from datetime import timedelta
from difflib import SequenceMatcher
from typing import Optional

from ddgs import DDGS
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator

from directori.models import ZonaCerca, ServeiPsicologia


# ==========================================
# 1. MODELS PYDANTIC
# ==========================================

class ServeiPydantic(BaseModel):
    nom: str = Field(..., min_length=1)
    adreca: Optional[str] = None
    poblacio: str = Field(..., min_length=1)
    telefon: Optional[str] = None
    url: Optional[str] = None
    descripcio: str = Field(..., min_length=1)
    latitud: Optional[float] = Field(None, ge=41.6, le=42.5)
    longitud: Optional[float] = Field(None, ge=1.7, le=3.4)

    @field_validator("adreca", "telefon", "url", mode="before")
    @classmethod
    def netejar_nuls(cls, valor):
        if isinstance(valor, str) and valor.strip().lower() in ("", "null", "none", "n/a"):
            return None
        return valor


LlistaServeisAdapter = TypeAdapter(list[ServeiPydantic])


# ==========================================
# 2. COMANDA DE DJANGO
# ==========================================

class Command(BaseCommand):
    help = "Cerca nous serveis reals de psicologia per a la zona menys actualitzada."

    def _normalitzar_url(self, url: Optional[str]) -> str:
        if not url:
            return ""
        net = url.strip().lower()
        for prefix in ("https://", "http://", "www."):
            if net.startswith(prefix):
                net = net[len(prefix):]
        return net.rstrip("/")

    def es_duplicat(self, nou: ServeiPydantic, existents) -> bool:
        nom_nou = nou.nom.strip().lower()
        tel_nou = "".join(filter(str.isdigit, nou.telefon or ""))
        url_nou = self._normalitzar_url(nou.url)

        for ex in existents:
            # 1. Coincidència exacta de telèfon (últims 9 dígits)
            tel_ex = "".join(filter(str.isdigit, ex.telefon or ""))
            if tel_nou and len(tel_nou) >= 9 and tel_nou[-9:] == tel_ex[-9:]:
                return True

            # 2. Coincidència exacta de domini/URL normalitzada
            url_ex = self._normalitzar_url(ex.url)
            if url_nou and url_ex and url_nou == url_ex:
                return True

            # 3. Similitud de nom (Fuzzy matching > 85%)
            similitud = SequenceMatcher(None, nom_nou, ex.nom.strip().lower()).ratio()
            if similitud > 0.85:
                return True

        return False

    def handle(self, *args, **options):
        API_KEY = os.environ.get("GEMINI_API_KEY")
        if not API_KEY:
            self.stderr.write(self.style.ERROR("Falta la variable d'entorn GEMINI_API_KEY"))
            return

        HOST = "generativelanguage.googleapis.com"
        MODEL = "gemini-3.1-flash-lite"
        URL = f"https://{HOST}/v1beta/models/{MODEL}:generateContent"

        # 1. Selecció rotativa: zones mai cercades o revisades fa més de 15 dies
        data_limit = timezone.now() - timedelta(days=15)
        zona = (
            ZonaCerca.objects.filter(activa=True)
            .filter(Q(ultima_cerca__isnull=True) | Q(ultima_cerca__lt=data_limit))
            .order_by('ultima_cerca')
            .first()
        )
        if not zona:
            self.stdout.write("Totes les zones actives s'han revisat en els darrers 15 dies.")
            return

        self.stdout.write("=" * 50)
        self.stdout.write(f" CERCA REAL DE SERVEIS: {zona.nom}")
        self.stdout.write("=" * 50)

        # 2. Cerca real a internet amb DuckDuckGo (consulta neta amb rescat en castellà)
        if zona.nom.lower() == zona.municipi_base.lower():
            consulta_web = f"serveis de psicologia psicolegs a {zona.municipi_base} Girona"
        else:
            consulta_web = f"serveis depsicologia psicolegs a {zona.nom} Girona"

        resultats_web = []
        try:
            with DDGS() as ddgs:
                resultats_web = list(ddgs.text(consulta_web, region="es-es", max_results=15))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Avís DDGS per a '{consulta_web}': {e}"))

        if not resultats_web:
            try:
                with DDGS() as ddgs:
                    resultats_web = list(ddgs.text(f"psicologos {zona.municipi_base}", region="es-es", max_results=15))
            except Exception:
                pass


        if not resultats_web:
            self.stdout.write(f"Sense resultats web per a '{zona.nom}'. Actualitzant data de control...")
            zona.ultima_cerca = timezone.now()
            zona.intents_sense_nous += 1
            if zona.intents_sense_nous >= 4:
                zona.activa = False
            zona.save()
            return

        text_resultats = "\n".join(
            f"- Títol: {r.get('title', '')} | URL: {r.get('href', '')} | Resum: {r.get('body', '')}"
            for r in resultats_web
        )
        self.stdout.write(f"Recuperats {len(resultats_web)} resultats web reals. Analitzant amb Gemini...")

        # 3. Recuperem existents per evitar duplicats i preparem mostra aleatòria pel prompt
        existents = list(ServeiPsicologia.objects.filter(poblacio__iexact=zona.municipi_base))
        bloc_exclusio = ""
        if existents:
            mostra = random.sample(existents, min(len(existents), 45))
            llista_noms = "\n".join(f"- {s.nom}" for s in mostra)
            bloc_exclusio = f"\nNO incloguis aquests serveis que ja tinc registrats:\n{llista_noms}\n"

        prompt = f"""
Extreu un llistat de fins a 8 serveis, clíniques o professionals de psicologia reals situats a {zona.nom} (província de Girona) ÚNICAMENT a partir dels següents resultats de cerca web.

REGLES ESTRICTES:
1. No inventis cap nom, adreça, telèfon ni URL que no aparegui explícitament al text proporcionat.
2. Si cap dels resultats correspon a un servei de psicologia real d'aquesta zona, retorna una llista buida: []
{bloc_exclusio}
RESULTATS DE CERCA WEB:
{text_resultats}

Retorna exclusivament un JSON vàlid (array d'objectes) amb aquests camps exactes:
- nom
- adreca (només via i número si surten al text, o null)
- poblacio (municipi real, ex: "{zona.municipi_base}")
- telefon (si surt al text, o null)
- url (la URL real dels resultats, o null)
- descripcio (breu resum basat en el text)
- latitud (número decimal float WGS84 aproximat del municipi/adreça dins Girona, o null)
- longitud (número decimal float WGS84 aproximat del municipi/adreça dins Girona, o null)
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
        for intent in range(4):
            try:
                self.stdout.write(f"\nIntent {intent + 1}/4...")
                inici = time.time()

                with urllib.request.urlopen(req, timeout=60) as response:
                    resultat = json.loads(
                        response.read().decode("utf-8")
                    )

                    temps = round(time.time() - inici, 2)

                    candidat = next(iter(resultat["candidates"]))
                    part = next(iter(candidat["content"]["parts"]))
                    resposta_ia = part["text"]

                    # Validem amb Pydantic
                    serveis_validats = LlistaServeisAdapter.validate_json(resposta_ia)
                    nous_guardats = 0

                    for item in serveis_validats:
                        if not self.es_duplicat(item, existents):
                            nou_registre = ServeiPsicologia.objects.create(
                                nom=item.nom,
                                adreca=item.adreca,
                                poblacio=item.poblacio,
                                telefon=item.telefon,
                                url=item.url,
                                descripcio=item.descripcio,
                                latitud=item.latitud,
                                longitud=item.longitud,
                                zona_origen=zona
                            )
                            existents.append(nou_registre)
                            nous_guardats += 1

                    # Actualitzem estat i control d'esgotament de la zona
                    zona.ultima_cerca = timezone.now()
                    if nous_guardats == 0:
                        zona.intents_sense_nous += 1
                        if zona.intents_sense_nous >= 4:
                            zona.activa = False
                            self.stdout.write(self.style.WARNING(
                                f"Zona '{zona.nom}' desactivada automàticament (4 intents seguits sense nous resultats)."
                            ))
                    else:
                        zona.intents_sense_nous = 0

                    zona.save()

                    self.stdout.write(self.style.SUCCESS(
                        f"\nTemps de resposta: {temps} segons | Nous serveis guardats a PostgreSQL: {nous_guardats}"
                    ))
                    break

            except urllib.error.HTTPError as e:
                missatge = e.read().decode("utf-8")
                self.stderr.write(f"\nERROR HTTP: {e.code}")
                self.stderr.write(missatge)

                if e.code not in (429, 500, 502, 503, 504):
                    break

                if intent < 3:
                    espera = 5 * (2 ** intent)
                    self.stdout.write(f"Nou intent en {espera} segons...")
                    time.sleep(espera)

            except ValidationError as e:
                self.stderr.write("\nERROR DE VALIDACIÓ PYDANTIC:")
                self.stderr.write(e.json(indent=2))
                break

            except json.JSONDecodeError as e:
                self.stderr.write("\nERROR: Gemini no ha retornat un JSON vàlid.")
                self.stderr.write(repr(e))
                break

            except Exception as e:
                self.stderr.write("\nERROR INESPERAT:")
                self.stderr.write(repr(e))
                break
