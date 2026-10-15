import os

SCORE_SHOW = 60
SCORE_REVIEW = 75
SCORE_HIGH = 88

LIST_FILES = [
    os.path.join(os.path.dirname(__file__), '..', 'data', 'ofac_sample.csv'),
    os.path.join(os.path.dirname(__file__), '..', 'data', 'un_sample.csv'),
    os.path.join(os.path.dirname(__file__), '..', 'data', 'eu_sample.csv'),
    os.path.join(os.path.dirname(__file__), '..', 'data', 'pep_sample.csv'),
]

DB_PATH = '/tmp/screendesk.db' if os.environ.get('VERCEL') else os.path.join(os.path.dirname(__file__), '..', 'screendesk.db')

CLAUDE_MODEL = 'claude-haiku-4-5-20251001'
DEMO_ANALYST = 'demo.analyst@tradepe.example'
