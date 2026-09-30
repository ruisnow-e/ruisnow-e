"""Builds my résumé as a film end-credit crawl, in two cuts from one credits list:

  assets/reel.svg   auto-rolling trailer for the GitHub profile README (GitHub renders
                    SVGs as plain images, so no scrolling or links are possible there)
  site/index.html   interactive version: scroll / keyboard control, hover underlines, links

Follows feature-film crawl conventions: white on black, one sans-serif family,
centered gutter (roles right-aligned, names left-aligned in caps), headings set
apart by caps and space rather than color, constant slow speed, hard frame edges.

Run:  python3 src/build.py
"""
import base64
import hashlib
import html
import io
import pathlib
import re

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "src" / "fonts"
FACES = {
    (400, "normal"): "Inter-Regular.ttf",
    (500, "normal"): "Inter-Medium.ttf",
    (700, "normal"): "Inter-Bold.ttf",
}
# No italic faces on purpose: titles of works are slanted versions of the upright
# letterforms (browser-synthesized oblique), not Inter's rounder true italic.

W, H = 1000, 560
GUTTER = 28     # half-width of the space between role and name columns (SVG)
SPEED = 34      # SVG px/s — about 6% of frame height per second, a theatrical crawl pace
LEAD_IN = 2.5   # seconds the opening card is already on screen when the README loads

SITE = "https://www.snowsong.studio"
GH = "https://github.com/ruisnow-e"
ARXIV = "https://arxiv.org/abs/2605.27705"
FILMS = f"{SITE}/work/film"
DANCE = f"{SITE}/work/dance"

