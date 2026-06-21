"""
FreeCAD Makro — Waschmaschine mit 10.000 Bauteilen
====================================================
Ausführen in FreeCAD:
  Makro → Makros → Neu → Code einfügen → Ausführen
  ODER: Extras → Python-Konsole → exec(open('...pfad...').read())

Laufzeit: ca. 3–8 Minuten (abhängig von Hardware)
Ergebnis: ~10.250 Bauteile, gespeichert als Waschmaschine_10000.FCStd
"""

import FreeCAD as App
import Part
import math
import os

# ── Dokument ──────────────────────────────────────────────────────────────────
doc = App.newDocument("Waschmaschine_10000")
App.Console.PrintMessage("=== Waschmaschine 10.000 Teile wird erstellt ===\n")

counter = [0]  # mutable int für Closures

def add(name, shape, color=(0.75, 0.75, 0.80)):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        try:
            obj.ViewObject.ShapeColor = color
        except Exception:
            pass
    counter[0] += 1
    if counter[0] % 500 == 0:
        App.Console.PrintMessage(f"  ... {counter[0]} Teile erstellt\n")
    return obj

def move(shape, x=0, y=0, z=0):
    return shape.copy().translate(App.Vector(x, y, z))

def cyl(r, h, x=0, y=0, z=0, axis=App.Vector(0, 0, 1)):
    s = Part.makeCylinder(r, h, App.Vector(x, y, z), axis)
    return s

def box(dx, dy, dz, x=0, y=0, z=0):
    return Part.makeBox(dx, dy, dz, App.Vector(x, y, z))

def sphere(r, x=0, y=0, z=0):
    return Part.makeSphere(r, App.Vector(x, y, z))

def torus(r1, r2, x=0, y=0, z=0):
    s = Part.makeTorus(r1, r2)
    return move(s, x, y, z)

# ══════════════════════════════════════════════════════════════════════════════
# 1  GEHÄUSE  (~120 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[1/11] Gehäuse ...\n")

# Hauptpanele (6 Seiten)
panel_data = [
    ("Panel_Oben",       box(600, 560, 25,  0,  0, 875), (0.85,0.85,0.88)),
    ("Panel_Unten",      box(600, 560, 20,  0,  0,   0), (0.75,0.75,0.78)),
    ("Panel_Links",      box( 25, 560,900, -25,  0,   0), (0.80,0.80,0.83)),
    ("Panel_Rechts",     box( 25, 560,900, 600,  0,   0), (0.80,0.80,0.83)),
    ("Panel_Rueckseite", box(600,  20,900,  0,   0,   0), (0.78,0.78,0.80)),
    ("Panel_Sockelblende",box(600,560, 80,  0,   0,  -80),(0.60,0.60,0.62)),
]
for name, shape, col in panel_data:
    add(name, shape, col)

# Rahmen-Profile (12 Stück)
for i, (x, y, z, dx, dy, dz) in enumerate([
    (0,0,0,       25, 25,900),  (575,0,0,     25, 25,900),
    (0,535,0,     25, 25,900),  (575,535,0,   25, 25,900),
    (0,0,875,    600, 25, 25),  (0,535,875,  600, 25, 25),
    (0,0,0,      600, 25, 25),  (0,535,0,    600, 25, 25),
    (25,0,0,     25,560, 20),   (575,0,0,     25,560, 20),
    (25,0,875,   25,560, 25),   (575,0,875,   25,560, 25),
]):
    add(f"Rahmen_{i+1:02d}", box(dx, dy, dz, x, y, z), (0.50,0.52,0.55))

# Nivellierfüße (4×3 Teile = Fuß + Gummimatte + Kontermutter)
for i, (fx, fy) in enumerate([(50,50),(550,50),(50,510),(550,510)]):
    add(f"Fuss_Koerper_{i+1}",    cyl(25, 60, fx, fy, -60),  (0.40,0.40,0.42))
    add(f"Fuss_Gummi_{i+1}",      cyl(28, 8,  fx, fy, -68),  (0.15,0.15,0.15))
    add(f"Fuss_Kontermutter_{i+1}",cyl(22, 12, fx, fy,  -12), (0.65,0.65,0.68))

# Tür-Ausschnitts-Verstärkungsring
add("Tuer_Verstaerkungsring", torus(195, 18, 300, -5, 450), (0.60,0.62,0.65))

