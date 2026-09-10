"""Content-based horizontal provenance, independent of portrait additions."""
from pathlib import Path
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[1]
RECORDS=ROOT/'media/manifests/horizontal'

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def inputs(scene):
    from cygno_anim.config import load_branding
    brand=load_branding()
    paths=[ROOT/scene['file'],*sorted((ROOT/'cygno_anim').glob('*.py')),
        *[ROOT/'config'/name for name in ['branding.yaml','science.yaml','scenes.yaml']],ROOT/'requirements.txt',
        *[ROOT/brand[name] for name in ['logo_path','website_qr_path','instagram_qr_path']]]
    if scene['requires_local_science']:
        paths.extend([Path(os.environ.get('CYGNO_LOCAL_CONFIG',str(ROOT/'config/local.yaml'))).resolve(),ROOT/'assets/LNGS/View_exp_underground_2.png'])
    return {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):digest(p) for p in paths}

def record(scene,video_root):
    from scripts.render import _expected_outputs
    value={'inputs':inputs(scene),'outputs':{str(p.relative_to(video_root)):digest(p) for p in _expected_outputs(video_root=video_root,scenes=[scene])}}
    RECORDS.mkdir(parents=True,exist_ok=True)
    path=RECORDS/(scene['id']+'.json');temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2));os.replace(temporary,path)

def verify(scene,video_root):
    """Return False only when no provenance exists; stale records always fail."""
    from scripts.render import _expected_outputs
    path=RECORDS/(scene['id']+'.json');baseline=False
    if not path.is_file():path=RECORDS/'baseline.json';baseline=True
    if not path.is_file():return False
    value=json.loads(path.read_text());current=inputs(scene)
    if any(value['inputs'].get(p)!=h for p,h in current.items()):raise RuntimeError(f"{scene['id']}: horizontal source fingerprint changed")
    for p in _expected_outputs(video_root=video_root,scenes=[scene]):
        key=str(p.relative_to(video_root))
        if baseline:key='media/videos/'+key
        if value['outputs'].get(key)!=digest(p):raise RuntimeError(f'{p}: horizontal output fingerprint changed')
    return True
