"""Catalog-driven portrait rendering, verification and isolated delivery installs."""
from __future__ import annotations
import hashlib,json,os,sys,tempfile
from pathlib import Path
import yaml
from scripts.render import Profile,ROOT,MEDIA_ROOT,_run,_tool,_ffmpeg_wrapper,_locate_render,_faststart,verify_mp4,_probe,_remove_tree,_replace_directory

POSTING=Profile('1080x1920p30',1080,1920,30,18)
PREVIEW=Profile('360x640p30',360,640,30,18)
PROFILES=(PREVIEW,POSTING)

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load_catalog():
    data=yaml.safe_load((ROOT/'config/vertical.yaml').read_text())
    if data.get('schema_version')!=1:raise ValueError('Unsupported vertical catalog version')
    ids=set();sections=set()
    for scene in data['scenes']:
        if scene['id'] in ids:raise ValueError('Duplicate vertical scene ID')
        ids.add(scene['id'])
        for section in scene['sections']:
            if section['id'] in sections:raise ValueError('Duplicate Story ID')
            sections.add(section['id'])
            if not 15<=section['story_seconds']<=30:raise ValueError('Story must be 15–30 seconds')
            for field in ['entry','method','title','context','takeaway']:
                if not section.get(field):raise ValueError(f'Missing {field}')
    return data

def targets(action='all',identifier=None):
    result=[]
    for scene in load_catalog()['scenes']:
        if action in ('all','scene') and (identifier is None or identifier==scene['id']):result.append((scene,None))
        for section in scene['sections']:
            if action in ('all','stories') and (identifier in (None,'all',scene['id'])) or action=='story' and identifier==section['id']:
                result.append((scene,section))
    if not result:raise ValueError(f'Unknown portrait selection: {action} {identifier}')
    return result

def target_root(scene,section):
    return MEDIA_ROOT/'stories'/scene['id']/section['id'] if section else MEDIA_ROOT/'vertical'/scene['id']

def record_path(scene,section):
    return MEDIA_ROOT/'manifests'/('stories' if section else 'vertical')/f"{section['id'] if section else scene['id']}.json"

def dependencies(scene):
    paths=[ROOT/scene['file'],ROOT/'scenes/vertical/common.py',ROOT/'scenes/vertical/baseline.py',
        *[ROOT/'scenes'/f'{sid}.py' for sid in ['01_galactic_wind','02_wimp_recoil','04_cygno04_full_track']],ROOT/'scripts/vertical.py',ROOT/'scripts/vertical_render.py',ROOT/'scripts/render.py',
        ROOT/'config/vertical.yaml',ROOT/'config/branding.yaml',ROOT/'config/science.yaml',ROOT/'requirements.txt',
        *sorted((ROOT/'cygno_anim').glob('*.py'))]
    from cygno_anim.config import load_branding
    brand=load_branding()
    paths.extend(ROOT/brand[k] for k in ['logo_path','website_qr_path','instagram_qr_path'])
    if scene['requires_local_science']:
        paths.extend([Path(os.environ.get('CYGNO_LOCAL_CONFIG',str(ROOT/'config/local.yaml'))).resolve(),
            ROOT/'scenes/05_lngs_positioning.py',ROOT/'assets/LNGS/View_exp_underground_2.png'])
    return {str(p.resolve()):digest(p) for p in paths}

def output_name(scene,section):return section['id'] if section else scene['class_name']

def expected_paths(scene,section,root=None):
    base=root or target_root(scene,section)
    return [base/p.name/(output_name(scene,section)+'.mp4') for p in PROFILES]

def verify_outro(path,compact):
    import cv2,numpy as np
    from cygno_anim.config import load_branding
    from urllib.parse import urlsplit
    probe=_probe(path);duration=float(probe['format']['duration']);brand=load_branding()
    for offset in ((1.1,.25) if compact else (3.0,1.8,.3)):
        with tempfile.TemporaryDirectory(prefix='cygno-portrait-card-') as d:
            frame=Path(d)/'frame.png'
            _run([_tool('ffmpeg'),'-v','error','-y','-ss',str(duration-offset),'-i',str(path),'-frames:v','1','-threads','1',str(frame)])
            image=cv2.imread(str(frame));h,w=image.shape[:2]
            # Check logo fidelity in both closing styles.
            from cygno_anim.branding import load_branding_settings,_circular_logo_pixels
            logo=_circular_logo_pixels(load_branding_settings().logo_path)
            for is_logo in [True] if compact else [True,False]:
                if is_logo:
                    source=cv2.cvtColor(logo[:,:,:3],cv2.COLOR_RGB2BGR);display_height=(.65 if compact else .38)/16*h
                else:
                    source=cv2.imread(str(ROOT/brand['instagram_qr_path']));display_height=(320/120*2700/1880)/16*h
                best=-1
                for height in range(round(display_height)-2,round(display_height)+3):
                    if height<4:continue
                    scaled=cv2.resize(source,(round(height*source.shape[1]/source.shape[0]),height),interpolation=cv2.INTER_AREA)
                    sh,sw=scaled.shape[:2];template=scaled[int(sh*.18):int(sh*.82),int(sw*.18):int(sw*.82)]
                    best=max(best,float(cv2.matchTemplate(image,template,cv2.TM_CCOEFF_NORMED).max()))
                if best<.80:raise RuntimeError(f'{path}: missing closing artwork ({best:.3f})')
            if w==1080:
                centre=(8-(1.3 if compact else 2.65))/16*h
                region=image[round(centre-210):round(centre+210),int(w*.25):int(w*.75)]
                decoded,_,_=cv2.QRCodeDetector().detectAndDecode(region)
                if not decoded:
                    decoded,_,_=cv2.QRCodeDetector().detectAndDecode(cv2.resize(region,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC))
                key=lambda url:(urlsplit(url).scheme,urlsplit(url).netloc,urlsplit(url).path.rstrip('/'))
                if key(decoded)!=key(brand['website_url']):raise RuntimeError(f'{path}: website QR did not decode correctly')

