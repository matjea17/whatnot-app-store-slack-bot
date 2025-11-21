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
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------------------
# iOS Ranking (using AMP API)
# ---------------------------
def get_ios_rank(country_code, app_id):
    """
    Debug-heavy version so we can see exactly what Apple AMP returns.
    """

    BASE = f"https://amp-api.apps.apple.com/v1/catalog/{country_code}/apps/charts"

    CHARTS = [
        ("top-free", 0, "Overall Free"),
        ("top-free", 36, "Shopping"),
    ]

    for chart, genre, label in CHARTS:
        url = f"{BASE}?chart={chart}&genre={genre}&limit=200"

        for attempt in range(1, RETRIES + 1):
            try:
                r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
                print("\n===== iOS DEBUG =====")
                print("Country:", country_code)
                print("Chart:", label)
                print("URL:", url)
                print("Status:", r.status_code)
                print("Raw response first 300 chars:")
                print(r.text[:300])
                print("=====================\n")

                r.raise_for_status()

                data = r.json()
                apps = data.get("results", [])

                print(f"Returned {len(apps)} apps for {label}")
                print("First 10 IDs:", [a.get("id") for a in apps[:10]])

                for idx, app in enumerate(apps, start=1):
                    if str(app.get("id")) == str(app_id):
                        print(f"FOUND WHATNOT at position {idx} ({label})")
                        return idx, label

                print(f"Whatnot NOT FOUND in {label}")
                break

            except Exception as e:
                print(f"[iOS] Error on attempt {attempt}: {e}")
                if attempt < RETRIES:
                    time.sleep(2)

    return None, None


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

        except Exception as e:
            print(f"[Android] Attempt {attempt} failed for {country_code}: {e}")
            if attempt < RETRIES:
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

        prev = old.get(country, {})
        ios_prev_rank = prev.get("ios", {}).get("rank") if prev.get("ios") else None
        android_prev = prev.get("android")

        ios_delta = format_delta(ios_rank, ios_prev_rank)
        android_delta = format_delta(android_rank, android_prev)

        new_data[country] = {
            "ios": {"rank": ios_rank, "chart": ios_chart},
            "android": android_rank
        }

        line = (
            f":earth_africa: *{country.upper()}*\n"
            f"• iOS ({ios_chart if ios_chart else 'Unknown'}): "
            f"{ios_rank if ios_rank else 'Not in top 200'} {ios_delta}\n"
            f"• Android: {android_rank if android_rank else 'Not in charts'} {android_delta}\n"
        )

        message_lines.append(line)

    send_slack_message("\n".join(message_lines))
    save_history(new_data)


if __name__ == "__main__":
    main()
