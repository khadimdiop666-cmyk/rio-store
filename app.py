
from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cle-temporaire-rio-store-2026")
creer_table_produits()

BASE_DIR = os.path.expanduser("~")
DB_PATH = os.path.join(BASE_DIR, "commandes.db")


def creer_base():
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            telephone TEXT,
            adresse TEXT,
            paiement TEXT,
            total INTEGER
        )
    """)

    connexion.commit()
    connexion.close()


def creer_table_produits():
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            prix INTEGER,
            image TEXT
        )
    """)

    curseur.execute("SELECT COUNT(*) FROM produits")
    nombre = curseur.fetchone()[0]

    if nombre == 0:
        curseur.executemany("""
            INSERT INTO produits (nom, prix, image)
            VALUES (?, ?, ?)
        """, [
            ("Vêtements", 25000, "vetement.jpg"),
            ("Chaussures", 20000, "chaussure.jpg"),
            ("Sacoche", 18000, "sacoche.jpg")
        ])

    connexion.commit()
    connexion.close()


creer_base()
creer_table_produits()



@app.route("/")
def accueil():
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("SELECT * FROM produits")
    produits = curseur.fetchall()

    connexion.close()

    return render_template("index.html", produits=produits)



@app.route("/commandes")
def afficher_commandes():
    if not session.get("connecte"):
        return redirect(url_for("connexion"))

    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("SELECT * FROM commandes")
    commandes = curseur.fetchall()

    connexion.close()

    total_ventes = sum(commande[5] for commande in commandes)
    nombre_commandes = len(commandes)
    nombre_wave = sum(1 for c in commandes if c[4] == "Wave")
    nombre_orange = sum(1 for c in commandes if c[4] == "Orange Money")

    return render_template(
        "commandes.html",
        commandes=commandes,
        total_ventes=total_ventes,
        nombre_commandes=nombre_commandes,
        nombre_wave=nombre_wave,
        nombre_orange=nombre_orange
    )


@app.route("/commander", methods=["POST"])
def recevoir_commande():
    nom = request.form.get("nom")
    telephone = request.form.get("telephone")
    adresse = request.form.get("adresse")
    paiement = request.form.get("paiement")
    total = request.form.get("total")

    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("""
        INSERT INTO commandes
        (nom, telephone, adresse, paiement, total)
        VALUES (?, ?, ?, ?, ?)
    """, (nom, telephone, adresse, paiement, total))

    connexion.commit()
    connexion.close()

    return "Commande enregistrée avec succès !"


@app.route("/connexion", methods=["GET", "POST"])

def connexion():
    if request.method == "POST":
        mot_de_passe = request.form.get("mot_de_passe")

        

        if mot_de_passe == os.environ.get("ADMIN_PASSWORD"):
            session["connecte"] = True
            return redirect(url_for("afficher_commandes"))

        return "Mot de passe incorrect !"

    return """
        <h1>Connexion administrateur</h1>
        <form method="POST">
            <input type="password" name="mot_de_passe" placeholder="Mot de passe">
            <button type="submit">Se connecter</button>
        </form>
    """



@app.route("/produits")
def gestion_produits():
    if not session.get("connecte"):
        return redirect(url_for("connexion"))

    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("SELECT * FROM produits")
    produits = curseur.fetchall()

    connexion.close()

    return render_template("produits.html", produits=produits)


@app.route("/ajouter-produit", methods=["POST"])
def ajouter_produit():
    if not session.get("connecte"):
        return redirect(url_for("connexion"))

    nom = request.form.get("nom")
    prix = request.form.get("prix")
    image = request.form.get("image")

    if not nom or not prix or not image:
        return "Veuillez remplir tous les champs."

    try:
        prix = int(prix)
        if prix <= 0:
            return "Le prix doit être supérieur à zéro."
    except ValueError:
        return "Prix invalide."

    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("""
        INSERT INTO produits (nom, prix, image)
        VALUES (?, ?, ?)
    """, (nom, prix, image))

    connexion.commit()
    connexion.close()

    return redirect(url_for("gestion_produits"))


@app.route("/modifier-produit/<int:id>", methods=["POST"])
def modifier_produit(id):
    if not session.get("connecte"):
        return redirect(url_for("connexion"))

    prix = request.form.get("prix")

    try:
        prix = int(prix)
        if prix <= 0:
            return "Le prix doit être supérieur à zéro."
    except (ValueError, TypeError):
        return "Prix invalide."

    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute(
        "UPDATE produits SET prix = ? WHERE id = ?",
        (prix, id)
    )

    connexion.commit()
    connexion.close()

    return redirect(url_for("gestion_produits"))


@app.route("/supprimer-produit/<int:id>", methods=["POST"])
def supprimer_produit(id):
    if not session.get("connecte"):
        return redirect(url_for("connexion"))

    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute(
        "DELETE FROM produits WHERE id = ?",
        (id,)
    )

    connexion.commit()
    connexion.close()

    return redirect(url_for("gestion_produits"))


@app.route("/deconnexion")
def deconnexion():
    session.pop("connecte", None)
    return redirect(url_for("accueil"))


if __name__ == "__main__":
    app.run(debug=True)
