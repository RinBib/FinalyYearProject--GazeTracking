def _on_rt_select(self, _evt):
        
        sel = self.rt_tree.selection()
        if not sel: return
        item = sel[0]
        if self.rt_tree.parent(item) == "":  
            return
        fn = self.rt_tree.item(item, "text")
        user = self.controller.current_user_name or self.controller.current_user_email
        base = os.path.join("deterministic_model_test", user)

        # load CSV
        df = pd.read_csv(os.path.join(base, fn))
        self.rt_text.delete("1.0", END)
        self.rt_text.insert(END, df.head(20).to_string(index=False))

        # load graphs
        for w in self.rt_graphs.winfo_children():
            w.destroy()
        rootname, _ = os.path.splitext(fn)
        imgs = []
        for img in sorted(os.listdir(base)):
            if img.startswith(rootname) and img.lower().endswith(".png"):
                path = os.path.join(base, img)
                im = Image.open(path).resize((180,180), Image.LANCZOS)
                imgs.append(ImageTk.PhotoImage(im))
        for i,photo in enumerate(imgs):
            lbl = tk.Label(self.rt_graphs, image=photo)
            lbl.image = photo
            lbl.grid(row=i//3, column=i%3, padx=5, pady=5)