# Any text may be a plain string or a (text, url) tuple.
# "pair" takes a role and one or more names (stacked); "stack" centers a label over one or more lines.
CREDITS = [
    ("card", "Directed by", ("RUI SONG", SITE)),
    ("caps", "ENGINEER  ·  FILM DIRECTOR  ·  CHOREOGRAPHER"),
    ("gap", 110),

    ("head", "EDUCATION"),
    ("pair", "M.S. Computer Science", ("NORTHEASTERN UNIVERSITY", "https://www.khoury.northeastern.edu/")),
    ("pair", "", "GPA 4.0 · MERIT SCHOLARSHIP"),
    ("pair", "MFA Film Production", ("CALIFORNIA COLLEGE OF THE ARTS", "https://www.cca.edu/")),
    ("pair", "", "MERIT SCHOLARSHIP"),
    ("pair", "B.A. Communication", "CAPITAL UNIV. OF ECONOMICS & BUSINESS"),

    ("head", "RESEARCH"),
    ("title", ("AgenticVBench", ARXIV)),
    ("line", "Can AI Agents Complete Real-World Post-Production Tasks?"),
    ("gap", 14),
    ("pair", "Authors", "ZONGHENG CAO", "YI ZHENG", "RUI SONG", "XINYU HU"),
    ("pair", "Published", ("ARXIV:2605.27705 · 2026", ARXIV)),

    ("head", "EXPERIENCE"),
    ("pair", "Khoury Student Ambassador", ("NORTHEASTERN UNIVERSITY", "https://sv-research-showcase.vercel.app/")),
    ("pair", "Member of Technical Staff", ("PHILO LABS", "https://philolabs.ai/")),
    ("pair", "Teaching Assistant", ("CALIFORNIA COLLEGE OF THE ARTS", "https://www.cca.edu/")),
    ("pair", "Student Fellow", ("THE FLAHERTY", "https://flahertyseminar.org/")),
    ("pair", "Social Video Producer", "ELLE MAGAZINE"),
    ("pair", "Assistant Business Director", "CHINA CENTRAL TELEVISION"),
    ("pair", "Social Media Volunteer", ("UNITED NATIONS VOLUNTEERS", "https://www.unv.org/")),

    ("head", "PROJECTS"),
    ("pair", "In Development", "SLATEONE"),
    ("pair", "Algorithms · Python", ("STRIPBOARD", f"{GH}/stripboard")),
    ("pair", "Multi-Domain RAG System", ("OMNIRAG", f"{GH}/OmniRAG")),
    ("pair", "Compiler, C to x86-64", ("JIVE COMPILER", f"{GH}/jive_compiler")),
    ("pair", "Pygame · TensorFlow", ("CYBER FISH TANK", f"{GH}/Cyber_Fish_Tank")),

    ("head", "FILMOGRAPHY"),
    ("pair", "Director · Screenwriter · Co-producer · Editor", ("HEIRLOOM", FILMS)),
    ("pair", "Director · Screenwriter · Editor · Colorist", ("LET ME OUT", FILMS)),
    ("pair", "Photographer · Colorist", ("REFLECTIONS OF LIFE", FILMS)),
    ("pair", "Editor", ("COMMERCIAL ADS", FILMS)),
    ("pair", "Director · Screenwriter", ("SANATORIUM", FILMS)),

    ("head", "AWARDS & SELECTIONS"),
    ("caps", "HEIRLOOM"),
    # One line per award, like Technical Skills: a list becomes "A · B · C", each part linkable.
    ("stack", "Official Selection", [
        ("KYOTO", "https://www.consortium.or.jp/en/project/kisfvf/details/2024-2"),
        ("SAN ANTONIO QFEST", f"{SITE}/films/san-antonio-qfest-2024.pdf"),
        ("SF HOLE IN THE HEAD", "https://holehead2024.eventive.org/films/671997f6f12b3b004193fb7e")]),
    ("stack", "Best Editing", ("CHICAGO FILMMAKER AWARDS", "https://cifawards.net/winners-october-2024/")),
    ("stack", "Best LGBTQ Short", [
        ("SF ARTHOUSE", "https://sanfranciscoindieshort.com/winners-july-2024/"),
        ("BERLIN", "https://berlinshortsaward.com/winners-july-2024/"),
        ("MADRID", "https://maffestival.com/winners-october-2024/"),
        ("PHOENIX", "https://phoenixshortfestival.com/winners-august-2024/")]),
    ("stack", "Honorable Mention", "LOS ANGELES SHORT FILM AWARDS"),

    ("head", "PRESS"),
    ("caps", "HEIRLOOM"),
    ("stack", "Featured in", ("UNIVERSALCINEMA MAGAZINE", "https://universalcinema.net/heirloom-navigating-family-identity-and-surrogacy-in-lgbtq-narratives/")),
    ("stack", "Listed on Japan’s largest film review platform", ("FILMARKS", "https://filmarks.com/movies/121171")),

    ("head", "CHOREOGRAPHY"),
    ("stack", "Music",
        ("ESCAPISM", DANCE), ("FUXK UP THE WORLD", DANCE), ("THE WAY I ARE", DANCE),
        ("WITH THE IE", DANCE), ("SPORTS CAR", DANCE), ("APT", DANCE),
        ("PARTY 4 U", DANCE), ("TIT FOR TAT", DANCE), ("LV BAG", DANCE)),

    # Lists read better centered, like a "special thanks" card, than hung off one short role.
    ("head", "TECHNICAL SKILLS"),
    ("stack", "Languages", "JAVA · PYTHON · C · JAVASCRIPT"),
    ("stack", "Backend", "SPRING BOOT · REST · SSE"),
    ("stack", "AI / ML", "RAG · AGENT EVALUATION · LLM-AS-JUDGE"),
    ("stack", "Video", "FFMPEG · OPENTIMELINEIO · DAVINCI RESOLVE"),

    ("gap", 120),
    ("small", "No frames were dropped in the making of this profile."),
    ("gap", 70),
    ("small", "© 2026 SNOW®", ("SNOWSONG.STUDIO", SITE), ("GITHUB", GH), ("LINKEDIN", "https://www.linkedin.com/in/ruisong09/")),
]


