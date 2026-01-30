import requests
import re
import json
import time
import random
from datetime import date, datetime

START_ID = 1
END_ID = 10000

API_URL = "https://api.resy.com/4/find"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": 'ResyAPI api_key="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"',
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://resy.com",
    "priority": "u=1, i",
    "referer": "https://resy.com/",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "x-origin": "https://resy.com",
    "x-resy-auth-token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3NzM2OTk2NzUsInVpZCI6MjAyODU4OSwiZ3QiOiJjb25zdW1lciIsImdzIjpbXSwibGFuZyI6ImVuLXVzIiwiZXh0cmEiOnsiZ3Vlc3RfaWQiOjg1OTg2ODV9fQ.ASrV0u9kjAXhudB_0qxtsSnyhW7g0SA9TCtwHLISP3ezzinOD_OSxgFBbKfK7bBtBCpPw7sjFQNa4RDhvcEtd2JdAcuwMe4y-G6Jdh7ZMkjAiEUK4eVxK2bTeWo4qzfWX82ezEnt0uXLlDUA_grgAp6ijRheytSzp8lXX7TyjdYrpuQK",
    "x-resy-universal-auth": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3NzM2OTk2NzUsInVpZCI6MjAyODU4OSwiZ3QiOiJjb25zdW1lciIsImdzIjpbXSwibGFuZyI6ImVuLXVzIiwiZXh0cmEiOnsiZ3Vlc3RfaWQiOjg1OTg2ODV9fQ.ASrV0u9kjAXhudB_0qxtsSnyhW7g0SA9TCtwHLISP3ezzinOD_OSxgFBbKfK7bBtBCpPw7sjFQNa4RDhvcEtd2JdAcuwMe4y-G6Jdh7ZMkjAiEUK4eVxK2bTeWo4qzfWX82ezEnt0uXLlDUA_grgAp6ijRheytSzp8lXX7TyjdYrpuQK",
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def find_emails(text):
    return list(set(EMAIL_REGEX.findall(text)))


def extract_venue_name(data):
    try:
        results = data.get("results", {})
        venues = results.get("venues", [])
        if venues:
            venue = venues[0].get("venue", {})
            return venue.get("name", "Unknown")
    except (AttributeError, IndexError, TypeError):
        pass
    return "Unknown"


def save_results(restaurants, interrupted=False):
    label = "Interrupted" if interrupted else "Done"
    filename = f"resy-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(restaurants, f, indent=2)

    print(f"\n{label}. {len(restaurants)} restaurant(s) with emails saved to {filename}")

    if restaurants:
        print("\n--- Results ---\n")
        for venue_id, details in restaurants.items():
            emails = ", ".join(item["email"] for item in details["info"])
            print(f"  [{venue_id}] {details['name']}: {emails}")


def crawl():
    restaurants = {}

    try:
        for venue_id in range(START_ID, END_ID + 1):
            payload = {
                "lat": 0,
                "long": 0,
                "day": date.today().isoformat(),
                "party_size": 2,
                "venue_id": venue_id,
            }

            try:
                resp = requests.post(API_URL, headers=HEADERS, json=payload)
                if resp.status_code == 500:
                    print(f"[{venue_id}] HTTP 500 — waiting 60s before retrying")
                    time.sleep(60)
                    resp = requests.post(API_URL, headers=HEADERS, json=payload)
                    if resp.status_code != 200:
                        print(f"[{venue_id}] HTTP {resp.status_code} after retry — skipping")
                        continue
                elif resp.status_code != 200:
                    print(f"[{venue_id}] HTTP {resp.status_code} — skipping")
                    continue

                body = resp.text
                data = resp.json()
                name = extract_venue_name(data)
                emails = find_emails(body)

                if emails:
                    info = [{"email": e, "domain": e.split("@")[1]} for e in emails]
                    restaurants[str(venue_id)] = {"name": name, "info": info}
                    print(f"[{venue_id}] {name} — found {len(emails)} email(s)")
                else:
                    print(f"[{venue_id}] {name} — no emails")

            except requests.RequestException as e:
                print(f"[{venue_id}] Request error: {e}")
            except json.JSONDecodeError:
                print(f"[{venue_id}] Invalid JSON response")

            time.sleep(0.2 + random.uniform(0, 0.3))
    except KeyboardInterrupt:
        print("\n\nCaught interrupt — saving collected results...")
        save_results(restaurants, interrupted=True)
        return

    save_results(restaurants)


if __name__ == "__main__":
    crawl()
