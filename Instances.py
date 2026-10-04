import math
import random

SEED = random.randrange(1_000_000)
print("SEED usada:", SEED)
CAP_MIN = 200          # capacidade mínima por escola
CAP_MAX = 500          # capacidade máxima por escola
BAIXAR_ARQUIVOS = False  # baixa os .txt ao final

# Impressão
PRINTAR = True              # liga/desliga toda a impressão
PRINT_RESUMO = True         # totais, utilização, candidatos e capacidade por tipo
PRINT_CANDIDATOS = True     # lista de candidatos
PRINT_ESCOLAS = True        # escolas (id, cep, coordenadas, tipos, capacidade, nº de salas)
PRINT_SALAS = True          # capacidade de cada sala de cada escola
PRINT_MATRIZ = False        # matriz de distâncias (pode ser enorme)
LIMITE_LINHAS = 15          # máx. de linhas de candidatos/matriz impressas (None = todas)

# Gráfico dos candidatos
PLOTAR = True               # mostra um gráfico por instância (candidatos + escolas)
PLOT_ROTULOS = True         # escreve id e tipos possíveis ao lado de cada escola
PLOT_SALVAR_PNG = False     # também salva instancia_1.png / instancia_2.png

TIPOS = ["M1", "M2", "M3e", "M3s", "M3h", "M3d"]
AREA_KM = 30.0                              # área quadrada (km x km) onde tudo é sorteado
SALA_MIN = 20                               # menor capacidade possível de uma sala
SALA_MAX = 100                              # maior capacidade possível de uma sala
PASSO = 5                                   # capacidades sempre múltiplas de PASSO (20, 25, 30, ... 100)
PROPOSTAS_AFASTAMENTO = 20                  # nº de posições sorteadas por candidato quando afastamento > 0
NUM_BAIRROS = 8                             # nº de centros em torno dos quais os candidatos são agrupados

# PERFIS: Base e a diferenciada para dificultar
PERFIS = {
    "base": {
        "utilizacao": 0.85,           # candidatos / capacidade total (0.80 a 0.95)
        "agrupar_candidatos": False,  # False = candidatos uniformes na área
        "desbalancear_tipos": False,  # False = tipos distribuídos uniformemente nas escolas
        "prob_segundo_tipo": 0.5,     # chance de a escola poder oferecer um 2º tipo (máx. 2)
        "afastamento": 0.0,           # 0 = posição do candidato independe das escolas do seu tipo
    },
    "diferenciada": {
        "utilizacao": 0.95,
        "agrupar_candidatos": True,   # candidatos concentrados em poucos "bairros"
        "desbalancear_tipos": True,   # alguns tipos têm pouquíssima capacidade
        "prob_segundo_tipo": 0.5,
        "afastamento": 2.0,           # > 0 = candidatos tendem a ficar longe das escolas que aplicam seu tipo
                                      # (peso = distância ^ afastamento; quanto maior, mais forte o efeito)
    },
}


def gerar_cep(x, rng):
    """CEP fictício (faixa 36000-000 a 36099-999) correlacionado com a coordenada x.
    É apenas um rótulo de localização; a distância usa as coordenadas."""
    prefixo = min(99, int(x / AREA_KM * 100))
    return f"36{prefixo:03d}{rng.randint(0, 999):03d}"


def gerar_salas(cap_alvo, rng):
    """ Cada sala tem uma capacidade múltipla de PASSO entre SALA_MIN e SALA_MAX ]
    A soma das salas é exatamente cap_alvo."""
    salas, restante = [], cap_alvo
    while restante > 0:
        if restante <= SALA_MAX:
            c = restante                      # última sala
        else:
            # sorteia sem deixar um resto menor que SALA_MIN
            c = rng.randrange(SALA_MIN, min(SALA_MAX, restante - SALA_MIN) + 1, PASSO)
        salas.append(c)
        restante -= c
    return salas


