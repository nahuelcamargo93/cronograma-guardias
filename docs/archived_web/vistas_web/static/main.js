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
    if (sectionId === 'calendar') loadCalendarData();
    if (sectionId === 'staff') loadStaffData();
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
    
    if (sectionId !== 'calendar' || !window.isViewingSpecificCronograma) {
        refreshActiveSection(sectionId);
    }
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
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No hay cronogramas generados para este servicio</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        data.forEach(c => {
            const tr = document.createElement('tr');
            
            const statusBadge = c.estado === 'aprobado' 
                ? '<span class="badge badge-success">Aprobado</span>' 
                : '<span class="badge badge-warning">Borrador</span>';
                
            const approveBtn = c.estado === 'borrador'
                ? `<button class="btn-primary btn-sm" onclick="approveCronograma(${c.id})" style="margin-left: 8px;">Aprobar</button>`
                : '';
                
            tr.innerHTML = `
                <td>#${c.id}</td>
                <td>${c.fecha_inicio} a ${c.fecha_fin}</td>
                <td>${statusBadge}</td>
                <td>${new Date(c.creado_en).toLocaleString()}</td>
                <td>${c.notas || '-'}</td>
                <td>
                    <button class="btn-secondary btn-sm" onclick="viewCronograma(${c.id})">Ver Detalle</button>
                    ${approveBtn}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error al cargar historial:", err);
    }
}

async function approveCronograma(id) {
    if (!confirm(`¿Estás seguro de que querés aprobar el Cronograma #${id}? Esto lo marcará como el cronograma activo oficial y los demás quedarán como borradores.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/aprobar/${id}`, { method: 'POST' });
        const result = await res.json();
        if (res.ok) {
            alert(`¡Cronograma #${id} aprobado con éxito!`);
            await loadCronogramasHistorial();
        } else {
            alert("Error al aprobar: " + (result.detail || "Error desconocido"));
        }
    } catch(e) {
        console.error("Error al aprobar:", e);
        alert("Error de conexión al aprobar.");
    }
}

