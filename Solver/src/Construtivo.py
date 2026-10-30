import pandas as pd
import heapq
import numpy as np

import pprint as pp
from Variables import *
from Auxiliar import *

class Constructive:
    def __init__(self, File, dual = True):
        self.cand_df, self.esc_df, self.mat_df, self.NS, self.NC = txt_to_df(File)
        self.esc_df["id"]  = remove_0lefts(self.esc_df["id"])
        self.cand_df["id"] = remove_0lefts(self.cand_df["id"])
        self.dual = dual
        calculate_capacity(self.esc_df)
        self._setup()

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

    def calc_capacity(self, df, sid):
        t1 = df.at[sid, "tipo_prova_1"]
        t2 = df.at[sid, "tipo_prova_2"]
        cap_rem = (int(df.at[sid, "cap_total_t1"]) if t1 else 0) \
            + (int(df.at[sid, "cap_total_t2"]) if t2 else 0)
        return cap_rem

    def compute_cap_aware_claims(self, allowed_by_school, min_quota=1):
            school_names = self.mat_cp.columns.values
            school_to_j  = {s: j for j, s in enumerate(school_names)}
            values       = self.mat_cp.values
            pos_to_label = self.mat_cp.index.values
            n_alive      = len(pos_to_label)
            cand_codes   = self.cand_cp["tipo_prova"].loc[self.mat_cp.index].values
        
            sids = list(self.esc_cp.index)
        
            school_state = {}
            for sid in sids:
                t1 = self.esc_cp.at[sid, "tipo_prova_1"]
                t2 = self.esc_cp.at[sid, "tipo_prova_2"]
                c1 = self.esc_cp.at[sid, "cap_total_t1"]
                c2 = self.esc_cp.at[sid, "cap_total_t2"]
                b1 = int(c1) if (t1 and c1 is not None and not pd.isna(c1)) else 0
                b2 = int(c2) if (t2 and c2 is not None and not pd.isna(c2)) else 0
                school_state[sid] = {"t1": t1, "t2": t2, "b1": b1, "b2": b2}
        
            claims   = pd.Series(index=self.mat_cp.index, dtype=object)
            reserved = np.zeros(n_alive, dtype=bool)
        
            for sid in sids:
                st = school_state.get(sid)
                if st is None:
                    continue
                t1, t2, b1, b2 = st["t1"], st["t2"], st["b1"], st["b2"]
                quota = min(min_quota, b1 + b2)
                if quota <= 0 or not (t1 or t2):
                    continue
                j = school_to_j.get(sid)
                if j is None:
                    continue
                allowed = allowed_by_school.get(sid, set())
                if not allowed:
                    continue
        
                order       = np.argsort(values[:, j])
                allowed_arr = np.array(list(allowed))
                type_ok     = np.isin(cand_codes[order], allowed_arr)
                free        = ~reserved[order]
                ok_pos      = order[type_ok & free]
                to_claim    = ok_pos[:quota]
        
                for pos in to_claim:
                    claims.at[pos_to_label[pos]] = sid
                    reserved[pos] = True
                    code = cand_codes[pos]
                    if code == t1 and b1 > 0:
                        b1 -= 1
                    elif t2 and code == t2 and b2 > 0:
                        b2 -= 1
        
                school_state[sid]["b1"] = b1
                school_state[sid]["b2"] = b2
        
            school_pos = np.argsort(values, axis=1)
            min_dists  = values[np.arange(n_alive), school_pos[:, 0]]
            free_pos   = np.flatnonzero(~reserved)
            free_pos   = free_pos[np.argsort(min_dists[free_pos])]
        
            for pos in free_pos:
                code = cand_codes[pos]
                for s_pos in school_pos[pos]:
                    sid = school_names[s_pos]
                    st  = school_state.get(sid)
                    if st is None:
                        continue
                    if code == st["t1"] and st["b1"] > 0:
                        claims.at[pos_to_label[pos]] = sid
                        reserved[pos] = True
                        st["b1"] -= 1
                        break
                    if st["t2"] and code == st["t2"] and st["b2"] > 0:
                        claims.at[pos_to_label[pos]] = sid
                        reserved[pos] = True
                        st["b2"] -= 1
                        break
        
            return claims

    def Distributed_Rank(self, allowed_by_school):
        claims = self.compute_cap_aware_claims(allowed_by_school, min_quota=1)
        dist_sums, K_cache = {}, {}

        school_names = self.mat_cp.columns.values
        school_to_j  = {s: j for j, s in enumerate(school_names)}
        values       = self.mat_cp.values
        pos_to_label = self.mat_cp.index.values
        cand_codes   = self.cand_cp["tipo_prova"].loc[self.mat_cp.index].values

        for sid in self.esc_cp.index:
            allowed = allowed_by_school[sid]
            if not allowed:
                dist_sums[sid] = float("inf")
                continue
            cap_rem = self.calc_capacity(self.esc_cp, sid)
            if cap_rem <= 0:
                dist_sums[sid] = float("inf")
                continue

            j           = school_to_j[sid]
            order       = np.argsort(values[:, j])
            ranked_lbl  = pos_to_label[order]
            is_claimed  = (claims.loc[ranked_lbl] == sid).values
            allowed_arr = np.array(list(allowed))
            type_ok     = np.isin(cand_codes[order], allowed_arr)
            claimed_pos = order[is_claimed & type_ok]
            others_pos  = order[~is_claimed & type_ok]
            pool_pos    = np.concatenate([claimed_pos, others_pos])

            K_cache[sid] = pos_to_label[pool_pos].tolist()
            head         = pool_pos[:cap_rem]
            dist_sums[sid] = float(values[head, j].mean()) if len(head) else float("inf")
        return dist_sums, K_cache

    def Assign_Exams(self, sid):
        if sid in self.sol:
            return
        cap_tot = int(self.esc_cp.at[sid, "capacidade_total"])
    
        K = min(cap_tot, len(self.mat_cp))
        if K == 0:
            return
    
        near  = self.mat_cp.nsmallest(K, sid).index
        avail = [t for t in self.exams if self.remaining.get(t, 0) > 0]
        if not avail:
            return
        type_counts = self.cand_cp.loc[near, "tipo_prova"].value_counts()
    
        capacity_committed = {t: 0 for t in self.exams}
        for info in self.sol.values():
            if "exam" not in info:
                continue
            t_s1, t_s2 = info["exam"]
            if t_s1:
                capacity_committed[t_s1] += info["cap1"]
            if t_s2:
                capacity_committed[t_s2] += info["cap2"]
    
        props = {t: type_counts.get(t, 0) / (self.remaining[t] + capacity_committed[t] + 1)
                 for t in avail}
        top2 = heapq.nlargest(2, props, key=lambda t: (props[t], self.remaining[t], t))
        t1 = top2[0]
        t2 = top2[1] if (self.dual and len(top2) > 1) else None
    
        local1 = type_counts.get(t1, 0)
        local2 = type_counts.get(t2, 0) if t2 else 0
        rt1, rt2 = self.split_rooms(self.cap_salas[sid], local1, local2)
    
        self.esc_cp.at[sid, "tipo_prova_1"] = t1
        if self.dual:
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

    def Generate_Solution(self, best_sid, allocated_idx, t_idxs, t1, t2):
        n1 = len(t_idxs[0])
        n2 = len(t_idxs[1]) if t2 else 0
        allocated = self.cand_cp.loc[allocated_idx]

        self.esc_cp.at[best_sid, "cap_total_t1"] -= n1
        if t2:
            self.esc_cp.at[best_sid, "cap_total_t2"] -= n2

        remaining_cap = self.calc_capacity(self.esc_cp, best_sid)
        for tipo, qtd in allocated["tipo_prova"].value_counts().items():
            self.remaining[tipo] -= int(qtd)
        for cid_real in self.cand_cp.loc[allocated_idx, "id"]:
            self.alocacao[cid_real] = best_sid

        if best_sid not in self.sol:
            self.sol[best_sid] = {
                "dist_sum":self.esc_cp.at[best_sid, "dist_sum"],
                "exam": (t1, t2),
                "cap1": int(self.esc_cp.at[best_sid, "cap_total_t1"]) + n1,
                "cap2": (int(self.esc_cp.at[best_sid, "cap_total_t2"]) + n2) if t2 else 0,
                "alctd": 0,
                "sobra": None,
            }
        self.sol[best_sid]["alctd"] += len(allocated_idx)
        self.sol[best_sid]["sobra"]  = remaining_cap
        return remaining_cap

    def run(self):
        stagnation = 0
        while self.nc > 0 and self.ns > 0:
            before = self.nc

            for sid in list(self.esc_cp.index):
                self.Assign_Exams(sid)

            allowed_by_school = {
                sid: {self.esc_cp.at[sid, "tipo_prova_1"]} | ({self.esc_cp.at[sid, "tipo_prova_2"]}
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
                K_cache, best_sid, t1, t2, cap1, cap2
            )

            if not allocated_idx:
                self.sol.setdefault(best_sid, {})["motivo"] = "sem_candidatos_do_tipo"
                self.esc_cp = self.esc_cp.drop(best_sid)
                self.ns -= 1
                continue

            remaining_cap = self.Generate_Solution(
                best_sid, allocated_idx, t_idxs, t1, t2
            )

            self.cand_cp = self.cand_cp.drop(allocated_idx)
            self.mat_cp  = self.mat_cp.drop(allocated_idx)
            self.nc     -= len(allocated_idx)

            if remaining_cap <= 0:
                self.esc_cp = self.esc_cp.drop(best_sid)
                self.ns -= 1

            if self.nc == before:
                stagnation += 1
                if stagnation > 3:
                    print(f"[AVISO] sem progresso — {self.nc} restantes")
                    break
            else:
                stagnation = 0

        return self.sol, self.alocacao


