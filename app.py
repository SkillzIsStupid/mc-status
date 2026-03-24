from flask import Flask, jsonify, send_from_directory
from mcstatus import JavaServer
import os

app = Flask(__name__)

SERVER = "your-playit-address.playit.gg"
PORT = 25565

@app.route("/api")
def api():
    try:
        server = JavaServer.lookup(f"{SERVER}:{PORT}")
        status = server.status()

        return jsonify({
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "names": [p.name for p in status.players.sample] if status.players.sample else []
        })
    except:
        return jsonify({"online": False})

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
