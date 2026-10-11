"""Animate cached wallpaper surfaces without PrintWindow or an input overlay."""
import time,tkinter as tk
from PIL import Image

class SkinFade:
    def __init__(self,app):
        self.app=app;self.root=app.root;self.renderer=app.skin_renderer;self.job=None;self.frames=[];self.started=time.perf_counter()
        previous=getattr(app,'_skin_fade',None)
        if previous:previous.finish()
        self.old=self.renderer.scene
        self.target=None;self.renderer._defer_paint=self.old is not None and self.root.state()=='normal'
        app._skin_fade=self
    def start(self):
        self.target=self.renderer.scene;self._target_stamp=getattr(self.renderer,"_scene_stamp",None);self.renderer._defer_paint=False;self.renderer._hold=True
        if self.renderer.job:self.root.after_cancel(self.renderer.job);self.renderer.job=None
        if self.old is None or self.target is None or self.old.size!=self.target.size or self.root.state()!='normal':self.finish();return
        self.prepared_ms=(time.perf_counter()-self.started)*1000;self.started=time.perf_counter();self._frame()
    def _frame(self):
        self.job=None
        if not self.root.winfo_exists():return
        t=min(1,(time.perf_counter()-self.started)/.30);eased=t*t*(3-2*t);self.frames.append(eased)
        # A normal control refresh can render between animation frames.
        # Keep that newer selection instead of replacing it with a stale target.
        if getattr(self.renderer,"_scene_stamp",None)!=self._target_stamp:self.target=self.renderer.scene
        self.renderer.scene=Image.blend(self.old,self.target,eased) if t<1 else self.target
        previous_stamp=getattr(self.renderer,'_scene_stamp',None)
        self.renderer.generation+=1;self.renderer.render()
        # Selection or time-mode changes during the fade remain the final scene.
        if getattr(self.renderer,'_scene_stamp',None)!=previous_stamp:self.target=self.renderer.scene
        self._target_stamp=getattr(self.renderer,'_scene_stamp',None)
        if t>=1:self.finish();return
        # No animation backlog: the next frame follows completion of this frame.
        self.job=self.root.after(8,self._frame)
    def finish(self):
        if self.job:
            try:self.root.after_cancel(self.job)
            except tk.TclError:pass
            self.job=None
        self.renderer._defer_paint=False;self.renderer._hold=False
        if self.target is not None and self.renderer.scene is not self.target:
            self.renderer.scene=self.target;self.renderer.generation+=1;self.renderer.render()
        self.app._last_skin_fade_stats={'frames':list(self.frames),'prepare_ms':getattr(self,'prepared_ms',0),'strategy':'cached-surfaces'}
        if getattr(self.app,'_skin_fade',None) is self:self.app._skin_fade=None
