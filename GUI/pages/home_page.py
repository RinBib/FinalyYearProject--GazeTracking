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


class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Load GIF frames
        self.gif_frames = []
        gif = Image.open("GUI/fractal-tree-transparent.gif")
        for frame in ImageSequence.Iterator(gif):
            f = frame.convert("RGBA")\
                     .resize((300,300), Image.LANCZOS)
            self.gif_frames.append(ImageTk.PhotoImage(f))

        # GIF label 
        self.gif_label = tb.Label(self)
        self.gif_label.pack(pady=(30, 10))
        self.animate_gif(0)

        # Title under GIF
        tb.Label(self,
                 text="Cognitive Eye Tracker",
                 font=("Poppins", 24),
                 foreground="#ccd6f6").pack(pady=(0, 20))

        # Start / Exit
        tb.Button(self,
                  text="Start",
                  command=lambda: controller.show_frame("InstructionPage"),
                  bootstyle="success-outline",
                  takefocus=False,
                  width=20,
                  padding=30).place(relx=0.1, rely=0.85, anchor='w')
        
        tb.Button(self,
                  text="Exit",
                  command=controller.quit,
                  bootstyle="danger-outline",
                  takefocus=False,
                  width=20,
                  padding=30).place(relx=0.9, rely=0.85, anchor='e')

    def animate_gif(self, idx):
        self.gif_label.config(image=self.gif_frames[idx])
        self.after(100, self.animate_gif, (idx+1) % len(self.gif_frames))