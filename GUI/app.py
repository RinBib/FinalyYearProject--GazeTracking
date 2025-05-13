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



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report
from GUI.auth import register_user, verify_user, get_user_name


# app.py
from GUI.pages.base_page        import BasePage
from GUI.pages.login_page       import LoginPage
from GUI.pages.home_page        import HomePage
from GUI.pages.instructions_page import InstructionPage
from GUI.pages.test_page        import TestPage
from GUI.pages.live_test_page   import LiveTestPage
from GUI.pages.view_data_page   import ViewDataPage
from GUI.pages.import_page      import ImportPage
from GUI.pages.settings_page    import SettingsPage
from GUI.pages.about_page       import AboutPage
from GUI.pages.legal_page       import LegalPage



class EyeTrackingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")

        
        self.current_user_email       = None
        self.current_user_name        = None
        self.user_data_folder         = None
        self.imported_folder          = None
        self.current_user_display_var = tk.StringVar(value="")
        self.user_name_var            = tk.StringVar(value="")
        self.user_email_var           = tk.StringVar(value="")
        self.user_password_var        = tk.StringVar()

        # setting window
        self.configure(background="#0a192f")
        self.geometry("1200x680")
        self.resizable(False, False)

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Poppins", size=20)
        tkfont.nametofont("TkTextFont").configure(family="Poppins", size=20)
        tkfont.nametofont("TkHeadingFont").configure(family="Poppins", size=20)

        # stlying
        style = tb.Style()

        # frames, labels, button themes
        style.configure('TFrame', background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('TLabel', background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('dark.TFrame', background='#0a192f')
        style.configure('dark.TLabel', background='#0a192f')
        style.configure('dark.TButton', background='#0a192f', focusthickness=0,focuscolor='' )
        style.configure('inverse-dark.TLabel', background='#0a192f')
        style.configure('Outline.Success.TButton', background='#0a192f')
        style.configure('Outline.Danger.TButton', background='#0a192f')
        style.configure('Instr.TFrame', background='#223344')
        style.configure('OvalBox.TFrame', background='#273746')
        style.configure('round-toggle.TCheckbutton', font=('Poppins', 8))

        style.configure('Sidebar.TButton',
            font=('Poppins', 14),
            background='#0a192f',
            bordercolor='#ccd6f6',
            foreground='#ccd6f6',
            borderwidth=1,
            relief='flat'
        )
        style.map('Sidebar.TButton',
            background=[('active', '#0a192f')],
            bordercolor=[('active', '#ffffff')],
            foreground=[('active', '#77e4e5')]
        )

        # Notebook tab styling
        style.configure("secondary.TNotebook.Tab",
            background="#223344",
            foreground="#ccd6f6"
        )
        style.map("secondary.TNotebook.Tab",
            background=[
                # hover
                ("active",   "#345473"), 
                # selected
                ("selected", "#345473"), 
                # unselected
                ("!selected","#223344")   
            ],
            foreground=[
                ("active",   "#ffffff"),
                ("selected", "#ffffff"),
                ("!selected","#ccd6f6")
            ]
        )

        # container for pages
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True)

        # placement of each page
        self.frames = {}
        for PageClass in (
            LoginPage, HomePage, InstructionPage, TestPage, LiveTestPage,
            ViewDataPage, ImportPage, SettingsPage, AboutPage, LegalPage
        ):
            page = PageClass(parent=self.main_frame, controller=self)
            self.frames[PageClass.__name__] = page
            page.place(relwidth=1, relheight=1)

        # sidebar nav
        self.sidebar_visible = False
        self.sidebar_frame   = None

        # login page is first page
        self.show_frame("LoginPage")


    def show_frame(self, page_name):
        
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "refresh_all"):
            frame.refresh_all()


    def toggle_sidebar(self):
        # hide/show sidebar
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
        else:
            self.sidebar_frame = tb.Frame(self, bootstyle="dark")
            self.sidebar_frame.place(
                x=0, y=50,
                width=200,
                height=self.winfo_height() - 50
            )
            tb.Label(
                self.sidebar_frame,
                text="Menu",
                font=("Poppins", 24),
                foreground="#ccd6f6",
                background="#0a192f"
            ).pack(pady=(15,10))

            for text, action in [
                ("Home",            lambda: self.show_frame("HomePage")),
                ("Start Test",      lambda: self.show_frame("InstructionPage")),
                ("Import Data",     lambda: self.show_frame("ImportPage")),
                ("View Data Files", lambda: self.show_frame("ViewDataPage")),
                ("Settings",        lambda: self.show_frame("SettingsPage")),
                ("About",           lambda: self.show_frame("AboutPage")),
                ("Legal",           lambda: self.show_frame("LegalPage")),
                ("Log Out",         self.logout),
                ("Exit",            self.quit)
            ]:
                btn = tb.Button(
                    self.sidebar_frame,
                    text=text,
                    style='Sidebar.TButton',
                    takefocus=False,
                    command=action
                )
                btn.pack(fill=X, padx=10, pady=6)

        self.sidebar_visible = not self.sidebar_visible


    def view_data(self):
        tb.messagebox.showinfo("Data Folders", "Feature to view data folders coming soon!")


    def add_hover(self, widget):
        # buttons can be hovered
        widget.bind("<Enter>", lambda e: widget.configure(bootstyle="primary"))
        widget.bind("<Leave>", lambda e: widget.configure(
            bootstyle="danger" if widget.cget("text") == "Exit" else "secondary"
        ))


    def logout(self):
        
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
            self.sidebar_visible = False

        self.current_user_email = None
        self.current_user_name  = None
        self.current_user_display_var.set("")
        self.user_password_var.set("")

        self.show_frame("LoginPage")



if __name__ == "__main__":
    app = EyeTrackingApp()
    app.mainloop()