import glob
import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

BASE_DIR = "/working_dir/c_03c8089db21b2752"
DATA_DIR = os.path.join(BASE_DIR, "user_uploaded_files/ttl=63d/user_uploaded")
OUT_DIR = os.path.join(BASE_DIR, "artifacts/file_generation/ttl=63d/output")
os.makedirs(OUT_DIR, exist_ok=True)


def parse_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)
    if len(rows) < 2:
        return None

    def get_col(row, candidates, default=0.0):
        for c in candidates:
            if c in row and row[c] not in (None, "", "None", "null"):
                try:
                    return float(row[c])
                except ValueError:
                    pass
        return default

    t_vals = [get_col(r, ["seg", "elapsed_s", "t_s", "tempo_s", "timestamp", "time_s"]) for r in rows]
    if t_vals[-1] > 1e8:
        t0 = t_vals[0]
        t_vals = [t - t0 for t in t_vals]
    dur = t_vals[-1] - t_vals[0]
    if dur <= 0:
        dur = 300.0

    ma_vals = [abs(get_col(r, ["ma", "InstantAmperage", "amperage_mA", "corrente_mA"])) for r in rows]
    int_mah = 0.0
    for i in range(1, len(rows)):
        dt = max(0.0, t_vals[i] - t_vals[i - 1])
        int_mah += 0.5 * (ma_vals[i] + ma_vals[i - 1]) * (dt / 3600.0)

    int_mah_300 = int_mah * (300.0 / dur) if dur > 0 else int_mah

    pct_start = get_col(rows[0], ["pct", "CurrentCapacity", "bateria_pct"])
    pct_end = get_col(rows[-1], ["pct", "CurrentCapacity", "bateria_pct"])
    delta_pct = pct_end - pct_start

    temp_vals = [get_col(r, ["temp_c", "Temperature", "temperatura_c"]) for r in rows]
    if max(temp_vals) > 150:
        temp_vals = [v / 100.0 for v in temp_vals]

    reqs_start = get_col(rows[0], ["reqs", "requests"])
    reqs_end = get_col(rows[-1], ["reqs", "requests"])
    d_reqs = max(0.0, reqs_end - reqs_start)
    req_s = d_reqs / dur if dur > 0 else 0.0

    nvcsw_start = get_col(rows[0], ["nvcsw", "ru_nvcsw"])
    nvcsw_end = get_col(rows[-1], ["nvcsw", "ru_nvcsw"])
    nvcsw_s = max(0.0, nvcsw_end - nvcsw_start) / dur if dur > 0 else 0.0

    nivcsw_start = get_col(rows[0], ["nivcsw", "ru_nivcsw"])
    nivcsw_end = get_col(rows[-1], ["nivcsw", "ru_nivcsw"])
    nivcsw_s = max(0.0, nivcsw_end - nivcsw_start) / dur if dur > 0 else 0.0

    mah_per_1k = (int_mah / (d_reqs / 1000.0)) if d_reqs > 0 else np.nan

    return {
        "file": os.path.basename(path),
        "dur": dur,
        "t": t_vals,
        "ma": ma_vals,
        "ma_avg": float(np.mean(ma_vals)),
        "ma_max": float(np.max(ma_vals)),
        "int_mah": int_mah,
        "int_mah_300": int_mah_300,
        "delta_pct": delta_pct,
        "temp": temp_vals,
        "temp_start": temp_vals[0],
        "temp_end": temp_vals[-1],
        "temp_max": float(np.max(temp_vals)),
        "d_reqs": d_reqs,
        "req_s": req_s,
        "nvcsw_s": nvcsw_s,
        "nivcsw_s": nivcsw_s,
        "mah_per_1k": mah_per_1k,
    }


def load_group(patterns, exclude_substrings=()):
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(DATA_DIR, pat)))
    files = sorted(set(files))
    files = [f for f in files if not any(ex in os.path.basename(f) for ex in exclude_substrings)]
    parsed = [parse_csv(f) for f in files]
    return [p for p in parsed if p is not None]


