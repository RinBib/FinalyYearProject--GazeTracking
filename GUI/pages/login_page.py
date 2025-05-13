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



class LoginPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # defining user, name, email
        self.email_var = tk.StringVar()
        self.pw_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=False)
        self.msg_var = tk.StringVar()
        
        # Label Title for the app
        self.app_title = tb.Label(self, text="Cognitive Eye Tracker", font=("Poppins", 24), foreground="#ccd6f6")
        self.app_title.pack(pady=(30, 20))  

        # styling notebook for log in/ sign up
        self.nb = tb.Notebook(self, bootstyle="secondary.TNotebook")
        self.nb.place(relx=0.5, rely=0.25, anchor='n', width=420, height=360)

        # tab
        login_tab = tb.Frame(self.nb)
        self.nb.add(login_tab, text="Log In")
        self._build_login_grid(login_tab)

        # tab
        signup_tab = tb.Frame(self.nb)
        self.nb.add(signup_tab, text="Sign Up")
        self._build_signup_grid(signup_tab)

        tb.Label(self,
                 textvariable=self.msg_var,
                 font=("Poppins", 10),
                 foreground="red")\
          .place(relx=0.5, rely=0.8, anchor='center')

        # Tooltip library used for password auth
        # storing pop up
        self.tooltip = None  

    def _build_login_grid(self, frame):
        frame.columnconfigure(0, weight=1, minsize=120)
        frame.columnconfigure(1, weight=2, minsize=240)

        # text insert with label - email
        tb.Label(frame, text="Email:", font=("Poppins", 10))\
          .grid(row=0, column=0, sticky='e', pady=(20, 5), padx=(10, 5))
        tb.Entry(frame, textvariable=self.email_var, font=("Poppins", 10))\
          .grid(row=0, column=1, sticky='we', pady=(20, 5), padx=(5, 10))

        # text insert with label - password
        tb.Label(frame, text="Password:", font=("Poppins", 10))\
          .grid(row=1, column=0, sticky='e', pady=5, padx=(10, 5))
        tb.Entry(frame, textvariable=self.pw_var, show="*", font=("Poppins", 10))\
          .grid(row=1, column=1, sticky='we', pady=5, padx=(5, 10))

        # checkbox prototype for keep logges in
        tk.Checkbutton(
            frame,
            text="Keep me logged in",
            variable=self.remember_var,
            font=("Poppins", 8),
            bg="#273746",
            fg="#ccd6f6",
            selectcolor="#0a192f",
            activebackground="#273746",
            activeforeground="#ccd6f6",
            borderwidth=0,
            highlightthickness=0
        ).grid(row=2, column=0, columnspan=2, pady=10)


        # log in button
        tb.Button(
            frame,
            text="Log In",
            bootstyle="dark", 
            width=20,
            command=self._on_login
        ).grid(row=3, column=0, columnspan=2, pady=(67, 77))


    def _build_signup_grid(self, frame):
        frame.columnconfigure(0, weight=1, minsize=120)
        frame.columnconfigure(1, weight=2, minsize=240)

        # label and insert for name
        tb.Label(frame, text="Name:", font=("Poppins", 10))\
          .grid(row=0, column=0, sticky='e', pady=(20, 5), padx=(10, 5))
        tb.Entry(frame, textvariable=self.name_var, font=("Poppins", 10))\
          .grid(row=0, column=1, sticky='we', pady=(20, 5), padx=(5, 10))
        
        # label and insert for email
        tb.Label(frame, text="Email:", font=("Poppins", 10))\
          .grid(row=1, column=0, sticky='e', pady=5, padx=(10, 5))
        tb.Entry(frame, textvariable=self.email_var, font=("Poppins", 10))\
          .grid(row=1, column=1, sticky='we', pady=5, padx=(5, 10))

        # label for password
        tb.Label(frame, text="Password:", font=("Poppins", 10))\
          .grid(row=2, column=0, sticky='e', pady=5, padx=(10, 5))
        # password info and auth
        password_entry = tb.Entry(frame, textvariable=self.pw_var, show="*", font=("Poppins", 10))
        password_entry.grid(row=2, column=1, sticky='we', pady=5, padx=(5, 10))

        # hover for tool tip box
        password_entry.bind("<Enter>", lambda e: self.show_password_tooltip(password_entry))
        password_entry.bind("<Leave>", lambda e: self.hide_password_tooltip())

        # another keep me loggen in checkbox
        tk.Checkbutton(
            frame,
            text="Keep me logged in",
            variable=self.remember_var,
            font=("Poppins", 8),
            bg="#273746",
            fg="#ccd6f6",
            selectcolor="#0a192f",
            activebackground="#273746",
            activeforeground="#ccd6f6",
            borderwidth=0,
            highlightthickness=0
        ).grid(row=3, column=0, columnspan=2, pady=10)

        # creating button
        tb.Button(
            frame,
            text="Sign Up",
            bootstyle="dark",  
            width=20,
            command=self._on_signup
        ).grid(row=4, column=0, columnspan=2, pady=(20, 30))

    # tool tip defined
    def show_password_tooltip(self, entry_widget):
        
        if self.tooltip is None:
            self.tooltip = Toplevel(self)
            self.tooltip.wm_overrideredirect(True) 
            # position in entry password box
            self.tooltip.geometry(f"+{entry_widget.winfo_rootx()}+{entry_widget.winfo_rooty() + 30}")  
            # message box
            tooltip_label = tk.Label(self.tooltip, text="• At least 8 characters\n• At least one uppercase\n• At least one number\n• At least one special character", 
                                     font=("Poppins", 10), bg="yellow", padx=10, pady=10)
            tooltip_label.pack()

    def hide_password_tooltip(self):
        # once off entry box, tooltip box disapears
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    
    def _on_login(self):
        email = self.email_var.get().strip().lower()
        pw = self.pw_var.get().strip()

        # Verify user credentials
        if verify_user(email, pw):
            name = get_user_name(email)
            self.controller.current_user_email = email
            self.controller.current_user_name = name
            
            # show info in settings page
            self.controller.user_name_var.set(name)  
            self.controller.user_email_var.set(email)
            self.controller.user_password_var.set(self.pw_var.get())  

            # Set folder name in terms of user name and email
            self.controller.user_data_folder = os.path.join("deterministic_model_test", email)  
            self.controller.show_frame("HomePage")  # Go to the home page after login
        else:
            self.msg_var.set("Invalid email or password.")



    def _on_signup(self):
        name = self.name_var.get().strip()
        email = self.email_var.get().strip().lower()
        pw = self.pw_var.get().strip()

        # Register user and send to home page, if not, nagigate to sign up
        success, message = register_user(email, pw, name)
        if success:
            self.msg_var.set("Account created! Please log in.")
            self.nb.select(0)  
        else:
            self.msg_var.set(message)  