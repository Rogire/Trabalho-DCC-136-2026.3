import random

SEED = random.randrange(1_000_000)
CAP_MIN = 200          # capacidade mínima por escola
CAP_MAX = 500          # capacidade máxima por escola
BAIXAR_ARQUIVOS = False  # baixa os .txt ao final

# Impressão
PRINTAR = True              # liga/desliga toda a impressão
PRINT_RESUMO = True         # totais, utilização, candidatos e capacidade por tipo
PRINT_CANDIDATOS = True     # lista de candidatos
PRINT_ESCOLAS = True        # escolas (id, cep, coordenadas, tipos, capacidade, nº de salas)
PRINT_SALAS = True          # capacidade de cada sala de cada escola
PRINT_MATRIZ = False        # matriz de distâncias (pode ser enorme)
LIMITE_LINHAS = 15          # máx. de linhas de candidatos/matriz impressas (None = todas)

# Gráfico dos candidatos
PLOTAR = True               # mostra um gráfico por instância (candidatos + escolas)
PLOT_ROTULOS = True         # escreve id e tipos possíveis ao lado de cada escola
PLOT_SALVAR_PNG = False     # também salva instancia_1.png / instancia_2.png

#Informações Escolas
TIPOS = ["M1", "M2", "M3e", "M3s", "M3h", "M3d"]
AREA_KM  = 30.0                            # área quadrada (km x km) onde tudo é sorteado
SALA_MIN = 20                               # menor capacidade possível de uma sala
SALA_MAX = 100                              # maior capacidade possível de uma sala
PASSO = 5                                   # capacidades sempre múltiplas de PASSO (20, 25, 30, ... 100)
PROPOSTAS_AFASTAMENTO = 20                  # nº de posições sorteadas por candidato quando afastamento > 0
NUM_BAIRROS = 8                             # nº de centros em torno dos quais os candidatos são agrupados

MAX_USAGE = 0.98
MIN_USAGE = 0.80

#Caminhos
PATH_JSON = "../Data/cepsjf_consolidado.json"
PATH_CSV  = "../Data/Relacao_Bairros_JF.csv"
PATH_MEAN = "../Data/nbh_latitude_longitude.json"

BASE_PATH_TXT = "../../../Instancias_criadas/txt/"
BASE_PATH_CSV = "../../../Instancias_criadas/csv/"


POP_JF = 540756
DATA_MAIN_NBH = {
    "Benfica":
        {'pop':23414,'peso':23414/POP_JF},
    "São Mateus":
        {'pop':19255,'peso':19255/POP_JF},
    "São Pedro":
        {'pop':18940,'peso':18940/POP_JF},
    "Centro":
        {'pop':18569,'peso':18569/POP_JF},
    "Santa Cruz":
        {'pop':17032,'peso':17032/POP_JF},
    "Ipiranga":
        {'pop':16478,'peso':16478/POP_JF},
    "Progresso":
        {'pop':16191,'peso':16191/POP_JF},
    "Maçunge da Grama":
        {'pop':15364,'peso':15364/POP_JF},
    "Francisco Bernardino":
        {'pop':14145,'peso':14145/POP_JF},
    "Vale dos Bandeirantes":
        {'pop':12990,'peso':12990/POP_JF}
}

ESTIMATED_NBH_POP=0
for i in DATA_MAIN_NBH.values():
    ESTIMATED_NBH_POP+=i['pop']

ESTIMATED_NBH_POP = (POP_JF-ESTIMATED_NBH_POP)/101
ESTIMATED_NBH_W = ESTIMATED_NBH_POP/POP_JF