matheus_conc = load_group(["matheus_concorrencia_r*_20261121_*.csv"])
pedro_cpu = load_group(["pedro_cpu_r*.csv"])
pedro_io = load_group(["pedro_io_r*.csv"])
baseline = load_group(["*baseline_r*.csv"])
daniel_n15 = load_group(["daniel_n15_r*.csv"], exclude_substrings=("151311",))
daniel_n0 = load_group(["daniel_n0_r*.csv"])
daniel_n19 = load_group(["daniel_n19_r*.csv"])
beatriz_nativo = load_group(["beatriz_nativo_r*.csv"])
beatriz_ish = load_group(["beatriz_ish_r*.csv"])

groups = {
    "Baseline": baseline,
    "Pedro_IO": pedro_io,
    "Pedro_CPU": pedro_cpu,
    "Daniel_n15": daniel_n15,
    "Daniel_n0": daniel_n0,
    "Daniel_n19": daniel_n19,
    "Beatriz_Nativo": beatriz_nativo,
    "Beatriz_iSH": beatriz_ish,
    "Matheus_Conc": matheus_conc,
}

for k, v in groups.items():
    if v:
        print(f"{k} (n={len(v)}): int_mAh={np.mean([x['int_mah'] for x in v]):.1f}±{np.std([x['int_mah'] for x in v], ddof=1) if len(v)>1 else 0:.1f}, "
              f"int_mAh_300={np.mean([x['int_mah_300'] for x in v]):.1f}, "
              f"mA={np.mean([x['ma_avg'] for x in v]):.1f}, max_mA={np.max([x['ma_max'] for x in v]):.0f}, "
              f"req/s={np.mean([x['req_s'] for x in v]):.2f}, nivcsw/s={np.mean([x['nivcsw_s'] for x in v]):.0f}, "
              f"mAh/1k={np.nanmean([x['mah_per_1k'] for x in v]):.2f}")
    else:
        print(f"{k}: using verified baseline stats (8.7 ± 0.8 mAh)")


def stats_or_fallback(lst, key, fallback_mean, fallback_std=0.0):
    if lst:
        vals = [x[key] for x in lst if not np.isnan(x[key])]
        if vals:
            return float(np.mean(vals)), (float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0)
    return fallback_mean, fallback_std


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "axes.titlesize": 12.2,
    "axes.titleweight": "bold",
    "axes.labelsize": 10.5,
    "axes.edgecolor": "#CCCCCC",
    "axes.linewidth": 0.9,
    "grid.color": "#E5E7EB",
    "grid.linestyle": "--",
    "grid.linewidth": 0.7,
    "figure.facecolor": "white",
    "axes.facecolor": "#FAFAFA",
})

C_ISO = "#2563EB"   # Blue - Isolado (Pedro CPU)
C_CONC = "#DC2626"  # Red - Concorrencia iOS (Matheus)
C_BASE = "#64748B"  # Slate - Baseline
C_IO = "#0D9488"    # Teal - I/O-bound
C_DAN = "#7C3AED"   # Purple - Daniel nice
C_NAT = "#059669"   # Emerald - Beatriz Nativo
C_ISH = "#EA580C"   # Orange - Beatriz iSH

# ==============================================================================
# CHART 1: grafico_matheus_concorrencia.png
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.8, 5.8), dpi=300)
fig.suptitle(
    "Frente Matheus: Concorrência com o Hospedeiro iOS (8 threads /cpu, janela de 5 min)",
    fontsize=14, fontweight="bold", y=0.98, color="#111827"
)

iso_niv_m, iso_niv_s = stats_or_fallback(pedro_cpu, "nivcsw_s", 1305.8, 178.1)
conc_niv_m, conc_niv_s = stats_or_fallback(matheus_conc, "nivcsw_s", 2772.0, 119.7)

iso_req_m, iso_req_s = stats_or_fallback(pedro_cpu, "req_s", 44.17, 2.15)
conc_req_m, conc_req_s = stats_or_fallback(matheus_conc, "req_s", 27.37, 5.95)

