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
    cand_df, esc_df, mat_df, NS,NC = txt_to_df(File)
    
    esc_df["id"] = remove_0lefts(esc_df["id"])
    cand_df["id"]= remove_0lefts(cand_df["id"])
    
    calculate_capacity(esc_df)

    # soma das distâncias entre os alunos alocados na escola e a escola
    sum_of_dists = {f"{k}":0 for k in esc_df["id"]}
    esc_df = esc_df.sort_values(by=["capacidade_total"], ascending=False)

    Exams = cand_df["tipo_prova"].unique()
    total_exams_types={f"{k}":0 for k in cand_df["tipo_prova"]}
    for exam in cand_df["tipo_prova"] : total_exams_types[exam] +=1
    
    def step(esc_cp,cand_cp, mat_cp, nc,ns, sol):
        if(nc <= 0 or ns <= 0):
            print("Solução encontrada!")
            print(f"{nc}, {ns}")
            return sol
        
        K = nc//ns
        K_dists = []
        M_props = []
        
        for i in esc_cp['id']:
            sum_of_types = {f"{k}":0 for k in Exams}
            
            ordered_dists = pd.DataFrame(mat_cp[i]).sort_values(by=[i])
            K_dist = ordered_dists[0:K]
            dist_sum = sum(K_dist[i])
            sum_of_dists[i] = dist_sum
            
            K_dists.append(dist_sum)            
            for i in K_dist.index:
                candidate = cand_cp.loc[i]
                sum_of_types[candidate["tipo_prova"]] += 1

            proportions = {key: (value/total_exams_types[key]) for key, value in sum_of_types.items()}
            majority_prop = max(proportions, key=lambda k: proportions[k])

            M_props.append(majority_prop)
            
        esc_cp["dist_sum"] = K_dists
        esc_cp["tipo_prova"] = M_props
        ordered_dists = esc_cp.sort_values(by=['dist_sum'])

        best = ordered_dists.iloc[0]
        ordered = pd.DataFrame(mat_cp[best["id"]]).sort_values(by=[best["id"]])[0:K]
        
        allocated_cand = cand_cp.loc[ordered.index].copy()
        
        allocated_cand = allocated_cand[allocated_cand["tipo_prova"]==best["tipo_prova"]]
        allocated_cand["escola"] = best["id"]
        num_allocated = allocated_cand.shape[0]


        sol[best["id"]] = {"dist":best["dist_sum"], "exam":best["tipo_prova"], "cap":best["capacidade_total"], "alctd": num_allocated}

        ordered_dists.drop(best.name, axis=0, inplace=True)
        ns-=1

        cand_cp.drop(index=allocated_cand.index, inplace=True)
        mat_cp.drop(index=allocated_cand.index, inplace=True)
        
        nc -= num_allocated

        return step(ordered_dists, cand_cp, mat_cp, nc, ns, sol)

    solution = step(esc_df.copy(), cand_df.copy(), mat_df.copy(), NC, NS, {})
    return solution
    
res = construtivo(PATH_BASE);

print(res)