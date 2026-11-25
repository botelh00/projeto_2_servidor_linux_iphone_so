import glob
import os
import csv
import zipfile
import shutil
import numpy as np

BASE_DIR = "/working_dir/c_03c8089db21b2752"
DATA_DIR = os.path.join(BASE_DIR, "user_uploaded_files/ttl=63d/user_uploaded")
OUT_DIR = os.path.join(BASE_DIR, "artifacts/file_generation/ttl=63d/output")
os.makedirs(OUT_DIR, exist_ok=True)


def parse_csv(path, frente, condicao, rodada):
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)

    def get_col(row, cands, default=0.0):
        for c in cands:
            if c in row and row[c] not in (None, "", "None", "null"):
                try:
                    return float(row[c])
                except ValueError:
                    pass
        return default

    t_vals = [get_col(r, ["seg", "elapsed_s", "t_s", "tempo_s"]) for r in rows]
    dur = t_vals[-1] - t_vals[0]
    ma_vals = [abs(get_col(r, ["ma", "InstantAmperage"])) for r in rows]
    int_mah = 0.0
    for i in range(1, len(rows)):
        dt = max(0.0, t_vals[i] - t_vals[i - 1])
        int_mah += 0.5 * (ma_vals[i] + ma_vals[i - 1]) * (dt / 3600.0)

    pct0 = get_col(rows[0], ["pct"])
    pct1 = get_col(rows[-1], ["pct"])
    temp_vals = [get_col(r, ["temp_c"]) for r in rows]
    if max(temp_vals) > 150:
        temp_vals = [v / 100.0 for v in temp_vals]

    reqs0, reqs1 = get_col(rows[0], ["reqs"]), get_col(rows[-1], ["reqs"])
    d_reqs = max(0.0, reqs1 - reqs0)
    req_s = d_reqs / dur if dur > 0 else 0.0

    nvcsw0, nvcsw1 = get_col(rows[0], ["nvcsw"]), get_col(rows[-1], ["nvcsw"])
    nivcsw0, nivcsw1 = get_col(rows[0], ["nivcsw"]), get_col(rows[-1], ["nivcsw"])
    nvcsw_s = max(0.0, nvcsw1 - nvcsw0) / dur if dur > 0 else 0.0
    nivcsw_s = max(0.0, nivcsw1 - nivcsw0) / dur if dur > 0 else 0.0

    mah_1k = (int_mah / (d_reqs / 1000.0)) if d_reqs > 0 else ""

    return {
        "frente": frente,
        "condicao": condicao,
        "rodada": rodada,
        "arquivo": os.path.basename(path),
        "duracao_s": round(dur, 1),
        "delta_pct": round(pct1 - pct0, 1),
        "int_mah": round(int_mah, 2),
        "ma_media": round(float(np.mean(ma_vals)), 1),
        "ma_pico": round(float(np.max(ma_vals)), 0),
        "temp_ini_c": round(temp_vals[0], 1),
        "temp_fim_c": round(temp_vals[-1], 1),
        "temp_max_c": round(float(np.max(temp_vals)), 1),
        "reqs_total": int(round(d_reqs)),
        "req_s": round(req_s, 2),
        "nvcsw_s": round(nvcsw_s, 1),
        "nivcsw_s": round(nivcsw_s, 1),
        "mah_por_1k_req": round(mah_1k, 2) if mah_1k != "" else "",
    }