def esc(s):
    return html.escape(s, quote=False)


def label(item):
    if isinstance(item, list):
        return " · ".join(label(x) for x in item)
    return item[0] if isinstance(item, tuple) else item


def all_text():
    parts = []
    for kind, *a in CREDITS:
        if kind != "gap":
            parts += [label(x) for x in a]
    return "".join(parts) + " ·↑↓"


def font_faces(text):
    """Inter, subset to the glyphs actually used, as inline woff2 @font-face rules."""
    chars = set(text) | set(text.upper()) | set("0123456789")
    faces = []
    for (weight, style), name in FACES.items():
        font = TTFont(FONTS / name)
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt"]
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(chars))
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        faces.append(f"@font-face{{font-family:'Inter';font-weight:{weight};font-style:{style};font-display:block;"
                     f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(faces)


# ── Cut 1: README trailer (SVG) ────────────────────────────────────────────
def svg_crawl():
    """Lays out the credits top-down. Returns (markup, total height, opening-card center)."""
    mid = W / 2
    y, out, card_mid = 0, [], 0

    def text(x, y, s, size, weight, anchor="middle", spacing=0, opacity=1, italic=False):
        return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" '
                f'letter-spacing="{spacing}"{' font-style="italic"' if italic else ''} fill="#fff" fill-opacity="{opacity}">{esc(label(s))}</text>')

    for kind, *a in CREDITS:
        if kind == "gap":
            y += a[0]
        elif kind == "card":
            y += 18
            out.append(text(mid, y, a[0], 17, 400, opacity=.75))
            y += 64
            out.append(text(mid, y, a[1], 58, 700, spacing=6))
            card_mid = y - 30
        elif kind == "caps":
            y += 42
            out.append(text(mid, y, a[0], 13, 500, spacing=3, opacity=.75))
        elif kind == "head":
            y += 96
            out.append(text(mid, y, a[0], 14, 700, spacing=5))
            y += 18
        elif kind == "title":
            y += 34
            out.append(text(mid, y, a[0], 15, 500, spacing=.3, italic=True))
        elif kind == "line":
            y += 30
            out.append(text(mid, y, a[0], 13, 400, opacity=.7, italic=True))
        elif kind == "stack":
            if a[0]:
                y += 38
                out.append(text(mid, y, a[0], 13, 400, opacity=.7))
            for i, item in enumerate(a[1:]):
                y += (24 if a[0] else 38) if i == 0 else 26
                out.append(text(mid, y, item, 16, 500, spacing=1.5))
        elif kind == "small":
            y += 16
            out.append(text(mid, y, "  ·  ".join(label(x) for x in a), 13, 400, spacing=1, opacity=.6))
        elif kind == "pair":
            role, *names = a
            y += 34
            if role:
                out.append(text(mid - GUTTER, y, role, 15, 400, anchor="end", opacity=.7))
            for i, name in enumerate(names):
                out.append(text(mid + GUTTER, y + i * 26, name, 16, 500, anchor="start", spacing=1.5))
            y += (len(names) - 1) * 26
    return "".join(out), y, card_mid


def reel(faces):
    body_svg, total, card_mid = svg_crawl()
    T = (H + total) / SPEED
    # Start mid-roll so the "Directed by" card is on screen on first view.
    start_offset = (H / 2 + card_mid) / SPEED - LEAD_IN
    style = f"""{faces}text{{font-family:'Inter',system-ui,-apple-system,'Segoe UI',Arial,sans-serif}}
.roll{{animation:roll {T:.2f}s linear -{start_offset:.2f}s infinite}}
@keyframes roll{{from{{transform:translateY({H}px)}}to{{transform:translateY(-{total}px)}}}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>{style}</style>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="12"/></clipPath>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="#000"/>
<g class="roll">{body_svg}</g>
</g>
</svg>
""", T


