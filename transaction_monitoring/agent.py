def run(txn_data):
    score = 0
    findings = []
    warnings = []

    amount = txn_data.get('transaction_amount')
    typical = txn_data.get('typical_transaction_amount')
    corridor = txn_data.get('transaction_corridor', '')
    unusual_corridor = bool(txn_data.get('unusual_corridor_flag'))

    # Amount band
    amount_band = None
    if amount and typical and typical > 0:
        ratio = amount / typical
        if ratio > 5:
            amount_band = 'highly_unusual'
            score += 45
            findings.append(f'Transaction amount {ratio:.1f}x typical — highly unusual (+45 points)')
        elif ratio > 2:
            amount_band = 'moderately_unusual'
            score += 20
            findings.append(f'Transaction amount {ratio:.1f}x typical — moderately unusual (+20 points)')
        else:
            amount_band = 'normal'
    elif amount and (not typical or typical == 0):
        amount_band = 'unknown'
        warnings.append('Typical transaction amount not available — amount anomaly could not be assessed')
        findings.append('Typical transaction amount missing — amount risk not assessed')

    # Unusual corridor
    if unusual_corridor:
        score += 35
        findings.append(f'Unusual transaction corridor flagged (+35 points): {corridor}')

    score = min(score, 100)

    if score >= 60:
        outcome = 'FAIL'
    elif score >= 30:
        outcome = 'REVIEW'
    else:
        outcome = 'PASS'

    requires_human_review = outcome in ('REVIEW', 'FAIL')

    return {
        'agent_id': 'transaction_monitoring',
        'agent_name': 'Transaction Monitoring Agent',
        'execution_status': 'ok',
        'outcome': outcome,
        'risk_score': score,
        'domain_metrics': {
            'transaction_amount': amount,
            'typical_transaction_amount': typical,
            'amount_ratio': round(amount / typical, 2) if (amount and typical and typical > 0) else None,
            'amount_band': amount_band,
            'transaction_corridor': corridor,
            'unusual_corridor_flag': unusual_corridor,
        },
        'findings': findings,
        'evidence': [{'amount': amount, 'typical': typical, 'corridor': corridor, 'unusual_corridor': unusual_corridor}],
        'confidence': 0.9,
        'summary': f'Transaction monitoring score: {score}/100 — {outcome}. Amount band: {amount_band}. Corridor unusual: {unusual_corridor}.',
        'requires_human_review': requires_human_review,
        'warnings_or_errors': warnings,
    }
