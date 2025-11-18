import requests
import os
import json

# Countries to track
COUNTRIES = ["us", "gb”, "fr”, "be”, “de”, "at", “nl", "ca", "au", "es"]

IOS_APP_ID = "1601150422"  # Whatnot iOS App ID
ANDROID_PACKAGE = "com.whatnot.whatnot"

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

HISTORY_FILE = "ranking_history.json"


# ---------------------------
# iOS Ranking (Apple RSS)
# ---------------------------
def get_ios_rank(country_code, app_id):
    url = f"https://rss.applemarketingtools.com/api/v2/{country_code}/apps/top-free/200/apps.json"
    r = requests.get(url)

    if r.status_code != 200:
        return None

    apps = r.json().get("feed", {}).get("results", [])
    for idx, app in enumerate(apps, start=1):
        if str(app.get("id")) == str(app_id):
            return idx

    return None


# ---------------------------
# Android Ranking (AppBrain)
# ---------------------------
def get_android_rank(country_code, package):
    url = f"https://www.appbrain.com/api/chart?country={country_code}&cat=overall&format=json"
    r = requests.get(url)

    if r.status_code != 200:
        return None

    apps = r.json().get("ranks", [])
    for idx, entry in enumerate(apps, start=1):
        if entry.get("p") == package:
            return idx

    return None


# ---------------------------
# Slack Messaging
# ---------------------------
def send_slack_message(text):
    if not SLACK_WEBHOOK:
        print("Missing webhook")
        return

    requests.post(SLACK_WEBHOOK, json={"text": text})


# ---------------------------
# Load + Save History
# ---------------------------
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}

    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------
# Delta Helper
# ---------------------------
def format_delta(today, yesterday):
    if yesterday is None:
        return "(new)"

    if today is None:
        return "(out of top)"

    diff = yesterday - today

    if diff > 0:
        return f"(▲ +{diff})"
    elif diff < 0:
        return f"(▼ {diff})"
    else:
        return "(➖)"


# ---------------------------
# Main
# ---------------------------
def main():
    old = load_history()
    new_data = {}

    message_lines = ["*📈 Whatnot Daily App Rankings (with Δ)*", ""]

    for c in COUNTRIES:
        ios_rank = get_ios_rank(c, IOS_APP_ID)
        android_rank = get_android_rank(c, ANDROID_PACKAGE)

        # Save today's values for this country
        new_data[c] = {
            "ios": ios_rank,
            "android": android_rank
        }

        # Yesterday's values
        prev = old.get(c, {})
        ios_prev = prev.get("ios")
        android_prev = prev.get("android")

        # Delta
        ios_delta = format_delta(ios_rank, ios_prev)
        android_delta = format_delta(android_rank, android_prev)

        line = (
            f":earth_africa: *{c.upper()}*\n"
            f"• iOS: {ios_rank if ios_rank else 'Not in top 200'} {ios_delta}\n"
            f"• Android: {android_rank if android_rank else 'Not in charts'} {android_delta}\n"
        )

        message_lines.append(line)

    # Send Slack message
    send_slack_message("\n".join(message_lines))

    # Save new history file
    save_history(new_data)


if __name__ == "__main__":
    main()
