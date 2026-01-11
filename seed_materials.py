import os
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

url = urlparse(DATABASE_URL)

conn = psycopg2.connect(
    dbname=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port,
    sslmode="require"
)

cur = conn.cursor()

print("🔄 Clearing old data...")
cur.execute("DELETE FROM material_settings")
cur.execute("DELETE FROM materials")
conn.commit()

print("📦 Inserting materials...")

materials = [
    ("Basswood Plywood", 3, "Best all-around engraving & cutting wood"),
    ("Birch Plywood", 3, "Harder plywood, darker engraving"),
    ("MDF Board", 3, "Cheap material, heavy smoke"),
    ("Pine Wood", 3, "Soft wood, light engraving"),
    ("Bamboo", 3, "Hard material, high contrast engraving"),
    ("Acrylic Clear", 3, "Needs masking for engraving"),
    ("Acrylic Black", 3, "Best engraving contrast"),
    ("Leather Veg Tan", 2, "Natural leather only"),
    ("Kraft Paper", 0.3, "Mini crafts and packaging"),
    ("Cardboard", 1, "Prototyping material"),
    ("Cork Sheet", 3, "Soft, low density"),
    ("Rubber Sheet", 2, "Laser-safe rubber only"),
    ("Denim Fabric", 1, "Low power engraving"),
    ("Felt Fabric", 2, "Craft fabric"),
    ("Anodized Aluminum", 1, "Marking only"),
    ("Stainless Steel (Coated)", 1, "Use marking spray")
]

material_ids = {}

for name, thickness, notes in materials:
    cur.execute(
        "INSERT INTO materials (name, thickness, notes) VALUES (%s, %s, %s) RETURNING id",
        (name, thickness, notes)
    )
    material_ids[name] = cur.fetchone()[0]

conn.commit()

print("⚙️ Inserting laser settings...")

def add(material, process, intensity, power, speed, passes, notes=""):
    cur.execute("""
        INSERT INTO material_settings
        (material_id, process, intensity, power, speed, passes, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        material_ids[material],
        process,
        intensity,
        power,
        speed,
        passes,
        notes
    ))

# ---- WOODS ----
woods = [
    ("Basswood Plywood", [(20,1200,1),(35,900,1),(55,700,2)], (90,300,4)),
    ("Birch Plywood", [(25,1100,1),(40,850,1),(65,650,2)], (95,250,5)),
    ("MDF Board", [(25,1000,1),(45,800,1),(70,600,2)], (95,220,6)),
    ("Pine Wood", [(18,1300,1),(30,1000,1),(50,750,2)], (85,350,4)),
    ("Bamboo", [(30,900,1),(50,700,1),(75,500,2)], (95,250,5))
]

for material, engraves, cut in woods:
    levels = ["light","medium","dark"]
    for lvl,(p,s,pa) in zip(levels, engraves):
        add(material,"engrave",lvl,p,s,pa)
    add(material,"cut",None,cut[0],cut[1],cut[2])

# ---- ACRYLIC ----
for material in ["Acrylic Clear","Acrylic Black"]:
    add(material,"engrave","light",20,1400,1)
    add(material,"engrave","medium",40,1000,1)
    add(material,"engrave","dark",65,800,2)

# ---- LEATHER ----
add("Leather Veg Tan","engrave","light",18,1200,1)
add("Leather Veg Tan","engrave","medium",30,900,1)
add("Leather Veg Tan","engrave","dark",50,700,2)

# ---- PAPER / FABRIC ----
add("Kraft Paper","engrave","light",10,2000,1)
add("Kraft Paper","cut",None,45,900,1)

add("Cardboard","engrave","light",15,1800,1)
add("Cardboard","cut",None,60,700,1)

add("Denim Fabric","engrave","light",12,2000,1)
add("Felt Fabric","engrave","light",10,2200,1)

# ---- METALS ----
add("Anodized Aluminum","engrave","medium",90,400,2,"Marking only")
add("Stainless Steel (Coated)","engrave","dark",100,300,3,"Use marking spray")

conn.commit()
cur.close()
conn.close()

print("✅ Material Guide seeding complete!")
