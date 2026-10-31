"""Split an ordered run of items into consecutive chunks without reordering or shortening anything (03 COPY-03):
numbering simply continues in the next chunk, with no 'continued' label."""

def partition(hs, caps, gap=0):
    """Ends of len(caps) non-empty consecutive chunks of items with heights hs, minimising the largest
    (chunk height / chunk capacity). caps are relative capacities (a full-width two-column page holds about 2)."""
    n, m = len(hs), len(caps)
    if m <= 1 or n <= 1: return [n]
    m = min(m, n); memo = {}
    def cost(a, b, c): return (sum(hs[a:b]) + gap * (b - a - 1)) / caps[c]
    def go(a, c):
        if (a, c) not in memo:
            if c == m - 1: memo[(a, c)] = (cost(a, n, c), [n])
            else:
                best = None
                for b in range(a + 1, n - (m - c - 1) + 1):
                    v, rest = go(b, c + 1); v = max(v, cost(a, b, c))
                    if best is None or v < best[0]: best = (v, [b] + rest)
                memo[(a, c)] = best
        return memo[(a, c)]
    return go(0, 0)[1]

def chunks(n, ends):
    out, a = [], 0
    for b in ends: out.append((a, b)); a = b
    return out

def split_rows(data, fits, key='rows', min_last=0.5):
    """Greedy pages of data[key] (a table's rows, a list's items): each page takes what fits, the next page goes
    on from the next row; a last page under min_last of the one before shares the last two pages evenly."""
    rows = list(data[key])
    if fits(data): return [data]
    pages, a = [], 0
    while a < len(rows):
        k = 0
        while a + k < len(rows) and fits({**data, key: rows[a:a + k + 1], 'row_start': a}): k += 1
        if k == 0: raise ValueError(f'{key} 第 {a + 1} 行单独一页也放不下')
        pages.append((a, a + k)); a += k
    if len(pages) > 1:
        (a0, b0), (a1, b1) = pages[-2], pages[-1]
        if (b1 - a1) < min_last * (b0 - a0):
            mid = (a0 + b1 + 1) // 2
            trial = [(a0, mid), (mid, b1)]
            if all(fits({**data, key: rows[x:y], 'row_start': x}) for x, y in trial): pages[-2:] = trial
    return [{**data, key: rows[x:y], 'row_start': x, 'page_of': [n + 1, len(pages)]} for n, (x, y) in enumerate(pages)]