def gerar_escolas(n_escolas, cap_min, cap_max, desbalancear, prob_segundo, rng):
    # tipos: garante que todos os 6 tipos existam em pelo menos 1 escola
    tipos = TIPOS[:] + [None] * (n_escolas - len(TIPOS))
    pesos = [0.40, 0.25, 0.15, 0.10, 0.05, 0.05] if desbalancear else [1] * len(TIPOS)
    for i in range(len(TIPOS), n_escolas):
        tipos[i] = rng.choices(TIPOS, weights=pesos)[0]
    rng.shuffle(tipos)

    escolas = []
    for i in range(n_escolas):
        cap_alvo = rng.randrange(-(-cap_min // PASSO) * PASSO, cap_max + 1, PASSO)  # múltiplo de PASSO
        salas = gerar_salas(cap_alvo, rng)
        x, y = rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM)
        # "tipo"  = tipo de referência (solução plantada; garante viabilidade; NÃO vai ao arquivo)
        # "tipos" = tipos que a escola pode oferecer (1 ou 2, incluindo o de referência)
        tipos_ok = [tipos[i]]
        if rng.random() < prob_segundo:
            tipos_ok.append(rng.choice([t for t in TIPOS if t != tipos[i]]))
        escolas.append({
            "id": f"E{i + 1:02d}", "x": x, "y": y, "cep": gerar_cep(x, rng),
            "salas": salas, "capacidade": sum(salas), "tipo": tipos[i], "tipos": tipos_ok,
        })
    return escolas


def gerar_candidatos(escolas, utilizacao, agrupar, afastamento, rng):
    # nº de candidatos por tipo = utilização x capacidade (de referência) daquele tipo
    cap_tipo = {t: 0 for t in TIPOS}
    for e in escolas:
        cap_tipo[e["tipo"]] += e["capacidade"]
    n_tipo = {t: int(cap_tipo[t] * utilizacao) for t in TIPOS}

    # posições das escolas que PODEM aplicar cada tipo (usadas no afastamento)
    locais_tipo = {t: [(e["x"], e["y"]) for e in escolas if t in e["tipos"]] for t in TIPOS}

    # centros para agrupar candidatos no perfil diferenciado
    centros = [(rng.uniform(0.15, 0.85) * AREA_KM, rng.uniform(0.15, 0.85) * AREA_KM)
               for _ in range(NUM_BAIRROS)]

    def sorteia_ponto():
        if not agrupar:
            return rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM)
        cx, cy = rng.choice(centros)
        x = min(max(rng.gauss(cx, 2.0), 0), AREA_KM)
        y = min(max(rng.gauss(cy, 2.0), 0), AREA_KM)
        return x, y

    def sorteia_ponto_afastado(t):
        # sorteia várias posições candidatas e escolhe uma com probabilidade proporcional a
        # (distância à escola elegível mais próxima) ^ afastamento -> favorece posições distantes
        props = [sorteia_ponto() for _ in range(PROPOSTAS_AFASTAMENTO)]
        pesos = [min(math.hypot(px - ex, py - ey) for ex, ey in locais_tipo[t]) ** afastamento + 1e-9
                 for px, py in props]
        return rng.choices(props, weights=pesos)[0]

    candidatos = []
    for t in TIPOS:
        for _ in range(n_tipo[t]):
            x, y = sorteia_ponto_afastado(t) if afastamento > 0 else sorteia_ponto()
            candidatos.append({"id": "", "x": x, "y": y, "cep": gerar_cep(x, rng), "tipo": t})
    rng.shuffle(candidatos)

    # numera após embaralhar para o id não revelar a ordem por tipo
    for i, c in enumerate(candidatos, 1):
        c["id"] = f"C{i:05d}"
    return candidatos


def matriz_distancias(candidatos, escolas):
    return [[round(math.hypot(c["x"] - e["x"], c["y"] - e["y"]), 2) for e in escolas]
            for c in candidatos]


def dist_media_elegivel(candidatos, escolas):
    """Distância média (km) de cada candidato à escola mais próxima que pode aplicar seu tipo."""
    total = 0.0
    for c in candidatos:
        total += min(math.hypot(c["x"] - e["x"], c["y"] - e["y"])
                     for e in escolas if c["tipo"] in e["tipos"])
    return total / len(candidatos)


