import csv, json, re, subprocess, sys, time, urllib.request
from datetime import datetime

nome = sys.argv[1] if len(sys.argv) > 1 else "teste"
duracao = int(sys.argv[2]) if len(sys.argv) > 2 else 300
porta = int(sys.argv[3]) if len(sys.argv) > 3 else 8080
arq = f"{nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
CAMPOS = ["CurrentCapacity", "AppleRawCurrentCapacity", "InstantAmperage", "Voltage", "Temperature", "ExternalConnected"]

def bat():
    out = subprocess.check_output(["/usr/sbin/ioreg", "-rw0", "-c", "IOPMPowerSource"], text=True)
    d = {}
    for c in CAMPOS:
        m = re.search(rf'^\s*\|\s*"{c}"\s*=\s*(\S+)', out, re.M)
        val = m.group(1) if m else ""
        if c == "InstantAmperage" and val.isdigit():
            v = int(val)
            val = v - 2**64 if v >= 2**63 else v
        d[c] = val
    return d

def stats():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/stats", timeout=1) as r:
            return json.loads(r.read())
    except Exception:
        return {"reqs": 0, "nvcsw": 0, "nivcsw": 0, "cpu_user_s": 0, "cpu_sys_s": 0}

with open(arq, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ts", "seg", "pct", "mah", "ma", "mv", "temp_c", "cabo", "reqs", "nvcsw", "nivcsw", "user_s", "sys_s"])
    t0 = time.time()
    while True:
        dt = round(time.time() - t0, 1)
        b = bat()
        s = stats()
        tc = round(int(b["Temperature"]) / 100.0, 2) if str(b["Temperature"]).isdigit() else ""
        w.writerow([datetime.now().isoformat(timespec="seconds"), dt, b["CurrentCapacity"], b["AppleRawCurrentCapacity"], b["InstantAmperage"], b["Voltage"], tc, b["ExternalConnected"], s["reqs"], s["nvcsw"], s["nivcsw"], s["cpu_user_s"], s["cpu_sys_s"]])
        f.flush()
        print(f"[{dt}s] {b['CurrentCapacity']}% | {b['AppleRawCurrentCapacity']}mAh | {b['InstantAmperage']}mA | {tc}C | req={s['reqs']} | ctx={s['nvcsw']}+{s['nivcsw']}")
        if dt >= duracao:
            break
        time.sleep(5)
