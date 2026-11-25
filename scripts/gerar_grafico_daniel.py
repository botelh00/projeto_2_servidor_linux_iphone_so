import csv
import os
import statistics
import matplotlib.pyplot as plt
import numpy as np

IN_DIR = "/working_dir/c_03c8089db21b2752/user_uploaded_files/ttl=63d/user_uploaded"
OUT_DIR = "/working_dir/c_03c8089db21b2752/artifacts/file_generation/ttl=63d/output"
os.makedirs(OUT_DIR, exist_ok=True)

VALID = [
    ("nice -15\n(Máxima)", "daniel_n15_r1_20261119_151500.csv"),
    ("nice -15\n(Máxima)", "daniel_n15_r2_20261119_152330.csv"),
    ("nice -15\n(Máxima)", "daniel_n15_r3_20261119_153136.csv"),
    ("nice 0\n(Padrão)",   "daniel_n0_r1_20261119_153943.csv"),
    ("nice 0\n(Padrão)",   "daniel_n0_r2_20261119_154747.csv"),
    ("nice 0\n(Padrão)",   "daniel_n0_r3_20261119_155551.csv"),
    ("nice 19\n(Mínima)",  "daniel_n19_r1_20261119_160403.csv"),
    ("nice 19\n(Mínima)",  "daniel_n19_r2_20261119_161205.csv"),
    ("nice 19\n(Mínima)",  "daniel_n19_r3_20261119_162010.csv"),
]

order = ["nice -15\n(Máxima)", "nice 0\n(Padrão)", "nice 19\n(Mínima)"]
groups = {k: [] for k in order}

for grp, fname in VALID:
    with open(os.path.join(IN_DIR, fname)) as f:
        rows = list(csv.DictReader(f))
    r0, r1 = rows[0], rows[-1]
    dt = float(r1["seg"]) - float(r0["seg"])
    dpct = int(r0["pct"]) - int(r1["pct"])
    mas = [-int(r["ma"]) for r in rows]
    int_mah = sum(((-int(rows[i]["ma"]) + -int(rows[i - 1]["ma"])) / 2.0) * (float(rows[i]["seg"]) - float(rows[i - 1]["seg"])) / 3600.0 for i in range(1, len(rows)))
    dreqs = int(r1["reqs"]) - int(r0["reqs"])
    groups[grp].append({
        "dpct": dpct,
        "int_mah": int_mah,
        "ma_avg": statistics.mean(mas),
        "req_s": dreqs / dt,
        "mah_1k": int_mah / dreqs * 1000.0,
    })

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#CCCCCC",
    "axes.linewidth": 0.8,
    "grid.color": "#EAEAEA",
    "grid.linestyle": "--",
    "grid.linewidth": 0.7,
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.4), dpi=300)
fig.patch.set_facecolor("white")

x = np.arange(len(order))
colors = ["#DC2626", "#2563EB", "#0D9488"]

# Panel A: Consumo energetico (mAh integrado e % tela)
mah_means = [statistics.mean(r["int_mah"] for r in groups[k]) for k in order]
mah_stds = [statistics.stdev(r["int_mah"] for r in groups[k]) for k in order]
pct_means = [statistics.mean(r["dpct"] for r in groups[k]) for k in order]

bars1 = ax1.bar(x, mah_means, width=0.52, color=colors, yerr=mah_stds, capsize=6,
                error_kw={"elinewidth": 1.4, "ecolor": "#334155"}, zorder=3)
ax1.axhline(8.7, color="#64748B", ls=":", lw=1.3, zorder=2)
ax1.text(2.38, 10.2, "Baseline ocioso (~8,7 mAh)", ha="right", fontsize=8.5, color="#475569")

ax1.set_title("A. Consumo Energético por Prioridade (5 min)", fontsize=11.5, fontweight="bold", pad=12, color="#0F172A")
ax1.set_ylabel("Carga Consumida Integrada (mAh)", fontsize=10.5, fontweight="bold", color="#1E293B")
ax1.set_xticks(x)
ax1.set_xticklabels(order, fontsize=9.8)
ax1.set_ylim(0, 78)
ax1.yaxis.grid(True, zorder=0)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

for idx, (bar, mah, pct) in enumerate(zip(bars1, mah_means, pct_means)):
    ax1.text(bar.get_x() + bar.get_width() / 2, mah + mah_stds[idx] + 1.8,
             f"{mah:.1f} mAh\n(Δ tela: -{pct:.2f}%)",
             ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#0F172A")

# Panel B: Vazao (req/s) vs Eficiencia Energetica (mAh / 1000 req)
req_means = [statistics.mean(r["req_s"] for r in groups[k]) for k in order]
req_stds = [statistics.stdev(r["req_s"] for r in groups[k]) for k in order]
eff_means = [statistics.mean(r["mah_1k"] for r in groups[k]) for k in order]

w = 0.34
b_req = ax2.bar(x - w / 2, req_means, width=w, color="#2563EB", yerr=req_stds, capsize=4,
                error_kw={"elinewidth": 1.1, "ecolor": "#1E3A8A"}, label="Vazão (req/s) — maior é melhor", zorder=3)
ax2.set_title("B. Vazão vs. Custo por 1.000 Requisições", fontsize=11.5, fontweight="bold", pad=12, color="#0F172A")
ax2.set_ylabel("Vazão do Servidor (req/s)", fontsize=10.2, fontweight="bold", color="#1D4ED8")
ax2.set_xticks(x)
ax2.set_xticklabels(order, fontsize=9.8)
ax2.set_ylim(0, 34)
ax2.yaxis.grid(True, zorder=0)
ax2.spines["top"].set_visible(False)

ax2_r = ax2.twinx()
b_eff = ax2_r.bar(x + w / 2, eff_means, width=w, color="#F59E0B", alpha=0.92,
                  label="Custo (mAh / 1.000 req) — menor é melhor", zorder=3)
ax2_r.set_ylabel("Custo Energético (mAh / 1.000 req)", fontsize=10.2, fontweight="bold", color="#B45309")
ax2_r.set_ylim(0, 12.5)
ax2_r.spines["top"].set_visible(False)

for idx, (bar, val) in enumerate(zip(b_req, req_means)):
    ax2.text(bar.get_x() + bar.get_width() / 2, val + req_stds[idx] + 0.7, f"{val:.1f}/s",
             ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1D4ED8")
for bar, val in zip(b_eff, eff_means):
    ax2_r.text(bar.get_x() + bar.get_width() / 2, val + 0.25, f"{val:.2f}",
               ha="center", va="bottom", fontsize=9, fontweight="bold", color="#B45309")

l1, lb1 = ax2.get_legend_handles_labels()
l2, lb2 = ax2_r.get_legend_handles_labels()
ax2.legend(l1 + l2, lb1 + lb2, loc="upper left", frameon=True, facecolor="white", edgecolor="#E2E8F0", fontsize=8.5)

fig.suptitle("Frente Daniel Motta — Impacto da Prioridade de Processo (nice) sob Carga CPU-bound no iPhone 7 Plus",
             fontsize=12.8, fontweight="bold", y=0.98, color="#0F172A")
fig.text(0.5, 0.01, "Média de 3 repetições (~5 min cada, n=9 rodadas, temp. 36–38,7 °C) | Hardware: Apple A10 Fusion, iOS 15.8 (Dopamine)",
         ha="center", fontsize=8.6, color="#475569")

plt.tight_layout(rect=[0, 0.04, 1, 0.93])
out = os.path.join(OUT_DIR, "grafico_daniel_nice.png")
plt.savefig(out, dpi=300)
plt.close(fig)
print("OK:", out)
