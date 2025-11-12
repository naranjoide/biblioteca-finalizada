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


@app.route('/libros')
def libros():
    if 'username' not in session:
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    conn = get_db_connection()
    if q:
        like = f"%{q}%"
        libros = conn.execute("SELECT * FROM libros WHERE titulo LIKE ? OR autor LIKE ? ORDER BY titulo", (like, like)).fetchall()
    else:
        libros = conn.execute("SELECT * FROM libros ORDER BY titulo").fetchall()

    prestamos = conn.execute(
        """
        SELECT p.id AS prestamo_id, p.id_libro, p.id_usuario, p.fecha_prestamo, p.fecha_devolucion,
               l.titulo AS libro_titulo, u.username AS usuario_nombre, u.apellido AS usuario_apellido
        FROM prestamos p
        JOIN libros l ON p.id_libro = l.id
        JOIN usuarios u ON p.id_usuario = u.id
        WHERE p.fecha_devolucion IS NULL
        ORDER BY p.fecha_prestamo
        """
    ).fetchall()
    conn.close()

    return render_template('libros.html', user=session['username'], libros=libros, prestamos=prestamos, q=q)


@app.route('/add_book', methods=['POST'])
def add_book_route():
    if 'username' not in session:
        return redirect(url_for('login'))
    titulo = request.form.get('titulo')
    autor = request.form.get('autor')
    año = request.form.get('año')
    genero = request.form.get('genero')
    año_val = int(año) if año and año.strip() else None
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO libros (titulo, autor, año, genero, disponibilidad) VALUES (?, ?, ?, ?, 1)", (titulo, autor, año_val, genero))
    conn.commit()
    conn.close()
    flash('Libro agregado', 'success')
    return redirect(url_for('libros'))


@app.route('/create_loan', methods=['POST'])
def create_loan_route():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        id_libro = int(request.form.get('id_libro'))
        id_usuario = int(request.form.get('id_usuario'))
    except (TypeError, ValueError):
        flash('IDs inválidos', 'danger')
        return redirect(url_for('libros'))
    conn = get_db_connection()
    cur = conn.cursor()
    book = cur.execute('SELECT disponibilidad FROM libros WHERE id = ?', (id_libro,)).fetchone()
    if not book:
        conn.close()
        flash('Libro no encontrado', 'danger')
        return redirect(url_for('libros'))
    if book[0] == 0:
        conn.close()
        flash('El libro no está disponible', 'danger')
        return redirect(url_for('libros'))
    from datetime import date
    fecha = date.today().isoformat()
    cur.execute('INSERT INTO prestamos (id_libro, id_usuario, fecha_prestamo, fecha_devolucion) VALUES (?, ?, ?, NULL)', (id_libro, id_usuario, fecha))
    cur.execute('UPDATE libros SET disponibilidad = 0 WHERE id = ?', (id_libro,))
    conn.commit()
    conn.close()
    flash('Préstamo registrado', 'success')
    return redirect(url_for('libros'))


@app.route('/return_loan', methods=['POST'])
def return_loan_route():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        prestamo_id = int(request.form.get('prestamo_id'))
    except (TypeError, ValueError):
        flash('ID de préstamo inválido', 'danger')
        return redirect(url_for('libros'))
    conn = get_db_connection()
    cur = conn.cursor()
    row = cur.execute('SELECT id_libro, fecha_devolucion FROM prestamos WHERE id = ?', (prestamo_id,)).fetchone()
    if not row:
        conn.close()
        flash('Préstamo no encontrado', 'danger')
        return redirect(url_for('libros'))
    if row[1] is not None:
        conn.close()
        flash('Préstamo ya fue devuelto', 'info')
        return redirect(url_for('libros'))
    from datetime import date
    fecha = date.today().isoformat()
    id_libro = row[0]
    cur.execute('UPDATE prestamos SET fecha_devolucion = ? WHERE id = ?', (fecha, prestamo_id))
    cur.execute('UPDATE libros SET disponibilidad = 1 WHERE id = ?', (id_libro,))
    conn.commit()
    conn.close()
    flash('Devolución registrada', 'success')
    return redirect(url_for('libros'))

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
