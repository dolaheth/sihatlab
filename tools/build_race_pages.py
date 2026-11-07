#!/usr/bin/env python3
"""Build one static page per approved race (site/race/<slug>.html) so Google can index each race.

Reads live data from Supabase with the public anon key (same as race.html): races, race_summary,
and approved review text from review_list. Also rewrites the race links in race.html (between the
<!-- race-pages:start/end --> markers) and the race entries in sitemap.xml.

Run: python3 content/website/build_race_pages.py   (deploy-site.sh runs it before every deploy)
The published repo (dolaheth/sihatlab) also runs it every night via .github/workflows/race-pages.yml.
If Supabase can't be reached it exits without touching anything, so the last pages stay live.
"""
import html, json, os, re, sys, unicodedata, urllib.request
from datetime import date
from pathlib import Path

# SITE_DIR=. when it runs inside the published repo (GitHub Action), else content/website/site.
SITE = Path(os.environ.get("SITE_DIR") or Path(__file__).resolve().parent / "site").resolve()
OUT = SITE / "race"
BASE = "https://sihatlab.com.my"
API = "https://ipzdgezezjgveuyihxdu.supabase.co/rest/v1"
KEY = re.search(r"eyJ[A-Za-z0-9._-]+", (SITE / "race.html").read_text(encoding="utf-8")).group(0)
COMPANY = "SIHAT LAB SERVICE (TR0352367-D)"
MS = ["Jan", "Feb", "Mac", "Apr", "Mei", "Jun", "Jul", "Ogo", "Sep", "Okt", "Nov", "Dis"]
MS_FULL = ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai", "Ogos", "September", "Oktober", "November", "Disember"]
KEYS = [("org", "Organisasi"), ("route", "Laluan"), ("water", "Water station"), ("medal", "Medal / jersey"), ("value", "Nilai harga")]


