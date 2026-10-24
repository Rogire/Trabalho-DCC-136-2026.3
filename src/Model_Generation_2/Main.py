from Variables import *
from Create_Instances_JF import Create_instances
from Profiles import *

def main():
    Instances = Create_instances()
    Instances.gerar_instancia(PERFIS["base"], SEED, CAP_MIN, CAP_MAX,
        {
            "txt": BASE_PATH_TXT + "instancia_1.txt",
            "candidatos": BASE_PATH_CSV + "candidatos_1.csv",
            "escolas": BASE_PATH_CSV + "escolas_1.csv",
            "matriz": BASE_PATH_CSV + "matriz_1.csv",
            "salas": BASE_PATH_CSV + "salas_1.csv"
        },Plot=True)
    Instances.gerar_instancia(PERFIS["diferenciada"], SEED + 1, CAP_MIN, CAP_MAX,
        {
            "txt": BASE_PATH_TXT + "instancia_2.txt",
            "candidatos": BASE_PATH_CSV + "candidatos_2.csv",
            "escolas": BASE_PATH_CSV + "escolas_2.csv",
            "matriz": BASE_PATH_CSV + "matriz_2.csv",
            "salas": BASE_PATH_CSV + "salas_2.csv"
        },Plot=True)

    if BAIXAR_ARQUIVOS:
        try:
            from google.colab import files  # só existe no Colab
            files.download("instancia_1.txt")
            files.download("instancia_2.txt")
            files.download("candidatos_1.csv")
            files.download("escolas_1.csv")
            files.download("matriz_1.csv")
            files.download("candidatos_2.csv")
            files.download("escolas_2.csv")
            files.download("matriz_2.csv")
        except ImportError:
            print("Fora do Colab: arquivos salvos na pasta atual.")
main()