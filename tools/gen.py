#!/usr/bin/env python3
"""Generate animated SVGs for the Nam0101 profile README.

usage: python3 -I gen.py <assets_out_dir> <icons_dir> <worlds.json>  (or just run tools/build.sh)

worlds.json comes from tools/export.ts: scenes, rigs and Claude's desks from the claude-multiverse mod.
"""
import html
import json
import math
import pathlib
import re
import sys
import unicodedata

OUT = pathlib.Path(sys.argv[1])
ICONS = pathlib.Path(sys.argv[2])
MV = json.loads(pathlib.Path(sys.argv[3]).read_text())
OUT.mkdir(parents=True, exist_ok=True)

PINK, MAG, PURPLE, INDIGO, CYAN, GREEN = "#f72585", "#b5179e", "#7209b7", "#3a0ca3", "#4cc9f0", "#3ddc84"
SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','Fira Code','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def esc(s):
    return html.escape(s, quote=False)


def write(name, body):
    (OUT / name).write_text(body, encoding="utf-8")
    print(f"{name}: {len(body.encode()) / 1024:.1f} KB")


def stars(rnd, n, x0, x1, y0, y1, avoid=None):
    out = []
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if avoid and avoid(x, y):
            continue
        r = rnd.choice([0.6, 0.8, 1.0, 1.2, 1.5])
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="tw" '
            f'style="animation-duration:{rnd.uniform(2, 5):.1f}s;animation-delay:-{rnd.uniform(0, 5):.1f}s"/>'
        )
    return "".join(out)


# ---------------------------------------------------------------- editor + phone
KW = {"object", "val", "var", "fun", "class", "data"}
TOKEN = re.compile(r'"[^"]*"|[A-Za-z_][A-Za-z0-9_]*|\d+|\s+|.')


def tokens(line):
    out, prev = [], ""
    for m in TOKEN.finditer(line):
        t = m.group(0)
        if t.isspace():
            out.append((t, None))
            continue
        if t.startswith('"'):
            c = "s"
        elif t in KW:
            c = "k"
        elif t[0].isupper():
            c = "t"
        elif t[0].isalpha() and line[m.end():m.end() + 1] == "(":
            c = "f"
        elif t[0].isalpha() and prev == "val":
            c = "p"
        elif t[0].isdigit():
            c = "n"
        else:
            c = "d" if t[0].isalnum() else "o"
        out.append((t, c))
        prev = t
    return out


