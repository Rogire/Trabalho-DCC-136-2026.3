from Variables import MAX_USAGE

PERFIS = {
    "base": {
        "utilizacao": 0.85,           # candidatos / capacidade total (0.80 a 0.95)
        "agrupar_candidatos": False,  # False = candidatos uniformes na área
        "desbalancear_tipos": False,  # False = tipos distribuídos uniformemente nas escolas
        "prob_segundo_tipo": 0.0,     # chance de a escola poder oferecer um 2º tipo (máx. 2)
        "afastamento": 0.0,           # 0 = posição do candidato independe das escolas do seu tipo

    },
    "diferenciada": {
        "utilizacao": MAX_USAGE,
        "agrupar_candidatos": True,   # candidatos concentrados em poucos "bairros"
        "desbalancear_tipos": True,   # alguns tipos têm pouquíssima capacidade
        "prob_segundo_tipo": 0.0,
        "afastamento": 0.0,           # > 0 = candidatos tendem a ficar longe das escolas que aplicam seu tipo
                                      # (peso = distância ^ afastamento; quanto maior, mais forte o efeito)
    },
}