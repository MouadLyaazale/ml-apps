/**
 * Atelier Schiele Maroc – Kiosque de suivi de temps v3
 * Badge-only login · Start/Pause · 1 opération à la fois · sans onglet pointage
 */
"use strict";

// ═══════════════════════════════════════════════════════════════
// Utilitaires
// ═══════════════════════════════════════════════════════════════

async function rpc(url, params = {}) {
    const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'call', id: Date.now(), params }),
    });
    const data = await resp.json();
    if (data.error) throw new Error(data.error.data?.message || data.error.message);
    return data.result;
}

function el(id)  { return document.getElementById(id); }

function fmt(minutes) {
    if (!minutes && minutes !== 0) return '00:00:00';
    const absMin = Math.abs(minutes);
    const h = Math.floor(absMin / 60);
    const m = Math.floor(absMin % 60);
    const s = Math.floor((absMin * 60) % 60);
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

function showToast(msg, type = 'success') {
    document.querySelectorAll('.atelier-toast').forEach(t => t.remove());
    const div = document.createElement('div');
    div.className = `atelier-toast ${type}`;
    div.textContent = msg;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 3500);
}

function showBlockingError(msg) {
    // Modal bloquant pour les erreurs métier importantes (ex: opération concurrente)
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.65);z-index:9999;display:flex;align-items:center;justify-content:center;';
    overlay.innerHTML = `
    <div style="background:#1e1e2e;border:2px solid #ef4444;border-radius:16px;padding:32px 40px;max-width:420px;width:90%;text-align:center;">
        <div style="font-size:2.5rem;margin-bottom:12px">🚫</div>
        <div style="font-size:1.1rem;color:#ef4444;font-weight:700;margin-bottom:12px">Démarrage bloqué</div>
        <div style="color:#e0e0e0;margin-bottom:24px;line-height:1.5">${msg}</div>
        <button style="background:#ef4444;color:#fff;border:none;border-radius:8px;padding:12px 28px;font-size:1rem;cursor:pointer;font-weight:600;" id="blocking-ok-btn">Compris</button>
    </div>`;
    document.body.appendChild(overlay);
    overlay.querySelector('#blocking-ok-btn').addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
}

function kpiBar(done, expected, label = '') {
    const pct = expected > 0 ? Math.min(Math.round(done / expected * 100), 200) : 0;
    const cls = pct < 80 ? 'kpi-ok' : pct <= 110 ? 'kpi-warn' : 'kpi-over';
    return `<div class="atelier-kpi-wrap" title="${label}">
        <div class="atelier-kpi-bar">
            <div class="atelier-kpi-fill ${cls}" style="width:${Math.min(pct, 100)}%"></div>
        </div>
        <span class="atelier-kpi-pct ${cls}">${pct}%</span>
    </div>`;
}

function burndownBadge(pct) {
    const cls = pct < 50 ? '' : pct < 90 ? 'bd-warn' : 'bd-over';
    return `<span class="atelier-burndown ${cls}">${pct}% consommé</span>`;
}

function priorityBadge(p) {
    const map = { '0': '', '1': '<span class="prio-urgent">⚠ URGENT</span>', '2': '<span class="prio-critique">🔴 CRITIQUE</span>' };
    return map[p] || '';
}

function otherEmpsHtml(others) {
    if (!others || !others.length) return '';
    const avatars = others.map(e =>
        `<img src="${e.image}" title="${e.name} – actif depuis ${fmt((Date.now() - new Date(e.start_time + (e.start_time.endsWith('Z')?'':'Z')).getTime()) / 60000)}"
              class="atelier-peer-avatar" onerror="this.style.display='none'"/>`
    ).join('');
    return `<div class="atelier-peers">👥 ${avatars}</div>`;
}

// ═══════════════════════════════════════════════════════════════
// État global
// ═══════════════════════════════════════════════════════════════

const App = {
    employee:        null,
    orders:          [],
    timers:          {},
    expandedMO:      new Set(),
    refreshInterval: null,
    autoLogoutMs:    10 * 60 * 1000,
    lastActivity:    Date.now(),
    logoutTimer:     null,
    countdownTimer:  null,
};

