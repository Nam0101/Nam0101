#!/usr/bin/env python3
"""Screenshot an SVG at fixed animation times via headless Chrome.

usage: python3 -I shoot.py <svg> <out_prefix> <width> <height> <t1> [t2 ...]
"""
import pathlib
import subprocess
import sys

CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
svg, prefix, w, h = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
body = svg.read_text()
work = pathlib.Path(prefix).parent
for t in sys.argv[5:]:
    page = work / f"_h_{svg.stem}_{t}.html"
    page.write_text(
        f"""<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:#0d1117">{body}
<script>
const T = {float(t)};
document.getAnimations().forEach(a => {{ a.pause(); a.currentTime = T * 1000; }});
document.querySelectorAll('svg').forEach(s => {{ s.pauseAnimations(); s.setCurrentTime(T); }});
</script></body></html>""",
        encoding="utf-8",
    )
    out = f"{prefix}-{t}.png"
    subprocess.run(
        [CH, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={work / 'chrome-prof'}",
         f"--window-size={w},{h}", "--virtual-time-budget=1500", f"--screenshot={out}", page.as_uri()],
        capture_output=True, check=False, timeout=60,
    )
    page.unlink()
    print(out)
