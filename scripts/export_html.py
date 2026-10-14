"""Export the project page as a single HTML file, including images and fonts."""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
LICENSES = {
    "Open Sans": "https://raw.githubusercontent.com/google/fonts/main/ofl/opensans/OFL.txt",
    "Roboto": "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/OFL.txt",
    "Ubuntu": "https://raw.githubusercontent.com/google/fonts/main/ufl/ubuntu/UFL.txt",
    "Varela Round": "https://raw.githubusercontent.com/google/fonts/main/ofl/varelaround/OFL.txt",
}


def download(url):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=25) as response:
        return response.read()


def data_uri(data, mime):
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def embed_fonts(css, characters):
    match = re.search(r'@import\s+url\("([^\"]+)"\);', css)
    if not match:
        raise ValueError("Expected the site's Google Fonts import")
    # Preserve the current typography while bundling only the needed glyphs.
    font_css = download(match.group(1) + "&text=" + quote(characters, safe="")).decode()
    font_urls = sorted(set(re.findall(r"url\((https://[^)]+)\)", font_css)))
    urls = font_urls + list(LICENSES.values())
    with ThreadPoolExecutor(max_workers=8) as pool:
        files = dict(zip(urls, pool.map(download, urls)))
    for url in font_urls:
        font_css = font_css.replace(url, data_uri(files[url], "font/woff2"))
    licenses = "\n\n".join(
        f"{name}\n{files[url].decode('utf-8')}" for name, url in LICENSES.items()
    )
    css = css[:match.start()] + font_css + css[match.end():]
    return css, licenses, len(font_urls)


class ResourceAudit(HTMLParser):
    """Ensure the exported document has no local or remote loading dependencies."""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "src" in attrs:
            assert attrs["src"].startswith("data:"), (tag, attrs["src"])
        if tag == "link" and "href" in attrs:
            assert attrs["href"].startswith("data:"), attrs["href"]
        if tag == "a" and "href" in attrs:
            href = attrs["href"]
            assert href.startswith("#") or urlparse(href).scheme, href


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "Faster-WAM-share.html")
    args = parser.parse_args()
    page = (ROOT / "index.html").read_text()
    css = (ROOT / "styles.css").read_text()
    script = (ROOT / "script.js").read_text()
    characters = "".join(sorted({c for c in page + script if ord(c) >= 32}))
    css, licenses, font_count = embed_fonts(css, characters)

    embedded = {}

    def asset(path):
        if path not in embedded:
            file = (ROOT / path).resolve()
            if not file.is_relative_to(ROOT):
                raise ValueError(f"Asset outside the project: {path}")
            mime = mimetypes.guess_type(file)[0] or "application/octet-stream"
            embedded[path] = data_uri(file.read_bytes(), mime)
        return embedded[path]

    # All recorded frames must be present, including those selected later by JS.
    frames = {
        path.relative_to(ROOT).as_posix(): asset(path.relative_to(ROOT).as_posix())
        for path in sorted((ROOT / "assets/rollouts").rglob("*.webp"))
    }

    def replace_reference(match):
        attribute, path = match.groups()
        embedded_value = asset(path)
        if attribute == "href" and path.endswith("method.svg"):
            return f'href="{embedded_value}" data-embedded-image="true"'
        return f'{attribute}="{embedded_value}"'

    page = re.sub(r'(src|href)="(assets/[^\"]+)"', replace_reference, page)
    page, count = re.subn(
        r'<link\s+rel="stylesheet"\s+href="styles.css"\s*/?>',
        lambda _: "<style>\n" + css + "\n</style>", page,
    )
    assert count == 1
    page, count = re.subn(r'<script\s+src="script.js"\s+defer></script>', '', page)
    assert count == 1
    # A local review copy does not claim a deployed URL or remote social image.
    page = re.sub(
        r'<meta\s+(?:property="og:(?:image|url)"|name="twitter:card")[^>]*>',
        '', page, flags=re.S,
    )
    script, count = re.subn(
        r'img\.src\s*=\s*(`assets/rollouts/[^;]+`);',
        r'img.src = embeddedFrames[\1];', script,
    )
    assert count == 1, "Update the exporter to match the rollout image assignment"
    script = '"use strict";\nconst embeddedFrames = ' + json.dumps(frames, separators=(',', ':')) + ";\n" + script
    # Browsers block top-level data-URL navigation. Blob links retain full-size
    # figure viewing when this HTML is opened directly from the filesystem.
    script += '''
document.querySelectorAll('a[data-embedded-image]').forEach(link => {
  const [header, encoded] = link.getAttribute('href').split(',');
  const type = header.slice(5).split(';')[0];
  const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
  link.href = URL.createObjectURL(new Blob([bytes], { type }));
});
'''
    script = script.replace("</script", "<\\/script")
    # This also makes missing dependencies visible during offline verification.
    policy = (
        "default-src 'none'; img-src data: blob:; font-src data:; "
        "style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
        "base-uri 'none'; form-action 'none'"
    )
    page = page.replace('<meta charset="utf-8" />',
        '<meta charset="utf-8" />\n<meta http-equiv="Content-Security-Policy" content="' + policy + '">', 1)
    comment = "<!-- Standalone review copy. Images, styles, scripts, and fonts are embedded. -->\n"
    page = page.replace('<body>', '<body>\n' + comment, 1)
    license_block = '<!--\nEmbedded font licenses:\n' + licenses.replace('--', '—') + '\n-->\n'
    page = page.replace('</body>', license_block + '<script>\n' + script + '\n</script>\n</body>', 1)
    page = '\n'.join(line.rstrip() for line in page.splitlines()) + '\n'
    ResourceAudit().feed(page)
    assert not re.search(r'@import\b|url\([\"\']?https?://', css)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page)
    print(f"Exported {args.output.name}: {args.output.stat().st_size / 1024 / 1024:.2f} MiB")
    print(f"Embedded {len(frames)} rollout images, paper figures, favicon, and {font_count} font files.")
    print("Resource audit passed: no external files are needed to render the page.")


if __name__ == "__main__":
    main()
