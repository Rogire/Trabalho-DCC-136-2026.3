import os
import matplotlib.pyplot as plt
import time

from timeit import default_timer as timer
from Construtivo import *
from Validation import *
from Plot_Inst import *
from BuscaLocal import LocalSearch

BASE_NAME = "../../Instancias_Grupos/"
LEN_GRUPOS = 14
def get_filename(t,i):
    return f"Instancia1_G{i}" if t == "base" else f"Instancia2_G{i}"

def validate(path):
    cand_df, esc_df, _, _, _ = txt_to_df(path)
    calculate_capacity(esc_df)
    return validate_instance(cand_df, esc_df, verbose=True)
    
def execute_instance(type, get_sol=True, dual=True, use_local=False):
    File_path_errors = []
    File_value_errors = []
    solutions = []

    suffix = "_ls" if use_local else ""
    
    os.makedirs("output/sol/ls/", exist_ok=True)
    os.makedirs("output/sol/const", exist_ok=True)
    os.makedirs("output/al/ls/", exist_ok=True)
    os.makedirs("output/al/const", exist_ok=True)
    
    for i in range(LEN_GRUPOS):
        filename = get_filename(type, i + 1)
        path = BASE_NAME + filename + ".txt"
        out_path_al  = f"output/al/const/{filename}{suffix}.txt"
        out_path_sol = f"output/sol/const/{filename}{suffix}.txt"

        try:
            print("====================================")
            print(f"Grupo {i+1} (dual={dual}, local={use_local})")
            start_t = time.time()
            ctv = Constructive(path, dual)
            sol, al = ctv.run()
            end_t = time.time()
            
            if use_local:
                start_t = time.time()
                ls = LocalSearch(ctv)
                sol, al = ls.run()
                end_t = time.time()
                out_path_al = f"output/al/ls/{filename}{suffix}.txt"
                out_path_sol = f"output/sol/ls/{filename}{suffix}.txt"
                
            if get_sol:
                with open(f"{out_path_al}", "w") as f:
                    for k, v in al.items():
                        f.writelines(f"{k} : {v}\n")
                with open(f"{out_path_sol}", "w") as f:
                    for k, v in sol.items():
                        f.write(f"{k} : {v}\n")

                total_dist = sum(v["dist_sum"] for v in sol.values())
                solutions.append({"file": filename, "sum": total_dist, "time": end_t - start_t})

            print("====================================")

        except FileNotFoundError:
            print(f"Erro abrindo arquivo — grupo {i+1}: {path}")
            File_path_errors.append(f"G{i+1}")
        except ValueError:
            print(f"Erro de valor — grupo {i+1}: {path}")
            File_value_errors.append(f"G{i+1}")
        except RuntimeError as e:
            print(f"Erro de runtime — grupo {i+1}: {e}")
            File_value_errors.append(f"G{i+1}")

    return File_path_errors, File_value_errors, solutions
    
def get_dist_sum_sol(path,ctv=None):
    if ctv is None: ctv = Constructive(path)
    sol, _ = ctv.run()
    sum=0
    for i in sol.values():  sum+=i["dist_sum"]
    return sum
    
def get_file_errors(File_path_errors_1, File_value_errors_1, File_path_errors_2, File_value_errors_2, type):
    print("Executando instâncias base")
    print(f"Arquivos com caminho errado {type} ")
    if len(File_path_errors_1)==0: print("Nenhum arquivo com problema!")
    else:
        for i in File_path_errors_1:    print(i)
    
    print(f"Arquivos escritos fora do padrão {type}")
    if len(File_value_errors_1)==0: print("Nenhum arquivo com problema!")
    else:
        for i in File_value_errors_1:   print(i) 

    print(f"Arquivos com caminho errado {type} ")
    if len(File_path_errors_2)==0: print("Nenhum arquivo com problema!")
    else:
        for i in File_path_errors_2:    print(i)
    
    print(f"Arquivos escritos fora do padrão {type}")
    if len(File_value_errors_1)==0: print("Nenhum arquivo com problema!")
    else:
        for i in File_value_errors_2:   print(i) 

    print("========================================================================================")

def execute(const=False, local=True):
    for sub in ("construtivo/unico", "construtivo/dual",
                "local/unico",       "local/dual", "tempo/local/dual",
                "tempo/local/unico", "tempo/construtivo/dual","tempo/construtivo/dual"):
        os.makedirs(f"output/img/{sub}", exist_ok=True)

    def sort_and_plot(sol_1, sol_2, path, suffix_label, time=False):
        sol_1.sort(key=lambda e: e["sum"])
        sol_2.sort(key=lambda e: e["sum"])
        plot_instance_sums(sol_1,
            title=f"Soma das distâncias base — {suffix_label}",
            show_mean=True, save_path=f"{path}/inst1.png",
            time=time)
        plot_instance_sums(sol_2,
            title=f"Soma das distâncias diferenciadas — {suffix_label}",
            show_mean=True, save_path=f"{path}/inst2.png",
            time=time)

    if const:
        print("=== Construtivo, tipo único ===")
        _, _, sol_cu1 = execute_instance("base", dual=False, use_local=False)
        _, _, sol_cu2 = execute_instance("dif",  dual=False, use_local=False)
    
        print("=== Construtivo, dois tipos ===")
        _, _, sol_cd1 = execute_instance("base", dual=True, use_local=False)
        _, _, sol_cd2 = execute_instance("dif",  dual=True, use_local=False)
        
        sort_and_plot(sol_cu1, sol_cu2, "output/img/construtivo/unico", "construtivo, 1 tipo")
        sort_and_plot(sol_cd1, sol_cd2, "output/img/construtivo/dual",  "construtivo, 2 tipos")
        
        sort_and_plot(sol_cu1, sol_cu2, "output/img/construtivo/unico", "construtivo, 1 tipo", time=True)
        sort_and_plot(sol_cd1, sol_cd2, "output/img/construtivo/dual",  "construtivo, 2 tipos", time=True)
    if local:
        print("=== Construtivo + Busca Local, tipo único ===")
        _, _, sol_lu1 = execute_instance("base", dual=False, use_local=True)
        _, _, sol_lu2 = execute_instance("dif",  dual=False, use_local=True)
    
        print("=== Construtivo + Busca Local, dois tipos ===")
        _, _, sol_ld1 = execute_instance("base", dual=True, use_local=True)
        _, _, sol_ld2 = execute_instance("dif",  dual=True, use_local=True)
        
        sort_and_plot(sol_lu1, sol_lu2, "output/img/local/unico",       "constr. + busca local, 1 tipo")
        sort_and_plot(sol_ld1, sol_ld2, "output/img/local/dual",        "constr. + busca local, 2 tipos")

        sort_and_plot(sol_lu1, sol_lu2, "output/img/tempo/local/unico",     "constr. + busca local, 1 tipo", time=True,)
        sort_and_plot(sol_ld1, sol_ld2, "output/img/tempo/local/dual",        "constr. + busca local, 2 tipos", time=True,)

execute()
