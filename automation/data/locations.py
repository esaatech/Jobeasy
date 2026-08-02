"""Canonical location catalog for Ultimate job-search preferences.

Start with USA, Canada, and the UK. Expand this module (or load from JSON)
when adding more countries — keep the public API stable.
"""

from __future__ import annotations

COUNTRIES: list[dict] = [
    {
        'code': 'US',
        'name': 'United States',
        'region_label': 'States',
    },
    {
        'code': 'CA',
        'name': 'Canada',
        'region_label': 'Provinces / territories',
    },
    {
        'code': 'GB',
        'name': 'United Kingdom',
        'region_label': 'Countries / nations',
    },
]

REGIONS: dict[str, list[str]] = {
    'US': [
        'Alabama',
        'Alaska',
        'Arizona',
        'Arkansas',
        'California',
        'Colorado',
        'Connecticut',
        'Delaware',
        'District of Columbia',
        'Florida',
        'Georgia',
        'Hawaii',
        'Idaho',
        'Illinois',
        'Indiana',
        'Iowa',
        'Kansas',
        'Kentucky',
        'Louisiana',
        'Maine',
        'Maryland',
        'Massachusetts',
        'Michigan',
        'Minnesota',
        'Mississippi',
        'Missouri',
        'Montana',
        'Nebraska',
        'Nevada',
        'New Hampshire',
        'New Jersey',
        'New Mexico',
        'New York',
        'North Carolina',
        'North Dakota',
        'Ohio',
        'Oklahoma',
        'Oregon',
        'Pennsylvania',
        'Rhode Island',
        'South Carolina',
        'South Dakota',
        'Tennessee',
        'Texas',
        'Utah',
        'Vermont',
        'Virginia',
        'Washington',
        'West Virginia',
        'Wisconsin',
        'Wyoming',
        'Remote',
    ],
    'CA': [
        'Alberta',
        'British Columbia',
        'Manitoba',
        'New Brunswick',
        'Newfoundland and Labrador',
        'Northwest Territories',
        'Nova Scotia',
        'Nunavut',
        'Ontario',
        'Prince Edward Island',
        'Quebec',
        'Saskatchewan',
        'Yukon',
        'Remote',
    ],
    'GB': [
        'England',
        'Scotland',
        'Wales',
        'Northern Ireland',
        'Remote',
    ],
}


def list_countries() -> list[dict]:
    return [
        {
            'code': c['code'],
            'name': c['name'],
            'region_label': c['region_label'],
            'region_count': len(REGIONS.get(c['code'], [])),
        }
        for c in COUNTRIES
    ]


def get_country(code: str) -> dict | None:
    code = (code or '').strip().upper()
    for country in COUNTRIES:
        if country['code'] == code:
            return country
    return None


def list_regions(code: str) -> list[str] | None:
    """Return regions for a country code, or None if the country is unknown."""
    code = (code or '').strip().upper()
    if code not in REGIONS:
        return None
    return list(REGIONS[code])
