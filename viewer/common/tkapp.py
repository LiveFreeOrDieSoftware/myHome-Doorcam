
import glob
import logging
import os
import queue
import shutil
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import cv2
import imutils
import numpy as np
from PIL import Image, ImageTk


class ClickableLabel(ttk.Label):
    def __init__(self, master=None, onClick=None, ** kwargs):
        ttk.Label.__init__(self, master, **kwargs)
        self.onClick = onClick
        self.bind("<Button-1>", self.clickHandler)

    def clickHandler(self, event):
        if self.onClick:
            self.onClick(event)


class TkApp(threading.Thread):
    # inspired by
    # https://stackoverflow.com/questions/459083/how-do-you-run-your-own-code-alongside-tkinters-event-loop
    # https://www.oreilly.com/library/view/python-cookbook/0596001673/ch09s07.html

    def __init__(self, opts=None):
        self.logger = logging.getLogger(__name__)
        self.ctrlQueue = queue.Queue()
        self.opts = opts
        self.running = False
        self.actionLevel = self.opts["action"]

        self.tabs = None
        # clip tab
        self.panelClip = None
        # monitor tab
        self.panelMonitor = None

        # faces tab
        self.panelFaces = None
        self.facesScale = None
        self.facesOnPage = 6
        self.facesImgPanels = []
        self.faces = []

        # videos tab
        self.videosScale = None
        self.videosOnPage = 6
        self.videosImgPanels = []
        self.thumbs = []

        # status bar
        self.iconMotion = None
        self.iconMotion = None
        self.iconWrite = None
        self.iconWrite = None
        self.statusClock = None
        self.statusLabel = None
        self.showMotionCid = None
        self.showWriteCid = None

        self.tglFaces = False
        self.tglMonitor = False
        self.tglVideos = False
        self.tglClip = False

        threading.Thread.__init__(self)
        # self.start()

    def run(self):
        self.wnd = tk.Tk()
        self.wnd.protocol("WM_DELETE_WINDOW", self.onQuit)
        self.wnd.geometry(self.opts["geometry"])
        self.createWndEls()
        self.processCtrlQueue()
        self.processWorkdir()
        self.updateStatusClock()
        self.running = True
        # self.wnd.mainloop()

    def eventLoop(self):
        self.wnd.mainloop()

    def processCtrlQueue(self):
        # Check every `interval` ms if there is something new in the queue.
        interval = self.opts["tk_queue_interval"]
        while self.ctrlQueue.qsize():
            try:
                msg = self.ctrlQueue.get(0)
                if msg["subj"] == "drawFrame":
                    self.drawFrame(msg["frame"])
                if msg["subj"] == "showMotion":
                    self.showMotion()
                if msg["subj"] == "showWrite":
                    self.showWrite()
            except queue.Empty:
                pass
        self.wnd.after(interval, self.processCtrlQueue)

    def processWorkdir(self, interval=5000):
        # Check every `interval` ms if there is something new in the workdir.
        thumbNames = glob.glob(os.path.sep.join([self.opts["workdir"]] + ["*.thumb.jpeg"]))
        for t in set(thumbNames).difference(self.thumbs):
            self.thumbs.append(t)
        if self.videosScale:
            v = 0 if not self.thumbs else len(self.thumbs) - 1
            self.videosScale.configure(to=v)
        if self.tglVideos:
            self.onVideosSelect(self.videosScale.get())

        self.faces = glob.glob(os.path.sep.join([self.opts["workdir"]] + ["*.fd.jpeg"]))
        if self.facesScale:
            v = 0 if not self.faces else len(self.faces) - 1
            self.facesScale.configure(to=v)
        if not getattr(self.panelFaces, "image", None) and self.faces:
            self.onFacesSelect(self.facesScale.get())

        self.logger.debug("#processWorkdir: thumbs %d faces %d", len(self.thumbs), len(self.faces))
        self.wnd.after(interval, self.processWorkdir)

    def updateStatusClock(self, interval=400):
        now = datetime.now()
        self.statusClock.set(now.strftime("%Y/%m/%d %H:%M:%S"))
        self.wnd.after(interval, self.updateStatusClock)

    def onQuit(self):
        self.running = False
        try:
            self.wnd.quit()
        except:
            pass

    def onTabSelect(self, event):
        selected_tab = event.widget.select()
        tab_text = event.widget.tab(selected_tab, "text")
        self.tglMonitor = tab_text == "Monitor"
        self.tglFaces = tab_text == "Faces"
        self.tglVideos = tab_text == "Videos"
        self.tglClip = tab_text == "Clip"
        if not self.tglClip:
            event.widget.tab(3, state=tk.HIDDEN)
        if self.tglMonitor:
            self.statusBarClock.pack(side=tk.LEFT)
            self.statusBarLabel.pack_forget()
        else:
            self.statusBarClock.pack_forget()
            self.statusBarLabel.pack(side=tk.LEFT)
        if self.tglFaces:
            self.onFacesSelect(self.facesScale.get())
        if self.tglVideos:
            self.onVideosSelect(self.videosScale.get())

    # def onFacesSelect(self, value):
    #     self.logger.debug("#onFacesSelect: %s", value)
    #     fname = self.faces[int(value)]
    #     if self.panelFaces:
    #         self.statusLabel.set(os.path.basename(fname).strip(".fd.jpeg"))
    #         # img = ImageTk.PhotoImage(file=fname)
    #         img = None
    #         with Image.open(fname) as im:
    #             a = np.asarray(im)
    #             img = Image.fromarray(a)
    #         setattr(self.panelFaces, "img", img)
    #         h, w = self.panelFaces.winfo_height(), self.panelFaces.winfo_width()
    #         img = self.imgFit(img, (w, h))
    #         img = ImageTk.PhotoImage(img)
    #         self.panelFaces.configure(image=img)
    #         self.panelFaces.image = img

    def onFacesSelect(self, value):
        value = int(value)
        fname = self.faces[value]
        self.statusLabel.set(os.path.basename(fname).strip(".fd.jpeg"))
        paged = value // self.facesOnPage * self.facesOnPage
        if self.facesImgPanels:
            for i in range(self.facesOnPage):
                idx = paged + i if paged + i < len(self.faces) else None
                state = tk.ACTIVE if value == idx else tk.NORMAL
                imgName = self.faces[idx] if idx is not None else None
                # img = ImageTk.PhotoImage(file=imgName) if imgName else ""
                img = ""
                if imgName:
                    with Image.open(imgName) as im:
                        a = np.asarray(im)
                        img = Image.fromarray(a)
                    img = self.imgFit(img, (200, 200))
                    img = ImageTk.PhotoImage(img)
                self.facesImgPanels[i].configure(image=img, state=state)
                self.facesImgPanels[i].image = img
                setattr(self.facesImgPanels[i], "facesIdx", idx)

    def onFacesClick(self, event):
        facesIdx = getattr(event.widget, "facesIdx", None)
        if facesIdx is not None:
            self.facesScale.set(facesIdx)

    def onFacesBegin(self):
        self.facesScale.set(0)

    def onFacesEnd(self):
        v = 0 if not self.faces else len(self.faces) - 1
        self.facesScale.set(v)

    def onFacesNext(self):
        v = self.facesScale.get() + 1
        v = v if v < len(self.faces) else len(self.faces) - 1
        self.facesScale.set(v)

    def onFacesPrev(self):
        v = self.facesScale.get() - 1
        v = v if v > 0 else 0
        self.facesScale.set(v)

    def onFacesDelete(self):
        idx = self.facesScale.get()
        res = messagebox.askyesno(title="Delete", message="Delete image?")
        if res:
            try:
                os.unlink(self.faces[idx])
                del self.faces[idx]
                v = 0 if not self.faces else len(self.faces) - 1
                self.facesScale.configure(to=v)
                self.onFacesPrev() if idx > 0 else self.onFacesNext()
            finally:
                pass

    def onFacesSave(self):
        idx = self.facesScale.get()
        fname = self.faces[idx]
        res = filedialog.asksaveasfilename(title="Save As", initialdir="", initialfile=os.path.basename(fname))
        if res:
            shutil.copyfile(fname, res)

    def onVideosSelect(self, value):
        value = int(value)
        fname = self.thumbs[value]
        self.statusLabel.set(os.path.basename(fname).strip(".thumb.jpeg"))
        paged = value // self.videosOnPage * self.videosOnPage
        if self.videosImgPanels:
            for i in range(self.videosOnPage):
                idx = paged + i if paged + i < len(self.thumbs) else None
                imgName = self.thumbs[idx] if idx is not None else None
                img = ImageTk.PhotoImage(file=imgName) if imgName else ""
                state = tk.ACTIVE if value == idx else tk.NORMAL
                self.videosImgPanels[i].configure(image=img, state=state)
                self.videosImgPanels[i].image = img
                setattr(self.videosImgPanels[i], "thumbsIdx", idx)

    def onVideosClick(self, event):
        thumbsIdx = getattr(event.widget, "thumbsIdx", None)
        if thumbsIdx is not None:
            # self.onVideosSelect(thumbsIdx)
            self.videosScale.set(thumbsIdx)

    def onVideosBegin(self):
        self.videosScale.set(0)

    def onVideosEnd(self):
        v = 0 if not self.thumbs else len(self.thumbs) - 1
        self.videosScale.set(v)

    def onVideosNext(self):
        v = self.videosScale.get() + 1
        v = v if v < len(self.thumbs) else len(self.thumbs) - 1
        self.videosScale.set(v)

    def onVideosPrev(self):
        v = self.videosScale.get() - 1
        v = v if v > 0 else 0
        self.videosScale.set(v)

    def onVideosDelete(self):
        idx = self.videosScale.get()
        res = messagebox.askyesno(title="Delete", message="Delete clip?")
        if res:
            try:
                clipNameTpl = "{}.mp4" if self.opts["mdclip_codec"] == "mp4v" else "{}.avi"
                clipName = clipNameTpl.format(self.thumbs[idx].strip(".thumb.jpeg"))
                os.unlink(clipName)
                os.unlink(self.thumbs[idx])
                del self.thumbs[idx]
                v = 0 if not self.thumbs else len(self.thumbs) - 1
                self.videosScale.configure(to=v)
                self.onVideosPrev() if idx > 0 else self.onVideosNext()
            finally:
                pass

    def onVideosSave(self):
        idx = self.videosScale.get()
        clipNameTpl = "{}.mp4" if self.opts["mdclip_codec"] == "mp4v" else "{}.avi"
        clipName = clipNameTpl.format(self.thumbs[idx].strip(".thumb.jpeg"))
        res = filedialog.asksaveasfilename(title="Save As", initialdir="", initialfile=os.path.basename(clipName))
        if res:
            shutil.copyfile(clipName, res)

    def onVideosPlay(self):
        idx = self.videosScale.get()
        clipNameTpl = "{}.mp4" if self.opts["mdclip_codec"] == "mp4v" else "{}.avi"
        clipName = clipNameTpl.format(self.thumbs[idx].strip(".thumb.jpeg"))
        self.tabs.tab(3, state=tk.NORMAL)
        self.tabs.select(3)

        # https://stackoverflow.com/questions/50922175/to-show-video-streaming-inside-frame-in-tkinter
        # https://stackoverflow.com/questions/36635567/tkinter-inserting-video-into-window
        thread = threading.Thread(target=self.playClip, args=(clipName,))
        thread.daemon = 1
        thread.start()

    def playClip(self, fname):
        vs = cv2.VideoCapture(fname)
        while vs.isOpened() and self.tglClip:
            ok, frame = vs.read()
            if not ok:
                continue

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            setattr(self.panelClip, "img", img)
            h, w = self.panelClip.winfo_height(), self.panelClip.winfo_width()
            img = self.imgFit(img, (w, h))

            img = ImageTk.PhotoImage(img)
            self.panelClip.configure(image=img)
            self.panelClip.image = img
            time.sleep(0.02)

    def onActionLevelClick(self):
        self.actionLevel = self.monitorAction.get()

    def onImgPanelConfigure(self, event):
        h, w = event.height, event.width
        img = getattr(event.widget, "img", None)
        if img:
            img = self.imgFit(img, (w, h))
            img = ImageTk.PhotoImage(img)
            event.widget.configure(image=img)
            event.widget.image = img

    def createWndEls(self):
        # status icons ◇ : ◆ : ◻ : ◼
        # by some cause the tk.Label update works better with `textvariable` then `text`
        self.iconMotion = tk.StringVar()
        self.iconMotion.set("◻")
        self.iconWrite = tk.StringVar()
        self.iconWrite.set("◻")
        self.statusClock = tk.StringVar()
        self.statusLabel = tk.StringVar()

        style = ttk.Style()
        style.configure("StatusBarPads.TLabel", padding=10)
        style.configure("ImgPanels.TLabel", padding=10)
        style.map("ImgPanels.TLabel", background=[(tk.ACTIVE, "white")])

        statusBar = ttk.Frame(self.wnd)
        statusBar.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusBarClock = ttk.Label(statusBar, textvariable=self.statusClock, style="StatusBarPads.TLabel")
        self.statusBarClock.pack(side=tk.LEFT)
        self.statusBarLabel = ttk.Label(statusBar, textvariable=self.statusLabel, style="StatusBarPads.TLabel")
        self.statusBarLabel.pack(side=tk.LEFT)

        statusBarIcons = ttk.Frame(statusBar)
        statusBarIcons.pack(side=tk.RIGHT)
        statusBarMotion = ttk.Label(statusBarIcons, text="motion")
        statusBarMotion.pack(side=tk.LEFT)
        statusBarMotionIcon = ttk.Label(statusBarIcons, textvariable=self.iconMotion, style="StatusBarPads.TLabel")
        statusBarMotionIcon.pack(side=tk.LEFT)
        statusBarWrite = ttk.Label(statusBarIcons, text="write")
        # statusBarWrite.pack(side=tk.LEFT)
        statusBarWriteIcon = ttk.Label(statusBarIcons, textvariable=self.iconWrite, style="StatusBarPads.TLabel")
        # statusBarWriteIcon.pack(side=tk.LEFT)

        self.tabs = ttk.Notebook(self.wnd)
        self.tabs.bind("<<NotebookTabChanged>>", self.onTabSelect)
        self.tabs.pack(expand=1, fill=tk.BOTH)

        tabMonitor = ttk.Frame(self.tabs)
        tabFaces = ttk.Frame(self.tabs)
        tabVideos = ttk.Frame(self.tabs)
        tabClip = ttk.Frame(self.tabs)
        self.tabs.add(tabMonitor, text="Monitor")
        self.tabs.add(tabFaces, text="Faces")
        self.tabs.add(tabVideos, text="Videos")
        self.tabs.add(tabClip, text="Clip", state=tk.HIDDEN)
        # tabs.select(tabFaces)

        self.panelClip = ttk.Label(tabClip, anchor=tk.CENTER)
        self.panelClip.pack(expand=1, fill=tk.BOTH)
        self.panelClip.bind("<Configure>", self.onImgPanelConfigure)

        self.monitorAction = tk.IntVar(value=self.opts["action"])
        monitorButtons = ttk.Frame(tabMonitor)
        monitorButtons.pack(side=tk.BOTTOM)
        ttk.Radiobutton(monitorButtons, text="MD", value=0, variable=self.monitorAction,
                        command=self.onActionLevelClick).pack(side=tk.LEFT)
        ttk.Radiobutton(monitorButtons, text="FD", value=1, variable=self.monitorAction,
                        command=self.onActionLevelClick).pack(side=tk.LEFT)
        ttk.Radiobutton(monitorButtons, text="FR", value=2, variable=self.monitorAction,
                        command=self.onActionLevelClick).pack(side=tk.LEFT)

        self.panelMonitor = ttk.Label(tabMonitor, anchor=tk.CENTER)
        self.panelMonitor.pack(expand=1, fill=tk.BOTH)
        self.panelMonitor.bind("<Configure>", self.onImgPanelConfigure)

        # the ttk.Scale doesn't support `resolution` and `showvalue` options
        self.facesScale = tk.Scale(tabFaces, orient=tk.VERTICAL, command=self.onFacesSelect,
                                   from_=0, to=0, resolution=1, showvalue=0)
        self.facesScale.pack(side=tk.RIGHT, fill=tk.BOTH)

        facesButtons = ttk.Frame(tabFaces)
        facesButtons.pack(side=tk.BOTTOM)
        btnFacesBegin = ttk.Button(facesButtons, text="⏮", width=2, command=self.onFacesBegin)
        btnFacesBegin.pack(side=tk.LEFT)
        btnFacesPrev = ttk.Button(facesButtons, text="⏪", width=2, command=self.onFacesPrev)
        btnFacesPrev.pack(side=tk.LEFT)
        btnFacesSave = ttk.Button(facesButtons, text="Save", command=self.onFacesSave)
        btnFacesSave.pack(side=tk.LEFT)
        btnFacesDelete = ttk.Button(facesButtons, text="Delete", command=self.onFacesDelete)
        btnFacesDelete.pack(side=tk.LEFT)
        btnFacesNext = ttk.Button(facesButtons, text="⏩", width=2, command=self.onFacesNext)
        btnFacesNext.pack(side=tk.LEFT)
        btnFacesEnd = ttk.Button(facesButtons, text="⏭", width=2, command=self.onFacesEnd)
        btnFacesEnd.pack(side=tk.LEFT)

        # self.panelFaces = ttk.Label(tabFaces, anchor=tk.CENTER)
        # self.panelFaces.pack(expand=1, fill=tk.BOTH)
        # self.panelFaces.bind("<Configure>", self.onImgPanelConfigure)

        self.facesFrame = ttk.Frame(tabFaces)
        self.facesFrame.pack(side=tk.LEFT, expand=1)
        for i in range(self.facesOnPage):
            panel = ClickableLabel(self.facesFrame, style="ImgPanels.TLabel",
                                   onClick=self.onFacesClick)
            panel.grid(row=i // 3, column=i % 3)
            self.facesImgPanels.append(panel)

        self.videosScale = tk.Scale(tabVideos, orient=tk.VERTICAL, command=self.onVideosSelect,
                                    from_=0, to=0, resolution=1, showvalue=0)
        self.videosScale.pack(side=tk.RIGHT, fill=tk.BOTH)

        videosButtons = ttk.Frame(tabVideos)
        videosButtons.pack(side=tk.BOTTOM)
        btnVideosBegin = ttk.Button(videosButtons, text="⏮", width=2, command=self.onVideosBegin)
        btnVideosBegin.pack(side=tk.LEFT)
        btnVideosPrev = ttk.Button(videosButtons, text="⏪", width=2, command=self.onVideosPrev)
        btnVideosPrev.pack(side=tk.LEFT)
        btnVideosPlay = ttk.Button(videosButtons, text="►", width=2, command=self.onVideosPlay)
        btnVideosPlay.pack(side=tk.LEFT)
        btnVideosSave = ttk.Button(videosButtons, text="Save", command=self.onVideosSave)
        btnVideosSave.pack(side=tk.LEFT)
        btnVideosDelete = ttk.Button(videosButtons, text="Delete", command=self.onVideosDelete)
        btnVideosDelete.pack(side=tk.LEFT)
        btnVideosNext = ttk.Button(videosButtons, text="⏩", width=2, command=self.onVideosNext)
        btnVideosNext.pack(side=tk.LEFT)
        btnVideosEnd = ttk.Button(videosButtons, text="⏭", width=2, command=self.onVideosEnd)
        btnVideosEnd.pack(side=tk.LEFT)

        videosFrame = ttk.Frame(tabVideos)
        videosFrame.pack(side=tk.LEFT, expand=1)
        for i in range(self.videosOnPage):
            panel = ClickableLabel(videosFrame, style="ImgPanels.TLabel",
                                   onClick=self.onVideosClick)
            panel.grid(row=i // 3, column=i % 3)
            self.videosImgPanels.append(panel)

    def showMotion(self):
        if self.showMotionCid:
            self.wnd.after_cancel(self.showMotionCid)
        self.iconMotion.set("◼")
        self.showMotionCid = self.wnd.after(500, lambda: self.iconMotion.set("◻"))

    def showWrite(self):
        if self.showWriteCid:
            self.wnd.after_cancel(self.showWriteCid)
        self.iconWrite.set("◼")
        self.showWriteCid = self.wnd.after(500, lambda: self.iconWrite.set("◻"))

    def drawFrame(self, frame):
        if self.tglMonitor:
            # OpenCV represents images in BGR order; however PIL represents
            # images in RGB order, so we need to swap the channels
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # convert the images to PIL format...
            img = Image.fromarray(img)
            # store and resize to fit area
            setattr(self.panelMonitor, "img", img)
            h, w = self.panelMonitor.winfo_height(), self.panelMonitor.winfo_width()
            img = self.imgFit(img, (w, h))
            # ...and then to ImageTk format
            img = ImageTk.PhotoImage(img)
            # update the image panel
            self.panelMonitor.configure(image=img)
            self.panelMonitor.image = img

    def imgFit(self, img, size=(640, 480)):
        w, h = img.width, img.height
        r0, r1 = w/size[0], h/size[1]
        if r0 > r1:
            w, h = int(w/r0), int(h/r0)
        else:
            w, h = int(w/r1), int(h/r1)
        return img.resize((w, h)) if w > 0 and h > 0 else img