records = [
    # Verified Baseline (3 runs from 2026-11-18)
    {"frente": "Baseline", "condicao": "Ocioso (0 req/s)", "rodada": "r1", "arquivo": "baseline_r1_20261118.csv", "duracao_s": 302.8, "delta_pct": 0.0, "int_mah": 8.0, "ma_media": 95.0, "ma_pico": 115, "temp_ini_c": 33.3, "temp_fim_c": 32.6, "temp_max_c": 33.3, "reqs_total": 0, "req_s": 0.0, "nvcsw_s": 0.0, "nivcsw_s": 3.1, "mah_por_1k_req": ""},
    {"frente": "Baseline", "condicao": "Ocioso (0 req/s)", "rodada": "r2", "arquivo": "baseline_r2_20261118.csv", "duracao_s": 302.6, "delta_pct": 0.0, "int_mah": 9.6, "ma_media": 115.0, "ma_pico": 130, "temp_ini_c": 32.5, "temp_fim_c": 31.6, "temp_max_c": 32.5, "reqs_total": 0, "req_s": 0.0, "nvcsw_s": 0.0, "nivcsw_s": 3.1, "mah_por_1k_req": ""},
    {"frente": "Baseline", "condicao": "Ocioso (0 req/s)", "rodada": "r3", "arquivo": "baseline_r3_20261118.csv", "duracao_s": 302.7, "delta_pct": 0.0, "int_mah": 8.4, "ma_media": 100.0, "ma_pico": 120, "temp_ini_c": 31.5, "temp_fim_c": 30.9, "temp_max_c": 31.5, "reqs_total": 0, "req_s": 0.0, "nvcsw_s": 0.0, "nivcsw_s": 3.1, "mah_por_1k_req": ""},
]

file_specs = [
    ("Pedro Botelho", "CPU-bound (8T /cpu)", "r1", "pedro_cpu_r1_20261118_181954.csv"),
    ("Pedro Botelho", "CPU-bound (8T /cpu)", "r2", "pedro_cpu_r2_20261118_182812.csv"),
    ("Pedro Botelho", "CPU-bound (8T /cpu)", "r3", "pedro_cpu_r3_20261118_183814.csv"),
    ("Pedro Botelho", "I/O-bound (8T /io)", "r1", "pedro_io_r1_20261118_185004.csv"),
    ("Pedro Botelho", "I/O-bound (8T /io)", "r2", "pedro_io_r2_20261118_185835.csv"),
    ("Pedro Botelho", "I/O-bound (8T /io)", "r3", "pedro_io_r3_20261118_191502.csv"),
    ("Daniel Motta", "nice -15 (8T /cpu)", "r1", "daniel_n15_r1_20261119_151500.csv"),
    ("Daniel Motta", "nice -15 (8T /cpu)", "r2", "daniel_n15_r2_20261119_152330.csv"),
    ("Daniel Motta", "nice -15 (8T /cpu)", "r3", "daniel_n15_r3_20261119_153136.csv"),
    ("Daniel Motta", "nice 0 (8T /cpu)", "r1", "daniel_n0_r1_20261119_153943.csv"),
    ("Daniel Motta", "nice 0 (8T /cpu)", "r2", "daniel_n0_r2_20261119_154747.csv"),
    ("Daniel Motta", "nice 0 (8T /cpu)", "r3", "daniel_n0_r3_20261119_155551.csv"),
    ("Daniel Motta", "nice 19 (8T /cpu)", "r1", "daniel_n19_r1_20261119_160403.csv"),
    ("Daniel Motta", "nice 19 (8T /cpu)", "r2", "daniel_n19_r2_20261119_161205.csv"),
    ("Daniel Motta", "nice 19 (8T /cpu)", "r3", "daniel_n19_r3_20261119_162010.csv"),
    ("Beatriz Siqueira", "Nativo ARM64 (2T /cpu)", "r1", "beatriz_nativo_r1_20261121_153300.csv"),
    ("Beatriz Siqueira", "Nativo ARM64 (2T /cpu)", "r2", "beatriz_nativo_r2_20261121_154105.csv"),
    ("Beatriz Siqueira", "Nativo ARM64 (2T /cpu)", "r3", "beatriz_nativo_r3_20261121_154910.csv"),
    ("Beatriz Siqueira", "Emulado iSH x86 (2T /cpu)", "r1", "beatriz_ish_r1_20261121_143335.csv"),
    ("Beatriz Siqueira", "Emulado iSH x86 (2T /cpu)", "r2", "beatriz_ish_r2_20261121_144139.csv"),
    ("Beatriz Siqueira", "Emulado iSH x86 (2T /cpu)", "r3", "beatriz_ish_r3_20261121_144943.csv"),
    ("Matheus Medeiros", "Concorrência iOS (8T /cpu)", "r1", "matheus_concorrencia_r1_20261121_171207.csv"),
    ("Matheus Medeiros", "Concorrência iOS (8T /cpu)", "r2", "matheus_concorrencia_r2_20261121_172010.csv"),
    ("Matheus Medeiros", "Concorrência iOS (8T /cpu)", "r3", "matheus_concorrencia_r3_20261121_172814.csv"),
]

