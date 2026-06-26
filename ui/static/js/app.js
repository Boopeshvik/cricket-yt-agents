// ── Navigation ────────────────────────────────────────────────────────────────

function showSection(id, el) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    if (el) el.classList.add('active');
}

// ── Format markdown ───────────────────────────────────────────────────────────

function formatMessage(text) {
    if (!text) return '';
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/^### (.*$)/gm, '<h4 style="color:#fff;margin:10px 0 4px">$1</h4>');
    text = text.replace(/^## (.*$)/gm, '<h3 style="color:#4ade80;margin:12px 0 6px">$1</h3>');
    text = text.replace(/^\- (.*$)/gm, '<li style="margin:4px 0;color:#cbd5e1">$1</li>');
    text = text.replace(/^\d+\. (.*$)/gm, '<li style="margin:4px 0;color:#cbd5e1">$1</li>');
    text = text.replace(/(<li.*<\/li>\n?)+/g, '<ul style="padding-left:18px;margin:8px 0">$&</ul>');
    text = text.replace(/\n\n/g, '<br><br>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

// ── Run Agent ─────────────────────────────────────────────────────────────────

async function runAgent(agentId) {
    const logEl = document.getElementById(`log-${agentId}`) ||
                  document.getElementById(`log-${agentId}-pub`);
    if (!logEl) return;

    logEl.style.display = 'block';
    logEl.textContent   = '';

    const btn = event.currentTarget;
    btn.disabled    = true;
    btn.textContent = '⏳ Running...';

    const agentNames = {
        '1': 'Creative Head', '2': 'Visual Designer',
        '3': 'Analytics Manager', '4': 'Executive Reporter', '5': 'Auto Publisher'
    };

    logEl.textContent = `Starting Agent ${agentId} — ${agentNames[agentId] || ''}...\nPlease wait, this may take 30–90 seconds...\n`;

    let dots = 0;
    const timer = setInterval(() => {
        dots++;
        const base = `Starting Agent ${agentId} — ${agentNames[agentId] || ''}...\nPlease wait, this may take 30–90 seconds...\n`;
        logEl.textContent = base + `⏳ Running${'.'.repeat(dots % 4)}`;
        logEl.scrollTop = logEl.scrollHeight;
    }, 1000);

    try {
        const response = await fetch(`/api/run-agent/${agentId}`, { method: 'POST' });
        clearInterval(timer);
        const data = await response.json();
        if (data.status === 'success') {
            logEl.textContent += `\n\n✅ ${data.message}\n🔄 Refresh the page to see updated data.`;
        } else {
            logEl.textContent += `\n\n❌ Error: ${data.detail}`;
        }
    } catch (err) {
        clearInterval(timer);
        logEl.textContent += `\n\n❌ Failed: ${err.message}`;
    }

    btn.disabled    = false;
    btn.textContent = `▶ Run Agent ${agentId}`;
    logEl.scrollTop = logEl.scrollHeight;
}

// ── Chat ──────────────────────────────────────────────────────────────────────

async function sendChat(agentNum) {
    const input   = document.getElementById(`chat-input-${agentNum}`);
    const chatBox = document.getElementById(`chat-box-${agentNum}`);
    const message = input.value.trim();
    if (!message) return;

    chatBox.innerHTML += `<div class="chat-msg user">${message}</div>`;
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    const typingId = 'typing-' + Date.now();
    chatBox.innerHTML += `
        <div class="chat-msg agent" id="${typingId}">
            <div class="sender">Agent ${agentNum}</div>
            <span>Thinking...</span>
        </div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch(`/api/chat/agent${agentNum}`, {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify({ message })
        });
        const data = await response.json();
        document.getElementById(typingId)?.remove();
        chatBox.innerHTML += `
            <div class="chat-msg agent">
                <div class="sender">Agent ${agentNum}</div>
                ${formatMessage(data.reply || data.error)}
            </div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (err) {
        document.getElementById(typingId)?.remove();
        chatBox.innerHTML += `
            <div class="chat-msg agent">
                <div class="sender">Agent ${agentNum}</div>
                Error connecting to agent.
            </div>`;
    }
}

// ── Report ────────────────────────────────────────────────────────────────────

async function sendReport() {
    const status = document.getElementById('report-status');
    status.textContent = '⏳ Sending report...';
    try {
        const response = await fetch('/api/run-agent/4', { method: 'POST' });
        const data     = await response.json();
        status.textContent = data.status === 'success'
            ? '✅ Report sent successfully!'
            : '❌ Error sending report.';
    } catch (err) {
        status.textContent = '❌ Error sending report.';
    }
}

function loadReport() {
    document.getElementById('report-frame').src = '/api/report?' + Date.now();
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => alert('Copied to clipboard!'));
}

// ── Handoff ───────────────────────────────────────────────────────────────────

async function handoffToAgent2() {
    const btn    = document.querySelector('.btn-handoff');
    const status = document.getElementById('handoff-status');

    btn.disabled       = true;
    btn.textContent    = '⏳ Sending to Agent 2...';
    status.textContent = 'Preparing content plan for Agent 2...';

    try {
        const response = await fetch('/api/handoff/agent1-to-agent2', { method: 'POST' });
        const data     = await response.json();

        if (data.status === 'success') {
            btn.textContent    = '✅ Sent to Agent 2!';
            status.textContent = '✅ Content plan sent! Go to Thumbnails tab to see Agent 2\'s response.';
            status.style.color = '#4ade80';
            const chat2 = document.getElementById('chat-box-2');
            if (chat2) {
                chat2.innerHTML += `
                    <div class="chat-msg agent">
                        <div class="sender">Agent 2 — Visual Designer</div>
                        ${formatMessage(data.reply)}
                    </div>`;
                chat2.scrollTop = chat2.scrollHeight;
            }
            setTimeout(() => {
                status.textContent = '👉 Click "Thumbnails" in the sidebar to see Agent 2\'s thumbnail concepts.';
            }, 2000);
        } else {
            btn.disabled       = false;
            btn.textContent    = '🎨 Send to Agent 2 — Visual Designer';
            status.textContent = '❌ Error: ' + (data.error || 'Unknown error');
            status.style.color = '#f87171';
        }
    } catch (err) {
        btn.disabled       = false;
        btn.textContent    = '🎨 Send to Agent 2 — Visual Designer';
        status.textContent = '❌ Failed: ' + err.message;
        status.style.color = '#f87171';
    }
}

// ── Performance Review ────────────────────────────────────────────────────────

let perfData        = null;
let benchmarks      = {};
let currentBenchTab = 'video';
let sortCol         = 'views';
let sortAsc         = false;
let chartInstances  = {};

const METRIC_LABELS = {
    impressions       : 'Impressions',
    views             : 'Avg Views / Video',
    ctr               : 'CTR %',
    avg_view_duration : 'Avg Duration',
    audience_retention: 'Avg Retention %',
    watch_hours       : 'Avg Watch Hours',
    subs_gained       : 'Avg Subs / Video',
    returning_viewers : 'Returning Viewers'
};

const METRIC_KEYS = Object.keys(METRIC_LABELS);

function setDefaultDates() {
    const end   = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 28);
    const fmt = d => d.toISOString().split('T')[0];
    const si  = document.getElementById('perf-start');
    const ei  = document.getElementById('perf-end');
    if (si) si.value = fmt(start);
    if (ei) ei.value = fmt(end);
}

async function loadBenchmarks() {
    try {
        const res  = await fetch('/api/benchmarks');
        benchmarks = await res.json();
        renderBenchmarkGrid();
    } catch (e) {
        console.error('Could not load benchmarks', e);
    }
}

function renderBenchmarkGrid() {
    const grid = document.getElementById('benchmark-grid');
    if (!grid) return;
    const b = benchmarks[currentBenchTab] || {};
    grid.innerHTML = METRIC_KEYS.map(key => `
        <div class="bench-item">
            <div class="bench-item-label">${METRIC_LABELS[key]}</div>
            <input type="number" id="bench-${key}" value="${b[key] || 0}" step="0.1">
        </div>`).join('');
}

function switchBenchTab(type, btn) {
    currentBenchTab = type;
    document.querySelectorAll('.bench-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderBenchmarkGrid();
}

async function saveBenchmarks() {
    const status = document.getElementById('bench-save-status');
    METRIC_KEYS.forEach(key => {
        const input = document.getElementById(`bench-${key}`);
        if (input) {
            if (!benchmarks[currentBenchTab]) benchmarks[currentBenchTab] = {};
            benchmarks[currentBenchTab][key] = parseFloat(input.value) || 0;
        }
    });
    try {
        const res  = await fetch('/api/benchmarks', {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify(benchmarks)
        });
        const data = await res.json();
        if (data.status === 'saved') {
            status.textContent = '✅ Benchmarks saved!';
            setTimeout(() => status.textContent = '', 3000);
        }
    } catch (e) {
        status.textContent = '❌ Failed to save';
    }
}

async function fetchPerformance() {
    const start = document.getElementById('perf-start').value;
    const end   = document.getElementById('perf-end').value;
    const type  = document.getElementById('perf-type').value;
    const limit = parseInt(document.getElementById('perf-limit').value) || 10;

    if (!start || !end) {
        alert('Please select both start and end dates');
        return;
    }

    document.getElementById('perf-loading').style.display = 'block';
    document.getElementById('perf-results').style.display = 'none';

    try {
        const res = await fetch('/api/performance', {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify({
                start_date  : start,
                end_date    : end,
                content_type: type,
                max_videos  : limit
            })
        });

        document.getElementById('perf-loading').style.display = 'none';

        if (!res.ok) {
            alert('Server error: ' + res.status);
            return;
        }

        const data = await res.json();

        if (!data || data.status === 'error') {
            alert('Error: ' + (data?.detail || 'Unknown error'));
            return;
        }

        perfData = data;
        renderSummary(data.consolidated, type);
        renderTable(data.individual, type);
        renderCharts(data.individual);
        document.getElementById('perf-results').style.display = 'block';

    } catch (e) {
        document.getElementById('perf-loading').style.display = 'none';
        alert('Failed: ' + e.message);
    }
}

function renderSummary(consolidated, type) {
    const grid  = document.getElementById('perf-summary-grid');
    const bench = benchmarks[type] || {};
    const title = document.getElementById('perf-summary-title');

    if (title && consolidated.num_videos) {
        title.innerHTML = `📊 Consolidated Summary <span style="font-size:12px;color:#64748b;font-weight:400">(avg across ${consolidated.num_videos} videos)</span>`;
    }

    const metricMap = {
        impressions       : consolidated.impressions,
        views             : consolidated.views,
        ctr               : consolidated.ctr,
        avg_view_duration : consolidated.avg_view_duration_sec,
        audience_retention: consolidated.audience_retention,
        watch_hours       : consolidated.watch_hours,
        subs_gained       : consolidated.subs_gained,
        returning_viewers : consolidated.returning_viewers
    };

    grid.innerHTML = METRIC_KEYS.map(key => {
        const actual   = metricMap[key] || 0;
        const target   = bench[key] || 1;
        const isNA     = key === 'impressions' || key === 'ctr' || key === 'returning_viewers';
        const isGood   = actual >= target;
        const pct      = Math.min((actual / target) * 100, 100).toFixed(0);
        const diff     = actual - target;
        const diffSign = diff >= 0 ? '+' : '';
        const diffFmt  = (key === 'ctr' || key === 'audience_retention')
                         ? `${diffSign}${diff.toFixed(2)}`
                         : `${diffSign}${Math.round(diff).toLocaleString()}`;

        let displayVal;
        if (isNA) {
            displayVal = 'N/A';
        } else if (key === 'audience_retention') {
            displayVal = actual.toFixed(1) + '%';
        } else if (key === 'avg_view_duration') {
            const m = Math.floor(actual / 60);
            const s = Math.floor(actual % 60);
            displayVal = `${m}:${String(s).padStart(2, '0')}`;
        } else if (key === 'watch_hours') {
            displayVal = actual.toFixed(1) + 'h';
        } else {
            displayVal = Math.round(actual).toLocaleString();
        }

        return `
            <div class="perf-metric-card ${isNA ? 'na-card' : (isGood ? 'positive' : 'negative')}">
                <div class="metric-status">${isNA ? '—' : (isGood ? '✅' : '❌')}</div>
                <div class="metric-name">${METRIC_LABELS[key]}</div>
                <div class="metric-actual" style="${isNA ? 'color:#475569;font-size:16px' : ''}">${displayVal}</div>
                <div class="metric-benchmark">${isNA ? 'Not available via API' : 'Target: ' + target.toLocaleString()}</div>
                ${isNA ? '' : `
                <div class="metric-bar-bg">
                    <div class="metric-bar-fill ${isGood ? 'positive' : 'negative'}" style="width:${pct}%"></div>
                </div>
                <div class="metric-diff ${isGood ? 'positive' : 'negative'}">${diffFmt} vs target</div>`}
            </div>`;
    }).join('');
}

function renderCharts(videos) {
    if (!videos || !videos.length) return;

    const labels = videos.map(v =>
        v.title.substring(0, 18) + (v.title.length > 18 ? '…' : '')
    );

    const makeConfig = (data, label, bgColor, borderColor) => ({
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label,
                data,
                backgroundColor: bgColor,
                borderColor,
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    ticks: { color: '#64748b', font: { size: 9 }, maxRotation: 45 },
                    grid: { color: '#1e2235' }
                },
                y: {
                    ticks: { color: '#64748b', font: { size: 9 } },
                    grid: { color: '#1e2235' }
                }
            }
        }
    });

    // Destroy old charts
    Object.values(chartInstances).forEach(c => c.destroy());
    chartInstances = {};

    chartInstances.views = new Chart(
        document.getElementById('chart-views'),
        makeConfig(videos.map(v => v.views), 'Views', 'rgba(96,165,250,0.6)', '#3b82f6')
    );

    chartInstances.duration = new Chart(
        document.getElementById('chart-duration'),
        makeConfig(
            videos.map(v => +(v.avg_view_duration_sec / 60).toFixed(1)),
            'Duration (mins)', 'rgba(251,146,60,0.6)', '#f97316'
        )
    );

    chartInstances.retention = new Chart(
        document.getElementById('chart-retention'),
        makeConfig(videos.map(v => v.audience_retention), 'Retention %', 'rgba(74,222,128,0.6)', '#22c55e')
    );

    chartInstances.watch = new Chart(
        document.getElementById('chart-watch'),
        makeConfig(videos.map(v => v.watch_hours), 'Watch Hours', 'rgba(196,181,253,0.6)', '#a78bfa')
    );
}

