#!/usr/bin/env python3.12
"""
出海ID指南 站点生成器

用法:
    python3.12 build.py          # 重建索引页、首页、sitemap，并统一全站导航与页脚
    python3.12 build.py --check  # 只检查不写盘，报告会发生哪些变更
    python3.12 build.py --new <品类> <slug>   # 用模板新建一篇空文章

日常流程:
    1. build.py --new appleid change-region   生成 appleid/change-region.html
    2. 编辑该文件正文(改 title / description / excerpt / group 三个 meta 和 <article> 内容)
    3. build.py                                索引页、首页、sitemap 自动更新
    4. git push
"""
import json, re, sys, shutil
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent
CFG = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
SITE, CATS = CFG['site'], CFG['categories']
CAT_BY_SLUG = {c['slug']: c for c in CATS}
TODAY = date.today().isoformat()

CHECK = '--check' in sys.argv
changes = []


def write(path: Path, content: str):
    """写文件；--check 模式下只记录差异。"""
    old = path.read_text(encoding='utf-8') if path.exists() else None
    if old == content:
        return
    changes.append(('新建' if old is None else '更新', str(path.relative_to(ROOT))))
    if not CHECK:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')


def meta(src: str, name: str) -> str:
    m = re.search(rf'<meta\s+name="{name}"\s+content="([^"]*)"', src)
    return m.group(1) if m else ''


def parse_article(path: Path) -> dict:
    src = path.read_text(encoding='utf-8')
    t = re.search(r'<title>(.*?)</title>', src, re.S)
    title = t.group(1).strip() if t else path.stem
    title = title.split(' - ')[0].strip()          # 去掉站名后缀
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', src, re.S)
    d = re.search(r'"datePublished":"([\d-]+)"', src)
    desc = meta(src, 'description')
    return {
        'path': path,
        'url': '/' + str(path.relative_to(ROOT)).replace('\\', '/'),
        'title': title,
        'h1': re.sub(r'<[^>]+>', '', h1.group(1)).strip() if h1 else title,
        'excerpt': meta(src, 'excerpt') or desc,
        'group': meta(src, 'group'),
        'date': d.group(1) if d else TODAY,
        'src': src,
    }


def collect(cat_slug: str) -> list:
    """按「分组顺序 → 日期倒序」排列，保证首页与索引页顺序一致。"""
    d = ROOT / cat_slug
    if not d.is_dir():
        return []
    arts = [parse_article(p) for p in sorted(d.glob('*.html')) if p.name != 'index.html']
    order = {g['key']: i for i, g in enumerate(CAT_BY_SLUG[cat_slug].get('groups', []))}
    return sorted(arts, key=lambda a: (order.get(a['group'], 99), a['date']))


# ---------- 公共片段 ----------

def nav_html() -> str:
    links = '\n'.join(
        f'    <a href="/{c["slug"]}/">{c["nav"]}</a>' for c in CATS
    )
    return f'<nav class="site">\n{links}\n  </nav>'


def header_html() -> str:
    return (f'<header class="site"><div class="wrap">\n'
            f'  <a class="logo" href="/">{SITE["name"]}</a>\n'
            f'  {nav_html()}\n'
            f'</div></header>')


def footer_html() -> str:
    return (f'<footer class="site"><div class="wrap">\n'
            f'  <p>{SITE["name"]} · {SITE["tagline"]}</p>\n'
            f'  <p>{SITE["footer_note"]}</p>\n'
            f'</div></footer>')


def cta_html(cat: dict) -> str:
    return (f'<div class="cta">\n  <p>{cat["cta"]}</p>\n'
            f'  <a class="btn" href="{cat["target"]}" target="_blank" rel="noopener">{cat["cta_btn"]}</a>\n'
            f'</div>')


def page(title: str, desc: str, canonical: str, body: str, ld: str = '') -> str:
    ldblock = f'\n<script type="application/ld+json">\n{ld}\n</script>' if ld else ''
    gv = SITE.get('google_verification', '')
    gvtag = f'\n<meta name="google-site-verification" content="{gv}">' if gv else ''
    full_title = title if title == SITE["name"] else f'{title} - {SITE["name"]}'
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">{gvtag}
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="/assets/style.css">{ldblock}
</head>
<body>

