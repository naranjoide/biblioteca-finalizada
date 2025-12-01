
import sqlite3
from typing import List, Dict, Optional
from werkzeug.security import generate_password_hash

DB_FILE = "biblioteca.db"


def get_db_connection():
	conn = sqlite3.connect(DB_FILE)
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA foreign_keys = ON;")
	return conn


def row_to_dict(row: sqlite3.Row) -> Dict:
	return dict(row) if row is not None else None


def list_all_books() -> List[Dict]:
	conn = get_db_connection()
	rows = conn.execute("SELECT * FROM libros ORDER BY titulo").fetchall()
	conn.close()
	return [row_to_dict(r) for r in rows]


def search_books(query: str) -> List[Dict]:
	q = f"%{query}%"
	conn = get_db_connection()
	rows = conn.execute(
		"SELECT * FROM libros WHERE titulo LIKE ? OR autor LIKE ? ORDER BY titulo",
		(q, q),
	).fetchall()
	conn.close()
	return [row_to_dict(r) for r in rows]


def list_active_loans() -> List[Dict]:
	conn = get_db_connection()
	rows = conn.execute(
		"""
		SELECT p.id AS prestamo_id, p.id_libro, p.id_usuario, p.fecha_prestamo, p.fecha_devolucion,
			   l.titulo AS libro_titulo, l.autor AS libro_autor,
			   u.username AS usuario_nombre, u.apellido AS usuario_apellido
		FROM prestamos p
		JOIN libros l ON p.id_libro = l.id
		JOIN usuarios u ON p.id_usuario = u.id
		WHERE p.fecha_devolucion IS NULL
		ORDER BY p.fecha_prestamo
		"""
	).fetchall()
	conn.close()
	return [row_to_dict(r) for r in rows]


def add_book(titulo: str, autor: str, año: Optional[int], genero: str) -> int:
	conn = get_db_connection()
	cur = conn.cursor()
	cur.execute(
		"INSERT INTO libros (titulo, autor, año, genero, disponibilidad) VALUES (?, ?, ?, ?, 1)",
		(titulo, autor, año, genero),
	)
	conn.commit()
	last = cur.lastrowid
	conn.close()
	return last


def add_user(username: str, apellido: str, password: str, email: Optional[str] = None) -> int:
	conn = get_db_connection()
	cur = conn.cursor()
	password_hash = generate_password_hash(password)
	cur.execute(
		"INSERT INTO usuarios (username, apellido, password_hash, email) VALUES (?, ?, ?, ?)",
		(username, apellido, password_hash, email),
	)
	conn.commit()
	last = cur.lastrowid
	conn.close()
	return last


def get_book_by_id(book_id: int) -> Optional[Dict]:
	conn = get_db_connection()
	row = conn.execute("SELECT * FROM libros WHERE id = ?", (book_id,)).fetchone()
	conn.close()
	return row_to_dict(row)


def get_user_by_id(user_id: int) -> Optional[Dict]:
	conn = get_db_connection()
	row = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
	conn.close()
	return row_to_dict(row)


def list_users() -> List[Dict]:
	conn = get_db_connection()
	rows = conn.execute("SELECT id, username, apellido, email FROM usuarios ORDER BY username").fetchall()
	conn.close()
	return [row_to_dict(r) for r in rows]


def create_loan(id_libro: int, id_usuario: int, fecha_prestamo: str) -> Dict:
	conn = get_db_connection()
	cur = conn.cursor()
	book = cur.execute("SELECT disponibilidad FROM libros WHERE id = ?", (id_libro,)).fetchone()
	if book is None:
		conn.close()
		return {"ok": False, "msg": "Libro no encontrado"}
	if book[0] == 0:
		conn.close()
		return {"ok": False, "msg": "El libro no está disponible"}

	cur.execute(
		"INSERT INTO prestamos (id_libro, id_usuario, fecha_prestamo, fecha_devolucion) VALUES (?, ?, ?, NULL)",
		(id_libro, id_usuario, fecha_prestamo),
	)
	cur.execute("UPDATE libros SET disponibilidad = 0 WHERE id = ?", (id_libro,))
	conn.commit()
	last = cur.lastrowid
	conn.close()
	return {"ok": True, "msg": "Préstamo registrado", "prestamo_id": last}


def return_loan(prestamo_id: int, fecha_devolucion: str) -> Dict:
	conn = get_db_connection()
	cur = conn.cursor()
	row = cur.execute("SELECT id_libro, fecha_devolucion FROM prestamos WHERE id = ?", (prestamo_id,)).fetchone()
	if row is None:
		conn.close()
		return {"ok": False, "msg": "Préstamo no encontrado"}
	if row[1] is not None:
		conn.close()
		return {"ok": False, "msg": "Préstamo ya fue devuelto"}

	id_libro = row[0]
	cur.execute("UPDATE prestamos SET fecha_devolucion = ? WHERE id = ?", (fecha_devolucion, prestamo_id))
	cur.execute("UPDATE libros SET disponibilidad = 1 WHERE id = ?", (id_libro,))
	conn.commit()
	conn.close()
	return {"ok": True, "msg": "Devolución registrada"}


if __name__ == "__main__":
	print("Módulo database.py: ejecutar desde otros scripts (p. ej. consultas.py o main.py)")

