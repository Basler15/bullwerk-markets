# Bullwerk Markets - zentrale SEC-Datenquelle
# Bullwerk Markets - zentrale SEC-Datenquelle

import json
import urllib.request


USER_AGENT = "Bullwerk Markets bullwerkmarkets@gmail.com"

SEC_COMPANYFACTS_URL = (
    "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
)


def get_json(url):
    """
    Lädt JSON-Daten von der SEC.
    """

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:

        print(
            "HTTP Status:",
            response.status,
        )

        return json.loads(
            response.read().decode(
                "utf-8"
            )
        )


def get_company_facts(cik):
    """
    Lädt die SEC Company Facts eines Unternehmens anhand der CIK.
    """

    cik = str(cik).zfill(10)

    url = SEC_COMPANYFACTS_URL.format(
        cik=cik
    )

    return get_json(url)
