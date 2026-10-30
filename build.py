#!/usr/bin/env python3
"""Сборка «Кино на двоих».

  python3 build.py             → index.html + manifest.webmanifest + sw.js (PWA, например для GitHub Pages)
  python3 build.py --artifact  → dist/artifact.html (страница для публикации как артефакт в Claude)

Необязательно:
  posters/<id>.jpg   — постеры (id = позиция фильма в src/films.js). Подхватываются автоматически.
  avatars/a.jpg, avatars/b.jpg — фото пары (кого видит владелец и кого видит второй человек).
Нужен Pillow только если есть аватарки: pip install pillow
"""
import base64, glob, io, json, os, re, sys

D = os.path.dirname(os.path.abspath(__file__))
read = lambda *p: open(os.path.join(D, *p), encoding="utf-8").read()

def avatar(key, letter, color):
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(D, "avatars", f"{key}.{ext}")
        if os.path.exists(p):
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
            s = min(im.size); l = (im.width - s) // 2; t = (im.height - s) // 2
            im = im.crop((l, t, l + s, t + s)).resize((192, 192))
            b = io.BytesIO(); im.save(b, "JPEG", quality=82)
            return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect width="96" height="96" fill="{color}"/>'
           f'<text x="48" y="62" font-family="Arial" font-size="44" font-weight="700" fill="#fff" text-anchor="middle">{letter}</text></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

ids = sorted({str(int(m.group(1))) for p in glob.glob(os.path.join(D, "posters", "*"))
              if (m := re.match(r"(\d+)\.jpe?g$", os.path.basename(p), re.I))}, key=int)

page = read("src", "template.html")
page = page.replace("__AVA_A__", avatar("a", "П", "#A8234A")).replace("__AVA_B__", avatar("b", "П", "#6B4FA8"))
page = page.replace("/*__FILMS__*/", read("src", "films.js") + "\n" + read("src", "cast.js") +
                    "\nconst POSTER_IDS=" + json.dumps(ids) + ";")

if "--artifact" in sys.argv:
    os.makedirs(os.path.join(D, "dist"), exist_ok=True)
    out = os.path.join(D, "dist", "artifact.html")
    html = page
else:
    out = os.path.join(D, "index.html")
    head = ('<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="theme-color" content="#F3F0F6" media="(prefers-color-scheme: light)">'
            '<meta name="theme-color" content="#141118" media="(prefers-color-scheme: dark)">'
            '<meta name="apple-mobile-web-app-capable" content="yes">'
            '<meta name="mobile-web-app-capable" content="yes">'
            '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
            '<meta name="apple-mobile-web-app-title" content="Кино">'
            '<meta name="description" content="Тиндер для фильмов на двоих: свайпайте фильмы с IMDb 7+ и находите общие.">'
            '<link rel="manifest" href="manifest.webmanifest">'
            '<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">'
            '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">'
            '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
            'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>')
    sw_reg = ('<script>if("serviceWorker" in navigator&&location.protocol!=="file:")'
              'addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));</script>')
    html = ('<!doctype html>\n<html lang="ru"><head>' + head + '</head><body>\n'
            + page + "\n" + sw_reg + "\n</body></html>\n")
    # PWA: манифест и service worker
    import hashlib
    version = hashlib.sha1((html + ",".join(ids)).encode()).hexdigest()[:10]
    manifest = {
        "name": "Кино на двоих", "short_name": "Кино", "lang": "ru",
        "description": "Тиндер для фильмов на двоих: свайпайте фильмы с IMDb 7+ и находите общие.",
        "start_url": "./", "scope": "./", "id": "./",
        "display": "standalone", "orientation": "portrait",
        "background_color": "#141118", "theme_color": "#141118",
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    open(os.path.join(D, "manifest.webmanifest"), "w", encoding="utf-8").write(json.dumps(manifest, ensure_ascii=False, indent=2))
    sw = read("src", "sw.js").replace("__VERSION__", version)
    open(os.path.join(D, "sw.js"), "w", encoding="utf-8").write(sw)
open(out, "w", encoding="utf-8").write(html)
print(f"{os.path.relpath(out, D)}: {len(html)//1024} KB, постеров: {len(ids)}")