def verify_target(scene,section,root=None,check_record=True):
    base=root or target_root(scene,section);paths=expected_paths(scene,section,base)
    actual=set(base.rglob('*.mp4'))
    if actual!=set(paths) or any(p.is_file() and p not in paths for p in base.rglob('*')):raise RuntimeError(f'{base}: output matrix mismatch')
    durations=[]
    for profile,path in zip(PROFILES,paths):
        duration=verify_mp4(path,profile);durations.append(duration)
        if section and not 15-1/30<=duration<=30+1/30:raise RuntimeError(f'{path}: Story duration out of bounds')
        expected_duration=section['story_seconds'] if section else 4.4+sum(s['full_seconds'] for s in scene['sections'])
        if abs(duration-expected_duration)>.25:raise RuntimeError(f'{path}: duration differs from catalog')
        verify_outro(path,bool(section))
    if abs(durations[0]-durations[1])>.05:raise RuntimeError('Portrait preview/posting timing mismatch')
    if check_record:
        record=json.loads(record_path(scene,section).read_text())
        if record['inputs']!=dependencies(scene):raise RuntimeError(f'{base}: stale portrait source dependencies')
        for path in paths:
            if digest(path)!=record['outputs'][str(path.relative_to(base))]:raise RuntimeError(f'{path}: differs from verified render')

def render_target(scene,section,profiles=PROFILES,install=True):
    if scene['requires_local_science']:
        from cygno_anim.config import load_science
        load_science(require_local=True)
    locked=dependencies(scene)
    work_parent=MEDIA_ROOT/'work'/'vertical';work_parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix=(section or scene)['id']+'-',dir=work_parent))
    out=work/'output';audits={}
    try:
        for profile in profiles:
            print(f"Rendering {(section or scene)['id']} {profile.name}",flush=True)
            rendered_dir=work/profile.name;rendered_dir.mkdir()
            env=os.environ.copy();env['CYGNO_VERTICAL_SECTION']=section['id'] if section else 'full'
            audit=rendered_dir/'layout.json';env['CYGNO_VERTICAL_AUDIT']=str(audit)
            wrapper,log=_ffmpeg_wrapper(rendered_dir,_tool('ffmpeg'),profile.crf)
            env['PATH']=str(rendered_dir)+os.pathsep+env.get('PATH','')
            _run([sys.executable,str(ROOT/'scripts/vertical_render.py'),scene['id'],str(rendered_dir),profile.name,output_name(scene,section)],env=env)
            if not log.is_file() or not log.read_text().strip():raise RuntimeError('Portrait CRF wrapper was not used')
            source=_locate_render(rendered_dir,output_name(scene,section))
            path=out/profile.name/(output_name(scene,section)+'.mp4');_faststart(source,path)
            verify_mp4(path,profile)
            audits[profile.name]=json.loads(audit.read_text())
        if not install:
            print('REVIEW OUTPUT:',out,flush=True)
            return out
        verify_target(scene,section,out,check_record=False)
        if dependencies(scene)!=locked:raise RuntimeError('Source changed during portrait render; retaining installed delivery')
        record={'inputs':locked,'outputs':{str(p.relative_to(out)):digest(p) for p in expected_paths(scene,section,out)},'audit':audits}
        dest=target_root(scene,section);family=MEDIA_ROOT/('stories' if section else 'vertical')
        _replace_directory(out,dest,within=family)
        path=record_path(scene,section);path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(record,indent=2));os.replace(temporary,path)
        print(f"VERIFIED AND INSTALLED: {(section or scene)['id']}",flush=True)
        return dest
    finally:
        if install:_remove_tree(work,within=work_parent)

def render_selection(action,identifier=None):
    for scene,section in targets(action,identifier):render_target(scene,section)

def verify_family(family):
    selected=[(s,c) for s,c in targets() if (family=='vertical')==(c is None)]
    expected=set()
    for scene,section in selected:
        expected.update(expected_paths(scene,section));verify_target(scene,section)
    root=MEDIA_ROOT/family
    actual={p for p in root.rglob('*') if p.is_file()}
    if actual!=expected:raise RuntimeError(f'{family}: missing or unexpected delivery files')
    print(f'All {len(expected)} {family} MP4 files passed verification.',flush=True)
