"""Exact LNGS artwork, baseline route and supplied shielding geometry in portrait."""
import importlib.util
import numpy as np
from manim import *
from scenes.vertical.common import PortraitScene,text,ROOT
from cygno_anim.config import load_science
from cygno_anim.visuals import BACKGROUND,FOREGROUND,MUTED,CYGNUS,PHOTON

# Geometry is reused without running or altering horizontal choreography.
spec=importlib.util.spec_from_file_location('horizontal_site_geometry',ROOT/'scenes/05_lngs_positioning.py')
site=importlib.util.module_from_spec(spec);spec.loader.exec_module(site)
ROUTE=(
    ([(982,1104),(982,1060),(982,1023),(979,1006),(973,995),(959,985),(837,928)],4.4),
    ([(837,928),(777,900),(716,871),(679,852)],3.1),
    ([(679,852),(703,841),(731,825),(714,816),(676,801)],3.0))

class VerticalLNGS(PortraitScene):
    scene_id='05_lngs_positioning'
    dimension_line=site.LNGSPositioning.dimension_line
    mass_badge=site.LNGSPositioning.mass_badge

    def enter_gran_sasso(self):
        layers,road,lab,_=site.LNGSPositioning.mountain_context(self)
        geometry=VGroup(layers,road,lab).set_width(6.25).move_to([-.25,1.5,0])
        self.state.update(mountain=geometry,layers=layers,road=road,lab=lab)
        # Layers are drawn progressively in the section, as in the baseline.

    def gran_sasso(self):
        s=self.state
        self.play(LaggedStart(*[Create(layer) for layer in s['layers']],lag_ratio=.16),run_time=2.2)
        self.play(Create(s['road']),run_time=1.6)
        labels=VGroup(text('GRAN SASSO',size=.33,weight='BOLD').move_to([-.25,3.55,0]),
            text('A24 motorway tunnel',size=.30,color=MUTED).move_to([-.25,-.45,0]))
        self.play(FadeIn(labels),FadeIn(s['lab']),run_time=.8)
        name=text('LNGS underground laboratory',size=.32,color=CYGNUS).move_to([-.25,-1.50,0])
        leader=VMobject(color=CYGNUS,stroke_width=1.5).set_points_as_corners([name.get_right()+[.1,.15,0],[2.6,-.2,0],s['lab'].get_center()])
        self.play(FadeIn(name),Create(leader),Indicate(s['lab'],color=CYGNUS),run_time=1.1)
        geometry=s['mountain']
        self.play(geometry.animate.scale(1.25,about_point=s['lab'].get_center()),run_time=1.5)
        self.audit('mountain and laboratory')

    def enter_hall_f(self):
        illustration=ImageMobject(str(ROOT/'assets/LNGS/View_exp_underground_2.png')).set_width(6.25).move_to([-.25,.85,0])
        self.state['map']=illustration;self.add(illustration)

    def pixel(self,x,y):
        image=self.state['map']
        return image.get_center()+[(x/1151-.5)*image.width,(.5-y/1160)*image.height,0]

    def hall_f(self):
        if 'map' not in self.state:
            self.clear_content();self.enter_hall_f()
            self.note('The underground halls share an access gallery.')
        illustration=self.state['map']
        self.wait(1.3)
        # Enlarge the exact image around the baseline access route. Fixed masks
        # keep the image in the central panel while the artwork pans underneath.
        masks=VGroup(Rectangle(width=9,height=4.05,stroke_width=0,fill_color=BACKGROUND,fill_opacity=1).move_to([0,6.075,0]),
            Rectangle(width=9,height=5.60,stroke_width=0,fill_color=BACKGROUND,fill_opacity=1).move_to([0,-5.20,0]),
            Rectangle(width=1,height=6.45,stroke_width=0,fill_color=BACKGROUND,fill_opacity=1).move_to([-4, .825,0]),
            Rectangle(width=1.5,height=6.45,stroke_width=0,fill_color=BACKGROUND,fill_opacity=1).move_to([3.75,.825,0]))
        masks.set_z_index(8)
        for item in self.chrome:item.set_z_index(30)
        self.add(masks)
        enlarged=illustration.copy().set_width(13.8)
        focus=np.array([770/1151-.5,.5-930/1160,0])
        enlarged.move_to(np.array([-.25,.7,0])-focus*[enlarged.width,enlarged.height,1])
        self.play(Transform(illustration,enlarged),run_time=2.2)
        labels=VGroup()
        for title,anchor,centre in [('Hall A',(519,811),(-2.5,3.6)),('Hall B',(841,788),(.9,3.6))]:
            name=text(title,size=.30).move_to([*centre,0]).set_z_index(12)
            name.add_background_rectangle(color=BACKGROUND,opacity=.9,buff=.08)
            labels.add(Line(name.get_bottom(),self.pixel(*anchor),color=FOREGROUND,stroke_width=1),name)
        labels.set_z_index(12);self.play(FadeIn(labels),run_time=.6)
        marker=VGroup(Dot(radius=.10,color=BACKGROUND),Dot(radius=.055,color=CYGNUS,stroke_color=FOREGROUND,stroke_width=1))
        marker.move_to(self.pixel(*ROUTE[0][0][0])).set_z_index(15)
        self.play(FadeIn(marker),run_time=.4)
        self.note('Enter from the lower right and follow the access gallery.')
        for index,(points,duration) in enumerate(ROUTE):
            path=VMobject().set_points_as_corners([self.pixel(*p) for p in points])
            self.play(MoveAlongPath(marker,path,rate_func=linear),run_time=duration)
            self.audit(f'route waypoint {index+1}')
        self.play(FadeOut(labels),run_time=.4)
        name=text('HallF - CYGNO04',size=.34,color=CYGNUS,weight='BOLD').move_to([-.25,3.55,0]).set_z_index(15)
        name.add_background_rectangle(color=BACKGROUND,opacity=.95,buff=.12)
        destination=self.pixel(676,801)
        ring=Circle(radius=.16,color=CYGNUS,stroke_width=2).move_to(destination)
        leader=DashedLine(name.get_bottom(),destination+UP*.18,color=CYGNUS,stroke_width=1.5)
        self.play(FadeIn(name),Create(ring),Create(leader),run_time=.7)
        self.play(Indicate(ring,scale_factor=1.3),run_time=.8)
        self.audit('Hall F narrow connector')

    def enter_assembly(self):
        base,stages=site.LNGSPositioning.shielding_assembly(self,load_science(require_local=True)['shielding'])
        shapes=[s[0] for s in stages]
        # Replace the original small detector text with a phone-size caption;
        # camera and PMT geometry stays part of the detector insertion group.
        shapes[3].remove(shapes[3][1])
        geometry=VGroup(*shapes).set_width(6.15).move_to([-.25,-.6,0])
        floor=Line([-3.4,geometry.get_bottom()[1]-.08,0],[2.9,geometry.get_bottom()[1]-.08,0],color=MUTED)
        self.state.update(assembly=geometry,stages=shapes,floor=floor)
        self.add(floor)

    def assembly(self):
        self.clear_content()
        if 'assembly' not in self.state:self.enter_assembly()
        else:self.add(self.state['floor'])
        science=load_science(require_local=True)['shielding'];dims=science['dimensions']
        masses=science['component_masses_tonnes']
        names=['Containment pool','Polyethylene base','Copper shielding','Detector + readout','Water shielding']
        sizes=[dims['safety_pool_footprint_mm'],dims['polyethylene_base_overall_mm'],dims['copper_shield_outer_mm'],
            dims['detector_outer_envelope_mm'],dims['outer_envelope_mm']]
        mass=[None,masses['polyethylene'],masses['copper'],None,science['water']['derived_mass_tonnes_approx']]
        for index,(shape,name,size,mass_value) in enumerate(zip(self.state['stages'],names,sizes,mass)):
            shape.save_state()
            shape.scale(min(5.4/max(shape.width,.01),2.1/max(shape.height,.01))).move_to([-.25,3.2,0])
            label=text(name,size=.34,color=CYGNUS,weight='BOLD').move_to([-.25,4.9,0])
            dimensions=(' × '.join(f'{v/1000:g}' for v in size)+' m') if isinstance(size,(list,tuple)) and all(isinstance(v,(int,float)) for v in size) else 'qCMOS cameras + PMTs'
            detail=dimensions+((f' · ≈{mass_value:g} t' if index==4 else f' · {mass_value:g} t') if mass_value is not None else '')
            annotation=text(detail,size=.30,color=MUTED).move_to([-.25,1.75,0])
            self.play(FadeIn(shape,shift=UP*.12),FadeIn(label),FadeIn(annotation),run_time=.7)
            self.wait(.7)
            self.audit(f'component preview: {name}')
            self.play(Restore(shape),run_time=1.3)
            self.wait(.5)
            self.play(FadeOut(label),FadeOut(annotation),run_time=.4)
            if index==3:
                sensors=text('Readout: qCMOS cameras + PMTs',size=.30,color=PHOTON).move_to([-.25,-3.2,0])
                self.play(FadeIn(sensors),run_time=.5)
                self.audit('component insertion with original sensor sketches')
        self.audit('restored component-by-component assembly')