async function viewCronograma(id) {
    window.isViewingSpecificCronograma = true;
    showSection('calendar');
    await loadCalendarData(id);
    window.isViewingSpecificCronograma = false;
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

async function loadStaffData() {
    if (!currentServiceId) {
        document.getElementById('staff-list').innerHTML = '<tr><td colspan="7" class="empty-state">Selecciona un servicio para comenzar</td></tr>';
        return;
    }
    
    const tbody = document.getElementById('staff-list');
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Cargando personal...</td></tr>';
    
    try {
        const response = await fetch(`/api/personal/${currentServiceId}`);
        const staff = await response.json();
        
        if (staff.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No hay personal registrado en este servicio</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        staff.forEach(p => {
            const tr = document.createElement('tr');
            
            const parentStatus = [];
            if (p.es_madre) parentStatus.push("Madre");
            if (p.es_padre) parentStatus.push("Padre");
            const parentLabel = parentStatus.join(" / ") || "-";
            
            tr.innerHTML = `
                <td style="font-weight:600; color:var(--primary);">${p.nombre}</td>
                <td>${p.categoria || "-"}</td>
                <td><span class="badge badge-secondary" style="font-size:0.75rem; padding: 2px 8px; background: #f1f5f9; color: #475569; border-radius: 4px; font-weight:500;">${p.rol || "-"}</span></td>
                <td>${p.regimen_trabajo || "-"}</td>
                <td>${p.fecha_cumpleanos || "-"}</td>
                <td>${parentLabel}</td>
                <td>${p.horas_mensuales_reglamentarias ? p.horas_mensuales_reglamentarias + ' hs' : "-"}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error al cargar personal:", err);
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state" style="color:var(--danger);">Error al cargar personal del servicio</td></tr>';
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

// ============================================================
//  CALENDAR SECTION
// ============================================================

let currentCronogramaData = null;
let currentCronogramaLics = [];
let currentCalendarView  = 'cronograma';
let currentWeekStart     = null;

const DAY_NAMES = ['L', 'M', 'X', 'J', 'V', 'S', 'D']; // 0=Mon..6=Sun

const SHIFT_COLORS = {
    'G' : 'shift-G',
    'D' : 'shift-D',
    'N' : 'shift-N',
    'T' : 'shift-T',
    'M' : 'shift-M',
    'TN': 'shift-TN',
};

function getShiftClass(turno) {
    if (!turno) return 'shift-free';
    const prefix = turno.split('_')[0];
    return SHIFT_COLORS[prefix] || 'shift-free';
}

function getShiftAbbrev(turno) {
    if (!turno) return '';
    const parts = turno.split('_');
    if (parts.length < 2) return turno;
    return parts[0] + '_' + parts.slice(1).map(p => p[0]).join('');
}

function getMondayOf(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    const day = d.getDay();
    const diff = day === 0 ? -6 : 1 - day;
    d.setDate(d.getDate() + diff);
    return d;
}

function dateToStr(d) {
    // Use local date parts — toISOString() would shift to UTC and cause off-by-one in UTC-3
    const y  = d.getFullYear();
    const m  = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${dd}`;
}

function addDays(d, n) {
    const r = new Date(d);
    r.setDate(r.getDate() + n);
    return r;
}

function formatWeekLabel(mon) {
    const sun = addDays(mon, 6);
    const opts = { day: 'numeric', month: 'short' };
    return mon.toLocaleDateString('es-AR', opts) + ' – ' + sun.toLocaleDateString('es-AR', opts);
}

let allCronogramasGlobal = [];

async function syncSidebar(orgId, serviceId) {
    if (!orgId || !serviceId) return;
    
    currentOrgId = orgId;
    currentServiceId = serviceId;
    
    const selectOrg = document.getElementById('select-org');
    if (selectOrg) {
        selectOrg.value = orgId;
    }
    
    try {
        const response = await fetch(`/api/servicios/${orgId}`);
        const services = await response.json();
        const selectSvc = document.getElementById('select-service');
        if (selectSvc) {
            selectSvc.innerHTML = '<option value="">Seleccionar...</option>';
            services.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.nombre;
                selectSvc.appendChild(opt);
            });
            selectSvc.value = serviceId;
            
            const serviceName = selectSvc.options[selectSvc.selectedIndex]?.text || '';
            document.getElementById('page-subtitle').textContent = `Servicio: ${serviceName}`;
        }
    } catch (err) {
        console.error("Error al sincronizar barra lateral:", err);
    }
}

async function loadCalendarData(forcedCronogramaId = null) {
    const sel = document.getElementById('select-cronograma');
    try {
        const res = await fetch('/api/cronogramas');
        const allList = await res.json();
        allCronogramasGlobal = allList;

        sel.innerHTML = '<option value="">Seleccionar cronograma...</option>';
        allList.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            const srvLabel = c.servicio_nombre ? ` [${c.servicio_nombre}]` : '';
            const statusLabel = c.estado === 'aprobado' ? ' (Aprobado)' : ' (Borrador)';
            opt.textContent = `#${c.id}${srvLabel} — ${c.fecha_inicio} → ${c.fecha_fin}${statusLabel}`;
            opt.dataset.servicio = c.servicio_nombre || '';
            sel.appendChild(opt);
        });

        let best = forcedCronogramaId;
        if (!best && currentServiceId) {
            // Fetch only the active approved cronograma
            const activeRes = await fetch(`/api/cronograma_activo/${currentServiceId}`);
            const activeC = await activeRes.json();
            if (activeC) {
                best = activeC.id;
            }
        }

        if (best) {
            sel.value = best;
            await onCronogramaChange();
        } else {
            document.getElementById('calendar-content-view').innerHTML = `
                <div class="empty-state">
                    <h3>No hay ningún cronograma aprobado para este servicio</h3>
                    <p class="text-muted mt-8">Podés generar un nuevo borrador haciendo click en "Generar Nuevo" abajo en la barra lateral, o aprobar un borrador existente desde la "Vista General".</p>
                </div>
            `;
        }
    } catch(e) { console.error('Error cargando cronogramas:', e); }
}

async function onCronogramaChange() {
    const id = document.getElementById('select-cronograma').value;
    if (!id) return;
    
    // Auto-sync sidebar if needed
    const cronInfo = allCronogramasGlobal.find(c => String(c.id) === String(id));
    if (cronInfo && cronInfo.servicio_id && cronInfo.organizacion_id) {
        if (String(currentServiceId) !== String(cronInfo.servicio_id)) {
            await syncSidebar(cronInfo.organizacion_id, cronInfo.servicio_id);
        }
    }

    const view = document.getElementById('calendar-content-view');
    view.innerHTML = '<div class="empty-state">Cargando...</div>';
    try {
        const cronRes = await fetch(`/api/cronograma/${id}`);
        currentCronogramaData = await cronRes.json();

        // Get servicio_id from the first guardia in the cronograma
        const srvId = currentCronogramaData.guardias.length > 0
            ? currentCronogramaData.guardias[0].servicio_id
            : null;

        currentCronogramaLics = [];
        if (srvId) {
            const fi = currentCronogramaData.metadata.fecha_inicio;
            const ff = currentCronogramaData.metadata.fecha_fin;
            const licsRes = await fetch(`/api/licencias/${srvId}?desde=${fi}&hasta=${ff}`);
            currentCronogramaLics = await licsRes.json();
        }

        currentWeekStart = getMondayOf(currentCronogramaData.metadata.fecha_inicio);
        renderCurrentCalendarView();
    } catch(e) {
        view.innerHTML = '<div class="alert danger">Error al cargar cronograma</div>';
        console.error(e);
    }
}

function showCalendarView(type) {
    currentCalendarView = type;
    document.querySelectorAll('.cal-tab').forEach(t => {
        t.classList.toggle('active', t.getAttribute('data-view') === type);
    });
    renderCurrentCalendarView();
}

function prevWeek() {
    if (!currentCronogramaData) return;
    const candidate = addDays(currentWeekStart, -7);
    const fi = getMondayOf(currentCronogramaData.metadata.fecha_inicio);
    if (candidate >= fi) { currentWeekStart = candidate; renderCurrentCalendarView(); }
}

function nextWeek() {
    if (!currentCronogramaData) return;
    const candidate = addDays(currentWeekStart, 7);
    const ff = new Date(currentCronogramaData.metadata.fecha_fin + 'T00:00:00');
    if (candidate <= ff) { currentWeekStart = candidate; renderCurrentCalendarView(); }
}

function goToDate(val) {
    if (!val || !currentCronogramaData) return;
    const mon = getMondayOf(val);
    const fi  = getMondayOf(currentCronogramaData.metadata.fecha_inicio);
    const ff  = new Date(currentCronogramaData.metadata.fecha_fin + 'T00:00:00');
    if (mon >= fi && mon <= ff) { currentWeekStart = mon; renderCurrentCalendarView(); }
}

function renderCurrentCalendarView() {
    if (!currentCronogramaData || !currentWeekStart) return;

    // Build the 7 dates of this week that overlap with the cronograma
    const fi = currentCronogramaData.metadata.fecha_inicio;
    const ff = currentCronogramaData.metadata.fecha_fin;
    const weekDates = [];
    for (let i = 0; i < 7; i++) {
        const d = addDays(currentWeekStart, i);
        const ds = dateToStr(d);
        if (ds >= fi && ds <= ff) weekDates.push(ds);
    }

    // Update nav UI
    document.getElementById('week-label').textContent = formatWeekLabel(currentWeekStart);
    document.getElementById('week-picker').value = dateToStr(currentWeekStart);

    if (weekDates.length === 0) {
        document.getElementById('calendar-content-view').innerHTML =
            '<div class="empty-state">Esta semana está fuera del rango del cronograma</div>';
        return;
    }

    if (currentCalendarView === 'cronograma') {
        renderVistaCronograma(weekDates);
    } else {
        renderVistaPersonal(weekDates);
    }
}

function renderVistaCronograma(weekDates) {
    const { guardias, puestos } = currentCronogramaData;
    const lics = currentCronogramaLics;

    // Group guardias by puesto → date → [names]
    const byPuesto = {};
    puestos.forEach(p => { byPuesto[p.nombre] = {}; });
    guardias.forEach(g => {
        if (!weekDates.includes(g.fecha)) return;
        const p = g.puesto || g.rol;
        if (!byPuesto[p]) byPuesto[p] = {};
        if (!byPuesto[p][g.fecha]) byPuesto[p][g.fecha] = [];
        byPuesto[p][g.fecha].push(g);
    });

    // Max slots per puesto
    const maxSlots = {};
    Object.entries(byPuesto).forEach(([p, days]) => {
        maxSlots[p] = Math.max(1, ...Object.values(days).map(arr => arr.length));
    });

    let html = '<div class="cal-grid-wrapper"><table class="cal-grid-table"><thead>';

    // Row 1: day names
    html += '<tr><th class="row-label" rowspan="2">PUESTO</th>';
    weekDates.forEach(d => {
        const dt = new Date(d + 'T00:00:00');
        const isSun = dt.getDay() === 0;
        const dayName = DAY_NAMES[(dt.getDay() + 6) % 7];
        html += `<th class="col-header-day${isSun ? ' col-sep-right' : ''}">${dayName}<br><small style="font-weight:400; font-size:0.75rem;">${dt.getDate()}/${dt.getMonth()+1}</small></th>`;
    });
    html += '</tr></thead><tbody>';

    // Rows: one puesto = possibly multiple slot rows
    Object.entries(byPuesto).forEach(([puesto, days]) => {
        const slots = maxSlots[puesto];
        for (let slot = 0; slot < slots; slot++) {
            html += '<tr>';
            if (slot === 0) {
                html += `<td class="row-label" rowspan="${slots}">${puesto}</td>`;
            }
            weekDates.forEach(d => {
                const dt = new Date(d + 'T00:00:00');
                const isSun = dt.getDay() === 0;
                const arr = (days[d] || []).sort((a,b) => a.nombre.localeCompare(b.nombre));
                const g = arr[slot];
                const sepCls = isSun ? ' col-sep-right' : '';
                if (g) {
                    const abbrev = getShiftAbbrev(g.turno);
                    const cls = getShiftClass(g.turno);
                    html += `<td class="shift-cell ${cls}${sepCls}" title="${g.turno}">${g.nombre}<br><small style="opacity:.7">${abbrev}</small></td>`;
                } else {
                    // Check license
                    html += `<td class="shift-cell shift-free${sepCls}"></td>`;
                }
            });
            html += '</tr>';
        }
    });

    // License rows
    const licTypes = ['LPP', 'LAR', 'LM', 'CM'];
    licTypes.forEach(tipo => {
        const relevant = lics.filter(l => l.tipo.toUpperCase() === tipo);
        if (relevant.length === 0) return;
        html += `<tr><td class="row-label" style="background:#E9E9E9; color:#595959;">${tipo}</td>`;
        weekDates.forEach(d => {
            const dt = new Date(d + 'T00:00:00');
            const isSun = dt.getDay() === 0;
            const names = relevant.filter(l => l.fecha_inicio <= d && l.fecha_fin >= d).map(l => l.nombre);
            const sepCls = isSun ? ' col-sep-right' : '';
            html += `<td class="shift-cell shift-lic${sepCls}">${names.join('<br>')}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    document.getElementById('calendar-content-view').innerHTML = html;
}

function renderVistaPersonal(weekDates) {
    const { guardias } = currentCronogramaData;
    const lics = currentCronogramaLics;

    // All unique persons
    const persons = [...new Set(guardias.map(g => g.nombre))].sort();

    // Guardia lookup: person → date → guardia
    const byPerson = {};
    persons.forEach(n => { byPerson[n] = {}; });
    guardias.forEach(g => {
        if (weekDates.includes(g.fecha)) byPerson[g.nombre][g.fecha] = g;
    });

    let html = '<div class="cal-grid-wrapper"><table class="cal-grid-table"><thead><tr>';
    html += '<th class="row-label">PERSONAL</th>';
    weekDates.forEach(d => {
        const dt = new Date(d + 'T00:00:00');
        const isSun = dt.getDay() === 0;
        const dayName = DAY_NAMES[(dt.getDay() + 6) % 7];
        html += `<th class="col-header-day${isSun ? ' col-sep-right' : ''}">${dayName}<br><small style="font-weight:400; font-size:0.75rem;">${dt.getDate()}/${dt.getMonth()+1}</small></th>`;
    });
    html += '<th class="col-total">Hs Ef.</th><th class="col-total">FS</th>';
    html += '</tr></thead><tbody>';

    persons.forEach(nombre => {
        let horasEf = 0;
        let fs = 0;
        html += `<tr><td class="row-label personal-name-cell">${nombre}</td>`;
        weekDates.forEach(d => {
            const dt = new Date(d + 'T00:00:00');
            const isSun = dt.getDay() === 0;
            const isFinde = dt.getDay() === 0 || dt.getDay() === 6;
            const sepCls = isSun ? ' col-sep-right' : '';
            const g = byPerson[nombre][d];
            if (g) {
                const abbrev = getShiftAbbrev(g.turno);
                const cls = getShiftClass(g.turno);
                horasEf += g.horas || 0;
                if (isFinde) fs++;
                html += `<td class="shift-cell ${cls}${sepCls}" title="${g.turno}">${abbrev}</td>`;
            } else {
                // Check license
                const lic = lics.find(l => l.nombre === nombre && l.fecha_inicio <= d && l.fecha_fin >= d);
                if (lic) {
                    html += `<td class="shift-cell shift-lic${sepCls}">${lic.tipo}</td>`;
                } else {
                    html += `<td class="shift-cell shift-free${sepCls}">F</td>`;
                }
            }
        });
        html += `<td class="col-total">${horasEf}</td><td class="col-total">${fs}</td></tr>`;
    });

    html += '</tbody></table></div>';
    document.getElementById('calendar-content-view').innerHTML = html;
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('collapsed');
    
    const icon = document.getElementById('toggle-icon');
    if (sidebar.classList.contains('collapsed')) {
        icon.setAttribute('data-feather', 'chevron-right');
    } else {
        icon.setAttribute('data-feather', 'chevron-left');
    }
    feather.replace();
}

