from database.queries import cargar_ajustes_reglas_personal
ajustes = cargar_ajustes_reglas_personal("2026-07-01", "2026-07-31")
print("Ajustes para Mora, Sergio Enrique:")
if "Mora, Sergio Enrique" in ajustes:
    for aj in ajustes["Mora, Sergio Enrique"]:
        print(aj)
else:
    print("Mora no tiene ajustes.")
