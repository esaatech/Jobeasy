import calendar
from datetime import datetime
from django.utils.translation import gettext as _

def get_month_year_options(locale=None, start_year=1980, end_year=None):
    """
    Returns:
        months: List of (number, translated name) tuples, e.g. [(1, 'January'), ...]
        years: List of years (int), e.g. [2025, 2024, ..., 1980]
        present_label: Translated string for 'Present'
        current_month: int
        current_year: int
    """
    # Get month names (1-indexed)
    months = [(i, _(calendar.month_name[i])) for i in range(1, 13)]
    # Years: descending from current year + 5 to start_year
    now = datetime.now()
    if end_year is None:
        end_year = now.year + 5
    years = list(range(end_year, start_year - 1, -1))
    present_label = _(u"Present")
    current_month = now.month
    current_year = now.year
    return {
        'months': months,
        'years': years,
        'present_label': present_label,
        'current_month': current_month,
        'current_year': current_year,
    } 