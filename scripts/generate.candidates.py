import json, requests, pandas as pd

# ---------- config ----------
MISSION_START = "2026-01-01"
MISSION_STOP  = "2026-02-01"
MISSION_STEP  = "1d"

# candidate asteroids: SBID -> (name, type, diameter_km)
CATALOG = {
    1:  ("(1) Ceres",    "C", 940),
    4:  ("(4) Vesta",    "V", 525),
    2:  ("(2) Pallas",   "C", 512),
    10: ("(10) Hygiea",  "C", 434),
    6:  ("(6) Hebe",     "S", 237),
    3:  ("(3) Juno",     "S", 234),
}

# mission trajectory: (x, y, z) in AU, heliocentric ecliptic J2000
#   <-- MUST be the same frame as SPARK returns, or distances are wrong
TRAJECTORY = [
    (1.0, 0.0, 0.0),
    (1.5, 0.8, 0.05),
    (2.2, 1.1, 0.08),
]

KM_PER_AU = 149_597_870.7

# ---------- 1. fetch asteroid positions from JPL SPARK ----------
def fetch_spark(sbids, start, stop, step):
    url = "https://ssd-api.jpl.nasa.gov/spark_orbits.api"
    params = {
        "sbids":       ",".join(map(str, sbids)),
        "epochlo":     start,
        "epochhi":     stop,
        "step":        step,
        "elements":    "0",       # cartesian x, y, z
        "rel":         "0",       # heliocentric
        "output_json": "true",
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    print("Columns:", data["columns"])          # <-- verify these first
    return pd.DataFrame(data["rows"], columns=data["columns"])

# ---------- 2. distance from a point to the trajectory polyline ----------
def dist_to_polyline(pt, pts):
    min_d = float("inf")
    for a, b in zip(pts, pts[1:]):
        vx, vy, vz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
        wx, wy, wz = pt[0]-a[0], pt[1]-a[1], pt[2]-a[2]
        ab = vx*vx + vy*vy + vz*vz or 1e-9
        t = max(0.0, min(1.0, (wx*vx + wy*vy + vz*vz) / ab))
        cx, cy, cz = a[0]+t*vx, a[1]+t*vy, a[2]+t*vz
        min_d = min(min_d, ((pt[0]-cx)**2 + (pt[1]-cy)**2 + (pt[2]-cz)**2) ** 0.5)
    return min_d

# ---------- 3. closest approach per asteroid ----------
sbids = list(CATALOG.keys())
eph = fetch_spark(sbids, MISSION_START, MISSION_STOP, MISSION_STEP)

summary_rows = []
for sbid in sbids:
    sub = eph[eph["id"] == sbid]
    d_au = sub.apply(lambda r: dist_to_polyline((r["x"], r["y"], r["z"]), TRAJECTORY), axis=1).min()
    name, typ, diam = CATALOG[sbid]
    summary_rows.append({
        "Asteroid": name,
        "Distance (km)": d_au * KM_PER_AU,
        "jpl_id": str(sbid),
        "type": typ,
        "diameter": diam,
    })

summary = pd.DataFrame(summary_rows)
print(summary)
summary.to_csv("summary.csv", index=False)   # your delta-v code reads this
