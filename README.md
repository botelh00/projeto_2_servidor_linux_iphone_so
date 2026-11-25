# Projeto 2: Custo — Sistemas Operacionais (CC 2026.2 · Turma 4N)

**Grupo:** `obrigado papai e mamae` (Código `QPE-H4U`)  
**Integrantes:** Pedro Araujo Botelho, Daniel Motta, Beatriz de Assis Siqueira e Matheus Medeiros  
**Docente:** Prof. Lucas Figueiredo — Universidade Presbiteriana Mackenzie (FCI)

## Pergunta Central
> *"Quanto custa, em consumo extra de bateria, hospedar um servidor Linux em um iPhone 7 Plus quando mudo a carga de requisições, medido em % de bateria e mAh em janela fixa?"*

## Estrutura do Repositório
* `relatorio_projeto2_custo.pdf` — Relatório final (8 páginas) com as 9 seções obrigatórias.
* `ROTEIRO_APRESENTACAO_25_11.md` — Roteiro da apresentação de 25/11 (5 blocos).
* `dados/` — Todos os arquivos CSV brutos coletados no iPhone 7 Plus (`ioreg IOPMPowerSource` + `getrusage()`), `resumo_matheus.txt` e a tabela consolidada das 27 rodadas válidas (`tabela_consolidada_27_rodadas.csv`).
* `graficos/` — Os 6 gráficos em alta resolução (300 DPI) gerados a partir dos CSVs brutos.
* `scripts/` — Scripts Python utilizados para processamento dos dados e geração dos gráficos.

## Principais Resultados (27 Rodadas Válidas · Janela de 5 min)
* **Baseline (0 req/s):** `8,7 ± 0,8 mAh` (103 mA).
* **Pedro — CPU-bound vs. I/O-bound:** CPU-bound consome **85,3 mAh** (**9,8×** o baseline e **3,0×** mais que I/O-bound com **28,5 mAh**), enquanto I/O-bound gera **18× mais trocas voluntárias** (`98,8` vs. `5,5 nvcsw/s`).
* **Daniel — Prioridade (`nice -15`, `0`, `19`):** sob *thermal throttling* (~38 °C) sem disputa externa, o consumo absoluto variou apenas +2,4%, mas `nice -15` entregou **+10,7% de vazão** e **-7,8% de custo/1k req** (`8,28` vs. `8,98 mAh/1k`).
* **Beatriz — Nativo ARM64 vs. Emulado iSH x86:** iSH entregou **72× menos vazão** (`0,46` vs. `32,85 req/s`) e custo energético **64,5× maior** por trabalho útil (`410,74` vs. `6,37 mAh/1k req`).
* **Matheus — Concorrência com iOS:** preempções involuntárias mais que dobraram (**+112%**, `2.772` vs. `1.306 nivcsw/s`), pico recorde de **1.648 mA**, temperatura de **39,2 °C**, vazão **-38%** e custo/1k req **+48%** (`9,48` vs. `6,40 mAh/1k`).
