"""Insight / note card icons (03 COPY-06): an explicit `icon` wins; otherwise the icon follows the card's words, and no two
cards on one page share an icon (a repeated explicit icon is replaced by the next match). Keyword table, first hit wins."""

RULES = [
    (('未达', '不显著', '跨 0', '跨0', '无差异', '未见'), 'alert-circle'),
    (('停药', '脱落', '退出', '失访'), 'user-x'),
    (('死亡', '严重', '风险', '关注', '警示', '信号'), 'warn'),
    (('安全', '不良', '耐受', 'AE', 'TEAE'), 'shield'),
    (('主要终点', '达到', '达标', '目标', '命中'), 'target'),
    (('倍', '对比', '优于', '差值', '相对'), 'scale'),
    (('下降', '降低', '减少', '多降', '再降'), 'trending-down'),
    (('上升', '提高', '增加', '增长', '剂量依赖', '依赖'), 'trending-up'),
    (('入组', '样本', '例数', '受试者', '人群'), 'people'),
    (('暴露', '人年', 'E1'), 'chart-bar'),
    (('里程碑', '季度', '时间', '提前', '推迟', '延期', 'NDA', '申报'), 'calendar-event'),
    (('随机', '分组', '分配'), 'arrows-split'),
    (('访视', '评估', '检查', '检验'), 'clipboard-check'),
    (('竞品', '格局', '同类', '靶点'), 'topology-star'),
    (('费用', '成本', '预算'), 'coin'),
    (('数据', '完整', '缺失'), 'database'),
    (('获批', '批准', '上市'), 'certificate'),
]
FALLBACK = ['bulb', 'sparkles', 'flag', 'check', 'chart-dots', 'target']


def pick(items, key_icon='icon'):
    """items: dicts with title/text (and maybe icon). Returns one icon name per item, all different on the page."""
    used, out = set(), []
    for it in items:
        words = f"{it.get('title', '')} {it.get('text', '')}"
        cands = ([it[key_icon]] if it.get(key_icon) else []) + [ic for keys, ic in RULES if any(k in words for k in keys)] + FALLBACK
        ic = next(c for c in cands if c not in used) if any(c not in used for c in cands) else cands[0]
        used.add(ic); out.append(ic)
    return out
