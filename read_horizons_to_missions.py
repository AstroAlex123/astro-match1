"""
read_horizons_to_missions.py

Reads real JUICE spacecraft trajectory from NAIF SPICE kernels and writes
data/missions.json for the ASTRA mission selector. Runs in the Codespace;
kernels download to ./kernels/ (cached between runs). spiceypy only
(this build has no ice_core C lib for pyice, and no bundled leapseconds).

Install: pip install spiceypy
Run:     python read_horizons_to_missions.py

Notes learned from this spiceypy build:
  * spkezp(targ:int, et, ref:str, abcorr:str, obs:int) -> (state, lt)
    (no kernel-handle arg; uses the furnished global pool; ids are ints).
  * The JUICE SPK stores state in km, heliocentric (observer=Sun id 10).
  * UTC->ET done by hand (no leapseconds kernel): ET = UTC + leap + 32.184 s.
"""
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta
import spiceypy as spice

KERNEL_DIR = "kernels"
OUTPUT = "data/missions.json"
BASE = "https://naif.jpl.nasa.gov/pub/naif/JUICE/kernels"
KM_PER_AU = 149_597_870.7
J2000 = datetime(2000, 1, 1, 12, 0, 0)  # UTC instant of the J2000 epoch

# TAI - UTC leap seconds (seconds), valid 1992-present.
LEAP_TABLE = [
    (datetime(1992, 7, 1), 32.0),
    (datetime(1996, 1, 1), 33.0),
    (datetime(1997, 7, 1), 34.0),
    (datetime(1999, 1, 1), 35.0),
    (datetime(2006, 1, 1), 36.0),
    (datetime(2017, 1, 1), 37.0),
]

def leap_seconds(dt):
    s = 0.0
    for d, val in LEAP_TABLE:
        if dt >= d:
            s = val
    return s

def utc_to_et_secs(dt):
    return (dt - J2000).total_seconds() + leap_seconds(dt) + 32.184

MISSIONS = {
    "JUICE": {
        "spk":  "juice_orbc_000010_230414_310721_v01.bsp",  # covers 2023-04 -> 2031-07
        "start": "2024-06-01",
        "stop":  "2024-08-01",
        "step":  1,   # days
    },
}

def _download(name, url):
    dest = os.path.join(KERNEL_DIR, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 50:
        return dest
    os.makedirs(KERNEL_DIR, exist_ok=True)
    print(f"  downloading {name} …")
    urllib.request.urlretrieve(url, dest)
    return dest

def _list(pattern, subdir):
    html = urllib.request.urlopen(f"{BASE}/{subdir}/").read().decode()
    return sorted(set(re.findall(r'href="([^"]*'+re.escape(pattern)+r'[^"]*)"', html)))

def sample_mission(cfg):
    spk = _download(cfg["spk"], f"{BASE}/spk/{cfg['spk']}")
    sclk = [_download(f, f"{BASE}/sclk/{f}") for f in _list(r"juice_step_", "sclk")]
    print(f"  SPK={cfg['spk']}  SCLK={len(sclk)} files")

    spice.furnsh(spk)
    for k in sclk:
        spice.furnsh(k)

    # JUICE body ID straight from the SPK contents (ints; the name kernel isn't furnished)
    bodies = list(spice.spkobj(spk))
    body_id = bodies[0] if bodies else None
    print(f"  SPK bodies: {bodies} -> using {body_id}")
    if body_id is None:
        raise RuntimeError("No body found in SPK")

    start = datetime.fromisoformat(cfg["start"])
    stop  = datetime.fromisoformat(cfg["stop"])
    step  = timedelta(days=cfg["step"])
    trajectory, n, dt = [], 0, start
    while dt <= stop:
        et = utc_to_et_secs(dt)
        # spkezp(target_id, et, ref, abcorr, observer_id); observer 10 = Sun (heliocentric)
        state, lt = spice.spkezp(body_id, et, "J2000", "NONE", 10)
        x, y, z = state[0], state[1], state[2]
        scale = 1.0 if abs(x) < 1000 else 1.0 / KM_PER_AU  # this SPK stores km
        trajectory.append([round(x * scale, 6), round(y * scale, 6), round(z * scale, 6)])
        if n == 0:
            dist = (x * x + y * y + z * z) ** 0.5 * scale
            print(f"  sample @ {dt.date()}: |pos|={dist:.4f} AU  (sanity: JUICE ~1 AU here)")
        dt += step
        n += 1
        if n > 3660:
            break
    spice.kclear()
    return trajectory

def main():
    out = {}
    for name, cfg in MISSIONS.items():
        print(f"Sampling {name}…")
        out[name] = {"start": cfg["start"], "stop": cfg["stop"],
                     "step": str(cfg["step"]) + "d", "trajectory": sample_mission(cfg)}
        print(f"  {len(out[name]['trajectory'])} points")
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {OUTPUT} ({len(out)} mission(s)).")

if __name__ == "__main__":
    main()


