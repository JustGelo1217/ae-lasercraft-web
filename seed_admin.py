import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

with open("material_guide.sql", "r") as f:
    cursor.executescript(f.read())

conn.commit()
conn.close()

print("Material Guide seeded successfully")
