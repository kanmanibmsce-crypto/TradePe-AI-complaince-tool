REGULATORY_UPDATES = [
    {
        'update_id': 'RU-001',
        'source': 'RBI (synthetic)',
        'title': 'Updated KYC/AML Guidelines for Cross-Border Payments',
        'summary': 'RBI has issued updated guidelines requiring enhanced due diligence for cross-border trade payments above USD 50,000, including mandatory UBO disclosure and periodic KYC refresh.',
        'impact': 'High',
        'action_required': 'Review KYC procedures for all counterparties in cross-border trade flows. Ensure UBO documentation is current.',
        'status': 'active',
        'published_at': '2026-07-15',
        'applicable_countries': ['IN', 'India'],
    },
    {
        'update_id': 'RU-002',
        'source': 'DGFT (synthetic)',
        'title': 'Import/Export Documentation Requirements — Trade Finance',
        'summary': 'DGFT has clarified documentation requirements for import/export transactions under the Foreign Trade Policy, emphasizing commercial invoice validation and PO cross-referencing.',
        'impact': 'Medium',
        'action_required': 'Ensure all trade finance cases include validated commercial invoices cross-referenced to purchase orders.',
        'status': 'active',
        'published_at': '2026-06-20',
        'applicable_countries': ['IN', 'India'],
    },
    {
        'update_id': 'RU-003',
        'source': 'FATF (synthetic)',
        'title': 'Updated High-Risk Jurisdictions — FATF Grey List',
        'summary': 'FATF has updated its list of jurisdictions subject to increased monitoring. Enhanced due diligence is required for transactions with entities in listed countries.',
        'impact': 'High',
        'action_required': 'Review all active counterparties in FATF-monitored jurisdictions. Apply enhanced due diligence procedures.',
        'status': 'active',
        'published_at': '2026-08-01',
        'applicable_countries': ['AE', 'UAE', 'United Arab Emirates', 'IN', 'India', 'CN', 'China'],
    },
    {
        'update_id': 'RU-004',
        'source': 'MAS (synthetic)',
        'title': 'Singapore AML/CFT Requirements for Trade Finance',
        'summary': 'MAS has issued guidance on AML/CFT controls for trade finance activities, specifically addressing document verification and counterparty screening for Singapore-connected transactions.',
        'impact': 'Medium',
        'action_required': 'Apply MAS trade finance controls for cases involving Singapore-based entities or SGD-denominated transactions.',
        'status': 'active',
        'published_at': '2026-07-30',
        'applicable_countries': ['SG', 'Singapore'],
    },
    {
        'update_id': 'RU-005',
        'source': 'RBI (synthetic)',
        'title': 'FEMA Compliance — Outward Remittance Reporting',
        'summary': 'Updated FEMA reporting requirements for outward remittances above specified thresholds. All AD Category-I banks must file enhanced reports for cross-border trade payments.',
        'impact': 'High',
        'action_required': 'Ensure FEMA reporting workflows are updated for new threshold requirements. Verify AD bank compliance.',
        'status': 'active',
        'published_at': '2026-08-10',
        'applicable_countries': ['IN', 'India', 'AE', 'UAE', 'United Arab Emirates'],
    },
]


def get_all_updates():
    return REGULATORY_UPDATES


def get_updates_for_countries(countries):
    if not countries:
        return REGULATORY_UPDATES
    countries_set = set(c.strip() for c in countries if c)
    result = []
    for upd in REGULATORY_UPDATES:
        applicable = set(upd.get('applicable_countries', []))
        if countries_set & applicable:
            result.append(upd)
    return result