def validar(candidatos, escolas):
    cap_total = sum(e["capacidade"] for e in escolas)
    assert 10 <= len(escolas) <= 20, "nº de escolas fora de 10..20"
    assert len(candidatos) <= cap_total, "candidatos excedem a capacidade total"
    razao = len(candidatos) / cap_total
    assert 0.80 <= razao <= 0.95 + 1e-9, f"utilização fora de 80-95%: {razao:.3f}"
    for e in escolas:
        assert e["capacidade"] == sum(e["salas"])
        assert 1 <= len(e["tipos"]) <= 2, "escola com mais de 2 tipos"
        assert e["tipo"] in e["tipos"]
    # viabilidade: a atribuição de referência (1 tipo por escola) acomoda todos
    for t in TIPOS:
        n = sum(1 for c in candidatos if c["tipo"] == t)
        cap = sum(e["capacidade"] for e in escolas if e["tipo"] == t)
        assert n <= cap, f"tipo {t}: {n} candidatos > capacidade {cap}"
    return cap_total, razao


def escrever(caminho, candidatos, escolas, dist):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(f"{len(candidatos)}\n")   # 1. quantidade de candidatos
        f.write(f"{len(escolas)}\n")      # 2. quantidade de escolas
        f.write("# CANDIDATOS: id_estudante cep x_km y_km tipo_prova\n")  # 3.
        for c in candidatos:
            f.writelines(f"{c['id']} {c['cep']} {c['x']:.2f} {c['y']:.2f} {c['tipo']}\n")
        f.write("# ESCOLAS: id_escola cep x_km y_km tipos_possiveis capacidade num_salas\n")  # 4.
        for e in escolas:
            f.writelines(f"{e['id']} {e['cep']} {e['x']:.2f} {e['y']:.2f} "
                    f"{','.join(e['tipos'])} {e['capacidade']} {len(e['salas'])}\n")
        f.write("# SALAS: id_escola cap_sala_1 cap_sala_2 ...\n")  # 5.
        for e in escolas:
            f.writelines(e["id"] + " " + " ".join(map(str, e["salas"])) + "\n")
        f.write("# MATRIZ DE DISTANCIAS (km): linhas = candidatos, colunas = escolas\n")  # 6.
        for linha in dist:
            f.writelines(" ".join(f"{d:.2f}" for d in linha) + "\n")


def imprimir_instancia(nome, candidatos, escolas, dist):
    """Mostra a instância na tela, conforme as flags PRINT_* do topo do arquivo."""
    def corta(linhas):
        if LIMITE_LINHAS is None or len(linhas) <= LIMITE_LINHAS:
            return linhas, ""
        return linhas[:LIMITE_LINHAS], f"  ... (+{len(linhas) - LIMITE_LINHAS} linhas ocultas)"

    print("=" * 70)
    print(f"{nome}: {len(candidatos)} candidatos, {len(escolas)} escolas")
    print("=" * 70)

    if PRINT_RESUMO:
        cap_total = sum(e["capacidade"] for e in escolas)
        print(f"Capacidade total: {cap_total} | utilização: {len(candidatos) / cap_total:.1%}")
        print(f"Distância média à escola elegível mais próxima: "
              f"{dist_media_elegivel(candidatos, escolas):.2f} km")
        print(f"{'tipo':<5}{'candidatos':>11}{'cap. (ref.)':>13}")
        for t in TIPOS:
            n = sum(1 for c in candidatos if c["tipo"] == t)
            cap = sum(e["capacidade"] for e in escolas if e["tipo"] == t)
            print(f"{t:<5}{n:>11}{cap:>13}")
        print()

    if PRINT_CANDIDATOS:
        print("# CANDIDATOS: id_estudante cep x_km y_km tipo_prova")
        linhas = [f"{c['id']} {c['cep']} {c['x']:.2f} {c['y']:.2f} {c['tipo']}" for c in candidatos]
        mostradas, aviso = corta(linhas)
        print("\n".join(mostradas) + (("\n" + aviso) if aviso else ""))
        print()

    if PRINT_ESCOLAS:
        print("# ESCOLAS: id_escola cep x_km y_km tipos_possiveis capacidade num_salas")
        for e in escolas:
            print(f"{e['id']} {e['cep']} {e['x']:.2f} {e['y']:.2f} "
                  f"{','.join(e['tipos'])} {e['capacidade']} {len(e['salas'])}")
        print()

    if PRINT_SALAS:
        print("# SALAS: id_escola cap_sala_1 cap_sala_2 ...")
        for e in escolas:
            print(e["id"] + " " + " ".join(map(str, e["salas"])))
        print()

    if PRINT_MATRIZ:
        print("# MATRIZ DE DISTANCIAS (km): linhas = candidatos, colunas = escolas")
        print("      " + " ".join(f"{e['id']:>6}" for e in escolas))
        linhas = [f"{c['id'][-5:]:>5} " + " ".join(f"{d:6.2f}" for d in linha)
                  for c, linha in zip(candidatos, dist)]
        mostradas, aviso = corta(linhas)
        print("\n".join(mostradas) + (("\n" + aviso) if aviso else ""))
        print()


