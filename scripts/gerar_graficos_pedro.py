import csv
import os
import statistics
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = "/working_dir/c_03c8089db21b2752/artifacts/file_generation/ttl=63d/output"
IN_DIR = "/working_dir/c_03c8089db21b2752/user_uploaded_files/ttl=63d/user_uploaded"
os.makedirs(OUT_DIR, exist_ok=True)

# Exact baseline metrics computed verbatim from user-provided CSVs in prompt:
# baseline_r1 (302.8s), baseline_r2 (302.6s), baseline_r3 (302.7s)
BASELINE_R2_SERIES = [
    (0.0, 90, 32.5), (10.2, 124, 32.4), (30.7, 109, 32.3), (51.2, 120, 32.3),
    (71.7, 101, 32.2), (92.3, 119, 32.1), (112.8, 91, 32.1), (133.3, 152, 32.0),
    (153.9, 91, 32.0), (174.4, 122, 31.9), (194.8, 138, 31.8), (215.4, 125, 31.8),
    (235.9, 122, 31.7), (256.4, 118, 31.7), (277.0, 123, 31.6), (297.5, 109, 31.6),
    (302.6, 109, 31.6),
]

baseline_runs = [
    {"name": "baseline_r1", "ma_avg": 95.0, "int_mah": 8.0, "nvcsw_s": 0.0, "cpu_pct": 0.05},
    {"name": "baseline_r2", "ma_avg": 115.0, "int_mah": 9.6, "nvcsw_s": 0.0, "cpu_pct": 0.05},
    {"name": "baseline_r3", "ma_avg": 100.0, "int_mah": 8.4, "nvcsw_s": 0.003, "cpu_pct": 0.05},
]

def load_csv(filename):
    path = os.path.join(IN_DIR, filename)
    with open(path) as f:
        rows = list(csv.DictReader(f))
    r0, r1 = rows[0], rows[-1]
    dt = float(r1["seg"]) - float(r0["seg"])
    segs = [float(r["seg"]) for r in rows]
    mas = [-int(r["ma"]) for r in rows]
    temps = [float(r["temp_c"]) for r in rows]
    mahs = [int(r["mah"]) for r in rows]
    int_mah = 0.0
    for i in range(1, len(rows)):
        dsec = segs[i] - segs[i - 1]
        int_mah += ((mas[i] + mas[i - 1]) / 2.0) * dsec / 3600.0
    # Normalize integrated mAh to 300s window for fair comparison (pedro_io_r2 was 261.7s)
    int_mah_300 = int_mah * (300.0 / dt)
    dnvcsw = int(r1["nvcsw"]) - int(r0["nvcsw"])
    dnivcsw = int(r1["nivcsw"]) - int(r0["nivcsw"])
    duser = float(r1["user_s"]) - float(r0["user_s"])
    dreqs = int(r1["reqs"]) - int(r0["reqs"])
    return {
        "name": filename,
        "dt": dt,
        "segs": segs,
        "mas": mas,
        "temps": temps,
        "mahs": mahs,
        "ma_avg": statistics.mean(mas),
        "int_mah": int_mah,
        "int_mah_300": int_mah_300,
        "nvcsw_s": dnvcsw / dt,
        "nivcsw_s": dnivcsw / dt,
        "cpu_pct": (duser / dt) * 100.0,
        "reqs_s": dreqs / dt,
    }

cpu_runs = [
    load_csv("pedro_cpu_r1_20261118_181954.csv"),
    load_csv("pedro_cpu_r2_20261118_182812.csv"),
    load_csv("pedro_cpu_r3_20261118_183814.csv"),
]
io_runs = [
    load_csv("pedro_io_r1_20261118_185004.csv"),
    load_csv("pedro_io_r2_20261118_185835.csv"),
    load_csv("pedro_io_r3_20261118_191502.csv"),
]

# Style config
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#CCCCCC",
    "axes.linewidth": 0.8,
    "grid.color": "#EAEAEA",
    "grid.linestyle": "--",
    "grid.linewidth": 0.7,
})

C_BASE = "#64748B"  # Slate gray
C_IO = "#0284C7"    # Sky blue
C_CPU = "#DC2626"   # Crimson red
C_CPU3 = "#EA580C"  # Orange for throttling run

# ==========================================
# GRAFICO 1: Custo Energetico vs Escalonador
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.4), dpi=300)
fig.patch.set_facecolor("white")