def get(path):
    req = urllib.request.Request(f"{API}/{path}", headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def e(x):
    return html.escape(str(x or ""), quote=True)


def d(s, full=False):
    y, m, dd = map(int, s.split("-"))
    return f"{dd} {(MS_FULL if full else MS)[m - 1]} {y}"


def when(r):
    if r.get("date_end") and r["date_end"] != r["date_start"]:
        return f"{d(r['date_start'])} hingga {d(r['date_end'])}"
    return d(r["date_start"], True)


def host(u):
    return re.sub(r"^https?://(www\.)?", "", u).rstrip("/")


def stars(v):
    n = round(float(v or 0))
    return '<span class="st" aria-label="%s daripada 5">%s<i>%s</i></span>' % (f"{float(v):.1f}" if v else "0", "★" * n, "★" * (5 - n))


CSS = """:root{--paper:#F4F4F1;--ink:#111;--grey:#5E5E63;--line:#1111111f;--volt:#C8F31D;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}
*{box-sizing:border-box;margin:0}
body{background:var(--paper);color:var(--ink);font-family:Inter,-apple-system,Arial,sans-serif;font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:inherit}:focus-visible{outline:2px solid #0071E3;outline-offset:2px}
.mono{font-family:var(--mono);text-transform:uppercase;letter-spacing:.04em;font-size:12px}
header{display:flex;align-items:stretch;justify-content:space-between;height:56px;border-bottom:1px solid var(--ink);padding-left:20px}
header>a{align-self:center;display:flex}header>a img{height:20px;width:auto}
header nav{display:flex}header nav a{display:flex;align-items:center;padding:0 14px;border-left:1px solid var(--ink);font:500 12px var(--mono);text-transform:uppercase;text-decoration:none;min-width:44px;justify-content:center}
header nav a.v{background:var(--volt);font-weight:700}
main{max-width:860px;margin:0 auto;padding:28px 20px 48px}
.crumb{color:var(--grey)}.crumb a{text-decoration:none}.crumb a:hover{text-decoration:underline}
h1{margin-top:14px;font-weight:900;font-size:clamp(34px,6vw,58px);line-height:1.02;letter-spacing:-.045em;text-transform:uppercase}
.lede{margin-top:14px;font-size:18px;color:#333;max-width:640px}
.facts{margin-top:24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));border:1px solid var(--ink);background:#fff}
.facts div{padding:12px 14px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.facts span{display:block;font:500 11px var(--mono);text-transform:uppercase;color:var(--grey)}.facts b{font-weight:700}
.note{margin-top:16px;color:#333}
.cta{margin-top:20px;display:flex;gap:8px;flex-wrap:wrap}
.cta a{display:inline-flex;align-items:center;min-height:48px;padding:12px 18px;border:1px solid var(--ink);background:#fff;font:700 13px var(--mono);text-transform:uppercase;text-decoration:none}
.cta a.v{background:var(--volt)}
h2{margin-top:40px;font-weight:900;font-size:26px;letter-spacing:-.03em;text-transform:uppercase;border-bottom:1px solid var(--ink);padding-bottom:8px}
.sum{margin-top:16px;display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:start}
.avg b{display:block;font:700 64px/1 var(--mono);letter-spacing:-.04em}.avg small{display:block;margin-top:6px;color:var(--grey);font:500 12px var(--mono);text-transform:uppercase}
.st{color:#111;letter-spacing:2px}.st i{font-style:normal;color:#11111133}
.crit div{display:grid;grid-template-columns:130px 1fr 36px;gap:10px;align-items:center;padding:5px 0;font-size:14px}
.crit i{display:block;height:8px;background:#1111111a}.crit i b{display:block;height:100%;background:var(--volt);border-right:2px solid var(--ink)}
.crit em{font:700 13px var(--mono);font-style:normal;text-align:right}
.again{margin-top:12px;font-size:15px}.again b{font:700 18px var(--mono)}
.rv{padding:16px 0;border-bottom:1px solid var(--line)}
.rv .who{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}.rv .who b{font-weight:800}.rv .who span{color:var(--grey);font:500 12px var(--mono);text-transform:uppercase}
.rv p{margin-top:6px}.rv .rep{margin-top:8px;padding:10px 12px;background:#fff;border-left:3px solid var(--volt);font-size:14px}
.empty{margin-top:16px;padding:18px;border:1px dashed var(--ink);background:#fff}
.disc{margin-top:16px;color:var(--grey);font-size:13px}
.more{margin-top:12px;list-style:none;padding:0}.more li{border-bottom:1px solid var(--line)}
.more a{display:flex;justify-content:space-between;gap:12px;padding:12px 0;text-decoration:none}.more a:hover b{text-decoration:underline}.more span{color:var(--grey);font:500 12px var(--mono);white-space:nowrap}
footer{border-top:1px solid var(--ink);padding:20px;text-align:center;color:#555;font:500 11px/1.8 var(--mono);text-transform:uppercase}
@media (max-width:400px){header nav .hs{display:none}}
@media (max-width:600px){header{padding-left:16px}main{padding:22px 16px 40px}.sum{grid-template-columns:1fr;gap:12px}.crit div{grid-template-columns:110px 1fr 32px}}"""


def page(r, s, revs, others, today):
    url = f"{BASE}/race/{slug(r['name'])}.html"
    past = r["date_start"] <= today
    n = s["n"] if s else 0
    avg = float(s["s_all"]) if s else 0
    cats = "/".join(r.get("cats") or [])
    year = r["date_start"][:4]
    if n:
        desc = f"{r['name']}: {avg:.1f}/5 dari {n} pelari. Rating organisasi, laluan, water station, medal dan harga, plus ulasan pelari yang dah join."
    else:
        desc = f"{r['name']}, {when(r)} di {r['place']}. Info race, kategori {cats}, dan rating pelari lepas race."
    title = f"{r['name']}: rating dan ulasan pelari · SihatLab"

    facts = [("Tarikh", when(r))]
    if r.get("flagoff"):
        facts.append(("Flag off", r["flagoff"]))
    facts += [("Tempat", r["place"]), ("Negeri", r["state"]), ("Kategori", cats or "-")]
    facts_html = "".join(f"<div><span>{e(k)}</span><b>{e(v)}</b></div>" for k, v in facts)
    if r.get("url"):
        facts_html += f'<div><span>Laman rasmi</span><b><a href="{e(r["url"])}" rel="noopener nofollow" target="_blank">{e(host(r["url"]))}</a></b></div>'

    rate_url = f"../race.html?rate=1#{r['id']}"
    cal_url = f"../race.html#{r['id']}"
    if past:
        cta = f'<a class="v" href="{rate_url}">★ Rate race ni</a><a href="{cal_url}">Tengok dalam kalendar</a>'
    else:
        cta = f'<a class="v" href="{cal_url}">Countdown dan kira pace</a>'
    if r.get("url"):
        cta += f'<a href="{e(r["url"])}" rel="noopener nofollow" target="_blank">Laman rasmi</a>'

    if n:
        crit = "".join(f'<div><span>{lab}</span><i><b style="width:{float(s["s_" + k]) / 5 * 100:.0f}%"></b></i><em>{float(s["s_" + k]):.1f}</em></div>' for k, lab in KEYS)
        rating = (f'<div class="sum"><div class="avg"><b>{avg:.1f}</b>{stars(avg)}<small>{n} rating pelari</small></div><div class="crit">{crit}</div></div>'
                  f'<p class="again"><b>{s["again_pct"]}%</b> nak join lagi tahun depan.</p>')
    elif past:
        rating = f'<p class="empty">Belum ada rating untuk race ni. Kau join? <a href="{rate_url}"><b>Jadi orang pertama rate</b></a>.</p>'
    else:
        rating = f'<p class="empty">Race ni belum berlangsung. Rating dibuka lepas {d(r["date_start"], True)}. Lepas race, datang balik dan bagi rating.</p>'

    rv_html = ""
    for v in revs:
        rep = ""
        if v.get("org_reply"):
            rep += f'<div class="rep"><b>Balasan penganjur:</b> {e(v["org_reply"])}</div>'
        if v.get("reply"):
            rep += f'<div class="rep"><b>Balasan SihatLab:</b> {e(v["reply"])}</div>'
        rv_html += (f'<div class="rv"><div class="who"><b>{e(v["display_name"])}</b><span>{e(v["cat"])} · {d(v["created_at"][:10])}</span>{stars(v["s_all"])}</div>'
                    f'<p>{e(v["body"])}</p>{rep}</div>')
    reviews = ""
    if rv_html:
        reviews = (f'<h2>Apa kata pelari</h2>{rv_html}'
                   '<p class="disc">Ulasan ialah pendapat peribadi pelari, bukan pandangan SihatLab. Ayat ulasan disemak sebelum keluar. '
                   '<a href="../terma.html">Terma</a></p>')

    more = "".join(f'<li><a href="{slug(o["name"])}.html"><b>{e(o["name"])}</b><span>{d(o["date_start"])}</span></a></li>' for o in others)

    ld = {
        "@context": "https://schema.org", "@type": "SportsEvent", "name": r["name"], "url": url,
        "startDate": r["date_start"] + (f"T{r['flagoff']}:00+08:00" if r.get("flagoff") else ""),
        "endDate": r.get("date_end") or r["date_start"],
        "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "sport": "Running", "description": r.get("note") or desc,
        "location": {"@type": "Place", "name": r["place"], "address": {"@type": "PostalAddress", "addressLocality": r["place"], "addressRegion": r["state"], "addressCountry": "MY"}},
        "image": [f"{BASE}/og-race.jpg"],
    }
    if r.get("organizer_name"):
        ld["organizer"] = {"@type": "Organization", "name": r["organizer_name"]}
    if n:
        ld["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": f"{avg:.1f}", "ratingCount": n, "bestRating": 5, "worstRating": 1}
    if revs:
        ld["review"] = [{"@type": "Review", "author": {"@type": "Person", "name": v["display_name"]}, "datePublished": v["created_at"][:10],
                         "reviewBody": v["body"], "reviewRating": {"@type": "Rating", "ratingValue": v["s_all"], "bestRating": 5, "worstRating": 1}} for v in revs[:10]]
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "SihatLab", "item": f"{BASE}/"},
        {"@type": "ListItem", "position": 2, "name": "Race", "item": f"{BASE}/race.html"},
        {"@type": "ListItem", "position": 3, "name": r["name"], "item": url}]}

    lede = (f"Rating dan ulasan dari pelari yang dah join {e(r['name'])}." if past else
            f"{e(r['name'])} pada {when(r)}. Tengok info race sekarang, dan lepas race baca rating dari pelari yang join.")
    return f"""<!doctype html>
<html lang="ms">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{e(r['name'])}: rating pelari · SihatLab">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{BASE}/og-race.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="../favicon.png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumbs, ensure_ascii=False)}</script>
</head>
<body>
<header><a href="../index.html"><img src="../logo-dark.png" alt="SihatLab" height="20"></a><nav><a href="../race.html">Race</a><a class="hs" href="../kalkulator.html">Kalkulator</a><a class="v" href="../kelas.html">Kelas</a></nav></header>
<main>
<p class="crumb mono"><a href="../index.html">SihatLab</a> / <a href="../race.html">Race</a> / {year}</p>
<h1>{e(r['name'])}</h1>
<p class="lede">{lede}</p>
<div class="facts">{facts_html}</div>
{f'<p class="note">{e(r["note"])}</p>' if r.get("note") else ""}
<div class="cta">{cta}</div>
<h2>Rating pelari</h2>
{rating}
{reviews}
<h2>Race lain</h2>
<ul class="more">{more}</ul>
<p class="disc">Info race diambil dari laman rasmi dan berita. Sentiasa semak laman rasmi penganjur sebelum daftar atau bayar. Kemas kini {d(today)}.</p>
</main>
<footer>© {today[:4]} {COMPANY} · <a href="../terma.html">Terma</a> · <a href="../privasi.html">Privasi</a> · <a href="mailto:hai@sihatlab.com.my">hai@sihatlab.com.my</a></footer>
</body>
</html>
"""


