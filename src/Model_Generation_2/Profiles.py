from Variables import MAX_USAGE

PERFIS = {
    "base": {
        "utilizacao": 0.85,
        "agrupar_candidatos": False,       # agora: candidatos espalhados pelo bairro (sigma maior)
        "desbalancear_tipos": False,
        "prob_segundo_tipo": 0.0,
        "afastamento": 0.0,
        "sigma_km_escolas": 0.5,           # NOVO: dispersão das escolas no bairro
        "sigma_km_candidatos": 1.2,        # NOVO: dispersão dos candidatos no bairro
    },
    "diferenciada": {
        "utilizacao": MAX_USAGE,
        "agrupar_candidatos": True,        # agora: concentrados no centroide (sigma pequeno)
        "desbalancear_tipos": True,
        "prob_segundo_tipo": 0.0,
        "afastamento": 0.0,
        "sigma_km_escolas": 0.4,
        "sigma_km_candidatos": 0.4,
    },
}
