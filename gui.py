import tkinter as tk
from tkinter import messagebox, simpledialog
import json, os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "storage.json")
ADMIN_PASS = os.environ.get("MTBS_ADMIN_PASS", "admin123")

# ---------------- Data Persistence ----------------
def load_db():
    if not os.path.exists(DATA_FILE):
        return seed_db()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        # ensure structure
        if "movies" not in db: db["movies"] = {}
        if "bookings" not in db: db["bookings"] = {}
        if "next_ids" not in db: db["next_ids"] = {"movie": 1, "booking": 1}
        return db
    except Exception:
        messagebox.showerror("Error", "Corrupted storage.json, resetting database.")
        return seed_db()

def seed_db():
    db = {
        "meta": {"created_at": datetime.now().isoformat()},
        "next_ids": {"movie": 1, "booking": 1},
        "movies": {},
        "bookings": {}
    }
    save_db(db)
    return db

def save_db(db):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

def gen_movie_id(db):
    nid = db["next_ids"]["movie"]
    db["next_ids"]["movie"] += 1
    return f"M{nid:03d}"

def gen_booking_id(db):
    nid = db["next_ids"]["booking"]
    db["next_ids"]["booking"] += 1
    return f"B{nid:06d}"

def make_seat_map(rows=5, cols=8):
    seats = {}
    for r in range(rows):
        row_letter = chr(ord('A') + r)
        for c in range(1, cols+1):
            seats[f"{row_letter}{c}"] = {"booked": False, "booking_id": None}
    return {"rows": rows, "cols": cols, "seats": seats}

