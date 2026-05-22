import sys, pathlib, json, tempfile, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from launcher.docs import check_readme_drift, render_example_inventory

REPO_ROOT = pathlib.Path(__file__).resolve().parent
with open(REPO_ROOT / 'examples_manifest.json') as f:
    raw = json.load(f)
manifest = {k: v for k, v in raw.items() if not k.startswith('_')}
with open(REPO_ROOT / 'launch_schema.json') as f:
    raw = json.load(f)
schema = {k: v for k, v in raw.items() if not k.startswith('_')}

readme = (REPO_ROOT / 'README.md').read_text()
inv = render_example_inventory(manifest)
drifted = readme.replace(inv, inv.replace('Dash 简单直方图', 'Dash 被改了'))

tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
tmp.write(drifted)
tmp.close()
tmp_path = pathlib.Path(tmp.name)

drift = check_readme_drift(tmp_path, manifest, schema)
os.unlink(tmp.name)
print('Drift warnings:', len(drift))
for w in drift:
    print(' ', w)