function renderTable(videos, type) {
    const bench = benchmarks[type] || {};
    const count = document.getElementById('video-count');
    if (count) count.textContent = `(${videos.length} ${type}s)`;

    const sorted = [...videos].sort((a, b) => {
        const av = a[sortCol] || 0;
        const bv = b[sortCol] || 0;
        if (typeof av === 'string') return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
        return sortAsc ? av - bv : bv - av;
    });

    const tbody = document.getElementById('perf-table-body');
    if (!sorted.length) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:#64748b;padding:24px">No ${type}s found in this date range</td></tr>`;
        return;
    }

    const cls = (val, key) => {
        const target = bench[key];
        if (!target) return '';
        return val >= target ? 'good' : 'bad';
    };

    tbody.innerHTML = sorted.map(v => `
        <tr>
            <td class="td-title" title="${v.title}">${v.title.substring(0, 40)}${v.title.length > 40 ? '...' : ''}</td>
            <td>${v.published}</td>
            <td class="${cls(v.views, 'views')}">${v.views.toLocaleString()}</td>
            <td class="${cls(v.avg_view_duration_sec, 'avg_view_duration')}">${v.avg_view_duration_fmt}</td>
            <td class="${cls(v.audience_retention, 'audience_retention')}">${v.audience_retention.toFixed(1)}%</td>
            <td class="${cls(v.watch_hours, 'watch_hours')}">${v.watch_hours}h</td>
            <td class="${cls(v.subs_gained, 'subs_gained')}">${v.subs_gained}</td>
            <td>${v.likes.toLocaleString()}</td>
            <td>${v.comments.toLocaleString()}</td>
        </tr>`
    ).join('');
}

