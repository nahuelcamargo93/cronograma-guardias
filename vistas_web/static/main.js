let currentOrgId = null;
let currentServiceId = null;

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadOrganizaciones();
});

async function loadOrganizaciones() {
    try {
        const response = await fetch('/api/organizaciones');
        const orgs = await response.json();
        const select = document.getElementById('select-org');
        
        orgs.forEach(org => {
            const opt = document.createElement('option');
            opt.value = org.id;
            opt.textContent = org.nombre;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Error al cargar organizaciones:", err);
    }
}

async function loadServices() {
    const orgId = document.getElementById('select-org').value;
    if (!orgId) return;
    
    currentOrgId = orgId;
    try {
        const response = await fetch(`/api/servicios/${orgId}`);
        const services = await response.json();
        const select = document.getElementById('select-service');
        
        // Clear existing
        select.innerHTML = '<option value="">Seleccionar...</option>';
        
        services.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = s.nombre;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Error al cargar servicios:", err);
    }
}

function onServiceChange() {
    const serviceId = document.getElementById('select-service').value;
    if (!serviceId) return;
    
    currentServiceId = serviceId;
    
    // Refresh subtitle
    const serviceName = document.getElementById('select-service').options[document.getElementById('select-service').selectedIndex].text;
    document.getElementById('page-subtitle').textContent = `Servicio: ${serviceName}`;

    // Refresh active section data
    const activeSection = document.querySelector('.nav-item.active').getAttribute('onclick').match(/'([^']+)'/)[1];
    refreshActiveSection(activeSection);
}

function refreshActiveSection(sectionId) {
    if (sectionId === 'rules') loadRulesData();
    if (sectionId === 'overview') loadCronogramasHistorial();
    // Add other sections here
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    document.getElementById(`section-${sectionId}`).classList.add('active');
    
    // Find matching nav item
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('onclick').includes(`'${sectionId}'`)) {
            item.classList.add('active');
        }
    });

    const titles = {
        'overview': 'Vista General',
        'calendar': 'Calendario / Grilla',
        'rules': 'Reglas y Ajustes',
        'staff': 'Gestión de Personal'
    };
    document.getElementById('page-title').textContent = titles[sectionId];
    
    refreshActiveSection(sectionId);
}

async function loadDashboardData() {
    if (!currentServiceId) return;
    
    const serviceName = document.getElementById('select-service').options[document.getElementById('select-service').selectedIndex].text;
    document.getElementById('page-subtitle').textContent = `Servicio: ${serviceName}`;
    
    loadCronogramasHistorial();
}

