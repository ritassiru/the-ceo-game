import numpy as np, itertools, json, os
ORDER = ["bankrupt", "users_left", "sold", "thread", "stuck", "money", "rising", "tookoff", "unicorn"]
FIX = dict(R0=25, C0=10, R1=65)   # fronteiras das 3 faixas, já validadas

def classify(c, r, b, P):
    k = np.full(c.shape, 4, dtype=np.int8)                      # stuck
    k[(c < P["C5"]) | (r < P["R3"])] = 3                        # thread: dinheiro curto OU usuários insatisfeitos
    k[c >= P["C4"]] = 5                                         # money
    k[r >= P["R1"]] = 6                                         # rising
    k[(r >= P["R1"]) & (c >= P["C2"])] = 7                      # tookoff
    k[(r >= P["R2"]) & (c >= P["C3"])] = 8                      # unicorn
    k[c < P["C0"]] = 2                                          # sold
    k[r < P["R0"]] = 1                                          # users_left
    k[b] = 0                                                    # bankrupt
    return k

if __name__ == "__main__":
    z = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "paths.npz"))
    c = np.concatenate([z[f"c{i}"] for i in range(3)]); r = np.concatenate([z[f"r{i}"] for i in range(3)]); b = np.concatenate([z[f"b{i}"] for i in range(3)])
    best = []
    alvo = {3: 10, 4: 25, 5: 7, 6: 14, 7: 12}
    for C2, R2, C3, C4, C5, R3 in itertools.product([25, 30, 35, 40], [70, 75, 80], [30, 35, 40, 45, 50], [55, 60, 65, 70, 75], [15, 20, 25], [30, 35, 40]):
        if C3 < C2: continue
        P = dict(FIX, C2=C2, R2=R2, C3=C3, C4=C4, C5=C5, R3=R3)
        dist = 100 * np.bincount(classify(c, r, b, P), minlength=9) / len(c)
        if not (2 <= dist[8] <= 5) or dist.min() < 3: continue
        best.append((round(sum(abs(dist[i] - v) for i, v in alvo.items()), 1), P, dist.round(1)))
    best.sort(key=lambda x: x[0])
    print("configurações que atendem às metas:", len(best))
    for s, P, d in best[:3]:
        print(s, {k: P[k] for k in ("C2", "R2", "C3", "C4", "C5", "R3")}, dict(zip(ORDER, d)))
    if best: print("sugestão de endings_params.json:", best[0][1])
