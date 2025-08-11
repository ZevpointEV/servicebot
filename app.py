from flask import Flask, request, jsonify
import openai
import requests
import os
import base64

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")

@app.route("/webhook", methods=["POST"])
def webhook():
    print("🚨 Webhook endpoint hit!", flush=True)
    try:
        data = request.json or {}
        print("📦 Incoming data from Interakt:", data, flush=True)

        chat_type = data.get("data", {}).get("message", {}).get("chat_message_type")
        if chat_type != "CustomerMessage":
            print(f"🔁 Skipping message because chat_message_type is '{chat_type}'", flush=True)
            return jsonify({"status": "ignored"}), 200

        user_msg = data.get("data", {}).get("message", {}).get("message")
        phone_number_raw = data.get("data", {}).get("customer", {}).get("phone_number")
        country_code = data.get("data", {}).get("customer", {}).get("country_code", "+91")
        phone_number = f"{country_code}{phone_number_raw}"
        name = data.get("data", {}).get("customer", {}).get("traits", {}).get("name", "Customer")

        prompt = f'''
        A customer named {name} says: "{user_msg}"
        If the message includes '00', explain it means no current is being detected.
        Suggest:
        1. Power socket and supply
        2. MCB (main switch)
        3. Earthing
        Offer escalation if needed.
        '''

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful ZevPoint support assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response.choices[0].message.content.strip()

        payload = {
            "userId": "",
            "fullPhoneNumber": phone_number,
            "callbackData": "zevpoint-response",
            "type": "Text",
            "data": {
                "message": reply
            }
        }

        headers = {
            "Authorization": f"Basic {INTERAKT_API_KEY}",
            "Content-Type": "application/json"
        }

        res = requests.post("https://api.interakt.ai/v1/public/message/", json=payload, headers=headers)

        print(f"✅ Replied to {phone_number}: {reply}", flush=True)
        print("📬 Interakt API response:", res.status_code, res.text, flush=True)

        return jsonify({"status": "sent", "interakt": res.json()}), 200

    except Exception as e:
        print("❌ Error:", e, flush=True)
        return jsonify({"error": str(e)}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)