from Variables import MAX_USAGE

PERFIS = {
    "base": {
        "utilizacao": 0.8,
        "agrupar_candidatos": True,
        "desbalancear_tipos": False,
        "prob_segundo_tipo": 0.0,
        "afastamento": -10.0,
        "sigma_km_escolas": 0.4,
        "sigma_km_candidatos": 1.2,
    },
    "diferenciada": {
        "utilizacao": MAX_USAGE - 0.02,
        "agrupar_candidatos": True,
        "desbalancear_tipos": True,
        "prob_segundo_tipo": 0.0,
        "afastamento": -15.0,
        "sigma_km_escolas": 0.35,
        "sigma_km_candidatos": 0.6,
    },
}
