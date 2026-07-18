import base64
import gzip
import io
import sys
import re
import os

def decode_resource(data_b64: str) -> str:
    try:
        compressed = base64.b64decode(data_b64)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode='rb') as f:
            return f.read().decode('utf-8')
    except Exception as e:
        return ''

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(base_dir)
main_py_path = os.path.join(project_root, 'src', 'fluxmedia', 'main.py')

with open(main_py_path, 'r', encoding='utf-8') as f:
    content = f.read()

html_match = re.search(r'PORTAL_HTML_COMPRESSED = \"(.*?)\"', content)
css_match = re.search(r'PORTAL_CSS_COMPRESSED = \"(.*?)\"', content)
js_match = re.search(r'PORTAL_JS_COMPRESSED = \"(.*?)\"', content)

if html_match: open(os.path.join(project_root, 'index.html'), 'w', encoding='utf-8').write(decode_resource(html_match.group(1)))
if css_match: open(os.path.join(project_root, 'style.css'), 'w', encoding='utf-8').write(decode_resource(css_match.group(1)))
if js_match: open(os.path.join(project_root, 'app.js'), 'w', encoding='utf-8').write(decode_resource(js_match.group(1)))

print('Extracted to index.html, style.css, app.js')
