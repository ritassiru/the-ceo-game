# The CEO Game — instruções para o Claude

Converse com o professor em **português**. O jogo em si é em **inglês**, com
apoio em português (glossário, dicas).

## O projeto

Jogo *choose your own adventure* para praticar **First e Second Conditional**,
feito pelo Prof. Ritaciro Cavalcante (IFAL Campus Viçosa) para o 2º ano de
inglês do Ensino Médio Integrado (Informática e Administração).

Público: adolescentes, nível **A2/B1**, jogando **no celular**, muitas vezes
com internet limitada. Tudo precisa funcionar em tela pequena, no modo claro e
no escuro, e **sem internet**.

## Arquitetura

```
fonte/template.html       visual e lógica (HTML + CSS + JS num arquivo só)
fonte/decisions.json      as situações do jogo
fonte/irreg.json          verbos irregulares do glossário
fonte/endings_params.json limites dos 9 finais
fonte/build.py            gera ../index.html com os dados e as fontes embutidas
fonte/checar.py           confere o balanceamento (usa sim32.py e endings_sim.py)
index.html                GERADO. Nunca edite à mão.
aula/                     plano, slides e atividade (gerados fora deste repo)
```

**Depois de qualquer mudança:** rode `python3 fonte/build.py`. Se mexer em
`decisions.json` ou `endings_params.json`, rode também `python3 fonte/checar.py`
(precisa de numpy). Depois abra o `index.html` e jogue ao menos uma partida,
em largura de celular, para conferir.

## Regras de conteúdo (cada situação em decisions.json)

- `text`: fala do conselheiro, com pelo menos um **First Conditional**
  (*If you ..., you will ...*). Linguagem A2/B1, frases curtas.
- `result`: o que aconteceu, em **Simple Past**.
- `[[palavra|tradução]]` cria o glossário de toque. Use só em palavras
  difíceis. Verbos irregulares já são reconhecidos automaticamente.
- **Falsos positivos do glossário de verbos:** se um substantivo tiver a mesma
  forma de um verbo irregular (*costs*, *TV show*), marque-o com `[[...]]`
  para ele não mostrar o balão de verbo.
- `label` (texto do botão): nunca com `[[...]]`.
- `phrase`: a ação em inglês, forma base, começando com minúscula, sem
  pronomes soltos (*it*, *her*, *them*), e sem repetir a de outra opção. É
  usada no montador: *If I were the CEO again, I would* + phrase.
- `phrasePt`: a mesma ação em português.
- Conselheiros (`who`): `ana` (CFO, dinheiro), `lee` (mentor, produto e
  usuários), `costa` (investidora). Mantenha as falas equilibradas entre os três.

## Regras de balanceamento

- As duas opções de cada situação precisam ter **custo e benefício**. Nada de
  opção que só ganha, nem de situação em que as duas só perdem.
- **Fazer a coisa certa não pode ser só prejuízo.** Pagar impostos, proteger
  dados de usuários e tratar bem a equipe precisam render reputação de forma
  clara. Isso já precisou ser corrigido uma vez.
- Garantia obrigatória (`checar.py`): **qualquer** sorteio de 5 situações
  precisa conseguir chegar às três faixas de final (fracasso, meio-termo,
  sucesso). Se falhar, ajuste primeiro o conteúdo (valores de cash/rep das
  situações envolvidas), e só depois os limites.
- O Unicórnio deve continuar raro (cerca de 2 a 5% das partidas).
- Estratégias gananciosas ("sempre mais dinheiro", "sempre mais reputação")
  não podem chegar a *Took off* ou *Unicorn*.
- Se mudar qualquer regra de final, verifique que a lógica do jogo (JS) dá o
  mesmo resultado que a simulação (Python).

## Decisões de design já tomadas (não desfazer sem pedir)

- 5 situações sorteadas por partida; os dois botões têm o **mesmo estilo** e a
  ordem é embaralhada a cada decisão.
- Tela de palavras-chave antes do jogo.
- Glossário sublinhado só na **primeira ocorrência de cada palavra por tela**;
  o balão abre acima da palavra e não pode cobrir nem bloquear botões.
- Tela final: 9 finais, "Looking back" (melhor decisão nunca pode ter custado
  mais de 15 pontos num medidor; o erro mais caro é medido pelo medidor que
  afundou a empresa) e mapa de finais descobertos.
- Montador de frases (*Help me write*) em no máximo **2 das 3** frases. Editar
  uma frase montada não tira a etiqueta; só apagar o campo inteiro libera.
- **Play again** fica travado até as 3 frases passarem na checagem. A partida
  pendente fica salva, e recarregar a página volta para as frases.
- Histórico das últimas partidas na tela inicial, com opção de apagar
  (dois toques).
- Tudo que usa `localStorage` fica dentro de `try/catch`: o jogo precisa
  funcionar mesmo se o navegador bloquear o armazenamento.
- Texto digitado pelo aluno (nome da startup) sempre passa por `esc()`.

## O que não fazer

- Não adicionar bibliotecas externas, CDNs nem qualquer acesso à rede.
- Não coletar nem enviar dados dos alunos.
- Não reproduzir letras de música ou textos protegidos.
- Não editar os arquivos de `aula/` sem o professor pedir.

## Pendências conhecidas

- O plano e os slides em `aula/` ainda apontam para o link antigo do
  claude.ai. Quando o GitHub Pages estiver ativo, o professor vai atualizar
  esses arquivos.
- Licença do repositório ainda não definida.
- Ideia: uma GitHub Action que rode `fonte/build.py` sempre que
  `fonte/decisions.json` mudar, para o professor editar situações direto pelo
  site do GitHub.
