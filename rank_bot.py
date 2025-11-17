import requests
import json
import os

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
APP_NAME = "Whatnot"
RSS_URL = "https://rss.applemarketingtools.com/api/v2/us/apps/top-free/200/apps.json"

def get_ranking():
    response = requests.get(RSS_URL)
    data = response.json()

    apps = data.get("feed", {}).get("results", [])

    for i, app in enumerate(apps, start=1):
        if APP_NAME.lower() in app["name"].lower():
            return i  # rank position
    
    return None  # not in top 200

def post_to_slack(rank):
    if rank is None:
        msg = f"❌ Whatnot is not in the top 200 today."
    else:
        msg = f"📱 *Daily App Store Ranking — Whatnot*\n🇺🇸 Top Free (US): #{rank}"

    requests.post(SLACK_WEBHOOK, json={"text": msg})

if __name__ == "__main__":
    rank = get_ranking()
    post_to_slack(rank)