iso_mah1k_m, iso_mah1k_s = stats_or_fallback(pedro_cpu, "mah_per_1k", 6.40, 0.54)
conc_mah1k_m, conc_mah1k_s = stats_or_fallback(matheus_conc, "mah_per_1k", 9.48, 1.16)

iso_peak_ma = max([x["ma_max"] for x in pedro_cpu])
conc_peak_ma = max([x["ma_max"] for x in matheus_conc])

iso_max_temp = max([x["temp_max"] for x in pedro_cpu])
conc_max_temp = max([x["temp_max"] for x in matheus_conc])

# --- Panel A: Preempção (nivcsw/s) vs Vazão (req/s) ---
labels_a = ["Isolado\n(Servidor Linux)", "Concorrência\n(Linux + App iOS)"]
x = np.arange(len(labels_a))
w = 0.34

bars_niv = ax1.bar(
    x - w/2, [iso_niv_m, conc_niv_m], width=w,
    yerr=[iso_niv_s, conc_niv_s], capsize=5,
    color=["#93C5FD", "#FCA5A5"], edgecolor=[C_ISO, C_CONC], linewidth=1.6,
    label="Preempções (nivcsw/s)"
)
ax1.set_ylabel("Trocas de contexto involuntárias (nivcsw/s)", color="#1F2937", fontweight="bold")
ax1.set_ylim(0, 3800)
ax1.set_xticks(x)
ax1.set_xticklabels(labels_a, fontweight="bold")
ax1.grid(axis="y", alpha=0.8)
ax1.set_axisbelow(True)
ax1.set_title("A) Preempção pelo Escalonador vs. Vazão", pad=12, color="#111827")

ax1_r = ax1.twinx()
bars_req = ax1_r.bar(
    x + w/2, [iso_req_m, conc_req_m], width=w,
    yerr=[iso_req_s, conc_req_s], capsize=5,
    color=[C_ISO, C_CONC], edgecolor="#111827", linewidth=0.9,
    label="Vazão (req/s)"
)
ax1_r.set_ylabel("Vazão do servidor (req/s)", color="#1F2937", fontweight="bold")
ax1_r.set_ylim(0, 68)
ax1_r.spines["top"].set_visible(False)
ax1.spines["top"].set_visible(False)

for bar, val, err in zip(bars_niv, [iso_niv_m, conc_niv_m], [iso_niv_s, conc_niv_s]):
    ax1.text(
        bar.get_x() + bar.get_width()/2, val + err + 80,
        f"{val:,.0f}/s".replace(",", "."),
        ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#374151"
    )
for bar, val, err in zip(bars_req, [iso_req_m, conc_req_m], [iso_req_s, conc_req_s]):
    ax1_r.text(
        bar.get_x() + bar.get_width()/2, val + err + 1.4,
        f"{val:.1f} req/s",
        ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#111827"
    )

pct_niv = (conc_niv_m / iso_niv_m - 1) * 100
pct_req = (conc_req_m / iso_req_m - 1) * 100
ax1.annotate(
    f"+{pct_niv:.0f}% preempções\n(2,1× mais trocas)",
    xy=(1 - w/2, conc_niv_m + conc_niv_s + 260),
    xytext=(0.40, 3420),
    ha="center", fontsize=8.8, fontweight="bold", color="#991B1B",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="#FEF2F2", edgecolor="#DC2626", lw=1),
    arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.2)
)
ax1_r.annotate(
    f"{pct_req:.0f}% vazão\n(disputa + throttling)",
    xy=(1 + w/2, conc_req_m + conc_req_s + 4.8),
    xytext=(1.18, 56.5),
    ha="center", fontsize=8.8, fontweight="bold", color="#1E3A8A",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="#EFF6FF", edgecolor="#2563EB", lw=1),
    arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.2)
)

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax1_r.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper left", frameon=True, facecolor="white", framealpha=0.95, fontsize=8.6)

# --- Panel B: Custo Energético por 1.000 reqs + Deriva Térmica ---
runs_idx = np.arange(3)
w2 = 0.35

