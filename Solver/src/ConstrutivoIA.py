import pandas as pd
import heapq
import numpy as np

import pprint as pp
from Variables import *
from Aux import *

def split_rooms(rooms, dem1, dem2):
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

def compute_cap_aware_claims(mat_cp, cand_cp, esc_cp, allowed_by_school, min_quota=1):
    budget = {}
    # o orçamento de cada escola é a capacidade dela
    for sid in esc_cp.index:
        t1 = esc_cp.at[sid, "tipo_prova_1"]
        t2 = esc_cp.at[sid, "tipo_prova_2"]
        cap1 = int(esc_cp.at[sid, "cap_total_t1"]) if t1 else 0
        cap2 = int(esc_cp.at[sid, "cap_total_t2"]) if t2 else 0
        budget[sid] = cap1 + cap2

    claims = pd.Series(index=mat_cp.index, dtype=object)
    reserved = set()
    
    #  faz reserva mínima para cada escola -> nenhuma fica sem receber candidatos
    for sid in esc_cp.index:
        quota = min(min_quota, budget[sid])
        if quota <=0:
            continue

        for c in mat_cp[sid].sort_values().index:
            if c in reserved:
                continue
            if cand_cp.at[c, "tipo_prova"] not in allowed_by_school[sid]:
                continue
                
            claims.at[c] = sid
            reserved.add(c)
            budget[sid]=-1
            quota-=1
            if quota<=0:  break

    # Ordena as escolas por menor dist dentro das escolas com orçamento
    school_pos = np.argsort(mat_cp.values, axis=1)
    school_names_arr = mat_cp.columns.values
    
    min_dists = mat_cp.min(axis=1)
    for c in min_dists.sort_values().index:
        if c in reserved:
            continue
        c_pos = mat_cp.index.get_loc(c)
        c_type = cand_cp.at[c, "tipo_prova"]
        for s_pos in school_pos[c_pos]:
            sid = school_names_arr[s_pos]
            if budget.get(sid) != None and budget[sid] > 0 and c_type in allowed_by_school[sid]:
                claims.at[c] = sid
                budget[sid] -=1
                break;
                
    return claims

