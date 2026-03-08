import sqlite3

conn = sqlite3.connect("data/database.sqlite")
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS registros_actas")
conn.commit()
conn.close()

print("Tabla de actas eliminada. Ya puedes ejecutar el sistema.")