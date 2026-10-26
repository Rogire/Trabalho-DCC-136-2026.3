# Objetivo
O objetivo é desenvolver uma solução capaz de selecionar locais para a realização
das provas e alocar os candidatos aos locais selecionados, buscando reduzir a distância
total percorrida pelos candidatos e respeitando as restrições do problema.​

## Métricas relevantes:
    - D = Distância entre a escola e o aluno (Quanto menor melhor)
    - C = Capacidade da escola (Quanto maior melhor)

Fazer tipo um KNN:
1. Definir K vizinhos do ponto (escola)
    - Valor de K inicial: Vai ser a capacidade máxima C da escola
    - Os vizinhos definidos para uma escola i serão os C pontos mais próximos da escola menos aqueles que, dentre esses estiverem mais próximos de uma outra escola j

2. Ordenar as escolas por menor distâncias em relação aos seus K-vizinhos
  - O processo é feito utilizando o dataframe da matriz de distâncias entre candidato e escola, onde cada linha representa um aluno e cada coluna uma escola
  - A manipulação utilizando o dataframe permite que o atributo Name de cada linha permaneça o mesmo entre o daframe de candidatos e o da matriz

3. Na primeira vez ao definir os K vizinhos da escola, deve-se definir os dois tipos de prova da escola nas colunas e caso já existam valores não se deve fazer nada
  - Métricas de melhor prova a ser aplicada:
    - Maior proporção de tipos de prova dos vizinhos da escola em relação ao total de candidatos que vão fazer esse tipo de prova
    - D = Distância entre a escola e o aluno (Quanto menor melhor)
    - C = Capacidade da escola (Quanto maior melhor)

4. Filtrar os alunos referentes a escola no topo da lista, e alocá-los

5. Caso a escola tenha esgotado a suas vagas, ela é removida da lista

6. Os candidatos são removidos do dataframe de candidatos e suas linhas da matriz de distancias também

7. Adicionar a solução
  - Modelo de resposta:
  {
    "E01":{
      "dist":300,
      "exam":"M3h"
    },
    "E05":{
    ...
    }
  }
  
8. Repetir enquanto o número de candidatos for maior que 0