# ---------------- GUI Application ----------------
class CineReserveGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CineReserve - Movie Ticket Booking")
        self.geometry("900x650")
        self.configure(bg="#f0f4f7")
        self.db = load_db()
        self.current_movie = None
        self.current_showtime = None
        self.selected_seats = []
        self.main_menu()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def header(self, text):
        tk.Label(self, text=text, font=("Helvetica", 22, "bold"), bg="#2c3e50", fg="white", pady=12).pack(fill="x")

    def styled_button(self, text, cmd, color="#3498db"):
        return tk.Button(self, text=text, command=cmd,
                         font=("Arial", 14), bg=color, fg="white",
                         activebackground="#2980b9", activeforeground="white",
                         relief="flat", padx=10, pady=5, width=25)

    def main_menu(self):
        self.clear()
        self.header("🎬 CineReserve - Main Menu")
        frame = tk.Frame(self, bg="#f0f4f7")
        frame.pack(pady=60)

        self.styled_button("User", self.user_menu).pack(pady=10)
        self.styled_button("Admin", self.admin_login, "#e67e22").pack(pady=10)
        self.styled_button("Exit", self.destroy, "#c0392b").pack(pady=10)

    # ---------------- User Menu ----------------
    def user_menu(self):
        self.clear()
        self.header("👤 User Menu")
        frame = tk.Frame(self, bg="#f0f4f7")
        frame.pack(pady=40)

        self.styled_button("Browse & Book Movies", self.browse_movies).pack(pady=8)
        self.styled_button("Cancel Booking", self.cancel_booking).pack(pady=8)
        self.styled_button("View My Booking", self.view_booking).pack(pady=8)
        self.styled_button("⬅ Back", self.main_menu, "#7f8c8d").pack(pady=8)

    def browse_movies(self):
        self.clear()
        self.header("🎥 Available Movies")
        frame = tk.Frame(self, bg="#f0f4f7")
        frame.pack(pady=20)

        if not self.db["movies"]:
            tk.Label(frame, text="No movies available yet.", font=("Arial", 14), bg="#f0f4f7").pack()
        else:
            for mid, movie in self.db["movies"].items():
                title = movie.get("title", "(untitled)")
                self.styled_button(title, lambda m=mid: self.show_showtimes(m)).pack(pady=5)

        self.styled_button("⬅ Back", self.user_menu, "#7f8c8d").pack(pady=20)

    def show_showtimes(self, movie_id):
        self.clear()
        self.current_movie = movie_id
        movie = self.db["movies"][movie_id]

        self.header(f"⏰ Showtimes - {movie['title']}")
        frame = tk.Frame(self, bg="#f0f4f7")
        frame.pack(pady=20)

        if not movie["showtimes"]:
            tk.Label(frame, text="No showtimes available.", font=("Arial", 14), bg="#f0f4f7").pack()
        else:
            for st in movie["showtimes"].keys():
                self.styled_button(st, lambda s=st: self.show_seat_map(s)).pack(pady=5)

        self.styled_button("⬅ Back", self.browse_movies, "#7f8c8d").pack(pady=20)

    def show_seat_map(self, showtime):
        self.clear()
        self.current_showtime = showtime
        self.selected_seats = []
        st = self.db["movies"][self.current_movie]["showtimes"][showtime]

        self.header(f"💺 Seat Selection - {self.db['movies'][self.current_movie]['title']} @ {showtime}")
        seat_frame = tk.Frame(self, bg="#f0f4f7")
        seat_frame.pack(pady=10)
        rows, cols = st["rows"], st["cols"]
        self.seat_buttons = {}

        for r in range(rows):
            for c in range(cols):
                code = f"{chr(ord('A')+r)}{c+1}"
                bcolor = "red" if st["seats"][code]["booked"] else "green"
                btn = tk.Button(seat_frame, text=code, width=4, height=2, bg=bcolor, fg="white",
                                command=lambda x=code: self.toggle_seat(x))
                btn.grid(row=r, column=c, padx=3, pady=3)
                self.seat_buttons[code] = btn

        tk.Frame(self, height=20, bg="#f0f4f7").pack()  # spacer
        self.styled_button("✅ Confirm Booking", self.confirm_booking, "#27ae60").pack(pady=5)
        self.styled_button("⬅ Back", lambda: self.show_showtimes(self.current_movie), "#7f8c8d").pack(pady=5)
        self.styled_button("🏠 Exit to Main Menu", self.main_menu, "#c0392b").pack(pady=5)

    def toggle_seat(self, code):
        st = self.db["movies"][self.current_movie]["showtimes"][self.current_showtime]
        if st["seats"][code]["booked"]:
            return
        if code in self.selected_seats:
            self.selected_seats.remove(code)
            self.seat_buttons[code]["bg"] = "green"
        else:
            self.selected_seats.append(code)
            self.seat_buttons[code]["bg"] = "yellow"

    def confirm_booking(self):
        if not self.selected_seats:
            messagebox.showerror("Error", "No seats selected")
            return
        name = simpledialog.askstring("Name", "Enter your name:")
        if not name: name = "Guest"
        bid = gen_booking_id(self.db)
        self.db["bookings"][bid] = {
            "movie_id": self.current_movie,
            "showtime": self.current_showtime,
            "seats": self.selected_seats,
            "name": name,
            "created_at": datetime.now().isoformat()
        }
        st = self.db["movies"][self.current_movie]["showtimes"][self.current_showtime]
        for s in self.selected_seats:
            st["seats"][s]["booked"] = True
            st["seats"][s]["booking_id"] = bid
        save_db(self.db)
        messagebox.showinfo("Booking Confirmed", f"Booking ID: {bid}\nSeats: {', '.join(self.selected_seats)}")
        self.main_menu()

    def cancel_booking(self):
        bid = simpledialog.askstring("Booking ID", "Enter Booking ID to cancel:")
        if not bid or bid not in self.db["bookings"]:
            messagebox.showerror("Error", "Invalid Booking ID")
            return
        booking = self.db["bookings"][bid]
        st = self.db["movies"][booking["movie_id"]]["showtimes"][booking["showtime"]]
        for s in booking["seats"]:
            st["seats"][s]["booked"] = False
            st["seats"][s]["booking_id"] = None
        del self.db["bookings"][bid]
        save_db(self.db)
        messagebox.showinfo("Cancelled", "Booking cancelled successfully")

    def view_booking(self):
        bid = simpledialog.askstring("Booking ID", "Enter Booking ID to view:")
        if not bid or bid not in self.db["bookings"]:
            messagebox.showerror("Error", "Booking not found")
            return
        b = self.db["bookings"][bid]
        movie_title = self.db["movies"].get(b["movie_id"], {}).get("title", "(removed movie)")
        info = f"Booking ID: {bid}\nName: {b['name']}\nMovie: {movie_title}\nShowtime: {b['showtime']}\nSeats: {', '.join(b['seats'])}"
        messagebox.showinfo("Booking Details", info)

    # ---------------- Admin ----------------
    def admin_login(self):
        pw = simpledialog.askstring("Admin Login", "Enter admin password:", show="*")
        if pw != ADMIN_PASS:
            messagebox.showerror("Error", "Wrong password")
            return
        self.admin_menu()

    def admin_menu(self):
        self.clear()
        self.header("🛠 Admin Panel")
        frame = tk.Frame(self, bg="#f0f4f7")
        frame.pack(pady=40)

        self.styled_button("List Movies", self.list_movies).pack(pady=8)
        self.styled_button("Add Movie", self.add_movie).pack(pady=8)
        self.styled_button("Remove Movie", self.remove_movie).pack(pady=8)
        self.styled_button("Manage Showtimes", self.manage_showtimes).pack(pady=8)
        self.styled_button("⬅ Back", self.main_menu, "#7f8c8d").pack(pady=8)

    def list_movies(self):
        self.clear()
        self.header("📋 Movie List")
        frame = tk.Frame(self, bg="#f0f4f7")
        frame.pack(pady=20)

        if not self.db["movies"]:
            tk.Label(frame, text="No movies available.", font=("Arial", 14), bg="#f0f4f7").pack()
        else:
            for mid, movie in self.db["movies"].items():
                tk.Label(frame, text=f"{mid}: {movie.get('title','(untitled)')}", font=("Arial", 14), bg="#f0f4f7").pack(anchor="w", pady=3)

        self.styled_button("⬅ Back", self.admin_menu, "#7f8c8d").pack(pady=20)

    def add_movie(self):
        title = simpledialog.askstring("Add Movie", "Movie title:")
        if not title:
            messagebox.showerror("Error", "Title cannot be empty")
            return
        mid = gen_movie_id(self.db)
        self.db["movies"][mid] = {"title": title, "showtimes": {}}
        save_db(self.db)
        messagebox.showinfo("Added", f"Movie '{title}' added with ID {mid}")

    def remove_movie(self):
        mid = simpledialog.askstring("Remove Movie", "Enter Movie ID:")
        if not mid or mid not in self.db["movies"]:
            messagebox.showerror("Error", "Invalid Movie ID")
            return
        bids_to_remove = [b_id for b_id, b in self.db["bookings"].items() if b["movie_id"] == mid]
        for b_id in bids_to_remove:
            del self.db["bookings"][b_id]
        del self.db["movies"][mid]
        save_db(self.db)
        messagebox.showinfo("Removed", f"Movie {mid} removed along with its bookings")

    def manage_showtimes(self):
        mid = simpledialog.askstring("Movie ID", "Enter Movie ID:")
        if not mid or mid not in self.db["movies"]:
            messagebox.showerror("Error", "Invalid Movie ID")
            return
        movie = self.db["movies"][mid]
        action = simpledialog.askstring("Action", "Type 'add' to add showtime or 'remove' to remove showtime:")
        if action == "add":
            st_time = simpledialog.askstring("Showtime", "Enter showtime (YYYY-MM-DD HH:MM):")
            if not st_time:
                messagebox.showerror("Error", "Invalid showtime")
                return
            movie["showtimes"][st_time] = make_seat_map()
            save_db(self.db)
            messagebox.showinfo("Added", f"Showtime {st_time} added")
        elif action == "remove":
            st_time = simpledialog.askstring("Showtime", "Enter showtime to remove:")
            if st_time not in movie["showtimes"]:
                messagebox.showerror("Error", "Invalid showtime")
                return
            bids_to_remove = [b_id for b_id, b in self.db["bookings"].items() if b["movie_id"]==mid and b["showtime"]==st_time]
            for b_id in bids_to_remove:
                del self.db["bookings"][b_id]
            del movie["showtimes"][st_time]
            save_db(self.db)
            messagebox.showinfo("Removed", f"Showtime {st_time} removed")

# ---------------- Run ----------------
if __name__ == "__main__":
    app = CineReserveGUI()
    app.mainloop()






