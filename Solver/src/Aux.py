import pandas as pd
from Variables import *

PATH_CAND = "CSV/candidatos.csv"
PATH_SCH = "CSV/escolas.csv"
PATH_MAT = "CSV/matrice.csv"

def txt_to_df(File):
    NS,NC = 0,0
    writing = "nothing"
    with open(PATH_CAND, 'w') as candidatos_csv: pass
    with open(PATH_SCH, 'w') as escolas_csv: pass
    with open(PATH_MAT, 'w') as matrice_csv: pass

    with open(File, "r") as f:
        for line in f:
            str_value = line.rstrip("\n")
            if str_value.find("NUM_CANDIDATOS:") != -1: NC = int(str_value[str_value.find(":")+1:])
            if str_value.find("NUM_ESCOLAS:") != -1:    NS = int(str_value[str_value.find(":")+1:])
                
            if line.rstrip('\n') == CANDIDATES_HEADER:
                writing = "candidates"
                with open(PATH_CAND,'a') as candidatos_csv:
                    for i in CANDIDATES_COLUMNS:
                        candidatos_csv.writelines(f"{i},")
                    candidatos_csv.write("\n")
                continue
                
            if str_value == SCHOOLS_HEADER:
                writing = "schools"
                with open(PATH_SCH,'a') as escolas_csv:
                    for i in SCHOOLS_COLUMNS:
                        escolas_csv.writelines(f"{i},")
                    escolas_csv.write("\n")
                continue
                
            if str_value == MATRICE_HEADER: 
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
