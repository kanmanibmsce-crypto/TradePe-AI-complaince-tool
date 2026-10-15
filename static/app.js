/* =============================================================
   TradePe Compliance Dashboard — app.js
   Vanilla JS SPA, no build step, no frameworks.
   ============================================================= */

'use strict';

// ─── STATE ────────────────────────────────────────────────────────────────────

const State = {
  currentView: null,
  currentCaseId: null,
};

// ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

function recommendationBadge(rec) {
  const map = {
    APPROVE:       ['badge badge-green',  'APPROVE'],
    MANUAL_REVIEW: ['badge badge-yellow', 'REVIEW'],
    ESCALATE:      ['badge badge-red',    'ESCALATE'],
  };
  const [cls, label] = map[rec] || ['badge badge-grey', rec || 'UNKNOWN'];
  return `<span class="${cls}">${label}</span>`;
}

function outcomeBadge(outcome) {
  const map = {
    PASS:   ['badge badge-green',  'PASS'],
    REVIEW: ['badge badge-yellow', 'REVIEW'],
    FAIL:   ['badge badge-red',    'FAIL'],
  };
  const [cls, label] = map[outcome] || ['badge badge-grey', outcome || '–'];
  return `<span class="${cls}">${label}</span>`;
}

function levelBadge(level) {
  const map = {
    clear:    ['badge badge-green',  'CLEAR'],
    review:   ['badge badge-yellow', 'REVIEW'],
    high:     ['badge badge-red',    'HIGH'],
    critical: ['badge badge-red',    'CRITICAL'],
  };
  const [cls, label] = map[level] || ['badge badge-grey', level || '–'];
  return `<span class="${cls}">${label}</span>`;
}

function statusBadge(status) {
  const map = {
    pending:  ['badge badge-yellow', 'Pending'],
    approve:  ['badge badge-green',  'Approved'],
    hold:     ['badge badge-yellow', 'On Hold'],
    escalate: ['badge badge-red',    'Escalated'],
    escalated:['badge badge-red',    'Escalated'],
    reject:   ['badge badge-red',    'Rejected'],
  };
  const [cls, label] = map[status] || ['badge badge-grey', status || '–'];
  return `<span class="${cls}">${label}</span>`;
}

function formatDate(ts) {
  if (!ts) return '–';
  const d = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts);
  if (isNaN(d)) return ts;
  return d.toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function severityClass(rec) {
  if (rec === 'ESCALATE') return 'border-red';
  if (rec === 'MANUAL_REVIEW') return 'border-yellow';
  return 'border-green';
}

