from directori.models import ZonaCerca

zones_girona = [
    # ==========================================
    # 1. GIRONA CIUTAT (Dividida per barris i especialitats)
    # ==========================================
    ("Girona - Barri Vell i Mercadal", "Girona"),
    ("Girona - Eixample Nord i Plaça Catalunya", "Girona"),
    ("Girona - Eixample Sud i Migdia", "Girona"),
    ("Girona - Devesa i Güell", "Girona"),
    ("Girona - Santa Eugènia i Can Gibert del Pla", "Girona"),
    ("Girona - Sant Narcís", "Girona"),
    ("Girona - Palau i Montilivi", "Girona"),
    ("Girona - Pont Major, Pedret i Campdorà", "Girona"),
    ("Girona - Psicologia infantil i juvenil", "Girona"),
    ("Girona - Teràpia de parella i sexologia", "Girona"),
    ("Girona - Neuropsicologia i psicogeriatria", "Girona"),
    ("Girona - Psiquiatria i salut mental clínica", "Girona"),

    # ==========================================
    # 2. GIRONÈS (Resta de municipis principals)
    # ==========================================
    ("Salt", "Salt"),
    ("Cassà de la Selva", "Cassà de la Selva"),
    ("Llagostera", "Llagostera"),
    ("Sarrià de Ter i Sant Julià de Ramis", "Sarrià de Ter"),
    ("Bescanó i Vilablareix", "Bescanó"),
    ("Quart i Fornells de la Selva", "Quart"),
    ("Celrà i Bordils", "Celrà"),

    # ==========================================
    # 3. ALT EMPORDÀ
    # ==========================================
    ("Figueres - Centre i Rambla", "Figueres"),
    ("Figueres - Eixample i barris", "Figueres"),
    ("Figueres - Psicologia infantil i clínica", "Figueres"),
    ("Roses", "Roses"),
    ("Castelló d'Empúries i Empuriabrava", "Castelló d'Empúries"),
    ("L'Escala", "L'Escala"),
    ("Llançà i Portbou", "Llançà"),
    ("Cadaqués i El Port de la Selva", "Cadaqués"),
    ("Vilafant", "Vilafant"),
    ("La Jonquera i Agullana", "La Jonquera"),

    # ==========================================
    # 4. BAIX EMPORDÀ
    # ==========================================
    ("Palafrugell", "Palafrugell"),
    ("Sant Feliu de Guíxols", "Sant Feliu de Guíxols"),
    ("Palamós", "Palamós"),
    ("La Bisbal d'Empordà", "La Bisbal d'Empordà"),
    ("Castell-Platja d'Aro i S'Agaró", "Castell d'Aro, Platja d'Aro i s'Agaró"),
    ("Torroella de Montgrí i L'Estartit", "Torroella de Montgrí"),
    ("Calonge i Sant Antoni", "Calonge i Sant Antoni"),
    ("Santa Cristina d'Aro", "Santa Cristina d'Aro"),
    ("Begur i Pals", "Begur"),

    # ==========================================
    # 5. LA SELVA
    # ==========================================
    ("Blanes - Centre i Els Pins", "Blanes"),
    ("Blanes - Barris i especialitats", "Blanes"),
    ("Lloret de Mar - Centre", "Lloret de Mar"),
    ("Lloret de Mar - Fenals i urbanitzacions", "Lloret de Mar"),
    ("Santa Coloma de Farners", "Santa Coloma de Farners"),
    ("Arbúcies i Sant Hilari Sacalm", "Arbúcies"),
    ("Vidreres i Maçanet de la Selva", "Vidreres"),
    ("Tossa de Mar", "Tossa de Mar"),
    ("Sils i Caldes de Malavella", "Caldes de Malavella"),
    ("Hostalric i Breda", "Hostalric"),
    ("Anglès i Amer", "Anglès"),

    # ==========================================
    # 6. LA GARROTXA
    # ==========================================
    ("Olot - Centre i Eixample", "Olot"),
    ("Olot - Barris i especialitats", "Olot"),
    ("Besalú i Castellfollit de la Roca", "Besalú"),
    ("Sant Joan les Fonts i La Vall d'en Bas", "La Vall d'en Bas"),
    ("Les Preses i Santa Pau", "Les Preses"),

    # ==========================================
    # 7. PLA DE L'ESTANY
    # ==========================================
    ("Banyoles - Centre", "Banyoles"),
    ("Banyoles - Barris i especialitats", "Banyoles"),
    ("Porqueres i Cornellà del Terri", "Porqueres"),

    # ==========================================
    # 8. EL RIPOLLÈS
    # ==========================================
    ("Ripoll", "Ripoll"),
    ("Sant Joan de les Abadesses", "Sant Joan de les Abadesses"),
    ("Camprodon i Vall de Camprodon", "Camprodon"),
    ("Campdevànol i Ribes de Freser", "Campdevànol"),

    # ==========================================
    # 9. BAIXA CERDANYA (Part gironina)
    # ==========================================
    ("Puigcerdà", "Puigcerdà"),
    ("Alp, Llívia i Bolvir", "Puigcerdà"),
]

creades = 0
for nom_zona, municipi in zones_girona:
    _, creada = ZonaCerca.objects.get_or_create(
        nom=nom_zona,
        defaults={"municipi_base": municipi}
    )
    if creada:
        creades += 1

print(f"Procés completat: {creades} zones noves afegides (Total: {ZonaCerca.objects.count()}).")