# ── Cut 2: interactive page (HTML) ─────────────────────────────────────────
def link(item, cls=""):
    if isinstance(item, list):
        return " · ".join(link(x) for x in item)
    c = f' class="{cls}"' if cls else ""
    if isinstance(item, tuple):
        text, url = item
        return f'<a{c} href="{esc(url)}" target="_blank" rel="noopener">{esc(text)}</a>'
    return f"<span{c}>{esc(item)}</span>" if cls else esc(item)


def html_crawl():
    out = []
    for kind, *a in CREDITS:
        if kind == "gap":
            out.append(f'<div style="height:{a[0] / 16:.2f}em"></div>')
        elif kind == "card":
            out.append(f'<p class="by">{esc(a[0])}</p><h1>{link(a[1])}</h1>')
        elif kind == "caps":
            out.append(f'<p class="caps">{esc(a[0])}</p>')
        elif kind == "head":
            out.append(f"<h2>{esc(a[0])}</h2>")
        elif kind == "title":
            out.append(f"<h3>{link(a[0])}</h3>")
        elif kind == "line":
            out.append(f'<p class="line">{esc(a[0])}</p>')
        elif kind == "stack":
            out.append('<div class="stack">' + (f'<div class="role">{esc(a[0])}</div>' if a[0] else '') + '<div class="names">' + "".join(f"<div>{link(n)}</div>" for n in a[1:]) + '</div></div>')
        elif kind == "small":
            out.append('<p class="small">' + '<span class="dot">·</span>'.join(link(x) for x in a) + "</p>")
        elif kind == "pair":
            role, *names = a
            out.append(f'<div class="pair"><div class="role">{esc(role)}</div><div class="names">'
                       + "".join(f"<div>{link(n)}</div>" for n in names) + "</div></div>")
    return "\n".join(out)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rui Song — End Credits</title>
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<meta name="description" content="Rui Song — Engineer, Film Director, Choreographer. Résumé as a film end-credit crawl.">
<style>
__FACES__
:root{--u:clamp(12px,1.6vw,17px)}
*{box-sizing:border-box;margin:0}
html{background:#000;color:#fff;font-family:'Inter',system-ui,-apple-system,'Segoe UI',Arial,sans-serif;
  -webkit-font-smoothing:antialiased;scrollbar-width:none}
html::-webkit-scrollbar{display:none}
body{font-size:var(--u);text-align:center}
main{padding:calc(50vh - 4em) 1.5em 100vh}
a,span{color:inherit;text-decoration:none}
a{position:relative;cursor:pointer;display:inline-block;line-height:1.15}
/* Underline hugs the glyphs; right inset cancels the trailing letter-spacing. */
a::after{content:"";position:absolute;left:0;right:var(--ls,0);bottom:-.14em;height:1px;background:currentColor;
  transform:scaleX(0);transform-origin:left;transition:transform .35s cubic-bezier(.2,.7,.2,1)}
a:hover::after,a:focus-visible::after{transform:scaleX(1)}
a:focus-visible{outline:none}
.by{font-size:1.06em;opacity:.75}
h1{font-size:3.6em;font-weight:700;letter-spacing:.1em;margin:.35em 0 .15em;padding-left:.1em}
h1 a{--ls:.1em}h1 a::after{height:2px;bottom:-.06em}
.names a{--ls:.09em}h3 a{--ls:.02em}
.caps{font-size:.8em;font-weight:500;letter-spacing:.23em;opacity:.75;margin-top:1em}
h2{font-size:.88em;font-weight:700;letter-spacing:.36em;padding-left:.36em;margin:6em 0 1.1em}
h3{font-size:.94em;font-weight:500;font-style:italic;letter-spacing:.02em;margin-top:.4em}
.line{font-size:.82em;font-style:italic;opacity:.7;margin-top:.6em}
.small{font-size:.8em;letter-spacing:.06em;opacity:.6}
.dot{margin:0 .8em}
.pair{display:grid;grid-template-columns:1fr 1fr;column-gap:3.5em;margin-top:.85em;line-height:1.6}
.stack{margin-top:1.3em;line-height:1.6}.stack .role{text-align:center}.stack .names{text-align:center}
.role{text-align:right;font-size:.94em;opacity:.7}
.names{text-align:left;font-weight:500;letter-spacing:.09em}
@media (max-width:560px){.pair{column-gap:1.5em}h1{font-size:2.6em}}
#hud{position:fixed;right:1.8em;bottom:1.6em;display:flex;gap:1.4em;
  font-size:11px;letter-spacing:.2em;color:#fff;opacity:.45;transition:opacity .6s;pointer-events:none}
