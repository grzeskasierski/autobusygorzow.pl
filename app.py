
from flask import Flask, request, jsonify, session, send_from_directory
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "zmien_to_na_wlasny_tajny_klucz"
)

# =====================================
# ADMINISTRATORZY
# =====================================

ADMINI = {
    "GrzesieK": os.environ.get("ADMIN_PASSWORD", "ZMIEN_HASLO"),
    "WiktOgron": os.environ.get("MOD_PASSWORD", "ZMIEN_HASLO2")
}


# =====================================
# DANE FORUM
# =====================================

forum_posty = []
nastepne_id = 1


# =====================================
# SPRAWDZANIE ADMINISTRATORA
# =====================================

def admin_wymagany(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return jsonify({"blad": "Brak uprawnień"}), 403

        return f(*args, **kwargs)

    return wrapper


# =====================================
# POBIERANIE POSTÓW
# =====================================

@app.get("/api/posty")
def pobierz_posty():
    return jsonify(forum_posty)


# =====================================
# DODAWANIE POSTÓW I ODPOWIEDZI
# =====================================

@app.post("/api/posty")
def dodaj_post():
    global nastepne_id

    dane = request.get_json(silent=True) or {}

    tytul = str(dane.get("tytul", "")).strip()
    autor = str(dane.get("autor", "")).strip()
    tresc = str(dane.get("tresc", "")).strip()
    temat = str(dane.get("temat", "")).strip()
    parent_id = dane.get("parentId")

    if not autor or not tresc:
        return jsonify({"blad": "Podaj autora i treść"}), 400

    if not parent_id and not tytul:
        return jsonify({"blad": "Podaj tytuł"}), 400

    if parent_id:
        if not any(
            str(p["id"]) == str(parent_id)
            for p in forum_posty
        ):
            return jsonify({"blad": "Nie znaleziono wpisu"}), 404

    post = {
        "id": nastepne_id,
        "parentId": parent_id,
        "tytul": tytul,
        "autor": autor,
        "tresc": tresc,
        "temat": temat,
        "data": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "polubienia": 0
    }

    nastepne_id += 1
    forum_posty.append(post)

    return jsonify(post), 201


# =====================================
# POLUBIENIA
# =====================================

@app.post("/api/polub/<int:post_id>")
def polub_post(post_id):
    post = next(
        (p for p in forum_posty if p["id"] == post_id),
        None
    )

    if post is None:
        return jsonify({"blad": "Nie znaleziono wpisu"}), 404

    post["polubienia"] += 1

    return jsonify({
        "polubienia": post["polubienia"]
    })


# =====================================
# LOGOWANIE ADMINISTRATORA
# =====================================

@app.post("/api/admin/logowanie")
def admin_logowanie():
    dane = request.get_json(silent=True) or {}

    login = str(dane.get("login", "")).strip()
    haslo = str(dane.get("haslo", ""))

    poprawny_login = next(
        (
            nazwa for nazwa in ADMINI
            if nazwa.lower() == login.lower()
        ),
        None
    )

    if (
        poprawny_login
        and ADMINI[poprawny_login] not in ("ZMIEN_HASLO", "ZMIEN_HASLO2")
        and ADMINI[poprawny_login] == haslo
    ):
        session["admin"] = poprawny_login

        return jsonify({
            "sukces": True,
            "admin": poprawny_login
        })

    return jsonify({
        "blad": "Nieprawidłowy login lub hasło"
    }), 401


# =====================================
# WYLOGOWANIE
# =====================================

@app.post("/api/admin/wyloguj")
def admin_wyloguj():
    session.pop("admin", None)

    return jsonify({"sukces": True})


# =====================================
# USUWANIE POSTÓW I ODPOWIEDZI
# =====================================

@app.delete("/api/admin/usun/<int:post_id>")
@admin_wymagany
def usun_post(post_id):
    global forum_posty

    if not any(p["id"] == post_id for p in forum_posty):
        return jsonify({"blad": "Nie znaleziono wpisu"}), 404

    do_usuniecia = {post_id}

    zmiana = True

    while zmiana:
        zmiana = False

        for post in forum_posty:
            if post.get("parentId") is not None:
                if post["parentId"] in do_usuniecia:
                    if post["id"] not in do_usuniecia:
                        do_usuniecia.add(post["id"])
                        zmiana = True

    forum_posty = [
        p for p in forum_posty
        if p["id"] not in do_usuniecia
    ]

    return jsonify({"sukces": True})


# =====================================
# URUCHAMIANIE SERWERA
# =====================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
