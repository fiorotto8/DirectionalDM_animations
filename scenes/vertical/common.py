"""Portrait composition, independent chapter entry and phone-size typography."""
from __future__ import annotations
import json
import os
import textwrap
from pathlib import Path
import numpy as np
from manim import *
from cygno_anim.branding import load_branding_settings, _logo_mobject, _position_original_qr
from cygno_anim.visuals import BACKGROUND, FOREGROUND, MUTED, CYGNUS, FONT

ROOT = Path(__file__).resolve().parents[2]

def text(message, size=.40, color=FOREGROUND, width=6.35, weight="NORMAL"):
    # Wrap before sizing: never shrink a long sentence below its requested height.
    lines=[]
    for line in message.split('\n'):
        lines.extend(textwrap.wrap(line, width=max(12,int(width/(size*.62))), break_long_words=False) or [''])
    result=VGroup()
    for line in lines:
        item=Text(line or ' ',font=FONT,color=color,weight=weight)
        item.set_height(size)
        if item.width>width:
            # Wide glyphs need a second wrap rather than smaller letters.
            if width>4:return text(message,size,color,width*.94,weight)
            raise ValueError(f'Diagram label {line!r} exceeds width {width:g}; widen its panel or shorten the label.')
        item._portrait_text=True
        item._minimum_height=size
        result.add(item)
    result.arrange(DOWN,buff=size*.32)
    return result

def panel(width=6.25,height=2.0,color=MUTED):
    return RoundedRectangle(width=width,height=height,corner_radius=.13,
        stroke_color=color,stroke_width=1.5,fill_color=BACKGROUND,fill_opacity=.96)