async function loadCronogramasHistorial() {
    if (!currentServiceId) return;
    
    try {
        const response = await fetch(`/api/cronogramas/${currentServiceId}`);
        const data = await response.json();
        const tbody = document.getElementById('cronogramas-list');
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No hay cronogramas generados para este servicio</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        data.forEach(c => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${c.id}</td>
                <td>${c.fecha_inicio} a ${c.fecha_fin}</td>
                <td>${new Date(c.creado_en).toLocaleString()}</td>
                <td>${c.notas || '-'}</td>
                <td>
                    <button class="btn-secondary" onclick="viewCronograma(${c.id})">Ver Detalle</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error al cargar historial:", err);
    }
}

let lastRulesResponse = null;
let lastCatalogResponse = null;
let currentRulesSubTab = 'general';

async function loadRulesData() {
    if (!currentServiceId) {
        document.getElementById('rules-content-view').innerHTML = '<div class="empty-state">Selecciona un servicio para ver las reglas</div>';
        return;
    }
    
    const view = document.getElementById('rules-content-view');
    view.innerHTML = '<div class="empty-state">Cargando reglas...</div>';

    try {
        console.log(`Cargando reglas para servicio: ${currentServiceId}`);
        const [rulesRes, catalogRes] = await Promise.all([
            fetch(`/api/reglas/${currentServiceId}`),
            fetch(`/api/reglas_catalogo/${currentServiceId}`)
        ]);
        lastRulesResponse = await rulesRes.json();
        lastCatalogResponse = await catalogRes.json();
        
        // Show current sub-tab
        showRuleSub(currentRulesSubTab);
    } catch (err) {
        console.error("Error al cargar reglas:", err);
        view.innerHTML = '<div class="alert danger">Error al cargar datos del servicio</div>';
    }
}

function showRuleSub(type) {
    currentRulesSubTab = type;
    if (!lastRulesResponse) return;

    // Update tab UI
    document.querySelectorAll('.rule-tab').forEach(t => {
        t.classList.toggle('active', t.getAttribute('data-type') === type);
    });

    const view = document.getElementById('rules-content-view');
    const showInactivas = document.getElementById('toggle-inactivas') && document.getElementById('toggle-inactivas').checked;
    let html = '';

    if (type === 'general') {
        // Decide fuente de datos según checkbox
        const entries = showInactivas && lastCatalogResponse
            ? lastCatalogResponse.map(r => [r.codigo_regla, r, r.activa])
            : Object.entries(lastRulesResponse.reglas_generales).map(([k, v]) => [k, v, true]);

        html = `
            <div style="display:flex; align-items:center; justify-content:space-between; padding: 0 0 16px 0;">
                <div>
                    <h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 4px;">Reglas de Negocio</h3>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">Haz clic en una fila para ver el detalle técnico</p>
                </div>
                <label style="display:flex; align-items:center; gap: 8px; font-size: 0.85rem; color: var(--text-muted); cursor:pointer;">
                    <input type="checkbox" id="toggle-inactivas" ${showInactivas ? 'checked' : ''} onchange="showRuleSub('general')" style="width:16px; height:16px; accent-color:var(--primary);">
                    Mostrar inactivas
                </label>
            </div>
            <div class="main-card">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Regla</th>
                            <th>Descripción</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>`;

        for (const [key, val, activa] of entries) {
            let description = '';
            let jsonVal = val;
            // Si viene del catalogo completo, val es el objeto entero
            if (showInactivas && lastCatalogResponse) {
                description = val.descripcion || '';
                jsonVal = lastRulesResponse.reglas_generales[key] || null;
            }
            const rowStyle = activa ? '' : 'opacity: 0.5;';
            const badge = activa
                ? '<span class="rule-type-badge" style="background:#dcfce7; color:#16a34a;">Activa</span>'
                : '<span class="rule-type-badge" style="background:#f1f5f9; color:#94a3b8;">Inactiva</span>';
            const clickable = jsonVal !== null ? `class="clickable-row" onclick="showRuleDetail('${key}', 'general')"` : '';
            html += `
                <tr ${clickable} style="${rowStyle}">
                    <td style="font-weight: 600; color: var(--primary);">${key}</td>
                    <td style="font-size: 0.85rem; color: var(--text-muted);">${description}</td>
                    <td>${badge}</td>
                </tr>
            `;
        }
        html += `</tbody></table></div>`;

    } else if (type === 'personal') {
        const entries = Object.entries(lastRulesResponse.reglas_personal);
        if (entries.length === 0) {
            html = '<div class="empty-state">No hay reglas específicas configuradas por persona</div>';
        } else {
            html = `
                <div style="padding: 0 0 16px 0;">
                    <h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 4px;">Ajustes por Personal</h3>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">Haz clic en una fila para ver el detalle técnico</p>
                </div>
                <div class="main-card">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Persona</th>
                                <th>Vista previa</th>
                            </tr>
                        </thead>
                        <tbody>`;

            for (const [nombre, reglas] of entries) {
                const preview = JSON.stringify(reglas).substring(0, 80) + (JSON.stringify(reglas).length > 80 ? '...' : '');
                html += `
                    <tr class="clickable-row" onclick="showRuleDetail('${nombre}', 'personal')">
                        <td style="font-weight: 600; color: var(--primary);">${nombre}</td>
                        <td style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted);">${preview}</td>
                    </tr>
                `;
            }
            html += `</tbody></table></div>`;
        }

    } else if (type === 'turnos') {
        const DAY_LABELS = ['L', 'M', 'X', 'J', 'V', 'S', 'D'];
        html = `<h3 class="mb-16">Definición de Turnos</h3>`;
        html += `<div class="stats-grid" style="grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));">`;
        lastRulesResponse.turnos.forEach(t => {
            const activeDays = new Set((t.dias_semana || '').split(',').map(d => parseInt(d.trim())));
            const dayDots = DAY_LABELS.map((label, idx) => {
                const isActive = activeDays.has(idx);
                const style = isActive
                    ? 'background:var(--primary); color:#fff; font-weight:700;'
                    : 'background:#e2e8f0; color:#94a3b8; font-weight:500;';
                return `<span style="${style} width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:0.72rem;">${label}</span>`;
            }).join('');

            html += `
                <div class="rule-card" style="display:flex; flex-direction:column; gap:12px;">
                    <div class="rule-card-header" style="margin-bottom:0;">
                        <span class="rule-name">${t.nombre}</span>
                        <span class="rule-type-badge">${t.horas} HS</span>
                    </div>
                    <div style="font-size:0.82rem; color:var(--text-muted);">
                        Inicio: <strong>${t.hora_inicio || '--'}</strong>
                    </div>
                    <div style="display:flex; gap:5px; flex-wrap:wrap; padding-top:6px; border-top:1px solid var(--border);">
                        ${dayDots}
                    </div>
                </div>
            `;
        });
        html += `</div>`;

    } else if (type === 'demanda') {
        html = `<h3 class="mb-16">Configuración de Demanda</h3>`;
        html += `
            <div class="main-card">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Puesto / Rol</th>
                            <th>Franja Horaria</th>
                            <th>Min</th>
                            <th>Max</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        lastRulesResponse.puestos.forEach(p => {
            const franja = p.hora_inicio && p.hora_fin ? `${p.hora_inicio} – ${p.hora_fin}` : '–';
            html += `
                <tr>
                    <td style="font-weight: 600;">${p.puesto}</td>
                    <td style="font-size: 0.85rem; color: var(--text-muted); font-family: monospace;">${franja}</td>
                    <td><span style="font-weight:700; color:#10b981;">${p.cantidad_min ?? '–'}</span></td>
                    <td><span style="font-weight:700; color:var(--primary);">${p.cantidad_max ?? '–'}</span></td>
                </tr>
            `;
        });
        
        if (lastRulesResponse.puestos.length === 0) {
            html += '<tr><td colspan="4" class="empty-state">No hay puestos configurados</td></tr>';
        }
        
        html += `</tbody></table></div>`;
    }

    view.innerHTML = html;
}

function showRuleDetail(key, source) {
    if (!lastRulesResponse) return;

    let val;
    if (source === 'general') {
        val = lastRulesResponse.reglas_generales[key];
    } else if (source === 'personal') {
        val = lastRulesResponse.reglas_personal[key];
    }

    if (val === undefined) return;

    document.getElementById('rule-detail-title').textContent = key;
    document.getElementById('rule-detail-json').textContent = JSON.stringify(val, null, 2);
    document.getElementById('modal-rule-detail').classList.add('active');
}

// Modals
function openGenerateModal() {
    if (!currentServiceId) {
        alert("Por favor selecciona un servicio primero");
        return;
    }
    document.getElementById('modal-generate').classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

async function startGeneration() {
    const start = document.getElementById('gen-start').value;
    const end = document.getElementById('gen-end').value;
    
    if (!start || !end) {
        alert("Selecciona fechas válidas");
        return;
    }
    
    const btn = document.querySelector('#modal-generate .btn-primary');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Procesando...";
    
    try {
        const response = await fetch('/api/generar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                servicio_id: parseInt(currentServiceId),
                fecha_inicio: start,
                fecha_fin: end,
                notas: "Generado desde el Dashboard Web"
            })
        });
        
        const res = await response.json();
        
        if (response.ok) {
            alert("¡Cronograma generado con éxito!");
            closeModal('modal-generate');
            loadCronogramasHistorial(); // Refresh list
        } else {
            alert("Error: " + (res.detail || "No se pudo generar el cronograma"));
        }
    } catch (err) {
        console.error("Error en generación:", err);
        alert("Error de conexión con el servidor");
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}
