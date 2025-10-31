import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = "biblioteca.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)          # abre/crea archivo .db
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS libros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor  TEXT NOT NULL,
            año INTEGER,
            genero TEXT NOT NULL,
            disponibilidad INTEGER NOT NULL DEFAULT 1  -- 1 = disponible, 0 = prestado
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            apellido TEXT NOT NULL,
            email TEXT UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_libro INTEGER NOT NULL,
            id_usuario INTEGER NOT NULL,
            fecha_prestamo TEXT NOT NULL,
            fecha_devolucion TEXT,                     -- NULL si no fue devuelto
            FOREIGN KEY (id_libro) REFERENCES libros(id),
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id)       
            

        )
    """)
    conn.commit()
    conn.close()


def insertar_libros_ejemplo():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()  
    cursor.execute("SELECT COUNT(*) FROM libros") 
    cantidad = cursor.fetchone()[0]  

    if cantidad > 0:
        print(f"Ya hay {cantidad} libros en la tabla. No se insertan ejemplos.")
        conn.close()
        return  

    libros = [
        ("Cien años de soledad", "Gabriel García Márquez", 1967, "Realismo mágico", 1),
        ("Los tres chanchitos", "Joseph Jacobs", 1890, "Infantil", 0),
        ("Don Quijote de la Mancha", "Miguel de Cervantes", 1605, "Novela", 1),
        ("Cristian aprobame", "Agustin Perez", 2008, "Ciencia ficción", 0),
        ("La vida del Cris", "Cristiano Carlos", 2010, "Hacker", 1)
    ]
    cursor.executemany("""
        INSERT INTO libros (titulo, autor, año, genero, disponibilidad)
        VALUES (?, ?, ?, ?, ?)
    """, libros)
    conn.commit()
    print("puse  5 libros")

def insertar_usuarios_ejemplo():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()  
    cursor.execute("SELECT COUNT(*) FROM usuarios") 
    cantidad = cursor.fetchone()[0] 
    if cantidad > 0:
        print(f"Ya hay {cantidad} usuarios. No se insertan ejemplos.")
        conn.close()
        return

    usuarios = [
    ("agustin", "Perez", generate_password_hash("1234"), "agustin@gmail.com"),
    ("ciro", "chialvo", generate_password_hash("abcd"), "ciro@gmail.com"),
    ("juan", "massagli", generate_password_hash("qwerty"), "juan@gmail.com"),
    ("manuel", "gomez", generate_password_hash("pass"), "manu@gmail.com"),
    ("cristian", "carle", generate_password_hash("hola"), "cris@gmail.com")
]

    cursor.executemany("""
        INSERT INTO usuarios (username, apellido, password_hash, email)
        VALUES (?, ?, ?, ?)
    """, usuarios)    
    conn.commit()
    print("puse  5 usuarios .")
    conn.close()

def insertar_prestamos_ejemplo():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prestamos")
    cantidad = cursor.fetchone()[0]
    if cantidad > 0:
        print(f"Ya hay {cantidad} préstamos. No se insertan ejemplos.")
        conn.close()
        return

    cursor.execute("SELECT id FROM libros LIMIT 5")
    libros_ids = [row[0] for row in cursor.fetchall()]  

    cursor.execute("SELECT id FROM usuarios LIMIT 5")
    usuarios_ids = [row[0] for row in cursor.fetchall()]  

    prestamos = [
        (libros_ids[0], usuarios_ids[0], "2025-10-01", None),
        (libros_ids[1], usuarios_ids[1], "2025-10-02", "2025-10-10"),
        (libros_ids[2], usuarios_ids[2], "2025-10-03", None),
        (libros_ids[3], usuarios_ids[3], "2025-10-04", "2025-10-12"),
        (libros_ids[4], usuarios_ids[4], "2025-10-05", None)
    ]

    cursor.executemany("""
        INSERT INTO prestamos (id_libro, id_usuario, fecha_prestamo, fecha_devolucion)
        VALUES (?, ?, ?, ?)
    """, prestamos)
    conn.commit()
    print("puse 5 prestamos de ejemplo")
    conn.close()



if __name__ == "__main__":
    init_db()
    insertar_libros_ejemplo()
    insertar_usuarios_ejemplo()
    insertar_prestamos_ejemplo()
