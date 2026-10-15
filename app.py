import sys
import json
import time
import uuid
from flask import Flask, render_template, request, jsonify

from screening.store import (
    init_db, save_screening, get_queue, get_hit,
    set_hit_disposition, get_audit, get_stats,
    save_case, get_cases, get_case, record_case_decision,
    save_trade_document_record, audit_log,
)
from screening.matcher import Watchlist
from screening.ai_rationale import draft as draft_rationale
from screening.contract_adapter import run as run_sanctions_check
from orchestration.case_runner import evaluate_case
from regulatory_intelligence.data import get_all_updates, get_updates_for_countries
from screening.config import DEMO_ANALYST, SCORE_REVIEW, SCORE_HIGH

app = Flask(__name__)
_watchlist = None

init_db()


def get_watchlist():
    global _watchlist
    if _watchlist is None:
        _watchlist = Watchlist()
    return _watchlist


DECISION_VOCABULARY = {'approve', 'hold', 'escalate', 'reject'}
RECOMMENDATION_VOCABULARY = {'APPROVE', 'MANUAL_REVIEW', 'ESCALATE'}


def _is_override(action_taken, recommendation):
    mapping = {'approve': 'APPROVE', 'escalate': 'ESCALATE'}
    system_rec = recommendation or 'MANUAL_REVIEW'
    if action_taken == 'approve' and system_rec == 'APPROVE':
        return False
    if action_taken == 'escalate' and system_rec == 'ESCALATE':
        return False
    if action_taken in ('hold', 'reject'):
        return True
    if action_taken == 'approve' and system_rec != 'APPROVE':
        return True
    if action_taken == 'escalate' and system_rec != 'ESCALATE':
        return True
    return False


@app.route('/')
def index():
    wl = get_watchlist()
    return render_template('index.html', watchlist_count=wl.count,
                           score_review=SCORE_REVIEW, score_high=SCORE_HIGH)


# ── Screening ──────────────────────────────────────────────────────────────

@app.route('/api/screen', methods=['POST'])
def api_screen():
    data = request.get_json(force=True)
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400
    entity_type = data.get('entity_type', 'entity')
    country = data.get('country', '')
    wl = get_watchlist()
    matches = wl.screen(name, entity_type, country)
    sid = save_screening(name, entity_type, country, matches)
    result_matches = []
    for m in matches:
        result_matches.append({
            'uid': m['uid'],
            'matched_name': m['matched_name'],
            'list_name': m['list_name'],
            'score': m['score'],
            'level': m['level'],
        })
    top_level = matches[0]['level'] if matches else 'clear'
    top_score = matches[0]['score'] if matches else 0
    return jsonify({
        'screening_id': sid,
        'name': name,
        'top_level': top_level,
        'top_score': top_score,
        'matches': result_matches,
        'total': len(result_matches),
    })


@app.route('/api/demo-batch', methods=['POST'])
def api_demo_batch():
    import os
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_payments.json')
    with open(data_path) as f:
        payments = json.load(f)
    results = []
    wl = get_watchlist()
    for p in payments:
        matches = wl.screen(p['beneficiary'], 'entity', p.get('country', ''))
        sid = save_screening(p['beneficiary'], 'entity', p.get('country', ''), matches)
        top_level = matches[0]['level'] if matches else 'clear'
        top_score = matches[0]['score'] if matches else 0
        results.append({
            'txn_id': p['txn_id'],
            'name': p['beneficiary'],
            'top_level': top_level,
            'top_score': top_score,
            'match_count': len([m for m in matches if m['level'] != 'clear']),
        })
    return jsonify({'results': results})


@app.route('/api/queue', methods=['GET'])
def api_queue():
    return jsonify({'hits': get_queue()})


@app.route('/api/hits/<int:hit_id>/rationale', methods=['POST'])
def api_draft_rationale(hit_id):
    hit = get_hit(hit_id)
    if not hit:
        return jsonify({'error': 'hit not found'}), 404
    text = draft_rationale(hit)
    audit_log(DEMO_ANALYST, 'rationale.draft', f'Rationale drafted for hit #{hit_id}')
    return jsonify({'rationale': text})


@app.route('/api/hits/<int:hit_id>/disposition', methods=['POST'])
def api_disposition(hit_id):
    data = request.get_json(force=True)
    disposition = data.get('disposition', '').strip()
    rationale = (data.get('rationale') or '').strip()
    if not rationale:
        return jsonify({'error': 'rationale is required'}), 400
    if disposition not in ('false_positive', 'true_match', 'escalated'):
        return jsonify({'error': 'invalid disposition'}), 400
    hit = get_hit(hit_id)
    if not hit:
        return jsonify({'error': 'hit not found'}), 404
    set_hit_disposition(hit_id, disposition, rationale, DEMO_ANALYST)
    return jsonify({'ok': True, 'hit_id': hit_id, 'disposition': disposition})


