import sqlite3

def inicializar_tabla_gabinetes():
    conn = sqlite3.connect('data/database.sqlite')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS gabinetes_led (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            serie TEXT NOT NULL,
            modelo TEXT NOT NULL,
            pitch REAL NOT NULL,
            ancho_mm INTEGER NOT NULL,
            alto_mm INTEGER NOT NULL,
            res_ancho INTEGER NOT NULL,
            res_alto INTEGER NOT NULL,
            peso_kg REAL NOT NULL,
            consumo_max_w INTEGER NOT NULL
        )
    ''')
    
    c.execute('SELECT COUNT(*) FROM gabinetes_led')
    if c.fetchone()[0] == 0:
        datos_prueba = [
            ('Generico', 'Indoor Die-Cast', 'P2.5-500x500', 2.5, 500, 500, 200, 200, 7.5, 150),
            ('Generico', 'Indoor Die-Cast', 'P3.9-500x500', 3.91, 500, 500, 128, 128, 7.5, 150),
            ('Generico', 'Outdoor Rental', 'P4.8-500x1000', 4.81, 500, 1000, 104, 208, 12.5, 300)
        ]
        c.executemany('''
            INSERT INTO gabinetes_led 
            (marca, serie, modelo, pitch, ancho_mm, alto_mm, res_ancho, res_alto, peso_kg, consumo_max_w)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', datos_prueba)
        print("Datos de prueba insertados con éxito.")
        
    conn.commit()
    conn.close()
    print("Tabla 'gabinetes_led' estructurada y lista.")

if __name__ == "__main__":
    inicializar_tabla_gabinetes()