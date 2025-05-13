from .base_page import BasePage
import os
import sys
import shutil
from tkinter import filedialog, messagebox
import pandas as pd
import datetime
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps, ImageSequence, ImageDraw
from tkinter import BOTH, X, Y, TOP, LEFT, RIGHT, END
from tkinter.ttk import Treeview
import tkinter.font as tkfont
from auth import register_user, verify_user, get_user_name
import tkinter.font as tkfont
import tkinter as tk
import threading
import cv2
import time
from tkinter import Toplevel
from tkinter.ttk import Scrollbar


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report
from GUI.auth import register_user, verify_user, get_user_name


class ViewDataPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.controller.imported_folder = None

        # Notebook tabs
        self.notebook = tb.Notebook(self, bootstyle="secondary")
        self.notebook.pack(fill=BOTH, expand=True, padx=20, pady=20)

        self.rt_tab  = tb.Frame(self.notebook)
        self.imp_tab = tb.Frame(self.notebook)
        self.notebook.add(self.rt_tab,  text="Real-Time Data")
        self.notebook.add(self.imp_tab, text="Imported Data")

        # Build both panes
        self._build_rt_pane()
        self._build_imp_pane()

    # defining real time pane
    def _build_rt_pane(self):
        paned = tk.PanedWindow(self.rt_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=BOTH, expand=True)

        # ading left scrollbar 
        lf = tb.Frame(paned, width=300)
        lf.pack_propagate(False)
        paned.add(lf, stretch="always", minsize=300)

        self.rt_tree = Treeview(lf, show="tree")
        vsb = Scrollbar(
            lf,
            orient="vertical",
            command=self.rt_tree.yview,
            style='Vertical.TScrollbar'     
        )
        # tree drop dopwn for file
        self.rt_tree.configure(yscrollcommand=vsb.set)

        vsb.pack(side=RIGHT, fill=Y, padx=(0,5), pady=5)
        self.rt_tree.pack(fill=BOTH, expand=True, padx=(5,0), pady=5)
        self.rt_tree.bind("<<TreeviewSelect>>", self._on_rt_select)

        # adding right scrollbar - user testing feature
        rf = tb.Frame(paned)
        paned.add(rf, stretch="always")
        
        # vertical scrollbar
        self.rt_text = tk.Text(rf, wrap="none", state="disabled")
        text_vsb = Scrollbar(
            rf,
            orient="vertical",
            command=self.rt_text.yview,
            style='Vertical.TScrollbar'
        )
        # horizontal scrollbar
        text_hsb = Scrollbar(
            rf,
            orient="horizontal",
            command=self.rt_text.xview,
            style='Horizontal.TScrollbar'
        )
        self.rt_text.configure(
            yscrollcommand=text_vsb.set,
            xscrollcommand=text_hsb.set
        )

        # postiioning for scrollbars
        self.rt_text.grid(row=0, column=0, sticky="nsew", padx=(5,0), pady=(5,0))
        text_vsb.grid(row=0, column=1, sticky="ns",    padx=(0,5), pady=(5,0))
        text_hsb.grid(row=1, column=0, sticky="ew",    padx=(5,0), pady=(0,5))

        rf.rowconfigure(0, weight=1)
        rf.columnconfigure(0, weight=1)

        paned.update_idletasks()
        paned.sash_place(0, 300, 0)

        self._populate_rt()



    def _populate_rt(self):
        # Clears tab
        for iid in self.rt_tree.get_children():  
            self.rt_tree.delete(iid)

        # empty until user logs in
        user = self.controller.current_user_name or self.controller.current_user_email
        if not user:  
            return

        base = self.controller.user_data_folder
        if os.path.isdir(base):
            root = self.rt_tree.insert("", "end", text=user, open=True)
            for fn in sorted(os.listdir(base)):
                if fn.lower().endswith( (".csv", ".png", ".pdf") ):
                    self.rt_tree.insert(root, "end", text=fn)


    def _on_rt_select(self, _evt):
        # if tree is selcted, drop down
        sel = self.rt_tree.selection()
        if not sel:
            return
        item = sel[0]
        if self.rt_tree.parent(item) == "":
            return

        fn = self.rt_tree.item(item, "text")
        user = self.controller.current_user_name or self.controller.current_user_email
        base = os.path.join("deterministic_model_test", user)
        path = os.path.join(base, fn)

        self.rt_text.config(state='normal')
        self.rt_text.delete("1.0", END)

        ext = os.path.splitext(fn)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(path)
            self.rt_text.insert(END, df.head(20).to_string(index=False))

        # view png graphs, when selected.
        elif ext in (".png", ".jpg", ".jpeg"):
            # resize image
            img = Image.open(path).resize((400, 400), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.rt_text.image_create("1.0", image=photo)
            self.rt_text.image = photo
        # message when pdf saved
        elif ext == ".pdf":
            self.rt_text.insert(END, f"PDF report saved at:\n{path}")
        # error message when unformatted file type
        else:
            self.rt_text.insert(END, f"Cannot preview this file type:\n{fn}")

        self.rt_text.config(state='disabled')

    # build imported tab
    def _build_imp_pane(self):
        paned = tk.PanedWindow(self.imp_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=BOTH, expand=True)

        # left scrtollbar
        lf = tb.Frame(paned, width=300)
        lf.pack_propagate(False)
        paned.add(lf, stretch="always", minsize=300)

        self.imp_tree = Treeview(lf, show="tree")
        imp_vsb = Scrollbar(
            lf,
            orient="vertical",
            command=self.imp_tree.yview,
            style='Vertical.TScrollbar'
        )
        self.imp_tree.configure(yscrollcommand=imp_vsb.set)
        
        # treeview drop dpown folder
        imp_vsb.pack(side=RIGHT, fill=Y, padx=(0,5), pady=5)
        self.imp_tree.pack(fill=BOTH, expand=True, padx=(5,0), pady=5)
        self.imp_tree.bind("<<TreeviewSelect>>", self._on_imp_select)

        # right scrollbar
        rf = tb.Frame(paned)
        paned.add(rf, stretch="always")
        self.imp_text = tk.Text(rf, wrap="none", state="disabled")
        
        # vertical scroll bar
        imp_text_vsb = Scrollbar(
            rf,
            orient="vertical",
            command=self.imp_text.yview,
            style='Vertical.TScrollbar'
        )
        
        # horizontal scrollbar
        imp_text_hsb = Scrollbar(
            rf,
            orient="horizontal",
            command=self.imp_text.xview,
            style='Horizontal.TScrollbar'
        )
        self.imp_text.configure(
            yscrollcommand=imp_text_vsb.set,
            xscrollcommand=imp_text_hsb.set
        )

        # position scrollbar
        self.imp_text.grid(row=0, column=0, sticky="nsew", padx=(5,0), pady=(5,0))
        imp_text_vsb.grid(row=0, column=1, sticky="ns", padx=(0,5), pady=(5,0))
        imp_text_hsb.grid(row=1, column=0, sticky="ew", padx=(5,0), pady=(0,5))

        rf.rowconfigure(0, weight=1)
        rf.columnconfigure(0, weight=1)

        paned.update_idletasks()
        paned.sash_place(0, 300, 0)

    def _populate_imp(self):
        # clear tree
        for iid in self.imp_tree.get_children():
            self.imp_tree.delete(iid)

        user = self.controller.current_user_name or self.controller.current_user_email
        if not user:
            return

        base = os.path.join(self.controller.user_data_folder, "imported")
        if not os.path.isdir(base):
            return

        # one root per session folder
        for session in sorted(os.listdir(base)):
            session_path = os.path.join(base, session)
            if not os.path.isdir(session_path):
                continue
            sid = self.imp_tree.insert("", "end", text=session, open=True)
            # list every CSV, PNG, PDF, JPG
            for fn in sorted(os.listdir(session_path)):
                if fn.lower().endswith((".csv", ".png", ".jpg", ".jpeg", ".pdf")):
                    self.imp_tree.insert(sid, "end", text=fn)

    def _on_imp_select(self, _evt):
        sel = self.imp_tree.selection()
        if not sel:
            return
        item   = sel[0]
        parent = self.imp_tree.parent(item)

        # make widget editable
        self.imp_text.config(state='normal')
        self.imp_text.delete("1.0", END)

        # if they clicked the session name itself, show its latest summary
        if parent == "":
            session     = self.imp_tree.item(item, "text")
            session_dir = os.path.join(self.controller.user_data_folder, "imported", session)
            summary_csv = os.path.join(session_dir, "weekly_summary.csv")

            if os.path.exists(summary_csv):
                df   = pd.read_csv(summary_csv)
                last = df.iloc[-1]
                self.imp_text.insert(END,
                    f"Session: {session}\n\n"
                    f"Latest Weekly Summary:\n"
                    f"  Week {int(last['Week'])}: {last['Prediction']}"
                )
            else:
                self.imp_text.insert(END,
                    f"Session: {session}\n\n"
                    "No weekly_summary.csv found."
                )

            # lock and return early
            self.imp_text.config(state='disabled')
            return

        # otherwise they clicked a file under a session
        fn      = self.imp_tree.item(item, "text")
        session = self.imp_tree.item(parent, "text")
        path    = os.path.join(self.controller.user_data_folder, "imported", session, fn)
        ext     = os.path.splitext(fn)[1].lower()

        if ext == ".csv":
            df = pd.read_csv(path)
            self.imp_text.insert(END, df.head(50).to_string(index=False))

        # image imprted resized and formatted
        elif ext in (".png", ".jpg", ".jpeg"):
            img   = Image.open(path).resize((400, 400), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.imp_text.image = photo
            self.imp_text.image_create("1.0", image=photo)
            
        # pdf saved
        elif ext == ".pdf":
            self.imp_text.insert(END, f"PDF report saved at:\n{path}")

        else:
            self.imp_text.insert(END, f"Cannot preview this file type:\n{fn}")

        # lock it back down
        self.imp_text.config(state='disabled')



    def show_imported_tab(self):
        self.notebook.select(self.imp_tab)
        self._populate_imp()
        
        
    def refresh_all(self):
        
        self._populate_rt()
        self._populate_imp()    