function esc(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─── API WRAPPER ──────────────────────────────────────────────────────────────

async function api(path, opts = {}) {
  try {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...opts,
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
    return json;
  } catch (err) {
    console.error('API error:', path, err);
    throw err;
  }
}

// ─── ROUTER ───────────────────────────────────────────────────────────────────

const ROUTES = {
  '#dashboard':   'dashboard',
  '#screening':   'screening',
  '#queue':       'queue',
  '#cases':       'cases',
  '#regulatory':  'regulatory',
  '#agents':      'agents',
  '#audit':       'audit',
};

function getViewFromHash() {
  return ROUTES[location.hash] || 'dashboard';
}

function renderPage(name) {
  State.currentView = name;
  updateNav(name);
  const app = document.getElementById('app');
  app.innerHTML = '<div class="loading">Loading…</div>';

  const renderers = {
    dashboard:  renderDashboard,
    screening:  renderScreening,
    queue:      renderQueue,
    cases:      renderCases,
    regulatory: renderRegulatory,
    agents:     renderAgents,
    audit:      renderAudit,
  };

  const fn = renderers[name];
  if (fn) fn(app);
  else app.innerHTML = '<p class="error-msg">Unknown view.</p>';
}

function updateNav(view) {
  document.querySelectorAll('.nav-link').forEach(link => {
    const v = link.dataset.view;
    const normalized = v ? v.replace(/-/g, '').replace('newscreening', 'screening')
                            .replace('reviewqueue', 'queue')
                            .replace('regulatoryupdates', 'regulatory')
                            .replace('audittrail', 'audit') : '';
    link.classList.toggle('active', normalized === view);
  });
}

// ─── 1. DASHBOARD ─────────────────────────────────────────────────────────────

async function renderDashboard(el) {
  try {
    const data = await api('/api/dashboard');
    el.innerHTML = `
      <div class="view-header">
        <h1 class="view-title">Compliance Dashboard</h1>
        <p class="view-subtitle">Live overview of all compliance activity</p>
      </div>

      <div class="metric-grid">
        ${metricCard('Total Cases', data.total_cases, 'metric-blue')}
        ${metricCard('Needs Review', data.needs_review, 'metric-yellow')}
        ${metricCard('Auto Cleared', data.auto_cleared, 'metric-green')}
        ${metricCard('Escalated', data.escalated, 'metric-red')}
      </div>

      <div class="dashboard-grid">
        <section class="card dashboard-main">
          <h2 class="card-title">Recent Cases</h2>
          ${recentCasesTable(data.recent_cases)}
        </section>

        <aside class="card dashboard-side">
          <h2 class="card-title">Needs Attention</h2>
          ${attentionCasesList(data.attention_cases)}
        </aside>
      </div>

      <div class="dashboard-grid">
        <section class="card">
          <h2 class="card-title">Latest Regulatory Updates</h2>
          ${regUpdatesMini(data.regulatory_updates)}
        </section>

        <section class="card">
          <h2 class="card-title">Compliance Intelligence Network</h2>
          <div class="cin-summary">
            <p>TradePe's multi-agent compliance network continuously evaluates trade transactions against OFAC, UN, EU and PEP watchlists, customer risk profiles, trade document integrity, and real-time transaction patterns.</p>
            <ul class="cin-bullets">
              <li><strong>5 Specialized Agents</strong> — each covering a distinct risk dimension</li>
              <li><strong>Level A Scoring</strong> — weighted composite risk score</li>
              <li><strong>Level B Rules</strong> — hard-stop override rules for critical violations</li>
              <li><strong>Regulatory Intelligence</strong> — advisory context attached per case</li>
            </ul>
            <p class="cin-tagline">TradePe Recommends. Human Compliance Officer Decides.</p>
          </div>
        </section>
      </div>
    `;
  } catch (err) {
    el.innerHTML = errorHtml('Failed to load dashboard', err.message);
  }
}

function metricCard(label, value, cls) {
  return `
    <div class="metric-card ${cls}">
      <div class="metric-value">${value ?? 0}</div>
      <div class="metric-label">${label}</div>
    </div>`;
}

function recentCasesTable(cases) {
  if (!cases || !cases.length) return '<p class="empty-msg">No cases yet.</p>';
  const rows = cases.map(c => `
    <tr class="clickable-row" data-case-id="${c.id}">
      <td><code>${esc(c.case_ref)}</code></td>
      <td>${esc(c.counterparty_name)}</td>
      <td>${recommendationBadge(c.recommendation)}</td>
      <td>${statusBadge(c.status)}</td>
    </tr>`).join('');
  return `
    <table class="data-table">
      <thead><tr>
        <th>Ref</th><th>Counterparty</th><th>Recommendation</th><th>Status</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function attentionCasesList(cases) {
  if (!cases || !cases.length) return '<p class="empty-msg">No cases needing attention.</p>';
  return cases.map(c => `
    <div class="attention-item ${severityClass(c.recommendation)} clickable-row" data-case-id="${c.id}">
      <div class="attention-ref"><code>${esc(c.case_ref)}</code></div>
      <div class="attention-name">${esc(c.counterparty_name)}</div>
      <div>${recommendationBadge(c.recommendation)}</div>
    </div>`).join('');
}

function regUpdatesMini(updates) {
  if (!updates || !updates.length) return '<p class="empty-msg">No recent updates.</p>';
  return updates.map(u => `
    <div class="reg-mini-item">
      <div class="reg-mini-source">${esc(u.source)}</div>
      <div class="reg-mini-title">${esc(u.title)}</div>
      <div class="reg-mini-summary">${esc(u.summary)}</div>
    </div>`).join('');
}

// ─── 2. SCREENING ─────────────────────────────────────────────────────────────

function renderScreening(el) {
  el.innerHTML = `
    <div class="view-header">
      <h1 class="view-title">New Screening</h1>
    </div>

    <div class="tabs">
      <button class="tab-btn active" data-tab="quick">Quick Sanctions Check</button>
      <button class="tab-btn" data-tab="case">Create Compliance Case</button>
    </div>

    <div id="tab-quick" class="tab-panel active">
      ${renderQuickCheck()}
    </div>
    <div id="tab-case" class="tab-panel" style="display:none">
      ${renderCaseForm()}
    </div>
  `;

  el.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      el.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.dataset.tab;
      el.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
      document.getElementById(`tab-${tab}`).style.display = '';
    });
  });

  bindQuickCheck(el);
  bindCaseForm(el);
}

function renderQuickCheck() {
  return `
    <div class="card">
      <h2 class="card-title">Quick Sanctions Check</h2>
      <form id="quick-form" class="form-inline">
        <div class="form-group">
          <label for="qc-name">Name / Entity</label>
          <input id="qc-name" type="text" class="input" placeholder="e.g. Acme Trading Co." required />
        </div>
        <div class="form-group">
          <label for="qc-type">Entity Type</label>
          <select id="qc-type" class="input">
            <option value="entity">Entity</option>
            <option value="individual">Individual</option>
            <option value="vessel">Vessel</option>
          </select>
        </div>
        <div class="form-group">
          <label for="qc-country">Country (optional)</label>
          <input id="qc-country" type="text" class="input" placeholder="e.g. IN" />
        </div>
        <div class="form-actions">
          <button type="submit" class="btn-primary">Screen Now</button>
          <button type="button" id="demo-batch-btn" class="btn-secondary">Run Demo Batch</button>
        </div>
      </form>
      <div id="quick-result"></div>
      <div id="demo-batch-result"></div>
    </div>`;
}

function bindQuickCheck(el) {
  const form = el.querySelector('#quick-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = el.querySelector('#qc-name').value.trim();
    const entity_type = el.querySelector('#qc-type').value;
    const country = el.querySelector('#qc-country').value.trim();
    const resultEl = el.querySelector('#quick-result');
    resultEl.innerHTML = '<p class="loading">Screening…</p>';
    try {
      const data = await api('/api/screen', {
        method: 'POST',
        body: JSON.stringify({ name, entity_type, country }),
      });
      resultEl.innerHTML = renderScreenResult(data);
    } catch (err) {
      resultEl.innerHTML = errorHtml('Screening failed', err.message);
    }
  });

  el.querySelector('#demo-batch-btn').addEventListener('click', async () => {
    const resultEl = el.querySelector('#demo-batch-result');
    resultEl.innerHTML = '<p class="loading">Running demo batch…</p>';
    try {
      const data = await api('/api/demo-batch', { method: 'POST' });
      resultEl.innerHTML = renderDemoBatch(data.results);
    } catch (err) {
      resultEl.innerHTML = errorHtml('Demo batch failed', err.message);
    }
  });
}

function renderScreenResult(data) {
  const matchRows = data.matches && data.matches.length
    ? data.matches.map(m => `
        <tr>
          <td>${esc(m.matched_name)}</td>
          <td>${esc(m.list_name)}</td>
          <td>${m.score}</td>
          <td>${levelBadge(m.level)}</td>
        </tr>`).join('')
    : '<tr><td colspan="4" class="empty-msg">No matches found.</td></tr>';

  return `
    <div class="screen-result card-inset">
      <div class="screen-result-header">
        <strong>${esc(data.name)}</strong>
        <span>Score: <strong>${data.top_score}</strong></span>
        ${levelBadge(data.top_level)}
      </div>
      <table class="data-table">
        <thead><tr><th>Matched Name</th><th>List</th><th>Score</th><th>Level</th></tr></thead>
        <tbody>${matchRows}</tbody>
      </table>
    </div>`;
}

function renderDemoBatch(results) {
  if (!results || !results.length) return '<p class="empty-msg">No results.</p>';
  const rows = results.map(r => `
    <tr>
      <td><code>${esc(r.txn_id)}</code></td>
      <td>${esc(r.name)}</td>
      <td>${r.top_score}</td>
      <td>${levelBadge(r.top_level)}</td>
      <td>${r.match_count}</td>
    </tr>`).join('');
  return `
    <div class="card-inset">
      <h3 class="section-subtitle">Demo Batch Results</h3>
      <table class="data-table">
        <thead><tr>
          <th>Txn ID</th><th>Beneficiary</th><th>Score</th><th>Level</th><th>Matches</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function renderCaseForm() {
  return `
    <form id="case-form" novalidate>

      <!-- Agent 1: Sanctions (REQUIRED) -->
      <div class="agent-card required">
        <div class="agent-card-header">
          <span class="agent-badge">Agent 1</span>
          <span class="agent-title">Sanctions &amp; Watchlist Screening</span>
          <span class="badge badge-red">REQUIRED</span>
        </div>
        <div class="agent-card-body">
          <div class="form-row">
            <div class="form-group">
              <label>Counterparty Name *</label>
              <input name="counterparty_name" type="text" class="input" required placeholder="Entity or individual name" />
            </div>
            <div class="form-group">
              <label>Entity Type</label>
              <select name="entity_type" class="input">
                <option value="entity">Entity</option>
                <option value="individual">Individual</option>
                <option value="vessel">Vessel</option>
              </select>
            </div>
            <div class="form-group">
              <label>Counterparty Country</label>
              <input name="counterparty_country" type="text" class="input" placeholder="e.g. CN" />
            </div>
          </div>
        </div>
      </div>

      <!-- Agent 2: Customer Risk (REQUIRED) -->
      <div class="agent-card required">
        <div class="agent-card-header">
          <span class="agent-badge">Agent 2</span>
          <span class="agent-title">Customer Risk / KYC</span>
          <span class="badge badge-red">REQUIRED</span>
        </div>
        <div class="agent-card-body">
          <div class="form-row">
            <div class="form-group">
              <label>Customer Legal Name *</label>
              <input name="customer_legal_name" type="text" class="input" required placeholder="Registered company name" />
            </div>
            <div class="form-group">
              <label>IEC Code</label>
              <input name="customer_iec" type="text" class="input" placeholder="Import Export Code" />
            </div>
            <div class="form-group">
              <label>GST / PAN</label>
              <input name="customer_gst_pan" type="text" class="input" placeholder="GST or PAN number" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Customer Country *</label>
              <input name="customer_country" type="text" class="input" required placeholder="e.g. IN" />
            </div>
            <div class="form-group">
              <label>KYC Status</label>
              <select name="customer_kyc_status" class="input">
                <option value="verified">Verified</option>
                <option value="pending">Pending</option>
                <option value="expired">Expired</option>
              </select>
            </div>
            <div class="form-group">
              <label>UBO Count</label>
              <input name="customer_ubo_count" type="number" class="input" min="0" placeholder="0" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group checkbox-group">
              <label>
                <input name="customer_high_risk_flag" type="checkbox" />
                High Risk Customer
              </label>
            </div>
            <div class="form-group checkbox-group">
              <label>
                <input name="customer_adverse_media_flag" type="checkbox" />
                Adverse Media Flag
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Agent 3: Trade Document (OPTIONAL) -->
      <div class="agent-card optional">
        <div class="agent-card-header">
          <span class="agent-badge">Agent 3</span>
          <span class="agent-title">Trade Document Review</span>
          <span class="badge badge-grey">OPTIONAL</span>
          <label class="toggle-label">
            <input type="checkbox" id="toggle-trade" name="has_trade_doc" />
            Add Trade Documents
          </label>
        </div>
        <div class="agent-card-body collapsible" id="trade-doc-fields" style="display:none">
          <div class="form-row">
            <div class="form-group">
              <label>Invoice Number</label>
              <input name="invoice_number" type="text" class="input" placeholder="INV-001" />
            </div>
            <div class="form-group">
              <label>PO Number</label>
              <input name="po_number" type="text" class="input" placeholder="PO-001" />
            </div>
            <div class="form-group">
              <label>Bill of Lading</label>
              <input name="bol_number" type="text" class="input" placeholder="BOL-001" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Invoice Amount</label>
              <input name="invoice_amount" type="number" class="input" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label>PO Amount</label>
              <input name="po_amount" type="number" class="input" placeholder="0.00" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Invoice Seller</label>
              <input name="invoice_seller" type="text" class="input" />
            </div>
            <div class="form-group">
              <label>PO Buyer</label>
              <input name="po_buyer" type="text" class="input" />
            </div>
            <div class="form-group">
              <label>BOL Shipper</label>
              <input name="bol_shipper" type="text" class="input" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Invoice Goods Description</label>
              <input name="invoice_goods" type="text" class="input" />
            </div>
            <div class="form-group">
              <label>PO Goods Description</label>
              <input name="po_goods" type="text" class="input" />
            </div>
          </div>
        </div>
      </div>

      <!-- Agent 4: Transaction Monitoring (OPTIONAL) -->
      <div class="agent-card optional">
        <div class="agent-card-header">
          <span class="agent-badge">Agent 4</span>
          <span class="agent-title">Transaction Monitoring</span>
          <span class="badge badge-grey">OPTIONAL</span>
          <label class="toggle-label">
            <input type="checkbox" id="toggle-txn" name="has_transaction" />
            Add Transaction Details
          </label>
        </div>
        <div class="agent-card-body collapsible" id="txn-fields" style="display:none">
          <div class="form-row">
            <div class="form-group">
              <label>Transaction Amount</label>
              <input name="transaction_amount" type="number" class="input" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label>Transaction Corridor</label>
              <input name="transaction_corridor" type="text" class="input" placeholder="e.g. IN-CN" />
            </div>
            <div class="form-group">
              <label>Typical Transaction Amount</label>
              <input name="typical_transaction_amount" type="number" class="input" placeholder="0.00" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group checkbox-group">
              <label>
                <input name="unusual_corridor_flag" type="checkbox" />
                Unusual Corridor
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Agent 5: Regulatory Intelligence (ADVISORY) -->
      <div class="agent-card advisory">
        <div class="agent-card-header">
          <span class="agent-badge">Agent 5</span>
          <span class="agent-title">Regulatory Intelligence</span>
          <span class="badge badge-blue">ADVISORY</span>
        </div>
        <div class="agent-card-body">
          <p class="advisory-text">
            Relevant regulatory context will be attached automatically based on the countries involved.
            Does not affect the risk score.
          </p>
        </div>
      </div>

      <div class="form-actions form-actions-bottom">
        <button type="submit" class="btn-primary">Submit &amp; Evaluate Case</button>
      </div>
      <div id="case-form-result"></div>
    </form>`;
}

function bindCaseForm(el) {
  const toggleTrade = el.querySelector('#toggle-trade');
  const tradeFields = el.querySelector('#trade-doc-fields');
  toggleTrade && toggleTrade.addEventListener('change', () => {
    tradeFields.style.display = toggleTrade.checked ? '' : 'none';
  });

  const toggleTxn = el.querySelector('#toggle-txn');
  const txnFields = el.querySelector('#txn-fields');
  toggleTxn && toggleTxn.addEventListener('change', () => {
    txnFields.style.display = toggleTxn.checked ? '' : 'none';
  });

  const form = el.querySelector('#case-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const resultEl = el.querySelector('#case-form-result');
    resultEl.innerHTML = '<p class="loading">Evaluating case…</p>';

    const fd = new FormData(form);
    const payload = {};
    for (const [k, v] of fd.entries()) {
      if (v === 'on') payload[k] = true;
      else if (v === '') continue;
      else payload[k] = v;
    }

    // checkboxes not in FormData when unchecked
    ['customer_high_risk_flag', 'customer_adverse_media_flag', 'unusual_corridor_flag', 'has_trade_doc', 'has_transaction'].forEach(k => {
      if (!(k in payload)) payload[k] = false;
    });

    if (payload.customer_ubo_count) payload.customer_ubo_count = parseInt(payload.customer_ubo_count, 10);
    if (payload.invoice_amount) payload.invoice_amount = parseFloat(payload.invoice_amount);
    if (payload.po_amount) payload.po_amount = parseFloat(payload.po_amount);
    if (payload.transaction_amount) payload.transaction_amount = parseFloat(payload.transaction_amount);
    if (payload.typical_transaction_amount) payload.typical_transaction_amount = parseFloat(payload.typical_transaction_amount);

    try {
      const data = await api('/api/cases', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      resultEl.innerHTML = `<div class="success-msg">Case created: <strong>${esc(data.case.case_ref)}</strong>. Loading case detail…</div>`;
      State.currentCaseId = data.case.id;
      setTimeout(() => {
        location.hash = '#cases';
        renderPage('cases');
        // Show the new case detail after a brief delay
        setTimeout(() => openCaseDetail(data.case.id), 300);
      }, 800);
    } catch (err) {
      resultEl.innerHTML = errorHtml('Case creation failed', err.message);
    }
  });
}

// ─── 3. REVIEW QUEUE ──────────────────────────────────────────────────────────

async function renderQueue(el) {
  try {
    const data = await api('/api/queue');
    const hits = data.hits || [];

    if (!hits.length) {
      el.innerHTML = `
        <div class="view-header"><h1 class="view-title">Review Queue</h1></div>
        <div class="card"><p class="empty-msg">Queue is empty — no pending hits.</p></div>`;
      return;
    }

    const rows = hits.map(h => `
      <tr class="queue-row" data-hit-id="${h.id}" data-expanded="false">
        <td>${esc(h.screening_name)}</td>
        <td>${esc(h.matched_name)}</td>
        <td>${esc(h.list_name)}</td>
        <td>${h.score}</td>
        <td>${levelBadge(h.level)}</td>
        <td id="status-pill-${h.id}">${statusPill(h.disposition)}</td>
      </tr>
      <tr class="queue-detail-row" id="detail-${h.id}" style="display:none">
        <td colspan="6">
          <div class="queue-detail-panel">
            <button class="btn-secondary draft-btn" data-hit-id="${h.id}">Draft with AI</button>
            <textarea id="rationale-${h.id}" class="textarea" rows="4" placeholder="Enter rationale…">${esc(h.rationale || '')}</textarea>
            <div class="form-row">
              <div class="form-group">
                <label>Disposition</label>
                <select id="disp-${h.id}" class="input">
                  <option value="false_positive" ${h.disposition === 'false_positive' ? 'selected' : ''}>False Positive</option>
                  <option value="true_match"     ${h.disposition === 'true_match'     ? 'selected' : ''}>True Match</option>
                  <option value="escalated"      ${h.disposition === 'escalated'      ? 'selected' : ''}>Escalated</option>
                </select>
              </div>
              <div class="form-group">
                <button class="btn-primary save-disp-btn" data-hit-id="${h.id}">Save Disposition</button>
              </div>
            </div>
          </div>
        </td>
      </tr>`).join('');

    el.innerHTML = `
      <div class="view-header">
        <h1 class="view-title">Review Queue</h1>
        <p class="view-subtitle">${hits.length} pending hit(s)</p>
      </div>
      <div class="card">
        <table class="data-table">
          <thead><tr>
            <th>Screening Name</th><th>Matched Name</th><th>List</th>
            <th>Score</th><th>Level</th><th>Status</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;

    // Toggle expand
    el.querySelectorAll('.queue-row').forEach(row => {
      row.addEventListener('click', () => {
        const id = row.dataset.hitId;
        const detailRow = document.getElementById(`detail-${id}`);
        const expanded = row.dataset.expanded === 'true';
        row.dataset.expanded = !expanded;
        detailRow.style.display = expanded ? 'none' : '';
      });
    });

    // Draft with AI
    el.querySelectorAll('.draft-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.dataset.hitId;
        btn.textContent = 'Drafting…';
        btn.disabled = true;
        try {
          const data = await api(`/api/hits/${id}/rationale`, { method: 'POST' });
          document.getElementById(`rationale-${id}`).value = data.rationale;
        } catch (err) {
          alert('Failed to draft rationale: ' + err.message);
        } finally {
          btn.textContent = 'Draft with AI';
          btn.disabled = false;
        }
      });
    });

    // Save disposition
    el.querySelectorAll('.save-disp-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.dataset.hitId;
        const rationale = document.getElementById(`rationale-${id}`).value.trim();
        const disposition = document.getElementById(`disp-${id}`).value;
        if (!rationale) { alert('Please enter a rationale.'); return; }
        btn.textContent = 'Saving…';
        btn.disabled = true;
        try {
          await api(`/api/hits/${id}/disposition`, {
            method: 'POST',
            body: JSON.stringify({ rationale, disposition }),
          });
          document.getElementById(`status-pill-${id}`).innerHTML = statusPill(disposition);
          btn.textContent = 'Saved';
        } catch (err) {
          alert('Save failed: ' + err.message);
          btn.textContent = 'Save Disposition';
          btn.disabled = false;
        }
      });
    });
  } catch (err) {
    el.innerHTML = errorHtml('Failed to load queue', err.message);
  }
}

function statusPill(disposition) {
  if (!disposition) return '<span class="badge badge-grey">Pending</span>';
  const map = {
    false_positive: '<span class="badge badge-green">False Positive</span>',
    true_match:     '<span class="badge badge-red">True Match</span>',
    escalated:      '<span class="badge badge-red">Escalated</span>',
  };
  return map[disposition] || `<span class="badge badge-grey">${esc(disposition)}</span>`;
}

// ─── 4. CASES ─────────────────────────────────────────────────────────────────

async function renderCases(el) {
  try {
    const data = await api('/api/cases');
    const cases = data.cases || [];

    el.innerHTML = `
      <div class="view-header">
        <h1 class="view-title">Compliance Cases</h1>
        <p class="view-subtitle">${cases.length} case(s) on record</p>
      </div>
      <div id="case-list-container">
        ${renderCaseList(cases)}
      </div>
      <div id="case-detail-container" style="display:none"></div>`;

    el.querySelectorAll('.case-list-row').forEach(row => {
      row.addEventListener('click', () => openCaseDetail(row.dataset.caseId, el));
    });
  } catch (err) {
    el.innerHTML = errorHtml('Failed to load cases', err.message);
  }
}

function renderCaseList(cases) {
  if (!cases.length) return '<div class="card"><p class="empty-msg">No cases yet. Create one from New Screening.</p></div>';
  return cases.map(c => `
    <div class="case-list-row card-row ${severityClass(c.recommendation)}" data-case-id="${c.id}">
      <div class="case-row-ref"><code>${esc(c.case_ref)}</code></div>
      <div class="case-row-name">${esc(c.counterparty_name)}</div>
      <div class="case-row-customer">${esc(c.customer_legal_name)}</div>
      <div class="case-row-rec">${recommendationBadge(c.recommendation)}</div>
      <div class="case-row-status">${statusBadge(c.status)}</div>
    </div>`).join('');
}

async function openCaseDetail(caseId, elOverride) {
  const el = elOverride || document.getElementById('app');
  const listContainer = el.querySelector('#case-list-container') || document.getElementById('case-list-container');
  const detailContainer = el.querySelector('#case-detail-container') || document.getElementById('case-detail-container');

  if (!listContainer || !detailContainer) {
    // Fallback: re-render cases view then open detail
    renderPage('cases');
    setTimeout(() => openCaseDetail(caseId), 400);
    return;
  }

  listContainer.style.display = 'none';
  detailContainer.style.display = '';
  detailContainer.innerHTML = '<div class="loading">Loading case…</div>';

  try {
    const data = await api(`/api/cases/${caseId}`);
    const c = data.case;
    detailContainer.innerHTML = renderCaseDetail(c);

    detailContainer.querySelector('#back-to-list').addEventListener('click', () => {
      detailContainer.style.display = 'none';
      listContainer.style.display = '';
    });

    const toggleBtn = detailContainer.querySelector('#toggle-technical');
    const techPanel = detailContainer.querySelector('#technical-detail');
    if (toggleBtn && techPanel) {
      toggleBtn.addEventListener('click', () => {
        const vis = techPanel.style.display !== 'none';
        techPanel.style.display = vis ? 'none' : '';
        toggleBtn.textContent = vis ? 'View decision details' : 'Hide decision details';
      });
    }

    const decisionForm = detailContainer.querySelector('#decision-form');
    if (decisionForm) bindDecisionForm(decisionForm, caseId, c.recommendation);

  } catch (err) {
    detailContainer.innerHTML = errorHtml('Failed to load case', err.message);
  }
}

function renderCaseDetail(c) {
  const agentResults = c.agent_results || {};
  const levelA = c.level_a || {};
  const triggeredRules = c.triggered_rules || [];
  const decisions = c.decisions || [];
  const regUpdates = c.regulatory_updates || [];

  return `
    <div class="case-detail">
      <div class="case-detail-header">
        <button id="back-to-list" class="btn-back">← Back to Cases</button>
        <code class="case-ref-large">${esc(c.case_ref)}</code>
      </div>

      <!-- LAYER 1: Business Summary -->
      <div class="card layer-1">
        <h2 class="card-title">Business Summary</h2>

        <div class="summary-headline">
          ${statusBadge(c.status)}
          <span class="summary-cp">${esc(c.counterparty_name)}</span>
          <span class="summary-customer">for ${esc(c.customer_legal_name)}</span>
        </div>

        <div class="why-section">
          <strong>Why?</strong>
          <p>${esc(c.recommendation_source || 'Automated assessment completed.')}</p>
        </div>

        <div class="metric-grid metric-grid-sm">
          <div class="metric-card metric-blue">
            <div class="metric-value">${c.weighted_score != null ? Math.round(c.weighted_score) : '–'}</div>
            <div class="metric-label">Overall Risk Score</div>
          </div>
          <div class="metric-card metric-green">
            <div class="metric-value">${Object.keys(agentResults).length}</div>
            <div class="metric-label">Checks Completed</div>
          </div>
        </div>

        <div class="recommended-action">
          <span class="rec-label">Recommended Action:</span>
          ${recommendationBadge(c.recommendation)}
        </div>

        <div class="tradepe-banner">
          TradePe Recommends &rarr; Human Officer Decides
        </div>

        <button id="toggle-technical" class="btn-secondary btn-sm">View decision details</button>
      </div>

      <!-- LAYER 2: Technical Detail -->
      <div id="technical-detail" class="card layer-2" style="display:none">
        <h2 class="card-title">Full Technical Detail</h2>

        ${renderLevelAWeights(levelA)}
        ${renderAgentResults(agentResults)}
        ${renderTriggeredRules(triggeredRules)}
        ${renderDomainMetrics(c)}
      </div>

      <!-- Officer Decision Form -->
      <div class="card">
        <h2 class="card-title">Officer Decision</h2>
        <form id="decision-form">
          <div class="form-group">
            <label>Action Taken</label>
            <select name="action_taken" class="input" required>
              <option value="">— Select —</option>
              <option value="approve">Approve</option>
              <option value="hold">Hold</option>
              <option value="escalate">Escalate</option>
              <option value="reject">Reject</option>
            </select>
          </div>
          <div class="form-group">
            <label>Rationale <span id="rationale-required-note" class="subtle">(required if overriding recommendation)</span></label>
            <textarea name="rationale" class="textarea" rows="3" placeholder="Enter your reasoning…"></textarea>
          </div>
          <button type="submit" class="btn-primary">Submit Decision</button>
          <div id="decision-result"></div>
        </form>
      </div>

      <!-- Decision History -->
      ${renderDecisionHistory(decisions)}

      <!-- Regulatory Context -->
      ${renderRegulatoryContext(regUpdates)}
    </div>`;
}

function renderLevelAWeights(levelA) {
  const weights = levelA.weights || {};
  if (!Object.keys(weights).length) return '';
  const rows = Object.entries(weights).map(([k, v]) => `
    <tr><td>${esc(k)}</td><td>${v}</td></tr>`).join('');
  return `
    <div class="tech-section">
      <h3 class="tech-title">Level A — Weights Used</h3>
      <table class="data-table">
        <thead><tr><th>Agent</th><th>Weight</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function renderAgentResults(agentResults) {
  if (!Object.keys(agentResults).length) return '';
  const cards = Object.entries(agentResults).map(([agent, r]) => {
    const findings = r.findings || [];
    const findingsList = findings.length
      ? `<ul class="findings-list">${findings.map(f => `<li>${esc(f)}</li>`).join('')}</ul>`
      : '<p class="subtle">No findings.</p>';
    return `
      <div class="agent-result-card">
        <div class="agent-result-header">
          <strong>${esc(agent)}</strong>
          ${outcomeBadge(r.outcome)}
          <span class="subtle">Score: ${r.risk_score != null ? r.risk_score : '–'}</span>
        </div>
        ${findingsList}
      </div>`;
  }).join('');
  return `
    <div class="tech-section">
      <h3 class="tech-title">Agent Results</h3>
      ${cards}
    </div>`;
}

function renderTriggeredRules(rules) {
  if (!rules || !rules.length) return `
    <div class="tech-section">
      <h3 class="tech-title">Level B — Triggered Rules</h3>
      <p class="subtle">No hard-stop rules triggered.</p>
    </div>`;
  const items = rules.map(r => `<li class="rule-item">${esc(r)}</li>`).join('');
  return `
    <div class="tech-section">
      <h3 class="tech-title">Level B — Triggered Rules</h3>
      <ul class="rule-list">${items}</ul>
    </div>`;
}

function renderDomainMetrics(c) {
  const metrics = [];
  if (c.customer_kyc_status) metrics.push(['KYC Status', c.customer_kyc_status]);
  if (c.counterparty_country) metrics.push(['Counterparty Country', c.counterparty_country]);
  if (c.customer_country) metrics.push(['Customer Country', c.customer_country]);
  if (c.transaction_corridor) metrics.push(['Transaction Corridor', c.transaction_corridor]);
  if (c.transaction_amount) metrics.push(['Transaction Amount', c.transaction_amount]);
  if (!metrics.length) return '';
  const rows = metrics.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(String(v))}</td></tr>`).join('');
  return `
    <div class="tech-section">
      <h3 class="tech-title">Domain Metrics</h3>
      <table class="data-table">
        <thead><tr><th>Field</th><th>Value</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function renderDecisionHistory(decisions) {
  if (!decisions || !decisions.length) return '';
  const rows = decisions.map(d => `
    <tr>
      <td>${formatDate(d.created_at)}</td>
      <td>${esc(d.actor)}</td>
      <td>${esc(d.action_taken)}</td>
      <td>${d.is_override ? '<span class="badge badge-yellow">Override</span>' : '–'}</td>
      <td>${esc(d.rationale || '–')}</td>
    </tr>`).join('');
  return `
    <div class="card">
      <h2 class="card-title">Decision History</h2>
      <table class="data-table">
        <thead><tr>
          <th>Date</th><th>Officer</th><th>Action</th><th>Override</th><th>Rationale</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function renderRegulatoryContext(updates) {
  if (!updates || !updates.length) return '';
  const items = updates.map(u => `
    <div class="reg-context-item">
      <strong>${esc(u.source)}</strong>: ${esc(u.title)}
      <p class="subtle">${esc(u.summary)}</p>
    </div>`).join('');
  return `
    <div class="card">
      <h2 class="card-title">Regulatory Context</h2>
      ${items}
    </div>`;
}

function bindDecisionForm(form, caseId, recommendation) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const resultEl = form.querySelector('#decision-result');
    const action_taken = form.querySelector('[name="action_taken"]').value;
    const rationale = form.querySelector('[name="rationale"]').value.trim();
    if (!action_taken) { alert('Please select an action.'); return; }

    resultEl.innerHTML = '<p class="loading">Submitting…</p>';
    try {
      const data = await api(`/api/cases/${caseId}/decision`, {
        method: 'POST',
        body: JSON.stringify({ action_taken, rationale }),
      });
      resultEl.innerHTML = `<div class="success-msg">Decision recorded: <strong>${esc(data.action_taken)}</strong>${data.is_override ? ' (override)' : ''}.</div>`;
    } catch (err) {
      resultEl.innerHTML = errorHtml('Decision failed', err.message);
    }
  });
}

// ─── 5. REGULATORY UPDATES ────────────────────────────────────────────────────

async function renderRegulatory(el) {
  try {
    const data = await api('/api/regulatory-updates');
    const updates = data.updates || [];

    const cards = updates.map(u => `
      <div class="card reg-card">
        <div class="reg-card-header">
          <span class="reg-source">${esc(u.source)}</span>
          ${impactBadge(u.impact)}
          ${u.action_required ? '<span class="badge badge-red">Action Required</span>' : ''}
        </div>
        <h3 class="reg-title">${esc(u.title)}</h3>
        <p class="reg-summary">${esc(u.summary)}</p>
        ${u.countries && u.countries.length ? `<p class="reg-countries subtle">Countries: ${u.countries.join(', ')}</p>` : ''}
      </div>`).join('');

    el.innerHTML = `
      <div class="view-header">
        <h1 class="view-title">Regulatory Updates</h1>
        <p class="view-subtitle">${updates.length} update(s)</p>
      </div>
      ${cards}
      <div class="disclaimer-box">
        Disclaimer: Synthetic demo data — not real regulatory text or live monitoring. Illustrative only.
      </div>`;
  } catch (err) {
    el.innerHTML = errorHtml('Failed to load regulatory updates', err.message);
  }
}

function impactBadge(impact) {
  const map = {
    high:   ['badge badge-red',    'High Impact'],
    medium: ['badge badge-yellow', 'Medium Impact'],
    low:    ['badge badge-green',  'Low Impact'],
  };
  const [cls, label] = map[(impact || '').toLowerCase()] || ['badge badge-grey', impact || '–'];
  return `<span class="${cls}">${label}</span>`;
}

// ─── 6. AGENTS ────────────────────────────────────────────────────────────────

function renderAgents(el) {
  el.innerHTML = `
    <div class="view-header">
      <h1 class="view-title">Compliance Agents</h1>
      <p class="view-subtitle">Architecture overview of TradePe's AI compliance network</p>
    </div>

    <section class="card">
      <h2 class="card-title">Risk Assessment Agents</h2>
      <p>These agents directly contribute to the weighted risk score and can trigger hard-stop overrides.</p>

      <div class="agent-arch-card required">
        <div class="agent-arch-header">
          <span class="agent-badge">Agent 1</span>
          <strong>Sanctions &amp; Watchlist Screening</strong>
          <span class="badge badge-red">REQUIRED</span>
        </div>
        <p>Screens counterparties against OFAC, UN, EU, and PEP watchlists using fuzzy name matching. Returns a match score (0–100) and hit level (clear / review / high / critical). Any hit above the threshold is routed to the review queue.</p>
      </div>

      <div class="agent-arch-card required">
        <div class="agent-arch-header">
          <span class="agent-badge">Agent 2</span>
          <strong>Customer Risk / KYC</strong>
          <span class="badge badge-red">REQUIRED</span>
        </div>
        <p>Evaluates the customer's KYC status, IEC/GST/PAN registration, UBO count, high-risk flag, and adverse media flag. Produces a customer risk sub-score that feeds into the Level A weighted composite.</p>
      </div>

      <div class="agent-arch-card optional">
        <div class="agent-arch-header">
          <span class="agent-badge">Agent 3</span>
          <strong>Trade Document Review</strong>
          <span class="badge badge-grey">OPTIONAL</span>
        </div>
        <p>Cross-checks invoice, purchase order, and bill of lading for consistency — seller/buyer names, goods descriptions, and amount alignment. Inconsistencies raise the document risk sub-score.</p>
      </div>

      <div class="agent-arch-card optional">
        <div class="agent-arch-header">
          <span class="agent-badge">Agent 4</span>
          <strong>Transaction Monitoring</strong>
          <span class="badge badge-grey">OPTIONAL</span>
        </div>
        <p>Analyses transaction amount vs. typical value, flags unusual trade corridors, and detects structuring or velocity anomalies. Contributes a transaction risk sub-score.</p>
      </div>
    </section>

    <section class="card">
      <h2 class="card-title">Advisory Capabilities</h2>

      <div class="agent-arch-card advisory">
        <div class="agent-arch-header">
          <span class="agent-badge">Agent 5</span>
          <strong>Regulatory Intelligence</strong>
          <span class="badge badge-blue">ADVISORY</span>
        </div>
        <p>Automatically attaches relevant regulatory context (sanctions updates, export-control notices, AML advisories) based on the countries detected in the case. Does not affect the risk score — purely informational for the reviewing compliance officer.</p>
      </div>
    </section>

    <section class="card">
      <h2 class="card-title">Scoring Architecture</h2>

      <h3 class="tech-title">Level A — Weighted Composite Score</h3>
      <p>Each active agent contributes a sub-score (0–100). The final risk score is the weighted average of all active agents. Weights are configurable per deployment. Outcomes above the review threshold route to manual queue; above the high threshold trigger ESCALATE recommendation.</p>

      <h3 class="tech-title">Level B — Hard-Stop Rules</h3>
      <p>A set of deterministic rules that override Level A scoring regardless of numeric outcome. Examples: OFAC critical match, expired KYC, confirmed PEP, or sanctions-listed country. Any triggered rule immediately escalates the recommendation.</p>

      <div class="tradepe-banner">
        TradePe Recommends. Human Compliance Officer Decides.
      </div>
    </section>`;
}

// ─── 7. AUDIT TRAIL ───────────────────────────────────────────────────────────

async function renderAudit(el) {
  try {
    const data = await api('/api/audit');
    const events = data.events || [];

    const actionLabels = {
      'screening.created':    'Screening Created',
      'hit.disposition':      'Hit Disposition Set',
      'rationale.draft':      'Rationale Drafted (AI)',
      'case.created':         'Case Created',
      'case.decision':        'Officer Decision Recorded',
      'case.evaluated':       'Case Evaluated',
    };

    const rows = events.map(ev => `
      <tr>
        <td>${formatDate(ev.created_at)}</td>
        <td>${esc(ev.actor)}</td>
        <td>${esc(actionLabels[ev.action] || ev.action)}</td>
        <td class="subtle">${esc(ev.detail || '–')}</td>
      </tr>`).join('');

    el.innerHTML = `
      <div class="view-header">
        <h1 class="view-title">Audit Trail</h1>
        <p class="view-subtitle">${events.length} event(s) recorded</p>
      </div>
      <div class="card">
        ${events.length
          ? `<table class="data-table">
              <thead><tr>
                <th>Timestamp</th><th>Actor</th><th>Action</th><th>Detail</th>
              </tr></thead>
              <tbody>${rows}</tbody>
            </table>`
          : '<p class="empty-msg">No audit events yet.</p>'}
      </div>`;
  } catch (err) {
    el.innerHTML = errorHtml('Failed to load audit trail', err.message);
  }
}

// ─── 8. HELP MODAL ────────────────────────────────────────────────────────────

function buildHelpModal() {
  const modal = document.createElement('div');
  modal.id = 'help-modal';
  modal.className = 'modal-overlay';
  modal.style.display = 'none';
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h2>Help &amp; Reference</h2>
        <button class="modal-close" aria-label="Close help">&times;</button>
      </div>
      <div class="modal-body">
        <h3>Getting Started</h3>
        <p>Use <strong>New Screening</strong> to quickly screen a name against watchlists, or create a full compliance case. Use <strong>Review Queue</strong> to disposition pending hits. Use <strong>Cases</strong> to view all evaluated cases and record officer decisions.</p>

        <h3>Understanding TradePe</h3>
        <p>TradePe is a multi-agent compliance copilot for trade finance. It does <em>not</em> make final compliance decisions — it provides a structured assessment for human compliance officers to review and act on. The system recommendation is always labelled "TradePe Recommends"; final authority rests with the officer.</p>
        <ul>
          <li><strong>APPROVE</strong> — Low risk, no watchlist hits, clean KYC</li>
          <li><strong>MANUAL_REVIEW</strong> — Moderate risk, officer review recommended</li>
          <li><strong>ESCALATE</strong> — High risk or hard-stop rule triggered</li>
        </ul>

        <h3>Demo &amp; Methodology</h3>
        <p>This is a demonstration environment. Watchlist data, case data, regulatory updates, and audit events are all synthetic or illustrative. No real watchlist data is used. Name matching uses fuzzy string similarity (not AI embeddings in the demo). Scores are calculated from heuristic rules and are not calibrated for production use.</p>

        <div class="disclaimer-box">
          Synthetic demo data — not real watchlist data, regulatory text, or live monitoring. For demonstration purposes only.
        </div>
      </div>
    </div>`;
  document.body.appendChild(modal);

  modal.querySelector('.modal-close').addEventListener('click', () => { modal.style.display = 'none'; });
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });
  return modal;
}

// ─── UTILITY HTML ─────────────────────────────────────────────────────────────

function errorHtml(title, detail) {
  return `
    <div class="error-box">
      <strong>${esc(title)}</strong>
      ${detail ? `<p>${esc(detail)}</p>` : ''}
    </div>`;
}

// ─── NAVIGATION BINDINGS ──────────────────────────────────────────────────────

function bindNav() {
  const viewMap = {
    'dashboard':          'dashboard',
    'new-screening':      'screening',
    'review-queue':       'queue',
    'cases':              'cases',
    'regulatory-updates': 'regulatory',
    'agents':             'agents',
    'audit-trail':        'audit',
  };

  document.querySelectorAll('.nav-link[data-view]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const view = viewMap[link.dataset.view] || link.dataset.view;
      const hashMap = {
        dashboard:  '#dashboard',
        screening:  '#screening',
        queue:      '#queue',
        cases:      '#cases',
        regulatory: '#regulatory',
        agents:     '#agents',
        audit:      '#audit',
      };
      location.hash = hashMap[view] || `#${view}`;
      renderPage(view);
    });
  });

  // Dashboard case row clicks (delegated)
  document.getElementById('app').addEventListener('click', (e) => {
    const row = e.target.closest('.clickable-row[data-case-id]');
    if (row) {
      location.hash = '#cases';
      renderPage('cases');
      setTimeout(() => openCaseDetail(row.dataset.caseId), 300);
    }
  });
}

function bindHelp() {
  const helpModal = buildHelpModal();
  document.querySelector('.btn-help').addEventListener('click', () => {
    helpModal.style.display = 'flex';
  });
}

// ─── BOOT ─────────────────────────────────────────────────────────────────────

function init() {
  bindNav();
  bindHelp();

  window.addEventListener('hashchange', () => {
    const view = getViewFromHash();
    if (view !== State.currentView) renderPage(view);
  });

  renderPage(getViewFromHash());
}

document.addEventListener('DOMContentLoaded', init);
