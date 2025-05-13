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


class InstructionPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Instruction box 
        instr_box = tb.Frame(self, style='Instr.TFrame', width=300, height=250)
        instr_box.place(relx=0.1, rely=0.5, anchor='w')
        tb.Label(
            instr_box,
            text=(
                "1. Keep your head inside the oval.\n"
                "2. Follow the moving dot with your eyes for 10 seconds.\n"
                "3. If box turns red, reposition head inside oval.\n\n"
                "Click Begin Test when ready."
            ),
            font=("Poppins", 12),
            foreground="#ccd6f6",
            background='#223344',
            wraplength=280,
            justify="left"
        ).place(x=10, y=10)

        # Helpers to draw the oval and dot
        def make_oval_img(w, h, outline, width):
            img = Image.new("RGBA", (w, h), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            inset = width/2
            draw.ellipse((inset, inset, w-inset, h-inset), outline=outline, width=width)
            return ImageTk.PhotoImage(img)

        def make_dot_img(r, fill):
            d = r*2
            img = Image.new("RGBA", (d, d), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((0,0,d,d), fill=fill)
            return ImageTk.PhotoImage(img)

        # Build once
        oval_w, oval_h = 200, 300
        dot_r, border_w = 20, 4
        dot_d = dot_r*2
        self.oval_img = make_oval_img(oval_w, oval_h, 'green', border_w)
        self.dot_img  = make_dot_img(dot_r, 'yellow')

        # Container for dot + oval
        container_h = dot_d + oval_h
        ovbox = tb.Frame(self, width=oval_w, height=container_h, style='TFrame')
        ovbox.place(relx=0.5, rely=0.5, anchor='center')

        # Place the dot at the top
        lbl_dot = tb.Label(ovbox, image=self.dot_img, background='#0a192f', borderwidth=0)
        lbl_dot.place(x=(oval_w - dot_d)/2, y=0, width=dot_d, height=dot_d)

        # Place the oval below it
        lbl_oval = tb.Label(ovbox, image=self.oval_img, background='#0a192f', borderwidth=0)
        lbl_oval.place(x=0, y=dot_d, width=oval_w, height=oval_h)

        # Begin Test button
        tb.Button(
            self,
            text="Begin Test",
            bootstyle="success-outline",
            takefocus=False,
            command=self._start_test
        ).place(
            relx=0.85, rely=0.5, anchor='e',
            width=260, height=80
        )
        

    def _start_test(self):
        patient_name = (
            self.controller.current_user_name
            or self.controller.current_user_email
            or "UnknownUser"
        )
        user_folder = os.path.join("deterministic_model_test", patient_name)
        os.makedirs(user_folder, exist_ok=True)

        # show test page
        test_page = self.controller.frames["TestPage"]
        self.controller.show_frame("TestPage")

        test_page.begin_countdown(5)
        
    
    # after test is finished, direct to view datapage
    def _finish_test(self):
        self.patient_name = (
        self.controller.current_user_name
        or self.controller.current_user_email
        or "UnknownUser"
        )
        view = self.controller.frames["ViewDataPage"]
        view.refresh_all()
        view._populate_rt()

        
        roots = view.rt_tree.get_children()
        if roots:
            files = view.rt_tree.get_children(roots[0])
            if files:
                view.rt_tree.selection_set(files[-1])
                view._on_rt_select(None)

       
        view.notebook.select(view.rt_tab)
        self.controller.show_frame("ViewDataPage")