{header_html()}

<main><div class="wrap">
{body}
</div></main>

{footer_html()}

</body>
</html>
'''


# ---------- 品类索引页 ----------

def build_category(cat: dict):
    arts = collect(cat['slug'])
    base = SITE['base']
    body = [f'<div class="crumb"><a href="/">首页</a> › {cat["nav"]}</div>\n',
            f'<h1>{cat["h1"]}</h1>']
    body.append(f'<p class="meta">共 {len(arts)} 篇 · 最近更新 {max(a["date"] for a in arts) if arts else TODAY}</p>\n')
    body.append(f'<p class="lead">{cat["lead"]}</p>\n')

    if not arts:
        body.append('<div class="note">这个品类的内容正在整理中，很快会补上。</div>\n')
    else:
        used = set()
        for g in cat.get('groups', []):
            sel = [a for a in arts if a['group'] == g['key']]
            if not sel:
                continue
            used.update(id(a) for a in sel)
            body.append(f'<h2>{g["name"]}</h2>\n<ul class="list">')
            for a in sel:
                body.append(f'<li>\n  <a href="{a["url"]}">{a["title"]}</a>\n  <p>{a["excerpt"]}</p>\n</li>')
            body.append('</ul>\n')
        rest = [a for a in arts if id(a) not in used]
        if rest:
            body.append('<h2>其他</h2>\n<ul class="list">')
            for a in rest:
                body.append(f'<li>\n  <a href="{a["url"]}">{a["title"]}</a>\n  <p>{a["excerpt"]}</p>\n</li>')
            body.append('</ul>\n')

    body.append(cta_html(cat))
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": cat['h1'], "description": cat['description'],
        "inLanguage": "zh-CN", "url": f'{base}/{cat["slug"]}/'
    }, ensure_ascii=False)
    write(ROOT / cat['slug'] / 'index.html',
          page(cat['title'], cat['description'], f'{base}/{cat["slug"]}/', '\n'.join(body), ld))
    return arts


# ---------- 首页 ----------

def build_home(all_arts: dict):
    base = SITE['base']
    total = sum(len(v) for v in all_arts.values())
    body = [f'<h1>{SITE["name"]}</h1>',
            f'<p class="meta">{SITE["tagline"]} · 共 {total} 篇 · 最近更新 {TODAY}</p>\n',
            '<p class="lead">下载区域限定的 App、注册海外服务，常常卡在「没有对应地区的账号」这一步。'
            '这个站整理各类海外账号的获取途径、常见故障的处理方法，以及使用中容易踩的坑。本站不销售账号。</p>\n']

    for cat in CATS:
        arts = all_arts.get(cat['slug'], [])
        body.append(f'<h2>{cat["name"]}</h2>')
        if not arts:
            body.append(f'<p>内容整理中，很快会补上。</p>\n')
            continue
        body.append('<ul class="list">')
        for a in arts[:6]:
            body.append(f'<li>\n  <a href="{a["url"]}">{a["title"]}</a>\n  <p>{a["excerpt"]}</p>\n</li>')
        body.append('</ul>')
        if len(arts) > 6:
            body.append(f'<p><a href="/{cat["slug"]}/">查看全部 {len(arts)} 篇 →</a></p>')
        body.append('')

    body.append('<h2>关于本站</h2>\n'
                '<p>本站是信息参考站点，整理公开可查证的使用方法和官方流程说明，不销售任何账号。'
                '文中提及的商家由各自运营方负责，列出不代表担保。</p>\n'
                '<p>海外账号的使用存在客观风险——平台条款、风控策略随时可能变化。'
                '文中方法以撰写时的实际情况为准，请结合自己的情况判断。</p>')

    ld = json.dumps({"@context": "https://schema.org", "@type": "WebSite",
                     "name": SITE['name'], "description": SITE['tagline'],
                     "inLanguage": "zh-CN", "url": base + '/'}, ensure_ascii=False)
    write(ROOT / 'index.html',
          page(SITE['name'], f'{SITE["tagline"]}。' +
               '、'.join(c['name'] for c in CATS) + '等账号的获取途径、常见故障处理与使用注意事项。',
               base + '/', '\n'.join(body), ld))


# ---------- sitemap ----------

def build_sitemap(all_arts: dict):
    base = SITE['base']
    rows = [(base + '/', TODAY, 'weekly', '1.0')]
    for cat in CATS:
        arts = all_arts.get(cat['slug'], [])
        if not (ROOT / cat['slug']).is_dir():
            continue
        rows.append((f'{base}/{cat["slug"]}/', max(a['date'] for a in arts) if arts else TODAY, 'weekly', '0.9'))
        for a in arts:
            rows.append((base + a['url'], a['date'], 'monthly', '0.8'))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod, freq, pri in rows:
        xml.append(f'  <url><loc>{loc}</loc><lastmod>{mod}</lastmod>'
                   f'<changefreq>{freq}</changefreq><priority>{pri}</priority></url>')
    xml.append('</urlset>')
    write(ROOT / 'sitemap.xml', '\n'.join(xml) + '\n')


# ---------- 统一全站导航与页脚 ----------

def sync_chrome(all_arts: dict):
    """把所有文章页的 <nav> 和 <footer> 同步成最新版本。"""
    for cat in CATS:
        for a in all_arts.get(cat['slug'], []):
            s = a['src']
            s2 = re.sub(r'<nav class="site">.*?</nav>', nav_html(), s, flags=re.S)
            s2 = re.sub(r'<footer class="site">.*?</footer>', footer_html(), s2, flags=re.S)
            if s2 != s:
                write(a['path'], s2)


# ---------- 新建文章 ----------

def new_article(cat_slug: str, slug: str):
    if cat_slug not in CAT_BY_SLUG:
        sys.exit(f'未知品类:{cat_slug}(可选:{", ".join(CAT_BY_SLUG)})')
    cat = CAT_BY_SLUG[cat_slug]
    dst = ROOT / cat_slug / f'{slug}.html'
    if dst.exists():
        sys.exit(f'已存在:{dst.relative_to(ROOT)}')
    tpl = (ROOT / '_template.html').read_text(encoding='utf-8')
    groups = cat.get('groups', [{'key': '', 'name': ''}])
    out = (tpl.replace('{{CAT_SLUG}}', cat_slug)
              .replace('{{CAT_NAV}}', cat['nav'])
              .replace('{{SLUG}}', slug)
              .replace('{{DATE}}', TODAY)
              .replace('{{GROUP}}', groups[0]['key'])
              .replace('{{GROUP_OPTIONS}}', ' / '.join(f'{g["key"]}={g["name"]}' for g in groups))
              .replace('{{NAV}}', nav_html())
              .replace('{{HEADER}}', header_html())
              .replace('{{FOOTER}}', footer_html())
              .replace('{{CTA}}', cta_html(cat))
              .replace('{{BASE}}', SITE['base']))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(out, encoding='utf-8')
    print(f'✅ 已创建 {dst.relative_to(ROOT)}')
    print(f'   下一步:填 title / description / excerpt / group({groups[0]["key"]} 等) 和正文,然后跑 build.py')


def main():
    if '--new' in sys.argv:
        i = sys.argv.index('--new')
        try:
            new_article(sys.argv[i + 1], sys.argv[i + 2])
        except IndexError:
            sys.exit('用法:build.py --new <品类> <slug>')
        return

    all_arts = {}
    for cat in CATS:
        (ROOT / cat['slug']).mkdir(exist_ok=True)
        all_arts[cat['slug']] = build_category(cat)

    sync_chrome(all_arts)
    build_home(all_arts)
    build_sitemap(all_arts)

    total = sum(len(v) for v in all_arts.values())
    print(f'{"[检查模式] " if CHECK else ""}文章总数 {total} 篇：' +
          '、'.join(f'{c["nav"]} {len(all_arts[c["slug"]])}' for c in CATS))
    if changes:
        for kind, p in changes:
            print(f'  {kind} {p}')
    else:
        print('  无变更')


if __name__ == '__main__':
    main()
