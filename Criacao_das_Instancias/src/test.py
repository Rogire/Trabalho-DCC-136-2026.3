import math
import json
import pandas as pd
from pickle import POP
from Variables import *

with open('../Data/nbh_latitude_longitude.json') as f:
    BAIRROS_JF= json.load(f)

def gerar_cep_jf(bairro, rng):
    cmin = BAIRROS_JF[bairro]["cmin"]
    cmax = BAIRROS_JF[bairro]["cmax"]
    prefixo = rng.randint(cmin, cmax)
    sufixo  = rng.randint(0, 999)
    return f"{prefixo:05d}-{sufixo:03d}"


def haversine_km(la1, lo1, la2, lo2):
    """
        Converte o sistema para coordenadas geográficas usando a fórmula de
        harversine
    """
    R = 6371.0
    lat1, lat2 = math.radians(la1), math.radians(la2)
    difLa = lat2 - lat1
    difLo = math.radians(lo2 - lo1)
    a = math.sin(difLa/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(difLo/2)**2
    return 2*R*math.asin(math.sqrt(a))

def sorteia_bairro_candidato(rng):
    nomes  = list(BAIRROS_JF.keys())
    pesos  = [BAIRROS_JF[b]['w'] for b in nomes]
    return rng.choices(nomes, weights=pesos)[0]

def sorteia_ponto_candidato(bairro, rng, sigma_km=0.8):
    lat0 = BAIRROS_JF[bairro]["latitude"]
    lon0 = BAIRROS_JF[bairro]["longitude"]
    dlat = rng.gauss(0, sigma_km/111.0)
    dlon = rng.gauss(0, sigma_km/(111.0*math.cos(math.radians(lat0))))
    return lat0 + dlat, lon0 + dlon

def gerar_escolas(self, n_escolas, cap_min, cap_max, desbalancear, prob_segundo, rng):
        # tipos: garante que todos os 6 tipos existam em pelo menos 1 escola
        tipos = TIPOS[:] + [None] * (n_escolas - len(TIPOS))

        total_bairros = pd.read_csv('../Data/Relacao_Bairros_JF.csv')['neighborhood_range']
        with open("../Data/nbh_latitude_longitude.json") as f:
            dados = json.load(f)

        index=0
        for i in total_bairros:
            tipos[index] = rng.choices(TIPOS, weights=dados[i].w)[0]
            index = enumerate(i)

        rng.shuffle(tipos)

        escolas = []
        for i in range(n_escolas):
            cap_alvo = rng.randrange((cap_min // PASSO) * PASSO, cap_max + 1, PASSO)  # múltiplo de PASSO
            salas = self.gerar_salas(cap_alvo, rng)
            x, y = rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM)
            # "tipo"  = tipo de referência (solução plantada; garante viabilidade; NÃO vai ao arquivo)
            # "tipos" = tipos que a escola pode oferecer (1 ou 2, incluindo o de referência)
            tipos_ok = [tipos[i]]
            if rng.random() < prob_segundo:
                tipos_ok.append(rng.choice([t for t in TIPOS if t != tipos[i]]))
            escolas.append({
                "id": f"E{i + 1:02d}", "x": x, "y": y, "cep": self.gerar_cep(x, rng),
                "salas": salas, "capacidade": sum(salas), "tipo": tipos[i], "tipos": tipos_ok,
            })
        return escolas
