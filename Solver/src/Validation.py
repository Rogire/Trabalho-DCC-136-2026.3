def validate_instance(cand_df, esc_df, verbose=True):
    report = {}

    # 1) Contagens básicas
    total_dem = len(cand_df)
    total_cap = int(esc_df["capacidade_total"].sum()) \
        if "capacidade_total" in esc_df.columns else \
        sum(sum(int(x) for x in r.split(";")) for r in esc_df["capacidades_salas"])

    demand = cand_df["tipo_prova"].value_counts().to_dict()
    demand = {t: int(d) for t, d in demand.items() if d > 0}
    n_types = len(demand)

    rooms = []
    for sid, rooms_str in zip(esc_df["id"], esc_df["capacidades_salas"]):
        for r in rooms_str.split(";"):
            rooms.append((sid, int(r)))
    n_rooms   = len(rooms)
    n_schools = len(esc_df)
    min_room  = min(s for _, s in rooms)
    max_room  = max(s for _, s in rooms)

    report.update({
        "total_demand": total_dem, "total_capacity": total_cap,
        "n_types": n_types, "n_schools": n_schools, "n_rooms": n_rooms,
        "min_room": min_room, "max_room": max_room,
        "demand_by_type": demand,
    })

    # 2) Condições necessárias
    errors = []
    if total_cap < total_dem:
        errors.append(f"N1: capacidade {total_cap} < demanda {total_dem}")
    if n_types > 2 * n_schools:
        errors.append(f"N2: #tipos {n_types} > 2×#escolas ({2*n_schools})")
    if n_types > n_rooms:
        errors.append(f"N3: #tipos {n_types} > #salas {n_rooms}")
    for t, d in demand.items():
        if d > total_cap:
            errors.append(f"N4: tipo {t} demanda {d} > capacidade total {total_cap}")

    if errors:
        report["feasible"] = False
        report["errors"]   = errors
        if verbose:
            for e in errors:
                print(f"[INVIÁVEL] {e}")
        return False, report

    # 3) Aviso de eficiência (não inviabilidade)
    waste = {}
    for t, d in demand.items():
        waste[t] = max(0, min_room - d) if d < min_room else 0
    report["min_waste_per_type"] = waste

    # 4) Greedy assignment
    ok, msg = _greedy_assign(rooms, demand, max_types_per_school=2)
    report["greedy_feasible"] = ok
    report["greedy_msg"]      = msg

    if not ok:
        report["feasible"] = False
        report["feasible_msg"] = (
            "Greedy não cobriu todos os tipos — provavelmente inviável "
            "(confirme com LP/MILP se necessário)"
        )
        if verbose:
            print(f"[PROVAVELMENTE INVIÁVEL] {msg}")
        return False, report

    report["feasible"] = True
    report["feasible_msg"] = "Necessárias OK; greedy OK — provavelmente viável"
    if verbose:
        print("[OK] Necessárias e greedy passaram.")
        if any(w > 0 for w in waste.values()):
            print(f"[INFO] Tipos com demanda < menor sala (desperdício garantido): "
                  f"{ {t: w for t, w in waste.items() if w > 0} }")
    return True, report


def _greedy_assign(rooms, demand, max_types_per_school=2):
    remaining     = dict(demand)
    types         = sorted(demand.keys(), key=lambda t: -demand[t])
    rooms_sorted  = sorted(enumerate(rooms), key=lambda x: -x[1][1])  # (idx, (sid, size))
    school_types  = {}
    used          = set()

    for t in types:
        for idx, (s, size) in rooms_sorted:
            if remaining[t] <= 0:
                break
            if idx in used:
                continue
            if t not in school_types.get(s, set()) and \
               len(school_types.get(s, set())) >= max_types_per_school:
                continue
            used.add(idx)
            school_types.setdefault(s, set()).add(t)
            remaining[t] -= size

    for t in types:
        if remaining[t] > 0:
            return False, f"tipo {t} faltam {remaining[t]} (greedy)"
    return True, "todos os tipos cobertos pelo greedy"