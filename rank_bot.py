import requests
import os

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
APP_NAME = "Whatnot"

# Top 10 countries by App Store revenue
COUNTRIES = ["us", "jp", "de", "gb", "fr", "ca", "au", "kr", "cn", "it"]
TOP_N = 200  # maximum apps in RSS feed

def get_ranking(app_name, country):
    rss_url = f"https://rss.applemarketingtools.com/api/v2/{country}/apps/top-free/{TOP_N}/apps.json"
    response = requests.get(rss_url)
    data = response.json()
    apps = data.get("feed", {}).get("results", [])
    
    for i, app in enumerate(apps, start=1):
        if app_name.lower() in app["name"].lower():
            return i
    return None

def post_to_slack(message):
    requests.post(SLACK_WEBHOOK, json={"text": message})

def main():
    message = "📱 *Daily App Store Ranking — Whatnot*"
    for country in COUNTRIES:
        rank = get_ranking(APP_NAME, country)
        if rank:
            message += f"\n🇨🇦 {country.upper()}: #{rank}"
        else:
            message += f"\n🇨🇦 {country.upper()}: Not in top {TOP_N}"
    
    post_to_slack(message)

if __name__ == "__main__":
    main()
