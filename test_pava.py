import numpy as np

def _pava_isotonic(x, xl=None, xu=None):
    n = len(x)
    result = np.empty(n, dtype=float)
    vals = [float(x[j]) for j in range(n)]
    sizes = [1] * n
    count = n
    i = 0
    while i < count - 1:
        if vals[i] <= vals[i + 1]:
            i += 1
        else:
            merged_val = (vals[i] * sizes[i] + vals[i + 1] * sizes[i + 1]) / (sizes[i] + sizes[i + 1])
            merged_size = sizes[i] + sizes[i + 1]
            vals[i] = merged_val
            sizes[i] = merged_size
            vals.pop(i + 1)
            sizes.pop(i + 1)
            count -= 1
            if i > 0:
                i -= 1
    idx = 0
    for b in range(count):
        val = vals[b]
        if xl is not None:
            val = max(val, float(xl[0]))
        if xu is not None:
            val = min(val, float(xu[0]))
        for _ in range(sizes[b]):
            result[idx] = val
            idx += 1
    return result


import numpy as np
np.random.seed(42)
print('PAVA repair test:')
all_ok = True
for trial in range(5):
    x = np.random.uniform(0.003, 0.025, 12)
    xl = np.full(12, 0.003)
    xu = np.full(12, 0.025)
    r = _pava_isotonic(x, xl, xu)
    mono = all(r[j] <= r[j+1] for j in range(len(r)-1))
    clipped = all(xl[j] <= r[j] <= xu[j] for j in range(12))
    if not mono:
        all_ok = False
    print('  {}: mono={} clipped={} vals={}'.format(trial, mono, clipped, ['{:.4f}'.format(v) for v in r]))
print('All passed:', all_ok)
