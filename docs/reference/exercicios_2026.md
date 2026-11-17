# Lista de exercícios — Análise Estatística

*Semente: 2026 — rode de novo com `--seed 2026` para obter a mesma lista.*

Para cada exercício: verifique os pré-requisitos (outliers, normalidade, variâncias), escolha o teste, calcule e conclua na linguagem do problema. Use α = 5%.


## Exercício 1 — Correlação e regressão

Uma empresa registrou, para 9 casos, as variáveis **Nº de commits na semana** (x) e **Bugs reportados** (y).

x: 15; 40; 31; 25; 25; 48; 55; 15; 41

y: 16; 9; 7; 6; 6; 9; 10; 4; 9

a) Existe correlação entre as variáveis ao nível de 5%? E de 1%?
b) Se existir, classifique a força, calcule r² e interprete.
c) Se fizer sentido, obtenha a reta de regressão, interprete os coeficientes e estime y para x = 35.


## Exercício 2 — Comparação antes × depois

Mediu-se **Tempo de resposta da API (ms)** em 12 indivíduos/itens, antes e depois da otimização (mesmos indivíduos, na mesma ordem).

Antes: 784; 635; 743; 879; 772; 782; 877; 1.019; 714; 962; 652; 821

Depois: 686; 648; 725; 879; 651; 755; 778; 923; 677; 946; 597; 715

a) Ao nível de 5%, há evidência de que o valor diminuiu? (hipótese unilateral definida antes da coleta)
b) Construa o intervalo de 95% de confiança para a diferença média (se o teste for paramétrico).


## Exercício 3 — Comparação de dois grupos

Compare **Tempo de deploy (min)** entre dois grupos independentes.

Equipe A (n = 6): 39; 34; 34; 43; 25; 45

Equipe B (n = 13): 47; 39; 34; 26; 35; 28; 30; 28; 32; 37; 27; 25; 25

a) Há diferença significativa entre os grupos (α = 5%)? Indique o teste usado e justifique.
b) Se houver, qual grupo é maior e com quanto de confiança?


## Exercício 4 — Comparação de 3 ou mais grupos

Deseja-se comparar **Nota final (0 a 100)** entre 3 grupos (Turma manhã, Turma tarde, Turma noite), com 32 observações cada.

Turma manhã: 47; 58; 40; 57; 33; 46; 82; 47; 68; 60; 53; 47; 70; 52; 73; 46; 55; 60; 59; 39; 46; 52; 44; 63; 62; 30; 32; 39; 56; 80; 50; 58

Turma tarde: 39; 30; 49; 59; 46; 63; 52; 49; 55; 54; 61; 42; 27; 51; 43; 49; 66; 39; 57; 59; 54; 61; 45; 43; 60; 57; 63; 52; 66; 47; 39; 29

Turma noite: 64; 39; 50; 79; 65; 75; 44; 27; 72; 39; 56; 58; 44; 73; 73; 61; 55; 57; 43; 52; 54; 46; 65; 39; 50; 30; 61; 63; 62; 88; 66; 45

a) Existe diferença entre os grupos (α = 5%)? Indique o teste e verifique os pré-requisitos.
b) Se existir, quais grupos diferem entre si?


## Exercício 5 — Comparação de 3 ou mais grupos

Deseja-se comparar **Nota final (0 a 100)** entre 3 grupos (Turma manhã, Turma tarde, Turma noite), com 19 observações cada.

Turma manhã: 80; 100; 82; 100; 90; 99; 100; 99; 86; 90; 100; 81; 91; 82; 86; 83; 92; 100; 100

Turma tarde: 60; 58; 51; 69; 62; 56; 51; 64; 58; 58; 37; 38; 60; 56; 57; 57; 60; 55; 57

Turma noite: 87; 66; 85; 82; 75; 67; 79; 86; 58; 74; 74; 64; 65; 52; 58; 52; 65; 66; 66

a) Existe diferença entre os grupos (α = 5%)? Indique o teste e verifique os pré-requisitos.
b) Se existir, quais grupos diferem entre si?


## Exercício 6 — Comparação de proporções

Avaliou-se a ocorrência de **aprovação na disciplina** em dois grupos independentes:

- Turma com monitoria: 31 ocorrências em 62
- Turma sem monitoria: 117 ocorrências em 182

A proporção de aprovação na disciplina difere entre os grupos (α = 5%)?


## Exercício 7 — Comparação de dois grupos

Compare **Resistência do material (MPa)** entre dois grupos independentes.

Fornecedor 1 (n = 15): 344; 362; 263; 320; 323; 314; 364; 376; 329; 320; 266; 266; 321; 298; 260

Fornecedor 2 (n = 10): 258; 270; 285; 258; 254; 261; 265; 232; 282; 316

a) Há diferença significativa entre os grupos (α = 5%)? Indique o teste usado e justifique.
b) Se houver, qual grupo é maior e com quanto de confiança?


## Exercício 8 — Comparação de proporções

Avaliou-se a ocorrência de **conversão de visitantes em clientes** em dois grupos independentes:

- Página versão A: 58 ocorrências em 148
- Página versão B: 41 ocorrências em 63

A proporção de conversão de visitantes em clientes difere entre os grupos (α = 5%)?


## Exercício 9 — Correlação e regressão

Uma empresa registrou, para 30 casos, as variáveis **Nº de commits na semana** (x) e **Bugs reportados** (y).

x: 28; 47; 14; 11; 43; 54; 53; 46; 59; 34; 48; 28; 24; 55; 29; 46; 32; 11; 12; 33; 44; 46; 23; 6; 34; 15; 23; 36; 27; 30

y: 7; 9; 5; 4; 9; 12; 10; 9; 11; 6; 10; 7; 6; 11; 6; 8; 6; 3; 4; 7; 8; 9; 6; 2; 6; 4; 6; 7; 6; 6

a) Existe correlação entre as variáveis ao nível de 5%? E de 1%?
b) Se existir, classifique a força, calcule r² e interprete.
c) Se fizer sentido, obtenha a reta de regressão, interprete os coeficientes e estime y para x = 32.


## Exercício 10 — Comparação antes × depois

Mediu-se **Nota no simulado (0 a 100)** em 17 indivíduos/itens, antes e depois do curso preparatório (mesmos indivíduos, na mesma ordem).

Antes: 63; 55; 57; 58; 49; 58; 54; 76; 55; 65; 64; 49; 48; 56; 67; 54; 53

Depois: 67; 56; 60; 100; 67; 65; 58; 100; 56; 73; 66; 49; 62; 59; 71; 56; 60

a) Ao nível de 5%, há evidência de que o valor aumentou? (hipótese unilateral definida antes da coleta)
b) Construa o intervalo de 95% de confiança para a diferença média (se o teste for paramétrico).