def editor_phone():
    W, H = 850, 400
    C = 16.0  # cycle seconds
    CW, X0, Y0, LH = 8.1, 56, 74, 21.5
    BG = "#120a24"
    code = [
        "object Nam : AndroidEngineer() {",
        '    val home = "Hà Nội, Việt Nam"',
        '    val school = "HUST"',
        '    val stack = listOf("Kotlin", "Compose", "KMP")',
        '    val sideQuests = listOf("Rust", "TypeScript", "MCP")',
        "",
        "    val building = listOf(",
        '        Project("rexc", "Rex terminal on Android"),',
        '        Project("mirako", "Gradle builds over SSH"),',
        '        Project("android-mcp-toolkit", "MCP tools"),',
        "    )",
        "",
        '    val motto = "Smooth at 120 FPS or it didn\'t ship."',
        "}",
    ]
    code = [unicodedata.normalize("NFC", s) for s in code]
    pct = lambda t: f"{t / C * 100:.3f}%"

    # typing schedule
    t, sched = 0.7, []
    for s in code:
        indent = len(s) - len(s.lstrip(" "))
        n = len(s) - indent
        if n == 0:
            sched.append(None)
            t += 0.15
            continue
        dur = n * 0.021
        sched.append((t, t + dur, indent, n))
        t += dur + 0.14
    t_done = t
    starts = [s[0] for s in sched if s]

    css, text, covers = [], [], []
    for i, (s, sc) in enumerate(zip(code, sched)):
        y = Y0 + i * LH
        text.append(f'<text x="40" y="{y}" class="ln">{i + 1}</text>')
        if not sc:
            continue
        spans, col = [], 0
        for tok, cls in tokens(s):
            if cls is not None:
                xs = " ".join(f"{X0 + (col + k) * CW:.1f}" for k in range(len(tok)))
                spans.append(f'<tspan class="{cls}" x="{xs}">{esc(tok)}</tspan>')
            col += len(tok)
        text.append(f'<text y="{y}" class="c">{"".join(spans)}</text>')
        t0, t1, indent, n = sc
        nxt = next((st for st in starts if st > t0), C * 0.955)
        sx = X0 + indent * CW
        css.append(
            f"@keyframes ty{i}{{0%,{pct(t0)}{{transform:translateX(0)}}{pct(t1)},100%{{transform:translateX({n * CW:.1f}px)}}}}"
            f".ty{i}{{animation:ty{i} {C}s steps({n},end) infinite}}"
            f"@keyframes cu{i}{{0%,{pct(t0 - 0.001)}{{opacity:0}}{pct(t0)},{pct(nxt - 0.001)}{{opacity:1}}{pct(nxt)},100%{{opacity:0}}}}"
            f".cu{i}{{animation:cu{i} {C}s linear infinite}}"
        )
        covers.append(
            f'<g class="ty{i}"><rect x="{sx:.1f}" y="{y - 15}" width="{n * CW + 6:.1f}" height="20" fill="{BG}"/>'
            f'<g class="cu{i}"><rect x="{sx - 1:.1f}" y="{y - 13}" width="2" height="16" fill="{PINK}" class="blink"/></g></g>'
        )
    ends = [sc[1] if sc else None for sc in sched]

    def appear(name, t_in, frm="translateY(8px)", ease="cubic-bezier(.2,1.4,.4,1)", d=0.45):
        css.append(
            f"@keyframes {name}{{0%,{pct(t_in)}{{opacity:0;transform:{frm};animation-timing-function:{ease}}}"
            f"{pct(t_in + d)},95%{{opacity:1;transform:none}}99%,100%{{opacity:0;transform:none}}}}"
            f".{name}{{animation:{name} {C}s linear infinite;transform-box:fill-box;transform-origin:center}}"
        )
        return name

    PX, PY, PW, PH = 592, 10, 220, 380
    SX0, SY0, SWD, SHT = PX + 8, PY + 8, PW - 16, PH - 16
    cxp = PX + PW / 2

    avatar = appear("av", ends[0], "scale(.2)")
    nm = appear("nm", ends[0] + 0.15)
    sub = appear("sb", ends[1])
    chips, x = [], cxp - 76
    for k, (label, w) in enumerate((("Kotlin", 46), ("Compose", 56), ("KMP", 38))):
        cls = appear(f"ch{k}", ends[3] + k * 0.12, "scale(.3)")
        chips.append(
            f'<g class="{cls}"><rect x="{x}" y="184" width="{w}" height="18" rx="9" fill="rgba(247,37,133,.16)" stroke="rgba(247,37,133,.6)"/>'
            f'<text x="{x + w / 2}" y="196.5" text-anchor="middle" class="pc">{label}</text></g>'
        )
        x += w + 6
    cards = []
    for k, (title, desc, glyph, color, line) in enumerate((
        ("rexc", "Rust core + Compose UI", "R", PINK, 7),
        ("mirako", "Gradle builds over SSH", "M", PURPLE, 8),
        ("android-mcp-toolkit", "MCP tools for Android", "A", CYAN, 9),
    )):
        cy = 214 + k * 46
        cls = appear(f"cd{k}", ends[line], "translateX(70px)", d=0.55)
        ripple = ""
        if k == 0:
            r0 = ends[12] + 1.3
            css.append(
                f"@keyframes rp{{0%,{pct(r0)}{{transform:scale(0);opacity:0}}{pct(r0 + 0.02)}{{transform:scale(0);opacity:.35}}"
                f"{pct(r0 + 0.9)},100%{{transform:scale(1);opacity:0}}}}"
                f".rp{{animation:rp {C}s ease-out infinite;transform-box:fill-box;transform-origin:center}}"
            )
            ripple = f'<g clip-path="url(#c0)"><circle cx="{SX0 + 52}" cy="{cy + 20}" r="110" fill="#fff" class="rp"/></g>'
        cards.append(
            f'<g class="{cls}"><rect x="{SX0 + 12}" y="{cy}" width="{SWD - 24}" height="40" rx="10" fill="#21153d" stroke="#3a2a63"/>'
            f'{ripple}<rect x="{SX0 + 22}" y="{cy + 9}" width="22" height="22" rx="6" fill="{color}"/>'
            f'<text x="{SX0 + 33}" y="{cy + 24.5}" text-anchor="middle" class="gl">{glyph}</text>'
            f'<text x="{SX0 + 52}" y="{cy + 17.5}" class="ct">{esc(title)}</text>'
            f'<text x="{SX0 + 52}" y="{cy + 31}" class="cs">{esc(desc)}</text>'
            f'<text x="{SX0 + SWD - 22}" y="{cy + 25}" class="cv">›</text></g>'
        )
    fps = appear("fp", ends[12], "scale(.4)")
    bars = "".join(
        f'<rect x="{cxp + 30 + k * 5}" y="352" width="3" height="12" rx="1" fill="{GREEN}" class="bar" style="animation-delay:-{k * 0.23:.2f}s"/>'
        for k in range(6)
    )
    compiling = (f"@keyframes cmp{{0%,{pct(0.5)}{{opacity:0}}{pct(0.6)},{pct(t_done)}{{opacity:1}}{pct(t_done + 0.05)},100%{{opacity:0}}}}"
                 f".cmp{{animation:cmp {C}s linear infinite}}")
    css.append(compiling)
    ok = appear("ok", t_done + 0.25, "translateY(4px)", "ease-out", 0.3)
    css.append(f"@keyframes fade{{0%{{opacity:0}}3%,95%{{opacity:1}}99%,100%{{opacity:0}}}}.fade{{animation:fade {C}s linear infinite}}")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Nam.kt: object Nam : AndroidEngineer, home Hà Nội Việt Nam, school HUST, stack Kotlin Compose KMP, side quests Rust TypeScript MCP, building rexc, mirako, android-mcp-toolkit; motto: smooth at 120 FPS or it didn't ship. A phone renders the profile as the code is typed.</title>
