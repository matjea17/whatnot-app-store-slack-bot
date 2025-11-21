import requests
import os
import json
import time

# ---------------------------
# Configuration
# ---------------------------
COUNTRIES = ["us", "gb", "fr", "be", "de", "at", "nl", "ca", "au", "es"]

IOS_APP_ID = "1488269261"  # Whatnot iOS App ID
ANDROID_PACKAGE = "com.whatnot.whatnot"

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
HISTORY_FILE = "ranking_history.json"

RETRIES = 3
TIMEOUT = 10
HEADERS = {"User-Agent": "Mozilla/5.0"}  # Avoid Apple blocking CI requests

# ---------------------------
# iOS Ranking (Overall + Shopping)
# ---------------------------
def get_ios_rank(country_code, app_id):
    charts = [
        {"type": "top-free", "category": None, "label": "Overall Free"},
        {"type": "top-free", "category": "shopping", "label": "Shopping"}
    ]

    for chart in charts:
        chart_type = chart["type"]
        category = chart["category"]
        label = chart["label"]

        # Build URL
        if category:
            url = f"https://rss.applemarketingtools.com/api/v2/{country_code}/apps/{chart_type}/{category}/200/apps.json"
        else:
            url = f"https://rss.applemarketingtools.com/api/v2/{country_code}/apps/{chart_type}/200/apps.json"

        for attempt in range(1, RETRIES + 1):
            try:
                r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
                r.raise_for_status()
                if not r.text.strip():
                    continue
                data = r.json()
                apps = data.get("feed", {}).get("results", [])
                for idx, app in enumerate(apps, start=1):
                    if str(app.get("id")) == str(app_id):
                        return idx, label  # rank + chart name
                break  # exit retry loop if request successful but app not found
            except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
                print(f"[iOS] Attempt {attempt} failed for {label} chart in {country_code}: {e}")
                if attempt < RETRIES:
                    time.sleep(2)
                else:
                    print(f"[iOS] Failed to fetch {label} chart for {country_code} after {RETRIES} attempts")
    return None, None  # Not found in any chart

# ---------------------------
# Android Ranking (AppBrain)
# ---------------------------
def get_android_rank(country_code, package):
    url = f"https://www.appbrain.com/api/chart?country={country_code}&cat=overall&format=json"
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            if not r.text.strip():
                continue
            data = r.json()
            apps = data.get("ranks", [])
            for idx, entry in enumerate(apps, start=1):
                if entry.get("p") == package:
                    return idx
            break
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            print(f"[Android] Attempt {attempt} failed for {country_code}: {e}")
            if attempt < RETRIES:
                time.sleep(2)
            else:
                print(f"[Android] Failed to fetch chart for {country_code} after {RETRIES} attempts")
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
        ios_rank, ios_chart = get_ios_rank(country, IOS_APP_ID)
        android_rank = get_android_rank(country, ANDROID_PACKAGE)

        # Yesterday’s ranks
        prev = old.get(country, {})
        ios_prev_rank = prev.get("ios", {}).get("rank") if prev.get("ios") else None
        android_prev = prev.get("android")

        # Compute deltas
        ios_delta = format_delta(ios_rank, ios_prev_rank)
        android_delta = format_delta(android_rank, android_prev)

        # Save today’s values
        new_data[country] = {
            "ios": {"rank": ios_rank, "chart": ios_chart},
            "android": android_rank
        }

        # Build message line
        line = (
            f":earth_africa: *{country.upper()}*\n"
            f"• iOS ({ios_chart if ios_chart else 'Unknown'}): "
            f"{ios_rank if ios_rank else 'Not in top 200'} {ios_delta}\n"
            f"• Android: {android_rank if android_rank else 'Not in charts'} {android_delta}\n"
        )
        message_lines.append(line)

    # Send to Slack
    send_slack_message("\n".join(message_lines))

    # Save history
    save_history(new_data)

if __name__ == "__main__":
    main()