labels = ["Baseline\n(0 req/s)", "I/O-bound\n(/io: fsync + leitura)", "CPU-bound\n(/cpu: SHA-256)"]
colors = [C_BASE, C_IO, C_CPU]
x = np.arange(len(labels))

# Panel A: Corrente Media (mA) + mAh integrado (5 min)
ma_means = [
    statistics.mean(r["ma_avg"] for r in baseline_runs),
    statistics.mean(r["ma_avg"] for r in io_runs),
    statistics.mean(r["ma_avg"] for r in cpu_runs),
]
ma_stds = [
    statistics.stdev(r["ma_avg"] for r in baseline_runs),
    statistics.stdev(r["ma_avg"] for r in io_runs),
    statistics.stdev(r["ma_avg"] for r in cpu_runs),
]
mah_means = [
    statistics.mean(r["int_mah"] for r in baseline_runs),
    statistics.mean(r["int_mah_300"] for r in io_runs),
    statistics.mean(r["int_mah_300"] for r in cpu_runs),
]

bars1 = ax1.bar(x, ma_means, width=0.55, color=colors, yerr=ma_stds, capsize=6,
                error_kw={"elinewidth": 1.4, "ecolor": "#334155"}, zorder=3)
ax1.set_title("A. Consumo Energético (Corrente Média e Carga em 5 min)", fontsize=11.5, fontweight="bold", pad=12, color="#0F172A")
ax1.set_ylabel("Corrente Média Drenada (mA)", fontsize=10.5, fontweight="bold", color="#1E293B")
ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=9.8)
ax1.set_ylim(0, 1280)
ax1.yaxis.grid(True, zorder=0)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

