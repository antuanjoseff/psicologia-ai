from django.db import models

class ZonaCerca(models.Model):
    nom = models.CharField(max_length=150, unique=True, help_text="Ex: 'Olot' o 'Girona - Eixample'")
    municipi_base = models.CharField(max_length=100, help_text="Municipi principal per filtrar duplicats")
    activa = models.BooleanField(default=True)
    ultima_cerca = models.DateTimeField(null=True, blank=True)
    # NOU: Comptador per desactivar zones on ja no apareixen serveis nous
    intents_sense_nous = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ultima_cerca', 'id']
        verbose_name = "Zona de cerca"
        verbose_name_plural = "Zones de cerca"

    def __str__(self):
        return f"{self.nom} ({self.municipi_base})"


class ServeiPsicologia(models.Model):
    class EstatValidacio(models.TextChoices):
        PENDENT = 'PENDENT', 'Pendent de revisió'
        VALIDAT = 'VALIDAT', 'Validat (visible al mapa)'
        REBUTJAT = 'REBUTJAT', 'Rebutjat / Duplicat'

    nom = models.CharField(max_length=200)
    adreca = models.CharField(max_length=255, null=True, blank=True)
    poblacio = models.CharField(max_length=100)
    telefon = models.CharField(max_length=50, null=True, blank=True)
    url = models.URLField(max_length=300, null=True, blank=True)
    descripcio = models.TextField()
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

    estat = models.CharField(
        max_length=20,
        choices=EstatValidacio.choices,
        default=EstatValidacio.PENDENT
    )
    zona_origen = models.ForeignKey(ZonaCerca, on_delete=models.SET_NULL, null=True, blank=True)
    creat_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Servei de psicologia"
        verbose_name_plural = "Serveis de psicologia"

    def __str__(self):
        return f"{self.nom} - {self.poblacio} [{self.estat}]"
