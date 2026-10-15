import math
import json
from pickle import POP
from Variables import *
with open('../Data/nbh_latitude_longitude.json') as f:
    BAIRROS_JF= json.load(f)

def gerar_cep_jf( bairro, rng):
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