for idx, (bar, ma, mah) in enumerate(zip(bars1, ma_means, mah_means)):
    mult = f" ({ma/ma_means[0]:.1f}x)" if idx > 0 else ""
    ax1.text(bar.get_x() + bar.get_width()/2, ma + ma_stds[idx] + 28,
             f"{ma:.0f} mA{mult}\n(~{mah:.1f} mAh/5min)",
             ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#0F172A")

# Panel B: Trocas de Contexto Voluntarias (nvcsw/s) vs Uso de CPU (%)
nvcsw_means = [
    statistics.mean(r["nvcsw_s"] for r in baseline_runs),
    statistics.mean(r["nvcsw_s"] for r in io_runs),
    statistics.mean(r["nvcsw_s"] for r in cpu_runs),
]
cpu_means = [
    statistics.mean(r["cpu_pct"] for r in baseline_runs),
    statistics.mean(r["cpu_pct"] for r in io_runs),
    statistics.mean(r["cpu_pct"] for r in cpu_runs),
]

w = 0.34
b_ctx = ax2.bar(x - w/2, nvcsw_means, width=w, color="#0EA5E9", label="Trocas Voluntárias (nvcsw/s)", zorder=3)
ax2.set_title("B. Comportamento do Escalonador (Bloqueio vs. Uso de CPU)", fontsize=11.5, fontweight="bold", pad=12, color="#0F172A")
ax2.set_ylabel("Trocas Voluntárias / seg (nvcsw/s)", fontsize=10.2, fontweight="bold", color="#0369A1")
ax2.set_xticks(x)
ax2.set_xticklabels(labels, fontsize=9.8)
ax2.set_ylim(0, 130)
ax2.yaxis.grid(True, zorder=0)
ax2.spines["top"].set_visible(False)

ax2_r = ax2.twinx()
b_cpu = ax2_r.bar(x + w/2, cpu_means, width=w, color="#F97316", alpha=0.9, label="Tempo Ativo de CPU (% user_s)", zorder=3)
ax2_r.set_ylabel("Uso de CPU em Modo Usuário (%)", fontsize=10.2, fontweight="bold", color="#C2410C")
ax2_r.set_ylim(0, 115)
ax2_r.spines["top"].set_visible(False)

for bar, val in zip(b_ctx, nvcsw_means):
    ax2.text(bar.get_x() + bar.get_width()/2, val + 2.5, f"{val:.1f}/s", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#0369A1")
for bar, val in zip(b_cpu, cpu_means):
    ax2_r.text(bar.get_x() + bar.get_width()/2, val + 2.2, f"{val:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#C2410C")

lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_r.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=True, facecolor="white", edgecolor="#E2E8F0", fontsize=8.8)

fig.suptitle("Frente Pedro Botelho — Custo Energético: Requisições CPU-bound vs. I/O-bound no iPhone 7 Plus",
             fontsize=13, fontweight="bold", y=0.98, color="#0F172A")
fig.text(0.5, 0.01, "Média de 3 repetições (~5 min cada, n=9 rodadas) | Hardware: Apple A10 Fusion, iOS 15.8 (Dopamine) | Fonte: IOPMPowerSource & getrusage()",
         ha="center", fontsize=8.6, color="#475569")

plt.tight_layout(rect=[0, 0.04, 1, 0.93])
out1 = os.path.join(OUT_DIR, "grafico1_pedro_custo_vs_ctx.png")
plt.savefig(out1, dpi=300)
plt.close(fig)

# ==========================================
# GRAFICO 2: Series Temporais + Thermal Throttling
# ==========================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 6.8), dpi=300, sharex=True, gridspec_kw={"height_ratios": [1.3, 1]})
fig.patch.set_facecolor("white")

b_t = [p[0] for p in BASELINE_R2_SERIES]
b_ma = [p[1] for p in BASELINE_R2_SERIES]
b_temp = [p[2] for p in BASELINE_R2_SERIES]

cpu1 = cpu_runs[0]
cpu3 = cpu_runs[2]
io1 = io_runs[0]

# Top: Instantaneous Current (mA)
ax1.plot(cpu1["segs"], cpu1["mas"], color=C_CPU, lw=2.2, label="CPU-bound r1 (30,8 → 33,7 °C | média 1005 mA)")
ax1.plot(cpu3["segs"], cpu3["mas"], color=C_CPU3, lw=2.0, ls="--", label="CPU-bound r3 (34,6 → 36,3 °C | thermal throttling)")
ax1.plot(io1["segs"], io1["mas"], color=C_IO, lw=2.2, label="I/O-bound r1 (média 345 mA)")
ax1.plot(b_t, b_ma, color=C_BASE, lw=2.0, ls=":", label="Baseline r2 (0 req/s | média 115 mA)")

ax1.annotate("Thermal throttling em cpu_r3\n(~147s: bateria > 36 °C,\ncorrente cai ~1280 → ~760 mA)",
             xy=(168, 781), xytext=(155, 460),
             arrowprops=dict(arrowstyle="->", color="#C2410C", lw=1.4),
             fontsize=8.8, fontweight="bold", color="#9A3412",
             bbox=dict(boxstyle="round,pad=0.35", fc="#FFF7ED", ec="#FDBA74"))

ax1.set_title("Evolução Temporal da Corrente Drenada e Temperatura da Bateria (Janela de 300s)", fontsize=12.5, fontweight="bold", pad=38, color="#0F172A")
ax1.set_ylabel("Corrente Drenada (mA)", fontsize=10.5, fontweight="bold", color="#1E293B")
ax1.set_ylim(0, 1480)
ax1.grid(True)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.legend(loc="upper center", bbox_to_anchor=(0.5, 1.17), frameon=True, facecolor="white", edgecolor="#E2E8F0", fontsize=8.8, ncol=2)

# Bottom: Temperature (C)
ax2.plot(cpu1["segs"], cpu1["temps"], color=C_CPU, lw=2.2, label="CPU-bound r1")
ax2.plot(cpu3["segs"], cpu3["temps"], color=C_CPU3, lw=2.0, ls="--", label="CPU-bound r3")
ax2.plot(io1["segs"], io1["temps"], color=C_IO, lw=2.2, label="I/O-bound r1")
ax2.plot(b_t, b_temp, color=C_BASE, lw=2.0, ls=":", label="Baseline r2")
ax2.axhline(36.0, color="#DC2626", ls=":", lw=1.1, alpha=0.7)
ax2.text(5, 36.12, "Limiar térmico observado (~36,0 °C)", fontsize=8.5, color="#B91C1C")

ax2.set_xlabel("Tempo decorrido na rodada (segundos)", fontsize=10.5, fontweight="bold", color="#1E293B")
ax2.set_ylabel("Temperatura da Bateria (°C)", fontsize=10.5, fontweight="bold", color="#1E293B")
ax2.set_ylim(30.0, 37.2)
ax2.set_xlim(0, 305)
ax2.grid(True)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

fig.text(0.5, 0.01, "Dados reais coletados a cada 5s via /usr/sbin/ioreg -rw0 -c IOPMPowerSource no iPhone 7 Plus (cabo USB desconectado)",
         ha="center", fontsize=8.6, color="#475569")

plt.tight_layout(rect=[0, 0.03, 1, 0.98])
out2 = os.path.join(OUT_DIR, "grafico2_pedro_series_temporais.png")
plt.savefig(out2, dpi=300)
plt.close(fig)

print("Gerados:", out1, out2)
