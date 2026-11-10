from django.contrib import admin
from .models import ZonaCerca, ServeiPsicologia


@admin.register(ZonaCerca)
class ZonaCercaAdmin(admin.ModelAdmin):
    list_display = ('nom', 'municipi_base', 'activa', 'intents_sense_nous', 'ultima_cerca')
    list_filter = ('activa', 'municipi_base')
    list_editable = ('activa',)


@admin.action(description="✅ Validar serveis seleccionats (publicar al mapa)")
def validar_serveis(modeladmin, request, queryset):
    queryset.update(estat=ServeiPsicologia.EstatValidacio.VALIDAT)


@admin.action(description="❌ Rebutjar serveis seleccionats")
def rebutjar_serveis(modeladmin, request, queryset):
    queryset.update(estat=ServeiPsicologia.EstatValidacio.REBUTJAT)


@admin.register(ServeiPsicologia)
class ServeiPsicologiaAdmin(admin.ModelAdmin):
    list_display = ('nom', 'poblacio', 'telefon', 'estat', 'latitud', 'longitud', 'creat_el')
    list_filter = ('estat', 'poblacio', 'zona_origen')
    search_fields = ('nom', 'adreca', 'descripcio')
    list_editable = ('estat',)
    actions = [validar_serveis, rebutjar_serveis]
    readonly_fields = ('creat_el', 'zona_origen')
