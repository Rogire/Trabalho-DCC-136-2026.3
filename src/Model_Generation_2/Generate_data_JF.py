import math
import json
from Variables import *

class Generate_data_test:
    def __init__(self, 
        SALA_MIN=SALA_MIN, SALA_MAX=SALA_MAX, 
        AREA_KM=AREA_KM, PASSO=PASSO, 
        TIPOS=TIPOS, NUM_BAIRROS=NUM_BAIRROS, 
        PROPOSTAS_AFASTAMENTO=PROPOSTAS_AFASTAMENTO,
        MIN_USAGE=MIN_USAGE, MAX_USAGE=MAX_USAGE
    ) -> None:
            
        self.SALA_MIN = SALA_MIN
        self.SALA_MAX = SALA_MAX
        self.AREA_KM = AREA_KM
        self.PASSO = PASSO
        self.TIPOS = TIPOS
        self.NUM_BAIRROS = NUM_BAIRROS
        self.PROPOSTAS_AFASTAMENTO= PROPOSTAS_AFASTAMENTO
        self.MIN_USAGE= MIN_USAGE
        self.MAX_USAGE= MAX_USAGE
        self.LAT_MIN, self.LAT_MAX = -21.95, -21.55   # limites de lat e long de JF
        self.LON_MIN, self.LON_MAX = -43.60, -43.20
        
        with open('../../Data/nbh_latitude_longitude.json') as f:
            self.BAIRROS_JF= json.load(f)

    def gerar_cep_jf(self,bairro, rng):
        cmin = self.BAIRROS_JF[bairro]["cmin"]
        cmax = self.BAIRROS_JF[bairro]["cmax"]
        prefixo = rng.randint(cmin, cmax)
        sufixo  = rng.randint(0, 999)
        return f"{prefixo // 1000:05d}-{sufixo:03d}"

    def haversine_km(self,la1, lo1, la2, lo2):
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

    def sorteia_bairro_candidato(self,rng):
        nomes  = list(self.BAIRROS_JF.keys())
        pesos  = [self.BAIRROS_JF[b]['w'] for b in nomes]
        return rng.choices(nomes, weights=pesos)[0]

    def sorteia_ponto_candidato(self,bairro, rng, sigma_km=0.8):
       lat0 = self.BAIRROS_JF[bairro]["latitude"]
       lon0 = self.BAIRROS_JF[bairro]["longitude"]
   
       for _ in range(100):                     
           dlat = rng.gauss(0, sigma_km/111.0)
           dlon = rng.gauss(0, sigma_km/(111.0*math.cos(math.radians(lat0))))
           lat, lon = lat0 + dlat, lon0 + dlon
           if self.LAT_MIN <= lat <= self.LAT_MAX and self.LON_MIN <= lon <= self.LON_MAX:
               return lat, lon
   
       return (min(max(lat0, self.LAT_MIN), self.LAT_MAX),
               min(max(lon0, self.LON_MIN), self.LON_MAX))


    def _amostra_ponderada_sem_reposicao(self,itens, pesos, k, rng):
        """Sorteia k itens sem reposição, respeitando os pesos.
        Complexidade O(k·n) — ok para n pequeno (bairros de uma cidade)."""
        itens  = list(itens); pesos  = list(pesos)
        escolhidos = []
        for _ in range(k):
            idx = rng.choices(range(len(itens)), weights=pesos)[0]
            escolhidos.append(itens.pop(idx))
            pesos.pop(idx)
        return escolhidos

    def gerar_salas(self, cap_alvo, rng):
        """ Cada sala tem uma capacidade múltipla de PASSO entre SALA_MIN e SALA_MAX ]
        A soma das salas é exatamente cap_alvo."""
        salas, restante = [], cap_alvo
        while restante > 0:
            if restante <= SALA_MAX:
                c = restante                      # última sala
            else:
                c = rng.randrange(SALA_MIN, min(SALA_MAX, restante - SALA_MIN) + 1, PASSO)
            salas.append(c)
            restante -= c
        return salas

    def gerar_escolas(self, n_escolas, cap_min, cap_max,
                      desbalancear, prob_segundo, rng, sigma_km=0.5):
        tipos  = TIPOS[:] + [None] * (n_escolas - len(TIPOS))
        pesos  = [0.40, 0.25, 0.15, 0.10, 0.05, 0.05] if desbalancear else [1] * len(TIPOS)
        for i in range(len(TIPOS), n_escolas):
            tipos[i] = rng.choices(TIPOS, weights=pesos)[0]
        rng.shuffle(tipos)

        nomes  = list(self.BAIRROS_JF.keys())
        pesos_b = [self.BAIRROS_JF[b]["w"] for b in nomes]

        if n_escolas <= len(nomes):
            bairros_escolhidos = self._amostra_ponderada_sem_reposicao(
                nomes, pesos_b, n_escolas, rng
            )
        else:
            bairros_escolhidos = []
            while len(bairros_escolhidos) < n_escolas:
                k = min(len(nomes), n_escolas - len(bairros_escolhidos))
                bairros_escolhidos.extend(
                    self._amostra_ponderada_sem_reposicao(nomes, pesos_b, k, rng)
                )

        escolas = []
        for i in range(n_escolas):
            cap_alvo = rng.randrange(-(-cap_min // PASSO) * PASSO, cap_max + 1, PASSO)
            salas    = self.gerar_salas(cap_alvo, rng)

            bairro   = bairros_escolhidos[i]
            lat, lon = self.sorteia_ponto_candidato(bairro, rng, sigma_km=sigma_km)

            tipos_ok = [tipos[i]]
            if rng.random() < prob_segundo:
                tipos_ok.append(rng.choice([t for t in TIPOS if t != tipos[i]]))

            escolas.append({
                "id":         f"E{i + 1:02d}",
                "latitude":   lat,
                "longitude":  lon,
                "bairro":     bairro,
                "cep":        self.gerar_cep_jf(bairro, rng),
                "salas":      salas,
                "capacidade": sum(salas),
                "tipo":       tipos[i],
                "tipos":      tipos_ok,
            })
        return escolas
        
    def dist_media_elegivel(self, candidatos, escolas):
        """Distância média (km) de cada candidato à escola mais próxima que pode aplicar seu tipo."""
        if not candidatos:
            return 0.0
        total = 0.0
        for c in candidatos:
            elegiveis = [
                self.haversine_km(c["latitude"], c["longitude"],
                             e["latitude"], e["longitude"])
                for e in escolas if c["tipo"] in e["tipos"]
            ]
            if not elegiveis:
                raise ValueError(
                    f"candidato {c['id']} tipo {c['tipo']}: nenhuma escola elegível"
                )
            total += min(elegiveis)
        return total / len(candidatos)
        
    def matriz_distancias(self,candidatos, escolas):
        return [[round(self.haversine_km(c["latitude"], c["longitude"],
                                    e["latitude"], e["longitude"]), 2)
                 for e in escolas]
                for c in candidatos]

    def gerar_candidatos(self,escolas, utilizacao, agrupar, afastamento, rng, sigma_km=0.5):
        cap_tipo = {t: 0 for t in TIPOS}
        for e in escolas:
            cap_tipo[e["tipo"]] += e["capacidade"]

        cap_total = sum(cap_tipo.values())
        total_alvo = int(cap_total * utilizacao)
        n_tipo = {t: int(cap_tipo[t] * utilizacao) for t in TIPOS}
        resto  = total_alvo - sum(n_tipo.values())
        
        frac = sorted(TIPOS, key=lambda t: cap_tipo[t] * utilizacao - n_tipo[t], reverse=True)
        for i in range(resto):
            n_tipo[frac[i]] += 1

        locais_tipo = {
            t: [(e["latitude"], e["longitude"]) for e in escolas if t in e["tipos"]]
            for t in TIPOS
        }

        sigma_km = sigma_km if agrupar else 1.2 

        def sorteia_ponto():
            bairro   = self.sorteia_bairro_candidato(rng)
            lat, lon = self.sorteia_ponto_candidato(bairro, rng, sigma_km=sigma_km)
            return lat, lon, bairro

        def sorteia_ponto_afastado(t):
            props = [sorteia_ponto() for _ in range(PROPOSTAS_AFASTAMENTO)]
            pesos = [
                min(self.haversine_km(plat, plon, elat, elon)
                    for elat, elon in locais_tipo[t]) ** afastamento + 1e-9
                for plat, plon, _ in props
            ]
            return rng.choices(props, weights=pesos)[0]

        candidatos = []
        for t in TIPOS:
            for _ in range(n_tipo[t]):
                if afastamento != 0:
                    lat, lon, bairro = sorteia_ponto_afastado(t)
                else:
                    lat, lon, bairro = sorteia_ponto()

                candidatos.append({
                    "id":        "",
                    "latitude":  lat,
                    "longitude": lon,
                    "bairro":    bairro,
                    "cep":       self.gerar_cep_jf(bairro, rng),
                    "tipo":      t,
                })

        rng.shuffle(candidatos)
        for i, c in enumerate(candidatos, 1):
            c["id"] = f"C{i:05d}"
        return candidatos
    
    def validar(self, candidatos, escolas):
        cap_total = sum(e["capacidade"] for e in escolas)
        assert 10 <= len(escolas) <= 20, "nº de escolas fora de 10..20"
        assert len(candidatos) <= cap_total, "candidatos excedem a capacidade total"
        razao = len(candidatos) / cap_total
        
        assert MIN_USAGE <= razao <= MAX_USAGE + 1e-9, f"utilização fora de 80-95%: {razao:.3f}"
        for e in escolas:
            assert e["capacidade"] == sum(e["salas"])
            assert 1 <= len(e["tipos"]) <= 2, "escola com mais de 2 tipos"
            assert e["tipo"] in e["tipos"]

        for t in TIPOS:
            n = sum(1 for c in candidatos if c["tipo"] == t)
            cap = sum(e["capacidade"] for e in escolas if e["tipo"] == t)
            assert n <= cap, f"tipo {t}: {n} candidatos > capacidade {cap}"

        for e in escolas:
            assert e["bairro"] in self.BAIRROS_JF, f"bairro desconhecido: {e['bairro']}"
            lat_ok = -21.95 <= e["latitude"] <= -21.55
            lon_ok = -43.60 <= e["longitude"] <= -43.20
            assert lat_ok and lon_ok, f"escola {e['id']} fora do bounding box de JF"
        return cap_total, razao

gen = Generate_data_test()