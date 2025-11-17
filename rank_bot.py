import requests
import os

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
APP_NAME_IOS = "Whatnot"
APP_NAME_ANDROID = "Whatnot"

# Top 10 countries by App Store revenue
COUNTRIES = ["us", "nl", "de", "gb", "fr", "ca", "au", "be", "at", "es"]
TOP_N = 200  # maximum apps in RSS feed

def get_ios_ranking(app_name, country):
    rss_url = f"https://rss.applemarketingtools.com/api/v2/{country}/apps/top-free/{TOP_N}/apps.json"
    response = requests.get(rss_url)
    data = response.json()
    apps = data.get("feed", {}).get("results", [])
    
    for i, app in enumerate(apps, start=1):
        if app_name.lower() in app["name"].lower():
            return i
    return None

def get_android_ranking(app_name, country):
    # Placeholder: In real scenario, replace with actual API call (AppBrain, AppFollow, etc.)
    # Example: Assume top 100 free apps per country are returned in JSON
    # Here we simulate the ranking as None for simplicity
    return None

def post_to_slack(message):
    requests.post(SLACK_WEBHOOK, json={"text": message})

def main():
    message = "📱 *Daily App Rankings — Whatnot*\n\n*📱 iOS Rankings*"
    for country in COUNTRIES:
        rank = get_ios_ranking(APP_NAME_IOS, country)
        if rank:
            message += f"\n🇨🇦 {country.upper()}: #{rank}"
        else:
            message += f"\n🇨🇦 {country.upper()}: Not in top {TOP_N}"

    message += "\n\n*🤖 Android Rankings*"
    for country in COUNTRIES:
        rank = get_android_ranking(APP_NAME_ANDROID, country)
        if rank:
            message += f"\n🇨🇦 {country.upper()}: #{rank}"
        else:
            message += f"\n🇨🇦 {country.upper()}: Not in top {TOP_N}"

    post_to_slack(message)

if __name__ == "__main__":
    main()