function sortTable(col) {
    if (sortCol === col) sortAsc = !sortAsc;
    else { sortCol = col; sortAsc = false; }
    if (perfData) renderTable(perfData.individual, perfData.content_type);
}

function exportPDF() {
    window.print();
}

// ── Financials ────────────────────────────────────────────────────────────────

let finData        = { categories: [], entries: [] };
let finChartMonth  = null;
let finChartCat    = null;

const FIXED_COSTS = [
    { name: "Editor Salary", amount: 65.00 },
    { name: "Riverside",     amount: 29.00 },
    { name: "CapCut",        amount: 21.99 },
    { name: "Canva",         amount: 13.00 }
];

async function loadFinancials() {
    try {
        const res = await fetch('/api/financials');
        finData   = await res.json();
        renderFinancials();
        loadROI();
    } catch (e) {
        console.error('Could not load financials', e);
    }
}

async function loadROI() {
    try {
        const res  = await fetch('/api/financials/roi');
        const data = await res.json();

        document.getElementById('roi-total-spend').textContent  = `£${data.total_spend.toFixed(2)}`;
        document.getElementById('roi-cost-per-sub').textContent = `£${data.cost_per_sub.toFixed(2)}`;
        document.getElementById('roi-cost-per-1k').textContent  = `£${data.cost_per_1k_views.toFixed(2)}`;
        document.getElementById('roi-cost-per-hr').textContent  = `£${data.cost_per_watch_hr.toFixed(2)}`;
        document.getElementById('roi-projected').textContent    = `£${data.projected_revenue.toFixed(2)}`;
        document.getElementById('roi-pct').textContent          = `${data.roi_pct}%`;
    } catch (e) {
        console.error('Could not load ROI', e);
    }
}

