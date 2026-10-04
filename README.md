# Trabalho de Inteligência Computacional - DCC 136 2026.3

# Alunos: 
- Igor Correa Trifilio Campos
- Arthur Malvacini

# Enunciado do trabalho

## Parte 1 - Geração das instâncias
1. Instâncias a serem geradas
- Instância 1: Instância-base: uma instância representativa do problema, sem
características especialmente planejadas para aumentar sua dificuldade;
- Instância 2: Instância diferenciada: uma segunda instância na qual o grupo deverá
introduzir, de forma deliberada, alguma característica que altere a dificuldade de
resolução do problema.

2. Dados da instância

**Candidatos**
O número de candidatos deverá ser definido de forma que represente aproximadamente
80% a 95% da capacidade total disponível dos locais de prova.
Para cada candidato, devem ser informados:
- identificador do candidato;
- localização (CEP);
- tipo de prova a ser realizado.
- 
**Locais de prova - Escolas**
Para cada local, devem ser informados:
- identificador da escola;
- localização;
- capacidade (200 a 500 alunos);
- estrutura (número de salas e capacidade de cada sala);
- tipo de prova que o local poderá oferecer.

**Tipos de prova**
Considere os seguintes tipos:
M1, M2, M3e, M3s, M3h e M3d.
Cada candidato deverá estar associado a um desses tipos, e cada local de prova poderá
oferecer apenas um tipo de prova.

4. Regras de geração
Nesse caso, a distância entre um candidato e um local poderá ser calculada a partir das
localizações utilizadas na geração.
O grupo deve garantir que:
- todos os candidatos possam ser alocados;
- a capacidade total dos locais seja suficiente para acomodar todos os candidatos;
- os dados sejam consistentes com as regras do problema;
- as duas instâncias possuam tamanhos e características compatíveis com os
parâmetros definidos nesta atividade.


Linguagem de implementação: Python

## Parte 2 - Implementação do algoritmo
# Trabalho-Inteligencia-Computacional-DCC-136-2026.3
