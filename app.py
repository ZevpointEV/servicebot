{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww34360\viewh18940\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 from flask import Flask, request, jsonify\
import openai\
import requests\
import os\
\
app = Flask(__name__)\
\
openai.api_key = os.getenv("OPENAI_API_KEY")\
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")\
\
@app.route("/webhook", methods=["POST"])\
def webhook():\
    try:\
        data = request.json or \{\}\
\
        if not data.get("message"):\
            print("\uc0\u55357 \u56553  Test webhook received from Interakt")\
            return jsonify(\{"status": "ok"\}), 200\
\
        user_msg = data.get("message")\
        phone_number = data.get("phone_number")\
        name = data.get("contact", \{\}).get("name", "Customer")\
\
        prompt = f"""\
        A customer named \{name\} says: "\{user_msg\}"\
        If the message includes '00', explain it means no current is being detected.\
        Suggest:\
        1. Power socket and supply\
        2. MCB (main switch)\
        3. Earthing\
        Offer escalation if needed.\
        """\
\
        response = openai.ChatCompletion.create(\
            model="gpt-3.5-turbo",\
            messages=[\
                \{"role": "system", "content": "You are a helpful ZevPoint support assistant."\},\
                \{"role": "user", "content": prompt\}\
            ]\
        )\
\
        reply = response.choices[0].message.content.strip()\
\
        payload = \{\
            "receiver": phone_number,\
            "type": "text",\
            "message": \{ "text": reply \}\
        \}\
\
        headers = \{\
            "Authorization": f"Bearer \{INTERAKT_API_KEY\}",\
            "Content-Type": "application/json"\
        \}\
\
        res = requests.post("https://api.interakt.ai/v1/public/message/", json=payload, headers=headers)\
\
        print(f"\uc0\u9989  Replied to \{phone_number\}: \{reply\}")\
        return jsonify(\{"status": "sent", "interakt": res.json()\}), 200\
\
    except Exception as e:\
        print("\uc0\u10060  Error:", e)\
        return jsonify(\{"error": str(e)\}), 200\
\
if __name__ == "__main__":\
    app.run()\
}