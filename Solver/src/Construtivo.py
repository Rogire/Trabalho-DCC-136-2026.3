import pandas as pd
import heapq
import numpy as np

import pprint as pp
from Variables import *
from Aux import *

class Constructive:
    def __init__(self, File):
        self.cand_df, self.esc_df, self.mat_df, self.NS, self.NC = txt_to_df(File)
        self.esc_df["id"]  = remove_0lefts(self.esc_df["id"])
        self.cand_df["id"] = remove_0lefts(self.cand_df["id"])
        calculate_capacity(self.esc_df)
        self._setup()

    # Configuração
    def _setup(self):
        self.esc_cp = (self.esc_df.sort_values("capacidade_total", ascending=False)
                                 .set_index("id", drop=False))
        for col in ("tipo_prova_1", "tipo_prova_2",
                    "cap_total_t1", "cap_total_t2", "dist_sum"):
            self.esc_cp[col] = None
        self.cap_salas = {sid: [int(x) for x in raw.split(";")]
                          for sid, raw in zip(self.esc_df["id"],
                                              self.esc_df["capacidades_salas"])}
        self.exams     = list(self.cand_df["tipo_prova"].unique())
        self.remaining = self.cand_df["tipo_prova"].value_counts().to_dict()
        self.cand_cp   = self.cand_df.copy()
        self.mat_cp    = self.mat_df.copy()
        self.ready     = set()
        self.nc, self.ns = self.NC, self.NS
        self.sol, self.alocacao = {}, {}

    #Passos do algoritmo
    def split_rooms(self, rooms, dem1, dem2):
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

    def compute_cap_aware_claims(self, allowed_by_school, min_quota=1):
        budget = {}
        for sid in self.esc_cp.index:
            t1 = self.esc_cp.at[sid, "tipo_prova_1"]
            t2 = self.esc_cp.at[sid, "tipo_prova_2"]
            c1 = int(self.esc_cp.at[sid, "cap_total_t1"]) if t1 else 0
            c2 = int(self.esc_cp.at[sid, "cap_total_t2"]) if t2 else 0
            budget[sid] = c1 + c2

        claims = pd.Series(index=self.mat_cp.index, dtype=object)
        reserved = set()

        for sid in self.esc_cp.index:
            quota = min(min_quota, budget[sid])
            if quota <= 0:
                continue
            for c in self.mat_cp[sid].sort_values().index:
                if c in reserved:
                    continue
                if self.cand_cp.at[c, "tipo_prova"] not in allowed_by_school[sid]:
                    continue
                claims.at[c] = sid
                reserved.add(c)
                budget[sid] -= 1  
                quota -= 1
                if quota <= 0:
                    break

        school_pos = np.argsort(self.mat_cp.values, axis=1)
        names      = self.mat_cp.columns.values
        for c in self.mat_cp.min(axis=1).sort_values().index:
            if c in reserved:
                continue
            c_pos = self.mat_cp.index.get_loc(c)
            ctype = self.cand_cp.at[c, "tipo_prova"]
            for s_pos in school_pos[c_pos]:
                sid = names[s_pos]
                if budget.get(sid, 0) > 0 and ctype in allowed_by_school[sid]:
                    claims.at[c] = sid
                    budget[sid] -= 1
                    break
        return claims

    def Distributed_Rank(self, allowed_by_school):
        claims = self.compute_cap_aware_claims(allowed_by_school, min_quota=1)
        dist_sums, K_cache = {}, {}
        for sid in self.esc_cp.index: 
            allowed = allowed_by_school[sid]
            if not allowed:
                dist_sums[sid] = float("inf"); continue
            ranked     = self.mat_cp[sid].sort_values().index
            is_claimed = (claims.loc[ranked] == sid).values
            claimed_t  = ranked[is_claimed]
            others_t   = ranked[~is_claimed]
            claimed_t  = claimed_t[self.cand_cp.loc[claimed_t, "tipo_prova"].isin(allowed).values]
            others_t   = others_t [self.cand_cp.loc[others_t,  "tipo_prova"].isin(allowed).values]
            pool = claimed_t.tolist() + others_t.tolist()
            K_cache[sid] = pool
            cap_tot = int(self.esc_cp.at[sid, "capacidade_total"])
            head = pool[:cap_tot]
            dist_sums[sid] = (float(self.mat_cp.loc[head, sid].sum())
                              if head else float("inf"))
        return dist_sums, K_cache

    def Assign_Exams(self, sid):
        if sid in self.ready:
            return
        cap_tot = int(self.esc_cp.at[sid, "capacidade_total"])
        K = min(cap_tot, len(self.mat_cp))
        near = self.mat_cp.nsmallest(K, sid).index
        avail = [t for t in self.exams if self.remaining.get(t, 0) > 0]
        if not avail:
            raise RuntimeError("Sem tipos disponíveis — instância inviável")
        type_counts = self.cand_cp.loc[near, "tipo_prova"].value_counts()
        props = {t: type_counts.get(t, 0) / self.remaining[t] for t in avail}
        top2  = heapq.nlargest(2, props,
                               key=lambda t: (props[t], self.remaining[t], t))
        t1 = top2[0]; t2 = top2[1] if len(top2) > 1 else None
        rt1, rt2 = self.split_rooms(self.cap_salas[sid],
                                    self.remaining.get(t1, 0),
                                    self.remaining.get(t2, 0) if t2 else 0)
        self.esc_cp.at[sid, "tipo_prova_1"] = t1
        self.esc_cp.at[sid, "tipo_prova_2"] = t2
        self.esc_cp.at[sid, "cap_total_t1"] = sum(rt1)
        self.esc_cp.at[sid, "cap_total_t2"] = sum(rt2)
        self.ready.add(sid)

    def Set_And_Allocate(self, K_cache, best_sid, t1, t2, cap1, cap2):
        pool       = K_cache[best_sid]
        pool_types = self.cand_cp.loc[pool, "tipo_prova"].values
        idx_t1, idx_t2 = [], []
        for c, tp in zip(pool, pool_types):
            if tp == t1 and len(idx_t1) < cap1:
                idx_t1.append(c)
            elif t2 and tp == t2 and len(idx_t2) < cap2:
                idx_t2.append(c)
            if len(idx_t1) >= cap1 and (not t2 or len(idx_t2) >= cap2):
                break
        return idx_t1 + idx_t2, [idx_t1, idx_t2]

    # Solucao
    def Generate_Solution(self, best_sid, allocated_idx, t_idxs, t1, t2):
        n1 = len(t_idxs[0])
        n2 = len(t_idxs[1]) if t2 else 0                   
        allocated = self.cand_cp.loc[allocated_idx]

        self.esc_cp.at[best_sid, "cap_total_t1"] -= n1
        if t2:
            self.esc_cp.at[best_sid, "cap_total_t2"] -= n2
        remaining_cap = (int(self.esc_cp.at[best_sid, "cap_total_t1"])
                         + (int(self.esc_cp.at[best_sid, "cap_total_t2"]) if t2 else 0))

        for tipo, qtd in allocated["tipo_prova"].value_counts().items():
            self.remaining[tipo] -= int(qtd)
        for cid_real in self.cand_cp.loc[allocated_idx, "id"]:
            self.alocacao[cid_real] = best_sid

        if best_sid not in self.sol:
            self.sol[best_sid] = {
                "exam": (t1, t2),
                "cap1": int(self.esc_cp.at[best_sid, "cap_total_t1"]) + n1,
                "cap2": (int(self.esc_cp.at[best_sid, "cap_total_t2"]) + n2) if t2 else 0,
                "alctd": 0,
                "sobra": None,
            }
        self.sol[best_sid]["alctd"] += len(allocated_idx)
        self.sol[best_sid]["sobra"]  = remaining_cap
        return remaining_cap

    #Loop Principal
    def run(self):
        stagnation = 0
        while self.nc > 0 and self.ns > 0:
            before = self.nc

            for sid in list(self.esc_cp.index):
                self.Assign_Exams(sid)

            allowed_by_school = {
                sid: {self.esc_cp.at[sid, "tipo_prova_1"]}
                     | ({self.esc_cp.at[sid, "tipo_prova_2"]}
                        if self.esc_cp.at[sid, "tipo_prova_2"] else set())
                for sid in self.esc_cp.index
            }
            dist_sums, K_cache = self.Distributed_Rank(allowed_by_school)
            self.esc_cp["dist_sum"] = self.esc_cp.index.map(dist_sums)

            best_sid = self.esc_cp["dist_sum"].idxmin()
            if not np.isfinite(self.esc_cp.at[best_sid, "dist_sum"]):
                print(f"[AVISO] nenhuma escola com pool viável — {self.nc} restantes")
                break

            t1 = self.esc_cp.at[best_sid, "tipo_prova_1"]
            t2 = self.esc_cp.at[best_sid, "tipo_prova_2"]
            cap1 = int(self.esc_cp.at[best_sid, "cap_total_t1"])
            cap2 = int(self.esc_cp.at[best_sid, "cap_total_t2"]) if t2 else 0

            allocated_idx, t_idxs = self.Set_And_Allocate(
                K_cache, best_sid, t1, t2, cap1, cap2)

            if not allocated_idx:                                # 1.5: só desiste de verdade
                self.sol.setdefault(best_sid, {})["motivo"] = "sem_candidatos_do_tipo"
                self.esc_cp = self.esc_cp.drop(best_sid); self.ns -= 1
                continue

            remaining_cap = self.Generate_Solution(
                best_sid, allocated_idx, t_idxs, t1, t2)

            self.cand_cp = self.cand_cp.drop(allocated_idx)
            self.mat_cp  = self.mat_cp.drop(allocated_idx)
            self.nc     -= len(allocated_idx)

            if remaining_cap <= 0:
                self.esc_cp = self.esc_cp.drop(best_sid); self.ns -= 1

            if self.nc == before:                                # 2.5: anti-loop
                stagnation += 1
                if stagnation > 3:
                    print(f"[AVISO] sem progresso — {self.nc} restantes")
                    break
            else:
                stagnation = 0

        return self.sol, self.alocacao

ctv = Constructive(DRIVE_BASE)
sol, al = ctv.run()
pp.pprint(sol)
