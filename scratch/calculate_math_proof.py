import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

# Get total active employees
c.execute("SELECT count(*) FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
total_employees = c.fetchone()[0]

# Let's count how many weeks in August
# August 2026 has 31 days, which spans across 6 calendar weeks.
# Let's look at the demand config for a standard week (5 weekdays + 2 weekend days)
# For 'N' (Night):
# Weekdays: 7 min, 8 max
# Weekend: 7 min, 8 max
# So daily demand is at least 7.
# For 7 days, weekly demand is 7 * 7 = 49 shifts.

# For 'TN' (Tarde Noche):
# Weekdays: 7 min, 11 max
# Weekend: 7 min, 10 max
# So daily demand is at least 7.
# For 7 days, weekly demand is 7 * 7 = 49 shifts.

print(f"Total empleados disponibles: {total_employees}")
print(f"Demanda mínima de Noche (N) por día: 7")
print(f"Demanda mínima de Tarde Noche (TN) por día: 7")
print(f"Demanda semanal mínima de N: 7 * 7 = 49 turnos")
print(f"Demanda semanal mínima de TN: 7 * 7 = 49 turnos")
print(f"Demanda semanal mínima total (N + TN): 49 + 49 = 98 turnos\n")

# With a distance of 3 weeks (ventana de 4 semanas), each employee can only have N/TN active in 1 out of 4 weeks.
# Therefore, in any given week, at most 1/4 of the staff can have an N shift assigned, and at most 1/4 can have a TN shift assigned.
max_active_staff_per_week = total_employees / 4
print(f"Máximo de empleados activos para N por semana (52 / 4): {max_active_staff_per_week:.1f}")
print(f"Máximo de empleados activos para TN por semana (52 / 4): {max_active_staff_per_week:.1f}")

# To cover 49 shifts of N with 13 employees, each active employee must work:
shifts_n_per_emp = 49 / max_active_staff_per_week
print(f"Turnos N que debería hacer cada empleado activo en su semana: {shifts_n_per_emp:.2f}")

# To cover 49 shifts of TN with 13 employees, each active employee must work:
shifts_tn_per_emp = 49 / max_active_staff_per_week
print(f"Turnos TN que debería hacer cada empleado activo en su semana: {shifts_tn_per_emp:.2f}")

# Total late/night shifts per active employee in their active week:
total_shifts_per_emp = 98 / max_active_staff_per_week
print(f"Total turnos (N + TN) que debería hacer cada empleado activo en su semana: {total_shifts_per_emp:.2f} turnos")

conn.close()
