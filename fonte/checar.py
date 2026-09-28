"""Confere o balanceamento do jogo depois de editar decisions.json.

Uso:  python3 fonte/checar.py      (precisa de numpy; leva cerca de 1 a 2 minutos)

1. Garantia principal: qualquer sorteio de 5 perguntas precisa conseguir chegar
   às três faixas de final (fracasso, meio-termo e sucesso). Testa todas as
   combinações, com as perguntas em ordem fixa e em ordem aleatória.
2. Mostra com que frequência cada um dos 9 finais acontece.
"""
import json, os, numpy as np
from sim32 import subsets, run, families, D
from endings_sim import classify, ORDER

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "endings_params.json")))

subs = subsets()
print(f"{len(D)} decisões, {len(subs)} combinações de 5 perguntas")
ok, tot, n = True, np.zeros(9), 0
for seed in (None, 7):
    c, r, b = run(subs, seed)
    f, m, s = families(c, r, b)
    bad = int((~(f.any(1) & m.any(1) & s.any(1))).sum())
    ok &= bad == 0
    print(f"  ordem {'fixa' if seed is None else 'aleatória'}: combinações que não alcançam as 3 faixas = {bad}")
    k = classify(c.ravel(), r.ravel(), b.ravel(), P)
    tot += np.bincount(k, minlength=9); n += k.size
print("\nfrequência de cada final:")
for e, v in zip(ORDER, 100 * tot / n):
    print(f"  {e:11s} {v:5.1f}%")
print("\nRESULTADO:", "OK, balanceado" if ok else "ATENÇÃO: algum sorteio não alcança as 3 faixas; ajuste os valores de cash/rep")
