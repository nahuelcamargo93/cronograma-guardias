import math

print("=" * 60)
print("CALCULO EXACTO MIN/MAX HORAS - AGUILERA JULIO 2026")
print("=" * 60)

dias_del_mes = 31
dias_m = 31          # mes completo julio
dias_lic = 6         # 01/07 al 06/07

min_horas_personal = 140
max_horas_personal = 150
horas_por_semana_credito = 36

# Credito horario por licencia
horas_lic = int((horas_por_semana_credito / 7.0) * dias_lic + 0.5)
print(f"\nhoras_lic (credito) = (36/7) * {dias_lic} = {horas_lic}h")

# Piso (MIN)
piso = int((float(min_horas_personal) / dias_del_mes) * dias_m + 0.5)
print(f"\npiso = ({min_horas_personal}/{dias_del_mes}) * {dias_m} = {piso}h")

# Tope (MAX)
tope = int((float(max_horas_personal) / dias_del_mes) * dias_m + 0.5)
print(f"tope = ({max_horas_personal}/{dias_del_mes}) * {dias_m} = {tope}h")

# Restricciones sobre sum(vars_h)
min_real = piso - horas_lic
max_real = tope - horas_lic
print(f"\n>>> sum(horas_trabajadas) >= {piso} - {horas_lic} = {min_real}h")
print(f">>> sum(horas_trabajadas) <= {tope} - {horas_lic} = {max_real}h")
print(f"\n>>> VENTANA FACTIBLE: [{min_real}h, {max_real}h]")

# Turnos disponibles para Aguilera (EXCLUYE G_Planta => solo 12h shifts)
print("\n--- Turnos disponibles (G_Planta EXCLUIDO) ---")
turno_horas = 12
print(f"D_Planta: {turno_horas}h | N_Planta: {turno_horas}h")

print("\n--- Multiples de 12h dentro del rango [{}, {}] ---".format(min_real, max_real))
multiples = [n * turno_horas for n in range(0, 30) if min_real <= n * turno_horas <= max_real]
print(f"Multiples de 12 en [{min_real}, {max_real}]: {multiples}")

if not multiples:
    print("\n!!! INFACTIBLE: NO existe ningún múltiplo de 12 en la ventana !!!")
    n_min = math.ceil(min_real / turno_horas)
    n_max = math.floor(max_real / turno_horas)
    print(f"    Turnos necesarios mínimo: {n_min} x 12h = {n_min*12}h  (requiere min {min_real}h)")
    print(f"    Turnos permitidos máximo: {n_max} x 12h = {n_max*12}h  (límite max {max_real}h)")
    print(f"\n--- SOLUCIONES ---")
    # Opcion A: bajar min
    for new_min in range(min_horas_personal - 10, min_horas_personal):
        new_piso = int((float(new_min) / dias_del_mes) * dias_m + 0.5)
        new_min_real = new_piso - horas_lic
        if any(new_min_real <= n * 12 <= max_real for n in range(1, 30)):
            print(f"  Opción A: bajar min_horas a {new_min} → min_real={new_min_real} → {new_min_real}≤{n_min*12}≤{max_real} ✓")
            break
    # Opcion B: subir max
    for new_max in range(max_horas_personal + 1, max_horas_personal + 15):
        new_tope = int((float(new_max) / dias_del_mes) * dias_m + 0.5)
        new_max_real = new_tope - horas_lic
        if any(min_real <= n * 12 <= new_max_real for n in range(1, 30)):
            print(f"  Opción B: subir max_horas a {new_max} → max_real={new_max_real} → {min_real}≤{n_max*12+12}≤{new_max_real} ✓")
            break
else:
    print(f"\n>>> OK: {len(multiples)} combinaciones válidas posibles")
