from screening.config import SCORE_REVIEW, SCORE_HIGH
from screening.matcher import Watchlist

_watchlist = None


def _get_watchlist():
    global _watchlist
    if _watchlist is None:
        _watchlist = Watchlist()
    return _watchlist


def run(name, entity_type='entity', country=None):
    wl = _get_watchlist()
    try:
        matches = wl.screen(name, entity_type, country)
    except Exception as e:
        return {
            'agent_id': 'sanctions',
            'agent_name': 'Sanctions & Watchlist Screening Agent',
            'execution_status': 'error',
            'outcome': 'REVIEW',
            'risk_score': 50,
            'domain_metrics': {},
            'findings': [],
            'evidence': [],
            'confidence': 0.0,
            'summary': f'Screening error: {str(e)}',
            'requires_human_review': True,
            'warnings_or_errors': [str(e)],
        }

    review_matches = [m for m in matches if m['level'] in ('review', 'high')]
    if not review_matches:
        return {
            'agent_id': 'sanctions',
            'agent_name': 'Sanctions & Watchlist Screening Agent',
            'execution_status': 'ok',
            'outcome': 'PASS',
            'risk_score': matches[0]['score'] if matches else 0,
            'domain_metrics': {
                'similarity_score': matches[0]['score'] if matches else 0,
                'matched_list': matches[0]['list_name'] if matches else None,
                'matched_name': matches[0]['matched_name'] if matches else None,
                'total_matches_above_show': len(matches),
            },
            'findings': [],
            'evidence': [{'matched_name': m['matched_name'], 'list': m['list_name'], 'score': m['score'], 'level': m['level']} for m in matches],
            'confidence': 0.95,
            'summary': f'No watchlist matches at or above review threshold for "{name}".',
            'requires_human_review': False,
            'warnings_or_errors': [],
        }

    best = review_matches[0]
    outcome = 'FAIL' if best['level'] == 'high' else 'REVIEW'
    return {
        'agent_id': 'sanctions',
        'agent_name': 'Sanctions & Watchlist Screening Agent',
        'execution_status': 'ok',
        'outcome': outcome,
        'risk_score': best['score'],
        'domain_metrics': {
            'similarity_score': best['score'],
            'matched_list': best['list_name'],
            'matched_name': best['matched_name'],
            'total_matches_above_show': len(matches),
            'matches': [{'matched_name': m['matched_name'], 'list': m['list_name'], 'score': m['score'], 'level': m['level']} for m in review_matches[:5]],
        },
        'findings': [f"Potential match: '{best['matched_name']}' on {best['list_name']} (score {best['score']})"],
        'evidence': [{'matched_name': m['matched_name'], 'list': m['list_name'], 'score': m['score'], 'level': m['level']} for m in review_matches],
        'confidence': 0.9,
        'summary': f'Found {len(review_matches)} watchlist match(es) at review/high level for "{name}". Best match: {best["matched_name"]} ({best["score"]}/100, {best["level"]}).',
        'requires_human_review': True,
        'warnings_or_errors': [],
    }
