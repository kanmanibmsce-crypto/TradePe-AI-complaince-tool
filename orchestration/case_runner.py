from screening.contract_adapter import run as run_sanctions
from customer_risk.agent import run as run_customer_risk
from trade_document.agent import run as run_trade_document
from transaction_monitoring.agent import run as run_transaction_monitoring
from regulatory_intelligence.data import get_updates_for_countries
from orchestration.level_a import compute
from orchestration.level_b import resolve
from screening.store import get_prior_invoices


def evaluate_case(case_data):
    agent_results = {}

    # Agent 1: Sanctions (required)
    agent_results['sanctions'] = run_sanctions(
        name=case_data.get('counterparty_name', ''),
        entity_type=case_data.get('entity_type', 'entity'),
        country=case_data.get('counterparty_country'),
    )

    # Agent 2: Customer Risk (required)
    agent_results['customer_risk'] = run_customer_risk({
        'legal_name': case_data.get('customer_legal_name'),
        'iec': case_data.get('customer_iec'),
        'gst_pan': case_data.get('customer_gst_pan'),
        'country': case_data.get('customer_country'),
        'kyc_status': case_data.get('customer_kyc_status', 'verified'),
        'ubo_count': case_data.get('customer_ubo_count', 1),
        'high_risk_country_flag': case_data.get('customer_high_risk_flag', False),
        'adverse_media_flag': case_data.get('customer_adverse_media_flag', False),
    })

    # Agent 3: Trade Document (optional)
    if case_data.get('has_trade_doc'):
        prior_invoices = get_prior_invoices()
        agent_results['trade_document'] = run_trade_document({
            'invoice_number': case_data.get('invoice_number'),
            'po_number': case_data.get('po_number'),
            'bol_number': case_data.get('bol_number'),
            'invoice_amount': case_data.get('invoice_amount'),
            'po_amount': case_data.get('po_amount'),
            'invoice_seller': case_data.get('invoice_seller'),
            'po_buyer': case_data.get('po_buyer'),
            'bol_shipper': case_data.get('bol_shipper'),
            'invoice_goods': case_data.get('invoice_goods'),
            'po_goods': case_data.get('po_goods'),
        }, prior_invoices=prior_invoices)

    # Agent 4: Transaction Monitoring (optional)
    if case_data.get('has_transaction'):
        agent_results['transaction_monitoring'] = run_transaction_monitoring({
            'transaction_amount': case_data.get('transaction_amount'),
            'transaction_corridor': case_data.get('transaction_corridor'),
            'unusual_corridor_flag': case_data.get('unusual_corridor_flag', False),
            'typical_transaction_amount': case_data.get('typical_transaction_amount'),
        })

    # Level A: weighted scoring
    level_a_result = compute(agent_results)

    # Level B: hard-stop rules + required-agent safety floor
    level_b_result = resolve(agent_results, level_a_result)

    # Agent 5: Regulatory Intelligence (advisory only, outside scoring)
    countries = [c for c in [case_data.get('customer_country'), case_data.get('counterparty_country')] if c]
    reg_updates = get_updates_for_countries(countries)

    return {
        'agent_results': agent_results,
        'level_a': level_a_result,
        'level_b': level_b_result,
        'recommendation': level_b_result['recommendation'],
        'recommendation_source': level_b_result['recommendation_source'],
        'weighted_score': level_b_result['weighted_score'],
        'triggered_rules': level_b_result['triggered_rules'],
        'regulatory_updates': reg_updates,
    }
