import math

WEIGHT_CONFIGS = {
    '2-agent': {'sanctions': 0.50, 'customer_risk': 0.50},
    '3-agent-TD': {'sanctions': 0.50, 'customer_risk': 0.25, 'trade_document': 0.25},
    '3-agent-TM': {'sanctions': 0.50, 'customer_risk': 0.25, 'transaction_monitoring': 0.25},
    '4-agent': {'sanctions': 0.40, 'customer_risk': 0.20, 'trade_document': 0.20, 'transaction_monitoring': 0.20},
}

SCORE_BANDS = {'APPROVE': (0, 34), 'MANUAL_REVIEW': (35, 64), 'ESCALATE': (65, 100)}


def _round_half_up(x):
    return math.floor(x + 0.5)


def select_config(agent_results):
    has_td = 'trade_document' in agent_results and agent_results['trade_document'].get('execution_status') == 'ok'
    has_tm = 'transaction_monitoring' in agent_results and agent_results['transaction_monitoring'].get('execution_status') == 'ok'
    if has_td and has_tm:
        return '4-agent', WEIGHT_CONFIGS['4-agent']
    if has_td:
        return '3-agent-TD', WEIGHT_CONFIGS['3-agent-TD']
    if has_tm:
        return '3-agent-TM', WEIGHT_CONFIGS['3-agent-TM']
    return '2-agent', WEIGHT_CONFIGS['2-agent']


def compute(agent_results):
    config_name, weights = select_config(agent_results)
    weighted_sum = 0.0
    weight_total = 0.0
    usable = []
    excluded = []

    for agent_id, weight in weights.items():
        result = agent_results.get(agent_id)
        if not result:
            excluded.append({'agent_id': agent_id, 'reason': 'not present'})
            continue
        if result.get('execution_status') != 'ok':
            excluded.append({'agent_id': agent_id, 'reason': f"execution_status={result.get('execution_status')}"})
            continue
        risk_score = result.get('risk_score')
        if risk_score is None:
            excluded.append({'agent_id': agent_id, 'reason': 'risk_score is None'})
            continue
        weighted_sum += risk_score * weight
        weight_total += weight
        usable.append({'agent_id': agent_id, 'risk_score': risk_score, 'weight': weight})

    if weight_total == 0:
        return {
            'config_name': config_name,
            'weighted_score': None,
            'usable_agents': usable,
            'excluded_agents': excluded,
            'is_partial': bool(excluded),
            'band': 'MANUAL_REVIEW',
        }

    weighted_score = _round_half_up(weighted_sum / weight_total)
    weighted_score = max(0, min(100, weighted_score))

    band = 'APPROVE'
    for b, (lo, hi) in SCORE_BANDS.items():
        if lo <= weighted_score <= hi:
            band = b
            break

    return {
        'config_name': config_name,
        'weighted_score': weighted_score,
        'usable_agents': usable,
        'excluded_agents': excluded,
        'is_partial': bool(excluded),
        'band': band,
    }


def compute_baseline_2agent(agent_results):
    # Required-agent safety floor: compute sanctions + customer_risk alone at 50/50
    baseline_results = {
        k: agent_results[k] for k in ('sanctions', 'customer_risk') if k in agent_results
    }
    result = compute(baseline_results)
    return result.get('weighted_score'), result.get('band')