// ═══════════════════════════════════════════════════════════════
// Auto-logout (inactivité)
// ═══════════════════════════════════════════════════════════════

function initAutoLogout() {
    const resetActivity = () => { App.lastActivity = Date.now(); };
    ['click','keydown','touchstart','mousemove'].forEach(ev =>
        document.addEventListener(ev, resetActivity, { passive: true })
    );

    App.logoutTimer = setInterval(() => {
        if (!App.employee) return;
        const remaining = App.autoLogoutMs - (Date.now() - App.lastActivity);
        const countdownEl = el('logout-countdown');

        if (remaining <= 0) {
            clearInterval(App.logoutTimer);
            showToast('Déconnexion automatique pour inactivité', 'info');
            logout();
        } else if (remaining <= 60000 && countdownEl) {
            countdownEl.textContent = '⏱ ' + Math.ceil(remaining / 1000) + 's';
            countdownEl.style.display = '';
        } else if (countdownEl) {
            countdownEl.style.display = 'none';
        }
    }, 1000);
}

function resetActivityFromUI() {
    App.lastActivity = Date.now();
}

// ═══════════════════════════════════════════════════════════════
// Écran de connexion – Badge uniquement
// ═══════════════════════════════════════════════════════════════

function renderLoginScreen() {
    el('atelier-root').innerHTML = `
    <div class="atelier-login-screen">
        <div class="atelier-login-title">⚙️ Atelier Schiele Maroc</div>
        <div class="atelier-login-subtitle">Scannez votre badge ou saisissez son numéro</div>
        <div class="atelier-login-card">
            <div style="text-align:center;font-size:3rem;margin-bottom:8px">🪪</div>
            <input class="atelier-badge-input" id="badge-input"
                   type="text" placeholder="Numéro de badge…" autocomplete="off"
                   autofocus inputmode="text"/>
            <button class="atelier-submit-btn" id="badge-ok">Se connecter</button>
            <div class="atelier-login-error" id="login-error"></div>
        </div>
    </div>`;

    // Focus immédiat pour capter le scanner HID
    const badgeInput = el('badge-input');
    badgeInput.focus();

    async function doLogin(badge) {
        badge = badge.trim();
        if (!badge) return;
        badgeInput.disabled = true;
        el('badge-ok').disabled = true;
        el('login-error').textContent = '';
        try {
            const r = await rpc('/atelier/auth', { badge });
            if (r.success) {
                App.employee = r.employee;
                App.autoLogoutMs = (r.employee.auto_logout_minutes || 10) * 60 * 1000;
                renderMainApp();
            } else {
                el('login-error').textContent = r.error || 'Badge invalide';
                badgeInput.value = '';
                badgeInput.disabled = false;
                el('badge-ok').disabled = false;
                badgeInput.focus();
            }
        } catch (e) {
            el('login-error').textContent = 'Erreur réseau';
            badgeInput.disabled = false;
            el('badge-ok').disabled = false;
            badgeInput.focus();
        }
    }

    el('badge-ok').addEventListener('click', () => doLogin(badgeInput.value));
    badgeInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') doLogin(badgeInput.value);
    });

    // Re-focus sur clic partout sur l'écran de login (capture scanner peu importe le focus)
    el('atelier-root').addEventListener('click', e => {
        if (e.target !== el('badge-ok')) badgeInput.focus();
    });
}

// ═══════════════════════════════════════════════════════════════
// Application principale
// ═══════════════════════════════════════════════════════════════

