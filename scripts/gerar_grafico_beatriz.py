import csv
import os
import statistics
import matplotlib.pyplot as plt
import numpy as np

IN_DIR = "/working_dir/c_03c8089db21b2752/user_uploaded_files/ttl=63d/user_uploaded"
OUT_DIR = "/working_dir/c_03c8089db21b2752/artifacts/file_generation/ttl=63d/output"
os.makedirs(OUT_DIR, exist_ok=True)

FILES = [
    ("Nativo ARM64\n(Jailbreak / XNU)", "beatriz_nativo_r1_20261121_153300.csv"),
    ("Nativo ARM64\n(Jailbreak / XNU)", "beatriz_nativo_r2_20261121_154105.csv"),
    ("Nativo ARM64\n(Jailbreak / XNU)", "beatriz_nativo_r3_20261121_154910.csv"),
    ("Emulado x86\n(iSH Usermode)",      "beatriz_ish_r1_20261121_143335.csv"),
    ("Emulado x86\n(iSH Usermode)",      "beatriz_ish_r2_20261121_144139.csv"),
    ("Emulado x86\n(iSH Usermode)",      "beatriz_ish_r3_20261121_144943.csv"),
]

order = ["Nativo ARM64\n(Jailbreak / XNU)", "Emulado x86\n(iSH Usermode)"]
groups = {k: [] for k in order}

for grp, fname in FILES:
    with open(os.path.join(IN_DIR, fname)) as f:
        rows = list(csv.DictReader(f))
    r0, r1 = rows[0], rows[-1]
    dt = float(r1["seg"]) - float(r0["seg"])
    mas = [-int(r["ma"]) for r in rows]
    int_mah = sum(((-int(rows[i]["ma"]) + -int(rows[i - 1]["ma"])) / 2.0) * (float(rows[i]["seg"]) - float(rows[i - 1]["seg"])) / 3600.0 for i in range(1, len(rows)))
    dreqs = int(r1["reqs"]) - int(r0["reqs"])
    groups[grp].append({
        "int_mah": int_mah,
        "ma_avg": statistics.mean(mas),
        "req_s": dreqs / dt,
        "reqs": dreqs,
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

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 5.4), dpi=300)
fig.patch.set_facecolor("white")

x = np.arange(len(order))
colors = ["#059669", "#DC2626"]

# Panel A: Custo Energetico por 1.000 Requisicoes (mAh / 1k req)
eff_means = [statistics.mean(r["mah_1k"] for r in groups[k]) for k in order]
eff_stds = [statistics.stdev(r["mah_1k"] for r in groups[k]) for k in order]

bars1 = ax1.bar(x, eff_means, width=0.48, color=colors, yerr=eff_stds, capsize=6,
                error_kw={"elinewidth": 1.4, "ecolor": "#334155"}, zorder=3)
ax1.set_title("A. Custo Energético por Trabalho Útil (mAh / 1.000 req)", fontsize=11.3, fontweight="bold", pad=12, color="#0F172A")
ax1.set_ylabel("Bateria Consumida por 1.000 req (mAh)", fontsize=10.3, fontweight="bold", color="#1E293B")
ax1.set_xticks(x)
ax1.set_xticklabels(order, fontsize=10)
ax1.set_ylim(0, 495)
ax1.yaxis.grid(True, zorder=0)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

ax1.text(0, eff_means[0] + eff_stds[0] + 12, f"{eff_means[0]:.2f} mAh\n(base 1,0x)",
         ha="center", va="bottom", fontsize=9.8, fontweight="bold", color="#065F46")
ax1.text(1, eff_means[1] + eff_stds[1] + 12, f"{eff_means[1]:.1f} mAh\n(64,5x mais caro!)",
         ha="center", va="bottom", fontsize=9.8, fontweight="bold", color="#991B1B")

# Panel B: Vazao (req/s) vs Corrente Media (mA)
req_means = [statistics.mean(r["req_s"] for r in groups[k]) for k in order]
req_stds = [statistics.stdev(r["req_s"] for r in groups[k]) for k in order]
ma_means = [statistics.mean(r["ma_avg"] for r in groups[k]) for k in order]

w = 0.34
b_req = ax2.bar(x - w / 2, req_means, width=w, color="#2563EB", yerr=req_stds, capsize=4,
                error_kw={"elinewidth": 1.1, "ecolor": "#1E3A8A"}, label="Vazão (req/s)", zorder=3)
ax2.set_title("B. Vazão Entregue vs. Corrente Drenada na Janela (5 min)", fontsize=11.3, fontweight="bold", pad=12, color="#0F172A")
ax2.set_ylabel("Vazão do Servidor (req/s)", fontsize=10.2, fontweight="bold", color="#1D4ED8")
ax2.set_xticks(x)
ax2.set_xticklabels(order, fontsize=10)
ax2.set_ylim(0, 42)
ax2.yaxis.grid(True, zorder=0)
ax2.spines["top"].set_visible(False)

ax2_r = ax2.twinx()
b_ma = ax2_r.bar(x + w / 2, ma_means, width=w, color="#F59E0B", alpha=0.92,
                 label="Corrente Média (mA)", zorder=3)
ax2_r.set_ylabel("Corrente Média Drenada (mA)", fontsize=10.2, fontweight="bold", color="#B45309")
ax2_r.set_ylim(0, 950)
ax2_r.spines["top"].set_visible(False)

ax2.text(0 - w / 2, req_means[0] + req_stds[0] + 1.0, f"{req_means[0]:.1f}/s\n(~9.979 req)", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1D4ED8")
ax2.text(1 - w / 2, req_means[1] + req_stds[1] + 1.0, f"{req_means[1]:.2f}/s\n(~138 req)", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1D4ED8")
for bar, val in zip(b_ma, ma_means):
    ax2_r.text(bar.get_x() + bar.get_width() / 2, val + 18, f"{val:.0f} mA", ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#B45309")

l1, lb1 = ax2.get_legend_handles_labels()
l2, lb2 = ax2_r.get_legend_handles_labels()
ax2.legend(l1 + l2, lb1 + lb2, loc="upper right", frameon=True, facecolor="white", edgecolor="#E2E8F0", fontsize=8.8)

fig.suptitle("Frente Beatriz Siqueira — Overhead da Camada de Virtualização/Emulação no iPhone 7 Plus",
             fontsize=12.8, fontweight="bold", y=0.98, color="#0F172A")
fig.text(0.5, 0.01, "Média de 3 repetições (~5 min cada, 2 threads em /cpu, n=6 rodadas) | Hardware: Apple A10 Fusion, iOS 15.8",
         ha="center", fontsize=8.6, color="#475569")

plt.tight_layout(rect=[0, 0.04, 1, 0.93])
out = os.path.join(OUT_DIR, "grafico_beatriz_virtualizacao.png")
plt.savefig(out, dpi=300)
plt.close(fig)
print("OK:", out)
