import math
import json

with open('../Data/nbh_latitude_longitude.json') as f:
    BAIRROS_JF= json.load(f)
    
def gerar_cep_jf( bairro, rng):
    _, _, cmin, cmax, _ = BAIRROS_JF[bairro]
    prefixo = rng.randint(cmin, cmax)          
    sufixo  = rng.randint(0, 999)
    return f"{prefixo:05d}-{sufixo:03d}"

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    Phi1, Phi2 = math.radians(lat1), math.radians(lat2)
    dPhi = Phi2 - Phi1
    dLmbd = math.radians(lon2 - lon1)
    a = math.sin(dPhi/2)**2 + math.cos(Phi1)*math.cos(Phi2)*math.sin(dLmbd/2)**2
    return 2*R*math.asin(math.sqrt(a))
    
def sorteia_bairro_candidato(rng):
    nomes  = list(BAIRROS_JF.keys())
    pesos  = [BAIRROS_JF[b][4] for b in nomes]
    return rng.choices(nomes, weights=pesos)[0]
    
def sorteia_ponto_candidato(bairro, rng, sigma_km=0.8):
    lat0, lon0, *_ = BAIRROS_JF[bairro]

    dlat = rng.gauss(0, sigma_km/111.0)
    dlon = rng.gauss(0, sigma_km/(111.0*math.cos(math.radians(lat0))))
    return lat0 + dlat, lon0 + dlon