function renderFinancials() {
    renderCategoryDropdown();
    renderCategoryManager();
    renderEntriesTable();
    renderFinCharts();
}

function renderCategoryDropdown() {
    const sel = document.getElementById('fin-category');
    if (!sel) return;
    sel.innerHTML = finData.categories.map(c =>
        `<option value="${c.id}">${c.name}</option>`
    ).join('');
}

function renderCategoryManager() {
    const container = document.getElementById('fin-cats');
    if (!container) return;
    container.innerHTML = finData.categories.map(c => `
        <div class="fin-cat-item">
            <div class="fin-cat-dot" style="background:${c.color}"></div>
            <input class="fin-cat-name" value="${c.name}"
                   onblur="updateCategory('${c.id}', this.value, '${c.color}')">
            <button class="fin-cat-delete" onclick="deleteCategory('${c.id}')">✕</button>
        </div>`
    ).join('');
}

function renderEntriesTable() {
    const tbody = document.getElementById('fin-entries-table');
    if (!tbody) return;

    const catMap = {};
    finData.categories.forEach(c => catMap[c.id] = c);

    const sorted = [...finData.entries].sort((a, b) => b.month.localeCompare(a.month));

    if (!sorted.length) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#64748b;padding:24px">No expenses logged yet</td></tr>`;
        return;
    }

    tbody.innerHTML = sorted.map(e => {
        const cat = catMap[e.category_id] || { name: 'Unknown', color: '#64748b' };
        return `
            <tr>
                <td>${e.month}</td>
                <td>
                    <span style="display:inline-flex;align-items:center;gap:6px">
                        <span style="width:8px;height:8px;border-radius:50%;background:${cat.color};display:inline-block"></span>
                        ${cat.name}
                    </span>
                </td>
                <td style="color:#22c55e;font-weight:600">£${e.amount.toFixed(2)}</td>
                <td style="color:#64748b">${e.note || '—'}</td>
                <td style="color:#64748b;font-size:11px">${e.created_at?.split(' ')[0] || ''}</td>
                <td>
                    <button onclick="deleteEntry('${e.id}')"
                            style="background:none;border:none;color:#ef4444;cursor:pointer;font-size:13px">
                        🗑 Delete
                    </button>
                </td>
            </tr>`;
    }).join('');
}

