# The CEO Game

Jogo interativo em inglês, no estilo *choose your own adventure*, para praticar
**First** e **Second Conditional**. O aluno é CEO de uma startup e toma 5
decisões. Antes de cada uma, um conselheiro avisa das consequências em First
Conditional (*If you hire five engineers, we will spend all our money*). No
final, o aluno escreve frases em Second Conditional sobre o que faria diferente
(*If I were the CEO again, I would...*).

Feito para o 2º ano de inglês do Ensino Médio Integrado (nível A2/B1).
Funciona no celular, sem instalar nada, e também sem internet.

**▶ Jogar:** `https://ritassiru.github.io/the-ceo-game/`
*(o link passa a funcionar depois de ativar o GitHub Pages; veja abaixo)*

---

## O que tem no jogo

- **42 situações**, das quais 5 são sorteadas a cada partida, com três
  conselheiros: Ana (CFO), Mr. Lee (mentor) e Ms. Costa (investidora).
- **Dois medidores**, 💰 Cash e ⭐ Reputation, que reagem a cada escolha.
- **9 finais** em três faixas:
  - fracasso: *Bankrupt*, *Everybody left*, *Sold for almost nothing*
  - meio-termo: *Hanging by a thread*, *Stuck*, *Money machine*
  - sucesso: *Rising star*, *Took off*, *Unicorn* 🦄 (raro de propósito)
- **Palavras-chave** antes de começar, com tradução.
- **Glossário de toque:** palavras difíceis mostram a tradução, e verbos
  irregulares mostram as três formas (*go · went · gone*).
- **Tela final** com a melhor decisão, o erro mais caro e um mapa dos finais
  já descobertos.
- **Montador de frases** (*Help me write*) para quem não tem vocabulário,
  limitado a 2 das 3 frases.
- **Trava:** só dá para jogar de novo depois de escrever e conferir as 3 frases.
- **Histórico** das últimas partidas.
- **Configurações** (ícone de engrenagem, em todas as telas): glossário em três
  níveis (*Normal*, só as palavras difíceis; *Beginner*, para iniciantes totais
  (A1), com quase todas as palavras traduzidas e tradução nos botões; *Off*), cores (automático, claro ou escuro), tamanho do texto e
  animações. Ficam guardadas no próprio aparelho.

## Como usar em aula

O plano completo está em [`aula/`](aula/): plano de 4 encontros sobre Zero,
First e Second Conditional, slides e atividade de sala. O jogo entra no
**Encontro 4 (Review Day)**: 20 minutos em duplas no celular, e as 3 frases
finais, copiadas no caderno, valem o visto do dia.

**Sem internet na sala:** abra o `index.html` no computador, projete, leia as
falas em voz alta e deixe a turma votar em cada decisão.

## Usar sem internet

O `index.html` é autossuficiente: as fontes estão embutidas nele e ele não
acessa nada online. Baixe o arquivo e:

- **no computador:** dê dois cliques nele;
- **no celular Android:** envie como documento (WhatsApp, Bluetooth, pendrive)
  e abra com o **Chrome**;
- **no iPhone:** a pré-visualização de arquivos não roda o jogo; prefira o link
  do GitHub Pages.

## Publicar no GitHub Pages

1. No repositório, abra **Settings → Pages**.
2. Em *Build and deployment*, escolha **Deploy from a branch**, branch `main`,
   pasta `/ (root)`, e salve.
3. Em cerca de um minuto, o jogo fica disponível em
   `https://SEU-USUARIO.github.io/the-ceo-game/`.

## Estrutura

```
index.html               o jogo, pronto para jogar (gerado por fonte/build.py)
aula/                    plano de aula, slides e atividade
fonte/
  decisions.json         as 32 situações do jogo
  irreg.json             verbos irregulares do glossário
  a1.json                glossário do nível Beginner (A1)
  endings_params.json    limites que definem os 9 finais
  template.html          visual e lógica do jogo
  build.py               gera o index.html
  checar.py              confere o balanceamento
  sim32.py, endings_sim.py   simuladores usados pelo checar.py
  fonts/                 fontes embutidas (licença SIL OFL)
```

## Como editar ou acrescentar situações

Cada situação em `fonte/decisions.json` segue este modelo:

```json
{
  "id": "taxes",
  "who": "ana",
  "text": "We made a mistake with our [[taxes|impostos]]. If we pay now, we will lose a lot of money. If we don't pay, the newspapers will talk about it.",
  "a": {
    "label": "Pay the taxes now",
    "cash": -10, "rep": 10,
    "result": "It hurt, but your company did the right thing, and people respected you for it.",
    "phrase": "pay the taxes now", "phrasePt": "pagar os impostos agora"
  },
  "b": { "...": "mesmos campos da opção a" }
}
```

- `who`: `ana`, `lee` ou `costa`.
- `text`: a fala do conselheiro, com pelo menos um **First Conditional**.
  `[[palavra|tradução]]` cria o glossário de toque. Verbos irregulares são
  reconhecidos sozinhos.
- `label`: o texto do botão (sem `[[...]]`).
- `cash` e `rep`: quanto a escolha soma ou tira de cada medidor.
- `result`: o que aconteceu, em **Simple Past**.
- `phrase` e `phrasePt`: a ação, em inglês e em português, usada pelo montador
  de frases (*If I were the CEO again, I would* + `phrase`). Comece com letra
  minúscula e evite pronomes soltos como *it* e *her*.
- Palavras novas em `text` ou `result` precisam de tradução em
  `fonte/a1.json` (glossário Beginner). O `build.py` avisa quais faltam.

**Regra de ouro do balanceamento:** as duas opções precisam ter custo e
benefício. Se uma opção só ganha, ou se as duas só perdem, o jogo fica óbvio ou
injusto. E fazer a coisa certa (pagar impostos, proteger dados) não pode sair
sempre caro sem retorno nenhum.

Depois de editar:

```bash
python3 fonte/build.py      # gera de novo o index.html
pip install numpy           # só na primeira vez
python3 fonte/checar.py     # confere o balanceamento (1 a 2 minutos)
```

O `checar.py` testa todas as combinações possíveis de perguntas e avisa se
alguma delas deixou de alcançar as três faixas de final.

**Editando pelo site do GitHub:** não precisa rodar nada. Sempre que um arquivo
de `fonte/` muda na branch `main`, a GitHub Action *Gerar o jogo*
(`.github/workflows/build.yml`) roda o `build.py` e o `checar.py` e salva o
`index.html` novo sozinha, em cerca de 2 minutos. Se o build der erro ou o
balanceamento não passar, o `index.html` não é alterado e o GitHub avisa por
e-mail; os detalhes ficam na aba **Actions** do repositório.

## Privacidade

O jogo não envia nada para lugar nenhum. O histórico, o mapa de finais e a
trava das frases ficam guardados só no navegador do aparelho em que o aluno
jogou.

## Créditos

Criado por Prof. Ritaciro Cavalcante da Silva, IFAL Campus Viçosa.

Fontes: [Fraunces](https://github.com/undercasetype/Fraunces) (The Fraunces
Project Authors) e [Atkinson Hyperlegible](https://www.brailleinstitute.org/freefont/)
(Braille Institute), ambas sob a SIL Open Font License 1.1. As licenças estão
em `fonte/fonts/`.
