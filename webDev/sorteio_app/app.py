from flask import Flask, render_template, request, jsonify, redirect
import psycopg2
import random
from datetime import datetime
import os
from supabase import create_client

app = Flask(__name__)

# ---------- SUPABASE ----------
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

BUCKET = os.environ["SUPABASE_BUCKET"]

# ---------- DATABASE ----------
def get_db():
    return psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

# ---------- ROUTES ----------
@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id, name, photo_url, score FROM participants")
    participants = cur.fetchall()

    cur.execute(
        "SELECT draw_date, participants FROM draw_history ORDER BY id DESC LIMIT 5"
    )
    history = cur.fetchall()

    cur.close()
    db.close()

    return render_template(
        "index.html",
        participants=participants,
        history=history
    )

@app.route("/add", methods=["POST"])
def add_participant():
    name = request.form["name"]
    file = request.files["photo"]

    filename = f"{datetime.now().timestamp()}_{file.filename}"

    supabase.storage.from_(BUCKET).upload(
        filename,
        file.read(),
        file_options={
            "content-type": file.content_type
        }
    )

    photo_url = (
        f"{os.environ['SUPABASE_URL']}/storage/v1/object/public/"
        f"{BUCKET}/{filename}"
    )

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO participants (name, photo_url) VALUES (%s, %s)",
        (name, photo_url)
    )

    db.commit()
    cur.close()
    db.close()

    return redirect("/")

@app.route("/draw", methods=["POST"])
def draw():
    data = request.json
    ids = data["ids"]
    qty = data["qty"]

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT id, name, photo_url, score FROM participants WHERE id = ANY(%s)",
        (ids,)
    )
    rows = cur.fetchall()

    weighted = []
    for r in rows:
        weight = 1 / (r[3] + 1)
        weighted.append((r, weight))

    winners = random.choices(
        [w[0] for w in weighted],
        weights=[w[1] for w in weighted],
        k=qty
    )

    for w in winners:
        cur.execute(
            "UPDATE participants SET score = score + 1 WHERE id = %s",
            (w[0],)
        )

    cur.execute(
        "INSERT INTO draw_history (participants) VALUES (%s)",
        (",".join(str(w[0]) for w in winners),)
    )

    db.commit()

    result = []
    for w in winners:
        result.append({
            "name": w[1],
            "photo": w[2]
        })

    cur.close()
    db.close()

    return jsonify(result)

if __name__ == "__main__":
    app.run()


