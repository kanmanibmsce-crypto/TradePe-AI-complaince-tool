SEVERITY = {'APPROVE': 0, 'MANUAL_REVIEW': 1, 'ESCALATE': 2}
SEVERITY_REV = {0: 'APPROVE', 1: 'MANUAL_REVIEW', 2: 'ESCALATE'}


def _max_rec(*recommendations):
    return SEVERITY_REV[max(SEVERITY.get(r, 0) for r in recommendations)]


def resolve(agent_results, level_a_result):
    triggered_rules = []
    forced_rec = 'APPROVE'
    band = level_a_result.get('band', 'MANUAL_REVIEW')
    weighted_score = level_a_result.get('weighted_score')

    if weighted_score is None:
        triggered_rules.append({
            'rule_id': 'no_usable_agents',
            'reason': 'No usable agents — weighted_score is None',
            'forced': 'MANUAL_REVIEW',
        })
        forced_rec = _max_rec(forced_rec, 'MANUAL_REVIEW')

    # rule_1: sanctions FAIL → ESCALATE
    sanctions = agent_results.get('sanctions', {})
    if sanctions.get('execution_status') == 'ok' and sanctions.get('outcome') == 'FAIL':
        triggered_rules.append({'rule_id': 'rule_1_sanctions_fail', 'reason': 'Sanctions agent returned FAIL', 'forced': 'ESCALATE'})
        forced_rec = _max_rec(forced_rec, 'ESCALATE')

    # rule_3: customer_risk FAIL → MANUAL_REVIEW
    cr = agent_results.get('customer_risk', {})
    if cr.get('execution_status') == 'ok' and cr.get('outcome') == 'FAIL':
        triggered_rules.append({'rule_id': 'rule_3_customer_risk_fail', 'reason': 'Customer Risk agent returned FAIL', 'forced': 'MANUAL_REVIEW'})
        forced_rec = _max_rec(forced_rec, 'MANUAL_REVIEW')

    # rule_2: trade document missing mandatory invoice → MANUAL_REVIEW
    td = agent_results.get('trade_document', {})
    if td.get('execution_status') == 'ok':
        dm = td.get('domain_metrics', {})
        if dm.get('commercial_invoice_present') is False:
            triggered_rules.append({'rule_id': 'rule_2_missing_mandatory_document', 'reason': 'Commercial invoice not present', 'forced': 'MANUAL_REVIEW'})
            forced_rec = _max_rec(forced_rec, 'MANUAL_REVIEW')

    # requires_human_review_floor
    required_agents = ['sanctions', 'customer_risk']
    optional_agents = ['trade_document', 'transaction_monitoring']
    for ag_id in required_agents + optional_agents:
        ag = agent_results.get(ag_id, {})
        if ag.get('execution_status') == 'ok' and ag.get('requires_human_review'):
            triggered_rules.append({'rule_id': 'requires_human_review_floor', 'reason': f'{ag_id} requires human review', 'forced': 'MANUAL_REVIEW'})
            forced_rec = _max_rec(forced_rec, 'MANUAL_REVIEW')

    # rule_4: required agent execution failure
    for ag_id in required_agents:
        ag = agent_results.get(ag_id, {})
        if ag.get('execution_status') in ('error', 'timeout'):
            triggered_rules.append({'rule_id': 'rule_4_agent_execution_failure', 'reason': f'{ag_id} execution failed ({ag.get("execution_status")})', 'forced': 'MANUAL_REVIEW'})
            forced_rec = _max_rec(forced_rec, 'MANUAL_REVIEW')

    # rule_5: required agent missing or invalid
    for ag_id in required_agents:
        ag = agent_results.get(ag_id, {})
        if not ag or ag.get('execution_status') == 'unavailable':
            triggered_rules.append({'rule_id': 'rule_5_agent_missing_or_invalid', 'reason': f'{ag_id} is missing or unavailable', 'forced': 'MANUAL_REVIEW'})
            forced_rec = _max_rec(forced_rec, 'MANUAL_REVIEW')

    # Required-agent safety floor (4-agent path dilution prevention)
    config_name = level_a_result.get('config_name', '2-agent')
    safety_floor_applied = False
    if config_name == '4-agent':
        from orchestration.level_a import compute_baseline_2agent
        baseline_score, baseline_band = compute_baseline_2agent(agent_results)
        if baseline_band and SEVERITY.get(baseline_band, 0) > SEVERITY.get(band, 0):
            triggered_rules.append({
                'rule_id': 'required_agent_safety_floor',
                'reason': f'4-agent dilution prevention: Sanctions+CustomerRisk alone warrant {baseline_band} (score {baseline_score}), but 4-agent weighted score ({weighted_score}) falls in {band}',
                'forced': baseline_band,
            })
            forced_rec = _max_rec(forced_rec, baseline_band)
            safety_floor_applied = True

    final_rec = _max_rec(band, forced_rec)
    hard_stop = bool(triggered_rules) and final_rec != band
    recommendation_source = 'HARD_STOP_OVERRIDE' if (forced_rec != 'APPROVE' and SEVERITY.get(forced_rec, 0) >= SEVERITY.get(band, 0)) else 'WEIGHTED_SCORE'
    if weighted_score is None:
        recommendation_source = 'HARD_STOP_OVERRIDE'

    return {
        'recommendation': final_rec,
        'recommendation_source': recommendation_source,
        'hard_stop_triggered': hard_stop,
        'triggered_rules': triggered_rules,
        'is_partial': level_a_result.get('is_partial', False),
        'weighted_score': weighted_score,
        'level_a_band': band,
        'config_name': config_name,
    }
