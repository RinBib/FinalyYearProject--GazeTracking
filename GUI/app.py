import os
import sys
import shutil
from tkinter import filedialog, messagebox
import pandas as pd
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps, ImageSequence, ImageDraw
from tkinter import BOTH, X, TOP, LEFT
import tkinter.font as tkfont
from auth import register_user, verify_user, get_user_name
import tkinter as tk



# allow importing your own modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report


class LoginPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        
        style = tb.Style()
       
        style.map('Primary.TButton',
            background=[('active','#0b5ed7'),   
                        ('pressed','#0a58ca')], 
        )
        # Secondary button
        style.map('Secondary.TButton',
            background=[('active','#5c636a'),   
                        ('pressed','#4d5158')], 
        )

        
        self.email_var    = tk.StringVar()
        self.pw_var       = tk.StringVar()
        self.name_var     = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=False)
        self.msg_var      = tk.StringVar()

        
        self.nb = tb.Notebook(self, bootstyle="secondary.TNotebook")
        self.nb.place(relx=0.5, rely=0.2, anchor='n', width=420, height=360)

       
        login_tab = tb.Frame(self.nb)
        self.nb.add(login_tab, text="Log In")
        self._build_login_grid(login_tab)

        signup_tab = tb.Frame(self.nb)
        self.nb.add(signup_tab, text="Sign Up")
        self._build_signup_grid(signup_tab)

        
        tb.Label(self,
                 textvariable=self.msg_var,
                 font=("Poppins",10),
                 foreground="red")\
          .place(relx=0.5, rely=0.8, anchor='center')

    def _build_login_grid(self, frame):
        frame.columnconfigure(0, weight=1, minsize=120)
        frame.columnconfigure(1, weight=2, minsize=240)

        tb.Label(frame, text="Email:", font=("Poppins",10))\
          .grid(row=0, column=0, sticky='e', pady=(20,5), padx=(10,5))
        tb.Entry(frame, textvariable=self.email_var, font=("Poppins",10))\
          .grid(row=0, column=1, sticky='we', pady=(20,5), padx=(5,10))

        tb.Label(frame, text="Password:", font=("Poppins",10))\
          .grid(row=1, column=0, sticky='e', pady=5, padx=(10,5))
        tb.Entry(frame, textvariable=self.pw_var, show="*", font=("Poppins",10))\
          .grid(row=1, column=1, sticky='we', pady=5, padx=(5,10))

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

        tb.Button(
            frame,
            text="Log In",
            bootstyle="dark",  # uses Primary.TButton
            width=20,
            command=self._on_login
        ).grid(row=3, column=0, columnspan=2, pady=(10,20))

    def _build_signup_grid(self, frame):
        frame.columnconfigure(0, weight=1, minsize=120)
        frame.columnconfigure(1, weight=2, minsize=240)

        tb.Label(frame, text="Name:", font=("Poppins",10))\
          .grid(row=0, column=0, sticky='e', pady=(20,5), padx=(10,5))
        tb.Entry(frame, textvariable=self.name_var, font=("Poppins",10))\
          .grid(row=0, column=1, sticky='we', pady=(20,5), padx=(5,10))

        tb.Label(frame, text="Email:", font=("Poppins",10))\
          .grid(row=1, column=0, sticky='e', pady=5, padx=(10,5))
        tb.Entry(frame, textvariable=self.email_var, font=("Poppins",10))\
          .grid(row=1, column=1, sticky='we', pady=5, padx=(5,10))

        tb.Label(frame, text="Password:", font=("Poppins",10))\
          .grid(row=2, column=0, sticky='e', pady=5, padx=(10,5))
        tb.Entry(frame, textvariable=self.pw_var, show="*", font=("Poppins",10))\
          .grid(row=2, column=1, sticky='we', pady=5, padx=(5,10))

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

        tb.Button(
            frame,
            text="Sign Up",
            bootstyle="dark",  # uses Secondary.TButton
            width=20,
            command=self._on_signup
        ).grid(row=4, column=0, columnspan=2, pady=(10,20))

    def _on_login(self):
        email = self.email_var.get().strip().lower()
        pw    = self.pw_var.get().strip()
        if verify_user(email, pw):
            name = get_user_name(email)
            self.controller.current_user_email = email
            self.controller.current_user_name  = name
            self.controller.current_user_display_var.set(email)
            self.msg_var.set("")
            self.controller.show_frame("HomePage")
        else:
            self.msg_var.set("Invalid email or password.")

    def _on_signup(self):
        name  = self.name_var.get().strip()
        email = self.email_var.get().strip().lower()
        pw    = self.pw_var.get().strip()

        if not all((name, email, pw)):
            self.msg_var.set("All fields are required.")
        elif register_user(email, pw, name):
            self.msg_var.set("Account created! Please log in.")
            self.nb.select(0)
        else:
            self.msg_var.set("Email already registered.")



class BasePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # 1) Define a transparent icon-button style
        style = tb.Style()
        style.configure(
            'TransparentIcon.TButton',
            background='#0a192f',   
            borderwidth=0,
            relief='flat'
        )
        style.map(
            'TransparentIcon.TButton',
            background=[('active', '#1f2d47')],  # subtle hover shade
            relief=[('pressed','flat'), ('!pressed','flat')]
        )

        # 2) Nav bar frame (inherits TFrame → #0a192f)
        nav = tb.Frame(self)
        nav.pack(fill=X, side=TOP)

        # 3) Load & invert icons
        burger_img = Image.open("GUI/burger.png") \
                          .resize((30,30)) \
                          .convert("RGBA")
        inv_b = ImageOps.invert(burger_img.convert("RGB"))
        burger_img = Image.merge(
            "RGBA",
            (*inv_b.split(), burger_img.split()[3])
        )
        self.menu_img = ImageTk.PhotoImage(burger_img)

        home_img = Image.open("GUI/home-icon-png-31.png") \
                        .resize((30,40)) \
                        .convert("RGBA")
        inv_h = ImageOps.invert(home_img.convert("RGB"))
        home_img = Image.merge(
            "RGBA",
            (*inv_h.split(), home_img.split()[3])
        )
        self.home_img = ImageTk.PhotoImage(home_img)

        # 4) Icon buttons with zero-background style
        btn_menu = tb.Button(
            nav,
            image=self.menu_img,
            command=controller.toggle_sidebar,
            style='TransparentIcon.TButton',
            takefocus=False
        )
        btn_menu.pack(side=LEFT, padx=5)

        btn_home = tb.Button(
            nav,
            image=self.home_img,
            command=lambda: controller.show_frame("HomePage"),
            style='TransparentIcon.TButton',
            takefocus=False
        )
        btn_home.pack(side=LEFT, padx=5)

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
                 font=("Poppins", 24, "bold"),
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



class InstructionPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Instruction box 
        instr_box = tb.Frame(self,
                             style='Instr.TFrame',
                             width=300, height=200)
        instr_box.place(relx=0.1, rely=0.5, anchor='w')
        tb.Label(instr_box,
                 text=(
                     "1. Read these instructions carefully.\n"
                     "2. Keep your head inside the oval.\n"
                     "3. Follow the moving dot with your eyes.\n"
                     "4. Click Begin when ready."
                 ),
                 font=("Poppins", 12),
                 foreground="#ccd6f6",
                 background='#223344',
                 wraplength=280,
                 justify="left").place(x=10, y=10)

        # Oval + dot images
        oval_w, oval_h = 200, 300  
        dot_r = 20
        dot_d = dot_r * 2
        border_w = 4

        def make_oval_img(w, h, outline, width):
            img = Image.new("RGBA", (w, h), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            inset = width/2
            draw.ellipse(
                (inset, inset, w-inset, h-inset),
                outline=outline,
                width=width
            )
            return ImageTk.PhotoImage(img)

        def make_dot_img(r, fill):
            d = r*2
            img = Image.new("RGBA", (d, d), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((0,0,d,d), fill=fill)
            return ImageTk.PhotoImage(img)

        # build once
        self.oval_img = make_oval_img(oval_w, oval_h, 'red', border_w)
        self.dot_img  = make_dot_img(dot_r, 'yellow')

        # container exactly the size of dot + oval
        container_h = dot_d + oval_h
        ovbox = tb.Frame(self,
                         width=oval_w,
                         height=container_h,
                         style='TFrame')    
        ovbox.place(relx=0.5, rely=0.5, anchor='center')

        # place the dot at the top
        lbl_dot = tb.Label(ovbox,
                           image=self.dot_img,
                           background='#0a192f',
                           borderwidth=0)
        lbl_dot.place(x=(oval_w - dot_d)/2, y=0,
                      width=dot_d, height=dot_d)

        # place the oval below it
        lbl_oval = tb.Label(ovbox,
                            image=self.oval_img,
                            background='#0a192f',
                            borderwidth=0)
        lbl_oval.place(x=0, y=dot_d,
                       width=oval_w, height=oval_h)

        # Begin Test button 
        btn_w, btn_h = 260, 80
        tb.Button(self,
                  text="Begin Test",
                  bootstyle="success-outline",
                  takefocus=False,
                  command=self._start_test
                 ).place(relx=0.85,
                         rely=0.5,
                         anchor='e',
                         width=btn_w,
                         height=btn_h)

    def _start_test(self):
        # call real_time 
        track_eye_activity("PatientName", tracking_duration=10)
        # then flip to TestPage
        self.controller.show_frame("TestPage")



class TestPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        # placeholder
        tb.Label(
            self,
            text="Running the test…",
            font=("Poppins", 18),
            foreground="#ccd6f6"
        ).pack(pady=200)

        
class ImportPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Title
        tb.Label(self,
                 text="Import Existing Data",
                 font=("Poppins", 16),
                 foreground="#ccd6f6").pack(pady=(40,10))

        # Description
        tb.Label(self,
                 text="Select a folder containing CSV files\n(only .csv will be imported)",
                 font=("Poppins", 12),
                 foreground="#ccd6f6",
                 justify="center").pack(pady=(0,20))

        # Browse button
        tb.Button(self,
                  text="Choose Folder…",
                  bootstyle="primary-outline",
                  width=20,
                  command=self._on_browse).pack(pady=10)

        # Feedback label
        self.msg = tb.Label(self,
                            text="",
                            font=("Poppins", 12),
                            foreground="lightgreen")
        self.msg.pack(pady=(20,0))

    def _on_browse(self):
        from tkinter import filedialog, messagebox
        import os
        # Ask user for a folder
        folder = filedialog.askdirectory(title="Select folder with CSV files")
        if not folder:
            return

        # Gather CSVs
        csvs = [f for f in os.listdir(folder) if f.lower().endswith(".csv")]
        if not csvs:
            messagebox.showwarning("No CSVs Found",
                                   "That folder contains no .csv files.")
            return

        # Run your import + report pipeline
        user = self.controller.current_user_name or "UnknownUser"
        import_existing_data_and_generate_report(user, folder)

        # Show confirmation
        self.msg.config(text=f"Imported {len(csvs)} CSV file(s) for '{user}'")

        


class EyeTrackingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.current_user_email = None
        self.current_user_name = None
        self.current_user_display_var = tk.StringVar(value="")

        self.configure(background='#0a192f')

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Poppins", size=20)
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family="Poppins", size=20)
        heading_font = tkfont.nametofont("TkHeadingFont")
        heading_font.configure(family="Poppins Semibold", size=20)

        self.geometry("1200x680")
        self.resizable(False, False)

        style = tb.Style()
        style.configure('TFrame',                        background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('TLabel',                        background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('dark.TFrame',                   background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('dark.TLabel',                   background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('dark.TButton',                  background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('inverse-dark.TLabel',           background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('Outline.Success.TButton',       background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('Outline.Danger.TButton',        background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('Instr.TFrame',                  background='#223344', focusthickness=0, focuscolor='')
        style.configure('OvalBox.TFrame',                background='#273746', focusthickness=0, focuscolor='')
        style.configure('round-toggle.TCheckbutton', font=('Poppins', 8))
        
        style.configure(
            'Sidebar.TButton',
            font=('Poppins', 14),         
            background='#0a192f',         
            bordercolor='#ccd6f6',        
            foreground='#ccd6f6',
            borderwidth=1,
            relief='flat'
        )
        
        style.map(
            'Sidebar.TButton',
            background=[('active', '#0a192f')],     
            bordercolor=[('active','#ffffff')],     
            foreground=[('active','#77e4e5')]      
        )

        self.sidebar_visible = False
        self.sidebar_frame = None

        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True)

        self.frames = {}
        for F in (LoginPage, HomePage, InstructionPage, TestPage, ImportPage):
            frame = F(parent=self.main_frame, controller=self)
            self.frames[F.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        self.frames[page_name].tkraise()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
        else:
            # same width/height as before
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
            ).pack(pady=(15, 10))

            
            for text, action in [
                ("Home",              lambda: self.show_frame("HomePage")),
                ("Start Test",       lambda: self.show_frame("InstructionPage")),
                ("Import Data",       lambda: self.show_frame("ImportPage")),
                ("View Data Files",   self.view_data),
                ("Settings",          lambda: None),
                ("About",             lambda: None),
                ("Log Out",           self.logout),
                ("Exit",              self.quit)
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
        widget.bind("<Enter>", lambda e: widget.configure(bootstyle="primary"))
        widget.bind(
            "<Leave>",
            lambda e: widget.configure(
                bootstyle="danger" if widget.cget("text") == "Exit" else "secondary"
            )
        )
        
    def logout(self):
        # hide the sidebar if it's open
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
            self.sidebar_visible = False
        # clear user info
        self.current_user_email = None
        self.current_user_name  = None
        self.current_user_display_var.set("")
        # go back to login
        self.show_frame("LoginPage")




if __name__ == "__main__":
    app = EyeTrackingApp()
    app.mainloop()
