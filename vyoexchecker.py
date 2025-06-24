import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from threading import Thread
import random
import string
import requests

# ASCII Art and Credits
ASCII_ART = r"""
 __   ___   _  ___   _____  __
 \ \ / / | | |/ _ \ / _ \ \/ /
  \ V /| |_| | (_) |  __/>  < 
   \_/  \__, |\___/ \___/_/\_\
         __/ |                
        |___/                 
"""
AUTHOR_LINE = "meov fork with gui"

class RobloxNameChecker:
    def __init__(self):
        self.usernames = []
        self.running = False

    def gen_pat_digit(self, val=None, strict=False):
        while True:
            if val is None:
                val = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            has_digit = any(c.isdigit() for c in val)
            has_alpha = any(c.isalpha() for c in val)
            if has_digit and (not strict or has_alpha):
                return val
            val = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    def get_patterns(self):
        return {
            "1": ("X_XXX", lambda: f"{random.choice(string.ascii_uppercase)}_{''.join(random.choices(string.ascii_uppercase, k=3))}"),
            "2": ("XX_XX", lambda: f"{''.join(random.choices(string.ascii_uppercase, k=2))}_{''.join(random.choices(string.ascii_uppercase, k=2))}"),
            "3": ("XXX_X", lambda: f"{''.join(random.choices(string.ascii_uppercase, k=3))}_{random.choice(string.ascii_uppercase)}"),
            "4": ("1_X2X", lambda: self.gen_pat_digit(f"{random.choice(string.ascii_uppercase + string.digits)}_{random.choice(string.ascii_uppercase)}{random.choice(string.digits)}{random.choice(string.ascii_uppercase)}")),
            "5": ("1X_2X", lambda: self.gen_pat_digit(f"{random.choice(string.ascii_uppercase + string.digits)}{random.choice(string.ascii_uppercase)}_{random.choice(string.digits)}{random.choice(string.ascii_uppercase)}")),
            "6": ("1X2_X", lambda: self.gen_pat_digit(f"{random.choice(string.ascii_uppercase + string.digits)}{random.choice(string.ascii_uppercase)}{random.choice(string.digits)}_{random.choice(string.ascii_uppercase)}")),
            "7": ("X1X2X", lambda: self.gen_pat_digit(strict=True)),
            "8": ("Custom", None)
        }

    def rand_char(self, c):
        if c == "L":
            return random.choice(string.ascii_uppercase)
        elif c == "D":
            return random.choice(string.digits)
        return c

    def gen_from_fmt(self, fmt):
        return ''.join(self.rand_char(c) for c in fmt)

    def chk_user(self, username):
        url = f"https://auth.roblox.com/v1/usernames/validate?username={username}&birthday=2001-09-11"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return res.json().get("code")
        except Exception as e:
            print(f"Error checking {username}: {e}")
        return None

    def generate_usernames(self, choice, custom_pattern=None, num=10):
        patterns = self.get_patterns()
        if choice == "8" and custom_pattern:
            return [self.gen_from_fmt(custom_pattern) for _ in range(num)]
        elif choice in patterns:
            _, gen_fn = patterns[choice]
            return [gen_fn() for _ in range(num)]
        return []

    def save_results(self, valid, taken, censored):
        with open("valid.txt", "w") as f:
            f.write("\n".join(valid))
        with open("taken.txt", "w") as f:
            f.write("\n".join(taken))
        with open("censored.txt", "w") as f:
            f.write("\n".join(censored))

    def run_checker(self, choice, num, custom_pattern, callback):
        self.running = True
        valid, taken, censored = [], [], []

        if choice == "8":
            usernames = self.generate_usernames(choice, custom_pattern, num)
        else:
            usernames = self.generate_usernames(choice, num=num)

        for name in usernames:
            if not self.running:
                break
            code = self.chk_user(name)
            if code == 0:
                valid.append(name)
                callback(name, "valid")
            elif code == 1:
                taken.append(name)
                callback(name, "taken")
            elif code == 2:
                censored.append(name)
                callback(name, "censored")

        self.save_results(valid, taken, censored)
        callback(None, "done")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Roblox Username Checker")
        self.geometry("650x600")
        self.configure(bg="#1e1e1e")  # Dark background
        
        # Custom style
        self.style = ttk.Style()
        self.style.theme_use("alt")
        self.style.configure(".", background="#1e1e1e", foreground="#c678dd")  # Purple text
        self.style.map(".", background=[("active", "#3e3e3e")])
        
        self.checker = RobloxNameChecker()
        self.create_widgets()

    def create_widgets(self):
        # Header Frame
        header_frame = ttk.Frame(self)
        header_frame.pack(pady=10, fill="x")

        # ASCII Art
        ascii_label = tk.Label(
            header_frame,
            text=ASCII_ART,
            font=("Courier", 10, "bold"),
            fg="#c678dd",  # Purple
            bg="#1e1e1e",
            justify="center"
        )
        ascii_label.pack()

        # Author Credit
        author_label = tk.Label(
            header_frame,
            text=AUTHOR_LINE,
            font=("Courier", 8, "italic"),
            fg="#c678dd",
            bg="#1e1e1e",
            justify="center"
        )
        author_label.pack(pady=5)

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=5)

        # Pattern Selection
        self.pattern_label = ttk.Label(self, text="Select pattern:")
        self.pattern_label.pack(pady=5)

        self.pattern_var = tk.StringVar()
        self.pattern_var.trace_add("write", self.toggle_custom_entry)
        patterns = self.checker.get_patterns()
        
        pattern_frame = ttk.Frame(self)
        pattern_frame.pack(padx=20, pady=5, fill="x")
        
        for key, (desc, _) in patterns.items():
            rb = ttk.Radiobutton(
                pattern_frame,
                text=f"{key}. {desc}",
                variable=self.pattern_var,
                value=key,
                style="TRadiobutton"
            )
            rb.pack(anchor="w")

        # Custom Pattern (hidden by default)
        self.custom_frame = ttk.Frame(self)
        self.custom_label = ttk.Label(
            self.custom_frame,
            text="Enter custom pattern (L=letter, D=digit):"
        )
        self.custom_entry = ttk.Entry(self.custom_frame)
        self.custom_label.pack(pady=5)
        self.custom_entry.pack(fill="x")

        # Number of usernames
        self.num_label = ttk.Label(self, text="Number of usernames to check:")
        self.num_label.pack(pady=5)
        self.num_entry = ttk.Entry(self)
        self.num_entry.pack(fill="x", padx=20)

        # Check Button
        self.check_btn = ttk.Button(
            self,
            text="Check Availability",
            command=self.start_check
        )
        self.check_btn.pack(pady=10)

        # Results Log
        self.log = scrolledtext.ScrolledText(
            self,
            height=15,
            state="disabled",
            bg="#252526",
            fg="#c678dd",
            insertbackground="#c678dd",
            font=("Consolas", 9)
        )
        self.log.pack(fill="both", expand=True, padx=10, pady=10)

    def toggle_custom_entry(self, *args):
        if self.pattern_var.get() == "8":
            self.custom_frame.pack(pady=5, fill="x", padx=20)
        else:
            self.custom_frame.pack_forget()

    def start_check(self):
        if self.checker.running:
            messagebox.showwarning("Warning", "Check is already running!")
            return

        choice = self.pattern_var.get()
        custom_pattern = self.custom_entry.get().strip().upper() if choice == "8" else None
        
        try:
            num = int(self.num_entry.get())
            if num <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Please enter a valid number!")
            return

        self.log.configure(state="normal")
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "Starting check...\n")
        self.log.configure(state="disabled")

        Thread(
            target=self.checker.run_checker,
            args=(choice, num, custom_pattern, self.update_log)
        ).start()

    def update_log(self, name, status):
        self.log.configure(state="normal")
        if status == "done":
            self.log.insert(tk.END, "\nDone! Results saved to valid.txt, taken.txt, censored.txt\n")
        elif name:
            color = "#98c379" if status == "valid" else "#e06c75" if status == "censored" else "#abb2bf"
            self.log.tag_config(status, foreground=color)
            self.log.insert(tk.END, f"{name} - {status}\n", status)
        self.log.configure(state="disabled")
        self.log.see(tk.END)

if __name__ == "__main__":
    app = App()
    app.mainloop()