function renderFinCharts() {
    // Monthly chart
    const monthlyMap = {};
    finData.entries.forEach(e => {
        monthlyMap[e.month] = (monthlyMap[e.month] || 0) + e.amount;
    });

    const months = Object.keys(monthlyMap).sort();
    const monthAmounts = months.map(m => +monthlyMap[m].toFixed(2));

    if (finChartMonth) finChartMonth.destroy();
    const ctxM = document.getElementById('fin-chart-monthly');
    if (ctxM && months.length) {
        finChartMonth = new Chart(ctxM, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: 'Monthly Spend (£)',
                    data: monthAmounts,
                    backgroundColor: 'rgba(96,165,250,0.6)',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#64748b' }, grid: { color: '#1e2235' } },
                    y: { ticks: { color: '#64748b', callback: v => '£' + v }, grid: { color: '#1e2235' } }
                }
            }
        });
    }

    // Category chart
    const catMap = {};
    finData.categories.forEach(c => catMap[c.id] = c);

    const catTotals = {};
    finData.entries.forEach(e => {
        const name = catMap[e.category_id]?.name || 'Other';
        catTotals[name] = (catTotals[name] || 0) + e.amount;
    });

    const catNames   = Object.keys(catTotals);
    const catAmounts = catNames.map(n => +catTotals[n].toFixed(2));
    const catColors  = finData.categories.map(c => c.color);

    if (finChartCat) finChartCat.destroy();
    const ctxC = document.getElementById('fin-chart-category');
    if (ctxC && catNames.length) {
        finChartCat = new Chart(ctxC, {
            type: 'doughnut',
            data: {
                labels: catNames,
                datasets: [{
                    data: catAmounts,
                    backgroundColor: catColors,
                    borderColor: '#1a1d27',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#94a3b8', font: { size: 11 } }
                    }
                }
            }
        });
    }
}