# ── Cases ──────────────────────────────────────────────────────────────────

@app.route('/api/cases', methods=['GET'])
def api_list_cases():
    return jsonify({'cases': get_cases()})


@app.route('/api/cases', methods=['POST'])
def api_create_case():
    data = request.get_json(force=True)
    required = ['counterparty_name', 'customer_legal_name', 'customer_country']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    data['case_ref'] = 'CASE-' + str(uuid.uuid4())[:8].upper()
    result = evaluate_case(data)
    data['agent_results'] = result['agent_results']
    data['recommendation'] = result['recommendation']
    data['recommendation_source'] = result['recommendation_source']
    data['weighted_score'] = result['weighted_score']
    case_id = save_case(data)
    if data.get('has_trade_doc') and data.get('invoice_number'):
        save_trade_document_record(case_id, data['invoice_number'], data.get('invoice_seller', ''))
    case = get_case(case_id)
    case['triggered_rules'] = result['triggered_rules']
    case['level_a'] = result['level_a']
    case['regulatory_updates'] = result['regulatory_updates']
    return jsonify({'case': case}), 201


@app.route('/api/cases/<int:case_id>', methods=['GET'])
def api_get_case(case_id):
    case = get_case(case_id)
    if not case:
        return jsonify({'error': 'case not found'}), 404
    result = evaluate_case(case)
    case['triggered_rules'] = result['triggered_rules']
    case['level_a'] = result['level_a']
    countries = [c for c in [case.get('customer_country'), case.get('counterparty_country')] if c]
    case['regulatory_updates'] = get_updates_for_countries(countries)
    return jsonify({'case': case})


@app.route('/api/cases/<int:case_id>/decision', methods=['POST'])
def api_case_decision(case_id):
    case = get_case(case_id)
    if not case:
        return jsonify({'error': 'case not found'}), 404
    data = request.get_json(force=True)
    action_taken = (data.get('action_taken') or '').strip().lower()
    rationale = (data.get('rationale') or '').strip()
    if action_taken not in DECISION_VOCABULARY:
        return jsonify({'error': f'action_taken must be one of: {", ".join(DECISION_VOCABULARY)}'}), 400
    is_override = _is_override(action_taken, case.get('recommendation'))
    if is_override and not rationale:
        return jsonify({'error': 'rationale is required when overriding the system recommendation'}), 400
    record_case_decision(case_id, action_taken, rationale, is_override, DEMO_ANALYST)
    return jsonify({'ok': True, 'case_id': case_id, 'action_taken': action_taken, 'is_override': is_override})


# ── Dashboard / Stats ──────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    cases = get_cases(limit=100)
    total = len(cases)
    pending = sum(1 for c in cases if c.get('status') == 'pending')
    approved = sum(1 for c in cases if c.get('status') == 'approve')
    escalated = sum(1 for c in cases if c.get('status') in ('escalate', 'escalated'))
    needs_review = sum(1 for c in cases if c.get('recommendation') in ('MANUAL_REVIEW', 'ESCALATE') and c.get('status') == 'pending')
    auto_cleared = sum(1 for c in cases if c.get('recommendation') == 'APPROVE' and c.get('status') == 'pending')
    screening_stats = get_stats()
    recent_cases = cases[:5]
    attention_cases = [c for c in cases if c.get('recommendation') in ('MANUAL_REVIEW', 'ESCALATE') and c.get('status') == 'pending'][:5]
    reg_updates = get_all_updates()[:3]
    return jsonify({
        'total_cases': total,
        'needs_review': needs_review,
        'auto_cleared': auto_cleared,
        'escalated': escalated,
        'approved': approved,
        'screening_stats': screening_stats,
        'recent_cases': recent_cases,
        'attention_cases': attention_cases,
        'regulatory_updates': reg_updates,
    })


# ── Audit ──────────────────────────────────────────────────────────────────

@app.route('/api/audit', methods=['GET'])
def api_audit():
    return jsonify({'events': get_audit()})


# ── Regulatory Updates ─────────────────────────────────────────────────────

@app.route('/api/regulatory-updates', methods=['GET'])
def api_regulatory_updates():
    return jsonify({'updates': get_all_updates()})


@app.route('/api/regulatory-updates/case/<int:case_id>', methods=['GET'])
def api_regulatory_updates_case(case_id):
    case = get_case(case_id)
    if not case:
        return jsonify({'error': 'case not found'}), 404
    countries = [c for c in [case.get('customer_country'), case.get('counterparty_country')] if c]
    return jsonify({'updates': get_updates_for_countries(countries), 'case_id': case_id})


# ── Stats ──────────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def api_stats():
    return jsonify(get_stats())


if __name__ == '__main__':
    reset = '--reset' in sys.argv
    init_db(reset=reset)
    if reset:
        print('Database reset complete.')
    app.run(host='0.0.0.0', port=8000, debug=True)
