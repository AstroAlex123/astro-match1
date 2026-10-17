"""
generate_candidates.py
Fetches asteroid positions from JPL SPARK, computes each asteroid's closest
approach to the mission trajectory, runs the delta-v feasibility calc, and
writes api/candidates.json for the static site.

Run:  python scripts/generate_candidates.py
Requires: pip install pandas requests
"""
import json
import requests
import pandas as pd

# ==========================================================================
# CONFIG
# ==========================================================================
MISSION_START = "2026-01-01"
MISSION_STOP = "2026-02-01"
MISSION_STEP = "1d"
TOLERANCE_AU = 0.1                    # site's distance filter
OUTPUT_PATH = "api/candidates.json"

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
#   MUST be the same frame/units as SPARK returns, or distances are wrong
TRAJECTORY = [
    (1.0, 0.0, 0.0),
    (1.5, 0.8, 0.05),
    (2.2, 1.1, 0.08),
]

KM_PER_AU = 149_597_870.7

# ==========================================================================
# STEP 1 — fetch asteroid positions from JPL SPARK
# ==========================================================================
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
    print("Columns:", data["columns"])          # verify these first
    return pd.DataFrame(data["rows"], columns=data["columns"])

# ==========================================================================
# STEP 2 — distance from a point to the trajectory polyline
# ==========================================================================
def dist_to_polyline(pt, pts):
    min_d = float("inf")
    for a, b in zip(pts, pts[1:]):
        vx, vy, vz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        wx, wy, wz = pt[0] - a[0], pt[1] - a[1], pt[2] - a[2]
        ab = vx * vx + vy * vy + vz * vz or 1e-9
        t = max(0.0, min(1.0, (wx * vx + wy * vy + wz * vz) / ab))
        cx, cy, cz = a[0] + t * vx, a[1] + t * vy, a[2] + t * vz
        min_d = min(min_d, ((pt[0] - cx) ** 2 + (pt[1] - cy) ** 2 + (pt[2] - cz) ** 2) ** 0.5)
    return min_d

# ==========================================================================
# STEP 3 — closest approach per asteroid  ->  summary DataFrame
# ==========================================================================
def compute_distances(sbids, eph):
    rows = []
    for sbid in sbids:
        sub = eph[eph["id"] == sbid]
        d_au = sub.apply(
            lambda r: dist_to_polyline((r["x"], r["y"], r["z"]), TRAJECTORY), axis=1
        ).min()
        name, typ, diam = CATALOG[sbid]
        rows.append({
            "Asteroid": name,
            "Distance (km)": d_au * KM_PER_AU,
            "jpl_id": str(sbid),
            "type": typ,
            "diameter": diam,
        })
    return pd.DataFrame(rows)

# ==========================================================================
# STEP 4 — delta-v feasibility calc  (your existing logic)
# ==========================================================================
def delta_v_analysis(summary):
    d_spectro_km = 40000      # spectroscopy threshold (point-source NIR, V<10)
    d_imaging_km = 9800       # imaging/resolved threshold

    # Lucy-Dinkinesh anchor
    lucy_dv_ms, lucy_lead_d, lucy_gap_km = 3.4, 180, 63575
    rate = lucy_gap_km / (lucy_lead_d * lucy_dv_ms)   # km per day per m/s
    lead_times = [30, 60, 90, 120, 180, 270, 365]
    max_lead = max(lead_times)

    out = []
    for _, row in summary.iterrows():
        name = row["Asteroid"]
        d_passive_km = row["Distance (km)"]
        gap_spectro = d_passive_km - d_spectro_km

        if gap_spectro <= 0:
            relevance = "spectral"          # already in range, no delta-v
            dv_s = 0.0
        else:
            dv_s = gap_spectro / (max_lead * rate)   # best-case (longest lead)
            relevance = "spectral" if dv_s < 10 else "marginal"   # tune threshold

        gap_imaging = max(d_passive_km - d_imaging_km, 0.0)
        dv_i = gap_imaging / (max_lead * rate)

        out.append({
            "name": name,
            "jpl_id": row["jpl_id"],
            "type": row["type"],
            "diameter": row["diameter"],
            "distanceAU": d_passive_km / KM_PER_AU,
            "distance_km": round(d_passive_km),
            "relevance": relevance,
            "dv_spectro_min_ms": round(dv_s, 2),
            "dv_imaging_min_ms": round(dv_i, 2),
        })
    return out

# ==========================================================================
# MAIN
# ==========================================================================
def main():
    sbids = list(CATALOG.keys())
    eph = fetch_spark(sbids, MISSION_START, MISSION_STOP, MISSION_STEP)

    summary = compute_distances(sbids, eph)
    print("\nClosest-approach distances:")
    print(summary[["Asteroid", "Distance (km)"]].to_string(index=False))

    candidates = delta_v_analysis(summary)
    candidates = [c for c in candidates if c["distanceAU"] <= TOLERANCE_AU]
    candidates.sort(key=lambda c: c["distanceAU"])

    payload = {
        "metadata": {
            "source": "NASA JPL SPARK ephemeris (precomputed)",
            "mission_window": {"start": MISSION_START, "stop": MISSION_STOP, "step": MISSION_STEP},
            "note": "Regenerate whenever the mission timeframe/trajectory changes.",
        },
        "candidates": candidates,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote {len(candidates)} candidate(s) to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