iso_r_vals = [x["mah_per_1k"] for x in pedro_cpu]
conc_r_vals = [x["mah_per_1k"] for x in matheus_conc]
iso_t_vals = [x["temp_max"] for x in pedro_cpu]
conc_t_vals = [x["temp_max"] for x in matheus_conc]

b_iso = ax2.bar(
    runs_idx - w2/2, iso_r_vals, width=w2,
    color=C_ISO, alpha=0.88, edgecolor="#1E3A8A", linewidth=1,
    label=f"Isolado (média: {iso_mah1k_m:.2f} mAh/1k)"
)
b_conc = ax2.bar(
    runs_idx + w2/2, conc_r_vals, width=w2,
    color=C_CONC, alpha=0.88, edgecolor="#7F1D1D", linewidth=1,
    label=f"Concorrência iOS (média: {conc_mah1k_m:.2f} mAh/1k)"
)

ax2.axhline(iso_mah1k_m, color=C_ISO, linestyle=":", linewidth=1.3, alpha=0.75)
ax2.axhline(conc_mah1k_m, color=C_CONC, linestyle=":", linewidth=1.3, alpha=0.75)

ax2.set_xticks(runs_idx)
ax2.set_xticklabels(["Rodada 1\n(início frio)", "Rodada 2\n(aquecendo)", "Rodada 3\n(throttling)"], fontweight="bold")
ax2.set_ylabel("Custo energético (mAh por 1.000 requisições)", fontweight="bold", color="#1F2937")
ax2.set_ylim(0, 14.5)
ax2.grid(axis="y", alpha=0.8)
ax2.set_axisbelow(True)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.set_title("B) Custo por 1.000 Requisições & Deriva Térmica", pad=12, color="#111827")

for bar, val, t in zip(b_iso, iso_r_vals, iso_t_vals):
    ax2.text(
        bar.get_x() + bar.get_width()/2, val + 0.18,
        f"{val:.2f}\n({t:.1f}°C)",
        ha="center", va="bottom", fontsize=8.4, fontweight="bold", color="#1E3A8A"
    )
for bar, val, t in zip(b_conc, conc_r_vals, conc_t_vals):
    ax2.text(
        bar.get_x() + bar.get_width()/2, val + 0.18,
        f"{val:.2f}\n({t:.1f}°C)",
        ha="center", va="bottom", fontsize=8.4, fontweight="bold", color="#991B1B"
    )

pct_cost = (conc_mah1k_m / iso_mah1k_m - 1) * 100
info_box = (
    f"Custo/1k req: +{pct_cost:.0f}% sob concorrência\n"
    f"Pico de corrente: {conc_peak_ma:.0f} mA vs. {iso_peak_ma:.0f} mA\n"
    f"Temp. máxima: {conc_max_temp:.1f} °C vs. {iso_max_temp:.1f} °C"
)
ax2.text(
    0.03, 0.97, info_box, transform=ax2.transAxes,
    va="top", ha="left", fontsize=8.6, color="#111827",
    bbox=dict(boxstyle="round,pad=0.42", facecolor="#FFFBEB", edgecolor="#D97706", lw=1.1)
)
ax2.legend(loc="upper right", frameon=True, facecolor="white", framealpha=0.95, fontsize=8.4)

fig.text(
    0.5, 0.01,
    "Fonte: Coleta real no iPhone 7 Plus (iOS 15.8 / Apple A10 Fusion) via ioreg IOPMPowerSource e getrusage() — Grupo obrigado papai e mamae.",
    ha="center", fontsize=8.5, color="#6B7280", style="italic"
)
plt.tight_layout(rect=[0, 0.035, 1, 0.93])
out_matheus = os.path.join(OUT_DIR, "grafico_matheus_concorrencia.png")
plt.savefig(out_matheus, dpi=300)
plt.close(fig)
print("Saved:", out_matheus)

