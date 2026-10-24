import pandas as pd

TIPOS = {"M1", "M2", "M3e", "M3s", "M3h", "M3d"}
PATH_BASE = "../../Instancias_criadas/Instancia1_G7.txt"
PATH_DIF = "../../Instancias_criadas/Instancia2_G7.txt"

CANDIDATES_HEADER = "# CANDIDATOS (id, CEP, tipo_prova, latitude, longitude)"
CANDIDATES_COLUMNS  = ["id", "CEP", "tipo_prova", "latitude", "longitude"]

SCHOOLS_HEADER = "# ESCOLAS (id, CEP, latitude, longitude, num_salas, capacidades_salas)"
SCHOOLS_COLUMNS  = ["id", "CEP", "latitude", "longitude", "num_salas", "capacidades_salas"]

MATRICE_HEADER = "# MATRIZ_DISTANCIAS (linhas=candidatos, colunas=escolas, em km)"

def txt_to_df(File):
    writing = "nothing"
    with open("candidatos.csv", 'w') as candidatos_csv:
        pass
    with open("escolas.csv", 'w') as escolas_csv:
        pass

    with open(File, "r") as f:
        for line in f:
            if line.rstrip('\n') == CANDIDATES_HEADER:
                writing = "candidates"
                with open("candidatos.csv",'a') as candidatos_csv:
                    for i in CANDIDATES_COLUMNS:
                        candidatos_csv.writelines(f"{i},")
                    candidatos_csv.write("\n")
                continue
            if line.rstrip('\n') == SCHOOLS_HEADER:
                writing = "schools"
                with open("escolas.csv",'a') as escolas_csv:
                    for i in CANDIDATES_COLUMNS:
                        escolas_csv.writelines(f"{i},")
                    escolas_csv.write("\n")
                continue
            if line.rstrip('\n') == MATRICE_HEADER: writing = "nothing"

            match(writing):
                case "candidates":
                    with open("candidatos.csv", 'a') as candidatos_csv:
                        candidatos_csv.write(line)
                case "schools":
                    with open("escolas.csv", 'a') as escolas_csv:
                        escolas_csv.write(line)

    cand_df = pd.read_csv("candidatos.csv")
    esc_df = pd.read_csv("escolas.csv")
    cand_df = cand_df.drop(cand_df.columns[-1], axis=1)
    esc_df = esc_df.drop(esc_df.columns[-1],axis=1)

    return cand_df, esc_df

def construtivo(File):
    cand_df, esc_df = txt_to_df(File)
    print(cand_df.columns, cand_df.shape)
    print(cand_df.head())

    print(esc_df.columns, esc_df.shape)
    print(esc_df.head())
construtivo(PATH_BASE);
