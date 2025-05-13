# import librariies
import os
import sys
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


# import real-time and uth
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report
from GUI.auth import register_user, verify_user, get_user_name


class BasePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # style for base window
        style = tb.Style()
        style.configure(
            'TransparentIcon.TButton',
            background='#0a192f',   
            borderwidth=0,
            relief='flat'
        )
        # style for base button
        style.map(
            'TransparentIcon.TButton',
            background=[('active', '#1f2d47')], 
            relief=[('pressed','flat'), ('!pressed','flat')]
        )

        # adding nav bar
        nav = tb.Frame(self)
        nav.pack(fill=X, side=TOP)

        # burger menu button used for image
        burger_img = Image.open("GUI/burger.png") \
                          .resize((30,30)) \
                          .convert("RGBA")
        inv_b = ImageOps.invert(burger_img.convert("RGB"))
        burger_img = Image.merge(
            "RGBA",
            (*inv_b.split(), burger_img.split()[3])
        )
        # linking menu buton to image
        self.menu_img = ImageTk.PhotoImage(burger_img)

        # hime menue button used for image
        home_img = Image.open("GUI/home-icon-png-31.png") \
                        .resize((30,40)) \
                        .convert("RGBA")
        inv_h = ImageOps.invert(home_img.convert("RGB"))
        home_img = Image.merge(
            "RGBA",
            (*inv_h.split(), home_img.split()[3])
        )
        # linking menu button to image
        self.home_img = ImageTk.PhotoImage(home_img)

        # creating menu button
        btn_menu = tb.Button(
            nav,
            image=self.menu_img,
            command=controller.toggle_sidebar,
            style='TransparentIcon.TButton',
            takefocus=False
        )
        # position of button
        btn_menu.pack(side=LEFT, padx=5)

        # button for home
        btn_home = tb.Button(
            nav,
            image=self.home_img,
            command=lambda: controller.show_frame("HomePage"),
            style='TransparentIcon.TButton',
            takefocus=False
        )
        # position of button
        btn_home.pack(side=LEFT, padx=5)