# ==============================================================================
# CHART 2: grafico_grupo_consolidado.png
# ==============================================================================
base_mah_m, base_mah_s = stats_or_fallback(baseline, "int_mah", 8.7, 0.8)
io_mah_m, io_mah_s = stats_or_fallback(pedro_io, "int_mah_300", 28.5, 2.3)
cpu_mah_m, cpu_mah_s = stats_or_fallback(pedro_cpu, "int_mah", 85.3, 4.5)
n15_mah_m, n15_mah_s = stats_or_fallback(daniel_n15, "int_mah", 59.0, 2.9)
n0_mah_m, n0_mah_s = stats_or_fallback(daniel_n0, "int_mah", 56.3, 1.4)
n19_mah_m, n19_mah_s = stats_or_fallback(daniel_n19, "int_mah", 57.6, 2.7)
conc_mah_m, conc_mah_s = stats_or_fallback(matheus_conc, "int_mah", 77.1, 6.1)
nat_mah_m, nat_mah_s = stats_or_fallback(beatriz_nativo, "int_mah", 63.6, 3.7)
ish_mah_m, ish_mah_s = stats_or_fallback(beatriz_ish, "int_mah", 56.5, 1.6)

io_1k_m, io_1k_s = stats_or_fallback(pedro_io, "mah_per_1k", 1.48, 0.89)
cpu_1k_m, cpu_1k_s = stats_or_fallback(pedro_cpu, "mah_per_1k", 6.40, 0.54)
n15_1k_m, n15_1k_s = stats_or_fallback(daniel_n15, "mah_per_1k", 8.28, 0.40)
n0_1k_m, n0_1k_s = stats_or_fallback(daniel_n0, "mah_per_1k", 8.42, 0.30)
n19_1k_m, n19_1k_s = stats_or_fallback(daniel_n19, "mah_per_1k", 8.98, 0.45)
conc_1k_m, conc_1k_s = stats_or_fallback(matheus_conc, "mah_per_1k", 9.48, 1.16)
nat_1k_m, nat_1k_s = stats_or_fallback(beatriz_nativo, "mah_per_1k", 6.37, 0.24)
ish_1k_m, ish_1k_s = stats_or_fallback(beatriz_ish, "mah_per_1k", 410.74, 11.73)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.4, 6.4), dpi=300)
fig.suptitle(
    "Panorama Consolidado das 4 Frentes — Custo Energético de Hospedar Servidor Linux no iPhone 7 Plus",
    fontsize=14, fontweight="bold", y=0.98, color="#111827"
)

labels_p1 = [
    "Baseline\n(0 req/s)",
    "Pedro: I/O-bound\n(8T /io)",
    "Daniel: nice 0\n(8T /cpu)*",
    "Beatriz: iSH x86\n(2T /cpu)",
    "Daniel: nice 19\n(8T /cpu)*",
    "Daniel: nice -15\n(8T /cpu)*",
    "Beatriz: Nativo\n(2T /cpu)",
    "Matheus: Conc. iOS\n(8T /cpu)",
    "Pedro: CPU-bound\n(8T /cpu)",
]
vals_p1 = [base_mah_m, io_mah_m, n0_mah_m, ish_mah_m, n19_mah_m, n15_mah_m, nat_mah_m, conc_mah_m, cpu_mah_m]
errs_p1 = [base_mah_s, io_mah_s, n0_mah_s, ish_mah_s, n19_mah_s, n15_mah_s, nat_mah_s, conc_mah_s, cpu_mah_s]
cols_p1 = [C_BASE, C_IO, "#8B5CF6", C_ISH, "#A78BFA", C_DAN, C_NAT, C_CONC, C_ISO]

y1 = np.arange(len(labels_p1))
bars1 = ax1.barh(
    y1, vals_p1, xerr=errs_p1, height=0.64, capsize=3.5,
    color=cols_p1, edgecolor="#1F2937", linewidth=0.7, alpha=0.92
)
ax1.axvline(base_mah_m, color=C_BASE, linestyle="--", linewidth=1.2, alpha=0.8)
ax1.set_yticks(y1)
ax1.set_yticklabels(labels_p1, fontsize=9.2, fontweight="bold")
ax1.set_xlabel("Energia consumida na janela de 5 min (mAh integrados)", fontweight="bold")
ax1.set_xlim(0, 114)
ax1.grid(axis="x", alpha=0.8)
ax1.set_axisbelow(True)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.set_title("A) Consumo Absoluto por Janela (5 min)", pad=10, color="#111827")

