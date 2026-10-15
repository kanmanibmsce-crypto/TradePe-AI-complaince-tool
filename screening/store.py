import sqlite3
import time
import os
from screening.config import DB_PATH, DEMO_ANALYST


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db(reset=False):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if os.path.dirname(DB_PATH) else None
    conn = _conn()
    if reset:
        conn.execute('DROP TABLE IF EXISTS audit')
        conn.execute('DROP TABLE IF EXISTS hits')
        conn.execute('DROP TABLE IF EXISTS screenings')
        conn.execute('DROP TABLE IF EXISTS cases')
        conn.execute('DROP TABLE IF EXISTS case_decisions')
        conn.execute('DROP TABLE IF EXISTS trade_documents')
        conn.execute('DROP TABLE IF EXISTS transactions')
    conn.execute('''CREATE TABLE IF NOT EXISTS screenings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, entity_type TEXT, country TEXT,
        top_score INTEGER, top_level TEXT,
        hit_count INTEGER, created_at REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS hits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        screening_id INTEGER, uid TEXT, matched_name TEXT,
        list_name TEXT, score INTEGER, level TEXT,
        status TEXT DEFAULT "pending",
        reviewed_by TEXT, reviewed_at REAL,
        rationale TEXT, disposition TEXT,
        created_at REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, actor TEXT, action TEXT, detail TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_ref TEXT UNIQUE,
        counterparty_name TEXT, counterparty_country TEXT,
        entity_type TEXT,
        customer_legal_name TEXT, customer_iec TEXT, customer_gst_pan TEXT,
        customer_country TEXT, customer_kyc_status TEXT,
        customer_ubo_count INTEGER, customer_high_risk_flag INTEGER,
        customer_adverse_media_flag INTEGER,
        has_trade_doc INTEGER DEFAULT 0,
        invoice_number TEXT, po_number TEXT, bol_number TEXT,
        invoice_amount REAL, po_amount REAL,
        invoice_seller TEXT, po_buyer TEXT, bol_shipper TEXT,
        invoice_goods TEXT, po_goods TEXT,
        has_transaction INTEGER DEFAULT 0,
        transaction_amount REAL, transaction_corridor TEXT,
        unusual_corridor_flag INTEGER DEFAULT 0,
        typical_transaction_amount REAL,
        agent_results_json TEXT,
        recommendation TEXT, recommendation_source TEXT,
        weighted_score INTEGER,
        status TEXT DEFAULT "pending",
        created_at REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS case_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER, action_taken TEXT, rationale TEXT,
        is_override INTEGER, actor TEXT, created_at REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS trade_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER, invoice_number TEXT, seller_name TEXT,
        created_at REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER, amount REAL, corridor TEXT,
        unusual_corridor_flag INTEGER, typical_amount REAL,
        created_at REAL)''')
    conn.commit()
    conn.close()


def audit_log(actor, action, detail):
    conn = _conn()
    conn.execute('INSERT INTO audit (ts, actor, action, detail) VALUES (?,?,?,?)',
                 (time.time(), actor, action, detail))
    conn.commit()
    conn.close()


def save_screening(name, entity_type, country, matches):
    conn = _conn()
    top_score = matches[0]['score'] if matches else 0
    top_level = matches[0]['level'] if matches else 'clear'
    hit_count = len([m for m in matches if m['level'] != 'clear'])
    cur = conn.execute(
        'INSERT INTO screenings (name,entity_type,country,top_score,top_level,hit_count,created_at) VALUES (?,?,?,?,?,?,?)',
        (name, entity_type, country, top_score, top_level, hit_count, time.time()))
    sid = cur.lastrowid
    for m in matches:
        conn.execute(
            'INSERT INTO hits (screening_id,uid,matched_name,list_name,score,level,status,created_at) VALUES (?,?,?,?,?,?,?,?)',
            (sid, m['uid'], m['matched_name'], m['list_name'], m['score'], m['level'], 'pending', time.time()))
    conn.commit()
    audit_log(DEMO_ANALYST, 'screening.run', f'Screened: {name} — {top_level} ({top_score})')
    conn.close()
    return sid


def get_queue():
    conn = _conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT h.*,s.name as screening_name FROM hits h JOIN screenings s ON h.screening_id=s.id WHERE h.level IN ("review","high") AND h.status="pending" ORDER BY h.score DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hit(hit_id):
    conn = _conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT h.*,s.name as screening_name FROM hits h JOIN screenings s ON h.screening_id=s.id WHERE h.id=?', (hit_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def set_hit_disposition(hit_id, disposition, rationale, actor):
    conn = _conn()
    conn.execute('UPDATE hits SET status=?,disposition=?,rationale=?,reviewed_by=?,reviewed_at=? WHERE id=?',
                 (disposition, disposition, rationale, actor, time.time(), hit_id))
    conn.commit()
    audit_log(actor, 'hit.disposition', f'Hit #{hit_id} → {disposition}')
    conn.close()


