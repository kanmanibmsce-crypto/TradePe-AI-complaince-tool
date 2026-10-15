def run(customer):
    warnings = []
    score = 0
    findings = []

    fields = ['legal_name', 'iec', 'gst_pan', 'country']
    present = sum(1 for f in fields if customer.get(f))
    completeness = (present / len(fields)) * 100
    completeness_gap_points = round((100 - completeness) * 0.25)
    if completeness_gap_points > 0:
        score += completeness_gap_points
        findings.append(f'Registration completeness gap: {completeness:.0f}% ({completeness_gap_points} points)')

    ubo_count = customer.get('ubo_count', 1)
    if ubo_count == 0:
        score += 25
        findings.append('No UBOs declared (+25 points)')

    kyc_status = customer.get('kyc_status', 'verified')
    if kyc_status == 'pending':
        score += 10
        findings.append('KYC status pending (+10 points)')
    elif kyc_status == 'expired':
        score += 20
        findings.append('KYC status expired (+20 points)')

    if customer.get('high_risk_country_flag'):
        score += 15
        findings.append('High-risk country flag (+15 points)')

    if customer.get('adverse_media_flag'):
        score += 15
        findings.append('Adverse media flag (+15 points)')

    score = min(score, 100)

    if score >= 65:
        outcome = 'FAIL'
    elif score >= 35:
        outcome = 'REVIEW'
    else:
        outcome = 'PASS'

    # Decision G1d: critical failure override
    if ubo_count == 0 and kyc_status == 'expired':
        outcome = 'FAIL'
        findings.append('CRITICAL: No UBOs + expired KYC — Decision G1d override → FAIL regardless of score')

    requires_human_review = outcome in ('REVIEW', 'FAIL')

    return {
        'agent_id': 'customer_risk',
        'agent_name': 'Customer Risk / KYC Agent',
        'execution_status': 'ok',
        'outcome': outcome,
        'risk_score': score,
        'domain_metrics': {
            'completeness_pct': completeness,
            'completeness_gap_points': completeness_gap_points,
            'ubo_count': ubo_count,
            'kyc_status': kyc_status,
            'high_risk_country_flag': bool(customer.get('high_risk_country_flag')),
            'adverse_media_flag': bool(customer.get('adverse_media_flag')),
        },
        'findings': findings,
        'evidence': [{'field': f, 'value': customer.get(f)} for f in fields],
        'confidence': 0.95,
        'summary': f'Customer risk score: {score}/100 — {outcome}. {len(findings)} factor(s) assessed.',
        'requires_human_review': requires_human_review,
        'warnings_or_errors': warnings,
    }