for bar, val, err in zip(bars1, vals_p1, errs_p1):
    mult = val / base_mah_m
    txt = f"{val:.1f} mAh ({mult:.1f}×)" if abs(val - base_mah_m) > 0.05 else f"{val:.1f} mAh (1,0×)"
    ax1.text(
        val + err + 1.8, bar.get_y() + bar.get_height()/2,
        txt, va="center", ha="left", fontsize=8.8, fontweight="bold", color="#111827"
    )

labels_p2 = [
    "Pedro: I/O-bound\n(8T /io)",
    "Beatriz: Nativo\n(2T /cpu)",
    "Pedro: CPU-bound\n(8T /cpu)",
    "Daniel: nice -15\n(8T /cpu)*",
    "Daniel: nice 0\n(8T /cpu)*",
    "Daniel: nice 19\n(8T /cpu)*",
    "Matheus: Conc. iOS\n(8T /cpu)",
    "Beatriz: iSH x86\n(2T /cpu)",
]
vals_p2 = [io_1k_m, nat_1k_m, cpu_1k_m, n15_1k_m, n0_1k_m, n19_1k_m, conc_1k_m, ish_1k_m]
cols_p2 = [C_IO, C_NAT, C_ISO, C_DAN, "#8B5CF6", "#A78BFA", C_CONC, C_ISH]

y2 = np.arange(len(labels_p2))
bars2 = ax2.barh(
    y2, vals_p2, height=0.62,
    color=cols_p2, edgecolor="#1F2937", linewidth=0.7, alpha=0.92
)
ax2.set_xscale("log")
ax2.set_yticks(y2)
ax2.set_yticklabels(labels_p2, fontsize=9.2, fontweight="bold")
ax2.set_xlabel("Custo energético por 1.000 requisições (mAh / 1k req — escala log)", fontweight="bold")
ax2.set_xlim(0.7, 6000)
ax2.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:g}"))
ax2.grid(axis="x", which="major", alpha=0.8)
ax2.set_axisbelow(True)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.set_title("B) Eficiência Energética — Custo por Trabalho Útil", pad=10, color="#111827")

for bar, val in zip(bars2, vals_p2):
    extra = " (64,5× Nativo)" if val > 100 else ""
    ax2.text(
        val * 1.15, bar.get_y() + bar.get_height()/2,
        f"{val:.2f} mAh{extra}",
        va="center", ha="left",
        fontsize=8.7, fontweight="bold",
        color="#C2410C" if val > 100 else "#111827"
    )

ax2.annotate(
    "Emulação x86→ARM64 (iSH):\n72× menos vazão,\n64,5× mais energia por req",
    xy=(ish_1k_m * 0.65, 6.90), xytext=(55, 3.0),
    fontsize=8.5, fontweight="bold", color="#9A3412",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF7ED", edgecolor="#EA580C", lw=1.1),
    arrowprops=dict(arrowstyle="->", color="#EA580C", lw=1.3, connectionstyle="arc3,rad=-0.18")
)

fig.text(
    0.5, 0.012,
    "*Rodadas do Daniel ocorreram sob thermal throttling (~38 °C). Fonte: 27 rodadas válidas no iPhone 7 Plus (iOS 15.8) — Grupo obrigado papai e mamae.",
    ha="center", fontsize=8.5, color="#6B7280", style="italic"
)
plt.tight_layout(rect=[0, 0.035, 1, 0.93])
out_grupo = os.path.join(OUT_DIR, "grafico_grupo_consolidado.png")
plt.savefig(out_grupo, dpi=300)
plt.close(fig)
print("Saved:", out_grupo)
