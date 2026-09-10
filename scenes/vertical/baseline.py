"""Reuse original horizontal drawing primitives without changing their scenes."""
from functools import lru_cache
import importlib.util
import ast
from pathlib import Path
from cygno_anim.config import load_science
ROOT=Path(__file__).resolve().parents[2]

@lru_cache(None)
def original(scene_id):
    path=ROOT/'scenes'/f'{scene_id}.py'
    spec=importlib.util.spec_from_file_location('baseline_'+scene_id,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def detector_factory():
    factory=original('04_cygno04_full_track').CYGNO04FullTrack()
    factory.science=load_science(include_local=False)
    return factory

@lru_cache(None)
def recoil_reference():
    """Read the baseline's illustrative track samples without altering its scene.

    These literals are local to WIMPRecoil.construct, rather than an exported
    builder. Fail explicitly if that source contract changes.
    """
    wanted={'distances','wiggles','deposit_distances','gas_offsets','fan_angles'}
    tree=ast.parse((ROOT/'scenes/02_wimp_recoil.py').read_text())
    result={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in wanted:
                value=node.value.args[0] if isinstance(node.value,ast.Call) else node.value
                result[name]=ast.literal_eval(value)
    if set(result)!=wanted:raise ValueError('Baseline recoil geometry contract changed')
    return result