class PortraitScene(Scene):
    scene_id=''
    def setup(self):
        self.camera.background_color=BACKGROUND
        self.state={}
        self.heading=None
        self.caption=None
        self.checkpoints=[]
        self.chrome=[]
        self.section_timings=[]
        self.pause_records=[]
        self._pacing_active=False
        self._motion_scale=1.0
        self._motion_seconds=0.0
        self.measure_pacing=getattr(self,'measure_pacing',False)

    def construct(self):
        from scripts.vertical import load_catalog
        self.spec=next(s for s in load_catalog()['scenes'] if s['id']==self.scene_id)
        section_id=os.environ.get('CYGNO_VERTICAL_SECTION','full')
        self.story=section_id!='full'
        sections=self.spec['sections'] if not self.story else [s for s in self.spec['sections'] if s['id']==section_id]
        if not sections:raise ValueError(f'Unknown section {section_id}')
        self.add_chrome()
        first=sections[0]
        self.current=first
        getattr(self,first['entry'])()
        # Brief visual context, without the former narration-card delay.
        self.wait(.5 if self.story else .4)
        self.audit('opening')
        for index,section in enumerate(sections):
            self.current=section
            start=self.renderer.time
            self._pacing_active=True
            self._motion_seconds=0.0
            self._motion_scale=1.0 if self.measure_pacing else section.get('story_motion_scale' if self.story else 'full_motion_scale',1.0)
            getattr(self,section['method'])()
            self._pacing_active=False
            elapsed=self.renderer.time-start
            budget=(section['story_seconds']-2.5) if self.story else section['full_seconds']
            settle=section.get('story_settle_seconds' if self.story else 'full_settle_seconds',0.0)
            remaining=budget-elapsed-settle
            if not self.measure_pacing:
                if remaining < -.04 or remaining > .60:
                    raise ValueError(f"{section['id']}: action {elapsed:.3f}s, budget {budget:.3f}s; closing pause must be 0–0.6s. Adjust motion pacing, not idle padding.")
                if settle:
                    self.audit('settle: '+section['id'])
                    self.wait(settle,purpose='settle: '+section['id'])
                if remaining>0:self.wait(remaining)
            self.section_timings.append({'id':section['id'],'start':start,'action_seconds':elapsed,
                'motion_seconds':self._motion_seconds,'settle_seconds':settle if not self.measure_pacing else 0,
                'closing_pause':max(0,remaining) if not self.measure_pacing else 0})
            self.audit(section['id'])
        self.ending(compact=self.story)
        self.audit('ending')
        record=os.environ.get('CYGNO_VERTICAL_AUDIT')
        if record:Path(record).write_text(json.dumps({'scene':self.scene_id,'section':section_id,'duration':self.renderer.time,
            'checkpoints':self.checkpoints,'sections':self.section_timings,'pauses':self.pause_records},indent=2))

    def play(self,*animations,**kwargs):
        is_wait=all(isinstance(a,Wait) for a in animations)
        if self._pacing_active and not is_wait:
            duration=kwargs.get('run_time',max((getattr(a,'run_time',1.0) for a in animations),default=1.0))
            kwargs['run_time']=max(1/30,round(duration*self._motion_scale*30)/30)
        start=self.renderer.time
        result=super().play(*animations,**kwargs)
        if self._pacing_active and not is_wait:self._motion_seconds+=self.renderer.time-start
        return result

    def wait(self,duration=1,purpose=None,**kwargs):
        duration=min(duration,.2) if self._pacing_active else duration
        self.pause_records.append({'start':self.renderer.time,'seconds':duration,'within_section':self._pacing_active,'purpose':purpose})
        return super().wait(duration,**kwargs)

    def add_chrome(self):
        settings=load_branding_settings()
        logo=_logo_mobject(settings).set_height(.35).move_to([-2.8,5.72,0])
        handle=text('@cygno.exp',size=.20,color=CYGNUS).move_to([-.25,5.72,0])
        mark=Text(settings.watermark,font=FONT,color=MUTED,weight='BOLD').set_height(.105)
        mark.move_to([-.25,-4.36,0]).set_z_index(2000)
        self.chrome=[logo,handle,mark]
        self.add(*self.chrome)

    def note(self,message,color=FOREGROUND,hold=1.0):
        # Editorial narration metadata must not create invisible reading holds.
        pass

    def clear_content(self,keep=()):
        protected=[*self.chrome,self.heading,self.caption,*keep]
        old=[m for m in self.mobjects if not any(m is x for x in protected)]
        if old:self.play(*[FadeOut(m) for m in old],run_time=.4)

    def ending(self,compact):
        mark=self.chrome[-1]
        settings=load_branding_settings()
        old=[m for m in self.mobjects if m is not mark]
        logo=_logo_mobject(settings).set_height(.65 if compact else .38)
        logo.move_to([0,4.8 if compact else 5.65,0])
        name=text('CYGNO EXPERIMENT',size=.34 if compact else .27,weight='BOLD').move_to([0,3.9 if compact else 5.15,0])
        if compact:
            qr=_position_original_qr(settings.website_qr_path,(4,3,471,470),320/120,[0,1.3,0])
            qr.set_resampling_algorithm(RESAMPLING_ALGORITHMS['nearest'])
            card=RoundedRectangle(width=3.55,height=3.95,corner_radius=.12,stroke_width=0,fill_color=WHITE,fill_opacity=1).move_to([0,1.02,0])
            handle=text('@cygno.exp',size=.36,color=CYGNUS).move_to([0,-1.5,0])
            content=Group(logo,name,card,qr,handle)
        else:
            codes=[]
            # 320-pixel ink squares; both original full rasters remain intact.
            for path,bounds,y,caption in (
                (settings.website_qr_path,(4,3,471,470),2.65,'Website'),
                (settings.instagram_qr_path,(235,250,2115,2130),-1.95,'Instagram')):
                qr=_position_original_qr(path,bounds,320/120,[0,y,0])
                if caption=='Website':qr.set_resampling_algorithm(RESAMPLING_ALGORITHMS['nearest'])
                card=RoundedRectangle(width=3.55,height=3.95,corner_radius=.12,stroke_width=0,fill_color=WHITE,fill_opacity=1).move_to([0,y-.28,0])
                title=text(caption,size=.30).move_to([0,y+1.98,0])
                codes.extend([card,qr,title])
            content=Group(logo,name,*codes)
        self.play(*[FadeOut(m) for m in old],FadeIn(content),run_time=.5)
        self.heading=self.caption=None
        self.wait(1.5 if compact else 3.5)

    def audit(self,label):
        violations=[]; boxes=[]
        for obj in self.get_mobject_family_members():
            if isinstance(obj,Text) and getattr(obj,'_portrait_text',False) and obj.get_fill_opacity()>.01:
                box=[float(obj.get_left()[0]),float(obj.get_right()[0]),float(obj.get_bottom()[1]),float(obj.get_top()[1])]
                boxes.append({'text':obj.text,'box':box,'height':float(obj.height)})
                if obj.height+1e-6<obj._minimum_height:violations.append('undersized: '+obj.text)
                # Brand signature is intentionally smaller than narrative text.
                if box[0]<-3.5-.02 or box[1]>3+.02 or box[2]<-4.5-.02 or box[3]>5.917+.02:violations.append(obj.text)
        self.checkpoints.append({'label':label,'time':self.renderer.time,'text':boxes,'outside_safe_region':violations})
        if violations:raise ValueError(f'{label}: text outside portrait safe region: {violations}')
