import math
import json
import pandas as pd
from Variables import *

class Generate_data:
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
        with open('../Data/nbh_latitude_longitude.json') as f:
            dados = json.load(f)
        self.BAIRROS_JF = dados
        
    def gerar_cep(self, x, rng):
        """CEP fictício (faixa 36000-000 a 36099-999) correlacionado com a coordenada x.
        É apenas um rótulo de localização; a distância usa as coordenadas."""
        prefixo = min(99, int(x / AREA_KM * 100))
        return f"36{prefixo:03d}{rng.randint(0, 999):03d}"
   
    def gerar_salas(self, cap_alvo, rng):
        """ Cada sala tem uma capacidade múltipla de PASSO entre SALA_MIN e SALA_MAX ]
        A soma das salas é exatamente cap_alvo."""
        salas, restante = [], cap_alvo
        while restante > 0:
            if restante <= SALA_MAX:
                c = restante                      # última sala
            else:
                # sorteia sem deixar um resto menor que SALA_MIN
                c = rng.randrange(SALA_MIN, min(SALA_MAX, restante - SALA_MIN) + 1, PASSO)
            salas.append(c)
            restante -= c
        return salas
    
    
    def gerar_escolas(self, n_escolas, cap_min, cap_max, desbalancear, prob_segundo, rng):
        # tipos: garante que todos os 6 tipos existam em pelo menos 1 escola
        tipos = TIPOS[:] + [None] * (n_escolas - len(TIPOS))
        pesos = [0.40, 0.25, 0.15, 0.10, 0.05, 0.05] if desbalancear else [1] * len(TIPOS)
        for i in range(len(TIPOS), n_escolas):
            tipos[i] = rng.choices(TIPOS, weights=pesos)[0]
        rng.shuffle(tipos)
    
        escolas = []
        for i in range(n_escolas):
            cap_alvo = rng.randrange(-(-cap_min // PASSO) * PASSO, cap_max + 1, PASSO)  # múltiplo de PASSO
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
    
    
    def gerar_candidatos(self, escolas, utilizacao, agrupar, afastamento, rng):
        # nº de candidatos por tipo = utilização x capacidade (de referência) daquele tipo
        cap_tipo = {t: 0 for t in TIPOS}
        for e in escolas:
            cap_tipo[e["tipo"]] += e["capacidade"]
        n_tipo = {t: int(cap_tipo[t] * utilizacao) for t in TIPOS}
    
        # posições das escolas que PODEM aplicar cada tipo (usadas no afastamento)
        locais_tipo = {t: [(e["x"], e["y"]) for e in escolas if t in e["tipos"]] for t in TIPOS}
    
        # Gerar centros maximizando a distância mínima em relação a todas as escolas
        centros = []
        for _ in range(NUM_BAIRROS):
            melhor_centro = None
            maior_dist_min_escola = -1.0
            
            # Amostra pontos candidatos pelo mapa
            for _ in range(200):
                cx = rng.uniform(0.15, 0.85) * AREA_KM
                cy = rng.uniform(0.15, 0.85) * AREA_KM
                
                dist_escola_min = min(math.hypot(cx - e["x"], cy - e["y"]) for e in escolas)
                
                dist_centros_min = min([math.hypot(cx - ox, cy - oy) for ox, oy in centros] + [float('inf')])
                
                pontuacao = min(dist_escola_min, dist_centros_min)
                
                if pontuacao > maior_dist_min_escola:
                    maior_dist_min_escola = pontuacao
                    melhor_centro = (cx, cy)
                    
            centros.append(melhor_centro)
    
        def sorteia_ponto():
            if not agrupar:
                return rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM)
            cx, cy = rng.choice(centros)
            x = min(max(rng.gauss(cx, 2.0), 0), AREA_KM)
            y = min(max(rng.gauss(cy, 2.0), 0), AREA_KM)
            return x, y
    
        def sorteia_ponto_afastado(t):
            # sorteia várias posições candidatas e escolhe uma com probabilidade proporcional a
            # (distância à escola elegível mais próxima) ^ afastamento -> favorece posições distantes
            props = [sorteia_ponto() for _ in range(PROPOSTAS_AFASTAMENTO)]
            pesos = [min(math.hypot(px - ex, py - ey) for ex, ey in locais_tipo[t]) ** afastamento + 1e-9
                     for px, py in props]
            return rng.choices(props, weights=pesos)[0]
    
        candidatos = []
        for t in TIPOS:
            for _ in range(n_tipo[t]):
                x, y = sorteia_ponto_afastado(t) if afastamento > 0 else sorteia_ponto()
                candidatos.append({"id": "", "x": x, "y": y, "cep": self.gerar_cep(x, rng), "tipo": t})
        rng.shuffle(candidatos)
    
        # numera após embaralhar para o id não revelar a ordem por tipo
        for i, c in enumerate(candidatos, 1):
            c["id"] = f"C{i:05d}"
        return candidatos
    
    
    def matriz_distancias(self, candidatos, escolas):
        return [[round(math.hypot(c["x"] - e["x"], c["y"] - e["y"]), 2) for e in escolas]
                for c in candidatos]
    
    
    def dist_media_elegivel(self, candidatos, escolas):
        """Distância média (km) de cada candidato à escola mais próxima que pode aplicar seu tipo."""
        total = 0.0
        for c in candidatos:
            total += min(math.hypot(c["x"] - e["x"], c["y"] - e["y"])
                         for e in escolas if c["tipo"] in e["tipos"])
        return total / len(candidatos)
    
    
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
        # viabilidade: a atribuição de referência (1 tipo por escola) acomoda todos
        for t in TIPOS:
            n = sum(1 for c in candidatos if c["tipo"] == t)
            cap = sum(e["capacidade"] for e in escolas if e["tipo"] == t)
            assert n <= cap, f"tipo {t}: {n} candidatos > capacidade {cap}"
        return cap_total, razao