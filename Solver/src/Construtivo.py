import pandas as pd
from Variables import *

def txt_to_df(File):
    NS,NC = 0,0
    writing = "nothing"
    with open("candidatos.csv", 'w') as candidatos_csv: pass
    with open("escolas.csv", 'w') as escolas_csv: pass
    with open("matrice.csv", 'w') as matrice_csv: pass

    with open(File, "r") as f:
        for line in f:
            str_value = line.rstrip("\n")
            if str_value.find("NUM_CANDIDATOS:") != -1: NC = int(str_value[str_value.find(":")+1:])
            if str_value.find("NUM_ESCOLAS:") != -1:    NS = int(str_value[str_value.find(":")+1:])
                
            if line.rstrip('\n') == CANDIDATES_HEADER:
                writing = "candidates"
                with open("candidatos.csv",'a') as candidatos_csv:
                    for i in CANDIDATES_COLUMNS:
                        candidatos_csv.writelines(f"{i},")
                    candidatos_csv.write("\n")
                continue
                
            if str_value == SCHOOLS_HEADER:
                writing = "schools"
                with open("escolas.csv",'a') as escolas_csv:
                    for i in SCHOOLS_COLUMNS:
                        escolas_csv.writelines(f"{i},")
                    escolas_csv.write("\n")
                continue
                
            if str_value == MATRICE_HEADER: 
                writing = "matrice"
                with open("matrice.csv",'a') as matrice_csv:
                    for i in range(NS):
                        matrice_csv.writelines(f"E{i+1},")
                    matrice_csv.write("\n")
                continue
                

            match(writing):
                case "candidates":
                    with open("candidatos.csv", 'a') as candidatos_csv:
                        candidatos_csv.write(line)
                case "schools":
                    with open("escolas.csv", 'a') as escolas_csv:
                        escolas_csv.write(line)
                case "matrice":
                    with open("matrice.csv", 'a') as matrice_csv:
                        matrice_csv.write(line)

    cand_df = pd.read_csv("candidatos.csv")
    esc_df = pd.read_csv("escolas.csv")
    mat_df = pd.read_csv("matrice.csv")
    
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


def construtivo(File):
    cand_df, esc_df, mat_df, NS, NC = txt_to_df(File)
    esc_df["id"] = remove_0lefts(esc_df["id"])
    cand_df["id"] = remove_0lefts(cand_df["id"])
    calculate_capacity(esc_df)
    
    esc_df = esc_df.sort_values("capacidade_total", ascending=False)

    exams = cand_df["tipo_prova"].unique()
    remaining_cands_per_type = cand_df["tipo_prova"].value_counts().to_dict()
    
    sol = {}; alocacao = {}
    esc_cp  = esc_df.copy(); cand_cp = cand_df.copy(); mat_cp  = mat_df.copy()

    nc, ns = NC, NS
    while nc > 0 and ns > 0:
        K = nc // ns
        if K <= 0:
            break

        dist_sums = {}; types_per_school = {}; K_cache = {}

        for sid in esc_cp["id"]:
            K_dists = mat_cp.nsmallest(K,sid).index
            K_cache[sid] = K_dists
            dist_sums[sid] = float(mat_cp.loc[K_dists, sid].sum())

            counts = cand_cp.loc[K_dists, "tipo_prova"].value_counts()
            avail = [t for t in exams if remaining_cands_per_type.get(t, 0) > 0]
            if not avail:
                raise RuntimeError("Sem tipos disponíveis — instância inviável")
                
            props = {t: counts.get(t, 0) / remaining_cands_per_type[t] for t in avail}
            types_per_school[sid] = max(props,  key=lambda k: props[k])

        esc_cp["dist_sum"]   = esc_cp["id"].map(dist_sums)
        esc_cp["tipo_prova"] = esc_cp["id"].map(types_per_school)
        best = esc_cp.loc[esc_cp["dist_sum"].idxmin()]

        cap = int(best["capacidade_total"])
        idx_k = K_cache[best["id"]]
        cands = cand_cp.loc[idx_k]
        cands = cands[cands["tipo_prova"] == best["tipo_prova"]].head(cap)

        if cands.empty:
            esc_cp = esc_cp.drop(best.name)
            ns -= 1
            continue

        for cid in cands.index:
            alocacao[cid] = best["id"]
            remaining_cands_per_type[best["tipo_prova"]] -= 1

        sol[best["id"]] = {
            "dist": float(best["dist_sum"]),
            "exam": best["tipo_prova"],
            "cap":  cap,
            "alctd": len(cands),
        }

        esc_cp = esc_cp.drop(best.name); cand_cp = cand_cp.drop(cands.index); mat_cp  = mat_cp.drop(cands.index)
        ns -= 1; nc -= len(cands)

    if nc > 0:
        print(f"[AVISO] {nc} candidatos não alocados — solução inviável")

    return sol, alocacao

sol, al = construtivo(PATH_BASE)
#print(sol)