"""Baseline elastic collision, forward recoil ensemble and microscopic close-up."""
import numpy as np
from manim import *
from scenes.vertical.common import PortraitScene,text,panel
from scenes.vertical.baseline import original,recoil_reference
from cygno_anim.physics import elastic_scatter_lab

baseline=original('02_wimp_recoil')
FOREGROUND,MUTED,WIMP,RECOIL,ELECTRON=(baseline.FOREGROUND,baseline.MUTED,baseline.WIMP,baseline.RECOIL,baseline.ELECTRON)
nucleus_marker,candidate_marker=baseline.nucleus_marker,baseline.candidate_marker

class VerticalWIMPRecoil(PortraitScene):
    scene_id='02_wimp_recoil'

    def setup(self):
        super().setup();self.camera.background_color=baseline.BACKGROUND

    def enter_recoil(self):
        solution=elastic_scatter_lab();origin=np.array([-.6,1.8,0.]);scale=4.3
        self.state.update(solution=solution,origin=origin,incoming=origin-np.r_[solution.p_in,0]*scale,
            outgoing=origin+np.r_[solution.p_out,0]*scale,recoil_end=origin+np.r_[solution.q,0]*scale)
        target=nucleus_marker(.34).move_to(origin)
        atom=VGroup(Circle(radius=.48,color=MUTED,stroke_width=1.2).move_to(origin),
            Dot(origin+UP*.48,radius=.035,color=ELECTRON),Dot(origin+DOWN*.48,radius=.035,color=ELECTRON))
        gas=VGroup(*[VGroup(Circle(radius=.13,color=MUTED,stroke_width=1),Dot(radius=.035,color=MUTED),
            Dot(RIGHT*.13,radius=.025,color=ELECTRON)).set_opacity(.5).move_to([x,y,0])
            for x,y in [(-2.8,3.7),(-2.6,.1),(-.1,4.5),(2.4,3.5),(2.5,-.5),(-2.8,-1.4),(.3,-1.4)]])
        candidate=candidate_marker(.13).move_to(self.state['incoming'])
        labels=VGroup(text('Dark-matter particle',size=.30,color=WIMP).move_to([-1.6,2.6,0]),
            text('Detector-gas nucleus',size=.30,color=RECOIL).move_to([-.25,.55,0]),
            text('Ordinary matter',size=.30,color=MUTED).move_to([-.25,.05,0]))
        self.state.update(nucleus=target,dm=candidate,atom=atom,gas=gas,labels=labels)
        self.add(gas,atom,target,candidate,labels)

    def recoil(self):
        s=self.state
        incoming=Arrow(s['incoming'],s['origin'],buff=0,color=WIMP,stroke_width=4)
        pin=MathTex(r'\mathbf p_{\rm in}',color=WIMP).set_height(.30).move_to([-2.0,1.28,0])
        self.play(GrowArrow(incoming),FadeIn(pin),run_time=.7)
        self.play(MoveAlongPath(s['dm'],Line(s['incoming'],s['origin']),rate_func=linear),run_time=1.6)
        self.play(Flash(s['origin'],color=FOREGROUND,line_length=.16,flash_radius=.42),s['nucleus'].animate.scale(1.12),run_time=.4)
        self.play(s['nucleus'].animate.scale(1/1.12),run_time=.3)
        outgoing=Arrow(s['origin'],s['outgoing'],buff=0,color=WIMP,stroke_width=4)
        recoil=Arrow(s['origin'],s['recoil_end'],buff=0,color=RECOIL,stroke_width=4.5)
        pout=MathTex(r'\mathbf p_{\rm out}',color=WIMP).set_height(.30).move_to([1.45,3.0,0])
        q=MathTex(r'\mathbf q=\mathbf p_{\rm recoil}',color=RECOIL).set_height(.30).move_to([-1.7,.4,0])
        names=VGroup(text('Scattered dark matter',size=.30,color=WIMP).move_to([-.25,4.05,0]),
            text('Recoiling gas nucleus',size=.30,color=RECOIL).move_to([.75,-.7,0]))
        self.play(GrowArrow(outgoing),GrowArrow(recoil),FadeOut(s['atom']),FadeOut(s['labels']),FadeIn(pout),FadeIn(q),FadeIn(names),run_time=.9)
        self.play(MoveAlongPath(s['dm'],Line(s['origin'],s['outgoing']),rate_func=linear),
            MoveAlongPath(s['nucleus'],Line(s['origin'],s['recoil_end']),rate_func=linear),run_time=1.8)
        fan=VGroup()
        for angle in np.deg2rad(recoil_reference()['fan_angles']):
            direction=np.array([np.cos(angle),np.sin(angle),0]);centrality=np.cos(angle)**2
            fan.add(Arrow(s['origin']+.09*direction,s['origin']+(1.30+.28*centrality)*direction,
                buff=0,color=RECOIL,stroke_width=2).set_opacity(.12+.26*centrality))
        axis=DashedLine(s['origin']+.12*RIGHT,s['origin']+2.05*RIGHT,color=WIMP,stroke_width=1.7,dash_length=.08)
        tag=text('Recoil\nensemble',size=.30,color=MUTED,width=2).move_to([2.05,1.75,0])
        self.play(Create(axis),LaggedStart(*[GrowArrow(a) for a in fan],lag_ratio=.035),FadeIn(tag),run_time=1.2)
        formula=MathTex(r'\mathbf q=\mathbf p_{\rm in}-\mathbf p_{\rm out}=\mathbf p_{\rm recoil}',color=FOREGROUND).set_height(.36).move_to([-.25,-2.55,0])
        box=panel(height=.85).move_to(formula)
        self.play(FadeIn(box),Write(formula),run_time=1.0)
        self.audit('baseline collision, momentum labels and forward recoil ensemble')

    def make_track(self,formed=False):
        ref=recoil_reference();q=np.r_[elastic_scatter_lab().q,0];direction=q/np.linalg.norm(q)
        transverse=np.array([-direction[1],direction[0],0]);start=np.array([-1.50,2.90,0]);scale=2.55
        distances=np.array(ref['distances']);wiggles=np.array(ref['wiggles']);deposits=np.array(ref['deposit_distances'])
        points=np.array([start+scale*(d*direction+w*transverse) for d,w in zip(distances,wiggles)])
        trail=VMobject(color=RECOIL,stroke_width=4.2,stroke_opacity=.78).set_points_as_corners(points)
        ions,electrons,neutrals=VGroup(),VGroup(),VGroup();bound=[];free=[];ion_opacity=[];electron_opacity=[]
        for i,distance in enumerate(deposits):
            progress=distance/distances[-1];side=-1 if i%2 else 1
            p=start+scale*(distance*direction+np.interp(distance,distances,wiggles)*transverse)
            ion_point=p+scale*side*(.022+.007*(i%3))*transverse
            free_point=p+scale*side*(.102+.015*(i%4))*transverse
            ions.add(Circle(radius=scale*(.030+.012*(1-progress)),color=RECOIL,stroke_width=1.5,
                fill_color=RECOIL,fill_opacity=.12+.28*(1-progress)).move_to(ion_point))
            electrons.add(Dot(free_point,radius=scale*(.016+.007*(1-progress)),color=ELECTRON,fill_opacity=.55+.40*(1-progress)))
            neutrals.add(Circle(radius=scale*.052,color=MUTED,stroke_width=1.1).move_to(ion_point))
            bound.append(ion_point+scale*.052*transverse);free.append(free_point)
            ion_opacity.append(ions[-1].get_fill_opacity());electron_opacity.append(electrons[-1].get_fill_opacity())
        ambient=VGroup()
        for along,across in ref['gas_offsets']:
            p=start+scale*((along+.18)*direction+across*transverse)
            if -3.25<p[0]<2.75 and -1.8<p[1]<4.7:
                ambient.add(Circle(radius=scale*.075,color=MUTED,stroke_width=1.2,stroke_opacity=.65,fill_color=MUTED,fill_opacity=.08).move_to(p))
        if formed:neutrals.set_opacity(0)
        else:
            ions.set_opacity(0)
            for dot,p in zip(electrons,bound):dot.move_to(p).set_opacity(.45)
        self.state.update(points=points,track_start=start,track_scale=scale,direction=direction,transverse=transverse,
            deposits=deposits,trail=trail,ions=ions,electrons=electrons,sites=neutrals,ambient=ambient,
            bound=np.array(bound),free=np.array(free),ion_opacity=ion_opacity,electron_opacity=electron_opacity)

    def enter_ionization(self):
        self.make_track();s=self.state;s['nucleus']=nucleus_marker(.34*.47*s['track_scale']).move_to(s['points'][0])
        self.add(s['ambient'],s['sites'],s['ions'],s['electrons'],s['nucleus'])

    def ionization(self):
        nucleus=self.state['nucleus']
        if 'points' not in self.state:
            gas=self.state['gas'];self.clear_content(keep=[nucleus,gas]);self.make_track()
            self.play(ReplacementTransform(gas,self.state['ambient']),
                nucleus.animate.scale(.47*self.state['track_scale']).move_to(self.state['points'][0]),run_time=1.5)
            self.play(FadeIn(self.state['sites']),FadeIn(self.state['electrons']),run_time=.6)
        else:
            self.play(Indicate(self.state['sites'][:3],color=ELECTRON,scale_factor=1.1),run_time=.8)
        s=self.state;full=s['trail'].copy();s['trail'].pointwise_become_partial(full,0,0)
        group=VGroup(s['trail'],nucleus,s['ions'],s['electrons'],s['sites']);self.add(group)
        def form(_,alpha):
            s['trail'].pointwise_become_partial(full,0,alpha);nucleus.move_to(s['trail'].get_end())
            travelled=np.dot(nucleus.get_center()-s['track_start'],s['direction'])/s['track_scale']
            for i,distance in enumerate(s['deposits']):
                visible=float(np.clip((travelled-distance)/.045,0,1))
                s['ions'][i].set_stroke(opacity=visible).set_fill(opacity=s['ion_opacity'][i]*visible)
                s['sites'][i].set_opacity(.65*(1-visible))
                s['electrons'][i].move_to((1-visible)*s['bound'][i]+visible*s['free'][i]).set_opacity(.45*(1-visible)+s['electron_opacity'][i]*visible)
        self.play(UpdateFromAlphaFunc(group,form,rate_func=linear),run_time=3.55)
        self.remove(group);self.add(s['trail'],nucleus,s['ions'],s['electrons'],s['sites'])
        s['track_formed']=True
        self.add_legend()
        self.audit('same nucleus, baseline microscopic path and bound-to-free electrons')

    def add_legend(self):
        legend=VGroup(VGroup(Dot(radius=.045,color=ELECTRON),text('Freed electrons',size=.30,color=ELECTRON)).arrange(RIGHT,buff=.12),
            VGroup(Circle(radius=.065,color=RECOIL,stroke_width=1.5),text('Positive gas ions',size=.30,color=RECOIL)).arrange(RIGHT,buff=.12))
        legend.arrange(DOWN,aligned_edge=LEFT,buff=.15).move_to([-1.65,-1.25,0])
        self.state['legend']=legend;self.play(FadeIn(legend),run_time=.7)

    def enter_sense(self):
        # A standalone sense clip first shows the event that will be analyzed.
        self.enter_ionization()

    def sense(self):
        if not self.state.get('track_formed'):self.ionization()
        s=self.state;p=s['points'];u=s['direction'];v=s['transverse']
        if 'legend' not in s:self.add_legend()
        start=text('START / TAIL\nMore ionization',size=.30,color=RECOIL).move_to([-.75,4.0,0])
        stop=text('STOP / HEAD\nLess ionization',size=.30,color=RECOIL).move_to([1.4,-1.15,0])
        callouts=VGroup(DashedLine(start.get_bottom(),p[0]+[.15,.1,0],color=MUTED,stroke_width=1.2),
            DashedLine(stop.get_top(),p[-1]+[.05,-.18,0],color=MUTED,stroke_width=1.2))
        arrow=Arrow(p[0]+.1*s['track_scale']*u-.28*s['track_scale']*v,
            p[-1]-.08*s['track_scale']*u-.28*s['track_scale']*v,buff=0,color=RECOIL,stroke_width=2.6)
        axis=Line(arrow.get_start(),arrow.get_end(),color=RECOIL,stroke_width=2.6)
        self.play(FadeIn(start),FadeIn(stop),Create(callouts),Create(axis),run_time=1.0)
        self.play(ReplacementTransform(axis,arrow),run_time=.8)
        label=text('Recoil sense',size=.30,color=RECOIL).move_to([-1.95,-.3,0])
        self.play(FadeIn(label),Create(DashedLine(label.get_top(),arrow.point_from_proportion(.52),color=MUTED,stroke_width=1.1)),run_time=.6)
        nodes=VGroup()
        for x,title,color in [(-2.45,'NR energy\nloss',RECOIL),(-.25,'Ionization\nasymmetry',ELECTRON),(1.95,'Head–tail\nestimate',FOREGROUND)]:
            nodes.add(VGroup(panel(width=2.0,height=1.05,color=color).move_to([x,-2.9,0]),text(title,size=.30,color=color,width=1.9).move_to([x,-2.9,0])))
        links=VGroup(*[Arrow(nodes[i].get_right(),nodes[i+1].get_left(),buff=.02,color=MUTED,stroke_width=1.5,tip_length=.08) for i in range(2)])
        self.play(LaggedStart(*[FadeIn(n) for n in nodes],lag_ratio=.18),Create(links),run_time=1.4)
        self.play(FadeIn(text('Statistical sense recognition',size=.30,color=MUTED).move_to([-.25,-3.85,0])),run_time=.6)
        self.audit('baseline head-tail callouts and energy-loss chain')
