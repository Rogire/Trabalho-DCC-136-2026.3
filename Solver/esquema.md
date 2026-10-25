# Objetivo
O objetivo é desenvolver uma solução capaz de selecionar locais para a realização
das provas e alocar os candidatos aos locais selecionados, buscando reduzir a distância
total percorrida pelos candidatos e respeitando as restrições do problema.​

## Métricas relevantes:
    - D = Distância entre a escola e o aluno (Quanto menor melhor)
    - C = Capacidade da escola (Quanto maior melhor)


- Ordenar as escolas de forma decrescente por capacidade : Feito

Fazer tipo um KNN:
1. Definir K vizinhos do ponto
    - São os alunos em volta da escola
    - Valor de K inicial: Média aritmética simples de total de candidatos por escolas

2. Métricas de melhor prova a ser aplicada:
    - Maior proporção de tipos de prova pelos vizinhos da escola em relação ao total de candidatos que vão fazer esse tipo de prova
    - D = Distância entre a escola e o aluno (Quanto menor melhor)
    - C = Capacidade da escola (Quanto maior melhor)

3. Definir os ranks os melhores tipos de prova
4. Alocar o aluno na melhor escola
