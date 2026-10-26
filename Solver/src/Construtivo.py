import pandas as pd
import heapq
import pprint as pp
from Variables import *
from Aux import *

def split_rooms_by_demand(rooms, dem1, dem2):
    total_cap = sum(rooms)
    total_dem = dem1 + dem2
    if total_dem == 0 or total_cap == 0:
        return rooms, []
    target1 = total_cap * dem1 / total_dem
    rooms_sorted = sorted(rooms, reverse=True)
    t1, t2 = [], []
    c1 = 0
    for r in rooms_sorted:
        if c1 < target1:
            t1.append(r); c1 += r
        else:
            t2.append(r)
    return t1, t2

def construtivo(File):
    #Preparação
    cand_df, esc_df, mat_df, NS, NC = txt_to_df(File)
    esc_df["id"] = remove_0lefts(esc_df["id"])
    cand_df["id"] = remove_0lefts(cand_df["id"])
    calculate_capacity(esc_df)

    cap_salas = {
        sid:[int(x) for x in raw.split(";")] for sid, raw in zip(esc_df["id"], esc_df["capacidades_salas"])
    }

    esc_df = esc_df.sort_values("capacidade_total", ascending=False)

    exams = cand_df["tipo_prova"].unique()
    remaining_cands_per_type = cand_df["tipo_prova"].value_counts().to_dict()

    sol = {}; alocacao = {}
    esc_cp  = esc_df.copy(); cand_cp = cand_df.copy(); mat_cp  = mat_df.copy()
    school_params = {}

    nc, ns = NC, NS

    while nc > 0 and ns > 0:
        dist_sums, types_per_school, K_cache = {}, {}, {}
        cap1_map, cap2_map = {}, {}

        #Soma das K menores distâncias e definição dos dois tipos de prova dominantes entre elas
        for sid in esc_cp["id"]:
            if sid not in school_params:
                cap_tot = esc_cp.loc[esc_df["id"]==sid, "capacidade_total"].iloc[0]
                K = cap_tot
    
                K_dists = mat_cp.nsmallest(K, sid)
                K_dists = K_dists[K_dists.idxmin(axis=1)==sid].index
                K_cache[sid] = K_dists
    
                counts = cand_cp.loc[K_dists, "tipo_prova"].value_counts()
                avail = [t for t in exams if remaining_cands_per_type.get(t, 0) > 0]
                if not avail:
                    raise RuntimeError("Sem tipos disponíveis — instância inviável")

                # Só executa na primeira vez que passar pela escola
                if (types_per_school.get(sid) == None):
                    props = {t: counts.get(t, 0) / remaining_cands_per_type[t] for t in avail}
                    top2 = heapq.nlargest(2, props, key=lambda t: (props[t], remaining_cands_per_type[t]))
                    t1 = top2[0]
                    t2 = top2[1] if len(top2) > 1 else None
                    types_per_school[sid] = (t1, t2)
    
                    #preenchimento das salas
                    rooms = cap_salas[sid]
                    dem1 = remaining_cands_per_type.get(t1, 0)
                    dem2 = remaining_cands_per_type.get(t2, 0) if t2 else 0
                    rt1, rt2 = split_rooms_by_demand(rooms, dem1, dem2)
                    cap1_map[sid], cap2_map[sid] = sum(rt1), sum(rt2)
            else:
                t1 = esc_cp.loc[esc_df["id"]==sid,"tipo_prova_1"].iloc[0]
                t2 = esc_cp.loc[esc_df["id"]==sid,"tipo_prova_2"].iloc[0] 
                
            allowed = {t1} | ({t2} if t2 else set())
            mask = cand_cp["tipo_prova"].isin(allowed)
            K_typed = mat_cp.loc[mask, sid].nsmallest(K).index
            dist_sums[sid] = float(mat_cp.loc[K_typed, sid].sum()) if len(K_typed) else float("inf")
                
        # alocação no dataframe
        if (    
            (not "cap_total_t1" in esc_cp.columns) 
            and not "cap_total_t2" in esc_cp.columns
            and not "tipo_prova_1" in esc_cp.columns
            and not "tipo_prova_2" in esc_cp.columns
        ):
            esc_cp["tipo_prova_1"] = esc_cp["id"].map(lambda s: types_per_school[s][0])
            esc_cp["tipo_prova_2"] = esc_cp["id"].map(lambda s: types_per_school[s][1])
            esc_cp["cap_total_t1"] = esc_cp["id"].map(cap1_map)
            esc_cp["cap_total_t2"] = esc_cp["id"].map(cap2_map)
            
        esc_cp["dist_sum"]     = esc_cp["id"].map(dist_sums)

        best = esc_cp.loc[esc_cp["dist_sum"].idxmin()]

        t1, t2 = best["tipo_prova_1"], best["tipo_prova_2"]
        cap1 = int(best["cap_total_t1"])
        cap2 = int(best["cap_total_t2"]) if t2 else 0

        cands = cand_cp.loc[K_cache[best["id"]]]
        allocated_t1 = len(cands[cands["tipo_prova"] == t1])
        allocated_t2 = len(cands[cands["tipo_prova"] == t2])

        best["cap_total_t1"] = best["cap_total_t1"]-allocated_t1
        best["cap_total_t2"] = best["cap_total_t2"]-allocated_t2
        
        allocated = pd.concat([
            cands[cands["tipo_prova"] == t1].head(cap1),
            cands[cands["tipo_prova"] == t2].head(cap2) if t2 else cands.iloc[0:0],
        ])

        if allocated.empty:
            esc_cp = esc_cp.drop(best.name); ns -= 1
            continue

        for tipo, qtd in allocated["tipo_prova"].value_counts().items():
            remaining_cands_per_type[tipo] -= qtd

        for cid_real in cand_cp.loc[allocated.index, "id"]:
            alocacao[cid_real] = best["id"]
        
        sol[best["id"]] = {
            "dist":  float(best["dist_sum"]),
            "exam":  (t1, t2),
            "cap1":  cap1,
            "cap2":  cap2,
            "total_cap":(cap1+cap2),
            "sobra":(cap1+cap2)-len(allocated),
            "alctd": len(allocated),
        }

        best["capacidade_total"] = best["capacidade_total"]-len(allocated)
        
        if best["capacidade_total"]<=0:
            esc_cp  = esc_cp.drop(best.name)
            ns -= 1
            
        cand_cp = cand_cp.drop(allocated.index)
        mat_cp  = mat_cp.drop(allocated.index)
        nc -= len(allocated)

    if nc > 0:
        print(f"[AVISO] {nc} candidatos não alocados — solução inviável")

    return sol, alocacao

sol, al = construtivo(PATH_DIF)
tot, sob, alc = 0,0,0
for i in sol:
    tot+=sol[i]["total_cap"]
    sob+=sol[i]["sobra"]
    alc+=sol[i]["alctd"]

# print(tot)
# print(sob)
# print(alc)

# pp.pprint(sol)