for frente, cond, rod, fname in file_specs:
    fpath = os.path.join(DATA_DIR, fname)
    if os.path.exists(fpath):
        records.append(parse_csv(fpath, frente, cond, rod))
    else:
        print("MISSING:", fname)

csv_out = os.path.join(OUT_DIR, "tabela_consolidada_27_rodadas.csv")
fieldnames = list(records[0].keys())
with open(csv_out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(records)
print(f"Wrote {len(records)} rows to {csv_out}")

# Build Markdown compilation for the group
md_content = """# Coletânea Consolidada — Projeto 2: Custo (Sistemas Operacionais)

**Grupo:** `obrigado papai e mamae` (Código `QPE-H4U`)  
**Integrantes:** Pedro Araujo Botelho, Daniel Motta, Beatriz de Assis Siqueira e Matheus Medeiros  
**Disciplina:** Sistemas Operacionais — CC 2026.2 (Turma 4N, Prof. Lucas Figueiredo, Mackenzie)  
**Pilar OSTEP:** Virtualização de CPU — *Escalonamento de processos, trocas de contexto e execução direta limitada* ([OSTEP Cap. 6](https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-mechanisms.pdf), [OSTEP Cap. 8](https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-sched-mlfq.pdf))

## 1. Pergunta Central e Setup Experimental

> **Pergunta:** *"Quanto custa, em consumo extra de bateria, hospedar um servidor Linux em um iPhone 7 Plus quando mudo a carga de requisições, medido em % de bateria e mAh em janela fixa?"*

* **Dispositivo:** [Apple iPhone 7 Plus](https://support.apple.com/en-us/111953) (iOS 15.8 com jailbreak [Dopamine](https://github.com/opa334/dopamine), chip Apple A10 Fusion quad-core 2,34 GHz, 3 GB RAM, bateria `DesignCapacity = 2890 mAh`, `AppleRawMaxCapacity = 2434 mAh`, `CycleCount = 346`).
* **Instrumentação:** servidor HTTP Python (`servidor.py`) expondo `/cpu` (15.000 iterações SHA-256), `/io` (escrita de 64 KB + `os.fsync()` + leitura) e `/stats` (`getrusage()` com `ru_nvcsw`, `ru_nivcsw`, `ru_utime`, `ru_stime`); coletor (`coletor.py`) amostrando `/usr/sbin/ioreg -rw0 -c IOPMPowerSource` a cada 5 s durante janelas de **5 minutos (~300 s)** com cabo USB desconectado.
* **Descobertas metodológicas importantes para a defesa (25/11):**
  1. **Queda de tensão (Voltage Sag):** sob corrente > 1 A, o contador `AppleRawCurrentCapacity` cai artificialmente (ex.: -279 mAh na `pedro_cpu_r1`, recuperando +183 mAh após 3 min de repouso). Por isso, integramos `InstantAmperage` no tempo ($\\int I\\,dt$) para obter o consumo eletroquímico real em mAh.
  2. **Thermal Throttling:** acima de ~36–38 °C, o Apple A10 reduz a corrente de ~1.280–1.600 mA para ~700–760 mA, reduzindo a vazão nas rodadas consecutivas.

## 2. Tabela Resumo das 4 Frentes (27 Rodadas Válidas)

| Frente / Condição | Rodadas | Δ% Bateria | mAh / 5 min (∫I dt) | Múltiplo vs. Baseline | Corrente média (pico) | Vazão média | Preempções (`nivcsw/s`) | Custo (`mAh / 1k req`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (0 req/s)** | 3 | 0,0% | **8,7 ± 0,8** | 1,0× | 103 mA | 0 req/s | 3/s | — |
| **Pedro — I/O-bound (8T `/io`)** | 3 | -1,3% | **28,5 ± 2,3*** | 3,3× | 340 (416) mA | 83,8 req/s | 1.592/s | **1,48** |
| **Pedro — CPU-bound (8T `/cpu`)** | 3 | -4,0% | **85,3 ± 4,5** | **9,8×** | 1.007 (1.349) mA | 44,2 req/s | 1.306/s | **6,40** |
| **Daniel — `nice -15` (8T `/cpu`)** | 3 | -3,3% | **59,0 ± 2,9** | 6,8× | 696 (1.117) mA | 23,7 req/s | 815/s | **8,28** |
| **Daniel — `nice 0` (8T `/cpu`)** | 3 | -3,0% | **56,3 ± 1,4** | 6,5× | 667 (1.114) mA | 22,3 req/s | 910/s | **8,42** |
| **Daniel — `nice 19` (8T `/cpu`)** | 3 | -2,7% | **57,6 ± 2,7** | 6,6× | 685 (1.344) mA | 21,4 req/s | 917/s | **8,98** |
| **Beatriz — Nativo ARM64 (2T `/cpu`)** | 3 | -3,0% | **63,6 ± 3,7** | 7,3× | 748 (1.146) mA | 32,9 req/s | 533/s | **6,37** |
| **Beatriz — Emulado iSH x86 (2T `/cpu`)** | 3 | -2,7% | **56,5 ± 1,6** | 6,5× | 669 (751) mA | **0,46 req/s** | 0/s (usermode) | **410,74** |
| **Matheus — Concorrência iOS (8T `/cpu`)** | 3 | -4,3% | **77,1 ± 6,1** | 8,9× | 914 (**1.648**) mA | 27,4 req/s | **2.772/s** | **9,48** |

*\*I/O-bound normalizado para 300 s (a `r2` encerrou aos 261,7 s com 22,9 mAh brutos). As rodadas do Daniel ocorreram sob thermal throttling contínuo (~38 °C).*

## 3. Pontos-Chave de Cada Integrante para a Defesa (25/11)

### Pedro Botelho — Natureza da Carga (CPU-bound vs. I/O-bound)
* **Gráficos:** `grafico1_pedro_custo_vs_ctx.png` e `grafico2_pedro_series_temporais.png`.
* **Achado principal:** CPU-bound consome **9,8× o baseline** (`85,3 mAh` vs. `8,7 mAh`) e **3,0× mais** que I/O-bound (`28,5 mAh`), apesar de I/O-bound gerar **18× mais trocas voluntárias de contexto** (`98,8 nvcsw/s` vs. `5,5 nvcsw/s`).
* **Explicação de SO:** em `/io`, cada `os.fsync()` coloca a thread em estado *Blocked* (`nvcsw`), liberando os núcleos para estados de baixo consumo (23,2% CPU); em `/cpu`, as threads saturam a CPU (85,5%) até sofrerem preempção involuntária (`nivcsw`), mantendo a frequência e a corrente no topo.

### Daniel Motta — Prioridade de Processo (`nice -15`, `0`, `19`)
* **Gráfico:** `grafico_daniel_nice.png`.
* **Achado principal:** sem disputa externa de CPU e sob thermal throttling (~38 °C), o consumo absoluto em 5 min quase não mudou (+2,4% entre `nice -15` e `nice 19`), mas `nice -15` entregou **+10,7% mais vazão** (`23,7` vs. `21,4 req/s`), menor latência média (`310,9 ms` vs. `357,2 ms`) e **7,8% menos energia por 1.000 requisições** (`8,28` vs. `8,98 mAh/1k`).
* **Explicação de SO:** prioridade (`nice`) decide *quem* ganha fatia quando há fila de prontos; com o servidor sozinho no aparelho, o gargalo foi o teto térmico do A10 Fusion, não o escalonador. Ainda assim, maior prioridade reduziu preempções por daemons do iOS (`815` vs. `917 nivcsw/s`).

### Beatriz Siqueira — Overhead de Emulação (Nativo ARM64 vs. [iSH Shell](https://ish.app/) x86)
* **Gráfico:** `grafico_beatriz_virtualizacao.png`.
* **Achado principal:** o emulador iSH gasta energia absoluta parecida na janela (`56,5 mAh` vs. `63,6 mAh` nativo), mas entrega **72× menos vazão** (`0,46` vs. `32,85 req/s` — apenas ~138 reqs em 5 min contra ~9.979 no nativo).
* **Impacto energético:** o custo por 1.000 requisições explode para **410,74 mAh** no iSH contra **6,37 mAh** no nativo — **64,5× mais energia por unidade de trabalho útil**.
* **Explicação de SO:** sem suporte a *Limited Direct Execution* (OSTEP Cap. 6), cada instrução x86 do interpretador Python precisa ser traduzida em software para ARM64 em *user mode*, desperdiçando ciclos de CPU na camada de emulação.

### Matheus Medeiros — Concorrência com o Hospedeiro iOS (Isolado vs. App Nativo)
* **Gráfico:** `grafico_matheus_concorrencia.png`.
* **Achado principal:** dividir o iPhone com um app nativo pesado faz as preempções involuntárias (`nivcsw/s`) **mais que dobrarem** (`2.772/s` vs. `1.306/s`, +112%), gera o maior pico de corrente do projeto (**1.648 mA**) e eleva a temperatura a **39,2 °C**.
* **Impacto energético:** a disputa + throttling derruba a vazão em **38%** (`27,4` vs. `44,2 req/s`, com 117–208 erros HTTP/rodada) e encarece o trabalho útil em **+48%** (`9,48` vs. `6,40 mAh/1k req`).

## 4. Arquivos Incluídos no Pacote (`coletanea_grupo_projeto2.zip`)

* `RESUMO_COLETANEA_GRUPO.md` — este documento completo.
* `tabela_consolidada_27_rodadas.csv` — métricas processadas de todas as 27 rodadas válidas.
* `graficos/grafico1_pedro_custo_vs_ctx.png`
* `graficos/grafico2_pedro_series_temporais.png`
* `graficos/grafico_daniel_nice.png`
* `graficos/grafico_beatriz_virtualizacao.png`
* `graficos/grafico_matheus_concorrencia.png`
* `graficos/grafico_grupo_consolidado.png`

## 5. Checklist de Entregas

* **23/11 (Relatório PDF + GitHub):** PDF de até 10 páginas com as 9 seções na ordem *(1. Pergunta, 2. Método, 3. Hipóteses, 4. Resultados, 5. Discussão, 6. Limites, 7. Frentes, 8. Referências, 9. Declaração de uso de IA)* + pasta `dados/` com os CSVs brutos e scripts no repositório público.
* **25/11 (Apresentação):** cada integrante defende sua frente e explica seus gráficos; preparar leitura cruzada de gráficos de outro grupo.
"""

md_out = os.path.join(OUT_DIR, "coletanea_grupo_projeto2.md")
with open(md_out, "w", encoding="utf-8") as fh:
    fh.write(md_content.strip() + "\n")
print("Wrote:", md_out)

# Create ZIP bundle with MD, CSV, and all 6 PNG charts
zip_out = os.path.join(OUT_DIR, "coletanea_grupo_projeto2.zip")
chart_files = [
    "grafico1_pedro_custo_vs_ctx.png",
    "grafico2_pedro_series_temporais.png",
    "grafico_daniel_nice.png",
    "grafico_beatriz_virtualizacao.png",
    "grafico_matheus_concorrencia.png",
    "grafico_grupo_consolidado.png",
]

with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(md_out, arcname="RESUMO_COLETANEA_GRUPO.md")
    zf.write(csv_out, arcname="tabela_consolidada_27_rodadas.csv")
    for cf in chart_files:
        cpath = os.path.join(OUT_DIR, cf)
        if os.path.exists(cpath):
            zf.write(cpath, arcname=os.path.join("graficos", cf))
        else:
            print("WARNING missing chart:", cf)

print("Wrote ZIP:", zip_out, f"({os.path.getsize(zip_out) / 1024:.1f} KB)")
with zipfile.ZipFile(zip_out, "r") as zf:
    print("ZIP contents:", zf.namelist())
