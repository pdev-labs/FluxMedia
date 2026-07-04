import base64
import gzip
import io
import sys
import re

def decode_resource(data_b64: str) -> str:
    try:
        compressed = base64.b64decode(data_b64)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode='rb') as f:
            return f.read().decode('utf-8')
    except Exception as e:
        return ''

with open(r'd:\Dev\fluxmedia\fluxmedia\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

html_match = re.search(r'PORTAL_HTML_COMPRESSED = \"(.*?)\"', content)
css_match = re.search(r'PORTAL_CSS_COMPRESSED = \"(.*?)\"', content)
js_match = re.search(r'PORTAL_JS_COMPRESSED = \"(.*?)\"', content)

if html_match: open(r'd:\Dev\fluxmedia\index.html', 'w', encoding='utf-8').write(decode_resource(html_match.group(1)))
if css_match: open(r'd:\Dev\fluxmedia\style.css', 'w', encoding='utf-8').write(decode_resource(css_match.group(1)))
if js_match: open(r'd:\Dev\fluxmedia\app.js', 'w', encoding='utf-8').write(decode_resource(js_match.group(1)))

print('Extracted to index.html, style.css, app.js')
