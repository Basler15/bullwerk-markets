"""Fail-closed market permission; never changes stock quality scores."""
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def market_gate(report, now):
    blocked = {'allowed': False, 'farbe': None, 'datum': None,
               'reason': 'Keine aktuelle freigegebene Marktampel'}
    try:
        if now.tzinfo is None:
            return blocked
        expected = now.astimezone(ZoneInfo('Europe/Berlin')).date()
        while expected.weekday() >= 5:
            expected -= timedelta(days=1)
        if not isinstance(report, dict):
            return blocked
        approval = report.get('freigabe') or {}
        stamp = datetime.fromisoformat(approval.get('zeitpunkt', '').replace('Z', '+00:00'))
        day = report.get('datum')
        if (report.get('schema_version') != 2 or report.get('status') != 'freigegeben'
                or report.get('geprueft') is not True
                or not isinstance(day, str) or date.fromisoformat(day).isoformat() != day
                or date.fromisoformat(day) != expected
                or not re.fullmatch(r'[a-zA-Z0-9_-]{6,80}', report.get('report_id', ''))
                or approval.get('von') != 'Basler15' or approval.get('text') != 'Bullwerk freigeben'
                or stamp.tzinfo is None or stamp > now):
            return blocked
        color = (report.get('ampel') or {}).get('farbe')
        if color not in ('rot', 'gelb', 'gruen'):
            return blocked
        return {'allowed': color != 'rot', 'farbe': color, 'datum': day,
                'reason': 'Marktampel ROT: keine Breakout-Freigabe' if color == 'rot'
                else 'Marktampel erlaubt die technische Signalpruefung'}
    except (TypeError, ValueError, AttributeError, OverflowError):
        return blocked
