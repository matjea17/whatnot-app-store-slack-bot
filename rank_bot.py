import requests
import os
import json
import time

# ---------------------------
# Configuration
# ---------------------------
COUNTRIES = ["us", "gb”, "fr”, "be”, “de”, "at", “nl", "ca", "au", "es"]

IOS_APP_ID = "1601150422"  # Whatnot iOS App ID
ANDROID_PACKAGE = "com.whatnot.whatnot"

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
HISTORY_FILE = "ranking_history.json"

RETRIES = 3
TIMEOUT = 10


# ---------------------------
# iOS Ranking (Apple RSS) with retries
# ---------------------------
def get_ios_rank(country_code, app_id):
    url = f"https://rss.applemarketingtools.com/api/v2/{country_code}/apps/top-free/200/apps.json"
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            apps = data.get("feed", {}).get("results", [])
            for idx, app in enumerate(apps, start=1):
                if str(app.get("id")) == str(app_id):
                    return idx
            return None  # Not found
        except (requests.RequestException, ValueError) as e:
            print(f"[iOS] Attempt {attempt} failed for {country_code}: {e}")
            time.sleep(2)
    return None


# ---------------------------
# Android Ranking (AppBrain) with retries
# ---------------------------
def get_android_rank(country_code, package):
    url = f"https://www.appbrain.com/api/chart?country={country_code}&cat=overall&format=json"
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            apps = data.get("ranks", [])
            for idx, entry in enumerate(apps, start=1):
                if entry.get("p") == package:
                    return idx
            return None
        except (requests.RequestException, ValueError) as e:
            print(f"[Android] Attempt {attempt} failed for {country_code}: {e}")
            time.sleep(2)
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
    if di
