import requests
import os

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
APP_NAME = "Whatnot"

COUNTRIES = ["us", "jp", "de", "gb", "fr"]
OS_TYPES = ["iphone", "ipad", "mac"]
TOP_N = 200

def get_ranking(app_name, country, os_type):
    url = f"https://rss.applemarketingtools.com/api/v2/{country}/apps/top-free/{TOP_N}/{os_type}-apps.json"
    response = requests.get(url)
    data = response.json()
    apps = data.get("feed", {}).get("results", [])
    
    for i, app in enumerate(apps, start=1):
        if app_name.lower() in app["name"].lower():
            return i
    return None

def post_to_slack(message):
    requests.post(SLACK_WEBHOOK, json={"text": message})

def main():
    message = "📱 *Daily App Store Ranking — Whatnot (Split by OS)*"
    for country in COUNTRIES:
        for os_type in OS_TYPES:
            rank = get_ranking(APP_NAME, country, os_type)
            os_label = os_type.capitalize()
            if rank:
                message += f"\n🇨🇦 {country.upper()} {os_label}: #{rank}"
            else:
                message += f"\n🇨🇦 {country.upper()} {os_label}: Not in top {TOP_N}"
    
    post_to_slack(message)

if __name__ == "__main__":
    main()