#hud.hide{opacity:0}
#play{pointer-events:auto;cursor:pointer;background:none;border:0;color:inherit;font:inherit;letter-spacing:inherit}
</style>
</head>
<body>
<main id="crawl">
__CREDITS__
</main>
<div id="hud"><button id="play" aria-label="Play or pause the roll">❚❚ PAUSE</button><span>SCROLL · ↑ ↓ · SPACE</span></div>
<script>
(() => {
  const hud = document.getElementById("hud"), btn = document.getElementById("play");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let dir = reduce ? 0 : 1, last = 0, pos = scrollY, idle;

  const speed = () => innerHeight * 0.06;               // px/s — theatrical crawl pace
  const end = () => document.documentElement.scrollHeight - innerHeight;
  const label = () => btn.textContent = dir ? "❚❚ PAUSE" : "▶ PLAY";
  const set = d => { dir = d; pos = scrollY; label(); };
  const wake = () => { hud.classList.remove("hide"); clearTimeout(idle); idle = setTimeout(() => dir && hud.classList.add("hide"), 2500); };

  function tick(t) {
    const dt = last ? (t - last) / 1000 : 0; last = t;
    if (dir) {
      pos = Math.min(end(), Math.max(0, pos + dir * speed() * dt));
      scrollTo(0, pos);
      if (pos >= end() && dir > 0) set(0);
    }
    requestAnimationFrame(tick);
  }

  // Any manual scroll takes over; press space / play to resume from there.
  const manual = () => { if (dir) set(0); wake(); };
  addEventListener("wheel", manual, {passive: true});
  addEventListener("touchstart", manual, {passive: true});
  addEventListener("scroll", () => { if (!dir) pos = scrollY; });
  addEventListener("mousemove", wake);
  addEventListener("keydown", e => {
    const k = e.key;
    if (k === " " || k === "k" || k === "K") { e.preventDefault(); set(dir ? 0 : (scrollY >= end() ? (scrollTo(0, 0), 1) : 1)); }
    else if (k === "l" || k === "L") set(1);                 // editor shortcuts: L forward,
    else if (k === "j" || k === "J") set(-1);                // J reverse, K pause
    else if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End"].includes(k)) manual();
    wake();
  });
  btn.addEventListener("click", () => { set(dir ? 0 : 1); wake(); });

  label(); wake(); requestAnimationFrame(tick);
})();
</script>
</body>
</html>
"""


def page(faces):
    return PAGE.replace("__FACES__", faces).replace("__CREDITS__", html_crawl())


def main():
    faces = font_faces(all_text())
    svg, T = reel(faces)
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "reel.svg").write_text(svg)
    # Version the README image URL by content so browsers and GitHub's cache fetch each new cut.
    readme = ROOT / "README.md"
    v = hashlib.sha1(svg.encode()).hexdigest()[:8]
    readme.write_text(re.sub(r"reel\.svg\?v=[\w]+", f"reel.svg?v={v}", readme.read_text()))
    (ROOT / "site").mkdir(exist_ok=True)
    (ROOT / "site" / "index.html").write_text(page(faces))
    print(f"assets/reel.svg   {len(svg) // 1024} KB · loop {T:.1f}s")
    print(f"site/index.html   {len(page(faces)) // 1024} KB")


if __name__ == "__main__":
    main()
