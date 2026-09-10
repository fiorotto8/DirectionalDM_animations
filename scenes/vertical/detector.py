"""One deterministic recoil through drift, light, acquisition and offline analysis."""
import numpy as np
from manim import *
from scenes.vertical.common import PortraitScene, text, panel
from scenes.vertical.baseline import detector_factory
from cygno_anim.config import load_science
from cygno_anim.detector import half_tpc, camera_icon, pmt_icon
from cygno_anim.events import simulate_nr_track, diffuse_track
from cygno_anim.visuals import (BACKGROUND, FOREGROUND, MUTED, CYGNUS, ELECTRON,
    FIELD, NUCLEUS, PHOTON, nucleus_marker)

class VerticalFullTrack(PortraitScene):
    scene_id='04_cygno04_full_track'

    def factory(self):
        if not hasattr(self,'_factory'):self._factory=detector_factory()
        return self._factory

    def chamber(self,add=True):
        d=self.factory().build_detector()
        chamber=VGroup(d.right_volume,d.right_cage,d.cathode,d.right_stack)
        cameras,pmts=d.right_cameras,d.right_pmts
        active=VGroup(chamber,cameras,pmts).set_width(6.10).move_to([-.25,1.65,0])
        labels=VGroup(text('One of two drift volumes',size=.30).move_to([-.25,4.05,0]),
            text('Cathode',size=.30).move_to([-2.1,-1.30,0]),
            text('Triple GEM',size=.30,color=PHOTON).move_to([.70,-1.30,0]),
            text('qCMOS + PMTs',size=.30,color=CYGNUS).move_to([-.25,-1.95,0]))
        self.state.update(chamber=chamber,cameras=cameras,pmts=pmts,chamber_labels=labels)
        if add:self.add(chamber,cameras,pmts,labels)
        return active,labels

    def primary(self,formed=False,drifted=False):
        sample=simulate_nr_track(seed=410)
        p=sample.points-sample.points.mean(axis=0)
        a=np.deg2rad(-24);p=p@np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]).T
        p=np.c_[p[:,0]*1.8-1.0,p[:,1]*1.8+1.2,np.zeros(len(p))]
        weights=sample.weights/sample.weights.max()
        rng=np.random.default_rng(411)
        gem_x=self.state['chamber'][3][0].get_x()
        end=np.array([[gem_x-.17+rng.uniform(-.055,.055),q[1]+rng.normal(0,.18),0] for q in p])
        electrons=VGroup(*[Dot(q,radius=.035+.017*w,color=ELECTRON) for q,w in zip(end if drifted else p,weights)])
        if not formed:electrons.set_opacity(0)
        trail=VMobject(color=NUCLEUS,stroke_width=2).set_points_as_corners(p)
        if drifted:trail.set_stroke(opacity=.2)
        self.state.update(points=p,weights=weights,electrons=electrons,ends=end,trail=trail)
        self.add(electrons)
        if formed:self.add(trail)

    def enter_recoil(self):
        d=self.factory().build_detector()
        d.remove(d.cathode_label,d.left_gem_label,d.right_gem_label)
        d.set_width(6.15).move_to([-.25,1.8,0])
        self.state['overview']=d
        self.add(d,text('Two back-to-back drift volumes',size=.30).move_to([-.25,4.25,0]))

    def recoil(self):
        d=self.state['overview']
        active=VGroup(d.right_volume,d.right_cage,d.cathode,d.right_stack,d.right_cameras,d.right_pmts)
        inactive=VGroup(d.left_volume,d.left_cage,d.left_stack,d.left_cameras,d.left_pmts)
        self.remove(d);self.add(active,inactive)
        self.wait(.6)
        self.clear_content(keep=[active,inactive])
        focused,labels=self.chamber(add=False)
        self.play(FadeOut(inactive),ReplacementTransform(active,focused),run_time=1.6)
        self.remove(focused);self.add(self.state['chamber'],self.state['cameras'],self.state['pmts'],labels)
        self.primary()
        self.state['nucleus']=nucleus_marker(.19).move_to(self.state['points'][0])
        self.add(self.state['nucleus'])
        s=self.state;p=s['points'];n=len(p);nucleus=s['nucleus']
        impact=Circle(radius=.24,color=NUCLEUS).move_to(p[0])
        self.play(Create(impact),Indicate(nucleus,color=NUCLEUS),run_time=.8)
        self.note('A struck gas nucleus starts the recoil here.')
        full=s['trail'].copy();s['trail'].pointwise_become_partial(full,0,0)
        self.add(s['trail'])
        group=VGroup(nucleus,s['trail'],s['electrons'])
        def form(_,alpha):
            t=alpha*(n-1);i=min(int(t),n-2);f=t-i
            nucleus.move_to(p[i]*(1-f)+p[i+1]*f)
            s['trail'].pointwise_become_partial(full,0,alpha)
            for j,d in enumerate(s['electrons']):d.set_opacity(float(np.clip(t-j+1,0,1)))
        self.play(UpdateFromAlphaFunc(group,form,rate_func=linear),run_time=3.2)
        self.remove(group);self.add(nucleus,s['trail'],s['electrons'])
        self.play(FadeOut(impact),FadeOut(nucleus),run_time=.5)
        self.note('The moving nucleus frees electrons from the gas.')
        self.audit('primary ionization')

    def enter_drift(self):self.chamber();self.primary(formed=True)
    def drift(self):
        s=self.state
        field=Arrow([.35,2.3,0],[-1.75,2.3,0],buff=0,color=FIELD,stroke_width=2.5)
        drift=Arrow([-1.75,.15,0],[.35,.15,0],buff=0,color=ELECTRON,stroke_width=2.5)
        labels=VGroup(text('E field',size=.30,color=FIELD).move_to([-.7,3.06,0]),
            text('Electron drift',size=.30,color=ELECTRON).move_to([-.7,-.78,0]))
        self.play(GrowArrow(field),GrowArrow(drift),FadeIn(labels),run_time=.9)
        self.note('Negative electrons drift opposite to the electric field.')
        rng=np.random.default_rng(404)
        self.play(*[MoveAlongPath(d,CubicBezier(d.get_center(),d.get_center()+[.5,rng.normal(0,.12),0],
            q+[-.35,rng.normal(0,.13),0],q)) for d,q in zip(s['electrons'],s['ends'])],
            s['trail'].animate.set_stroke(opacity=.2),run_time=3.8,rate_func=linear)
        envelope=Ellipse(width=.38,height=np.ptp(s['ends'][:,1])+.28,color=ELECTRON,stroke_width=1.5).move_to(s['electrons'])
        self.play(Create(envelope),run_time=.6)
        self.audit('drift arrival, fixed detector')
        self.wait(1.2)
        self.play(FadeOut(field),FadeOut(drift),FadeOut(labels),FadeOut(envelope),run_time=.6)

    def enter_gem(self):self.chamber();self.primary(formed=True,drifted=True)

    @staticmethod
    def avalanche_daughters(cloud,exit_x,rng):
        # Two representative daughters per marker, not a numerical GEM gain.
        # Keep each parent's symbol size and transverse position. Multiplication
        # branches locally rather than replacing the track with a central blob.
        daughters=VGroup();destinations=[]
        for parent in cloud:
            position=parent.get_center()
            spread=rng.uniform(.035,.065)
            for sign in (-1,1):
                daughters.add(parent.copy())
                destinations.append([exit_x+rng.uniform(-.025,.025),position[1]+sign*spread,0])
        return daughters,np.array(destinations)

    def audit_cloud(self,label,cloud):
        self.audit(label)
        self.checkpoints[-1]['electron_cloud']={
            'count':len(cloud),'minimum_radius':min(d.width/2 for d in cloud),
            'maximum_radius':max(d.width/2 for d in cloud),
            'vertical_span':float(np.ptp([d.get_y() for d in cloud]))}

    def gem(self):
        s=self.state;cloud=s['electrons'];rng=np.random.default_rng(405)
        centre_y=float(cloud.get_y())
        self.audit_cloud('GEM input cloud',cloud)
        # Foils remain exactly where they were throughout drift.
        for i,foil in enumerate(s['chamber'][3]):
            x=foil.get_x()
            self.play(cloud.animate.shift(RIGHT*(x-.07-cloud.get_x())),run_time=.5)
            next_cloud,destinations=self.avalanche_daughters(cloud,x+.07,rng)
            flash=VGroup(*[Line([x,centre_y,0],np.array([x,centre_y,0])+.35*np.array([np.cos(a),np.sin(a),0]),
                color=PHOTON,stroke_width=2) for a in np.linspace(0,2*np.pi,12,endpoint=False)])
            self.remove(cloud);self.add(next_cloud)
            self.play(*[d.animate.move_to(q) for d,q in zip(next_cloud,destinations)],
                FadeIn(flash),Indicate(foil,color=PHOTON,scale_factor=1.02),run_time=.8)
            self.play(FadeOut(flash),run_time=.3);cloud=next_cloud
            self.audit_cloud(f'GEM stage {i+1}',cloud)
        s['electrons']=cloud
        self.note('Three amplification stages produce charge and light.')
        rays=VGroup(*[Line(cloud.get_center(),q.get_center(),color=PHOTON,stroke_width=1.3,stroke_opacity=.6)
            for q in [*s['cameras'],*s['pmts']]])
        photons=VGroup(*[Dot(r.get_start(),radius=.035,color=PHOTON) for r in rays])
        self.play(Create(rays),run_time=.6);self.add(photons)
        self.play(*[MoveAlongPath(p,r) for p,r in zip(photons,rays)],run_time=1.1)
        self.play(FadeOut(photons),run_time=.3)
        self.audit('GEM light and sensors')

    def event(self):return diffuse_track(simulate_nr_track(seed=410),sigma=.060,seed=412)

    def signals(self):
        factory=self.factory()
        pixels=factory.build_projected_light_pattern(np.array([-.25,2.0,0]),width=5.65,height=1.6)
        grid=VGroup(*[Line([x,1.05,0],[x,2.95,0],color=CYGNUS,stroke_width=.4,stroke_opacity=.12) for x in np.linspace(-3.1,2.6,20)])
        camera=VGroup(panel(height=2.30,color=CYGNUS).move_to([-.25,2.0,0]),pixels,
            text('qCMOS: light on the GEM plane',size=.30,color=CYGNUS).move_to([-.25,3.50,0]),grid)
        axis=Line([-2.8,-1.45,0],[2.3,-1.45,0],color=MUTED,stroke_width=1)
        wave=factory.build_time_profile(np.array([-.25,-.95,0]),width=5.1,height=1.0)
        timing=VGroup(panel(height=1.75,color=PHOTON).move_to([-.25,-.95,0]),axis,wave,
            text('PMTs: light versus time',size=.30,color=PHOTON).move_to([-.25,.25,0]),
            text('Time →',size=.30,color=MUTED).move_to([-.25,-2.15,0]))
        self.state.update(camera_signal=camera,pixels=pixels,timing_signal=timing,wave=wave)
        return camera,timing

    def enter_readout(self):self.chamber();self.primary(formed=True,drifted=True)
    def readout(self):
        self.note('The same light is recorded in space and in time.')
        self.clear_content();camera,timing=self.signals()
        self.play(FadeIn(camera[0]),FadeIn(camera[2]),Create(camera[3]),run_time=.7)
        self.play(LaggedStart(*[FadeIn(p) for p in self.state['pixels']],lag_ratio=.002),run_time=2.0)
        self.play(FadeIn(timing[0]),Create(timing[1]),FadeIn(timing[3]),FadeIn(timing[4]),run_time=.7)
        self.play(Create(self.state['wave']),run_time=2.0)
        self.note('Diffusion spreads the image; PMTs record an irregular pulse.')
        self.audit('camera pixels and PMT waveform')

    def enter_daq_cloud(self):
        camera,timing=self.signals();self.add(camera,timing)

    def flow_node(self,title,detail,y,color):
        return VGroup(panel(height=1.13,color=color).move_to([-.25,y,0]),
            text(title,size=.33,color=color,weight='BOLD').move_to([-.25,y+.24,0]),
            text(detail,size=.30).move_to([-.25,y-.27,0]))

    def daq_cloud(self):
        self.clear_content();factory=self.factory()
        image_packet=factory.mini_image_packet(np.array([-1.7,4.2,0])).scale(1.2)
        wave_packet=factory.mini_wave_packet(np.array([1.2,4.2,0])).scale(1.2)
        source_labels=VGroup(text('qCMOS image',size=.30,color=CYGNUS).move_to([-1.7,4.95,0]),
            text('PMT timing',size=.30,color=PHOTON).move_to([1.2,4.95,0]))
        centre=np.array([-.25,2.35,0])
        ring=Circle(radius=.78,color=ELECTRON,stroke_width=2,fill_color=ELECTRON,fill_opacity=.06).move_to(centre)
        sweep=Arc(radius=.64,start_angle=.25,angle=5.4,color=CYGNUS,stroke_width=2.5).move_to(centre)
        trigger=text('Trigger + DAQ',size=.31,weight='BOLD').move_to(centre)
        cloud=factory.build_cloud_icon(np.array([-.25,-.05,0]),scale=1.25)
        cloud.remove(cloud[1],cloud[2])
        cloud.add(text('INFN Cloud',size=.33,color=CYGNUS,weight='BOLD').move_to([-.25,.05,0]))
        archive=VGroup(*[factory.event_packet(np.array([-.55+.30*i,-1.30-.10*i,0]),scale=.65) for i in range(3)])
        archive_label=text('Stored events',size=.30,color=CYGNUS).move_to([-.25,-2.10,0])
        offline=self.flow_node('Offline analysis','3D track + recoil type',-3.15,NUCLEUS)
        self.play(FadeIn(image_packet),FadeIn(wave_packet),FadeIn(source_labels),run_time=.7)
        links=VGroup(*[CubicBezier(p.get_bottom(),p.get_bottom()+DOWN*.5,centre+np.array([x,.8,0]),centre+np.array([x,.6,0]),
            color=c,stroke_width=2) for p,x,c in [(image_packet,-.35,CYGNUS),(wave_packet,.35,PHOTON)]])
        self.play(Create(links),Create(ring),Create(sweep),FadeIn(trigger),run_time=.8)
        packets=[image_packet.copy(),wave_packet.copy()];self.add(*packets)
        self.play(*[MoveAlongPath(p,path) for p,path in zip(packets,links)],Rotate(sweep,angle=2*PI,about_point=centre),run_time=1.6)
        self.remove(*packets)
        cloud_link=Arrow(ring.get_bottom(),[-.25,.9,0],buff=.05,color=ELECTRON,stroke_width=2.5)
        self.play(GrowArrow(cloud_link),FadeIn(cloud),run_time=.7)
        packet=factory.event_packet(cloud_link.get_start(),scale=.55);self.add(packet)
        self.play(MoveAlongPath(packet,cloud_link),run_time=1.2);self.remove(packet)
        self.play(LaggedStart(*[FadeIn(p,shift=DOWN*.18) for p in archive],lag_ratio=.2),FadeIn(archive_label),run_time=1)
        link=Arrow([-.25,-2.30,0],offline.get_top(),buff=.03,color=CYGNUS,stroke_width=2)
        self.play(GrowArrow(link),FadeIn(offline),run_time=.8)
        self.audit('trigger packets, cloud and stored-event archive')

    def enter_offline(self):
        self.state['stored_event']=self.event()
        self.add(self.flow_node('INFN Cloud','Stored camera + PMT data',2.7,CYGNUS))

    def offline(self):
        self.clear_content()
        original=self.factory().build_reconstruction_tableau()
        plot=VGroup(original.axes,original.perspective_grid,original.voxels,original.depth_guides,
                    original.unoriented_axis,original.direction_arrow)
        plot.set_width(5.45).move_to([-.25,2.0,0])
        for label in original.axes:
            if isinstance(label,Text):
                label.set_height(.30);label._portrait_text=True;label._minimum_height=.30
        self.play(Create(original.axes),Create(original.perspective_grid),run_time=1)
        self.play(LaggedStart(*[Create(g) for g in original.depth_guides],lag_ratio=.08),
            LaggedStart(*[FadeIn(v,scale=.65) for v in original.voxels],lag_ratio=.045),run_time=2.4)
        self.play(Create(original.unoriented_axis),run_time=.8)
        axis_label=text('3D recoil axis',size=.31,color=NUCLEUS).move_to([-.25,4.7,0])
        self.play(FadeIn(axis_label),run_time=.5);self.wait(1.0)
        self.play(ReplacementTransform(original.unoriented_axis,original.direction_arrow),run_time=.8)
        sense=text('Statistical sense estimate',size=.30,color=NUCLEUS).move_to([-.25,-.5,0])
        self.play(FadeIn(sense),run_time=.6)
        # Restore the explicit ER/NR topology comparison below the depth view.
        cards=[]
        for y,title,detail,colour,is_nr in [(-1.55,'ER-like','Diffuse / tortuous',MUTED,False),(-2.95,'NR-like','Compact / dense',NUCLEUS,True)]:
            box=panel(width=6.1,height=1.05,color=colour).move_to([-.25,y,0])
            icon=original.voxels.copy().set_height(.5) if is_nr else VMobject(color=MUTED,stroke_width=2).set_points_smoothly([[0,0,0],[.2,.4,0],[.4,-.1,0],[.6,.3,0],[.9,0,0]])
            icon.move_to([-2.45,y,0])
            label=VGroup(text(title,size=.32,color=colour,weight='BOLD'),text(detail,size=.30,color=colour)).arrange(DOWN,buff=.15).move_to([.25,y,0])
            cards.append(VGroup(box,icon,label))
        self.play(FadeIn(cards[0]),run_time=.6);self.play(FadeIn(cards[1]),run_time=.6)
        self.play(Indicate(cards[1][0],color=NUCLEUS,scale_factor=1.02),run_time=.8)
        self.audit('restored depth guides, charge colours and topology comparison')
