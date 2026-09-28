import json, itertools, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "decisions.json"), encoding="utf-8")); N = len(D)
EFF = np.array([[[d[k]["cash"], d[k]["rep"]] for k in "ab"] for d in D], dtype=np.int16)
CH = np.array(list(itertools.product([0, 1], repeat=5)), dtype=np.int8)
def subsets():
    return np.array(list(itertools.combinations(range(N), 5)), dtype=np.int16)
def run(subs, seed=None):
    s = subs if seed is None else np.take_along_axis(subs, np.argsort(np.random.default_rng(seed).random(subs.shape), axis=1), axis=1)
    S = len(s)
    c = np.full((S, 32), 50, np.int16); r = np.full((S, 32), 50, np.int16); b = np.zeros((S, 32), bool)
    for k in range(5):
        e = EFF[s[:, k]][:, CH[:, k]]
        c = np.where(b, c, np.clip(c + e[..., 0], 0, 100)); r = np.where(b, r, np.clip(r + e[..., 1], 0, 100))
        b |= c <= 0
    return c, r, b
def families(c, r, b):
    fail = b | (r < 25) | (c < 10)
    succ = ~fail & (r >= 65)
    mid = ~fail & ~succ
    return fail, mid, succ
