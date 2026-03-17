from flask import Flask, request, jsonify, render_template
import hashlib
import re

app = Flask(__name__)

FLAG = "MYTHX{time_travel_success}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ctf/jailbreak/api/challenge", methods=["POST"])
def challenge():
    data = request.json
    if not data or "payload" not in data:
        return jsonify({"success": False, "message": "No payload provided."}), 400
    
    payload = data["payload"]
    
    # 1. Stripping forbidden keywords according to the implied challenge rules
    forbidden_keywords = ['print', 'printf', 'flag', 'txt', 'cat']
    stripped = payload
    for keyword in forbidden_keywords:
        # Simple string replace removing the exact words
        stripped = stripped.replace(keyword, "")
    
    # Calculate md5 hash of the stripped payload as indicated by the frontend
    hash_received = hashlib.md5(stripped.encode()).hexdigest()
    
    # 2. The Vulnerability:
    # "ccatat flflagag.ttxtxt"
    # Wait, the user mentioned: "ccatat flflagag.ttxtxt"
    # If we strip 'cat', 'c[cat]at' -> 'cat'
    # 'fl[flag]ag' -> 'flag'
    # '.t[txt]xt' -> '.txt'
    # So "ccatat flflagag.ttxtxt" -> "cat flag.txt"
    #
    # If the stripped command equals "cat flag.txt", they win!
    
    if stripped.strip() == "cat flag.txt":
        return jsonify({
            "success": True,
            "message": "Vault bypass successful.",
            "flag": FLAG
        })
    else:
        return jsonify({
            "success": False,
            "stripped": stripped.strip(),
            "hash_received": hash_received
        })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
