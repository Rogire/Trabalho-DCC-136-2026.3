import random
from Generate_data import Generate_data
from Variables import *

class Create_instances:
    def __init__(self,         
        SALA_MIN=SALA_MIN, SALA_MAX=SALA_MAX, 
        AREA_KM=AREA_KM, PASSO=PASSO, 
        TIPOS=TIPOS, NUM_BAIRROS=NUM_BAIRROS, 
        PROPOSTAS_AFASTAMENTO=PROPOSTAS_AFASTAMENTO,
        MIN_USAGE=MIN_USAGE, MAX_USAGE=MAX_USAGE,
        LIMITE_LINHAS=LIMITE_LINHAS
    ) -> None:
        self.Data = Generate_data(SALA_MIN,SALA_MAX,AREA_KM,PASSO,TIPOS,NUM_BAIRROS,PROPOSTAS_AFASTAMENTO,MIN_USAGE,MAX_USAGE)
        self.LIMITE_LINHAS=LIMITE_LINHAS

    def gerar_instancia(self,perfil, seed, cap_min, cap_max, caminho:dict[str,str], Print=True, Plot=False):
        rng = random.Random(seed)
        n_escolas = rng.randint(10, 20)
        escolas = self.Data.gerar_escolas(n_escolas, cap_min, cap_max,
                                perfil["desbalancear_tipos"], perfil["prob_segundo_tipo"], rng)
        candidatos = self.Data.gerar_candidatos(escolas, perfil["utilizacao"],
                                      perfil["agrupar_candidatos"], perfil["afastamento"], rng)
        cap_total, razao = self.Data.validar(candidatos, escolas)
        dist = self.Data.matriz_distancias(candidatos, escolas)
    
        self.escrever(caminho, candidatos, escolas, dist, "txt")
        self.escrever(caminho, candidatos, escolas, dist, "csv")
    
        print(f"{caminho['txt']}: {len(candidatos)} candidatos, {len(escolas)} escolas, "
            f"capacidade total {cap_total}, utilização {razao:.1%}")
        if Print:
            self.imprimir_instancia(caminho['txt'], candidatos, escolas, dist)
        if Plot:
            self.plotar_instancia(caminho['txt'], candidatos, escolas)

    def plotar_instancia(self, nome, candidatos, escolas, Plot_labels=PLOT_ROTULOS):
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
            if Plot_labels:
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

    def imprimir_instancia(self, nome, candidatos, escolas, dist):
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
                  f"{self.Data.dist_media_elegivel(candidatos, escolas):.2f} km")
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
    
    def escrever(self, caminho:dict[str,str], candidatos, escolas, dist, tipo: str):
        match tipo:
            case "txt":
                with open(caminho["txt"], "w", encoding="utf-8") as f:
                    f.write(f"NUM_CANDIDATOS: {len(candidatos)}\n")   # 1. quantidade de candidatos
                    f.write(f"NUM_ESCOLAS: {len(escolas)}\n")      # 2. quantidade de escolas
                    f.write("# CANDIDATOS (id_estudante cep x_km y_km tipo_prova)\n")  # 3.
                    for c in candidatos:
                        f.writelines(f"{c['id']} {c['cep']} {c['x']:.2f} {c['y']:.2f} {c['tipo']}\n")
                    f.write("# ESCOLAS (id_escola cep x_km y_km tipos_possiveis capacidade num_salas)\n")  # 4.
                    for e in escolas:
                        f.writelines(f"{e['id']} {e['cep']} {e['x']:.2f} {e['y']:.2f} "
                                f"{','.join(e['tipos'])} {e['capacidade']} {len(e['salas'])}\n")
                    f.write("# SALAS (id_escola cap_sala_1 cap_sala_2 ...)\n")  # 5.
                    for e in escolas:
                        f.writelines(e["id"] + " " + " ".join(map(str, e["salas"])) + "\n")
                    f.write("# MATRIZ DE DISTANCIAS (km): linhas = candidatos, colunas = escolas\n")  # 6.
                    for linha in dist:
                        f.writelines(" ".join(f"{d:.2f}" for d in linha) + "\n")
                    f.close()
            case "csv":
                with open(caminho['candidatos'], "w", encoding="utf-8") as f:
                    for c in candidatos:
                        f.writelines(f"{c['id']},{c['cep']},{c['x']:.2f},{c['y']:.2f},{c['tipo']}\n")
                    f.close()
                with open(caminho['escolas'], "w", encoding="utf-8") as f:
                    for e in escolas:
                        f.writelines(f"{e['id']},{e['cep']},{e['x']:.2f},{e['y']:.2f},{','.join(e['tipos'])},"
                        f"{e['capacidade']},{len(e['salas'])}\n")
                    f.close()
                with open(caminho['salas'], "w", encoding="utf-8") as f:
                    for e in escolas:
                        f.writelines(e["id"] + "," + ",".join(map(str, e["salas"])) + "\n")
                    f.close()
                with open(caminho['matriz'], "w", encoding="utf-8") as f:
                    for linha in dist:
                        f.writelines(",".join(f"{d:.2f}" for d in linha) + "\n")
                    f.close()
            case _:
                raise ValueError(f"tipo inválido: {tipo}")