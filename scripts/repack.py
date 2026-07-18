import base64
import gzip
import io
import re
import sys
import os

def encode_resource(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = f.read().encode('utf-8')
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb') as f:
        f.write(data)
    return base64.b64encode(out.getvalue()).decode('utf-8')

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(base_dir)
html_enc = encode_resource(os.path.join(project_root, 'index.html'))
css_enc = encode_resource(os.path.join(project_root, 'style.css'))
js_enc = encode_resource(os.path.join(project_root, 'app.js'))

main_py_path = os.path.join(project_root, 'src', 'fluxmedia', 'main.py')
with open(main_py_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'PORTAL_HTML_COMPRESSED = ".*?"', f'PORTAL_HTML_COMPRESSED = "{html_enc}"', content, count=1)
content = re.sub(r'PORTAL_CSS_COMPRESSED = ".*?"', f'PORTAL_CSS_COMPRESSED = "{css_enc}"', content, count=1)
content = re.sub(r'PORTAL_JS_COMPRESSED = ".*?"', f'PORTAL_JS_COMPRESSED = "{js_enc}"', content, count=1)

with open(main_py_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Repacked successfully!")
