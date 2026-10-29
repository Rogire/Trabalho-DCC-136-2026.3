import pandas as pd
import math
import mpimg
from Variables import *

PATH_CAND = "CSV/candidatos.csv"
PATH_SCH = "CSV/escolas.csv"
PATH_MAT = "CSV/matrice.csv"

SCHOOLS_HEADER = "# ESCOLAS (id, CEP, latitude, longitude, num_salas, capacidades_salas)"
CANDIDATES_HEADER = "# CANDIDATOS (id, CEP, tipo_prova, latitude, longitude)"
MATRICE_HEADER = "# MATRIZ_DISTANCIAS (linhas=candidatos, colunas=escolas, em km)"

def txt_to_df(File):
    NS,NC = 0,0
    writing = "nothing"
    with open(PATH_CAND, 'w') as candidatos_csv: pass
    with open(PATH_SCH, 'w') as escolas_csv: pass
    with open(PATH_MAT, 'w') as matrice_csv: pass

    with open(File, "r") as f:
        for line in f:
            str_value = line.rstrip("\r\n")
            if str_value.find("NUM_CANDIDATOS:") != -1: NC = int(str_value[str_value.find(":")+1:])
            if str_value.find("NUM_ESCOLAS:") != -1:    NS = int(str_value[str_value.find(":")+1:])
                
            if line.startswith("# CANDIDATOS"):
                writing = "candidates"
                with open(PATH_CAND,'a') as candidatos_csv:
                    for i in CANDIDATES_COLUMNS:
                        candidatos_csv.writelines(f"{i},")
                    candidatos_csv.write("\n")
                continue
                
            if line.startswith("# ESCOLAS"):
                writing = "schools"
                with open(PATH_SCH,'a') as escolas_csv:
                    for i in SCHOOLS_COLUMNS:
                        escolas_csv.writelines(f"{i},")
                    escolas_csv.write("\n")
                continue
                
            if line.startswith("# MATRIZ"): 
                writing = "matrice"
                with open(PATH_MAT,'a') as matrice_csv:
                    for i in range(NS):
                        matrice_csv.writelines(f"E{i+1},")
                    matrice_csv.write("\n")
                continue
                

            match(writing):
                case "candidates":
                    with open(PATH_CAND, 'a') as candidatos_csv:
                        candidatos_csv.write(line)
                case "schools":
                    with open(PATH_SCH, 'a') as escolas_csv:
                        escolas_csv.write(line)
                case "matrice":
                    with open(PATH_MAT, 'a') as matrice_csv:
                        matrice_csv.write(line)

    cand_df = pd.read_csv(PATH_CAND)
    esc_df = pd.read_csv(PATH_SCH)
    mat_df = pd.read_csv(PATH_MAT)
    
    cand_df = cand_df.drop(cand_df.columns[-1], axis=1)
    esc_df = esc_df.drop(esc_df.columns[-1],axis=1)
    mat_df = mat_df.drop(mat_df.columns[-1],axis=1)
    return cand_df, esc_df, mat_df, NS, NC

def calculate_capacity(esc_df):
    cap_school = 0
    capacities = []
    for i, row in esc_df.iterrows():
        caps_rooms = [int(i) for i in row["capacidades_salas"].split(";")]
        cap_school = sum(caps_rooms)
        capacities.append(cap_school)

    esc_df["capacidade_total"] = capacities
    return cap_school
    
def remove_0lefts(esc_ids):
    return [s[0]+ str(int(s[1:])) for s in esc_ids]

def plotar_instancia(nome, candidatos, escolas, Plot_labels=True, mapa=False):
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
                   for c in candidatos if c["tipo_prova"] == t]
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
     #ax.set_xlim(-25, 15)
     #ax.set_ylim(-21, 23)
     ax.set_aspect("equal")
     ax.set_xlabel("x (km)")
     ax.set_ylabel("y (km)")
     ax.set_title(f"{nome}: {len(candidatos)} candidatos, {len(escolas)} escolas")
     ax.grid(alpha=0.25)
     ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="Tipo de prova", markerscale=2)
     fig.tight_layout()
     
     plt.show()