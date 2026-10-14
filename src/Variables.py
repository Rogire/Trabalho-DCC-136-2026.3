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

TIPOS = ["M1", "M2", "M3e", "M3s", "M3h", "M3d"]
AREA_KM  = 30.0                            # área quadrada (km x km) onde tudo é sorteado
SALA_MIN = 20                               # menor capacidade possível de uma sala
SALA_MAX = 100                              # maior capacidade possível de uma sala
PASSO = 5                                   # capacidades sempre múltiplas de PASSO (20, 25, 30, ... 100)
PROPOSTAS_AFASTAMENTO = 20                  # nº de posições sorteadas por candidato quando afastamento > 0
NUM_BAIRROS = 8                             # nº de centros em torno dos quais os candidatos são agrupados

BASE_PATH_TXT = "Instancias/txt/"
BASE_PATH_CSV = "Instancias/csv/"

MAX_USAGE = 0.98
MIN_USAGE = 0.80


PATH_JSON = "../Data/cepsjf_consolidado.json"
PATH_CSV  = "../Data/Relacao_Bairros_JF.csv"
PATH_MEAN = "../Data/nbh_latitude_longitude.json"