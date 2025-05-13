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


class SettingsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.controller.user_name_var.set(self.controller.current_user_name)
        self.controller.user_email_var.set(self.controller.current_user_email)
        
        nb = tb.Notebook(self, bootstyle="secondary.TNotebook")
        nb.pack(fill=BOTH, expand=True, padx=100, pady=100)

        
        profile_tab = tb.Frame(nb)
        nb.add(profile_tab, text="Profile")
        
         
        tb.Label(profile_tab,
                 text="Name:",
                 font=("Poppins", 12),
                 foreground="#ccd6f6")\
          .grid(row=0, column=0, sticky="w", padx=10, pady=(10,5))

        tb.Label(profile_tab,
                textvariable=controller.user_name_var,
                font=("Poppins",12,"bold"),
                foreground="#ffffff")\
            .grid(row=0, column=1, padx=10, pady=(10,5))
            
        
        
        tb.Label(profile_tab,
                 text="Email:",
                 font=("Poppins", 12),
                 foreground="#ccd6f6")\
          .grid(row=1, column=0, sticky="w", padx=10, pady=5)
              

        tb.Label(profile_tab,
                textvariable=controller.user_email_var,
                font=("Poppins",12,"bold"),
                foreground="#ffffff")\
            .grid(row=1, column=1, padx=10, pady=5)


        
        tb.Label(profile_tab, text="Password:", font=("Poppins",12), foreground="#ccd6f6")\
          .grid(row=2, column=0, sticky="w", padx=10, pady=5)

        pwd_entry = tb.Entry(profile_tab,
                             textvariable=controller.user_password_var,
                             font=("Poppins",12),
                             show="*",
                             state="readonly")
        pwd_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        def toggle_password():
            if pwd_entry.cget("show") == "":
                pwd_entry.config(show="*")
                btn_toggle.config(text="Show")
            else:
                pwd_entry.config(show="")
                btn_toggle.config(text="Hide")

        btn_toggle = tb.Button(profile_tab,
                               text="Show",
                               width=5,
                               bootstyle="dark",
                               command=toggle_password)
        btn_toggle.grid(row=2, column=2, padx=(5,10), pady=5)

        # (placeholder)
        other_tab = tb.Frame(nb)
        nb.add(other_tab, text="Other")
        tb.Label(other_tab,
                 text="TBC",
                 font=("Poppins", 14),
                 foreground="#888888")\
          .pack(expand=True)

        # (placeholder)
        other_tab = tb.Frame(nb)
        nb.add(other_tab, text="Other")
        tb.Label(other_tab,
                 text="TBC",
                 font=("Poppins", 14),
                 foreground="#888888")\
          .pack(expand=True)
          
        # (placeholder)
        other_tab = tb.Frame(nb)
        nb.add(other_tab, text="Other")
        tb.Label(other_tab,
                 text="TBC",
                 font=("Poppins", 14),
                 foreground="#888888")\
          .pack(expand=True)


        
        btn = tb.Button(self,
                        text="Save Settings",
                        bootstyle="dark",
                        command=lambda: tb.messagebox.showinfo("Settings", "Saved!"))
        btn.pack(pady=10)