def get_audit(limit=200):
    conn = _conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM audit ORDER BY ts DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = _conn()
    total = conn.execute('SELECT COUNT(*) FROM screenings').fetchone()[0]
    cleared = conn.execute("SELECT COUNT(*) FROM screenings WHERE top_level='clear'").fetchone()[0]
    review = conn.execute("SELECT COUNT(*) FROM screenings WHERE top_level='review'").fetchone()[0]
    high = conn.execute("SELECT COUNT(*) FROM screenings WHERE top_level='high'").fetchone()[0]
    conn.close()
    return {'total': total, 'cleared': cleared, 'review': review, 'high': high}


def save_case(data):
    import json
    conn = _conn()
    cur = conn.execute('''INSERT INTO cases (
        case_ref, counterparty_name, counterparty_country, entity_type,
        customer_legal_name, customer_iec, customer_gst_pan, customer_country,
        customer_kyc_status, customer_ubo_count, customer_high_risk_flag,
        customer_adverse_media_flag,
        has_trade_doc, invoice_number, po_number, bol_number,
        invoice_amount, po_amount, invoice_seller, po_buyer, bol_shipper,
        invoice_goods, po_goods,
        has_transaction, transaction_amount, transaction_corridor,
        unusual_corridor_flag, typical_transaction_amount,
        agent_results_json, recommendation, recommendation_source, weighted_score,
        status, created_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (data.get('case_ref'), data.get('counterparty_name'), data.get('counterparty_country'),
         data.get('entity_type', 'entity'), data.get('customer_legal_name'), data.get('customer_iec'),
         data.get('customer_gst_pan'), data.get('customer_country'), data.get('customer_kyc_status', 'verified'),
         data.get('customer_ubo_count', 1), int(data.get('customer_high_risk_flag', False)),
         int(data.get('customer_adverse_media_flag', False)),
         int(data.get('has_trade_doc', False)),
         data.get('invoice_number'), data.get('po_number'), data.get('bol_number'),
         data.get('invoice_amount'), data.get('po_amount'),
         data.get('invoice_seller'), data.get('po_buyer'), data.get('bol_shipper'),
         data.get('invoice_goods'), data.get('po_goods'),
         int(data.get('has_transaction', False)),
         data.get('transaction_amount'), data.get('transaction_corridor'),
         int(data.get('unusual_corridor_flag', False)), data.get('typical_transaction_amount'),
         json.dumps(data.get('agent_results', {})),
         data.get('recommendation'), data.get('recommendation_source'), data.get('weighted_score'),
         'pending', time.time()))
    case_id = cur.lastrowid
    conn.commit()
    audit_log(DEMO_ANALYST, 'case.created', f'Case #{case_id} ({data.get("case_ref","")}) created')
    conn.close()
    return case_id


def get_cases(limit=50):
    import json
    conn = _conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM cases ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d['agent_results'] = json.loads(d.get('agent_results_json') or '{}')
        except Exception:
            d['agent_results'] = {}
        result.append(d)
    conn.close()
    return result


def get_case(case_id):
    import json
    conn = _conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT * FROM cases WHERE id=?', (case_id,)).fetchone()
    if not row:
        conn.close()
        return None
    d = dict(row)
    try:
        d['agent_results'] = json.loads(d.get('agent_results_json') or '{}')
    except Exception:
        d['agent_results'] = {}
    decisions = conn.execute('SELECT * FROM case_decisions WHERE case_id=? ORDER BY created_at DESC', (case_id,)).fetchall()
    d['decisions'] = [dict(dec) for dec in decisions]
    conn.close()
    return d


def record_case_decision(case_id, action_taken, rationale, is_override, actor):
    conn = _conn()
    conn.execute('INSERT INTO case_decisions (case_id,action_taken,rationale,is_override,actor,created_at) VALUES (?,?,?,?,?,?)',
                 (case_id, action_taken, rationale, int(is_override), actor, time.time()))
    conn.execute("UPDATE cases SET status=? WHERE id=?", (action_taken, case_id))
    conn.commit()
    audit_log(actor, 'case.decision', f'Case #{case_id}: {action_taken} (override={is_override})')
    conn.close()


def get_prior_invoices():
    conn = _conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT invoice_number, seller_name FROM trade_documents').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_trade_document_record(case_id, invoice_number, seller_name):
    conn = _conn()
    conn.execute('INSERT INTO trade_documents (case_id,invoice_number,seller_name,created_at) VALUES (?,?,?,?)',
                 (case_id, invoice_number, seller_name, time.time()))
    conn.commit()
    conn.close()
