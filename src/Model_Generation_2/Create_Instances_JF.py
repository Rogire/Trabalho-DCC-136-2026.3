import random
import math

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from Generate_data_JF import Generate_data_test
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
        self.Data = Generate_data_test(SALA_MIN,SALA_MAX,AREA_KM,PASSO,TIPOS,NUM_BAIRROS,PROPOSTAS_AFASTAMENTO,MIN_USAGE,MAX_USAGE)
        self.LIMITE_LINHAS=LIMITE_LINHAS

    def gerar_instancia(self, perfil, seed, cap_min, cap_max,
                            caminho: dict[str, str], Print=True, Plot=False):
            rng = random.Random(seed)
            n_escolas = rng.randint(10, 20)

            sigma_esc = perfil.get("sigma_km_escolas", 0.5)
            sigma_can = perfil.get("sigma_km_candidatos", 0.8)

            escolas = self.Data.gerar_escolas(
                n_escolas, cap_min, cap_max,
                perfil["desbalancear_tipos"],
                perfil["prob_segundo_tipo"],
                rng,
                sigma_km=sigma_esc,
            )

            candidatos = self.Data.gerar_candidatos(
                escolas,
                perfil["utilizacao"],
                perfil["agrupar_candidatos"],
                perfil["afastamento"],
                rng,
                sigma_km = sigma_can

            )

            cap_total, razao = self.Data.validar(candidatos, escolas)
            dist = self.Data.matriz_distancias(candidatos, escolas)   # agora Haversine

            self.escrever(caminho, candidatos, escolas, dist, "txt")
            self.escrever(caminho, candidatos, escolas, dist, "csv")

            print(f"{caminho['txt']}: {len(candidatos)} candidatos, {len(escolas)} escolas, "
                  f"capacidade total {cap_total}, utilização {razao:.1%}")
            if Print:
                self.imprimir_instancia(caminho['txt'], candidatos, escolas, dist)
            if Plot:
                self.plotar_instancia(caminho['txt'], candidatos, escolas, mapa=True)

    def plotar_instancia(self, nome, candidatos, escolas, Plot_labels=PLOT_ROTULOS, mapa=False):
        """Gráfico da distribuição espacial: candidatos (coloridos por tipo de prova)
        e escolas (quadrados, com tamanho proporcional à capacidade)."""
        import matplotlib.pyplot as plt
        LAT0, LON0 = -21.76, -43.35   # centro de referência de JF

        def _para_km(lat, lon):
            print("LAT LON: ",lon , lat)
            x = (lon - LON0) * 111.0 * math.cos(math.radians(LAT0))
            y = (lat - LAT0) * 111.0
            return x, y

        cores = dict(zip(TIPOS, plt.cm.tab10.colors))
        fig, ax = plt.subplots(figsize=(9, 9))

        for t in TIPOS:
            pontos = [_para_km(c["latitude"], c["longitude"])
                      for c in candidatos if c["tipo"] == t]
            if not pontos:
                continue

            xs = [p[0] for p in pontos]
            ys = [p[1] for p in pontos]
            ax.scatter(xs, ys, s=6, alpha=0.35, color=cores[t], label=f"{t} ({len(xs)})")

        cap_max = max(e["capacidade"] for e in escolas)
        for e in escolas:
            xe, ye = _para_km(e["latitude"], e["longitude"])
            ax.scatter(xe , ye, marker="s", s=60 + 240 * e["capacidade"] / cap_max,
                       facecolor="white", edgecolor="black", linewidth=1.8, zorder=3)
            if Plot_labels:
                ax.annotate(f"{e['id']}\n{','.join(e['tipos'])}", (_para_km(e["latitude"],e["longitude"])[0], _para_km(e["latitude"],e["longitude"])[1] ),
                            textcoords="offset points", xytext=(9, 9), fontsize=8,
                            fontweight="bold", zorder=4)
        if mapa:
            LAT_MIN, LAT_MAX = -21.95, -21.55
            LON_MIN, LON_MAX = -43.60, -43.20
            
            COS_LAT0 = math.cos(math.radians(LAT0))
            
            # Converte os 4 cantos para km
            x_min = (LON_MIN - LON0) * 111.0 * COS_LAT0
            x_max = (LON_MAX - LON0) * 111.0 * COS_LAT0
            y_min = (LAT_MIN - LAT0) * 111.0
            y_max = (LAT_MAX - LAT0) * 111.0
            img = mpimg.imread("MapaJuizDeFora.jpg")
            ax.imshow(
                img,
                extent=(x_min, x_max, y_min, y_max),
                aspect="auto",    
                zorder=0,
                alpha=0.6,      
            )

        ax.scatter([], [], marker="s", s=120, facecolor="white", edgecolor="black",
                   linewidth=1.8, label=f"Escolas ({len(escolas)})")
        ax.set_xlim(-25, 15)
        ax.set_ylim(-21, 23)
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
            print("# CANDIDATOS: id cep tipo latitude longitude")
            linhas = [f"{c['id']} {c['cep']} {c['tipo']} "
                      f"{c['latitude']:.6f} {c['longitude']:.6f}" for c in candidatos]
            print()

        if PRINT_ESCOLAS:
            print("# ESCOLAS: id cep latitude longitude num_salas capacidades_salas")
            for e in escolas:
                salas_str = ";".join(map(str, e["salas"]))
                print(f"{e['id']} {e['cep']} {e['latitude']:.6f} {e['longitude']:.6f} "
                      f"{len(e['salas'])} {salas_str}")
            print()

        if PRINT_SALAS:
            print("# SALAS: id_escola cap_sala_1 cap_sala_2 ...")
            for e in escolas:
                print(e["id"] + " " + " ".join(map(str, e["salas"])))
            print()

        if PRINT_MATRIZ:
            print("# MATRIZ_DISTANCIAS (linhas=candidatos, colunas=escolas, em km)")
            print("      " + " ".join(f"{e['id']:>6}" for e in escolas))
            linhas = [f"{c['id'][-5:]:>5} " + " ".join(f"{d:6.2f}" for d in linha)
                      for c, linha in zip(candidatos, dist)]
            mostradas, aviso = corta(linhas)
            print("\n".join(mostradas) + (("\n" + aviso) if aviso else ""))
            print()

    def escrever(self, caminho: dict[str, str], candidatos, escolas, dist, tipo: str):
        match tipo:
            case "txt":
                with open(caminho["txt"], "w", encoding="utf-8") as f:
                    # 1. Cabeçalho geral
                    f.write(f"NUM_CANDIDATOS: {len(candidatos)}\n")
                    f.write(f"NUM_ESCOLAS: {len(escolas)}\n")

                    # 2. Candidatos
                    f.write("# CANDIDATOS (id, CEP, tipo_prova, latitude, longitude)\n")
                    for c in candidatos:
                        f.writelines(
                            f"{c['id']}, {c['cep']}, {c['tipo']}, "
                            f"{c['latitude']:.6f}, {c['longitude']:.6f}\n"
                        )

                    # 3. Escolas
                    f.write("# ESCOLAS (id, CEP, latitude, longitude, num_salas, capacidades_salas)\n")
                    for e in escolas:
                        salas_str = ";".join(map(str, e["salas"]))
                        f.write(
                            f"{e['id']}, {e['cep']}, "
                            f"{e['latitude']:.6f}, {e['longitude']:.6f}, "
                            f"{len(e['salas'])}, {salas_str}\n"
                        )
                    # 4. Matriz de distâncias
                    f.write("# MATRIZ_DISTANCIAS (linhas=candidatos, colunas=escolas, em km)\n")
                    for linha in dist:
                        f.writelines(", ".join(f"{d:.4f}" for d in linha) + "\n")
            case "csv":
                with open(caminho['candidatos'], "w", encoding="utf-8") as f:
                    f.write("id,cep,tipo,latitude,longitude\n")   # cabeçalho ajuda
                    for c in candidatos:
                        f.write(f"{c['id']},{c['cep']},{c['tipo']},"
                                f"{c['latitude']:.6f},{c['longitude']:.6f}\n")
                with open(caminho['escolas'], "w", encoding="utf-8") as f:
                    f.write("id,cep,latitude,longitude,num_salas,capacidades_salas\n")
                    for e in escolas:
                        salas_str = ";".join(map(str, e["salas"]))
                        f.write(f"{e['id']},{e['cep']},"
                                f"{e['latitude']:.6f},{e['longitude']:.6f},"
                                f"{len(e['salas'])},{salas_str}\n")

                with open(caminho['salas'], "w", encoding="utf-8") as f:
                    f.write("id,salas\n")
                    for e in escolas:
                        f.write(f"{e['id']}," + ";".join(map(str, e["salas"])) + "\n")

                with open(caminho['matriz'], "w", encoding="utf-8") as f:
                    for linha in dist:
                        f.write(",".join(f"{d:.4f}" for d in linha) + "\n")
