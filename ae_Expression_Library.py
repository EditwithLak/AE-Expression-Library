import json
import tkinter as tk
from tkinter import messagebox
import os
import re
from PIL import Image, ImageTk, ImageSequence
from tkinter import filedialog
import shutil

BG_COLOR = "#f5f5f5"

# === Tooltip Helper ===
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.enter)
        widget.bind("<Leave>", self.leave)

    def enter(self, _):
        try:
            if isinstance(self.widget, (tk.Entry, tk.Text)):
                x, y, _, _ = self.widget.bbox("insert")
            else:
                x, y = 0, 0
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 20
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            label = tk.Label(tw, text=self.text, justify='left',
                             background="#ffffe0", relief='solid',
                             borderwidth=1, font=("tahoma", "8", "normal"))
            label.pack(ipadx=1)
        except Exception as e:
            print(f"[Tooltip Error] {e}")

    def leave(self, _):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# === AE Expression Library ===
class ExpressionLibrary:
    def __init__(self, filename='expressions.json', terms_filename='ae_terms.json'):
        self.filename = filename
        self.terms_filename = terms_filename
        self.expressions = []
        self.terms = {}
        self.load_expressions()
        self.load_terms()

    def load_expressions(self):
        try:
            with open(self.filename, 'r') as file:
                data = json.load(file)
                for exp in data.get('expressions', []):
                    if 'usage' not in exp:
                        exp['usage'] = ''
                self.expressions = data.get('expressions', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Failed to load expressions: {e}")
            self.expressions = []

    def load_terms(self):
        try:
            with open(self.terms_filename, 'r') as file:
                self.terms = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Term Load Error] {e}")
            self.terms = {}

    def get_term_details(self, text):
        matches = []
        for key, value in self.terms.items():
            if key.lower() in text.lower():
                matches.append(value)
        return matches


    def save_expressions(self):
        with open(self.filename, 'w') as file:
            json.dump({"expressions": self.expressions}, file, indent=4)

    def add_expression(self, name, code, description, usage):
        if not name or not code or not description or not usage:
            messagebox.showerror("Invalid Input", "All fields are required!")
            return
        self.expressions.append({
            "name": name,
            "code": code,
            "description": description,
            "usage": usage,
            "favorite": False
        })
        self.save_expressions()

    def update_expression(self, index, name, code, description, usage):
        if not name or not code or not description or not usage:
            messagebox.showerror("Invalid Input", "All fields are required!")
            return
        self.expressions[index] = {
            "name": name,
            "code": code,
            "description": description,
            "usage": usage,
            "favorite": self.expressions[index]["favorite"]
        }
        self.save_expressions()

    def remove_expression(self, index):
        del self.expressions[index]
        self.save_expressions()

    def toggle_favorite(self, index):
        self.expressions[index]["favorite"] = not self.expressions[index]["favorite"]
        self.save_expressions()

    def filter_expressions(self, search_term="", filter_by_name=False, filter_by_favorite=False):
        return [
            exp for exp in self.expressions
            if (not filter_by_favorite or exp["favorite"]) and
               (not filter_by_name or search_term.lower() in exp["name"].lower())
        ]

    def sort_expressions(self, by="name"):
        if by == "name":
            self.expressions.sort(key=lambda exp: exp['name'].lower())
        elif by == "favorite":
            self.expressions.sort(key=lambda exp: exp['favorite'], reverse=True)
        self.save_expressions
        
