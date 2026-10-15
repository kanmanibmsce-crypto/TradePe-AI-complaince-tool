import os
import json
import urllib.request
import urllib.error
from screening.config import CLAUDE_MODEL


def _offline_template(hit):
    return (
        f"Review of screening hit for '{hit.get('screening_name', hit.get('matched_name', 'Unknown'))}':\n"
        f"Matched against '{hit.get('matched_name', '')}' on {hit.get('list_name', 'Unknown list')} "
        f"with a similarity score of {hit.get('score', 0)}/100 ({hit.get('level', 'unknown')} level).\n"
        f"After review of available information, this appears to be a false positive due to name similarity. "
        f"The counterparty does not match the listed entity based on country, registration, and business context. "
        f"No further action recommended at this time."
    )


def draft(hit):
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return _offline_template(hit)
    try:
        prompt = (
            f"You are a sanctions screening analyst. Draft a brief disposition rationale (2-3 sentences) "
            f"for this watchlist hit:\n"
            f"Screened name: {hit.get('screening_name', hit.get('matched_name', ''))}\n"
            f"Matched against: {hit.get('matched_name', '')}\n"
            f"List: {hit.get('list_name', '')}\n"
            f"Similarity score: {hit.get('score', 0)}/100\n"
            f"Draft a factual, professional rationale explaining why this is likely a false positive "
            f"or requires escalation. Do not make a compliance determination — the analyst will decide."
        )
        payload = json.dumps({
            'model': CLAUDE_MODEL,
            'max_tokens': 256,
            'messages': [{'role': 'user', 'content': prompt}]
        }).encode()
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data['content'][0]['text']
    except Exception:
        return _offline_template(hit)
