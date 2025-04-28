import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps, ImageSequence
from tkinter import BOTH, X, TOP
import tkinter.font as tkfont
import os, sys

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report

class EyeTrackingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        
        
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Poppins", size=20)

        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family="Poppins", size=20)

        heading_font = tkfont.nametofont("TkHeadingFont")
        heading_font.configure(family="Poppins Semibold", size=20)


        self.title("Cognitive Eye Tracker")
        self.geometry("1200x680")
        self.resizable(False, False)
        
        # Configure main frame style
        style = tb.Style()
        style.configure('MainFrame.TFrame', background='#0a192f')

        self.sidebar_visible = False
        self.sidebar_frame = None

        # Main container
        self.main_frame = tb.Frame(self, bootstyle='MainFrame')
        self.main_frame.pack(fill=BOTH, expand=True)

        # Initialize pages
        self.frames = {}
        for F in (HomePage, TestPage, ImportPage):
            page_name = F.__name__
            frame = F(parent=self.main_frame, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        self.frames[page_name].tkraise()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
        else:
            self.sidebar_frame = tb.Frame(self, bootstyle="dark")
            self.sidebar_frame.place(x=0, y=50, width=200, height=self.winfo_height()-50)

            tb.Label(self.sidebar_frame, text="Menu", font=("Helvetica", 14), bootstyle="inverse-dark", takefocus=False).pack(fill=X, pady=10)
            
            for text, action, style_name in [
                ("Import Data", lambda: self.show_frame("ImportPage"), "secondary"),
                ("View Data Folders", self.view_data, "secondary"),
                ("Settings", lambda: None, "secondary"),
                ("Exit", self.quit, "danger")
            ]:
                lbl = tb.Label(self.sidebar_frame, text=text, font=("Helvetica", 12), bootstyle=style_name, takefocus=False)
                lbl.pack(fill=X, pady=5, padx=10)
                lbl.bind("<Button-1>", lambda e, fn=action: fn())
                self.add_hover(lbl)

        self.sidebar_visible = not self.sidebar_visible

    def view_data(self):
        tb.messagebox.showinfo("Data Folders", "Feature to view data folders coming soon!")

    def add_hover(self, widget):
        widget.bind("<Enter>", lambda e: widget.configure(bootstyle="primary"))
        widget.bind("<Leave>", lambda e: widget.configure(
            bootstyle="danger" if widget.cget("text")=="Exit" else "secondary"
        ))

class BasePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Top navigation bar
        nav = tb.Frame(self, bootstyle="dark")
        nav.pack(fill=X, side=TOP)

        # Load icons
        burger_img = Image.open("GUI/burger.png").resize((30,30)).convert("RGBA")
        inv_b = ImageOps.invert(burger_img.convert("RGB"))
        burger_img = Image.merge("RGBA", (*inv_b.split(), burger_img.split()[3]))
        self.menu_img = ImageTk.PhotoImage(burger_img)

        home_img = Image.open("GUI/home-icon-png-31.png").resize((30,40)).convert("RGBA")
        inv_h = ImageOps.invert(home_img.convert("RGB"))
        home_img = Image.merge("RGBA", (*inv_h.split(), home_img.split()[3]))
        self.home_img = ImageTk.PhotoImage(home_img)

        # Buttons on left
        btn_menu = tb.Button(nav, image=self.menu_img, command=controller.toggle_sidebar, bootstyle="dark", takefocus=False)
        btn_menu.pack(side=LEFT, padx=5)
        self.add_hover(btn_menu)

        btn_home = tb.Button(nav, image=self.home_img, command=lambda: controller.show_frame("HomePage"), bootstyle="dark", takefocus=False)
        btn_home.pack(side=LEFT, padx=5)
        self.add_hover(btn_home)

        # Title in center
        lbl_title = tb.Label(nav, text="Cognitive Eye Tracker", font=("Poppins", 20, "bold"), foreground=("#ccd6f6"), bootstyle="inverse-dark", takefocus=False)
        
        # Center of navbar
        nav.update_idletasks()
        lbl_title.place(relx=0.5, rely=0.5, anchor='center')

    def add_hover(self, widget):
        widget.bind("<Enter>", lambda e: widget.configure(bootstyle="secondary"))
        widget.bind("<Leave>", lambda e: widget.configure(bootstyle="dark"))

class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        # Load GIF 
        self.gif_frames = []
        gif = Image.open("GUI/fractal-tree-transparent.gif")
        for frame in ImageSequence.Iterator(gif):
            f = frame.convert("RGBA").resize((300,300), Image.LANCZOS)
            self.gif_frames.append(ImageTk.PhotoImage(f))
        # Show GIF
        self.gif_label = tb.Label(self, bootstyle="dark")
        self.gif_label.pack(pady=(30,10))
        self.animate_gif(0)
 
        # Start/stop buttons
        tb.Button(self, text="Start Test", command=lambda: controller.show_frame("TestPage"),
                  bootstyle="success-outline", takefocus=False, width=20, padding=30).pack(pady=10)
        tb.Button(self, text="Exit", command=controller.quit,
                  bootstyle="danger-outline", takefocus=False, width=20, padding=30).pack(pady=10)

    def animate_gif(self, idx):
        self.gif_label.config(image=self.gif_frames[idx])
        self.after(100, self.animate_gif, (idx+1)%len(self.gif_frames))

class TestPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tb.Label(self, text="Test Page (Webcam)", font=("Helvetica",16), takefocus=False).pack(pady=20)

class ImportPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tb.Label(self, text="Import Data Page", font=("Helvetica",16), takefocus=False).pack(pady=20)

if __name__ == "__main__":
    app = EyeTrackingApp()
    app.mainloop()
