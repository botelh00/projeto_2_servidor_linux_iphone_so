# Roteiro da Apresentação — Projeto 2: Custo (25/11)

**Grupo:** `obrigado papai e mamae` (`QPE-H4U`)  
**Duração sugerida:** ~5–7 minutos + perguntas e leitura cruzada de gráficos.

## 1. Pergunta e Mecanismo de SO (Pedro — ~45 s)
* **Pergunta:** *"Quanto custa, em consumo extra de bateria, hospedar um servidor Linux em um iPhone 7 Plus quando mudo a carga de requisições, medido em % de bateria e mAh em janela fixa?"*
* **Mecanismo (OSTEP Caps. 6–8):** Virtualização de CPU — *Limited Direct Execution*, escalonamento, preempções involuntárias (`nivcsw`), bloqueios voluntários (`nvcsw`) e estados de frequência/potência do Apple A10 Fusion.

## 2. Hipóteses — Cada Integrante na Própria Frente (~1 min total, ~15 s cada)
* **Pedro:** esperava mais mAh em `/cpu` (esgotando o quantum em alta frequência) e mais `nvcsw/s` em `/io` (bloqueando em `os.fsync()`).
* **Daniel:** esperava que `nice -15` aumentasse vazão e gasto de bateria, enquanto `nice 19` reduziria consumo e aumentaria latência.
* **Beatriz:** esperava menor vazão e maior custo energético por requisição no iSH por causa da tradução x86→ARM64 em *user mode*.
* **Matheus:** esperava que concorrer com um app nativo do iOS multiplicasse as preempções (`nivcsw/s`), derrubasse a vazão e encarecesse cada requisição.

## 3. Método (Pedro ou Daniel — ~40 s)
* **Dispositivo:** iPhone 7 Plus (iOS 15.8 + jailbreak Dopamine, Apple A10 Fusion quad-core, 3 GB RAM, bateria 2.434 mAh úteis), cabo USB desconectado.
* **Setup:** 9 condições × 3 repetições = **27 rodadas válidas de 5 min**; `servidor.py` (`/cpu` SHA-256, `/io` 64 KB + `fsync`, `/stats` via `getrusage`) e `coletor.py` lendo `ioreg IOPMPowerSource` a cada 5 s, integrando corrente no tempo (`∫I dt`) para evitar erro de *voltage sag*.

## 4. Gráfico do Grupo e Frentes (~2,5–3 min)
* **Abrir `grafico_grupo_consolidado.png` e dizer a mensagem em voz alta:** *"Carga CPU-bound consome 9,8× mais bateria que o baseline em 5 min, mas a emulação x86 (iSH) encarece em 64,5× o custo energético por 1.000 requisições."*
* **Pedro (CPU vs I/O):** 85,3 mAh (9,8× baseline) vs. 28,5 mAh em I/O (3,0× menos), com 18× mais `nvcsw/s` em I/O (98,8 vs. 5,5/s) — bloqueio em `fsync` libera a CPU para baixo consumo.
* **Daniel (`nice`):** sob *thermal throttling* a ~38 °C e sem disputa externa, o mAh bruto variou só +2,4%, mas `nice -15` ganhou +10,7% de vazão e -7,8% de custo/1k req (8,28 vs. 8,98).
* **Beatriz (iSH vs Nativo):** na janela de 5 min parecem parecidos (56,5 vs. 63,6 mAh), mas o iSH fez 138 reqs contra 9.979 no nativo (72× menos vazão → 410,74 vs. 6,37 mAh/1k req = **64,5× mais caro**).
* **Matheus (Concorrência iOS):** preempções mais que dobram (+112%, 2.772 vs. 1.306 `nivcsw/s`), pico recorde de 1.648 mA e 39,2 °C → vazão cai 38% e custo/1k req sobe 48% (9,48 vs. 6,40).

## 5. Limites (Matheus ou Beatriz — ~45 s)
* **O que a medição não sustenta:** generalizar números absolutos para outros SoCs/servidores x86; separar o efeito puro de `nice` do teto térmico de 38 °C; zerar ruído de daemons do iOS.
* **O que mediríamos com mais tempo:** `nice` com resfriamento ativo (<32 °C) sob disputa controlada de CPU e rodadas longas de 30 min em regime térmico estacionário.