# === Main UI Function ===
def open_ui():
    current_animation = None
    
    window = tk.Tk()
    window.title("AE Expression Library")
    library = ExpressionLibrary()

    def update_listbox(search_term=""):
        filter_by_name = name_filter_var.get()
        filter_by_favorite = favorite_filter_var.get()
        listbox.delete(0, tk.END)
        filtered = library.filter_expressions(search_term, filter_by_name, filter_by_favorite)
        for exp in filtered:
            favorite = "★" if exp["favorite"] else "☆"
            listbox.insert(tk.END, f"{exp['name']} {favorite}")
        expression_count_label.config(text=f"Total: {len(filtered)}")
    
    def insert_markdown(text_widget, content):
        """
        Inserts content into a Text widget, interpreting basic markdown:
        - **bold**
        - *italic*
        """
        patterns = [
        (r"\*\*(.+?)\*\*", "bold"),
        (r"\*(.+?)\*", "italic"),
        ]

        idx = 0
        while idx < len(content):
            # Find the earliest match
            match_pos = len(content)
            style = None
            match = None

            for pattern, tag in patterns:
                m = re.search(pattern, content[idx:])
                if m and m.start() + idx < match_pos:
                    match_pos = m.start() + idx
                    match = m
                    style = tag

            if match:
                start = match.start() + idx
                end = match.end() + idx
    
                # Insert text before match
                if start > idx:
                    text_widget.insert(tk.END, content[idx:start])

                # Insert matched styled text
                text_widget.insert(tk.END, match.group(1), style)
                idx = end
            else:
                # No more matches, insert the rest
                text_widget.insert(tk.END, content[idx:])
                break


    def display_term_details(expression_text):
        help_box.config(state=tk.NORMAL)
        help_box.delete("1.0", tk.END)
        terms = library.get_term_details(expression_text)
        if terms:
            for term in terms:
                help_box.insert(tk.END, f"{term.get('title', '')}\n", "title")
                help_box.insert(tk.END, "\n")
                insert_markdown(help_box, term.get("description", ""))
                help_box.insert(tk.END, "\n")
                help_box.insert(tk.END, "\nNote: ")
                insert_markdown(help_box, term.get("note", ""))
                help_box.insert(tk.END, "\n")

                if "The Basic Syntax" in term:
                    help_box.insert(tk.END, "\nThe Basic Syntax: ")
                    insert_markdown(help_box, term["The Basic Syntax"])
                    help_box.insert(tk.END, "\n")

                if "Parameters" in term:
                    help_box.insert(tk.END, "\nParameters: ")
                    insert_markdown(help_box, term["Parameters"])
                    help_box.insert(tk.END, "\n")

                help_box.insert(tk.END, "\nExample: ")
                insert_markdown(help_box, term.get("Example", ""))
                help_box.insert(tk.END, "\n\n------------------\n\n")


        help_box.config(state=tk.DISABLED)

