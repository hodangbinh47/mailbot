from flask import Flask, request, jsonify
import requests
import msal
import os

app = Flask(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TENANT_ID = os.environ.get("TENANT_ID")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

def get_token():
    app_msal = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )
    token = app_msal.acquire_token_for_client(scopes=SCOPE)
    return token["access_token"]

@app.route("/")
def home():
    return "Mailbot running"

@app.route("/slack", methods=["POST"])
def slack_events():
    data = request.json

    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    if "event" in data:
        event = data["event"]

        if "thread_ts" in event:
            text = event.get("text")
            channel = event.get("channel")
            thread_ts = event.get("thread_ts")

            history = requests.get(
                "https://slack.com/api/conversations.replies",
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                params={"channel": channel, "ts": thread_ts}
            ).json()

            root_msg = history["messages"][0]["text"]

            if "EMAIL_ID:" in root_msg:
                email_id = root_msg.split("EMAIL_ID:")[1].strip()

                token = get_token()

                url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/reply"

                requests.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "message": {
                            "body": {
                                "contentType": "Text",
                                "content": text
                            }
                        }
                    }
                )

    return "OK", 200
