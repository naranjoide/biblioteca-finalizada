from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "clave_secreta" 

def get_db_connection():
    conn = sqlite3.connect("biblioteca.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")  
    return conn


@app.route("/")
def home():
    if "username" in session:
        return render_template("home.html", user=session["username"])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():        
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE username=?",  
                            (username, )).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):   
            session["username"] = username
            flash("Login exitoso", "success")
            return redirect(url_for("home"))
        else:
            flash("Usuario o contraseña incorrectos", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        apellido = request.form["apellido"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        email = request.form["email"]


        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO usuarios (username, apellido, password_hash, email) VALUES (?, ?, ?, ?)",
                         (username,apellido, hashed_password, email))
            conn.commit()
            conn.close()
            flash("Usuario registrado con éxito", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("El usuario ya existe", "danger")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Sesión cerrada", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
