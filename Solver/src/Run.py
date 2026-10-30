import os
import time
import numpy as np
import matplotlib.pyplot as plt
from timeit import default_timer as timer

from Construtivo import *
from Validation import *
from Plot_Inst import *
from BuscaLocal import LocalSearch

BASE_NAME = "../../Instancias_Grupos/"
LEN_GRUPOS = 14

def get_filename(t, i):
    return f"Instancia1_G{i}" if t == "base" else f"Instancia2_G{i}"

def validate(path):
    cand_df, esc_df, _, _, _ = txt_to_df(path)
    calculate_capacity(esc_df)
    return validate_instance(cand_df, esc_df, verbose=True)

def compute_total_distance(ctv, al):
    """Soma REAL (km) das distâncias de cada candidato à sua escola."""
    id_to_row   = dict(zip(ctv.cand_df["id"], range(len(ctv.cand_df))))
    school_col  = {s: j for j, s in enumerate(ctv.mat_df.columns)}
    mat         = ctv.mat_df.to_numpy()
    return float(sum(mat[id_to_row[c], school_col[s]] for c, s in al.items()))

def write_result_csv(solutions, csv_path):
    """Escreve CSV no formato do modelo: uma linha por instância."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Nome Instancia,Melhor resultado,Média dos resultados,Tempo médio de execução\n")
        for s in solutions:
            f.writelines(f"{s['file']},{s['best']:.4f},{s['mean']:.4f},{s['mean_time']:.4f}\n")
    print(f"[CSV] {csv_path} — {len(solutions)} instâncias")

def execute_instance(type, get_sol=True, dual=True, use_local=False, n_runs=5):
    File_path_errors = []
    File_value_errors = []
    solutions = []

    suffix     = "_ls" if use_local else ""
    u_d        = "dual" if dual else "unico"
    base_kind  = "ls" if use_local else "const"

    for p in (
        f"output/al/{base_kind}/{u_d}",
        f"output/sol/{base_kind}/{u_d}/inst",
        f"output/sol/{base_kind}/{u_d}/data",
    ):
        os.makedirs(p, exist_ok=True)

    for i in range(LEN_GRUPOS):
        filename = get_filename(type, i + 1)
        path     = BASE_NAME + filename + ".txt"

        out_path_al  = f"output/al/{base_kind}/{u_d}/{filename}{suffix}.txt"
        out_path_sol = f"output/sol/{base_kind}/{u_d}/inst/{filename}{suffix}.txt"

        print("====================================")
        print(f"[{base_kind}/{u_d}] {filename} — {n_runs} run(s)")

        run_dist, run_time = [], []
        failed = False

        for r in range(n_runs):
            try:
                ctv = Constructive(path, dual)

                start_t = time.time()
                sol, al = ctv.run()
                end_t = time.time()

                if use_local:
                    ls = LocalSearch(ctv)
                    start_t = time.time()
                    sol, al = ls.run()
                    end_t = time.time()

                total_dist = compute_total_distance(ctv, al)
                run_dist.append(total_dist)
                run_time.append(end_t - start_t)

                if r == 0 and get_sol:
                    with open(out_path_al, "w") as f:
                        for k, v in al.items():
                            f.writelines(f"{k} : {v}\n")
                    with open(out_path_sol, "w") as f:
                        for k, v in sol.items():
                            f.write(f"{k} : {v}\n")
                        f.write(f"\nTempo: {end_t - start_t:.4f}\n")
                        f.write(f"Distância: {total_dist:.4f}\n")

            except FileNotFoundError:
                print(f"[ERRO] arquivo não encontrado — {path}")
                File_path_errors.append(f"G{i+1}")
                failed = True
                break
            except ValueError as e:
                print(f"[ERRO] valor — {path}: {e}")
                File_value_errors.append(f"G{i+1}")
                failed = True
                break
            except RuntimeError as e:
                print(f"[ERRO] runtime — {path}: {e}")
                File_value_errors.append(f"G{i+1}")
                failed = True
                break

        if failed or not run_dist:
            continue

        solutions.append({
            "file":      filename,
            "sum":       min(run_dist),                        
            "best":      min(run_dist),
            "mean":      sum(run_dist) / len(run_dist),
            "mean_time": sum(run_time) / len(run_time),
            "time":      sum(run_time) / len(run_time),       
        })

    return File_path_errors, File_value_errors, solutions

def get_dist_sum_sol(path, ctv=None):
    if ctv is None:
        ctv = Constructive(path)
    sol, al = ctv.run()
    return compute_total_distance(ctv, al)

def get_file_errors(File_path_errors_1, File_value_errors_1,
                    File_path_errors_2, File_value_errors_2, type):
    print("Executando instâncias base")
    print(f"Arquivos com caminho errado {type} ")
    if len(File_path_errors_1) == 0: print("Nenhum arquivo com problema!")
    else:
        for i in File_path_errors_1: print(i)

    print(f"Arquivos escritos fora do padrão {type}")
    if len(File_value_errors_1) == 0: print("Nenhum arquivo com problema!")
    else:
        for i in File_value_errors_1: print(i)

    print(f"Arquivos com caminho errado {type} ")
    if len(File_path_errors_2) == 0: print("Nenhum arquivo com problema!")
    else:
        for i in File_path_errors_2: print(i)

    print(f"Arquivos escritos fora do padrão {type}")
    if len(File_value_errors_2) == 0: print("Nenhum arquivo com problema!")
    else:
        for i in File_value_errors_2: print(i)

    print("========================================================================================")

def execute(const=False, local=True, n_runs=5):
    for sub in ("construtivo/unico", "construtivo/dual",
                "local/unico", "local/dual",
                "tempo/local/dual", "tempo/local/unico",
                "tempo/construtivo/dual", "tempo/construtivo/unico"):
        os.makedirs(f"output/img/{sub}", exist_ok=True)

    def sort_and_plot(sol_1, sol_2, path, suffix_label, time=False):
        sol_1.sort(key=lambda e: e["sum"])
        sol_2.sort(key=lambda e: e["sum"])
        plot_instance_sums(sol_1,
            title=f"Soma das distâncias base — {suffix_label}",
            show_mean=True, save_path=f"{path}/inst1.png", time=time)
        plot_instance_sums(sol_2,
            title=f"Soma das distâncias diferenciadas — {suffix_label}",
            show_mean=True, save_path=f"{path}/inst2.png", time=time)

    if const:
        print("=== Construtivo, tipo único ===")
        _, _, sol_cu1 = execute_instance("base", dual=False, use_local=False, n_runs=n_runs)
        _, _, sol_cu2 = execute_instance("dif",  dual=False, use_local=False, n_runs=n_runs)

        out_path_sol_data = "output/sol/const/unico/data/resultados.csv"
        write_result_csv(sol_cu1 + sol_cu2, out_path_sol_data)

        sort_and_plot(sol_cu1, sol_cu2, "output/img/construtivo/unico", "construtivo, 1 tipo")
        sort_and_plot(sol_cu1, sol_cu2, "output/img/tempo/construtivo/unico", "construtivo, 1 tipo", time=True)

        print("=== Construtivo, dois tipos ===")
        _, _, sol_cd1 = execute_instance("base", dual=True, use_local=False, n_runs=n_runs)
        _, _, sol_cd2 = execute_instance("dif",  dual=True, use_local=False, n_runs=n_runs)

        out_path_sol_data = "output/sol/const/dual/data/resultados.csv"
        write_result_csv(sol_cd1 + sol_cd2, out_path_sol_data)

        sort_and_plot(sol_cd1, sol_cd2, "output/img/construtivo/dual", "construtivo, 2 tipos")
        sort_and_plot(sol_cd1, sol_cd2, "output/img/tempo/construtivo/dual", "construtivo, 2 tipos", time=True)

    if local:
        print("=== Construtivo + Busca Local, tipo único ===")
        _, _, sol_lu1 = execute_instance("base", dual=False, use_local=True, n_runs=n_runs)
        _, _, sol_lu2 = execute_instance("dif",  dual=False, use_local=True, n_runs=n_runs)

        out_path_sol_data = "output/sol/ls/unico/data/resultados.csv"
        write_result_csv(sol_lu1 + sol_lu2, out_path_sol_data)

        sort_and_plot(sol_lu1, sol_lu2, "output/img/local/unico", "constr. + busca local, 1 tipo")
        sort_and_plot(sol_lu1, sol_lu2, "output/img/tempo/local/unico", "constr. + busca local, 1 tipo", time=True)

        print("=== Construtivo + Busca Local, dois tipos ===")
        _, _, sol_ld1 = execute_instance("base", dual=True, use_local=True, n_runs=n_runs)
        _, _, sol_ld2 = execute_instance("dif",  dual=True, use_local=True, n_runs=n_runs)

        out_path_sol_data = "output/sol/ls/dual/data/resultados.csv"
        write_result_csv(sol_ld1 + sol_ld2, out_path_sol_data)

        sort_and_plot(sol_ld1, sol_ld2, "output/img/local/dual", "constr. + busca local, 2 tipos")
        sort_and_plot(sol_ld1, sol_ld2, "output/img/tempo/local/dual", "constr. + busca local, 2 tipos", time=True)

execute(const=True, local=True, n_runs=5)