function renderMainApp() {
    const emp = App.employee;
    el('atelier-root').innerHTML = `
    <div class="atelier-header">
        <div class="atelier-header-logo">⚙️ Atelier Schiele Maroc</div>
        <div class="atelier-header-employee">
            <img src="${emp.image}" onerror="this.src='/web/static/img/placeholder.png'" alt=""/>
            <div>
                <div style="font-weight:700">${emp.name}</div>
                <div style="font-size:0.8rem;color:var(--atelier-muted)">${emp.job_title}${emp.shift ? ' · ' + emp.shift : ''}</div>
            </div>
        </div>
        <div class="atelier-header-clock" id="header-clock"></div>
        <span id="logout-countdown" class="countdown-warning" style="display:none"></span>
        <button class="atelier-logout-btn" id="logout-btn">⏏ Déconnexion</button>
    </div>
    ${emp.is_supervisor ? `<div class="atelier-tabbar"><button class="atelier-tabbar-btn supervisor-tab" id="tabbar-sv">👁 Superviseur</button></div>` : ''}
    <div class="atelier-main" id="atelier-main-content">
        <div class="atelier-loading-screen" style="height:50vh"><div class="atelier-spinner"></div></div>
    </div>`;

    // Clock
    const clockTick = () => {
        const now = new Date();
        const clk = el('header-clock');
        if (clk) clk.innerHTML =
            `<div>${now.toLocaleTimeString('fr-MA',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}</div>
             <div style="font-size:0.75rem">${now.toLocaleDateString('fr-MA',{weekday:'long',day:'numeric',month:'long'})}</div>`;
    };
    clockTick();
    setInterval(clockTick, 1000);

    el('logout-btn').addEventListener('click', logout);
    if (emp.is_supervisor) {
        el('tabbar-sv').addEventListener('click', () => window.open('/atelier/supervisor', '_blank'));
    }

    initAutoLogout();
    loadAndRenderOrders();
    App.refreshInterval = setInterval(loadAndRenderOrders, 30000);
}

function logout() {
    Object.values(App.timers).forEach(t => clearInterval(t.interval));
    App.timers = {};
    clearInterval(App.refreshInterval);
    clearInterval(App.logoutTimer);
    App.employee = null; App.orders = []; App.expandedMO.clear();
    renderLoginScreen();
}

// ═══════════════════════════════════════════════════════════════
// Onglet OFs
// ═══════════════════════════════════════════════════════════════

async function loadAndRenderOrders() {
    try {
        const r = await rpc('/atelier/orders', { employee_id: App.employee.id });
        if (!r.success) { showToast(r.error || 'Erreur chargement OF', 'error'); return; }
        App.orders = r.orders || [];
        renderOrders();
        syncRunningTimers();
    } catch (e) { showToast('Erreur réseau', 'error'); }
}

function renderOrders() {
    const c = el('atelier-main-content');
    if (!c) return;

    if (!App.orders.length) {
        c.innerHTML = `
        <div class="atelier-section-title">🔧 Ordres de fabrication</div>
        <div class="atelier-no-orders">
            <div style="font-size:3rem;margin-bottom:16px">📭</div>
            Aucun OF lancé ne vous est assigné pour le moment.
            <br><small style="color:var(--atelier-muted)">Le superviseur doit lancer un OF et vous y assigner.</small>
        </div>`;
        return;
    }

    let html = `<div class="atelier-section-title">🔧 Mes OFs (${App.orders.length})</div>`;
    for (const mo of App.orders) {
        const isOpen = App.expandedMO.has(mo.id);
        const running = mo.workorders.filter(w => w.is_running).length;
        const prioCls = mo.priority === '2' ? 'mo-critique' : mo.priority === '1' ? 'mo-urgent' : '';
        html += `
        <div class="atelier-mo-card ${prioCls}">
            <div class="atelier-mo-header ${isOpen ? 'expanded' : ''}" data-toggle-mo="${mo.id}">
                <div style="flex:1">
                    <div class="atelier-mo-name">
                        ${priorityBadge(mo.priority)} ${mo.name}
                    </div>
                    <div class="atelier-mo-product">
                        📦 ${mo.product} &nbsp;•&nbsp; ${mo.workorders.length} op.
                        ${running ? `<span style="color:var(--atelier-success)"> &nbsp;▶ ${running} actif</span>` : ''}
                    </div>
                    ${burndownBadge(mo.burndown)}
                </div>
                <div style="display:flex;align-items:center;gap:12px">
                    <div class="atelier-mo-qty">${mo.product_qty} ${mo.product_uom}</div>
                    <div class="atelier-mo-chevron">▾</div>
                </div>
            </div>
            ${isOpen ? renderWorkorders(mo) : ''}
        </div>`;
    }
    c.innerHTML = html;

    c.querySelectorAll('[data-toggle-mo]').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = parseInt(btn.dataset.toggleMo);
            if (App.expandedMO.has(id)) App.expandedMO.delete(id); else App.expandedMO.add(id);
            renderOrders(); syncRunningTimers();
        });
    });
    c.querySelectorAll('[data-wo-start]').forEach(b => b.addEventListener('click', () => handleStart(+b.dataset.woStart)));
    c.querySelectorAll('[data-wo-pause]').forEach(b => b.addEventListener('click', () => handlePause(+b.dataset.woPause)));
    c.querySelectorAll('[data-wo-qc]').forEach(b    => b.addEventListener('click', () => openAutocontroleModal(+b.dataset.woQc)));
    syncRunningTimers();
}

