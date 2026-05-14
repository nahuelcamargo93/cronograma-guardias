import re

with open(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\soft_rules.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1. Identify the blocks
# First loop starts at line 82 (index 81)
# First loop ends at line 587 (index 586)
# Equidad block is 588-612 (index 587-611)
# Second loop starts at 613 (index 612)

loop1_start = 81
loop1_end = 586
equidad_block = lines[587:612]
loop2_start = 612
loop2_end = 806 # approximately

# 2. Extract loop 2 body (indented)
loop2_body = lines[613:loop2_end]

# 3. Fix loop 2 body: replace persona['Nombre'] -> nombre, emp.findes... -> emp.findes... (already done maybe?)
# Actually, let's just replace persona -> emp and persona['Nombre'] -> emp.nombre
fixed_loop2_body = []
for line in loop2_body:
    new_line = line.replace("persona['Nombre']", "emp.nombre")
    new_line = new_line.replace("persona", "emp")
    fixed_loop2_body.append(new_line)

# 4. Construct the new file
new_lines = lines[:loop1_start]
new_lines.extend(equidad_block)
new_lines.append(lines[loop1_start]) # for emp in empleados:
new_lines.extend(lines[loop1_start+1:loop1_end+1])
new_lines.extend(fixed_loop2_body)
new_lines.extend(lines[loop2_end:])

with open(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\soft_rules.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("soft_rules.py unificado y corregido")
