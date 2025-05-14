from flask import Flask, render_template_string, request, redirect
import firebase_admin
from firebase_admin import credentials, firestore
import time
import requests

# Initialiser Firebase
cred = credentials.Certificate("alien-team-boss-firebase-adminsdk-fbsvc-46d9ac00a5.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# CONFIG TELEGRAM
BOT_TOKEN = "7859879565:AAHzpptH99XYQmrV6nU8lAE0GIklRPuOXuE"
GROUP_CHAT_ID = "-1002697339023" # Remplacer par l'ID de votre groupe

# Template HTML simple
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <link rel="icon" href="/static/logo.jpg" type="image/jpg">
    <title>Panneau d'administration</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #f7f7f7; }
        .card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px; }
        .btn { padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; }
        .btn-refresh { background-color: #007bff; color: white; }
        .btn-delete { background-color: #dc3545; color: white; }
        .btn-ban { background-color: #ffc107; color: black; }
        .btn-noban { background-color: #28a745; color: white; }
        .btn-send { background-color: #17a2b8; color: white; }
    </style>
</head>
<body>
    <div style="display:flex; align-items:center; gap:10px;">
    <img src="/static/logo.jpg" alt="Logo" style="height:60px; border-radius:8px;">
    <h1 style="margin:0;">👨‍💻 Panneau d'administration des abonnements</h1>
</div>
    <p><strong>👥 Nombre total d'utilisateurs :</strong> {{ total_users }}</p>
    <form method="GET" action="/">
        <button type="submit" class="btn btn-refresh">🔄 Rafraîchir</button>
    </form>
    <form method="POST" action="/send-message">
        <input type="text" name="message" placeholder="Message au groupe" style="width:300px; padding:8px;">
        <button type="submit" class="btn btn-send">📤 Envoyer au groupe</button>
    </form>
    <br>
    {% if subscriptions %}
        {% for sub in subscriptions %}
            <div class="card">
                <p><strong>🆔 User ID:</strong> {{ sub['id'] }}</p>
                <p><strong>🎮 UID:</strong> {{ sub['uid'] }}</p>
                <p><strong>👤 Nickname:</strong> {{ sub['nickname'] }}</p>
                <p><strong>🕒 Dernier envoi:</strong> {{ sub['last_sent'] }}</p>
                <p><strong>🚫 Statut:</strong> {% if sub['banned'] %}<span style="color:red;">Banni</span>{% else %}<span style="color:green;">Actif</span>{% endif %}</p>
                <form method="POST" action="/delete" style="display:inline-block;">
                    <input type="hidden" name="user_id" value="{{ sub['id'] }}">
                    <button type="submit" class="btn btn-delete">❌ Supprimer</button>
                </form>
                {% if not sub['banned'] %}
                <form method="POST" action="/ban" style="display:inline-block;">
                    <input type="hidden" name="user_id" value="{{ sub['id'] }}">
                    <button type="submit" class="btn btn-ban">🚫 Bannir</button>
                </form>
                {% else %}
                <form method="POST" action="/noban" style="display:inline-block;">
                    <input type="hidden" name="user_id" value="{{ sub['id'] }}">
                    <button type="submit" class="btn btn-noban">✅ Débannir</button>
                </form>
                {% endif %}
            </div>
        {% endfor %}
    {% else %}
        <p>Aucun abonnement actif.</p>
    {% endif %}
</body>
</html>
'''

# Récupération des abonnements
def get_subscriptions():
    docs = db.collection("subscriptions").stream()
    return [
        {
            "id": doc.id,
            "uid": doc.to_dict().get("uid"),
            "nickname": doc.to_dict().get("nickname"),
            "last_sent": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(doc.to_dict().get("last_sent", 0))),
            "banned": doc.to_dict().get("banned", False)
        }
        for doc in docs
    ]

@app.route("/", methods=["GET"])
def home():
    subscriptions = get_subscriptions()
    total_users = len(subscriptions)
    return render_template_string(TEMPLATE, subscriptions=subscriptions, total_users=total_users)

@app.route("/send-message", methods=["POST"])
def send_message():
    msg = request.form.get("message")
    if msg:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": GROUP_CHAT_ID,
            "text": msg
        }
        try:
            requests.post(url, data=payload)
        except Exception as e:
            print("Erreur d'envoi Telegram:", e)
    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete():
    user_id = request.form.get("user_id")
    if user_id:
        db.collection("subscriptions").document(user_id).delete()
    return redirect("/")

@app.route("/ban", methods=["POST"])
def ban():
    user_id = request.form.get("user_id")
    if user_id:
        db.collection("subscriptions").document(user_id).update({"banned": True})
    return redirect("/")

@app.route("/noban", methods=["POST"])
def noban():
    user_id = request.form.get("user_id")
    if user_id:
        db.collection("subscriptions").document(user_id).update({"banned": False})
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