<style>
.c{{font:13.5px {MONO}}}
.ln{{font:12px {MONO};fill:#4b3f6b;text-anchor:end}}
.k{{fill:#ff7ab2}}.s{{fill:#c3e88d}}.t{{fill:#82aaff}}.f{{fill:{CYAN}}}.p{{fill:#f5d0fe}}.n{{fill:#f78c6c}}.d{{fill:#e6e1f5}}.o{{fill:#b9a7d6}}
.blink{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.ui{{font-family:{SANS}}}
.pc{{font:600 9.5px {SANS};fill:#ffd6ec}}
.gl{{font:700 11px {SANS};fill:#fff}}
.ct{{font:700 11.5px {SANS};fill:#fff}}
.cs{{font:9.5px {SANS};fill:#a89ccf}}
.cv{{font:16px {SANS};fill:#6b5b95}}
.bar{{transform-box:fill-box;transform-origin:50% 100%;animation:bar .9s ease-in-out infinite alternate}}
@keyframes bar{{from{{transform:scaleY(.25)}}to{{transform:scaleY(1)}}}}
.float{{animation:float 5s ease-in-out infinite}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6px)}}}}
.ring{{transform-box:fill-box;transform-origin:center;animation:ring 2s ease-out infinite}}
@keyframes ring{{from{{transform:scale(1);opacity:.8}}to{{transform:scale(1.55);opacity:0}}}}
.flow{{stroke-dasharray:4 5;animation:flow .8s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-9}}}}
.dot{{animation:dot 1.2s ease-in-out infinite}}
@keyframes dot{{50%{{opacity:.2}}}}
{"".join(css)}
{REDUCED}
</style>
<defs>
<clipPath id="ed"><rect x="1" y="1" width="538" height="398" rx="14"/></clipPath>
<clipPath id="c0"><rect x="{SX0 + 12}" y="214" width="{SWD - 24}" height="40" rx="10"/></clipPath>
<clipPath id="scr"><rect x="{SX0}" y="{SY0}" width="{SWD}" height="{SHT}" rx="26"/></clipPath>
<linearGradient id="avg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{INDIGO}"/></linearGradient>
<radialGradient id="pglow"><stop offset="0" stop-color="{PURPLE}" stop-opacity=".45"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>
</defs>
<g clip-path="url(#ed)">
<rect width="540" height="400" fill="{BG}"/>
<rect width="540" height="38" fill="#1a1030"/>
<circle cx="22" cy="19" r="6" fill="#ff5f57"/><circle cx="42" cy="19" r="6" fill="#febc2e"/><circle cx="62" cy="19" r="6" fill="#28c840"/>
<rect x="88" y="8" width="96" height="30" rx="7" fill="{BG}"/>
<rect x="100" y="17" width="12" height="12" rx="2" fill="url(#avg)"/>
<text x="120" y="28" class="ui" style="font-size:12.5px;fill:#e6e1f5">Nam.kt</text>
<text x="522" y="28" text-anchor="end" style="font:11px {MONO};fill:#6b5b95">Kotlin · UTF-8</text>
<g class="fade">{"".join(text)}{"".join(covers)}</g>
<rect y="370" width="540" height="30" fill="#1a1030"/>
<g class="cmp"><circle cx="20" cy="385" r="4" fill="#febc2e" class="dot"/><text x="32" y="389" style="font:11.5px {MONO};fill:#febc2e">compiling Nam.kt…</text></g>
<g class="ok"><text x="14" y="389" style="font:700 11.5px {MONO};fill:{GREEN}">✓ BUILD SUCCESSFUL in 0.9s</text></g>
<text x="522" y="389" text-anchor="end" style="font:11px {MONO};fill:#6b5b95">main ⎇</text>
</g>
<rect x="1" y="1" width="538" height="398" rx="14" fill="none" stroke="#3b2a63"/>
<path d="M548 200 H582" stroke="{PINK}" stroke-width="2" class="flow"/><path d="M580 194 L588 200 L580 206 Z" fill="{PINK}"/>
<ellipse cx="{cxp}" cy="205" rx="150" ry="190" fill="url(#pglow)"/>
<g class="float">
<rect x="{PX + PW - 1}" y="112" width="4" height="40" rx="2" fill="#2a2140"/>
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="34" fill="#1c1630" stroke="#4a3b6b" stroke-width="2"/>
<g clip-path="url(#scr)">
<rect x="{SX0}" y="{SY0}" width="{SWD}" height="{SHT}" fill="#140c26"/>
<text x="{SX0 + 16}" y="{SY0 + 22}" style="font:600 11px {SANS};fill:#fff">9:41</text>
<circle cx="{cxp}" cy="{SY0 + 17}" r="4.5" fill="#05020c" stroke="#2c2444"/>
<rect x="{SX0 + SWD - 50}" y="{SY0 + 14}" width="3" height="5" rx="1" fill="#fff"/><rect x="{SX0 + SWD - 45}" y="{SY0 + 12}" width="3" height="7" rx="1" fill="#fff"/><rect x="{SX0 + SWD - 40}" y="{SY0 + 10}" width="3" height="9" rx="1" fill="#fff"/>
<rect x="{SX0 + SWD - 33}" y="{SY0 + 10}" width="18" height="9" rx="2.5" fill="none" stroke="#fff"/><rect x="{SX0 + SWD - 31}" y="{SY0 + 12}" width="12" height="5" rx="1" fill="{GREEN}"/>
<text x="{SX0 + 16}" y="{SY0 + 52}" style="font:700 14px {SANS};fill:#fff">Nam.kt</text>
<rect x="{SX0 + SWD - 66}" y="{SY0 + 39}" width="52" height="18" rx="9" fill="rgba(247,37,133,.16)"/>
<circle cx="{SX0 + SWD - 56}" cy="{SY0 + 48}" r="3" fill="{PINK}" class="dot"/>
<text x="{SX0 + SWD - 49}" y="{SY0 + 51.5}" style="font:600 9px {SANS};fill:#ffd6ec">Preview</text>
<g class="{avatar}"><circle cx="{cxp}" cy="114" r="24" fill="none" stroke="{PINK}" stroke-width="2" class="ring"/>
<circle cx="{cxp}" cy="114" r="24" fill="url(#avg)"/><text x="{cxp}" y="122" text-anchor="middle" style="font:800 22px {SANS};fill:#fff">N</text></g>
<text x="{cxp}" y="158" text-anchor="middle" class="{nm}" style="font:700 14px {SANS};fill:#fff">Nguyen Van Nam</text>
<text x="{cxp}" y="174" text-anchor="middle" class="{sub}" style="font:10px {SANS};fill:#c4b5fd">Android Engineer · Hà Nội</text>
{"".join(chips)}
{"".join(cards)}
<g class="{fps}"><rect x="{cxp - 62}" y="346" width="124" height="24" rx="12" fill="rgba(61,220,132,.12)" stroke="rgba(61,220,132,.6)"/>
<circle cx="{cxp - 49}" cy="358" r="3.5" fill="{GREEN}" class="dot"/>
<text x="{cxp - 40}" y="362" style="font:700 10.5px {SANS};fill:{GREEN}">120 FPS</text>{bars}</g>
<rect x="{cxp - 32}" y="{SY0 + SHT - 8}" width="64" height="3.5" rx="2" fill="#5b4d80"/>
</g>
</g>
</svg>
'''


# ---------------------------------------------------------------- multiverse: Nam at his desk
SKIN, SKIN_SH, HAIR, HOOD, HOOD_SH, PANTS = "#f2c9a5", "#d6a583", "#1b1424", "#7209b7", "#4b0a7a", "#2a2342"
CORNER = (1180, 540)  # where the mod pins the desk box in its 1600×1000 picture
NAM_DX = -330  # Nam's desk sits left of Claude's, in the desk box's coordinates

NAM_CSS = (
    ".nm-tap{animation:nm-tap .3s ease-in-out infinite alternate}.nm-tap2{animation-delay:-.3s}"
    "@keyframes nm-tap{to{transform:translateY(-6px)}}"
    ".nm-nod{animation:nm-nod 2.6s ease-in-out infinite}@keyframes nm-nod{50%{transform:translateY(2px)}}"
    ".nm-blink{transform-box:fill-box;transform-origin:center;animation:nm-blink 4.6s infinite}"
    "@keyframes nm-blink{0%,93%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}"
    ".nm-flick{animation:nm-flick 3s infinite}@keyframes nm-flick{0%,47%,53%,100%{opacity:1}50%{opacity:.45}}"
    ".nm-puff{opacity:0;transform-box:fill-box;transform-origin:center;animation:nm-puff 2.4s ease-out infinite}"
    "@keyframes nm-puff{0%{opacity:0;transform:translate(0,0)}20%{opacity:.7}100%{opacity:0;transform:translate(18px,-22px) scale(1.8)}}"
    ".nm-bub{opacity:0;animation:nm-bub 3.3s ease-in infinite}"
    "@keyframes nm-bub{0%{opacity:0;transform:translateY(0)}15%{opacity:.8}100%{opacity:0;transform:translateY(-120px)}}"
    ".nm-scr{animation:nm-scr 2.2s ease-in-out infinite}@keyframes nm-scr{50%{opacity:.55}}"
)


def mix(a, b, t):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def star4(x, y, r, fill):
    q = r * 0.32
    return (f'<path d="M{x} {y - r}L{x + q} {y - q}L{x + r} {y}L{x + q} {y + q}L{x} {y + r}L{x - q} {y + q}L{x - r} {y}L{x - q} {y - q}Z" '
            f'fill="{fill}"/>')


def costume(kind, uid):
    """Nam's gear in one universe: (markup behind his head, markup over it)."""
    if kind == "visor":
        return "", ('<g class="nm-flick"><rect x="146" y="218" width="52" height="21" rx="9" fill="#00f0ff" fill-opacity=".26" '
                    'stroke="#5ff4ff" stroke-width="2.5"/><path d="M146 225 L122 221" stroke="#5ff4ff" stroke-width="3" stroke-linecap="round"/></g>')
    if kind == "wizard":
        return "", ('<path d="M110 196 Q158 180 208 194 Q160 208 110 196Z" fill="#2c1d5c"/>'
                    '<path d="M124 194 L190 190 Q178 150 170 128 Q166 112 186 100 Q158 100 152 126 Q140 160 124 194Z" fill="#3d2a7d"/>'
                    '<path d="M125 187 L188 183 L190 191 L124 195Z" fill="#e7b84a"/>'
                    + star4(150, 168, 5, "#ffe08a") + star4(166, 146, 4, "#ffe08a") + star4(141, 182, 3.5, "#ffe08a"))
    if kind == "helmet":
        return "", ('<rect x="118" y="260" width="78" height="10" rx="5" fill="#9aa3b5"/>'
                    '<circle cx="157" cy="221" r="55" fill="#cfeaff" fill-opacity=".08" stroke="#d6efff" stroke-opacity=".65" stroke-width="3"/>'
                    '<path d="M118 198 Q128 176 152 170" stroke="#fff" stroke-opacity=".6" stroke-width="4" fill="none" stroke-linecap="round"/>')
    if kind == "goggles":
        behind = ('<path d="M140 262 C116 262 100 270 78 262 C92 280 116 280 142 272Z" fill="#e5484d">'
                  '<animateTransform attributeName="transform" type="rotate" values="-5 140 266;7 140 266;-5 140 266" dur="1.6s" repeatCount="indefinite"/></path>')
        return behind, ('<rect x="130" y="254" width="46" height="13" rx="6" fill="#e5484d"/>'
                        '<path d="M116 206 Q156 194 200 203" stroke="#6b4a2b" stroke-width="6" fill="none"/>'
                        '<g fill="#f5b942" fill-opacity=".8" stroke="#c9a14a" stroke-width="3"><circle cx="166" cy="202" r="9"/><circle cx="187" cy="204" r="8"/></g>')
    if kind == "shades":
        return "", (f'<defs><linearGradient id="sh{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff3ea5"/>'
                    f'<stop offset="1" stop-color="#ffb347"/></linearGradient></defs>'
                    f'<g fill="url(#sh{uid})" stroke="#120c1c" stroke-width="2.6"><rect x="148" y="221" width="20" height="15" rx="4"/>'
                    f'<rect x="171" y="221" width="20" height="15" rx="4"/></g>')
    if kind == "beanie":
        puffs = "".join(f'<circle cx="200" cy="246" r="{r}" fill="#fff" class="nm-puff" style="animation-delay:{d}s"/>' for r, d in ((5, 0), (4, -1.2)))
        return "", ('<path d="M115 214 C110 182 132 166 158 166 C186 166 204 184 199 212Z" fill="#c8324a"/>'
                    '<rect x="112" y="203" width="90" height="13" rx="6.5" fill="#f2efe9"/><circle cx="158" cy="163" r="9" fill="#f2efe9"/>'
                    '<rect x="126" y="254" width="56" height="14" rx="7" fill="#f2efe9"/><rect x="166" y="262" width="13" height="36" rx="5" fill="#c8324a"/>'
                    + puffs)
    if kind == "petals":
        return "", "".join(f'<ellipse cx="{x}" cy="{y}" rx="5" ry="3" transform="rotate({a} {x} {y})" fill="#ffc0d6"/>'
                           for x, y, a in ((138, 186, 20), (168, 179, -30), (186, 192, 50)))
    if kind == "dive":
        bolts = "".join(f'<circle cx="{175 + 26 * math.cos(a):.1f}" cy="{228 + 26 * math.sin(a):.1f}" r="2.4" fill="#7a5326"/>' for a in (0.4, 2.0, 3.6, 5.2))
        bubbles = "".join(f'<circle cx="{c}" cy="168" r="{r}" fill="none" stroke="#9ff" stroke-opacity=".7" class="nm-bub" style="animation-delay:{d}s"/>'
                          for c, r, d in ((150, 4, 0), (160, 3, -1.1), (144, 2.5, -2.2)))
        return "", ('<path fill-rule="evenodd" fill="#a8743a" d="M101 222 a56 56 0 1 0 112 0 a56 56 0 1 0 -112 0Z M150 228 a25 25 0 1 0 50 0 a25 25 0 1 0 -50 0Z"/>'
                    '<circle cx="175" cy="228" r="25" fill="#2fc6c6" fill-opacity=".12" stroke="#e0b25a" stroke-width="5"/>' + bolts +
                    '<path d="M112 206 Q122 184 146 174" stroke="#ffd79a" stroke-opacity=".5" stroke-width="4" fill="none" stroke-linecap="round"/>'
                    '<rect x="112" y="262" width="90" height="12" rx="5" fill="#8a5a2a"/>' + bubbles)
    if kind == "nonla":
        ribs = "".join(f'<line x1="156" y1="150" x2="{x}" y2="207" stroke="#c9a964" stroke-width="1.2"/>' for x in (114, 132, 150, 168, 186, 204))
        return "", ('<path d="M96 205 L156 146 L216 205 Q156 217 96 205Z" fill="#ead39a"/>' + ribs +
                    '<path d="M96 205 Q156 217 216 205" stroke="#b8935a" stroke-width="3" fill="none"/>')
    return "", ""


def nam(w, uid, kind, pose="type"):
    """Nam at his own desk, drawn in the mod's desk-box coordinates (seat top 350, desk top 330, floor 456)."""
    ink, fur, metal, light = w["ink"], w["furniture"], w["metal"], w["light"]["work"]
    behind, front = costume(kind, uid)
    hood_sh, far_leg = mix(HOOD_SH, ink, 0.25), mix(PANTS, ink, 0.4)
    glow = (f'<defs><radialGradient id="ng{uid}"><stop offset="0" stop-color="{light}" stop-opacity=".3"/>'
            f'<stop offset="1" stop-color="{light}" stop-opacity="0"/></radialGradient></defs>'
            f'<ellipse cx="300" cy="284" rx="150" ry="110" fill="url(#ng{uid})"/>')
    chair = (f'<g fill="{fur}"><rect x="90" y="244" width="18" height="110" rx="9"/><rect x="96" y="348" width="96" height="12" rx="6"/>'
             f'<rect x="139" y="360" width="10" height="64" rx="3"/><rect x="104" y="430" width="80" height="8" rx="4"/>'
             f'<circle cx="110" cy="447" r="6.5"/><circle cx="178" cy="447" r="6.5"/></g>'
             f'<rect x="96" y="254" width="4" height="88" rx="2" fill="{PINK}" fill-opacity=".75"/>')
    far_arm = (f'<g class="nm-tap nm-tap2"><path d="M150 284 L196 306 L242 318" stroke="{hood_sh}" stroke-width="15" '
               f'stroke-linecap="round" stroke-linejoin="round" fill="none"/><circle cx="247" cy="318" r="6.5" fill="{SKIN_SH}"/></g>')
    legs_far = (f'<g fill="{far_leg}"><rect x="126" y="328" width="70" height="20" rx="10"/><rect x="180" y="334" width="15" height="104" rx="7"/></g>'
                f'<rect x="174" y="434" width="34" height="14" rx="7" fill="#b9b9c8"/>')
    torso = (f'<path d="M106 298 Q100 258 132 252 L148 268 Q120 270 118 302Z" fill="{hood_sh}"/>'
             f'<path d="M114 352 L114 290 Q114 262 142 262 L158 262 Q186 262 186 290 L186 352Z" fill="{HOOD}"/>'
             f'<path d="M114 352 L114 290 Q114 264 134 262 L134 352Z" fill="{ink}" fill-opacity=".28"/>'
             f'<rect x="181" y="282" width="5" height="66" rx="2.5" fill="{light}" fill-opacity=".35"/>'
             f'<path d="M168 266 v26 M176 266 v22" stroke="#ffd6ec" stroke-width="2.5" stroke-linecap="round"/>'
             f'<path d="M148 328 h32 l5 16 h-40z" fill="{hood_sh}" fill-opacity=".7"/>')
    legs = (f'<g fill="{PANTS}"><rect x="134" y="332" width="74" height="22" rx="11"/><rect x="192" y="338" width="16" height="104" rx="8"/></g>'
            f'<rect x="186" y="436" width="38" height="15" rx="7.5" fill="#f4f4f8"/><rect x="186" y="447" width="38" height="4" rx="2" fill="{PINK}"/>')
    head = (f'<g class="nm-nod">{behind}<rect x="141" y="250" width="22" height="18" fill="{SKIN_SH}"/>'
            f'<path d="M114 248 C102 206 122 176 156 176 C190 176 204 196 200 220 L122 238Z" fill="{HAIR}"/>'
            f'<rect x="118" y="186" width="76" height="74" rx="30" fill="{SKIN}"/>'
            f'<path d="M126 196 Q118 210 119 236 Q121 254 138 259 L136 196Z" fill="{ink}" fill-opacity=".12"/>'
            f'<path d="M193 210 Q198 232 190 254" stroke="{light}" stroke-opacity=".55" stroke-width="3" fill="none" stroke-linecap="round"/>'
            f'<ellipse cx="128" cy="231" rx="7" ry="9" fill="{SKIN_SH}"/>'
            f'<path d="M116 224 C112 190 132 174 160 175 C188 176 202 192 197 214 L189 206 L184 217 L176 203 L169 215 L161 201 L153 213 '
            f'L146 200 L140 212 C131 210 127 216 127 228Z" fill="{HAIR}"/>'
            f'<g class="nm-blink"><rect x="156.5" y="226" width="4.5" height="6.5" rx="2.2" fill="#120c1c"/>'
            f'<rect x="179.5" y="226" width="4.5" height="6.5" rx="2.2" fill="#120c1c"/></g>'
            f'<g fill="{light}" fill-opacity=".14" stroke="#120c1c" stroke-width="2.6"><rect x="149" y="221" width="18" height="15" rx="5"/>'
            f'<rect x="172" y="221" width="18" height="15" rx="5"/></g>'
            f'<path d="M167 227 h5 M149 226 L130 224" stroke="#120c1c" stroke-width="2.4" stroke-linecap="round"/>'
            f'<path d="M152 233 l6 -8 M175 233 l6 -8" stroke="{light}" stroke-opacity=".55" stroke-width="1.6"/>'
            f'<circle cx="189" cy="244" r="4.5" fill="#ff7aa8" fill-opacity=".35"/>'
            f'<path d="M168 247 q6 5 12 0" stroke="#7a3b2e" stroke-width="2.2" fill="none" stroke-linecap="round"/>{front}</g>')
    desk = (f'<g fill="{fur}"><rect x="176" y="330" width="226" height="12" rx="2"/><rect x="384" y="342" width="12" height="114"/>'
            f'<rect x="258" y="342" width="10" height="114"/></g>')
    laptop = (f'<rect x="232" y="323" width="90" height="7" rx="2" fill="{metal}"/><path d="M316 327 L322 250 L329 251 L323 328Z" fill="{metal}"/>'
              f'<line x1="317" y1="324" x2="323" y2="253" stroke="{light}" stroke-width="2.5" class="nm-scr"/>')
    coffee = ('<g transform="translate(350 296)"><path d="M0 0 L18 0 L16 34 L2 34Z" fill="#fff" fill-opacity=".12" stroke="#fff" stroke-opacity=".5" stroke-width="1.5"/>'
              '<path d="M1.6 12 L16.4 12 L15.8 33 L2.2 33Z" fill="#7a4a2b"/><path d="M2 24 L16 24 L15.8 33 L2.2 33Z" fill="#c69a6d"/>'
              '<rect x="4" y="13" width="5" height="5" rx="1" fill="#fff" fill-opacity=".55"/><rect x="10" y="16" width="5" height="5" rx="1" fill="#fff" fill-opacity=".45"/>'
              f'<line x1="12" y1="-12" x2="9" y2="30" stroke="{PINK}" stroke-width="2.5" stroke-linecap="round"/></g>')
    if pose == "wave":
        near = (f'<g><path d="M166 286 L196 262 L208 224" stroke="{HOOD}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                f'<circle cx="210" cy="216" r="8" fill="{SKIN}"/>'
                '<animateTransform attributeName="transform" type="rotate" values="-8 168 286;10 168 286;-8 168 286" dur="1.1s" repeatCount="indefinite"/></g>')
    else:
        near = (f'<g class="nm-tap"><path d="M166 286 L208 310 L252 320" stroke="{HOOD}" stroke-width="16" stroke-linecap="round" '
                f'stroke-linejoin="round" fill="none"/><circle cx="258" cy="320" r="7" fill="{SKIN}"/></g>')
    figure = chair + far_arm + legs_far + torso + legs + head + desk + laptop + coffee + near
    return glow + (f'<g class="bob">{figure}</g>' if w["floating"] else figure)


def desk_pair(w, uid, kind, pose="type", nook=True):
    """Nam's desk beside Claude's, in the desk box's coordinates, inside the world's own furniture."""
    return ((w["nook"] if nook else "") + f'<g transform="translate({NAM_DX} 0)">{nam(w, uid, kind, pose)}</g>'
            + w["claude"] + (w["front"] if nook else ""))


def pins(aspect):
    """The mod's top/bottom pins for a picture this wide, exact instead of stepped."""
    shift = max(0.0, (1000 - 1600 / aspect) / 2)
    return shift, f".mv-b{{transform:translateY(-{shift:.1f}px)}}.mv-t{{transform:translateY({shift:.1f}px)}}"


def picture(w, uid, kind, pose="type"):
    """A whole universe in the mod's 1600×1000 picture, Nam and Claude at their desks in the corner."""
    return (w["scenery"] + f'<g class="mv-r"><g class="mv-b"><g transform="translate({CORNER[0]} {CORNER[1]})">'
            f'{desk_pair(w, uid, kind, pose)}</g></g></g>')


def label(w, x, y, extra=""):
    light = w["light"]["work"]
    return (f'<g transform="translate({x} {y})"><text class="nm-ux" fill="{light}">UNIVERSE {w["index"]:03d}/{w["total"]}</text>'
            f'<text y="62" class="nm-un" stroke="{light}">{esc(w["name"].upper())}</text>'
            f'<text y="110" class="nm-ur"><tspan fill="#ff7ab2">nam</tspan><tspan fill="#e6e1f5">.role = </tspan>'
            f'<tspan fill="#c3e88d">"{esc(w["role"].lower())}"</tspan></text>{extra}</g>')


TITLE_CSS = (
    f".nm-hi{{font:500 30px {MONO};fill:#f9a8d4}}"
    f".nm-name{{font:800 92px {SANS};letter-spacing:-1px}}"
    f".nm-sub{{font:500 32px {SANS};fill:#ede4ff}}"
    f".nm-ux{{font:700 24px {SANS};letter-spacing:6px}}"
    f".nm-un{{font:800 56px {SANS};letter-spacing:3px;fill:#fff;stroke-width:2;stroke-opacity:.55;paint-order:stroke}}"
    f".nm-ur{{font:500 28px {MONO}}}"
    ".nm-caret{animation:nm-caret 1s steps(1) infinite}@keyframes nm-caret{50%{opacity:0}}"
)
TITLE_DEFS = (
    '<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="800" y2="0">'
    '<stop offset="0" stop-color="#fff"/><stop offset=".42" stop-color="#fff"/><stop offset=".5" stop-color="#ff8fd0"/>'
    '<stop offset=".58" stop-color="#fff"/><stop offset="1" stop-color="#fff"/>'
    '<animateTransform attributeName="gradientTransform" type="translate" values="-900 0;900 0" dur="5s" repeatCount="indefinite"/></linearGradient>'
    f'<filter id="neon" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur in="SourceAlpha" stdDeviation="9" result="b"/>'
    f'<feFlood flood-color="{PINK}" flood-opacity=".85"/><feComposite in2="b" operator="in" result="g"/>'
    '<feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    '<linearGradient id="scrim" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#07031a" stop-opacity=".86"/>'
    '<stop offset=".6" stop-color="#07031a" stop-opacity=".55"/><stop offset="1" stop-color="#07031a" stop-opacity="0"/></linearGradient>'
)

HERO_WORLDS = [("neon-2099", "visor"), ("dragonfire", "wizard"), ("black-hole", "helmet"), ("sky-whales", "goggles"),
               ("synthwave-highway", "shades"), ("polar-night", "beanie"), ("cherry-blossom", "petals"), ("deep", "dive")]


def hero():
    W, H = 850, 354
    shift, pin = pins(W / H)
    n, S, TR, R = len(HERO_WORLDS), 5.0, 1.1, 1320
    T = n * S
    kt = lambda t: f"{t / T:.4f}"
    # the portal opens from Nam's laptop screen
    pcx, pcy = CORNER[0] + NAM_DX + 320, CORNER[1] - shift + 290
    loop = f'dur="{T:g}s" repeatCount="indefinite"'
    defs, scenes, rings, labels = [], [], [], []
    for k, (wid, kind) in enumerate(HERO_WORLDS):
        w = MV["worlds"][wid]
        if k == 0:
            shown = ("inline;none;inline", f"0;{kt(S + TR)};{kt(T - TR)}")
            said = ("inline;none;inline", f"0;{kt(S + TR / 2)};{kt(T - TR / 2)}")
        elif k < n - 1:
            shown = ("none;inline;none", f"0;{kt(k * S)};{kt((k + 1) * S + TR)}")
            said = ("none;inline;none", f"0;{kt(k * S + TR / 2)};{kt((k + 1) * S + TR / 2)}")
        else:
            shown = ("none;inline", f"0;{kt(k * S)}")
            said = ("none;inline;none", f"0;{kt(k * S + TR / 2)};{kt(T - TR / 2)}")
        clip = ""
        if k > 0:
            a, b = k * S, k * S + TR
            if k < n - 1:
                r = (f"0;0;{R};{R}", f"0;{kt(a)};{kt(b)};1", "0 0 1 1;.3 0 .2 1;0 0 1 1")
            else:
                r = (f"0;0;{R};{R};0", f"0;{kt(a)};{kt(b)};{kt(T - TR)};1", "0 0 1 1;.3 0 .2 1;0 0 1 1;.7 0 .9 .5")
            grow = f'<animate attributeName="r" values="{r[0]}" keyTimes="{r[1]}" calcMode="spline" keySplines="{r[2]}" {loop}/>'
            defs.append(f'<clipPath id="pc{k}"><circle cx="{pcx}" cy="{pcy}" r="0">{grow}</circle></clipPath>')
            clip = f' clip-path="url(#pc{k})"'
            rings.append(
                f'<circle cx="{pcx}" cy="{pcy}" r="0" fill="none" stroke="url(#ring)" stroke-width="18" stroke-dasharray="70 34" opacity="0">'
                f'<animate attributeName="r" values="0;0;{R};{R}" keyTimes="0;{kt(a)};{kt(b)};1" calcMode="spline" keySplines="0 0 1 1;.3 0 .2 1;0 0 1 1" {loop}/>'
                f'<animate attributeName="opacity" values="0;0;1;.8;0;0" keyTimes="0;{kt(a)};{kt(a + .08)};{kt(a + TR * .6)};{kt(b)};1" {loop}/>'
                '<animate attributeName="stroke-dashoffset" values="0;-520" dur="1.6s" repeatCount="indefinite"/></circle>'
            )
        scenes.append(
            f'<g display="{"inline" if k == 0 else "none"}"><animate attributeName="display" values="{shown[0]}" keyTimes="{shown[1]}" '
            f'calcMode="discrete" {loop}/><g{clip}>{picture(w, f"h{k}", kind)}</g></g>'
        )
        dot = f'<circle cx="{8 + k * 30}" cy="146" r="8" fill="{w["light"]["work"]}"/>'
        labels.append(
            f'<g display="{"inline" if k == 0 else "none"}"><animate attributeName="display" values="{said[0]}" keyTimes="{said[1]}" '
            f'calcMode="discrete" {loop}/>{label(w, 92, 548, dot)}</g>'
        )
    a = T - TR
    rings.append(
        f'<circle cx="{pcx}" cy="{pcy}" r="{R}" fill="none" stroke="url(#ring)" stroke-width="18" stroke-dasharray="70 34" opacity="0">'
        f'<animate attributeName="r" values="{R};{R};0" keyTimes="0;{kt(a)};1" calcMode="spline" keySplines="0 0 1 1;.7 0 .9 .5" {loop}/>'
        f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{kt(a)};{kt(a + .1)};{kt(T - .15)};1" {loop}/>'
        '<animate attributeName="stroke-dashoffset" values="0;520" dur="1.6s" repeatCount="indefinite"/></circle>'
    )
    dots = "".join(f'<circle cx="{100 + k * 30}" cy="694" r="5" fill="#fff" fill-opacity=".28"/>' for k in range(n))
    styles = "".join(MV["worlds"][wid]["style"] for wid, _ in HERO_WORLDS)
    names = ", ".join(MV["worlds"][wid]["name"] for wid, _ in HERO_WORLDS)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" class="st-responding" role="img" aria-labelledby="t">
<title id="t">Nguyen Van Nam, Android Engineer: Kotlin, Jetpack Compose, Rust. Nam and Claude code side by side while a portal from Nam's laptop jumps them through eight universes of the claude-multiverse mod: {names}.</title>
<style>{MV["common"]}{MV["rig"]}{pin}{NAM_CSS}{TITLE_CSS}{styles}</style>
<defs>{TITLE_DEFS}<linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{PINK}"/><stop offset=".5" stop-color="#c77dff"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>{"".join(defs)}</defs>
{"".join(scenes)}
<rect width="1000" height="1000" fill="url(#scrim)"/>
{"".join(rings)}
<text x="90" y="292" class="nm-hi">// hello, multiverse! I'm<tspan class="nm-caret" fill="{PINK}">_</tspan></text>
<text x="84" y="388" class="nm-name" fill="url(#shine)" filter="url(#neon)">Nguyen Van Nam</text>
<text x="90" y="448" class="nm-sub">Android Engineer · Kotlin · Jetpack Compose · Rust</text>
{dots}{"".join(labels)}
</svg>
'''


def footer():
    W, H = 850, 354
    w = MV["worlds"]["golden-hour"]
    shift, pin = pins(W / H)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" class="{w["classes"]}" role="img" aria-labelledby="t">
<title id="t">Golden Hour, universe {w["index"]} of {w["total"]}: Nam, in a conical hat, waves goodbye while Claude celebrates a finished job. Thanks for stopping by, see you in another universe.</title>
<style>{MV["common"]}{MV["rig"]}{pin}{NAM_CSS}{TITLE_CSS}{w["style"]}</style>
<defs>{TITLE_DEFS}</defs>
{picture(w, "f", "nonla", "wave")}
<rect width="1000" height="1000" fill="url(#scrim)"/>
<text x="90" y="300" class="nm-hi">// thanks for stopping by<tspan class="nm-caret" fill="{PINK}">_</tspan></text>
<text x="84" y="392" class="nm-name" fill="url(#shine)" filter="url(#neon)" style="font-size:80px">See you in</text>
<text x="84" y="478" class="nm-name" fill="url(#shine)" filter="url(#neon)" style="font-size:80px">another universe</text>
{label(w, 92, 576)}
</svg>
'''


def about():
    """The Nam.kt editor and its phone, set in Hologram City."""
    W, H, SC = 850, 440, 0.9
    w = MV["worlds"]["hologram-city"]
    inner = editor_phone()
    m = re.match(r'<svg[^>]*>\s*<title id="t">(.*?)</title>\s*<style>(.*?)</style>(.*)</svg>\s*$', inner, re.S)
    title, style, body = m.groups()
    shift, pin = pins(W / H)
    light = w["light"]["work"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Hologram City, universe {w["index"]} of {w["total"]}. {title}</title>
<style>{MV["common"]}{pin}{w["style"]}{style}</style>
<defs><clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>
<g clip-path="url(#card)">
<svg width="{W}" height="{H}" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice" class="st-responding">{w["scenery"]}</svg>
<rect width="{W}" height="{H}" fill="#03090d" fill-opacity=".38"/>
<text x="{W / 2}" y="26" text-anchor="middle" style="font:700 11px {SANS};letter-spacing:3px" fill="{light}">UNIVERSE {w["index"]:03d}/{w["total"]} · {esc(w["name"].upper())} · <tspan style="font:500 11.5px {MONO};letter-spacing:0" fill="#e6e1f5">nam.role = "{esc(w["role"].lower())}"</tspan></text>
<g transform="translate({(W - 850 * SC) / 2:.1f} 40) scale({SC})">{body}</g>
</g>
</svg>
'''


# ---------------------------------------------------------------- toolbox orbit, in Void Drift
def icon_inner(name):
    t = (ICONS / f"{name}.svg").read_text()
    m = re.search(r'<g transform="translate\(0, 0\)">\s*(<svg.*</svg>)\s*</g>', t, re.S)
    if not m:
        raise SystemExit(f"icon {name} has no body")
    return m.group(1)


def orbit():
    W, H, CX, CY = 850, 370, 425, 182
    w = MV["worlds"]["void-drift"]
    shift, pin = pins(W / H)
    rings = [
        (150, 60, 22, 1, ["kotlin", "java", "androidstudio", "gradle", "flutter", "dart"], 40),
        (255, 98, 34, 0, ["rust", "py", "ts", "js", "cpp", "react", "nodejs", "nextjs", "tailwind"], 44),
        (360, 128, 48, 1, ["firebase", "postgres", "mysql", "mongodb", "docker", "linux", "git", "github", "idea", "vscode"], 46),
    ]
    tracks, bodies = [], []
    for ri, (rx, ry, dur, cw, names, size) in enumerate(rings):
        sweep = 1 if cw else 0
        path = f"M{CX},{CY + ry} A{rx},{ry} 0 1 {sweep} {CX},{CY - ry} A{rx},{ry} 0 1 {sweep} {CX},{CY + ry}"
        tracks.append(
            f'<ellipse cx="{CX}" cy="{CY}" rx="{rx}" ry="{ry}" fill="none" stroke="url(#trk)" stroke-width="1.2" '
            f'class="nm-track" style="animation-duration:{6 + ri * 3}s"/>'
        )
        for k, name in enumerate(names):
            phase = (0, 0.5, 0.25)[ri]  # keep the three rings from lining up at the front
            begin = f"-{dur * (k + phase) / len(names):.2f}s"
            s = size / 256
            bodies.append(
                f'<g><g transform="translate({-size / 2} {-size / 2}) scale({s:.5f})">{icon_inner(name)}</g>'
                f'<animateMotion dur="{dur}s" begin="{begin}" repeatCount="indefinite" path="{path}"/>'
                f'<animateTransform attributeName="transform" type="scale" values="1;.62;1" keyTimes="0;.5;1" dur="{dur}s" begin="{begin}" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="1;.5;1" keyTimes="0;.5;1" dur="{dur}s" begin="{begin}" repeatCount="indefinite"/></g>'
            )
    # Nam and Claude at the hub: the desk box spans x -240..470, y 160..456 with Nam's desk at NAM_DX
    ds = 0.36
    tx, ty = CX - 115 * ds, CY - 308 * ds
    light = w["light"]["work"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" class="st-responding" role="img" aria-labelledby="t">
<title id="t">Void Drift, universe {w["index"]} of {w["total"]}: Nam and Claude float at their desks while the toolbox orbits them. Kotlin, Java, Android Studio, Gradle, Flutter, Dart; Rust, Python, TypeScript, JavaScript, C++, React, Node.js, Next.js, Tailwind; Firebase, PostgreSQL, MySQL, MongoDB, Docker, Linux, Git, GitHub, IntelliJ IDEA, VS Code.</title>
<style>{MV["common"]}{MV["rig"]}{pin}{NAM_CSS}{w["style"]}
.nm-track{{stroke-dasharray:3 7;animation:nm-dash 6s linear infinite}}@keyframes nm-dash{{to{{stroke-dashoffset:-100}}}}
.nm-pulse{{transform-box:fill-box;transform-origin:center;animation:nm-pulse 3s ease-in-out infinite}}
@keyframes nm-pulse{{0%,100%{{transform:scale(.85);opacity:.55}}50%{{transform:scale(1.1);opacity:1}}}}
</style>
<defs>
<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<linearGradient id="trk" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{PINK}" stop-opacity=".85"/><stop offset=".5" stop-color="{PURPLE}" stop-opacity=".55"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".85"/></linearGradient>
<radialGradient id="core"><stop offset="0" stop-color="{PINK}" stop-opacity=".45"/><stop offset=".5" stop-color="{PURPLE}" stop-opacity=".2"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>
</defs>
<g clip-path="url(#card)">
<svg width="{W}" height="{H}" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice">{w["scenery"]}</svg>
<rect width="{W}" height="{H}" fill="#05040c" fill-opacity=".42"/>
{"".join(tracks)}
<ellipse cx="{CX}" cy="{CY + 8}" rx="130" ry="70" fill="url(#core)" class="nm-pulse"/>
<g transform="translate({tx:.1f} {ty:.1f}) scale({ds})">{desk_pair(w, "o", "helmet", nook=False)}</g>
{"".join(bodies)}
<text x="18" y="26" style="font:700 11px {SANS};letter-spacing:3px" fill="{light}">UNIVERSE {w["index"]:03d}/{w["total"]} · {esc(w["name"].upper())}</text>
<text x="{CX}" y="{H - 14}" text-anchor="middle" style="font:12px {MONO};fill:#c9bdf2">everything orbits the desk · nam.role = "{esc(w["role"].lower())}"</text>
</g>
</svg>
'''


write("hero.svg", hero())
write("code.svg", about())
write("orbit.svg", orbit())
write("footer.svg", footer())