async function addExpense() {
    const category_id = document.getElementById('fin-category').value;
    const amount      = parseFloat(document.getElementById('fin-amount').value);
    const month       = document.getElementById('fin-month').value;
    const note        = document.getElementById('fin-note').value;

    if (!category_id || !amount || !month) {
        alert('Please fill in Category, Amount and Month');
        return;
    }

    try {
        const res  = await fetch('/api/financials/entry', {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify({ category_id, amount, month, note })
        });
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('fin-amount').value = '';
            document.getElementById('fin-note').value   = '';
            await loadFinancials();
        }
    } catch (e) {
        alert('Failed to add expense: ' + e.message);
    }
}

async function quickAddMonth() {
    const month = document.getElementById('fin-quick-month').value;
    if (!month) {
        alert('Please select a month');
        return;
    }

    const catMap = {};
    finData.categories.forEach(c => catMap[c.name] = c.id);

    for (const cost of FIXED_COSTS) {
        const category_id = catMap[cost.name];
        if (!category_id) continue;

        await fetch('/api/financials/entry', {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify({
                category_id,
                amount: cost.amount,
                month,
                note: 'Monthly fixed cost'
            })
        });
    }

    await loadFinancials();
    alert(`✅ Logged all monthly expenses for ${month}!`);
}

async function deleteEntry(entryId) {
    if (!confirm('Delete this expense?')) return;
    try {
        await fetch(`/api/financials/entry/${entryId}`, { method: 'DELETE' });
        await loadFinancials();
    } catch (e) {
        alert('Failed to delete');
    }
}

async function addCategory() {
    const name = document.getElementById('fin-new-cat-name').value.trim();
    if (!name) { alert('Enter a category name'); return; }

    try {
        const res  = await fetch('/api/financials/category', {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('fin-new-cat-name').value = '';
            await loadFinancials();
        }
    } catch (e) {
        alert('Failed to add category');
    }
}

async function updateCategory(catId, name, color) {
    try {
        await fetch(`/api/financials/category/${catId}`, {
            method : 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify({ name, color })
        });
        await loadFinancials();
    } catch (e) {
        console.error('Failed to update category', e);
    }
}

async function deleteCategory(catId) {
    if (!confirm('Delete this category and all its expenses?')) return;
    try {
        await fetch(`/api/financials/category/${catId}`, { method: 'DELETE' });
        await loadFinancials();
    } catch (e) {
        alert('Failed to delete category');
    }
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    setDefaultDates();
    loadBenchmarks();
    loadFinancials();

    // Set default month fields to current month
    const now       = new Date();
    const monthStr  = now.toISOString().slice(0, 7);
    const mField    = document.getElementById('fin-month');
    const qmField   = document.getElementById('fin-quick-month');
    if (mField)  mField.value  = monthStr;
    if (qmField) qmField.value = monthStr;
});