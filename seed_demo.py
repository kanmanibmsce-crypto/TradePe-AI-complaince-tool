import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from screening.store import init_db, save_case, save_trade_document_record
from orchestration.case_runner import evaluate_case

SCENARIOS = [
    # Case 1: Clean / safe case — APPROVE
    {
        'case_ref': 'DEMO-001',
        'counterparty_name': 'Surya Handlooms Pvt Ltd',
        'counterparty_country': 'IN',
        'entity_type': 'entity',
        'customer_legal_name': 'Greenfield Exports Ltd',
        'customer_iec': 'IEC1234567',
        'customer_gst_pan': 'GSTIN1234567',
        'customer_country': 'IN',
        'customer_kyc_status': 'verified',
        'customer_ubo_count': 2,
        'customer_high_risk_flag': False,
        'customer_adverse_media_flag': False,
    },
    # Case 2: Borderline manual review — MANUAL_REVIEW (Level A score 48)
    {
        'case_ref': 'DEMO-002',
        'counterparty_name': 'Nexus Commodities FZE',
        'counterparty_country': 'AE',
        'entity_type': 'entity',
        'customer_legal_name': 'Horizon Trade Finance Co',
        'customer_iec': 'IEC2345678',
        'customer_gst_pan': None,
        'customer_country': 'IN',
        'customer_kyc_status': 'verified',
        'customer_ubo_count': 1,
        'customer_high_risk_flag': True,
        'customer_adverse_media_flag': False,
    },
    # Case 3: Strong sanctions match — ESCALATE
    {
        'case_ref': 'DEMO-003',
        'counterparty_name': 'Orion Metals FZE',
        'counterparty_country': 'AE',
        'entity_type': 'entity',
        'customer_legal_name': 'Atlas Minerals India Pvt Ltd',
        'customer_iec': 'IEC3456789',
        'customer_gst_pan': 'GSTIN3456789',
        'customer_country': 'IN',
        'customer_kyc_status': 'verified',
        'customer_ubo_count': 2,
        'customer_high_risk_flag': False,
        'customer_adverse_media_flag': False,
    },
    # Case 4: Customer Risk hard-stop (Decision G1d) — MANUAL_REVIEW
    {
        'case_ref': 'DEMO-004',
        'counterparty_name': 'Pacific Trade Solutions',
        'counterparty_country': 'SG',
        'entity_type': 'entity',
        'customer_legal_name': 'Coastal Shipping Ltd',
        'customer_iec': None,
        'customer_gst_pan': None,
        'customer_country': 'IN',
        'customer_kyc_status': 'expired',
        'customer_ubo_count': 0,
        'customer_high_risk_flag': False,
        'customer_adverse_media_flag': False,
    },
    # Case 5: Level A score warrants review — MANUAL_REVIEW (score ~43)
    {
        'case_ref': 'DEMO-005',
        'counterparty_name': 'Apex Commodities Ltd',
        'counterparty_country': 'AE',
        'entity_type': 'entity',
        'customer_legal_name': 'Summit Exports Pvt Ltd',
        'customer_iec': 'IEC5678901',
        'customer_gst_pan': 'GSTIN5678901',
        'customer_country': 'IN',
        'customer_kyc_status': 'verified',
        'customer_ubo_count': 1,
        'customer_high_risk_flag': True,
        'customer_adverse_media_flag': False,
    },
    # Case 6: Incomplete customer + requires_human_review_floor — MANUAL_REVIEW
    {
        'case_ref': 'DEMO-006',
        'counterparty_name': 'Sunrise Trading FZC',
        'counterparty_country': 'AE',
        'entity_type': 'entity',
        'customer_legal_name': 'Crescent Trade Finance',
        'customer_iec': None,
        'customer_gst_pan': None,
        'customer_country': 'IN',
        'customer_kyc_status': 'pending',
        'customer_ubo_count': 1,
        'customer_high_risk_flag': True,
        'customer_adverse_media_flag': False,
    },
    # Case 7: Trade Document — missing mandatory Commercial Invoice — MANUAL_REVIEW
    {
        'case_ref': 'DEMO-007',
        'counterparty_name': 'Monsoon Agri Exports Ltd',
        'counterparty_country': 'IN',
        'entity_type': 'entity',
        'customer_legal_name': 'Valley Grains Pvt Ltd',
        'customer_iec': 'IEC7890123',
        'customer_gst_pan': 'GSTIN7890123',
        'customer_country': 'IN',
        'customer_kyc_status': 'verified',
        'customer_ubo_count': 2,
        'customer_high_risk_flag': False,
        'customer_adverse_media_flag': False,
        'has_trade_doc': True,
        'invoice_number': None,
        'po_number': 'PO-2026-007',
        'bol_number': 'BOL-2026-007',
        'invoice_amount': None,
        'po_amount': 75000.0,
        'invoice_seller': None,
        'po_buyer': 'Valley Grains Pvt Ltd',
        'bol_shipper': None,
        'invoice_goods': None,
        'po_goods': 'Basmati Rice Grade A',
    },
    # Case 8: Transaction Monitoring — unusual amount — MANUAL_REVIEW
    {
        'case_ref': 'DEMO-008',
        'counterparty_name': 'Blue Horizon Electronics LLC',
        'counterparty_country': 'AE',
        'entity_type': 'entity',
        'customer_legal_name': 'TechBridge India Pvt Ltd',
        'customer_iec': 'IEC8901234',
        'customer_gst_pan': 'GSTIN8901234',
        'customer_country': 'IN',
        'customer_kyc_status': 'verified',
        'customer_ubo_count': 2,
        'customer_high_risk_flag': False,
        'customer_adverse_media_flag': False,
        'has_transaction': True,
        'transaction_amount': 600000.0,
        'transaction_corridor': 'India-UAE',
        'unusual_corridor_flag': False,
        'typical_transaction_amount': 50000.0,
    },
    # Case 9: Regulatory Context Demo — India-UAE, plain APPROVE
    {
        'case_ref': 'DEMO-009',
        'counterparty_name': 'Desert Rose Trading LLC',
        'counterparty_country': 'AE',
        'entity_type': 'entity',
        'customer_legal_name': 'Spice Route Exports',
        'customer_iec': 'IEC9012345',
        'customer_gst_pan': 'GSTIN9012345',
        'customer_country': 'IN',
        'customer_kyc_status': 'verified',
        'customer_ubo_count': 2,
        'customer_high_risk_flag': False,
        'customer_adverse_media_flag': False,
    },
    # Case 10: Combined 4-agent — MANUAL_REVIEW (TM 45/REVIEW + floor)
    {
        'case_ref': 'DEMO-010',
        'counterparty_name': 'Meridian Commerce Group',
        'counterparty_country': 'AE',
        'entity_type': 'entity',
        'customer_legal_name': 'IndoGulf Trade Solutions',
        'customer_iec': 'IEC0123456',
        'customer_gst_pan': 'GSTIN0123456',
        'customer_country': 'IN',
        'customer_kyc_status': 'verified',
        'customer_ubo_count': 2,
        'customer_high_risk_flag': False,
        'customer_adverse_media_flag': False,
        'has_trade_doc': True,
        'invoice_number': 'INV-2026-010',
        'po_number': 'PO-2026-010',
        'bol_number': 'BOL-2026-010',
        'invoice_amount': 100000.0,
        'po_amount': 100000.0,
        'invoice_seller': 'Meridian Commerce Group',
        'po_buyer': 'IndoGulf Trade Solutions',
        'bol_shipper': 'Meridian Commerce Group',
        'invoice_goods': 'Electronic Components',
        'po_goods': 'Electronic Components',
        'has_transaction': True,
        'transaction_amount': 600000.0,
        'transaction_corridor': 'India-UAE',
        'unusual_corridor_flag': False,
        'typical_transaction_amount': 50000.0,
    },
]


def seed():
    print('Resetting database and seeding 10 demo cases...')
    init_db(reset=True)
    for i, scenario in enumerate(SCENARIOS, 1):
        result = evaluate_case(scenario)
        scenario['agent_results'] = result['agent_results']
        scenario['recommendation'] = result['recommendation']
        scenario['recommendation_source'] = result['recommendation_source']
        scenario['weighted_score'] = result['weighted_score']
        case_id = save_case(scenario)
        if scenario.get('has_trade_doc') and scenario.get('invoice_number'):
            save_trade_document_record(case_id, scenario['invoice_number'], scenario.get('invoice_seller', ''))
        print(f'  Case {i:2d} ({scenario["case_ref"]}): {scenario["counterparty_name"][:40]:<40} -> {result["recommendation"]} ({result["recommendation_source"]}, score {result["weighted_score"]})')
    print('Done. 10 demo cases seeded.')


if __name__ == '__main__':
    seed()
