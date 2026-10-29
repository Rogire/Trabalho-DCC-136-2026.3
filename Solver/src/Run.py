from Construtivo import *

BASE_NAME = "../../Instancias_Grupos/"
LEN_GRUPOS = 14
def get_filename(t,i):
    return f"Instancia1_G{i}" if t == "base" else f"Instancia2_G{i}"

def execute():
    File_path_errors = []
    File_value_errors = []
    
    print("Executando instâncias base")
    for i in range(LEN_GRUPOS):
        try:
            ctv = Constructive(BASE_NAME+get_filename("base",i+1)+".txt")
            ctv.run()
        except FileNotFoundError:
            print(f"Erro abrindo o arquivo para o grupo {i+1}")
            File_path_errors.append(f"G{i+1}")
        except ValueError:
            print("Erro na escrita do arquivo")
            File_value_errors.append(f"G{i+1}")
            
    print("========================================================================================")
    print("Executando instâncias diferenciada")
    for i in range(LEN_GRUPOS):
        try:
            print(f"Executando instância do grupo {i+1}:")
            ctv = Constructive(BASE_NAME+get_filename("diferenciada",i+1)+".txt")
            ctv.run()
        except FileNotFoundError:
            print(f"Erro abrindo o arquivo para o grupo {i+1}")
            File_path_errors.append(f"G{i+1}")
        except ValueError:
            print("Erro na escrita do arquivo")
            File_value_errors.append(f"G{i+1}")

    print("Arquivos com caminho errado")
    sum=0
    for i in File_path_errors:
        print(i)
        sum+=1

    print(sum)
    print("Arquivos escritos fora do padrão")
    sum=0

    for i in File_path_errors:
        print(i)
        sum+=1
    print(sum)
    print("========================================================================================")
    
execute()
