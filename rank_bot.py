import requests
import os
import json
import time

# ---------------------------
# Configuration
# ---------------------------
COUNTRIES = ["us", "gb", "de", "fr", "ca", "au", "nl", "se", "in", "sg"]

IOS_APP_ID = "1601150422"  # Whatnot iOS App ID
ANDROID_PACKAGE = "com.whatnot.whatnot"

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
HISTORY_FILE = "ranking_history.json"

RETRIES = 3
TIMEOUT = 10
HEADERS = {"User-Agent": "Mozilla/5.0"}  # Avoid Apple blocking CI requests

# ---------------------------
# iOS Ranking (Apple RSS) with retries
# ---------------------------
def get_ios_rank(country_code, app_id):
    url = f"https://rss.applemarketingtools.com/api/v2/{country_code}/apps/top-free/200/apps.json"
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            if not r.text.strip():
                raise ValueError("Empty response")
            data = r.json()
            apps = data.get("feed", {}).get("results", [])
            for idx, app in enumerate(apps, start=1):
                if str(app.get("id")) == str(app_id):
                    return idx
            return None  # Not found
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            print(f"[iOS] Attempt {attempt} failed for {country_code}: {e}")
            if attempt < RETRIES:
                print("Retrying...")
                time.sleep(2)
    print(f"[iOS] Failed to get rank for {country_code} after {RETRIES} attempts")
    return None

# ---------------------------
# Android Ranking (AppBrain) with retries
# ---------------------------
def get_android_rank(country_code, package):
    url = f"https://www.appbrain.com/api/chart?country={country_code}&cat=overall&format=json"
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            if not r.text.strip():
                raise ValueError("Empty response")
            data = r.json()
            apps = data.get("ranks", [])
            for idx, entry in enumerate(apps, start=1):
                if entry.get("p") == package:
                    return idx
            return None
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            print(f"[Android] Attempt {attempt} failed for {country_code}: {e}")
            if attempt < RETRIES:
                print("Retrying...")
                time.sleep(2)
    print(f"[Android] Failed to get rank for {country_code} after {RETRIES} attempts")
    return None

# ---------------------------
# Slack messaging
# ---------------------------
def send_slack_message(text):
    if not SLACK_WEBHOOK:
        print("Missing Slack webhook")
        return
    try:
        requests.post(SLACK_WEBHOOK, json={"text": text})
    except Exception as e:
        print(f"Failed to send Slack message: {e}")

# ---------------------------
# History (load/save)
# ---------------------------
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------------------
# Delta formatting
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
        return f"(▼ {abs(diff)})"
    else:
        return "(➖)"

# ---------------------------
# Main
# ---------------------------
def main():
    old = load_history()
    new_data = {}
    message_lines = ["*📈 Whatnot Daily App Rankings (with Δ)*", ""]

    for country in COUNTRIES:
        ios_rank = get_ios_rank(country, IOS_APP_ID)
        android_rank = get_android_rank(country, ANDROID_PACKAGE)

        # Save today’s ranks
        new_data[country] = {"ios": ios_rank, "android": android_rank}

        # Yesterday’s ranks
        prev = old.get(country, {})
        ios_prev = prev.get("ios")
        android_prev = prev.get("android")

        # Compute deltas
        ios_delta = format_delta(ios_rank, ios_prev)
        android_delta = format_delta(android_rank, android_prev)

        # Build message line
        line = (
            f":earth_africa: *{country.upper()}*\n"
            f"• iOS: {ios_rank if ios_rank else 'Not in top 200'} {ios_delta}\n"
            f"• Android: {android_rank if android_rank else 'Not in charts'} {android_delta}\n"
        )
        message_lines.append(line)

    # Send to Slack
    send_slack_message("\n".join(message_lines))

    # Save history
    save_history(new_data)

if __name__ == "__main__":
    main()

