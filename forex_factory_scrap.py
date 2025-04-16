import requests
from bs4 import BeautifulSoup

def fetch_forexfactory_calendar():
    url = "https://www.forexfactory.com/calendar.php"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    events = []
    for row in soup.select(".calendar__row"):
        impact = row.select_one(".calendar__impact").get("title", "")
        time = row.select_one(".calendar__time").text.strip()
        currency = row.select_one(".calendar__currency").text.strip()
        event = row.select_one(".calendar__event").text.strip()

        if "High" in impact:  # filter for high-impact events
            events.append({
                "time": time,
                "currency": currency,
                "event": event,
                "impact": impact
            })

    return events
