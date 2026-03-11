/**
 * Atelier Schiele Maroc – Tableau de bord Superviseur
 * POST /atelier/api/supervisor/overview  (auth=user)
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

function el(id) { return document.getElementById(id); }

function fmtMin(minutes) {
    if (!minutes && minutes !== 0) return '00:00';
    const h = Math.floor(Math.abs(minutes) / 60);
    const m = Math.floor(Math.abs(minutes) % 60);
    return `${String(h).padStart(2,'0')}h${String(m).padStart(2,'0')}`;
}

function fmtSec(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

function floatToTime(f) {
    const h = Math.floor(f);
    const m = Math.round((f - h) * 60);
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
}

function svToast(msg, type = 'info') {
    const area = el('sv-toast-area');
    if (!area) return;
    const div = document.createElement('div');
    div.className = `sv-toast ${type}`;
    div.textContent = msg;
    area.appendChild(div);
    setTimeout(() => div.remove(), 4000);
}

// ═══════════════════════════════════════════════════════════════
// État
// ═══════════════════════════════════════════════════════════════

const Sv = {
    activeBlocks: [],   // [{id, employee_name, wo_name, mo_name, workcenter, date_start_ts}]
    refreshTimer: null,
    tickTimer: null,
    currentTab: 'active',
    statsData:   null,
    statsPeriod: 'day',
};

// ═══════════════════════════════════════════════════════════════
// Horloge en direct
// ═══════════════════════════════════════════════════════════════

function startClock() {
    function tick() {
        const now = new Date();
        const clock = el('sv-clock');
        if (clock) clock.textContent = now.toLocaleTimeString('fr-MA', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    tick();
    setInterval(tick, 1000);
}

// ═══════════════════════════════════════════════════════════════
// Navigation par onglets
// ═══════════════════════════════════════════════════════════════

function switchTab(tab) {
    Sv.currentTab = tab;
    document.querySelectorAll('.sv-tab').forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tab));
    ['active', 'mos', 'employees', 'shifts', 'stats'].forEach(t => {
        const panel = el(`sv-tab-${t}`);
        if (panel) panel.classList.toggle('hidden', t !== tab);
    });
    // Charger les stats à la première ouverture de l'onglet
    if (tab === 'stats' && !Sv.statsData) loadStats();
}

// ═══════════════════════════════════════════════════════════════
// Chargement des données
// ═══════════════════════════════════════════════════════════════

async function loadOverview() {
    try {
        const data = await rpc('/atelier/api/supervisor/overview');
        Sv.activeBlocks = data.active_blocks || [];
        renderActiveBlocks(Sv.activeBlocks);
        renderMOList(data.mo_list || []);
        renderEmployeeSummary(data.employee_summary || []);
        renderShifts(data.shifts || []);
        const ref = el('sv-last-refresh');
        if (ref) ref.textContent = 'Actualisé à ' + new Date().toLocaleTimeString('fr-MA', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        startElapsedTick();
    } catch (e) {
        svToast('Erreur de chargement : ' + e.message, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
// Onglet 5 : Performance (stats périodiques)
// ═══════════════════════════════════════════════════════════════

async function loadStats() {
    const container = el('sv-stats-list');
    if (container) container.innerHTML = '<div class="sv-loading">Chargement…</div>';
    try {
        const data = await rpc('/atelier/api/supervisor/stats', { period: Sv.statsPeriod });
        if (!data.success) { svToast('Erreur stats : ' + data.error, 'error'); return; }
        Sv.statsData = data;
        renderStats(data.stats);
        renderTimeline(data.timeline);
    } catch (e) {
        svToast('Erreur réseau stats : ' + e.message, 'error');
    }
}

function renderStats(stats) {
    const container = el('sv-stats-list');
    if (!container) return;
    if (!stats || !stats.length) {
        container.innerHTML = '<div class="sv-empty">📊 Aucune donnée pour cette période.</div>';
        return;
    }
    const rows = stats.map(s => {
        const h   = Math.floor(s.total_minutes / 60);
        const m   = Math.floor(s.total_minutes % 60);
        const dur = `${String(h).padStart(2,'0')}h${String(m).padStart(2,'0')}`;
        const score = s.score !== null ? s.score : null;
        const scoreCls = score === null ? '' : score <= 80 ? 'score-low' : score <= 120 ? 'score-ok' : 'score-high';
        const scorePct = score !== null ? Math.min(score, 150) : 0;
        const scoreLabel = score !== null
            ? `<div class="sv-score-bar-wrap" title="Score productivité : ${score}%">
                <div class="sv-score-bar"><div class="sv-score-fill ${scoreCls}" style="width:${Math.min(scorePct,100)}%"></div></div>
                <span class="sv-score-label ${scoreCls}">${score}%</span>
               </div>`
            : '<span class="sv-muted" style="font-size:0.8rem">N/A</span>';
        return `
        <div class="sv-stats-card">
            <div class="sv-emp-avatar-placeholder">${escHtml((s.name||'?')[0].toUpperCase())}</div>
            <div style="flex:1">
                <div class="sv-emp-name">${escHtml(s.name)}</div>
                <div style="font-size:0.85rem;color:var(--atelier-muted);margin:2px 0">
                    ${s.mo_count} OF &nbsp;•&nbsp; ${s.wo_count} opération(s) &nbsp;•&nbsp; ${s.blocks_count} bloc(s)
                </div>
                ${scoreLabel}
            </div>
            <div class="sv-stats-time">${dur}</div>
        </div>`;
    }).join('');
    container.innerHTML = rows;
}

function renderTimeline(timeline) {
    const container = el('sv-timeline-container');
    if (!container) return;
    if (!timeline || !timeline.length) {
        container.innerHTML = '<div class="sv-empty">Aucun bloc pour cette période.</div>';
        return;
    }

    // Regrouper par employé
    const byEmp = {};
    timeline.forEach(b => {
        if (!byEmp[b.employee_id]) byEmp[b.employee_id] = { name: b.employee_name, blocks: [] };
        byEmp[b.employee_id].blocks.push(b);
    });

    // Déterminer la fenêtre horaire (min/max de la journée)
    const allStart = timeline.map(b => new Date(b.date_start + 'Z').getTime()).filter(Boolean);
    const allEnd   = timeline.map(b => new Date(b.date_end   + 'Z').getTime()).filter(Boolean);
    const winMin = allStart.length ? Math.min(...allStart) : Date.now() - 28800000;
    const winMax = allEnd.length   ? Math.max(...allEnd)   : Date.now();
    const winSpan = winMax - winMin || 1;

    const rows = Object.values(byEmp).map(emp => {
        const segs = emp.blocks.map(b => {
            const s = new Date(b.date_start + 'Z').getTime();
            const e = new Date(b.date_end   + 'Z').getTime();
            const left = ((s - winMin) / winSpan * 100).toFixed(2);
            const width = Math.max(((e - s) / winSpan * 100), 0.5).toFixed(2);
            const title = `${b.wo_name} \u2013 ${b.mo_name} (${fmtMin(b.duration)})`;
            return `<div class="sv-tl-seg${b.is_open ? ' sv-tl-open' : ''}" style="left:${left}%;width:${width}%" title="${escHtml(title)}"></div>`;
        }).join('');
        return `
        <div class="sv-tl-row">
            <div class="sv-tl-label">${escHtml(emp.name)}</div>
            <div class="sv-tl-track">${segs}</div>
        </div>`;
    }).join('');
    container.innerHTML = rows;
}

// ═══════════════════════════════════════════════════════════════
// Onglet 1 : Actifs maintenant
// ═══════════════════════════════════════════════════════════════

function renderActiveBlocks(blocks) {
    const container = el('sv-active-list');
    if (!container) return;
    if (!blocks.length) {
        container.innerHTML = '<div class="sv-empty">⬜ Aucun technicien actif en ce moment.</div>';
        return;
    }
    container.innerHTML = blocks.map(b => `
        <div class="sv-active-card" id="sv-block-${b.id}">
            <div class="sv-card-emp-name">👷 ${escHtml(b.employee_name)}</div>
            <div class="sv-card-meta">
                <strong>${escHtml(b.wo_name)}</strong><br>
                OF : ${escHtml(b.mo_name)}<br>
                Poste : ${escHtml(b.workcenter || '—')}
            </div>
            <div class="sv-card-timer" id="sv-timer-${b.id}">—</div>
            <div class="sv-card-actions">
                <button class="sv-action-btn danger" onclick="forceStop(${b.id})">
                    ⏹ Forcer l'arrêt
                </button>
            </div>
        </div>
    `).join('');
}

function startElapsedTick() {
    if (Sv.tickTimer) clearInterval(Sv.tickTimer);
    Sv.tickTimer = setInterval(() => {
        const now = Date.now() / 1000;
        Sv.activeBlocks.forEach(b => {
            const timerEl = el(`sv-timer-${b.id}`);
            if (timerEl && b.date_start_ts) {
                const elapsed = Math.max(0, now - b.date_start_ts);
                timerEl.textContent = fmtSec(elapsed);
            }
        });
    }, 1000);
}

// ═══════════════════════════════════════════════════════════════
// Onglet 2 : OF Lancés
// ═══════════════════════════════════════════════════════════════

function renderMOList(mos) {
    const container = el('sv-mo-list');
    if (!container) return;
    if (!mos.length) {
        container.innerHTML = '<div class="sv-empty">📭 Aucun OF en cours.</div>';
        return;
    }
    const rows = mos.map(mo => {
        const pct = mo.burndown || 0;
        const fillCls = pct < 80 ? '' : pct <= 110 ? 'warn' : 'over';
        const fillW = Math.min(pct, 100);
        const prioCls = mo.priority === '2' ? 'prio-2' : mo.priority === '1' ? 'prio-1' : '';
        const prioLabel = mo.priority === '2' ? '🔴 Critique' : mo.priority === '1' ? '⚠ Urgent' : '';
        return `
        <div class="sv-mo-row ${prioCls}">
            <div>
                <div class="sv-mo-name">${escHtml(mo.name)}${prioLabel ? ` <span class="sv-shift-badge active-now" style="margin-left:8px">${prioLabel}</span>` : ''}</div>
                <div class="sv-mo-info">${escHtml(mo.product || '—')}  ·  Qté : ${mo.qty || 1}</div>
            </div>
            <div class="sv-burndown-wrap">
                <div class="sv-burndown-label">
                    <span>Avancement</span>
                    <strong>${pct.toFixed(1)} %</strong>
                </div>
                <div class="sv-burndown-bar">
                    <div class="sv-burndown-fill ${fillCls}" style="width:${fillW}%"></div>
                </div>
            </div>
        </div>`;
    }).join('');
    container.innerHTML = `<div class="sv-mo-list">${rows}</div>`;
}

// ═══════════════════════════════════════════════════════════════
// Onglet 3 : Techniciens du jour
// ═══════════════════════════════════════════════════════════════

function renderEmployeeSummary(emps) {
    const container = el('sv-emp-list');
    if (!container) return;
    if (!emps.length) {
        container.innerHTML = '<div class="sv-empty">👤 Aucun technicien actif aujourd\'hui.</div>';
        return;
    }
    container.innerHTML = emps.map(emp => {
        const isActive = emp.is_active;
        const avatar = `<div class="sv-emp-avatar-placeholder">${escHtml((emp.name || '?')[0].toUpperCase())}</div>`;
        const activeLine = isActive && emp.current_mo
            ? `<div class="sv-emp-current">
                <span class="sv-emp-active-dot"></span>
                <span class="sv-emp-current-mo">📋 ${escHtml(emp.current_mo)}</span>
                ${emp.current_op ? `<br><span class="sv-emp-current-op">⚙️ ${escHtml(emp.current_op)}</span>` : ''}
                ${emp.current_workcenter ? `<br><span class="sv-emp-current-wc">🏭 ${escHtml(emp.current_workcenter)}</span>` : ''}
               </div>`
            : (isActive ? `<div class="sv-emp-current"><span class="sv-emp-active-dot"></span> <em style="color:var(--atelier-muted)">Actif</em></div>` : '');
        return `
        <div class="sv-emp-card ${isActive ? 'sv-emp-card-active' : ''}">
            ${avatar}
            <div class="sv-emp-name">${escHtml(emp.name)}</div>
            ${activeLine}
            <div class="sv-emp-total">${fmtMin(emp.total_minutes || 0)}</div>
            <div class="sv-emp-ops">${emp.ops_count || 0} opération(s) aujourd'hui</div>
        </div>`;
    }).join('');
}

// ═══════════════════════════════════════════════════════════════
// Onglet 4 : Vacations
// ═══════════════════════════════════════════════════════════════

function renderShifts(shifts) {
    const container = el('sv-shift-list');
    if (!container) return;
    if (!shifts.length) {
        container.innerHTML = '<div class="sv-empty">🕐 Aucune vacation configurée.</div>';
        return;
    }
    const now = new Date();
    const currentHour = now.getHours() + now.getMinutes() / 60;
    const rows = shifts.map(sh => {
        const isActive = currentHour >= sh.start_hour && currentHour < sh.end_hour;
        const badgeCls = isActive ? 'active-now' : 'inactive';
        const badgeLabel = isActive ? '🟢 En cours' : '⬜ Inactive';
        const empList = (sh.employee_names || []).join(', ') || 'Aucun employé';
        return `
        <div class="sv-shift-row">
            <div>
                <div class="sv-shift-name">${escHtml(sh.name)}</div>
                <div class="sv-shift-hours">⏱ ${floatToTime(sh.start_hour)} – ${floatToTime(sh.end_hour)}</div>
                <div class="sv-shift-emps">👷 ${escHtml(empList)}</div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:10px">
                <span class="sv-shift-badge ${badgeCls}">${badgeLabel}</span>
                ${sh.auto_close_timers
                    ? `<button class="sv-action-btn warning" onclick="closeShift(${sh.id})">⏹ Clôturer</button>`
                    : '<span class="sv-muted" style="font-size:0.8rem">Clôture auto: non</span>'
                }
            </div>
        </div>`;
    }).join('');
    container.innerHTML = `<div class="sv-shift-list">${rows}</div>`;
}

// ═══════════════════════════════════════════════════════════════
// Actions superviseur
// ═══════════════════════════════════════════════════════════════

async function forceStop(blockId) {
    if (!confirm('Forcer l\'arrêt de ce bloc de temps ?')) return;
    try {
        const result = await rpc('/atelier/api/supervisor/force_stop', { block_id: blockId });
        if (result.success) {
            svToast('Bloc arrêté avec succès.', 'info');
            await loadOverview();
        } else {
            svToast('Erreur : ' + (result.error || 'inconnue'), 'error');
        }
    } catch (e) {
        svToast('Erreur réseau : ' + e.message, 'error');
    }
}

async function closeShift(shiftId) {
    if (!confirm('Clôturer tous les blocs ouverts de cette vacation ?')) return;
    try {
        const result = await rpc('/atelier/api/supervisor/close_shift', { shift_id: shiftId });
        if (result.success) {
            svToast(`${result.closed || 0} bloc(s) clôturé(s).`, 'info');
            await loadOverview();
        } else {
            svToast('Erreur : ' + (result.error || 'inconnue'), 'error');
        }
    } catch (e) {
        svToast('Erreur réseau : ' + e.message, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
// Sécurité XSS
// ═══════════════════════════════════════════════════════════════

function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ═══════════════════════════════════════════════════════════════
// Démarrage
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    startClock();

    // Tab buttons
    document.querySelectorAll('.sv-tab').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Refresh button
    const refreshBtn = el('sv-refresh-btn');
    if (refreshBtn) refreshBtn.addEventListener('click', loadOverview);

    // Stats refresh button
    const statsRefreshBtn = el('sv-stats-refresh-btn');
    if (statsRefreshBtn) statsRefreshBtn.addEventListener('click', () => { Sv.statsData = null; loadStats(); });

    // Période stats
    document.querySelectorAll('.sv-period-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            Sv.statsPeriod = btn.dataset.period;
            document.querySelectorAll('.sv-period-btn').forEach(b => b.classList.toggle('active', b === btn));
            Sv.statsData = null;
            loadStats();
        });
    });

    // Premier chargement
    loadOverview();

    // Auto-refresh toutes les 10 secondes
    Sv.refreshTimer = setInterval(loadOverview, 10000);
});