def plotar_instancia(nome, candidatos, escolas):
    """Gráfico da distribuição espacial: candidatos (coloridos por tipo de prova)
    e escolas (quadrados, com tamanho proporcional à capacidade)."""
    import matplotlib.pyplot as plt

    cores = dict(zip(TIPOS, plt.cm.tab10.colors))
    fig, ax = plt.subplots(figsize=(9, 9))

    for t in TIPOS:
        xs = [c["x"] for c in candidatos if c["tipo"] == t]
        ys = [c["y"] for c in candidatos if c["tipo"] == t]
        ax.scatter(xs, ys, s=6, alpha=0.35, color=cores[t], label=f"{t} ({len(xs)})")

    cap_max = max(e["capacidade"] for e in escolas)
    for e in escolas:
        ax.scatter(e["x"], e["y"], marker="s", s=60 + 240 * e["capacidade"] / cap_max,
                   facecolor="white", edgecolor="black", linewidth=1.8, zorder=3)
        if PLOT_ROTULOS:
            ax.annotate(f"{e['id']}\n{','.join(e['tipos'])}", (e["x"], e["y"]),
                        textcoords="offset points", xytext=(9, 9), fontsize=8,
                        fontweight="bold", zorder=4)

    ax.scatter([], [], marker="s", s=120, facecolor="white", edgecolor="black",
               linewidth=1.8, label=f"Escolas ({len(escolas)})")
    ax.set_xlim(-1, AREA_KM + 1)
    ax.set_ylim(-1, AREA_KM + 1)
    ax.set_aspect("equal")
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    ax.set_title(f"{nome}: {len(candidatos)} candidatos, {len(escolas)} escolas")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="Tipo de prova", markerscale=2)
    fig.tight_layout()
    if PLOT_SALVAR_PNG:
        fig.savefig(nome.replace(".txt", ".png"), dpi=150, bbox_inches="tight")
    plt.show()


def gerar_instancia(perfil, seed, cap_min, cap_max, caminho):
    rng = random.Random(seed)
    n_escolas = rng.randint(10, 20)
    escolas = gerar_escolas(n_escolas, cap_min, cap_max,
                            perfil["desbalancear_tipos"], perfil["prob_segundo_tipo"], rng)
    candidatos = gerar_candidatos(escolas, perfil["utilizacao"],
                                  perfil["agrupar_candidatos"], perfil["afastamento"], rng)
    cap_total, razao = validar(candidatos, escolas)
    dist = matriz_distancias(candidatos, escolas)
    escrever(caminho, candidatos, escolas, dist)
    print(f"{caminho}: {len(candidatos)} candidatos, {len(escolas)} escolas, "
          f"capacidade total {cap_total}, utilização {razao:.1%}")
    if PRINTAR:
        imprimir_instancia(caminho, candidatos, escolas, dist)
    if PLOTAR:
        plotar_instancia(caminho, candidatos, escolas)


def main():
    gerar_instancia(PERFIS["base"], SEED, CAP_MIN, CAP_MAX, "instancia_1.txt")
    gerar_instancia(PERFIS["diferenciada"], SEED + 1, CAP_MIN, CAP_MAX, "instancia_2.txt")

    if BAIXAR_ARQUIVOS:
        try:
            from google.colab import files  # só existe no Colab
            files.download("instancia_1.txt")
            files.download("instancia_2.txt")
        except ImportError:
            print("Fora do Colab: arquivos salvos na pasta atual.")


main()