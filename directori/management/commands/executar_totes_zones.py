import os
import time
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from directori.models import ZonaCerca


class Command(BaseCommand):
    help = "Executa la comanda cercar_serveis per a totes les zones pendents."

    def handle(self, *args, **options):
        if not os.environ.get("GEMINI_API_KEY"):
            self.stderr.write(self.style.ERROR("ERROR: Falta definir la variable d'entorn GEMINI_API_KEY."))
            return

        data_limit = timezone.now() - timedelta(days=15)
        pendents = ZonaCerca.objects.filter(activa=True).filter(
            Q(ultima_cerca__isnull=True) | Q(ultima_cerca__lt=data_limit)
        ).count()

        if pendents == 0:
            self.stdout.write("Totes les zones actives estan actualitzades (revisades en els darrers 15 dies).")
            return

        self.stdout.write("=" * 60)
        self.stdout.write(f" INICIANT PROCÉS MASSIU: {pendents} ZONES PENDENTS")
        self.stdout.write("=" * 60)

        for i in range(pendents):
            self.stdout.write(f"\n>>> Executant zona {i + 1} de {pendents}...")

            try:
                call_command("cercar_serveis")
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\nProcés aturat manualment per l'usuari (Ctrl + C)."))
                break
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"\nError inesperat a l'iteració {i + 1}: {e}"))

            if i < pendents - 1:
                pausa = 10
                self.stdout.write(f"Esperant {pausa} segons abans de la següent zona...")
                time.sleep(pausa)

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(" PROCÉS COMPLETAT"))
        self.stdout.write("=" * 60)