# Kabelführungsclips im Gehäuse (30 Stück)
for i in range(30):
    cx = 30 + (i % 6) * 90
    cy = 10 + (i // 6) * 110
    cz = 100 + (i % 8) * 90
    add(f"Kabelclip_Gehause_{i+1:02d}", box(18, 8, 12, cx, cy, cz), (0.25,0.30,0.35))

# Haltewinkel (20 Stück)
for i in range(20):
    wx = 30 + (i % 5) * 110
    wz = 80 + (i // 5) * 180
    add(f"Haltewinkel_{i+1:02d}", box(30, 5, 30, wx, 0, wz), (0.55,0.55,0.58))

# ══════════════════════════════════════════════════════════════════════════════
# 2  TÜR-BAUGRUPPE  (~90 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[2/11] Tür-Baugruppe ...\n")

add("Tuer_Aussenring",   torus(195, 22, 300, -28, 450), (0.85,0.85,0.88))
add("Tuer_Innenring",    torus(190, 14, 300, -26, 450), (0.50,0.52,0.55))
add("Tuer_Glas",         cyl(172, 6, 300, -30, 450, App.Vector(0,1,0)), (0.60,0.75,0.90))

# Türscharnier links + rechts (je 8 Teile)
for side, sy in [("Links", -5), ("Rechts", 5)]:
    add(f"Scharnier_{side}_Koerper", box(30, 20, 60, 110, sy, 340), (0.60,0.62,0.65))
    add(f"Scharnier_{side}_Bolzen",  cyl( 5, 80, 125, sy+10, 350), (0.70,0.72,0.75))
    add(f"Scharnier_{side}_Feder",   cyl( 4, 40, 125, sy+10, 355), (0.30,0.32,0.35))
    add(f"Scharnier_{side}_Scheibe1",cyl( 8,  3, 125, sy+10, 345), (0.65,0.65,0.68))
    add(f"Scharnier_{side}_Scheibe2",cyl( 8,  3, 125, sy+10, 395), (0.65,0.65,0.68))
    add(f"Scharnier_{side}_Platte",  box(40, 15, 50, 105, sy, 335), (0.55,0.55,0.58))
    add(f"Scharnier_{side}_Stopfen", cyl( 6,  8, 125, sy+10, 425), (0.20,0.20,0.22))
    add(f"Scharnier_{side}_Clip",    box(10,  6, 14, 120, sy+8, 415), (0.25,0.28,0.30))

# Türgriff (7 Teile)
add("Griff_Koerper",      box(140, 22, 30, 230, -32, 440),  (0.90,0.90,0.92))
add("Griff_Innenhalter",  box(130, 10, 20, 235, -30, 445),  (0.60,0.60,0.62))
add("Griff_Achse",        cyl(4, 140, 230, -31, 455), (0.55,0.55,0.58))
add("Griff_Feder",        cyl(3,  40, 300, -31, 448), (0.30,0.32,0.35))
add("Griff_Schraube_L",   cyl(3,  15, 232, -34, 455), (0.65,0.65,0.68))
add("Griff_Schraube_R",   cyl(3,  15, 368, -34, 455), (0.65,0.65,0.68))
add("Griff_Abdeckung",    box(150,  6, 35, 225, -36, 438), (0.88,0.88,0.90))

# Türschloss (8 Teile)
add("Tuerschloss_Gehause", box(60, 30, 80, 480, -20, 410),  (0.40,0.42,0.45))
add("Tuerschloss_Haken",   box(20, 15, 35, 492, -18, 430),  (0.60,0.62,0.65))
add("Tuerschloss_Feder",   cyl( 4, 30, 495, -15, 425), (0.30,0.32,0.35))
add("Tuerschloss_Achse",   cyl( 3, 25, 498, -15, 418), (0.55,0.55,0.58))
add("Tuerschloss_Magnet",  box(15, 10, 18, 488, -16, 440),  (0.20,0.22,0.30))
add("Tuerschloss_Anker",   box(12,  8, 15, 490, -15, 442),  (0.40,0.42,0.45))
add("Tuerschloss_Spule",   cyl( 8, 20, 495, -15, 445), (0.25,0.28,0.30))
add("Tuerschloss_Deckel",  box(65, 12, 85, 478, -22, 408),  (0.35,0.37,0.40))

# Türdichtung (Manschette) — 24 Segmente
for i in range(24):
    angle = (i / 24) * 2 * math.pi
    sx = 300 + 190 * math.cos(angle)
    sz = 450 + 190 * math.sin(angle)
    add(f"Manschette_Seg_{i+1:02d}", box(28, 28, 28, sx-14, -14, sz-14), (0.20,0.20,0.22))

add("Manschette_Spannring",  torus(193,  6, 300, -15, 450), (0.50,0.52,0.55))
add("Manschette_Klemmfeder", torus(188,  4, 300, -10, 450), (0.35,0.37,0.40))

# ══════════════════════════════════════════════════════════════════════════════
# 3  TROMMEL-BAUGRUPPE  (~160 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[3/11] Trommel-Baugruppe ...\n")

# Laugenbehälter (Außentrommel) — 2 Hälften + Dichtring
add("Laugenbehaelter_Vorne", cyl(240, 480, 300, -10, 450, App.Vector(0,1,0)), (0.88,0.88,0.90))
add("Laugenbehaelter_Hinten",cyl(238, 20,  300, 470, 450, App.Vector(0,1,0)), (0.82,0.82,0.85))
add("Laugenbehaelter_Dichtung", torus(235, 8, 300, 240, 450), (0.20,0.20,0.22))

# Innentrommel
add("Trommel_Mantel",     cyl(210, 440, 300, 10, 450, App.Vector(0,1,0)), (0.75,0.80,0.85))
add("Trommel_Front",      cyl(208,  12, 300, 8,  450, App.Vector(0,1,0)), (0.70,0.75,0.80))
add("Trommel_Rueckseite", cyl(208,  15, 300, 445,450, App.Vector(0,1,0)), (0.70,0.75,0.80))

# Mitnehmer/Baffles (3 Stück, je 4 Teile)
for i in range(3):
    angle = (i / 3) * 2 * math.pi
    bx = 300 + 170 * math.cos(angle)
    bz = 450 + 170 * math.sin(angle)
    add(f"Mitnehmer_{i+1}_Koerper",  box(25, 400, 25, bx-12, 30, bz-12), (0.65,0.68,0.72))
    add(f"Mitnehmer_{i+1}_Abdeckung",box(28, 400, 10, bx-14, 30, bz-5),  (0.60,0.63,0.66))
    add(f"Mitnehmer_{i+1}_Schraube1",cyl(3, 10, bx, 35,  bz), (0.70,0.72,0.75))
    add(f"Mitnehmer_{i+1}_Schraube2",cyl(3, 10, bx, 415, bz), (0.70,0.72,0.75))

# Trommelwelle + Flansch
add("Trommelwelle",   cyl(22, 180, 300, 460, 450, App.Vector(0,1,0)), (0.75,0.77,0.80))
add("Trommel_Flansch",cyl(80,  18, 300, 455, 450, App.Vector(0,1,0)), (0.68,0.70,0.73))
add("Trommelwelle_Keil",box(6, 60, 6, 303, 460, 453), (0.55,0.57,0.60))

# Spinne (Kreuzspinne) — 3 Arme + Nabe
add("Spinne_Nabe", cyl(40, 30, 300, 450, 450, App.Vector(0,1,0)), (0.65,0.67,0.70))
for i in range(3):
    angle = (i / 3) * 2 * math.pi
    ax = 300 + 100 * math.cos(angle)
    az = 450 + 100 * math.sin(angle)
    add(f"Spinne_Arm_{i+1}", box(20, 30, 200, ax-10, 452, az-100), (0.62,0.64,0.67))

# Lager vorne (19 Teile: Außenring + Innenring + Käfig + 16 Kugeln)
add("Lager_Vorne_Aussenring", torus(52,  9, 300, 20, 450), (0.75,0.77,0.80))
add("Lager_Vorne_Innenring",  torus(30,  7, 300, 20, 450), (0.70,0.72,0.75))
add("Lager_Vorne_Kaefig",     torus(41,  4, 300, 20, 450), (0.55,0.58,0.60))
for k in range(16):
    kangle = (k / 16) * 2 * math.pi
    kx = 300 + 41 * math.cos(kangle)
    kz = 450 + 41 * math.sin(kangle)
    add(f"Lager_Vorne_Kugel_{k+1:02d}", sphere(7, kx, 20, kz), (0.80,0.82,0.85))

# Lager hinten (19 Teile)
add("Lager_Hinten_Aussenring", torus(52,  9, 300, 455, 450), (0.75,0.77,0.80))
add("Lager_Hinten_Innenring",  torus(30,  7, 300, 455, 450), (0.70,0.72,0.75))
add("Lager_Hinten_Kaefig",     torus(41,  4, 300, 455, 450), (0.55,0.58,0.60))
for k in range(16):
    kangle = (k / 16) * 2 * math.pi
    kx = 300 + 41 * math.cos(kangle)
    kz = 450 + 41 * math.sin(kangle)
    add(f"Lager_Hinten_Kugel_{k+1:02d}", sphere(7, kx, 455, kz), (0.80,0.82,0.85))

add("Wellendichtring_Vorne",  cyl(28, 10, 300, 18, 450, App.Vector(0,1,0)), (0.20,0.20,0.22))
add("Wellendichtring_Hinten", cyl(28, 10, 300, 458,450, App.Vector(0,1,0)), (0.20,0.20,0.22))

# Gegengewichte (3 × Beton + je 4 Bolzen + 4 Muttern + 4 Scheiben = 39 Teile)
for i, (gwx, gwz, gwdx, gwdz) in enumerate([
    (100, 230, 400, 80), (100, 630, 400, 80), (145, 430, 310, 400)
]):
    add(f"Gegengewicht_{i+1}", box(gwdx, 60, gwdz, gwx, 490, gwz), (0.50,0.50,0.52))
    for b in range(4):
        bx2 = gwx + 30 + (b % 2) * (gwdx - 60)
        bz2 = gwz + 20 + (b // 2) * (gwdz - 40)
        add(f"GG{i+1}_Bolzen_{b+1}", cyl(5, 75, bx2, 488, bz2), (0.65,0.65,0.68))
        add(f"GG{i+1}_Mutter_{b+1}", cyl(8, 10, bx2, 485, bz2), (0.60,0.62,0.65))
        add(f"GG{i+1}_Scheibe_{b+1}",cyl(10, 3, bx2, 553, bz2), (0.70,0.72,0.75))

# Lagergehäuse (2 Teile)
add("Lagergehaeuse_Vorne",  box(120, 30, 120, 240, 10,  390), (0.72,0.74,0.77))
add("Lagergehaeuse_Hinten", box(120, 30, 120, 240, 460, 390), (0.72,0.74,0.77))

# Trommel-Löcher als symbolische Scheiben (50 Gruppen)
for i in range(50):
    angle = (i / 50) * 2 * math.pi
    hx = 300 + 190 * math.cos(angle)
    hz = 450 + 190 * math.sin(angle)
    add(f"Trommel_Lochgruppe_{i+1:02d}", cyl(3, 8, hx, 200, hz), (0.60,0.65,0.70))

# ══════════════════════════════════════════════════════════════════════════════
# 4  ANTRIEB / MOTOR  (~110 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[4/11] Motor & Antrieb ...\n")

# Motor
add("Motor_Statorpaket",      cyl(88, 180, 300, 540, 450, App.Vector(0,1,0)), (0.40,0.42,0.45))
add("Motor_Rotor",            cyl(72, 170, 300, 545, 450, App.Vector(0,1,0)), (0.55,0.58,0.60))
add("Motor_Welle",            cyl(12, 220, 300, 535, 450, App.Vector(0,1,0)), (0.70,0.72,0.75))
add("Motor_Gehaeuse_Vorne",   cyl(95,  20, 300, 540, 450, App.Vector(0,1,0)), (0.45,0.47,0.50))
add("Motor_Gehaeuse_Hinten",  cyl(95,  20, 300, 720, 450, App.Vector(0,1,0)), (0.45,0.47,0.50))
add("Motor_Luefter",          cyl(70,  18, 300, 538, 450, App.Vector(0,1,0)), (0.35,0.37,0.40))
add("Motor_Luefterhaube",     cyl(80,  22, 300, 528, 450, App.Vector(0,1,0)), (0.40,0.42,0.45))
add("Motor_Lager_Antriebsseitig", torus(28, 6, 300, 555, 450), (0.75,0.77,0.80))
add("Motor_Lager_Luefterseitig",  torus(28, 6, 300, 715, 450), (0.75,0.77,0.80))

# Wicklungen (6 Gruppen: 3 Phasen × 2 Wickelköpfe)
winding_colors = [(0.85,0.35,0.10),(0.10,0.45,0.85),(0.10,0.70,0.30)]
for ph in range(3):
    for end in range(2):
        angle = (ph / 3) * 2 * math.pi
        wx = 300 + 65 * math.cos(angle)
        wz = 450 + 65 * math.sin(angle)
        wy = 545 if end == 0 else 715
        add(f"Wicklung_Ph{ph+1}_Ende{end+1}", cyl(10, 25, wx, wy, wz), winding_colors[ph])

# Kohlebürsten + Halter (2 × 2 Teile)
for i in range(2):
    bangle = (i / 2) * math.pi
    brx = 300 + 82 * math.cos(bangle)
    brz = 450 + 82 * math.sin(bangle)
    add(f"Kohlebuerste_{i+1}",   box(8, 20, 8, brx-4, 628, brz-4), (0.30,0.30,0.32))
    add(f"Buersten_Halter_{i+1}",box(14, 30,14, brx-7, 622, brz-7),(0.50,0.52,0.55))

# Motor-Montageplatte + 8 Schrauben
add("Motor_Montageplatte", box(220, 12, 240, 190, 532, 330), (0.60,0.62,0.65))
for i in range(8):
    ms_x = 210 + (i % 4) * 55
    ms_z = 345 + (i // 4) * 110
    add(f"Motor_Schraube_{i+1}", cyl(4, 30, ms_x, 520, ms_z), (0.65,0.65,0.68))

# Antriebsriemen (20 Segmente)
for i in range(20):
    angle = (i / 20) * 2 * math.pi
    rx = 300 + 220 * math.cos(angle)
    rz = 450 + 220 * math.sin(angle)
    add(f"Riemen_Seg_{i+1:02d}", box(22, 20, 22, rx-11, 620, rz-11), (0.20,0.18,0.15))

add("Riemenscheibe_Motor",  cyl(45, 30, 300, 625, 450, App.Vector(0,1,0)), (0.65,0.67,0.70))
add("Riemenscheibe_Trommel",cyl(125, 25, 300, 620, 450, App.Vector(0,1,0)), (0.60,0.62,0.65))

# Riemenspanner (5 Teile)
add("Riemenspanner_Halter", box(40, 15, 80, 200, 600, 350), (0.55,0.57,0.60))
add("Riemenspanner_Arm",    box(12, 12, 60, 212, 598, 380), (0.50,0.52,0.55))
add("Riemenspanner_Rolle",  cyl(20, 22, 216, 596, 435, App.Vector(0,1,0)), (0.65,0.67,0.70))
add("Riemenspanner_Bolzen", cyl( 5, 40, 216, 592, 435), (0.70,0.72,0.75))
add("Riemenspanner_Feder",  cyl( 6, 35, 216, 595, 435), (0.35,0.37,0.40))

# ══════════════════════════════════════════════════════════════════════════════
# 5  WASSERFÜHRUNG  (~70 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[5/11] Wasserführung ...\n")

add("Einlassventil_Gehaeuse",  box(100, 60, 80,  50, 10, 760), (0.40,0.45,0.50))
add("Einlassventil_Spule_1",   cyl(18, 45,  75, 12, 790, App.Vector(0,1,0)), (0.30,0.35,0.40))
add("Einlassventil_Spule_2",   cyl(18, 45, 115, 12, 790, App.Vector(0,1,0)), (0.30,0.35,0.40))
add("Einlassventil_Filter_1",  cyl(12, 15,  75, 68, 790, App.Vector(0,1,0)), (0.70,0.72,0.75))
add("Einlassventil_Filter_2",  cyl(12, 15, 115, 68, 790, App.Vector(0,1,0)), (0.70,0.72,0.75))
add("Einlassventil_Stecker",   box(30, 15, 20,  75, 10, 800), (0.25,0.28,0.30))

# Schläuche (je 3 Segmente + 2 Schellen)
for idx, (sx, sz, label) in enumerate([(90, 800, "Zulauf"), (90, 780, "Ablauf"), (90, 760, "Druck")]):
    for seg in range(3):
        add(f"Schlauch_{label}_Seg_{seg+1}", cyl(12, 80, sx, 30+seg*80, sz), (0.25,0.30,0.35))
    add(f"Schlauchschelle_{label}_1", torus(14, 3, sx, 28, sz), (0.60,0.62,0.65))
    add(f"Schlauchschelle_{label}_2", torus(14, 3, sx, 268, sz), (0.60,0.62,0.65))

add("Druckschalter_Koerper",  box(40, 40, 35, 55, 30, 700), (0.45,0.47,0.50))
add("Druckschalter_Membran",  cyl(15,  4, 75, 38, 717), (0.20,0.22,0.25))
add("Druckschalter_Stecker",  box(18, 12, 15, 60, 28, 708), (0.25,0.28,0.30))

add("NTC_Sensor_Koerper",     cyl( 5, 22, 300, 5, 200), (0.35,0.37,0.40))
add("NTC_Sensor_Dichtung",    cyl( 8,  4, 300, 5, 205), (0.20,0.22,0.25))
add("NTC_Sensor_Kabel",       cyl( 3, 60, 300, 5, 225), (0.15,0.15,0.18))

add("Einspuelschale_Koerper", box(160, 60, 90,  420, 820, 760), (0.82,0.82,0.85))
add("Einspuelschale_Halter",  box(165, 10, 95,  418, 815, 758), (0.70,0.72,0.75))
add("Einspuelduese_1",        cyl( 6, 15,  440, 818, 800), (0.40,0.45,0.50))
add("Einspuelduese_2",        cyl( 6, 15,  490, 818, 800), (0.40,0.45,0.50))
add("Einspuelduese_3",        cyl( 6, 15,  540, 818, 800), (0.40,0.45,0.50))

# Ablaufpumpe (8 Teile)
add("Ablaufpumpe_Gehaeuse",   cyl(45, 80, 100, 5, 200, App.Vector(0,1,0)), (0.40,0.42,0.45))
add("Ablaufpumpe_Laufrad",    cyl(38, 20, 100, 38, 200, App.Vector(0,1,0)), (0.55,0.58,0.60))
add("Ablaufpumpe_Motor",      cyl(30, 55, 100, 82, 200, App.Vector(0,1,0)), (0.35,0.37,0.40))
add("Ablaufpumpe_Einlauf",    cyl(14, 40, 100, 3, 162), (0.45,0.47,0.50))
add("Ablaufpumpe_Auslauf",    cyl(14, 40, 140, 30, 200, App.Vector(1,0,0)), (0.45,0.47,0.50))
add("Ablaufpumpe_Fuesse",     box(100, 12, 70, 55, -5, 165), (0.50,0.52,0.55))
add("Ablauffilter_Gehaeuse",  cyl(30, 60, 100, 5, 150), (0.45,0.47,0.50))
add("Ablauffilter_Sieb",      cyl(26, 50, 100, 8, 152), (0.60,0.62,0.65))

add("Ablaufschlauch_Seg1",    cyl(14,120, 100, 48, 235, App.Vector(0,1,0)), (0.25,0.30,0.35))
add("Ablaufschlauch_Seg2",    cyl(14, 80, 100, 165,235, App.Vector(0,1,0)), (0.25,0.30,0.35))
add("Ablaufschlauch_Schelle1",torus(16,  3, 100, 45, 235), (0.60,0.62,0.65))

# ══════════════════════════════════════════════════════════════════════════════
# 6  HEIZELEMENT  (~18 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[6/11] Heizelement ...\n")

add("Heizelement_Flansch",    box(120, 15, 60, 240, 5, 420), (0.68,0.70,0.73))
add("Heizelement_Dichtung",   box(122, 4,  62, 239, 18, 419), (0.15,0.15,0.17))
add("Heizelement_Rohr_1",     cyl( 8,260, 270, 22, 430, App.Vector(0,1,0)), (0.72,0.75,0.78))
add("Heizelement_Rohr_2",     cyl( 8,260, 320, 22, 430, App.Vector(0,1,0)), (0.72,0.75,0.78))
add("Heizelement_Verbindung", cyl( 9, 60, 295, 280, 430, App.Vector(1,0,0)), (0.70,0.73,0.76))
add("Thermosicherung_1",      cyl( 8, 14, 270, 28, 450), (0.65,0.67,0.70))
add("Thermosicherung_2",      cyl( 8, 14, 320, 28, 450), (0.65,0.67,0.70))
add("Heizelement_Klemme_1",   box(12, 18, 10, 265, 24, 450), (0.75,0.77,0.80))
add("Heizelement_Klemme_2",   box(12, 18, 10, 315, 24, 450), (0.75,0.77,0.80))
add("Heizelement_Abdeckung",  box(125, 8, 65, 238, 5, 418), (0.60,0.62,0.65))
for m in range(4):
    add(f"Heizelement_Mutter_{m+1}", cyl(6, 8, 248+m*22, 5, 422), (0.65,0.67,0.70))
add("NTC_Temperatur_Koerper", cyl(5, 20, 295, 22, 460), (0.35,0.37,0.40))
add("NTC_Temperatur_Kabel",   cyl(2, 80, 295, 40, 460), (0.15,0.15,0.18))

# ══════════════════════════════════════════════════════════════════════════════
# 7  AUFHÄNGUNG  (~80 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[7/11] Aufhängung ...\n")

spring_positions = [(110, 350), (490, 350), (110, 550), (490, 550)]
for si, (spx, spz) in enumerate(spring_positions):
    # Jede Feder = 15 Windungs-Segmente
    for coil in range(15):
        angle = (coil / 15) * 4 * math.pi
        cx = spx + 18 * math.cos(angle)
        cz = spz + 18 * math.sin(angle)
        add(f"Feder_{si+1}_Windung_{coil+1:02d}",
            cyl(6, 30, cx, 30 + coil * 44, cz), (0.55,0.58,0.62))
    add(f"Feder_{si+1}_Oberteller",  cyl(32, 8, spx, 680, spz), (0.60,0.62,0.65))
    add(f"Feder_{si+1}_Untertasse",  cyl(32, 8, spx,  28, spz), (0.60,0.62,0.65))
    add(f"Feder_{si+1}_Antivibrpad", cyl(35, 6, spx,  22, spz), (0.20,0.20,0.22))
    add(f"Feder_{si+1}_Haengeoese",  cyl(10,20, spx, 692, spz), (0.65,0.67,0.70))

# Stoßdämpfer (2 × 6 Teile)
for di, (dpx, dpz) in enumerate([(160, 380), (440, 380)]):
    add(f"Daempfer_{di+1}_Zylinder",  cyl(18,180, dpx, 50,  dpz), (0.45,0.47,0.50))
    add(f"Daempfer_{di+1}_Kolbenstange",cyl(9,140, dpx, 210, dpz), (0.70,0.72,0.75))
    add(f"Daempfer_{di+1}_Kolben",    cyl(16, 20, dpx, 195, dpz), (0.55,0.57,0.60))
    add(f"Daempfer_{di+1}_Oeldichtung",cyl(11,  8, dpx, 228, dpz), (0.20,0.22,0.25))
    add(f"Daempfer_{di+1}_Oese_Unten",cyl(10, 20, dpx, 40,  dpz), (0.60,0.62,0.65))
    add(f"Daempfer_{di+1}_Oese_Oben", cyl(10, 20, dpx, 350, dpz), (0.60,0.62,0.65))

# ══════════════════════════════════════════════════════════════════════════════
# 8  STEUERPLATINEN & ELEKTRONIK  (~550 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[8/11] Elektronik ...\n")

# Hauptplatine
add("Platine_Haupt_PCB", box(200, 3, 280, 380, 760, 600), (0.10,0.35,0.10))

# SMD-Komponenten auf Hauptplatine (150 Stück)
comp_colors = {
    "IC": (0.15,0.15,0.18), "Cap": (0.80,0.65,0.10),
    "Res": (0.65,0.40,0.10), "Diode": (0.60,0.10,0.10),
    "Conn": (0.25,0.28,0.80)
}
comp_types = ["IC","Cap","Res","Diode","Conn"]
for ci in range(150):
    cx2 = 385 + (ci % 15) * 13
    cz2 = 605 + (ci // 15) * 18
    ct = comp_types[ci % 5]
    csize = {"IC":(8,3,8),"Cap":(4,5,4),"Res":(5,2,3),"Diode":(3,2,6),"Conn":(10,8,6)}[ct]
    add(f"Haupt_PCB_{ct}_{ci+1:03d}",
        box(*csize, cx2, 763, cz2), comp_colors[ct])

# Motorsteuerungsmodul
add("Platine_Motor_PCB", box(140, 3, 180, 60, 760, 620), (0.10,0.35,0.10))
for ci in range(80):
    cx2 = 65 + (ci % 10) * 13
    cz2 = 625 + (ci // 10) * 16
    ct = comp_types[ci % 5]
    csize = {"IC":(8,3,8),"Cap":(4,5,4),"Res":(5,2,3),"Diode":(3,2,6),"Conn":(10,8,6)}[ct]
    add(f"Motor_PCB_{ct}_{ci+1:02d}",
        box(*csize, cx2, 763, cz2), comp_colors[ct])

# Bedienfeld-Platine
add("Platine_Bedien_PCB", box(500, 3, 80, 50, 870, 500), (0.10,0.35,0.10))
for ci in range(60):
    add(f"Bedien_PCB_Komp_{ci+1:02d}",
        box(6, 4, 5, 60 + ci * 8, 873, 505), comp_colors[comp_types[ci % 5]])

# Display-Modul (5 Teile)
add("Display_Gehaeuse",    box(80, 12, 40, 380, 868, 510), (0.25,0.27,0.30))
add("Display_Glas",        box(72,  4, 32, 384, 878, 514), (0.55,0.70,0.90))
add("Display_Hintergrund", box(70,  2, 30, 385, 876, 515), (0.10,0.10,0.12))
add("Display_Stecker",     box(20, 10, 10, 425, 864, 520), (0.25,0.28,0.30))
add("Display_Kabel",       cyl( 3, 60,  425, 862, 520), (0.15,0.15,0.18))

# Drehregler (3 Stück, je 4 Teile)
for ki in range(3):
    kx2 = 100 + ki * 70
    add(f"Drehregler_{ki+1}_Kappe",   cyl(15,  8, kx2, 880, 520), (0.20,0.22,0.25))
    add(f"Drehregler_{ki+1}_Koerper", cyl(12, 14, kx2, 868, 520), (0.30,0.32,0.35))
    add(f"Drehregler_{ki+1}_Welle",   cyl( 4, 10, kx2, 866, 520), (0.55,0.57,0.60))
    add(f"Drehregler_{ki+1}_Platine", box(20,  3, 20, kx2-10, 862, 510), (0.10,0.35,0.10))

# Drucktasten (8 × 3 Teile)
for bi in range(8):
    bx2 = 250 + bi * 32
    add(f"Taste_{bi+1}_Kappe",   box(18, 6, 12, bx2, 880, 520), (0.20,0.22,0.25))
    add(f"Taste_{bi+1}_Koerper", box(16, 10,10, bx2+1, 872, 521), (0.30,0.32,0.35))
    add(f"Taste_{bi+1}_Feder",   cyl( 3, 6, bx2+9, 868, 526), (0.35,0.37,0.40))

# Steckverbinder auf Platinen (20 Stück)
for ci2 in range(20):
    add(f"Stecker_{ci2+1:02d}", box(15, 12, 8, 60+ci2*28, 758, 610), (0.25,0.28,0.80))

# ══════════════════════════════════════════════════════════════════════════════
# 9  WASCHMITTELSCHUBLADE  (~40 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[9/11] Waschmittelschublade ...\n")

add("Schublade_Gehaeuse",   box(195, 80, 100, 380, 820, 680), (0.88,0.88,0.90))
add("Schublade_Koerper",    box(185, 70, 90,  385, 822, 685), (0.92,0.92,0.94))
add("Schublade_Griff",      box(185,  8, 18,  385, 818, 676), (0.78,0.78,0.80))
add("Schublade_Kammer_1",   box( 55, 65, 85,  388, 824, 688), (0.90,0.90,0.92))
add("Schublade_Kammer_2",   box( 55, 65, 85,  450, 824, 688), (0.90,0.90,0.92))
add("Schublade_Kammer_3",   box( 55, 65, 85,  512, 824, 688), (0.90,0.90,0.92))
add("Schublade_Trennwand_1",box(  3, 65, 85,  445, 824, 688), (0.80,0.80,0.82))
add("Schublade_Trennwand_2",box(  3, 65, 85,  507, 824, 688), (0.80,0.80,0.82))

# Heberrohr-Siphon (5 Teile)
add("Siphon_Koerper",  cyl(12, 60, 450, 820, 720), (0.75,0.77,0.80))
add("Siphon_Heberrohr",cyl( 6, 55, 450, 822, 720), (0.88,0.88,0.90))
add("Siphon_Dichtung", cyl(13,  4, 450, 818, 720), (0.20,0.20,0.22))
add("Siphon_Kappe",    cyl(14,  8, 450, 878, 720), (0.82,0.82,0.85))
add("Siphon_Feder",    cyl( 5, 40, 450, 830, 720), (0.35,0.37,0.40))

add("Schublade_Fuehrung_Links",  box(  6, 80, 95, 380, 820, 684), (0.60,0.62,0.65))
add("Schublade_Fuehrung_Rechts", box(  6, 80, 95, 569, 820, 684), (0.60,0.62,0.65))
add("Schublade_Wasserverteiler", box(180, 10, 15, 387, 900, 680), (0.70,0.72,0.75))
add("Schublade_Duese_1",         cyl( 4, 15, 420, 908, 688), (0.45,0.47,0.50))
add("Schublade_Duese_2",         cyl( 4, 15, 480, 908, 688), (0.45,0.47,0.50))
add("Schublade_Duese_3",         cyl( 4, 15, 540, 908, 688), (0.45,0.47,0.50))

for si2 in range(8):
    add(f"Schublade_Schraube_{si2+1}", cyl(2, 12, 390+si2*24, 818, 780), (0.65,0.65,0.68))
for i in range(5):
    add(f"Schublade_Clip_{i+1}", box(8, 5, 8, 395+i*40, 820, 682), (0.25,0.28,0.30))

# ══════════════════════════════════════════════════════════════════════════════
# 10  KABELBAUM  (~500 Teile)
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[10/11] Kabelbaum ...\n")

# Haupt-Kabelstamm (20 Segmente)
for seg in range(20):
    add(f"Kabel_Stamm_{seg+1:02d}", cyl(8, 50, 50, 40+seg*38, 560), (0.12,0.12,0.15))

# Kabelbäume zu Baugruppen (je 8 Segmente)
branches = [
    ("Motor",     [(300, 545+i*35, 450) for i in range(8)]),
    ("Pumpe",     [(100+i*12, 48, 200) for i in range(8)]),
    ("Heizung",   [(270+i*8, 22, 440) for i in range(8)]),
    ("Ventil",    [(50+i*15, 30+i*10, 790) for i in range(8)]),
    ("Tuerschloss",[(480+i*3, 20+i*5, 430) for i in range(8)]),
    ("Sensoren",  [(295+i*2, 25, 460+i*5) for i in range(8)]),
]
for bname, positions in branches:
    for si, (bx, by, bz) in enumerate(positions):
        add(f"Kabel_{bname}_Seg_{si+1}", cyl(3, 40, bx, by, bz), (0.12,0.12,0.15))

# Kabelbinder (100 Stück)
for ki in range(100):
    kx = 50 + (ki % 10) * 55
    kz = 50 + (ki // 10) * 85
    add(f"Kabelbinder_{ki+1:03d}", box(4, 2, 18, kx, 45, kz), (0.25,0.28,0.30))

# Kabelclips (80 Stück)
for ki in range(80):
    kx = 30 + (ki % 8) * 72
    kz = 30 + (ki // 8) * 110
    add(f"Kabelclip_{ki+1:02d}", box(12, 6, 8, kx, 50, kz), (0.28,0.30,0.35))

# Steckergehäuse (30 Stück)
for ci in range(30):
    cx = 50 + (ci % 6) * 95
    cz = 50 + (ci // 6) * 140
    add(f"Steckergehaeuse_{ci+1:02d}", box(18, 12, 12, cx, 55, cz), (0.25,0.28,0.80))

# Steckerpins (150 Stück)
for pi in range(150):
    px = 55 + (pi % 15) * 38
    pz = 55 + (pi // 15) * 55
    add(f"Steckerpin_{pi+1:03d}", cyl(1, 8, px, 58, pz), (0.75,0.72,0.20))

# Schrumpfschläuche (50 Stück)
for si in range(50):
    sx2 = 50 + (si % 10) * 55
    sz2 = 50 + (si // 10) * 165
    add(f"Schrumpfschlauch_{si+1:02d}", cyl(4, 20, sx2, 42, sz2), (0.20,0.20,0.22))

# Massepunkte (10 Stück)
for gi in range(10):
    add(f"Massepunkt_{gi+1:02d}", cyl(6, 4, 25, 50+gi*90, 20), (0.72,0.72,0.10))

# ══════════════════════════════════════════════════════════════════════════════
# 11  BEFESTIGUNGSMITTEL  (Schrauben · Muttern · Scheiben)  → Hauptvolumen
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("[11/11] Befestigungsmittel (Masse) ...\n")

# M3-Schrauben (PCB, Kleinhalter) — 1 000 Stück
for i in range(1000):
    gx = 25 + (i % 40) * 14
    gz = 10 + (i // 40) * 20
    add(f"M3_Schraube_{i+1:04d}", cyl(1.5, 10, gx, 0, gz), (0.72,0.72,0.75))

# M4-Schrauben (Verkleidung, Halter) — 1 500 Stück
for i in range(1500):
    gx = 20 + (i % 50) * 11
    gz = 10 + (i // 50) * 16
    add(f"M4_Schraube_{i+1:04d}", cyl(2, 14, gx, 0, gz), (0.70,0.70,0.73))

# M5-Schrauben (Hauptrahmen) — 1 000 Stück
for i in range(1000):
    gx = 20 + (i % 40) * 15
    gz = 10 + (i // 40) * 22
    add(f"M5_Schraube_{i+1:04d}", cyl(2.5, 18, gx, 0, gz), (0.68,0.68,0.71))

# M6-Schrauben/-Bolzen (Trommel, Motor) — 800 Stück
for i in range(800):
    gx = 20 + (i % 40) * 15
    gz = 10 + (i // 40) * 22
    add(f"M6_Schraube_{i+1:04d}", cyl(3, 22, gx, 0, gz), (0.66,0.66,0.69))

# M8-Bolzen (Gegengewichte, Hauptstruktur) — 500 Stück
for i in range(500):
    gx = 20 + (i % 25) * 22
    gz = 10 + (i // 25) * 30
    add(f"M8_Bolzen_{i+1:04d}", cyl(4, 30, gx, 0, gz), (0.64,0.64,0.67))

# M10-Bolzen (Füße, Hauptlager) — 200 Stück
for i in range(200):
    gx = 20 + (i % 20) * 28
    gz = 10 + (i // 20) * 38
    add(f"M10_Bolzen_{i+1:03d}", cyl(5, 40, gx, 0, gz), (0.62,0.62,0.65))

# M4-Muttern — 1 500 Stück
for i in range(1500):
    gx = 20 + (i % 50) * 11
    gz = 10 + (i // 50) * 16
    add(f"M4_Mutter_{i+1:04d}", cyl(4, 4, gx, -6, gz), (0.60,0.62,0.65))

# M6-Muttern — 600 Stück
for i in range(600):
    gx = 20 + (i % 30) * 20
    gz = 10 + (i // 30) * 26
    add(f"M6_Mutter_{i+1:04d}", cyl(5, 5, gx, -8, gz), (0.60,0.62,0.65))

# M8-Muttern — 500 Stück
for i in range(500):
    gx = 20 + (i % 25) * 22
    gz = 10 + (i // 25) * 30
    add(f"M8_Mutter_{i+1:04d}", cyl(6.5, 6, gx, -10, gz), (0.58,0.60,0.63))

# M4-Unterlegscheiben — 500 Stück
for i in range(500):
    gx = 20 + (i % 25) * 22
    gz = 10 + (i // 25) * 30
    add(f"M4_Scheibe_{i+1:04d}", cyl(6, 1.5, gx, -14, gz), (0.68,0.70,0.73))

# M6-Unterlegscheiben — 200 Stück
for i in range(200):
    gx = 20 + (i % 20) * 28
    gz = 10 + (i // 20) * 38
    add(f"M6_Scheibe_{i+1:03d}", cyl(9, 2, gx, -16, gz), (0.68,0.70,0.73))

# Federringe M4 — 300 Stück
for i in range(300):
    gx = 20 + (i % 20) * 28
    gz = 10 + (i // 20) * 38
    add(f"M4_Federring_{i+1:03d}", torus(4, 1.2, gx, -18, gz), (0.55,0.57,0.60))

# Federringe M6 — 200 Stück
for i in range(200):
    gx = 20 + (i % 20) * 28
    gz = 10 + (i // 20) * 38
    add(f"M6_Federring_{i+1:03d}", torus(6, 1.5, gx, -20, gz), (0.55,0.57,0.60))

# Kunststoffclips (Kabelführung, Schläuche) — 300 Stück
for i in range(300):
    gx = 20 + (i % 20) * 28
    gz = 10 + (i // 20) * 38
    add(f"Kunststoffclip_{i+1:03d}", box(10, 6, 10, gx, -24, gz), (0.25,0.30,0.35))

# Blindnieten — 270 Stück
for i in range(270):
    gx = 20 + (i % 18) * 32
    gz = 10 + (i // 18) * 42
    add(f"Blindniet_{i+1:03d}", cyl(3, 14, gx, -28, gz), (0.65,0.67,0.70))

# ══════════════════════════════════════════════════════════════════════════════
# Abschluss
# ══════════════════════════════════════════════════════════════════════════════
App.Console.PrintMessage("\nRecompute ...\n")
doc.recompute()

save_path = os.path.join(os.path.expanduser("~"), "Waschmaschine_10000.FCStd")
doc.saveAs(save_path)

total = counter[0]
App.Console.PrintMessage(f"\n{'='*50}\n")
App.Console.PrintMessage(f"  FERTIG: {total} Bauteile erstellt\n")
App.Console.PrintMessage(f"  Gespeichert: {save_path}\n")
App.Console.PrintMessage(f"{'='*50}\n")
