def run(doc_data, prior_invoices=None):
    prior_invoices = prior_invoices or []
    score = 0
    findings = []
    warnings = []

    invoice_present = bool(doc_data.get('invoice_number'))

    if not invoice_present:
        return {
            'agent_id': 'trade_document',
            'agent_name': 'Trade Document Agent',
            'execution_status': 'ok',
            'outcome': 'FAIL',
            'risk_score': 100,
            'domain_metrics': {
                'commercial_invoice_present': False,
                'po_present': bool(doc_data.get('po_number')),
                'bol_present': bool(doc_data.get('bol_number')),
            },
            'findings': ['MANDATORY: No Commercial Invoice provided — automatic FAIL'],
            'evidence': [],
            'confidence': 1.0,
            'summary': 'Commercial Invoice is mandatory and was not provided.',
            'requires_human_review': True,
            'warnings_or_errors': [],
        }

    # Duplicate detection (Tier-1: exact invoice_number + seller_name)
    invoice_number = doc_data.get('invoice_number', '').strip()
    seller_name = (doc_data.get('invoice_seller') or '').strip().lower()
    for prior in prior_invoices:
        if (prior.get('invoice_number', '').strip() == invoice_number and
                (prior.get('seller_name') or '').strip().lower() == seller_name):
            score += 45
            findings.append(f'DUPLICATE: Invoice {invoice_number} from {seller_name} matches a prior case (+45 points, FAIL override)')
            dup_override = True
            break
    else:
        dup_override = False

    # Amount variance (Invoice vs PO)
    invoice_amount = doc_data.get('invoice_amount')
    po_amount = doc_data.get('po_amount')
    po_present = bool(doc_data.get('po_number'))
    bol_present = bool(doc_data.get('bol_number'))

    if invoice_amount and po_amount and po_amount > 0:
        ratio = abs(invoice_amount - po_amount) / po_amount
        if ratio > 0.10:
            score += 25
            findings.append(f'Amount variance >10% between Invoice and PO (+25 points)')
        elif ratio > 0.05:
            score += 12
            findings.append(f'Amount variance 5-10% between Invoice and PO (+12 points)')

    # Quantity/goods description checks
    invoice_goods = (doc_data.get('invoice_goods') or '').strip().lower()
    po_goods = (doc_data.get('po_goods') or '').strip().lower()
    if invoice_goods and po_goods and invoice_goods != po_goods:
        score += 10
        findings.append('Goods description mismatch between Invoice and PO (+10 points)')

    # Buyer/seller party name check
    invoice_seller = (doc_data.get('invoice_seller') or '').strip().lower()
    po_buyer = (doc_data.get('po_buyer') or '').strip().lower()
    bol_shipper = (doc_data.get('bol_shipper') or '').strip().lower()
    if po_present and invoice_seller and po_buyer and invoice_seller != po_buyer:
        score += 10
        findings.append('Buyer/seller party name mismatch (+10 points)')

    # PO cross-reference
    if po_present and not doc_data.get('po_number') in (doc_data.get('invoice_number', '') or ''):
        score += 5
        findings.append('Invoice missing PO cross-reference (+5 points)')

    score = min(score, 100)

    if dup_override or score >= 60:
        outcome = 'FAIL'
    elif score >= 30:
        outcome = 'REVIEW'
    else:
        outcome = 'PASS'

    requires_human_review = outcome in ('REVIEW', 'FAIL')

    return {
        'agent_id': 'trade_document',
        'agent_name': 'Trade Document Agent',
        'execution_status': 'ok',
        'outcome': outcome,
        'risk_score': score,
        'domain_metrics': {
            'commercial_invoice_present': True,
            'po_present': po_present,
            'bol_present': bol_present,
            'invoice_number': invoice_number,
            'duplicate_detected': dup_override,
            'amount_variance_pct': round(abs(invoice_amount - po_amount) / po_amount * 100, 1) if (invoice_amount and po_amount and po_amount > 0) else None,
        },
        'findings': findings,
        'evidence': [{'doc': 'invoice', 'number': invoice_number, 'amount': invoice_amount, 'seller': invoice_seller},
                     {'doc': 'po', 'number': doc_data.get('po_number'), 'amount': po_amount, 'buyer': po_buyer}],
        'confidence': 0.9,
        'summary': f'Trade Document score: {score}/100 — {outcome}. {len(findings)} issue(s) found.',
        'requires_human_review': requires_human_review,
        'warnings_or_errors': warnings,
    }