# Preview Frame
    preview_frame = tk.LabelFrame(window, text="Preview")
    preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)

    preview_label = tk.Label(preview_frame)
    preview_label.pack()

    def show_gif_preview(expression_name):
        nonlocal current_animation

        try:
            gif_path = f"previews/{expression_name.lower().replace(' ', '_')}.gif"

            if not os.path.isfile(gif_path):
                raise FileNotFoundError(f"Preview GIF not found: {gif_path}")

            img = Image.open(gif_path)
            frames = [ImageTk.PhotoImage(frame.copy().convert("RGBA")) for frame in ImageSequence.Iterator(img)]

            def update(ind):
                nonlocal current_animation
                preview_label.configure(image=frames[ind])
                current_animation = window.after(100, update, (ind + 1) % len(frames))

            if current_animation:
                window.after_cancel(current_animation)

            update(0)

        except Exception as e:
            if current_animation:
                window.after_cancel(current_animation)
                current_animation = None
            preview_label.config(image='', text="No preview available.")
            print(f"[Preview Error] {e}")


    def on_add():
        library.add_expression(
            name_entry.get(),
            code_text.get("1.0", tk.END).strip(),
            description_text.get("1.0", tk.END).strip(),
            usage_text.get("1.0", tk.END).strip()
        )
        update_listbox()
        clear_fields()
     
    def on_upload_preview():
        expression_name = name_entry.get().strip()
        if not expression_name:
            messagebox.showwarning("Missing Name", "Please enter an expression name first.")
            return

        file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
        if file_path:
            dest_dir = os.path.join(os.getcwd(), "previews")
            os.makedirs(dest_dir, exist_ok=True)

            clean_name = expression_name.lower().replace(" ", "_")
            dest_path = os.path.join(dest_dir, f"{clean_name}.gif")

            try:
                shutil.copy(file_path, dest_path)
                messagebox.showinfo("Preview Uploaded", f"Preview uploaded as {clean_name}.gif")
            except Exception as e:
                messagebox.showerror("Upload Failed", f"Error copying file:\n{e}")

    def on_update():
        selected = listbox.curselection()
        if selected:
            idx = selected[0]
            library.update_expression(
                idx,
                name_entry.get(),
                code_text.get("1.0", tk.END).strip(),
                description_text.get("1.0", tk.END).strip(),
                usage_text.get("1.0", tk.END).strip()
            )
            update_listbox()
            clear_fields()

    def on_edit(event=None):
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("Select an Expression", "Please select an expression to edit.")
            return

        idx = selected[0]
        try:
            exp = library.expressions[idx]
        except IndexError:
            messagebox.showerror("Error", "Selected index is invalid.")
            return

        name_entry.delete(0, tk.END)
        name_entry.insert(0, exp['name'])

        code_text.config(state=tk.NORMAL)
        code_text.delete("1.0", tk.END)
        code_text.insert(tk.END, exp['code'])

        description_text.delete("1.0", tk.END)
        description_text.insert(tk.END, exp['description'])

        usage_text.delete("1.0", tk.END)
        usage_text.insert(tk.END, exp['usage'])

        display_term_details(exp['name'] + " " + exp['code'])
        show_gif_preview(exp['name'])

        btn_add.config(state=tk.DISABLED)
        btn_update.config(state=tk.NORMAL)


    def on_remove():
        selected = listbox.curselection()
        if selected:
            library.remove_expression(selected[0])
            update_listbox()
            clear_fields()

    def on_toggle_fav():
        selected = listbox.curselection()
        if selected:
            library.toggle_favorite(selected[0])
            update_listbox()

    def on_sort_name():
        library.sort_expressions("name")
        update_listbox()

    def on_sort_fav():
        library.sort_expressions("favorite")
        update_listbox()

    def move_expression_up():
        selected = listbox.curselection()
        if selected and selected[0] > 0:
            idx = selected[0]
            # Save current yview position
            yview = listbox.yview()

            # Swap entries
            library.expressions[idx - 1], library.expressions[idx] = library.expressions[idx], library.expressions[idx - 1]
            library.save_expressions()
            update_listbox()

            # Restore yview and reselect moved item
            listbox.yview_moveto(yview[0])
            listbox.selection_set(idx - 1)


    def move_expression_down():
        selected = listbox.curselection()
        if selected and selected[0] < len(library.expressions) - 1:
            idx = selected[0]
            yview = listbox.yview()

            library.expressions[idx + 1], library.expressions[idx] = library.expressions[idx], library.expressions[idx + 1]
            library.save_expressions()
            update_listbox()

            listbox.yview_moveto(yview[0])
            listbox.selection_set(idx + 1)


    def on_copy_code():
        code = code_text.get("1.0", tk.END).strip()
        if code:
            window.clipboard_clear()
            window.clipboard_append(code)
            window.update()  # Now it stays on the clipboard
            messagebox.showinfo("Copied!", "Expression code copied to clipboard.")

    def clear_fields():
        name_entry.delete(0, tk.END)
        code_text.config(state=tk.NORMAL)
        code_text.delete("1.0", tk.END)
        description_text.delete("1.0", tk.END)
        usage_text.delete("1.0", tk.END)
        help_box.config(state=tk.NORMAL)
        help_box.delete("1.0", tk.END)
        help_box.config(state=tk.DISABLED)
        btn_add.config(state=tk.NORMAL)
        btn_update.config(state=tk.DISABLED)

    def on_search(event=None):
        update_listbox(search_entry.get())

    name_filter_var = tk.BooleanVar()
    favorite_filter_var = tk.BooleanVar()

    text_font = ("Helvetica", 10)
    bold_font = ("Helvetica", 10, "bold")
    italic_font = ("Helvetica", 10, "italic")
    underline_font = ("Helvetica", 10, "underline")

    # Layout containers
    top_frame = tk.Frame(window)
    top_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    search_frame = tk.Frame(top_frame)
    search_frame.pack(pady=5)
    tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
    search_entry = tk.Entry(search_frame, width=40)
    search_entry.pack(side=tk.LEFT)
    search_entry.bind("<KeyRelease>", on_search)
    ToolTip(search_entry, "Type to search expressions")
    tk.Checkbutton(search_frame, text="Filter by Name", variable=name_filter_var).pack(side=tk.LEFT, padx=5)
    tk.Checkbutton(search_frame, text="Favorites Only", variable=favorite_filter_var).pack(side=tk.LEFT, padx=5)
    expression_count_label = tk.Label(search_frame, text="Total: 0")
    expression_count_label.pack(side=tk.LEFT, padx=10)

    listbox_frame = tk.Frame(top_frame)
    listbox_frame.pack()
    listbox_scrollbar = tk.Scrollbar(listbox_frame)
    listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox = tk.Listbox(listbox_frame, width=50, height=10, yscrollcommand=listbox_scrollbar.set)
    listbox.pack(side=tk.LEFT, pady=5)
    listbox_scrollbar.config(command=listbox.yview)
    listbox.bind('<<ListboxSelect>>', on_edit)
    
    move_buttons_frame = tk.Frame(top_frame, bg=BG_COLOR)
    move_buttons_frame.pack(pady=5)

    btn_up = tk.Button(move_buttons_frame, text="⬆ Move Up", width=12, command=move_expression_up)
    btn_up.pack(pady=2)

    btn_down = tk.Button(move_buttons_frame, text="⬇ Move Down", width=12, command=move_expression_down)
    btn_down.pack(pady=2)

    sort_frame = tk.Frame(top_frame)
    sort_frame.pack()
    tk.Button(sort_frame, text="Sort by Name", command=on_sort_name).pack(side=tk.LEFT, padx=5)
    tk.Button(sort_frame, text="Sort by Favorite", command=on_sort_fav).pack(side=tk.LEFT, padx=5)
    tk.Button(sort_frame, text="Toggle Favorite", command=on_toggle_fav).pack(side=tk.LEFT, padx=5)

    form_frame = tk.LabelFrame(top_frame, text="Expression Details")
    form_frame.pack(padx=10, pady=10)

    tk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky='e')
    name_entry = tk.Entry(form_frame, width=50, font=text_font)
    name_entry.grid(row=0, column=1)

    tk.Label(form_frame, text="Code:").grid(row=1, column=0, sticky='ne')
    code_scroll = tk.Scrollbar(form_frame)
    code_scroll.grid(row=1, column=2, sticky='ns')
    code_text = tk.Text(form_frame, width=50, height=5, font=text_font, yscrollcommand=code_scroll.set)
    code_text.grid(row=1, column=1)
    code_scroll.config(command=code_text.yview)
    code_text.tag_configure("bold", font=bold_font)

    tk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky='ne')
    desc_scroll = tk.Scrollbar(form_frame)
    desc_scroll.grid(row=2, column=2, sticky='ns')
    description_text = tk.Text(form_frame, width=50, height=3, font=text_font, yscrollcommand=desc_scroll.set)
    description_text.grid(row=2, column=1)
    desc_scroll.config(command=description_text.yview)

    tk.Label(form_frame, text="Usage:").grid(row=3, column=0, sticky='ne')
    usage_scroll = tk.Scrollbar(form_frame)
    usage_scroll.grid(row=3, column=2, sticky='ns')
    usage_text = tk.Text(form_frame, width=50, height=3, font=text_font, yscrollcommand=usage_scroll.set)
    usage_text.grid(row=3, column=1)
    usage_scroll.config(command=usage_text.yview)

    btn_frame = tk.Frame(top_frame)
    btn_frame.pack(pady=5)
    btn_add = tk.Button(btn_frame, text="Add Expression", command=on_add)
    btn_add.grid(row=0, column=0, padx=5)
    btn_update = tk.Button(btn_frame, text="Update Expression", command=on_update, state=tk.DISABLED)
    btn_update.grid(row=0, column=1, padx=5)
    btn_copy = tk.Button(btn_frame, text="Copy Code", command=on_copy_code)
    btn_copy.grid(row=0, column=2, padx=5)
    btn_upload_preview = tk.Button(btn_frame, text="Upload Preview", command=on_upload_preview)
    btn_upload_preview.grid(row=0, column=3, padx=5)
    ToolTip(btn_upload_preview, "Make sure the expression name is filled in — the preview will be saved using it as the GIF name (e.g. wiggle.gif).")

    btn_remove = tk.Button(top_frame, text="Remove Selected Expression", command=on_remove)
    btn_remove.pack(pady=5)

# === AE Help Panel on the Right ===
    help_frame = tk.LabelFrame(window, text="AE Term Help", padx=10, pady=10)
    help_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

    help_scroll = tk.Scrollbar(help_frame)
    help_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    help_box = tk.Text(
        help_frame,
        width=50,
        height=20,
        font=text_font,
        wrap="word",
        state=tk.DISABLED,
        yscrollcommand=help_scroll.set,
        spacing1=5,  # spacing above paragraphs
        spacing3=5   # spacing below paragraphs
    )
    help_box.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
    help_scroll.config(command=help_box.yview)

    # Tag styles
    help_box.tag_configure("title", font=bold_font)
    help_box.tag_configure("bold", font=bold_font)
    help_box.tag_configure("italic", font=italic_font)
    help_box.tag_configure("section", font=bold_font, foreground="blue")

    update_listbox()
    window.mainloop()

if __name__ == "__main__":
    open_ui()
