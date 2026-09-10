"""Restore the Galactic orbit, stellar layers and repeated observer-frame wind."""
import numpy as np
from manim import *
from scenes.vertical.common import PortraitScene,text
from scenes.vertical.baseline import original
from cygno_anim.visuals import FOREGROUND,MUTED,CYGNUS,WIMP,SOLAR,EARTH,GALACTIC_DISK,STAR
from cygno_anim.physics import paired_halo_velocities,observer_frame_velocities,N_CYG

class VerticalGalacticWind(PortraitScene):
    scene_id='01_galactic_wind'
    def make_galaxy(self):
        rng=np.random.default_rng(260831);centre=np.array([-.25,2.0,0]);scale=.50
        backdrop=VGroup()
        for _ in range(84):
            point=[rng.uniform(-7,7)*.49,rng.uniform(-3.8,3.8)*1.0+.8,0]
            backdrop.add(Dot(point,radius=rng.uniform(.006,.018),color=WHITE,
                fill_opacity=rng.uniform(.12,.35),stroke_width=0))
        self.add(backdrop);self.chrome.insert(0,backdrop)
        halo=VGroup()
        for i,w in enumerate((12.2,8.5,3.8)):
            halo.add(Ellipse(width=w*scale,height=6.15*scale,stroke_color=WIMP,stroke_width=1.5,
                stroke_opacity=.55 if i==0 else .20,fill_color=WIMP,fill_opacity=.09 if i==0 else 0).move_to(centre))
        particles=VGroup()
        while len(particles)<210:
            x,y=rng.uniform(-5.65,5.65),rng.uniform(-2.78,2.78)
            if (x/5.65)**2+(y/2.78)**2>1:continue
            particles.add(Dot(centre+[x*scale,y*scale,0],radius=rng.uniform(.022,.050)*scale,
                color=WIMP,fill_opacity=rng.uniform(.48,.82),stroke_width=0))
        halo.add(particles)
        galaxy=VGroup(Ellipse(width=9.15*scale,height=3.82*scale,stroke_color=GALACTIC_DISK,
            stroke_opacity=.33,fill_color=GALACTIC_DISK,fill_opacity=.035).move_to(centre))
        for arm in range(4):
            phase=arm*PI/2
            curve=ParametricFunction(lambda t,phase=phase:centre+scale*np.array([(0.28+.35*t)*np.cos(t+phase),.44*(.28+.35*t)*np.sin(t+phase),0]),
                t_range=[.20,3.08*PI],color=GALACTIC_DISK,stroke_width=1.6).set_stroke(opacity=.68)
            galaxy.add(curve.copy().set_stroke(width=8,opacity=.075),curve)
        arm_stars=VGroup()
        for arm in range(4):
            for _ in range(24):
                t=rng.uniform(.45,3.02*PI);r=.28+.35*t
                p=centre+scale*np.array([r*np.cos(t+arm*PI/2)+rng.normal(0,.085),.44*r*np.sin(t+arm*PI/2)+rng.normal(0,.05),0])
                arm_stars.add(Dot(p,radius=rng.uniform(.008,.022),color=STAR if rng.random()>.20 else SOLAR,
                    fill_opacity=rng.uniform(.35,.82),stroke_width=0))
        bulge=VGroup(Ellipse(width=.575,height=.30,stroke_width=0,fill_color=SOLAR,fill_opacity=.09),
            Ellipse(width=.34,height=.17,stroke_width=0,fill_color=SOLAR,fill_opacity=.22),Dot(radius=.045,color=SOLAR)).move_to(centre)
        galaxy.add(arm_stars,bulge)
        orbit=DashedVMobject(Ellipse(width=3.15,height=1.54).move_to(centre),num_dashes=72,dashed_ratio=.56).set_stroke(SOLAR,width=1.4,opacity=.48)
        self.state.update(halo=halo,galaxy=galaxy,orbit=orbit,centre=centre)

    def solar_system(self,local=False):
        baseline=original('01_galactic_wind');size=1.8 if local else .8
        sun=baseline.sun_marker(ORIGIN,scale=size)
        orbit=Ellipse(width=1.65 if local else .78,height=.66 if local else .30,color=EARTH,stroke_width=1.1,stroke_opacity=.6)
        earth=baseline.earth_marker(orbit.get_right(),scale=2.4 if local else 1.2)
        return VGroup(orbit,sun,earth)

    def enter_halo(self):self.make_galaxy()
    def halo(self):
        s=self.state
        halo_name=text('DARK-MATTER HALO',size=.32,color=WIMP,weight='BOLD').move_to([-.25,4.3,0])
        self.play(FadeIn(s['halo']),FadeIn(halo_name),run_time=1.4);self.wait(.8)
        self.play(Create(s['galaxy']),run_time=2)
        labels=VGroup(text('Stars + gas',size=.31,color=GALACTIC_DISK).move_to([-.25,-.1,0]),
            text('Galactic centre',size=.30,color=SOLAR).move_to([-.25,3.1,0]),
            text('Solar orbit',size=.30,color=SOLAR).move_to([-.25,-.9,0]))
        solar=self.solar_system();centre=s['centre']
        def position(theta):return centre+[1.575*np.cos(theta),.77*np.sin(theta),0]
        solar.move_to(position(-2.62));self.state['sun']=solar
        self.play(Create(s['orbit']),FadeIn(solar),FadeIn(labels),run_time=1)
        motion=Arrow(ORIGIN,RIGHT*.65,color=SOLAR,buff=0,stroke_width=3)
        self.add(motion)
        def orbit_motion(_,alpha):
            angle=-2.62+alpha*(2.62-PI/2);p=position(angle)
            solar.move_to(p)
            solar[2].move_to(p+[.39*np.cos(.35+2*PI*alpha),.15*np.sin(.35+2*PI*alpha),0])
            tangent=np.array([-1.575*np.sin(angle),.77*np.cos(angle),0]);tangent/=np.linalg.norm(tangent)
            motion.put_start_and_end_on(p+.28*tangent,p+.93*tangent)
        self.play(UpdateFromAlphaFunc(solar,orbit_motion,rate_func=linear),run_time=4)
        self.state['motion']=motion
        self.show_global_cygnus(solar)
        self.audit('Galactic orbit and revolving Earth')

    def show_global_cygnus(self,solar,animate=True):
        constellation=original('01_galactic_wind').cygnus_marker(np.array([2.45,1.48,0]),compact=True)
        constellation.remove(constellation[-1])
        name=text('Cygnus',size=.30,color=CYGNUS).move_to([2.10,.48,0])
        sightline=Line(solar[1].get_center()+[.30,.06,0],[2.10,1.43,0],color=CYGNUS,stroke_width=1.8)
        self.state['global_cygnus']=VGroup(constellation,name,sightline)
        if animate:self.play(Create(sightline),FadeIn(constellation),FadeIn(name),run_time=1.0)
        else:self.add(self.state['global_cygnus'])

    def enter_wind(self):
        self.make_galaxy();s=self.state;s['sun']=self.solar_system().move_to(s['centre']+[0,-.77,0])
        self.add(s['halo'],s['galaxy'],s['orbit'],s['sun'])
        self.show_global_cygnus(s['sun'],animate=False)

    def wind(self):
        s=self.state;solar=s['sun']
        self.clear_content(keep=[s['halo'],s['galaxy'],s['orbit'],solar,s['global_cygnus'],*s['global_cygnus']])
        motion=Arrow(solar.get_center()+[.25,0,0],solar.get_center()+[1.1,0,0],buff=0,color=SOLAR,stroke_width=3)
        label=text('Solar motion → Cygnus',size=.31,color=SOLAR).move_to([-.25,-.5,0])
        self.play(GrowArrow(motion),FadeIn(label),run_time=.8);self.wait(.7)
        local=self.solar_system(local=True).move_to([-2.0,1.0,0])
        self.play(FadeOut(s['halo']),FadeOut(s['galaxy']),FadeOut(s['orbit']),FadeOut(motion),FadeOut(label),FadeOut(s['global_cygnus']),ReplacementTransform(solar,local),run_time=2)
        self.state['sun']=local
        angle=[0.]
        def revolve(earth,dt):
            angle[0]+=.92*dt;earth.move_to(local[1].get_center()+[.825*np.cos(angle[0]),.33*np.sin(angle[0]),0])
        local[2].add_updater(revolve)
        constellation=original('01_galactic_wind').cygnus_marker(np.array([2.0,3.5,0]),compact=True)
        constellation.remove(constellation[-1])
        sightline=Arrow([-2.65,2.65,0],[2.4,2.65,0],color=CYGNUS,buff=0,stroke_width=3)
        labels=VGroup(text('Sightline → Cygnus',size=.32,color=CYGNUS).move_to([-.25,4.3,0]),
            text('Solar System',size=.31,color=SOLAR).move_to([-1.65,-.12,0]),
            text('Solar rest frame',size=.30,color=MUTED).move_to([-.25,-2.25,0]))
        self.play(FadeIn(constellation),GrowArrow(sightline),FadeIn(labels),run_time=1)
        velocities=observer_frame_velocities(paired_halo_velocities(seed=260832,n_pairs=18,sigma=.32),.88*N_CYG)
        paths=[];guides=VGroup();arrows=VGroup()
        for i,y in zip((6,8,12,16,21,34,35),np.linspace(.05,2.0,7)):
            v=velocities[i];assert v[0]<0
            dy=v[1]/v[0]*(-4.7)
            start=np.array([2.5,y-dy/2,0]);end=np.array([-2.2,y+dy/2,0])
            path=Line(start,end);paths.append(path)
            guides.add(path.copy().set_stroke(WIMP,width=1,opacity=.23))
            u=(end-start)/np.linalg.norm(end-start);mid=(start+end)/2
            arrows.add(Arrow(mid-.25*u,mid+.25*u,buff=0,color=WIMP,stroke_width=2.5,tip_length=.13))
        cone=Polygon([2.65,2.25,0],[-2.2,.75,0],[2.65,-.5,0],stroke_width=0,fill_color=WIMP,fill_opacity=.045)
        self.play(FadeIn(cone),Create(guides),LaggedStart(*[GrowArrow(a) for a in arrows],lag_ratio=.08),run_time=1.2)
        for _ in range(2):
            animations=[]
            for path in paths:
                particle=VGroup(Circle(radius=.095,color=WIMP,stroke_width=1.3,fill_color=WIMP,fill_opacity=.06),Dot(radius=.032,color=WIMP)).move_to(path.get_start())
                animations.append(Succession(FadeIn(particle,run_time=.12),MoveAlongPath(particle,path,run_time=2.5,rate_func=linear),FadeOut(particle,run_time=.16)))
            self.play(LaggedStart(*animations,lag_ratio=.08),run_time=3.2)
        self.play(FadeIn(text('Incoming dark matter',size=.32,color=WIMP).move_to([-.25,-1.35,0])),run_time=.6)
        local[2].clear_updaters()
        self.audit('Repeated wind waves and Solar System close-up')