def main():
    try:
        races = get("races?select=id,name,date_start,date_end,flagoff,place,state,cats,url,note,organizer_name&status=eq.approved&order=date_start")
        sums = {s["race_id"]: s for s in get("race_summary?select=*")}
        revs = get("review_list?select=race_id,display_name,cat,s_all,body,reply,org_reply,created_at&status=eq.approved&body=not.is.null&order=created_at.desc")
    except Exception as ex:  # keep the last pages if the database can't be reached
        print(f"race pages: skipped, could not reach Supabase ({ex})")
        return 0
    today = date.today().isoformat()
    OUT.mkdir(exist_ok=True)
    keep = set()
    for r in races:
        mine = [v for v in revs if v["race_id"] == r["id"]]
        others = sorted([o for o in races if o["id"] != r["id"]], key=lambda o: abs(date.fromisoformat(o["date_start"]) - date.fromisoformat(r["date_start"])))[:6]
        name = f"{slug(r['name'])}.html"
        (OUT / name).write_text(page(r, sums.get(r["id"]), mine, others, today), encoding="utf-8")
        keep.add(name)
    for old in OUT.glob("*.html"):  # race removed or renamed
        if old.name not in keep:
            old.unlink()

    # Plain links in race.html so crawlers find every race page.
    links = "".join(f'<li><a href="race/{slug(r["name"])}.html">{e(r["name"])}</a></li>' for r in sorted(races, key=lambda r: r["date_start"], reverse=True))
    rh = SITE / "race.html"
    t = rh.read_text(encoding="utf-8")
    t2 = re.sub(r"(<!-- race-pages:start -->).*?(<!-- race-pages:end -->)", lambda m: m.group(1) + links + m.group(2), t, flags=re.S)
    if t2 != t:
        rh.write_text(t2, encoding="utf-8")

    # Sitemap: static pages stay, race pages are regenerated.
    sm = SITE / "sitemap.xml"
    x = re.sub(r"\s*<url><loc>https://sihatlab\.com\.my/race/[^<]+</loc>.*?</url>", "", sm.read_text(encoding="utf-8"))
    entries = "".join(f'\n  <url><loc>{BASE}/race/{slug(r["name"])}.html</loc><lastmod>{today}</lastmod><priority>0.7</priority></url>' for r in races)
    sm.write_text(x.replace("\n</urlset>", entries + "\n</urlset>"), encoding="utf-8")
    print(f"race pages: {len(races)} built, {len(revs)} review texts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
