import numpy as np
from collections import Counter
from itertools import combinations

# Busca local pro problema de alocação de candidatos
#   1. Reparo dos tipos: garante vagas de cada tipo >= candidatos do tipo (conserta o construtivo)
#   2. Retirada: quem está numa escola sem vaga do seu tipo vai pra "sem escola"
#   3. Busca local com duas vizinhanças (uma passada de cada por rodada, até nenhuma melhorar):
#        Realocação -> candidato muda pra escola mais perto com vaga do tipo dele
#        Troca      -> dois candidatos do mesmo tipo trocam de escola (funciona com escola lotada)
# Função de avaliação: distância total + penalidade por candidato sem escola

EPS = 1e-9                                                    # ignora melhora que é só erro de ponto flutuante

def somas_de_salas(salas):
    # Todas as capacidades que dá pra montar juntando salas inteiras (cada sala aplica 1 tipo só)
    somas = {0}
    for q in salas:
        somas |= {x + q for x in somas}
    return sorted(somas)

class LocalSearch:
    def __init__(self, ctv):
        # ctv: objeto Constructive depois do ctv.run()
        self.ids_esc  = list(ctv.mat_df.columns)              # "E1", "E2", ... mesmo padrão das chaves do sol
        self.ids_cand = list(ctv.cand_df["id"])               # já sem zeros à esquerda (feito no construtivo)
        self.tipos    = ctv.cand_df["tipo_prova"].to_numpy()
        self.n, self.m = len(self.ids_cand), len(self.ids_esc)
        col = {sid: e for e, sid in enumerate(self.ids_esc)}

        # Representação da solução
        #   aloc[i]   = escola do candidato i
        #   config[e] = {tipo: vagas} da escola e ({} = fechada), até 2 tipos, cada sala com 1 tipo
        # "Sem escola" vira uma escola extra (índice m) com vaga pra todos e distância = penalidade
        # -> quem está de fora é tratado igual aos outros, e pôr numa escola de verdade sempre melhora o custo
        D = ctv.mat_df.to_numpy(float)
        self.pen        = 10 * D.max()                        # maior que qualquer distância
        self.SEM_ESCOLA = self.m
        self.D          = np.column_stack([D, np.full(self.n, self.pen)])
        self.aloc       = np.array([col[ctv.alocacao[c]] if c in ctv.alocacao else self.SEM_ESCOLA
                                    for c in self.ids_cand])

        self.salas  = [ctv.cap_salas[sid] for sid in self.ids_esc]
        self.total  = [sum(s) for s in self.salas]
        self.somas  = [somas_de_salas(s) for s in self.salas]
        self.config = [{} for _ in self.ids_esc]
        for sid, v in ctv.sol.items():
            if "exam" in v:                                   # escola só com "motivo" fica fechada
                t1, t2 = v["exam"]
                self.config[col[sid]] = {t1: v["cap1"], **({t2: v["cap2"]} if t2 else {})}

        self.custo_inicial      = self.Custo()
        self.sem_escola_inicial = int((self.aloc == self.SEM_ESCOLA).sum())

    # Função de avaliação: soma da distância de cada candidato até a escola dele (sem escola custa pen)
    def Custo(self):
        return float(self.D[np.arange(self.n), self.aloc].sum())

    # Passo 1 - Reparo dos tipos
    # Busca em profundidade escola por escola: cada uma mantém o que tem ou redivide as salas (Opcoes)
    # até todo tipo ter vagas >= candidatos. Escolas fechadas e vazias ficam no fim da ordem -> mudam primeiro
    def Reparar_Tipos(self):
        demanda   = Counter(self.tipos)
        usados    = np.bincount(self.aloc, minlength=self.m + 1)[:self.m]
        ordem     = sorted(range(self.m), key=lambda e: (not self.config[e], -usados[e] / self.total[e]))
        cap_resto = [sum(self.total[e] for e in ordem[k:]) for k in range(self.m + 1)]   # vagas das escolas não vistas
        falta     = dict(sorted(demanda.items()))             # candidatos de cada tipo ainda sem vaga garantida
                                                              # (ordem por nome -> empate entre tipos sempre igual)
        nova      = list(self.config)
        sem_saida = set()                                     # estados que já deram errado -> não repete

        def busca(k, todas):
            falta_total = sum(max(f, 0) for f in falta.values())
            if falta_total == 0:
                return True                                   # demanda coberta: escolas que faltam ficam como estão
            estado = (k, tuple(max(falta[t], 0) for t in sorted(falta)))
            if cap_resto[k] < falta_total or estado in sem_saida:
                return False                                  # nem com todas as salas que sobram dá -> volta
            e = ordem[k]
            for conf in self.Opcoes(e, falta, todas):
                for t, q in conf.items():                     # aplica a configuração
                    falta[t] -= q
                nova[e] = conf
                if busca(k + 1, todas):
                    return True
                for t, q in conf.items():                     # desfaz e tenta a próxima
                    falta[t] += q
            nova[e] = self.config[e]
            sem_saida.add(estado)
            return False

        achou = busca(0, todas=False)                         # 1ª passada: só as opções rápidas (resolve o normal)
        if not achou:
            sem_saida.clear()
            achou = busca(0, todas=True)                      # 2ª passada: todas as divisões (quase sem folga)
        if not achou:
            raise RuntimeError("Nenhuma distribuição de tipos cobre a demanda — instância inviável")

        for e in range(self.m):
            if nova[e] != self.config[e]:
                print(f"[REPARO] {self.ids_esc[e]}: {self.config[e] or 'fechada'} -> {nova[e]}")
        self.config = nova
        self.cap = {(e, t): q for e, conf in enumerate(nova) for t, q in conf.items()}
        self.cap.update({(self.SEM_ESCOLA, t): self.n for t in demanda})
        self.escolas_do_tipo = {t: [e for e, tt in self.cap if tt == t] for t in demanda}

    # Configurações que a escola e pode assumir no reparo, dado o que ainda falta de cada tipo
    # Divide as salas entre 2 tipos t e u (1 tipo só = todas as salas pra um lado). Dar a um tipo mais
    # vagas do que falta só desperdiça sala -> só testa divisões sem sobra, e assim não perde solução
    def Opcoes(self, e, falta, todas):
        faltando = sorted((t for t in falta if falta[t] > 0), key=falta.get, reverse=True)   # maior falta primeiro
        total    = self.total[e]
        if len(faltando) == 1:
            return [self.config[e], {faltando[0]: total}]

        def dividir(t, vagas_t, u):                          # vagas_t pro tipo t, o resto das salas pro tipo u
            return {k: q for k, q in ((t, vagas_t), (u, total - vagas_t)) if q > 0}

        # menor capacidade (com salas inteiras) que cobre tudo que falta do tipo t
        cobre = {t: next((x for x in self.somas[e] if x >= falta[t]), total) for t in faltando}

        # Opções rápidas: manter como está, ou cobrir o tipo t com a menor sobra e dar o resto pro u
        ops = [self.config[e]] + [dividir(t, cobre[t], u) for t in faltando for u in faltando if u != t]
        # Só na 2ª passada: divisões em que nem t nem u ficam cobertos
        if todas:
            for t, u in combinations(faltando, 2):
                ops += [dividir(t, x, u) for x in self.somas[e] if total - cobre[u] < x < cobre[t]]
        return ops

    # Passo 2 - Quem não cabe na configuração nova vai pra "sem escola" (os mais longe saem primeiro)
    def Retirar_Excedentes(self):
        for e in range(self.m):
            for t in set(self.tipos[self.aloc == e]):
                ali     = np.flatnonzero((self.aloc == e) & (self.tipos == t))
                excesso = len(ali) - self.cap.get((e, t), 0)
                if excesso > 0:
                    mais_longe = ali[np.argsort(-self.D[ali, e])[:excesso]]
                    self.aloc[mais_longe] = self.SEM_ESCOLA
        self.carga = Counter(zip(self.aloc, self.tipos))     # candidatos em cada (escola, tipo)

    # Vizinhança 1 - Realocação: candidato vai pra escola mais perto com vaga do tipo dele
    # Estratégia: primeira melhora (move assim que acha) indo pro melhor destino
    def Realocacao(self):
        melhorou = False
        for i in range(self.n):
            t, atual = self.tipos[i], self.aloc[i]
            com_vaga = [e for e in self.escolas_do_tipo[t] if e != atual and self.carga[e, t] < self.cap[e, t]]
            if not com_vaga:
                continue
            destino = min(com_vaga, key=lambda e: self.D[i, e])
            if self.D[i, destino] < self.D[i, atual] - EPS:
                self.carga[atual, t]   -= 1
                self.carga[destino, t] += 1
                self.aloc[i] = destino
                melhorou = True
        return melhorou

    # Vizinhança 2 - Troca: i (na escola a) e j (na escola b), do mesmo tipo, trocam de escola
    # Lotação não muda -> funciona mesmo com as escolas cheias. Estratégia: melhor troca de cada par (a, b)
    def Troca(self):
        melhorou = False
        for t, escolas in self.escolas_do_tipo.items():
            do_tipo = self.tipos == t
            for a, b in combinations(escolas, 2):
                while True:
                    A = np.flatnonzero(do_tipo & (self.aloc == a))   # candidatos do tipo t na escola a
                    B = np.flatnonzero(do_tipo & (self.aloc == b))
                    if len(A) == 0 or len(B) == 0:
                        break
                    # ganho da troca (i, j) = ganho_A[i] + ganho_B[j]: as partes são independentes, então
                    # a melhor troca é o melhor i de A com o melhor j de B -> O(n) em vez de testar todos os pares
                    ganho_A = self.D[A, a] - self.D[A, b]             # quanto cada i economiza indo de a pra b
                    ganho_B = self.D[B, b] - self.D[B, a]             # quanto cada j economiza indo de b pra a
                    if ganho_A.max() + ganho_B.max() <= EPS:
                        break
                    i, j = A[ganho_A.argmax()], B[ganho_B.argmax()]
                    self.aloc[i], self.aloc[j] = b, a
                    melhorou = True
        return melhorou

    # Solucao no mesmo formato do ctv.run(), só com as escolas usadas
    def Gerar_Solucao(self):
        alocacao = {c: self.ids_esc[e] for c, e in zip(self.ids_cand, self.aloc)}
        usados   = Counter(alocacao.values())
        sol = {}
        for e, conf in enumerate(self.config):
            sid = self.ids_esc[e]
            if usados[sid]:
                (t1, c1), (t2, c2) = (list(conf.items()) + [(None, 0)])[:2]
                cands = np.flatnonzero(self.aloc == e)
                dist_sum = float(self.D[cands, e].sum()) if len(cands) else 0.0
                sol[sid] = {"dist_sum": dist_sum, "exam": (t1, t2),
                            "cap1": c1, "cap2": c2,
                            "alctd": usados[sid], "sobra": c1 + c2 - usados[sid]}
        return sol, alocacao
    #Loop Principal
    def run(self):
        self.Reparar_Tipos()                                  # 1. vagas de cada tipo >= candidatos do tipo
        self.Retirar_Excedentes()                             # 2. ninguém fica numa escola sem vaga do seu tipo
        # 3. Busca local: cada rodada faz uma passada de realocação e uma de troca
        #    Para quando uma rodada inteira não melhora nada -> ótimo local das duas vizinhanças
        melhorou = True
        while melhorou:
            melhorou_realocacao = self.Realocacao()
            melhorou_troca      = self.Troca()
            melhorou = melhorou_realocacao or melhorou_troca

        sem_escola = int((self.aloc == self.SEM_ESCOLA).sum())
        if sem_escola:                                        # não acontece: o reparo garante vaga pra todos
            raise RuntimeError(f"{sem_escola} candidatos sem escola depois da busca local")
        self.custo_final = self.Custo()
        return self.Gerar_Solucao()
