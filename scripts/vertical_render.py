"""Isolated Manim process with an explicit portrait logical canvas."""
from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from manim import tempconfig
from scripts.vertical import load_catalog,PROFILES

def main():
    sid,media_dir,profile_name,name=sys.argv[1:]
    scene=next(s for s in load_catalog()['scenes'] if s['id']==sid)
    profile=next(p for p in PROFILES if p.name==profile_name)
    with tempconfig({'pixel_width':profile.width,'pixel_height':profile.height,'frame_width':9,'frame_height':16,
        'frame_rate':30,'renderer':'cairo','format':'mp4','media_dir':media_dir,'output_file':name,
        'disable_caching':True,'progress_bar':'none','verbosity':'WARNING'}):
        spec=importlib.util.spec_from_file_location('portrait_entry',ROOT/scene['file'])
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        getattr(module,scene['class_name'])().render()
if __name__=='__main__':main()