function renderWorkorders(mo) {
    if (!mo.workorders.length)
        return `<div class="atelier-wo-list"><div style="color:var(--atelier-muted);text-align:center;padding:16px">Aucune opération</div></div>`;

    let html = `<div class="atelier-wo-list">`;
    for (const wo of mo.workorders) {
        html += `
        <div class="atelier-wo-item ${wo.is_running ? 'running' : ''}" id="wo-item-${wo.id}">
            <div class="atelier-wo-info">
                <div class="atelier-wo-name">${wo.name}</div>
                <div class="atelier-wo-workcenter">🏭 ${wo.workcenter}</div>
                <div style="font-size:0.8rem;color:var(--atelier-muted);margin-top:2px">
                    Prévu : ${fmt(wo.duration_expected)} &nbsp;|&nbsp; Total équipe : ${fmt(wo.duration)}
                </div>
                ${kpiBar(wo.my_duration, wo.duration_expected, 'Mon temps vs prévu')}
                ${otherEmpsHtml(wo.other_employees)}
            </div>
            <div class="atelier-wo-timer ${wo.is_running ? '' : 'paused'}" id="timer-display-${wo.id}">
                ${fmt(wo.my_duration)}
            </div>
            <div class="atelier-timer-actions">
                ${!wo.is_running
                    ? `<button class="atelier-btn atelier-btn-start" data-wo-start="${wo.id}">▶ Start</button>`
                    : `<button class="atelier-btn atelier-btn-pause" data-wo-pause="${wo.id}">⏸ Pause</button>`}
                ${wo.check_count > 0
                    ? `<button class="atelier-btn atelier-btn-qc" data-wo-qc="${wo.id}">📋 Autocontrôle</button>`
                    : ''}
            </div>
        </div>`;
    }
    return html + `</div>`;
}

// ═══════════════════════════════════════════════════════════════
// Chrono local
// ═══════════════════════════════════════════════════════════════

