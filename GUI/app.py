import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps
from PIL import ImageSequence  
import os, sys

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report

class EyeTrackingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title("Cognitive Eye Tracker")
        self.geometry("1200x680")
        self.resizable(False, False) 

        self.sidebar_visible = False  # Sidebar toggle state
        self.sidebar_frame = None

        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True)

        self.frames = {}
        for F in (HomePage, TestPage, ImportPage):
            page_name = F.__name__
            frame = F(parent=self.main_frame, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
            self.sidebar_visible = False
        else:
            self.sidebar_frame = tb.Frame(self, bootstyle="dark")
            self.sidebar_frame.place(x=0, y=50, width=200, height=430)  # Adjusted height for nav bar space

            tb.Label(self.sidebar_frame, text="Menu", font=("Helvetica", 14), bootstyle="inverse-dark", takefocus=False).pack(fill=X, pady=10)
            
            section = tb.Label(self.sidebar_frame, text="Import Data", font=("Helvetica", 12), takefocus=False, bootstyle="secondary")
            section.pack(fill=X, pady=5, padx=10)
            section.bind("<Button-1>", lambda e: self.show_frame("ImportPage"))
            self.add_hover(section)


            section1 = tb.Label(self.sidebar_frame, text="View Data Folders", font=("Helvetica", 12), bootstyle="secondary", takefocus=False)
            section1.pack(fill=X, pady=5, padx=10)
            section1.bind("<Button-1>", lambda e: self.view_data())
            self.add_hover(section1)

            section2 = tb.Label(self.sidebar_frame, text="Settings", font=("Helvetica", 12), bootstyle="secondary", takefocus=False)
            section2.pack(fill=X, pady=5, padx=10)
            self.add_hover(section2)

            section3 = tb.Label(self.sidebar_frame, text="Exit", font=("Helvetica", 12), bootstyle="danger", takefocus=False)
            section3.pack(fill=X, pady=5, padx=10)
            section3.bind("<Button-1>", lambda e: self.quit())
            self.add_hover(section3)

            self.sidebar_visible = True

    def view_data(self):
        tb.messagebox.showinfo("Data Folders", "Feature to view data folders coming soon!")

    def add_hover(self, widget):
        widget.bind("<Enter>", lambda e: widget.configure(bootstyle="primary"))
        widget.bind("<Leave>", lambda e: widget.configure(bootstyle="secondary" if "Exit" not in widget.cget("text") else "danger"))

class BasePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Top Navigation Bar
        nav_frame = tb.Frame(self, bootstyle="dark")
        nav_frame.pack(fill=X, side=TOP)

        burger_img = Image.open("GUI/burger.png").resize((30, 30)).convert("RGBA")
        inverted_burger = ImageOps.invert(burger_img.convert("RGB"))
        burger_img = Image.merge("RGBA", (*inverted_burger.split(), burger_img.split()[3]))  # Restore transparency
        self.menu_img = ImageTk.PhotoImage(burger_img)
        
        home_img = Image.open("GUI/home-icon-png-31.png").resize((30, 40)).convert("RGBA")
        inverted_home = ImageOps.invert(home_img.convert("RGB"))
        home_img = Image.merge("RGBA", (*inverted_home.split(), home_img.split()[3]))
        self.home_img = ImageTk.PhotoImage(home_img)

        # Burger (left)
        menu_button = tb.Button(nav_frame, image=self.menu_img, command=controller.toggle_sidebar, bootstyle="dark", takefocus=False)
        menu_button.pack(side=LEFT, padx=5)
        self.add_hover(menu_button)

        # Home (right)
        home_button = tb.Button(nav_frame, image=self.home_img, command=lambda: controller.show_frame("HomePage"), bootstyle="dark", takefocus=False)
        home_button.pack(side=LEFT)
        self.add_hover(home_button)
        
        tb.Label(self, text="Cognitive Eye Tracker", font=("Helvetica", 16), takefocus=False).pack(pady=(0, 20))

    def add_hover(self, button):
        button.bind("<Enter>", lambda e: button.configure(bootstyle="secondary"))
        button.bind("<Leave>", lambda e: button.configure(bootstyle="dark"))


    
    
class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        # Load GIF frames
        self.gif_frames = []
        gif_path = "GUI/fractal-tree-transparent.gif"
        gif = Image.open(gif_path)
        for frame in ImageSequence.Iterator(gif):
            frame = frame.convert("RGBA")
            # Resize the frame 
            resized_frame = frame.resize((300, 300), Image.LANCZOS)  # Adjust size as needed
            self.gif_frames.append(ImageTk.PhotoImage(resized_frame))


        # Display GIF
        self.gif_label = tb.Label(self, bootstyle="dark")
        self.gif_label.pack(pady=(30, 10))
        self.animate_gif(0)


        tb.Label(self, text="Cognitive Eye Tracker", font=("Helvetica", 16), takefocus=False).pack(pady=(0, 20))
        
        tb.Button(self, text="Start Test", command=lambda: controller.show_frame("TestPage"), bootstyle="success-outline", takefocus=False, width=20, padding=20).pack(pady=5)
        
        tb.Button(self, text="Exit", command=controller.quit, bootstyle="danger-outline", takefocus=False, width=20,  padding=20).pack(pady=5)
        
    def animate_gif(self, frame_index):
        frame = self.gif_frames[frame_index]
        self.gif_label.config(image=frame)
        next_index = (frame_index + 1) % len(self.gif_frames)
        self.after(100, self.animate_gif, next_index)  # Adjust speed (ms)
        
        

class TestPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tb.Label(self, text="Test Page (Webcam)", font=("Helvetica", 16), takefocus=False).pack(pady=20)

class ImportPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tb.Label(self, text="Import Data Page", font=("Helvetica", 16), takefocus=False).pack(pady=20)

if __name__ == "__main__":
    app = EyeTrackingApp()
    app.mainloop()