def constructive(File):
    cand_df, esc_df, mat_df, NS, NC = txt_to_df(File)
    esc_df["id"]  = remove_0lefts(esc_df["id"])
    cand_df["id"] = remove_0lefts(cand_df["id"])
    calculate_capacity(esc_df)

    cap_salas = {sid: [int(x) for x in raw.split(";")]
                 for sid, raw in zip(esc_df["id"], esc_df["capacidades_salas"])}

    esc_cp = (esc_df.sort_values("capacidade_total", ascending=False)
                    .set_index("id", drop=False))

    for col in ("tipo_prova_1", "tipo_prova_2","cap_total_t1", "cap_total_t2", "dist_sum"):
        esc_cp[col] = None

    exams     = list(cand_df["tipo_prova"].unique())
    remaining = cand_df["tipo_prova"].value_counts().to_dict()

    cand_cp = cand_df.copy()
    mat_cp  = mat_df.copy()

    ready     = set()
    sol, alocacao = {}, {}
    nc, ns = NC, NS

    while nc > 0 and ns > 0:
        # Calculas os tipos oferecidos e a divisão uma vez
        for sid in esc_cp.index:
            if sid not in ready:
                cap_tot = int(esc_cp.at[sid, "capacidade_total"])
                K = min(cap_tot, len(mat_cp))
                near = mat_cp.nsmallest(K, sid).index
                avail = [t for t in exams if remaining.get(t, 0) > 0]

                if not avail:
                    raise RuntimeError("Sem tipos disponíveis — instância inviável")

                #Tipos
                type_counts = cand_cp.loc[near, "tipo_prova"].value_counts()
                props = {t: type_counts.get(t, 0) / remaining[t] for t in avail}
                top2 = heapq.nlargest(2, props, key=lambda t: (props[t], remaining[t]))
                t1 = top2[0]
                t2 = top2[1] if len(top2) > 1 else None

                #Div Salas
                rooms = cap_salas[sid]
                rt1, rt2 = split_rooms(
                    rooms, remaining.get(t1, 0),
                    remaining.get(t2, 0) if t2 else 0)

                esc_cp.at[sid, "tipo_prova_1"] = t1
                esc_cp.at[sid, "tipo_prova_2"] = t2
                esc_cp.at[sid, "cap_total_t1"] = sum(rt1)
                esc_cp.at[sid, "cap_total_t2"] = sum(rt2)
                ready.add(sid)

        allowed_by_school = {}
        for sid in esc_cp.index:
            t1 = esc_cp.at[sid, "tipo_prova_1"]
            t2 = esc_cp.at[sid, "tipo_prova_2"]
            allowed_by_school[sid] = ({t1} | ({t2} if t2 else set())) if t1 else set()

        # Ranqueamento de entrada
        claims = compute_cap_aware_claims(mat_cp, cand_cp, esc_cp, allowed_by_school, min_quota=1)
        dist_sums, K_cache = {}, {}
        for sid in esc_cp.index:
            allowed = allowed_by_school[sid]
            if not allowed:
                dist_sums[sid] = float("inf")
                continue
                    
            ranked = mat_cp[sid].sort_values(ascending=True).index
            is_claimed = (claims.loc[ranked] == sid).values
    
            claimed_t = ranked[is_claimed]
            others_t  = ranked[~is_claimed]
            claimed_t = claimed_t[cand_cp.loc[claimed_t, "tipo_prova"].isin(allowed).values]
            others_t  = others_t [cand_cp.loc[others_t,  "tipo_prova"].isin(allowed).values]
            pool = claimed_t.tolist() + others_t.tolist()
    
            K_cache[sid] = pool
    
            # A soma das distâncias é o valor do custo pra encher
            cap_tot = int(esc_cp.at[sid, "capacidade_total"])
            head = pool[:cap_tot]
            dist_sums[sid] = float(mat_cp.loc[head, sid].sum()) if head else float("inf")

        esc_cp["dist_sum"] = esc_cp.index.map(dist_sums)

        best_sid = esc_cp["dist_sum"].idxmin()
        if not np.isfinite(esc_cp.at[best_sid, "dist_sum"]):
            print(f"[AVISO] nenhuma escola com pool viável — {nc} candidatos restantes")
            break

        t1 = esc_cp.at[best_sid, "tipo_prova_1"]
        t2 = esc_cp.at[best_sid, "tipo_prova_2"]
        cap1 = int(esc_cp.at[best_sid, "cap_total_t1"])
        cap2 = int(esc_cp.at[best_sid, "cap_total_t2"]) if t2 else 0
    
        pool = K_cache[best_sid]
        pool_types = cand_cp.loc[pool, "tipo_prova"].values
        idx_t1, idx_t2 = [], []
        for c, tp in zip(pool, pool_types):
            if tp == t1 and len(idx_t1) < cap1:
                idx_t1.append(c)
            elif t2 and tp == t2 and len(idx_t2) < cap2:
                idx_t2.append(c)
            if len(idx_t1) >= cap1 and (not t2 or len(idx_t2) >= cap2):
                break

        allocated_idx = idx_t1 + idx_t2
        if not allocated_idx:
            esc_cp = esc_cp.drop(best_sid)
            ns -= 1
            continue

        allocated = cand_cp.loc[allocated_idx]
        n1, n2 = len(idx_t1), len(idx_t2)
    
        # Atualiza a capacidade por tipos
        esc_cp.at[best_sid, "cap_total_t1"] -= n1
        if t2:
            esc_cp.at[best_sid, "cap_total_t2"] -= n2
        remaining_cap = (int(esc_cp.at[best_sid, "cap_total_t1"])
                         + (int(esc_cp.at[best_sid, "cap_total_t2"]) if t2 else 0))
    
        for tipo, qtd in allocated["tipo_prova"].value_counts().items():
            remaining[tipo] -= int(qtd)
        for cid_real in cand_cp.loc[allocated_idx, "id"]:
            alocacao[cid_real] = best_sid
    
        if best_sid not in sol:
            sol[best_sid] = {
                "exam": (t1, t2),
                "cap1": int(esc_cp.at[best_sid, "cap_total_t1"]) + n1,
                "cap2": (int(esc_cp.at[best_sid, "cap_total_t2"]) + n2) if t2 else 0,
                "alctd": 0,
                "sobra": None,
            }
        sol[best_sid]["alctd"] += len(allocated_idx)
        sol[best_sid]["sobra"] = remaining_cap
    
        # Remoção dos elementos já usados: remove escola só se tiver lotada
        cand_cp = cand_cp.drop(allocated_idx)
        mat_cp  = mat_cp.drop(allocated_idx)
        nc     -= len(allocated_idx)
        if remaining_cap <= 0:
            esc_cp = esc_cp.drop(best_sid)
            ns -= 1
    return sol, alocacao

sol, al = constructive(PATH_BASE)
pp.pprint(sol.keys())