function syncRunningTimers() {
    for (const mo of App.orders) {
        for (const wo of mo.workorders) {
            if (wo.is_running && wo.start_time) {
                if (!App.timers[wo.id]) {
                    const acc   = wo.my_duration || 0;
                    const start = new Date(wo.start_time + (wo.start_time.endsWith('Z') ? '' : 'Z'));
                    App.timers[wo.id] = {
                        acc, start,
                        interval: setInterval(() => {
                            const elapsed = (Date.now() - start.getTime()) / 60000;
                            const d = el(`timer-display-${wo.id}`);
                            if (d) d.textContent = fmt(acc + elapsed);
                        }, 1000),
                    };
                }
            } else {
                if (App.timers[wo.id]) { clearInterval(App.timers[wo.id].interval); delete App.timers[wo.id]; }
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// Actions Start / Pause / Stop
// ═══════════════════════════════════════════════════════════════

async function handleStart(woId) {
    setBtnDisabled(woId, true);
    const r = await safe(rpc('/atelier/workorder/start', { workorder_id: woId, employee_id: App.employee.id }));
    if (r?.success) { showToast('Chrono démarré ▶'); await loadAndRenderOrders(); }
    else if (r?.blocking) {
        // Erreur métier (ex : opération concurrente) — affichage proéminent
        showBlockingError(r.error || 'Opération bloquée');
        setBtnDisabled(woId, false);
    }
    else { showToast((r?.error) || 'Erreur démarrage', 'error'); setBtnDisabled(woId, false); }
}

async function handlePause(woId) {
    setBtnDisabled(woId, true);
    const r = await safe(rpc('/atelier/workorder/pause', { workorder_id: woId, employee_id: App.employee.id }));
    if (r?.success) {
        showToast('Mis en pause ⏸', 'info');
        if (App.timers[woId]) { clearInterval(App.timers[woId].interval); delete App.timers[woId]; }
        await loadAndRenderOrders();
    } else { showToast((r?.error) || 'Erreur pause', 'error'); setBtnDisabled(woId, false); }
}

async function safe(promise) {
    try { return await promise; } catch (e) { showToast('Erreur réseau', 'error'); return null; }
}

function setBtnDisabled(woId, disabled) {
    const item = el(`wo-item-${woId}`);
    if (item) item.querySelectorAll('button').forEach(b => b.disabled = disabled);
}

// ═══════════════════════════════════════════════════════════════
// Autocontrôle – modal qualité
// ═══════════════════════════════════════════════════════════════

async function openAutocontroleModal(woId) {
    // Show loading overlay
    const overlay = document.createElement('div');
    overlay.className = 'qc-overlay';
    overlay.innerHTML = `<div class="qc-modal"><div class="qc-loading">Chargement…</div></div>`;
    document.body.appendChild(overlay);

    let checks;
    try {
        const r = await rpc('/atelier/quality/checks', {
            workorder_id: woId,
            employee_id: App.employee.id,
        });
        if (!r.success) { overlay.remove(); showToast(r.error || 'Erreur chargement', 'error'); return; }
        checks = r.checks;
    } catch (e) { overlay.remove(); showToast('Erreur réseau', 'error'); return; }

    if (!checks.length) {
        overlay.remove();
        showToast('Aucun contrôle qualité sur cette opération', 'info');
        return;
    }

    const woName = (() => {
        for (const mo of App.orders)
            for (const wo of mo.workorders)
                if (wo.id === woId) return wo.name;
        return 'Opération';
    })();

    renderQcModal(overlay, woName, checks);
}

function renderQcModal(overlay, woName, checks) {
    const total    = checks.length;
    const done     = checks.filter(c => c.quality_state !== 'none').length;
    const allDone  = done === total;

    let checksHtml = checks.map((c, idx) => {
        const stateCls = c.quality_state === 'pass' ? 'qc-pass'
                       : c.quality_state === 'fail' ? 'qc-fail' : 'qc-pending';
        const stateIcon = c.quality_state === 'pass' ? '✅'
                        : c.quality_state === 'fail' ? '❌' : '⏳';

        let inputHtml = '';
        if (c.test_type === 'measure') {
            inputHtml = `
            <div class="qc-measure-row">
                <input type="number" class="qc-measure-input" id="measure-${c.id}"
                       value="${c.measure !== null ? c.measure : ''}"
                       placeholder="Valeur…" step="any"/>
                <span class="qc-measure-unit">${c.norm_unit || ''}</span>
                ${c.tolerance_min !== null ? `<span class="qc-tol">Min: ${c.tolerance_min} / Max: ${c.tolerance_max}</span>` : ''}
            </div>`;
        } else if (c.test_type === 'instructions') {
            inputHtml = `<div class="qc-instructions-note">${c.note || ''}</div>`;
        }

        const noteHtml = c.test_type !== 'instructions' && c.note
            ? `<div class="qc-note">${c.note}</div>` : '';

        const btnDisabled = '';
        let actionHtml = '';
        if (c.test_type !== 'instructions') {
            actionHtml = `
            <div class="qc-action-row">
                <button class="qc-btn qc-btn-pass ${c.quality_state === 'pass' ? 'active' : ''}"
                        data-qc-pass="${c.id}" ${btnDisabled}>✅ Conforme</button>
                <button class="qc-btn qc-btn-fail ${c.quality_state === 'fail' ? 'active' : ''}"
                        data-qc-fail="${c.id}" ${btnDisabled}>❌ Non conforme</button>
            </div>`;
        } else {
            actionHtml = `
            <div class="qc-action-row">
                <button class="qc-btn qc-btn-pass ${c.quality_state === 'pass' ? 'active' : ''}"
                        data-qc-pass="${c.id}">✅ Lu et compris</button>
            </div>`;
        }

        return `
        <div class="qc-check-card ${stateCls}" id="qc-card-${c.id}">
            <div class="qc-check-header">
                <span class="qc-check-num">${idx + 1}/${total}</span>
                <span class="qc-check-title">${stateIcon} ${c.title}</span>
            </div>
            ${noteHtml}
            ${inputHtml}
            ${actionHtml}
        </div>`;
    }).join('');

    overlay.querySelector('.qc-modal').innerHTML = `
    <div class="qc-modal-header">
        <div>
            <div class="qc-modal-title">📋 Autocontrôle</div>
            <div class="qc-modal-subtitle">${woName}</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
            <div class="qc-progress-badge">${done}/${total} effectués</div>
            <button class="qc-close-btn" id="qc-close">✕</button>
        </div>
    </div>
    <div class="qc-checks-list">${checksHtml}</div>
    <div class="qc-modal-footer">
        ${allDone
            ? `<div class="qc-all-done">🎉 Tous les contrôles sont complétés !</div>`
            : `<div class="qc-footer-hint">Veuillez compléter tous les contrôles.</div>`}
        <button class="qc-close-btn-bottom" id="qc-close-bottom">Fermer</button>
    </div>`;

    const closeModal = () => overlay.remove();
    overlay.querySelector('#qc-close').addEventListener('click', closeModal);
    overlay.querySelector('#qc-close-bottom').addEventListener('click', closeModal);
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });

    // Pass buttons
    overlay.querySelectorAll('[data-qc-pass]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const cid = +btn.dataset.qcPass;
            const check = checks.find(c => c.id === cid);
            if (!check) return;
            const measureInput = overlay.querySelector(`#measure-${cid}`);
            const measure = measureInput ? parseFloat(measureInput.value) : null;
            if (measureInput && isNaN(measure)) {
                showToast('Veuillez saisir une valeur de mesure', 'error'); return;
            }
            btn.disabled = true;
            const r = await safe(rpc('/atelier/quality/save', {
                check_id: cid, quality_state: 'pass',
                measure: measure, employee_id: App.employee.id,
            }));
            if (r?.success) {
                check.quality_state = 'pass';
                if (measure !== null) check.measure = measure;
                renderQcModal(overlay, woName, checks);
            } else {
                btn.disabled = false;
                showToast(r?.error || 'Erreur', 'error');
            }
        });
    });

    // Fail buttons
    overlay.querySelectorAll('[data-qc-fail]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const cid = +btn.dataset.qcFail;
            const check = checks.find(c => c.id === cid);
            if (!check) return;
            const measureInput = overlay.querySelector(`#measure-${cid}`);
            const measure = measureInput ? parseFloat(measureInput.value) : null;
            btn.disabled = true;
            const r = await safe(rpc('/atelier/quality/save', {
                check_id: cid, quality_state: 'fail',
                measure: measure, employee_id: App.employee.id,
            }));
            if (r?.success) {
                check.quality_state = 'fail';
                if (measure !== null) check.measure = measure;
                renderQcModal(overlay, woName, checks);
            } else {
                btn.disabled = false;
                showToast(r?.error || 'Erreur', 'error');
            }
        });
    });
}

// ═══════════════════════════════════════════════════════════════
// Démarrage
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Charger la config serveur (auto_logout etc.)
    rpc('/atelier/config').then(cfg => {
        if (cfg && cfg.auto_logout_minutes) App.autoLogoutMs = cfg.auto_logout_minutes * 60 * 1000;
    }).catch(() => {});
    renderLoginScreen();
});

