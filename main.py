import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
import json
import threading
import urllib.request

try:
    from PIL import Image, ImageTk, ImageOps, ImageDraw
except ImportError:
    Image = ImageTk = ImageOps = ImageDraw = None

# ============================================================
# TRIPORA | EXPLORE BEYOND
# A polished, local-first Tkinter travel planner.
# ============================================================

APP_TITLE = "Tripora | Explore Beyond"
DATA_FILE = Path.home() / ".tripora_trips.json"
ASSET_DIR = Path(__file__).resolve().parent / "assets"      # destination photos (cached)
IMAGE_DIR = ASSET_DIR / "images"                            # bundled brand images (local only)

# Public Unsplash image files. They are downloaded once into ./assets; no API key is needed.
PHOTO_URLS = {
    "bali.jpg": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=900&q=85",
    "alps.jpg": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=900&q=85",
    "kyoto.jpg": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=900&q=85",
    "santorini.jpg": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?auto=format&fit=crop&w=900&q=85",
    "manali.jpg": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=85",
    "jaipur.jpg": "https://images.unsplash.com/photo-1599661046827-dacff0c0f09a?auto=format&fit=crop&w=900&q=85",
    "munnar.jpg": "https://images.unsplash.com/photo-1602216056096-3b40cc0f9944?auto=format&fit=crop&w=900&q=85",
    "paris.jpg": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=900&q=85",
}

# Real airplane photo for the hero banner. Fetched once, then stored locally as
# assets/images/hero_airplane.jpg. You can also just drop your own photo at that path.
# If neither is available the bundled illustration (hero_airplane.png) is used.
HERO_PHOTO_URL = ("https://images.unsplash.com/photo-1436491865332-7a61a109cc05"
                  "?auto=format&fit=crop&w=2000&q=88")
HERO_PHOTO = IMAGE_DIR / "hero_airplane.jpg"
HERO_FALLBACK = IMAGE_DIR / "hero_airplane.png"

C = {
    "bg": "#F4F7FB",
    "white": "#FFFFFF",
    "text": "#172B4D",
    "muted": "#718096",
    "blue": "#356AE6",
    "blue_dark": "#2452BD",
    "blue_soft": "#EAF0FF",
    "green": "#23856D",
    "green_soft": "#E7F5EF",
    "orange": "#D8893A",
    "border": "#E3EAF3",
    "surface": "#F8FAFD",
    "danger": "#C45151",
}

DESTINATIONS = [
    {"name": "Bali, Indonesia", "region": "Beach", "price": 32000, "days": 5, "rating": 4.9,
     "tag": "MOST LOVED", "short": "Tropical calm & culture", "scene": "bali",
     "desc": "Golden sunsets, emerald rice terraces, quiet beaches and rich local culture.",
     "high": ["Ubud rice terraces", "Uluwatu sunset", "Beach cafés"]},
    {"name": "Swiss Alps", "region": "Mountains", "price": 78000, "days": 6, "rating": 4.9,
     "tag": "SCENIC ESCAPE", "short": "Peaks, lakes & fresh air", "scene": "alps",
     "desc": "Mountain villages, glassy alpine lakes, scenic rail journeys and panoramic trails.",
     "high": ["Lake Brienz", "Lauterbrunnen", "Mountain railway"]},
    {"name": "Kyoto, Japan", "region": "Culture", "price": 56000, "days": 5, "rating": 4.8,
     "tag": "CULTURE PICK", "short": "Temples & timeless streets", "scene": "kyoto",
     "desc": "Traditional streets, peaceful gardens, temples and seasonal Japanese food.",
     "high": ["Fushimi Inari", "Arashiyama", "Gion district"]},
    {"name": "Santorini, Greece", "region": "Beach", "price": 69000, "days": 4, "rating": 4.8,
     "tag": "SUNSET FAVOURITE", "short": "Whitewashed island views", "scene": "santorini",
     "desc": "White architecture, blue domes, cliffside paths and Mediterranean evenings.",
     "high": ["Oia sunset", "Caldera walk", "Local food"]},
    {"name": "Manali, India", "region": "Mountains", "price": 14000, "days": 4, "rating": 4.7,
     "tag": "BUDGET FRIENDLY", "short": "Mountain air & adventure", "scene": "manali",
     "desc": "A mountain escape with pine forests, river views, cafés and outdoor adventures.",
     "high": ["Old Manali", "Solang Valley", "Riverside cafés"]},
    {"name": "Jaipur, India", "region": "Culture", "price": 11000, "days": 3, "rating": 4.6,
     "tag": "HERITAGE TRAIL", "short": "Colourful forts & bazaars", "scene": "jaipur",
     "desc": "Grand forts, pink-hued streets, artisan markets and the flavours of Rajasthan.",
     "high": ["Amber Fort", "Hawa Mahal", "Local bazaars"]},
    {"name": "Munnar, India", "region": "Nature", "price": 12500, "days": 3, "rating": 4.7,
     "tag": "GREEN GETAWAY", "short": "Tea gardens & misty hills", "scene": "munnar",
     "desc": "Rolling tea estates, misty viewpoints, winding roads and a slower pace.",
     "high": ["Tea museum", "Top Station", "Tea garden walks"]},
    {"name": "Paris, France", "region": "City", "price": 72000, "days": 5, "rating": 4.8,
     "tag": "CITY CLASSIC", "short": "Art, cafés & architecture", "scene": "paris",
     "desc": "Art museums, elegant streets, riverside walks, bakeries and iconic landmarks.",
     "high": ["Eiffel Tower area", "Louvre district", "Seine walk"]},
]
REGIONS = ["All places", "Beach", "Mountains", "Culture", "Nature", "City"]


def money(value):
    return "₹{:,.0f}".format(value)


class Scene(tk.Canvas):
    """Lightweight destination illustrations drawn with native Tkinter shapes."""
    palettes = {
        "bali": ("#C4E0DC", "#77ADA0", "#347C70", "#F3D7A3"),
        "alps": ("#D8EAF5", "#A1C5D8", "#5D8EA5", "#FFFFFF"),
        "kyoto": ("#F5D8D0", "#D59B91", "#8E9F85", "#F8E7CA"),
        "santorini": ("#C7E4F2", "#FFFFFF", "#3F83BA", "#E8BA8E"),
        "manali": ("#D7E8E7", "#7BA9A2", "#466F69", "#E9C9A0"),
        "jaipur": ("#F5DCC4", "#E5A77C", "#C56F58", "#F9EAD8"),
        "munnar": ("#D9E9D5", "#91BE8C", "#4D8B6C", "#F2E7BF"),
        "paris": ("#D9E6F2", "#B7CBDC", "#718DAA", "#F2D8BC"),
    }

    def __init__(self, master, scene, height=130, **kwargs):
        super().__init__(master, height=height, highlightthickness=0, bd=0, **kwargs)
        self.scene = scene
        self.bind("<Configure>", self.draw)
        self.after(30, self.draw)

    def draw(self, event=None):
        if not self.winfo_exists():
            return
        self.delete("all")
        w, h = max(self.winfo_width(), 100), max(self.winfo_height(), 70)
        sky, mid, deep, sun = self.palettes.get(self.scene, self.palettes["bali"])
        self.configure(bg=sky)
        self.create_rectangle(0, 0, w, h, fill=sky, outline=sky)
        self.create_oval(w*.75, h*.09, w*.86, h*.35, fill=sun, outline=sun)

        if self.scene in ("bali", "alps", "manali", "munnar"):
            self.create_polygon(0,h*.68,w*.18,h*.24,w*.36,h*.61,w*.53,h*.18,
                                w*.77,h*.67,w,h*.4,w,h,0,h, fill=mid, outline=mid)
            self.create_polygon(0,h*.82,w*.2,h*.49,w*.4,h*.78,w*.67,h*.43,
                                w*.85,h*.68,w,h*.56,w,h,0,h, fill=deep, outline=deep)
            if self.scene == "alps":
                self.create_polygon(w*.47,h*.36,w*.53,h*.18,w*.59,h*.36,
                                    fill="#FFFFFF", outline="#FFFFFF")
            if self.scene == "bali":
                for x in (.13, .25, .77, .88):
                    self.create_line(w*x,h*.95,w*x,h*.5,fill="#2D7469",width=3)
                    self.create_arc(w*(x-.1),h*.36,w*(x+.1),h*.62,
                                    start=0,extent=180,style="arc",outline="#2D7469",width=4)
            if self.scene == "munnar":
                for y in (.68, .75, .82):
                    self.create_arc(w*.05,h*y,w*.75,h*(y+.36),start=5,extent=170,
                                    style="arc",outline="#D5E8C8",width=2)
        elif self.scene == "santorini":
            self.create_rectangle(0,h*.68,w,h,fill=mid,outline=mid)
            for x,y,ww in ((.12,.36,.18),(.34,.42,.16),(.59,.31,.2),(.79,.43,.13)):
                self.create_rectangle(w*x,h*y,w*(x+ww),h*.69,fill="#FFFFFF",outline="#FFFFFF")
                self.create_rectangle(w*(x+.04),h*(y+.1),w*(x+ww-.04),h*(y+.2),
                                      fill=sun,outline=sun)
                self.create_arc(w*(x+.04),h*(y-.08),w*(x+ww-.04),h*(y+.15),
                                start=0,extent=180,style="arc",outline=deep,width=3)
        elif self.scene == "kyoto":
            self.create_rectangle(0,h*.74,w,h,fill="#A8BEA1",outline="#A8BEA1")
            for x,y in ((.15,.4),(.43,.3),(.72,.42)):
                self.create_polygon(w*x,h*y,w*(x+.14),h*(y-.12),w*(x+.28),h*y,
                                    fill="#B75D56",outline="#B75D56")
                self.create_rectangle(w*(x+.03),h*y,w*(x+.25),h*.74,
                                      fill="#F5E5D2",outline="#F5E5D2")
                self.create_rectangle(w*(x+.12),h*(y+.1),w*(x+.17),h*.74,
                                      fill="#8E5B4E",outline="#8E5B4E")
        elif self.scene == "jaipur":
            self.create_rectangle(0,h*.76,w,h,fill="#E8B58D",outline="#E8B58D")
            self.create_rectangle(w*.23,h*.36,w*.77,h*.77,fill="#D9896B",outline="#D9896B")
            self.create_polygon(w*.18,h*.37,w*.5,h*.16,w*.82,h*.37,
                                fill="#B96550",outline="#B96550")
            for r in range(3):
                for col in range(5):
                    x, y = w*(.29+col*.095), h*(.43+r*.09)
                    self.create_rectangle(x,y,x+w*.045,y+h*.045,
                                          fill="#F8DDC4",outline="#F8DDC4")
        elif self.scene == "paris":
            self.create_rectangle(0,h*.79,w,h,fill="#9BB7CA",outline="#9BB7CA")
            self.create_polygon(w*.5,h*.12,w*.43,h*.78,w*.57,h*.78,
                                fill="#526D85",outline="#526D85")
            for y in (.38,.54,.7):
                self.create_line(w*.45,h*y,w*.55,h*y,fill="#EAF1F5",width=3)
            for x in (.12,.76):
                self.create_rectangle(w*x,h*.53,w*(x+.13),h*.8,
                                      fill="#F3E4D5",outline="#F3E4D5")


class Tripora(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1240x820")
        self.minsize(920, 650)
        self.configure(bg=C["bg"])

        self.page = "Explore"
        self.trips = self.load_trips()
        self.region = tk.StringVar(value="All places")
        self.search = tk.StringVar()
        self.nav = {}
        self.prefill = None
        self.image_refs = {}
        self.photo_cache = {}
        self.brand_cache = {}
        self._photo_download_started = False

        self.style_setup()
        self.build_shell()
        self.show_page("Explore")
        # Download photos in the background. Until then, the built-in Tkinter
        # illustrations remain visible as a graceful offline fallback.
        self.after(500, self.ensure_photos)

    def style_setup(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Tripora.TCombobox", padding=8, fieldbackground=C["white"],
                        background=C["white"], foreground=C["text"],
                        bordercolor=C["border"], arrowcolor=C["blue"])
        style.map("Tripora.TCombobox",
                  fieldbackground=[("readonly", C["white"])],
                  foreground=[("readonly", C["text"])])

    def build_shell(self):
        self.sidebar = tk.Frame(self, bg=C["white"], width=225,
                                highlightbackground=C["border"], highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=C["white"])
        brand.pack(fill="x", padx=17, pady=(22, 28))
        logo_photo = self.load_brand("tripora_logo.png", (60, 60))
        if logo_photo:
            logo = tk.Label(brand, image=logo_photo, bg=C["white"], bd=0)
            logo.image = logo_photo  # keep a reference
            logo.pack(side="left", padx=(0, 10))
        else:
            logo = tk.Canvas(brand, width=58, height=58, bg=C["white"], highlightthickness=0)
            logo.pack(side="left", padx=(0, 10))
            logo.create_oval(2, 2, 56, 56, fill=C["blue"], outline=C["blue"])
            logo.create_text(29, 29, text="✈", fill="white", font=("Arial", 27, "bold"))
        brand_text = tk.Frame(brand, bg=C["white"])
        brand_text.pack(side="left", anchor="center")
        tk.Label(brand_text, text="Tripora", bg=C["white"], fg=C["text"],
                 font=("Arial", 20, "bold")).pack(anchor="w")
        tk.Label(brand_text, text="EXPLORE BEYOND", bg=C["white"], fg=C["muted"],
                 font=("Arial", 8)).pack(anchor="w")

        tk.Label(self.sidebar, text="YOUR WORKSPACE", bg=C["white"], fg=C["muted"],
                 font=("Arial", 8, "bold")).pack(anchor="w", padx=20, pady=(0, 10))

        nav_items = [("Explore", "⌂"), ("Destinations", "◎"), ("Plan a Trip", "✧"),
                     ("My Itineraries", "▤"), ("Budget Planner", "◫")]
        for name, icon in nav_items:
            btn = tk.Button(
                self.sidebar, text=f"  {icon}     {name}", anchor="w",
                command=lambda n=name: self.show_page(n),
                relief="flat", bd=0, bg=C["white"], fg=C["muted"],
                activebackground=C["blue_soft"], activeforeground=C["blue"],
                cursor="hand2", font=("Arial", 10), padx=12, pady=13
            )
            btn.pack(fill="x", padx=11, pady=2)
            self.nav[name] = btn

        # Mountain illustration fills whatever space is left below the navigation.
        self.mountain_canvas = tk.Canvas(self.sidebar, bg=C["white"], height=10,
                                         highlightthickness=0, bd=0)
        self.mountain_canvas.pack(side="top", fill="both", expand=True)
        self.mountain_canvas.bind("<Configure>", self.paint_mountains)

        self.main = tk.Frame(self, bg=C["bg"])
        self.main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self.main, bg=C["bg"], height=76)
        header.pack(fill="x", padx=30, pady=(12, 0))
        header.pack_propagate(False)
        self.page_title = tk.Label(header, text="Explore", bg=C["bg"], fg=C["text"],
                                   font=("Arial", 23, "bold"))
        self.page_title.pack(side="left", anchor="center")
        right = tk.Frame(header, bg=C["bg"])
        right.pack(side="right", anchor="center")
        tk.Label(right, text="✦  Your next story starts here", bg=C["bg"],
                 fg=C["muted"], font=("Arial", 9)).pack(side="left", padx=(0, 14))
        tk.Label(right, text="S", bg=C["blue_soft"], fg=C["blue"],
                 font=("Arial", 11, "bold"), width=3, pady=6).pack(side="left")

        # Scrollable page area: prevents cards/forms being cut off on smaller screens.
        body = tk.Frame(self.main, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=(0, 7))
        self.page_canvas = tk.Canvas(body, bg=C["bg"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.page_canvas.yview)
        self.page_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.page_canvas.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(self.page_canvas, bg=C["bg"])
        self.content_window = self.page_canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind("<Configure>", self.update_scroll_region)
        self.page_canvas.bind("<Configure>", self.resize_content)
        self.page_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        footer = tk.Frame(self.main, bg=C["white"], height=30,
                          highlightbackground=C["border"], highlightthickness=1)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        self.status = tk.StringVar(value="Ready to explore")
        tk.Label(footer, textvariable=self.status, bg=C["white"], fg=C["muted"],
                 font=("Arial", 8), anchor="w").pack(side="left", padx=14, fill="y")
        tk.Label(footer, text="Made for curious travellers", bg=C["white"],
                 fg=C["muted"], font=("Arial", 8)).pack(side="right", padx=14)

    def ensure_photos(self):
        """Download destination photos once; the app remains usable offline."""
        if self._photo_download_started:
            return
        self._photo_download_started = True
        if Image is None:
            self.status.set("Install Pillow to display destination photos; illustrations are active")
            return

        def worker():
            ASSET_DIR.mkdir(parents=True, exist_ok=True)
            downloaded = False
            for filename, url in PHOTO_URLS.items():
                target = ASSET_DIR / filename
                if target.exists() and target.stat().st_size > 8_000:
                    continue
                try:
                    request = urllib.request.Request(
                        url, headers={"User-Agent": "TriporaTravelPlanner/1.0"}
                    )
                    with urllib.request.urlopen(request, timeout=18) as response:
                        data = response.read()
                    if len(data) > 8_000:
                        target.write_bytes(data)
                        downloaded = True
                except Exception:
                    # Network errors should never prevent Tripora from opening.
                    continue
            try:
                if not (HERO_PHOTO.exists() and HERO_PHOTO.stat().st_size > 30_000):
                    request = urllib.request.Request(
                        HERO_PHOTO_URL, headers={"User-Agent": "TriporaTravelPlanner/1.0"})
                    with urllib.request.urlopen(request, timeout=25) as response:
                        data = response.read()
                    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
                    tmp = HERO_PHOTO.with_suffix(".part")
                    tmp.write_bytes(data)
                    with Image.open(tmp) as check:   # keep only a valid image
                        check.verify()
                    tmp.replace(HERO_PHOTO)
                    downloaded = True
            except Exception:
                pass  # offline: the bundled illustration stays in place
            try:
                self.after(0, lambda: self.photos_ready(downloaded))
            except tk.TclError:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def photos_ready(self, downloaded=False):
        if not self.winfo_exists():
            return
        self.photo_cache.clear()
        self.image_refs.clear()
        self.brand_cache = {k: v for k, v in self.brand_cache.items() if k[0] != "hero"}
        if downloaded or (ASSET_DIR.exists() and any(ASSET_DIR.glob("*.jpg"))):
            self.status.set("Destination photography loaded")
            # Refresh the dashboard so the new local photos replace illustrations.
            if self.page == "Explore":
                self.show_page("Explore")
        else:
            self.status.set("Offline: showing built-in destination illustrations")

    def load_photo(self, filename, size):
        """Return a cropped Tk photo, or None when unavailable."""
        if Image is None:
            return None
        key = (filename, tuple(size))
        if key in self.photo_cache:
            return self.photo_cache[key]
        path = ASSET_DIR / filename
        if not path.exists():
            return None
        try:
            with Image.open(path) as source:
                image = ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.photo_cache[key] = photo
            self.image_refs[key] = photo
            return photo
        except Exception:
            return None

    def add_destination_visual(self, parent, scene, height=125, width=280, padx=8, pady=(8, 0)):
        photo = self.load_photo(f"{scene}.jpg", (width, height))
        if photo is not None:
            label = tk.Label(parent, image=photo, bg=C["white"], bd=0, highlightthickness=0)
            label.pack(fill="x", padx=padx, pady=pady)
            return label
        fallback = Scene(parent, scene, height=height)
        fallback.pack(fill="x", padx=padx, pady=pady)
        return fallback

    def load_brand(self, filename, size):
        """Bundled brand image resized to `size`, keeping transparency (no cropping)."""
        if Image is None:
            return None
        key = ("brand", filename, tuple(size))
        if key in self.brand_cache:
            return self.brand_cache[key]
        try:
            with Image.open(IMAGE_DIR / filename) as source:
                image = source.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            self.brand_cache[key] = ImageTk.PhotoImage(image)
            return self.brand_cache[key]
        except Exception:
            return None

    def paint_mountains(self, event=None):
        cv = self.mountain_canvas
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 20 or h < 40:
            return
        cv.delete("all")
        photo = None
        key = ("mountains", w, h)
        if Image is not None and key in self.brand_cache:
            photo = self.brand_cache[key]
        elif Image is not None:
            try:
                with Image.open(IMAGE_DIR / "sidebar_mountains.png") as source:
                    # Cover-fit, anchored to the bottom so trees/wordmark are never cropped.
                    art = ImageOps.fit(source.convert("RGB"), (w, h),
                                       method=Image.Resampling.LANCZOS, centering=(0.5, 1.0))
                # Fade the top edge into the white sidebar so there is no hard seam.
                fade = Image.linear_gradient("L").resize((w, max(1, int(h * 0.35))))
                mask = Image.new("L", (w, h), 255)
                mask.paste(fade, (0, 0))
                white = Image.new("RGB", (w, h), C["white"])
                art = Image.composite(art, white, mask)
                photo = ImageTk.PhotoImage(art)
                self.brand_cache = {k: v for k, v in self.brand_cache.items() if k[0] != "mountains"}
                self.brand_cache[key] = photo
            except Exception:
                photo = None
        if photo:
            cv.create_image(0, 0, image=photo, anchor="nw")
        else:
            cv.create_rectangle(0, 0, w, h, fill="#DCEBFA", outline="")
        # Text is drawn on the canvas so it has no background box.
        cv.create_text(20, h - 36, text="Tripora", anchor="sw", fill="white",
                       font=("Arial", 15, "bold"))
        cv.create_text(20, h - 14, text="Explore Beyond", anchor="sw", fill="white",
                       font=("Arial", 11))

    def hero_image(self, w, h, radius=20):
        """Hero photo cover-cropped (never stretched) with a left-side dark overlay and rounded corners."""
        key = ("hero", w, h)
        if key in self.brand_cache:
            return self.brand_cache[key]
        real = HERO_PHOTO.exists()
        with Image.open(HERO_PHOTO if real else HERO_FALLBACK) as source:
            # Real photo: aircraft is usually central. Illustration: aircraft sits right of centre.
            focus = 1.0 if real else (1.0 if w / h < 3.6 else 0.82)
            art = ImageOps.fit(source.convert("RGB"), (w, h),
                               method=Image.Resampling.LANCZOS, centering=(focus, 0.5)).convert("RGBA")
        # Subtle dark-blue overlay: strongest on the left behind the headline, gone by ~65% width.
        ramp = Image.linear_gradient("L").rotate(90).resize((w, h))   # 255 left -> 0 right
        ramp = ramp.point(lambda v: int(max(0, v - 70) * (0.50 if real else 0.42)))
        art.alpha_composite(Image.merge("RGBA", (
            Image.new("L", (w, h), 4), Image.new("L", (w, h), 28), Image.new("L", (w, h), 92), ramp)))
        # Rounded corners (4x supersampled mask for smooth edges).
        mask = Image.new("L", (w * 4, h * 4), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * 4 - 1, h * 4 - 1), radius * 4, fill=255)
        art.putalpha(mask.resize((w, h), Image.Resampling.LANCZOS))
        photo = ImageTk.PhotoImage(art)
        for old in [k for k in self.brand_cache if k[0] == "hero"]:
            del self.brand_cache[old]
        self.brand_cache[key] = photo
        return photo

    def add_hero_banner(self, parent):
        """Full-width airplane banner; heading and subtitle sit directly on the image."""
        hero = tk.Frame(parent, bg=C["bg"], height=238)
        hero.pack(fill="x", pady=(2, 12))
        hero.pack_propagate(False)
        banner = tk.Canvas(hero, bg=C["bg"], highlightthickness=0, bd=0)
        banner.pack(fill="both", expand=True)
        self._hero_canvas = banner
        pending = {"id": None}

        def paint_banner(event=None):
            pending["id"] = None
            if not banner.winfo_exists():
                return
            w = max(banner.winfo_width(), 400)
            # Responsive height: ~22% of width, kept between 200 and 260 px.
            h = max(200, min(260, int(w * 0.22)))
            if hero.winfo_height() != h:
                hero.configure(height=h)
            banner.delete("all")
            photo = self.hero_image(w, h) if Image is not None else None
            if photo:
                banner.create_image(0, 0, image=photo, anchor="nw")
                banner._photo = photo
            else:  # Pillow missing: plain blue fallback so text stays readable
                banner.create_rectangle(0, 0, w, h, fill="#1D5FD1", outline="")
            pad = max(28, int(w * 0.03))
            title_size = max(18, min(31, int(w / 38)))
            sub_size = max(10, min(13, int(w / 78)))
            banner.create_text(pad, h * 0.30, text="Your Trip Starts Here", anchor="w",
                               fill="white", font=("Arial", title_size, "bold"))
            banner.create_text(pad + 1, h * 0.52,
                               text="Discover destinations, plan your itinerary, and travel smarter with Tripora.",
                               anchor="nw", justify="left", fill="white", width=min(430, int(w * 0.40)),
                               font=("Arial", sub_size))
            banner.create_line(pad + 1, h * 0.80, pad + 91, h * 0.80, fill="#D7EEFF",
                               width=3, capstyle="round")

        def schedule(event=None):
            if pending["id"] is not None:
                banner.after_cancel(pending["id"])
            pending["id"] = banner.after(40, paint_banner)

        banner.bind("<Configure>", schedule)
        self.after(40, paint_banner)
        return hero

    def update_scroll_region(self, event=None):
        self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all"))

    def resize_content(self, event):
        self.page_canvas.itemconfigure(self.content_window, width=event.width)

    def on_mousewheel(self, event):
        if self.winfo_exists():
            self.page_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def reset_scroll(self):
        self.page_canvas.yview_moveto(0)

    def card(self, parent, **kwargs):
        return tk.Frame(parent, bg=C["white"], highlightbackground=C["border"],
                        highlightthickness=1, **kwargs)

    def heading(self, title, subtitle):
        frame = tk.Frame(self.content, bg=C["bg"])
        frame.pack(fill="x", pady=(2, 17))
        tk.Label(frame, text=title, bg=C["bg"], fg=C["text"],
                 font=("Arial", 16, "bold")).pack(anchor="w")
        tk.Label(frame, text=subtitle, bg=C["bg"], fg=C["muted"],
                 font=("Arial", 9)).pack(anchor="w", pady=(5, 0))

    def primary_button(self, parent, text, command, **kwargs):
        return tk.Button(parent, text=text, command=command, bg=C["blue"], fg="white",
                         activebackground=C["blue_dark"], activeforeground="white",
                         relief="flat", bd=0, padx=15, pady=9,
                         cursor="hand2", font=("Arial", 9, "bold"), **kwargs)

    def show_page(self, name):
        self.page = name
        for widget in self.content.winfo_children():
            widget.destroy()
        self.page_title.configure(text=name)
        for nav_name, button in self.nav.items():
            active = nav_name == name
            button.configure(
                bg=C["blue_soft"] if active else C["white"],
                fg=C["blue"] if active else C["muted"],
                font=("Arial", 10, "bold" if active else "normal")
            )
        pages = {
            "Explore": self.explore,
            "Destinations": self.destinations,
            "Plan a Trip": self.planner,
            "My Itineraries": self.itineraries,
            "Budget Planner": self.budget,
        }
        pages[name]()
        self.status.set(f"Viewing {name}")
        self.after_idle(self.reset_scroll)

    def explore(self):
        self.add_hero_banner(self.content)

        search_card = self.card(self.content)
        search_card.pack(fill="x", pady=(0, 18))
        tk.Label(search_card, text="Where would you like to go?",
                 bg=C["white"], fg=C["text"],
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=16, pady=(13, 7))
        row = tk.Frame(search_card, bg=C["white"])
        row.pack(fill="x", padx=15, pady=(0, 14))
        self.search.set("")
        entry = tk.Entry(row, textvariable=self.search, bg=C["surface"], fg=C["text"],
                         relief="flat", highlightthickness=1,
                         highlightbackground=C["border"], font=("Arial", 10))
        entry.pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 9))
        entry.bind("<Return>", lambda event: self.search_places())
        self.primary_button(row, "Search places", self.search_places).pack(side="left")

        heading = tk.Frame(self.content, bg=C["bg"])
        heading.pack(fill="x", pady=(0, 10))
        tk.Label(heading, text="Handpicked for you", bg=C["bg"], fg=C["text"],
                 font=("Arial", 16, "bold")).pack(side="left")
        tk.Button(heading, text="View all  →", command=lambda: self.show_page("Destinations"),
                  bg=C["bg"], fg=C["blue"], relief="flat", bd=0,
                  cursor="hand2", font=("Arial", 9, "bold")).pack(side="right")
        area = tk.Frame(self.content, bg=C["bg"])
        area.pack(fill="x")
        self.destination_cards(area, DESTINATIONS[:3], 3)

        stats = tk.Frame(self.content, bg=C["bg"])
        stats.pack(fill="x", pady=(10, 18))
        stat_items = [
            ("✦", "Thoughtful escapes", "Curated destinations"),
            ("◷", "Flexible planning", "Build trips your way"),
            ("♡", "Saved journeys", f"{len(self.trips)} trip(s) saved"),
        ]
        for icon, title, subtitle in stat_items:
            block = tk.Frame(stats, bg=C["bg"])
            block.pack(side="left", expand=True, fill="x")
            tk.Label(block, text=icon, bg=C["bg"], fg=C["blue"],
                     font=("Arial", 16, "bold")).pack(side="left", padx=(0, 8))
            info = tk.Frame(block, bg=C["bg"])
            info.pack(side="left")
            tk.Label(info, text=title, bg=C["bg"], fg=C["text"],
                     font=("Arial", 9, "bold")).pack(anchor="w")
            tk.Label(info, text=subtitle, bg=C["bg"], fg=C["muted"],
                     font=("Arial", 8)).pack(anchor="w", pady=(2, 0))

    def search_places(self):
        query = self.search.get()
        self.show_page("Destinations")
        self.dest_query.set(query)
        self.refresh_destinations()

    def destinations(self):
        self.heading(
            "Find a place that feels like you",
            "Browse destinations by travel style, then open a place to explore highlights and plan a trip."
        )
        bar = self.card(self.content)
        bar.pack(fill="x", pady=(0, 14))
        row = tk.Frame(bar, bg=C["white"])
        row.pack(fill="x", padx=14, pady=12)
        tk.Label(row, text="Travel style", bg=C["white"], fg=C["muted"],
                 font=("Arial", 9, "bold")).pack(side="left", padx=(0, 9))
        self.region.set("All places")
        combo = ttk.Combobox(row, textvariable=self.region, values=REGIONS,
                             state="readonly", width=16, style="Tripora.TCombobox")
        combo.pack(side="left", padx=(0, 16))
        combo.bind("<<ComboboxSelected>>", lambda event: self.refresh_destinations())
        tk.Label(row, text="Search", bg=C["white"], fg=C["muted"],
                 font=("Arial", 9, "bold")).pack(side="left", padx=(0, 9))
        self.dest_query = tk.StringVar(value=self.search.get())
        entry = tk.Entry(row, textvariable=self.dest_query, bg=C["surface"], fg=C["text"],
                         relief="flat", highlightthickness=1,
                         highlightbackground=C["border"], font=("Arial", 9))
        entry.pack(side="left", fill="x", expand=True, ipady=8)
        entry.bind("<KeyRelease>", lambda event: self.refresh_destinations())
        self.dest_area = tk.Frame(self.content, bg=C["bg"])
        self.dest_area.pack(fill="x")
        self.refresh_destinations()

    def refresh_destinations(self):
        if not hasattr(self, "dest_area") or not self.dest_area.winfo_exists():
            return
        for widget in self.dest_area.winfo_children():
            widget.destroy()
        region = self.region.get()
        query = self.dest_query.get().lower().strip()
        items = [
            d for d in DESTINATIONS
            if (region == "All places" or d["region"] == region)
            and (query in d["name"].lower() or query in d["short"].lower()
                 or query in d["region"].lower())
        ]
        if not items:
            tk.Label(self.dest_area, text="No destinations found. Try another keyword.",
                     bg=C["bg"], fg=C["muted"], font=("Arial", 11)).pack(pady=35)
            return
        self.destination_cards(self.dest_area, items, 3)

    def destination_cards(self, parent, items, columns=3):
        for col in range(columns):
            parent.grid_columnconfigure(col, weight=1, uniform="destination")
        for index, destination in enumerate(items):
            card = self.card(parent)
            card.grid(row=index//columns, column=index % columns,
                      sticky="nsew", padx=6, pady=7)
            self.add_destination_visual(card, destination["scene"], height=125, width=280)
            info = tk.Frame(card, bg=C["white"])
            info.pack(fill="both", expand=True, padx=12, pady=10)
            top = tk.Frame(info, bg=C["white"])
            top.pack(fill="x")
            tk.Label(top, text=destination["tag"], bg=C["green_soft"], fg=C["green"],
                     font=("Arial", 7, "bold"), padx=6, pady=4).pack(side="left")
            tk.Label(top, text=f"★ {destination['rating']}", bg=C["white"],
                     fg="#B17B32", font=("Arial", 8, "bold")).pack(side="right")
            tk.Label(info, text=destination["name"], bg=C["white"], fg=C["text"],
                     font=("Arial", 11, "bold")).pack(anchor="w", pady=(8, 2))
            tk.Label(info, text=destination["short"], bg=C["white"], fg=C["muted"],
                     font=("Arial", 8)).pack(anchor="w")
            bottom = tk.Frame(info, bg=C["white"])
            bottom.pack(fill="x", pady=(11, 0))
            price = tk.Frame(bottom, bg=C["white"])
            price.pack(side="left")
            tk.Label(price, text="STARTING BUDGET", bg=C["white"], fg=C["muted"],
                     font=("Arial", 6, "bold")).pack(anchor="w")
            tk.Label(price, text=money(destination["price"]), bg=C["white"],
                     fg=C["text"], font=("Arial", 11, "bold")).pack(anchor="w")
            tk.Button(bottom, text="Explore  →",
                      command=lambda d=destination: self.destination_detail(d),
                      bg=C["blue_soft"], fg=C["blue"], activebackground="#DCE7FF",
                      relief="flat", bd=0, padx=10, pady=7,
                      cursor="hand2", font=("Arial", 8, "bold")).pack(side="right")

    def destination_detail(self, destination):
        self.focus = destination
        for widget in self.content.winfo_children():
            widget.destroy()
        tk.Button(self.content, text="← Back to destinations",
                  command=lambda: self.show_page("Destinations"),
                  bg=C["bg"], fg=C["blue"], relief="flat", bd=0,
                  cursor="hand2", font=("Arial", 9, "bold")).pack(anchor="w", pady=(2, 12))
        hero = self.card(self.content)
        hero.pack(fill="x", pady=(0, 14))
        self.add_destination_visual(hero, destination["scene"], height=185, width=900, padx=9, pady=(9, 0))
        info = tk.Frame(hero, bg=C["white"])
        info.pack(fill="x", padx=17, pady=14)
        tk.Label(info, text=destination["name"], bg=C["white"], fg=C["text"],
                 font=("Arial", 21, "bold")).pack(anchor="w")
        tk.Label(info, text=destination["short"], bg=C["white"], fg=C["muted"],
                 font=("Arial", 10)).pack(anchor="w", pady=(4, 8))
        tk.Label(info, text=destination["desc"], bg=C["white"], fg=C["text"],
                 font=("Arial", 9), wraplength=800, justify="left").pack(anchor="w")
        tk.Label(info,
                 text=f"★ {destination['rating']}   •   Suggested duration: {destination['days']} days   •   Starting budget: {money(destination['price'])}",
                 bg=C["white"], fg=C["green"], font=("Arial", 9, "bold")).pack(anchor="w", pady=(11, 0))
        lower = tk.Frame(self.content, bg=C["bg"])
        lower.pack(fill="x", pady=(0, 15))
        highlights = self.card(lower)
        highlights.pack(side="left", fill="both", expand=True, padx=(0, 7))
        tk.Label(highlights, text="Highlights", bg=C["white"], fg=C["text"],
                 font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=(14, 8))
        for item in destination["high"]:
            tk.Label(highlights, text=f"✓  {item}", bg=C["white"], fg=C["muted"],
                     font=("Arial", 9)).pack(anchor="w", padx=15, pady=4)
        plan = self.card(lower)
        plan.pack(side="left", fill="both", expand=True, padx=(7, 0))
        tk.Label(plan, text="Make it your next trip", bg=C["white"], fg=C["text"],
                 font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=(14, 7))
        tk.Label(plan, text="Adjust your duration, budget and travel style in the planner.",
                 bg=C["white"], fg=C["muted"], font=("Arial", 9),
                 wraplength=320, justify="left").pack(anchor="w", padx=15)
        self.primary_button(plan, "Plan this trip  →",
                            lambda: self.planner_for(destination)).pack(
                                anchor="w", padx=15, pady=14
                            )

    def planner_for(self, destination):
        self.prefill = destination
        self.show_page("Plan a Trip")

    def planner(self):
        self.heading("Plan your next journey",
                     "Build a suggested itinerary and save it locally for later.")
        outer = tk.Frame(self.content, bg=C["bg"])
        outer.pack(fill="x")
        form = self.card(outer)
        form.pack(side="left", fill="both", expand=True, padx=(0, 9))
        aside = self.card(outer, width=245)
        aside.pack(side="left", fill="y", padx=(9, 0))
        aside.pack_propagate(False)

        tk.Label(form, text="TRIP DETAILS", bg=C["white"], fg=C["blue"],
                 font=("Arial", 8, "bold")).pack(anchor="w", padx=18, pady=(17, 13))
        pre = self.prefill
        self.p_dest = tk.StringVar(value=pre["name"] if pre else "Bali, Indonesia")
        self.p_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.p_days = tk.StringVar(value=str(pre["days"] if pre else 4))
        self.p_people = tk.StringVar(value="2")
        self.p_budget = tk.StringVar(value=str(pre["price"] if pre else 25000))
        self.p_pace = tk.StringVar(value="Balanced")

        self._field(form, "Destination", self.p_dest, [d["name"] for d in DESTINATIONS])
        self._field(form, "Start date (YYYY-MM-DD)", self.p_date)
        row = tk.Frame(form, bg=C["white"])
        row.pack(fill="x", padx=13, pady=(0, 10))
        self._small(row, "Days", self.p_days)
        self._small(row, "Travellers", self.p_people)
        self._small(row, "Total budget (₹)", self.p_budget)
        self._field(form, "Travel pace", self.p_pace, ["Relaxed", "Balanced", "Packed"])

        tk.Label(form, text="What do you enjoy?", bg=C["white"], fg=C["text"],
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=18, pady=(2, 7))
        self.interests = {
            name: tk.BooleanVar(value=name in ("Nature", "Local food"))
            for name in ["Nature", "Adventure", "Culture", "Local food", "Relaxation", "Photography"]
        }
        grid = tk.Frame(form, bg=C["white"])
        grid.pack(fill="x", padx=15, pady=(0, 11))
        for index, (name, variable) in enumerate(self.interests.items()):
            tk.Checkbutton(grid, text=name, variable=variable, bg=C["white"],
                           fg=C["text"], activebackground=C["white"],
                           selectcolor=C["blue_soft"], font=("Arial", 8)).grid(
                               row=index//3, column=index % 3, sticky="w", padx=4, pady=4
                           )
        self.primary_button(form, "Create my itinerary  →", self.create_trip).pack(
            anchor="w", padx=18, pady=(3, 18)
        )

        tk.Label(aside, text="YOUR PLAN AT A GLANCE", bg=C["white"], fg=C["blue"],
                 font=("Arial", 8, "bold")).pack(anchor="w", padx=15, pady=(18, 14))
        tk.Label(aside, text="Thoughtful,\nnot overpacked.", bg=C["white"], fg=C["text"],
                 font=("Arial", 15, "bold"), justify="left").pack(anchor="w", padx=15)
        tk.Label(aside,
                 text="Tripora balances discovery time with room to slow down. Your itinerary is a suggested starting point.",
                 bg=C["white"], fg=C["muted"], font=("Arial", 9),
                 wraplength=205, justify="left").pack(anchor="w", padx=15, pady=(9, 15))
        for label, value, colour in [
            ("LOCAL SAVING", "Automatic", C["green"]),
            ("TRIP STYLE", "Customizable", C["blue"]),
            ("BUDGET", "Editable", C["orange"]),
        ]:
            tk.Label(aside, text=label, bg=C["white"], fg=C["muted"],
                     font=("Arial", 8, "bold")).pack(anchor="w", padx=15, pady=(8, 1))
            tk.Label(aside, text=value, bg=C["white"], fg=colour,
                     font=("Arial", 10, "bold")).pack(anchor="w", padx=15)

    def _field(self, parent, label, variable, values=None):
        tk.Label(parent, text=label, bg=C["white"], fg=C["text"],
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=18, pady=(0, 5))
        if values:
            widget = ttk.Combobox(parent, textvariable=variable, values=values,
                                  state="readonly", style="Tripora.TCombobox")
        else:
            widget = tk.Entry(parent, textvariable=variable, bg=C["surface"],
                              fg=C["text"], relief="flat", highlightthickness=1,
                              highlightbackground=C["border"], font=("Arial", 10))
        widget.pack(fill="x", padx=18, pady=(0, 11), ipady=5 if not values else 0)

    def _small(self, parent, label, variable):
        frame = tk.Frame(parent, bg=C["white"])
        frame.pack(side="left", fill="x", expand=True, padx=4)
        tk.Label(frame, text=label, bg=C["white"], fg=C["text"],
                 font=("Arial", 8, "bold")).pack(anchor="w", pady=(0, 5))
        tk.Entry(frame, textvariable=variable, bg=C["surface"], fg=C["text"],
                 relief="flat", highlightthickness=1,
                 highlightbackground=C["border"], font=("Arial", 10)).pack(fill="x", ipady=8)

    def create_trip(self):
        try:
            days = int(self.p_days.get())
            people = int(self.p_people.get())
            budget = float(self.p_budget.get().replace(",", "").replace("₹", ""))
            start_date = self.p_date.get().strip()
            datetime.strptime(start_date, "%Y-%m-%d")
            if not 1 <= days <= 30:
                raise ValueError("Trip duration must be between 1 and 30 days.")
            if not 1 <= people <= 20:
                raise ValueError("Travellers must be between 1 and 20.")
            if budget <= 0:
                raise ValueError("Budget must be greater than zero.")
        except ValueError as error:
            messagebox.showerror("Check trip details",
                                 str(error) or "Please enter valid numbers and date.")
            return

        destination = next(
            (d for d in DESTINATIONS if d["name"] == self.p_dest.get()),
            DESTINATIONS[0]
        )
        interests = [name for name, variable in self.interests.items() if variable.get()]
        if not interests:
            interests = ["Local discovery"]
        pool = self.activity_pool(destination, interests)
        pace = self.p_pace.get()
        plan = []
        for index in range(days):
            start = index % len(pool)
            count = 1 if pace == "Relaxed" else (3 if pace == "Packed" else 2)
            activities = [pool[(start + j) % len(pool)] for j in range(count)]
            titles = ["Arrive & settle in", "Explore local highlights",
                      "A slower local day", "Your own discovery"]
            plan.append({
                "day": index + 1,
                "title": titles[index % len(titles)],
                "activities": activities
            })

        trip = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "destination": destination["name"],
            "start_date": start_date,
            "days": days,
            "travellers": people,
            "budget": round(budget),
            "pace": pace,
            "interests": interests,
            "itinerary": plan,
        }
        self.trips.insert(0, trip)
        self.save_trips()
        self.trip_detail(trip)
        self.status.set(f"Itinerary created for {destination['name']}")

    def activity_pool(self, destination, interests):
        pools = {
            "Beach": ["Sunrise beach walk", "Explore a local market", "Coastal viewpoint",
                      "Try a regional café", "Sunset by the water", "Free time by the beach"],
            "Mountains": ["Scenic viewpoint", "Mountain village walk", "Local café stop",
                          "Nature trail", "Sunset lookout", "Leisure time with mountain views"],
            "Culture": ["Visit a heritage site", "Explore traditional streets",
                        "Local food tasting", "Visit a craft market", "Garden or temple visit",
                        "Evening cultural walk"],
            "Nature": ["Morning nature walk", "Scenic viewpoint", "Explore local gardens",
                       "Try regional food", "Photography stop", "Slow afternoon outdoors"],
            "City": ["Neighbourhood walking tour", "Visit a museum or landmark",
                     "Local bakery stop", "Explore a public garden", "Riverside walk",
                     "Browse local shops"],
        }
        pool = list(pools.get(destination["region"], pools["Nature"]))
        if "Adventure" in interests:
            pool.insert(1, "Optional outdoor adventure")
        if "Photography" in interests:
            pool.append("Golden-hour photo walk")
        if "Local food" in interests:
            pool.insert(2, "Discover a local food favourite")
        if "Relaxation" in interests:
            pool.append("Unhurried relaxation time")
        return pool

    def trip_detail(self, trip):
        for widget in self.content.winfo_children():
            widget.destroy()
        tk.Button(self.content, text="← Back to itineraries",
                  command=lambda: self.show_page("My Itineraries"),
                  bg=C["bg"], fg=C["blue"], relief="flat", bd=0,
                  cursor="hand2", font=("Arial", 9, "bold")).pack(
                      anchor="w", pady=(2, 12)
                  )
        destination = next(
            (d for d in DESTINATIONS if d["name"] == trip["destination"]),
            DESTINATIONS[0]
        )
        hero = self.card(self.content)
        hero.pack(fill="x", pady=(0, 13))
        self.add_destination_visual(hero, destination["scene"], height=115, width=900, padx=9, pady=(9, 0))
        tk.Label(hero, text=trip["destination"], bg=C["white"], fg=C["text"],
                 font=("Arial", 19, "bold")).pack(anchor="w", padx=15, pady=(11, 3))
        tk.Label(hero,
                 text=f"{trip['start_date']}  ·  {trip['days']} days  ·  {trip['travellers']} traveller(s)  ·  {trip['pace']} pace",
                 bg=C["white"], fg=C["muted"], font=("Arial", 9)).pack(anchor="w", padx=15)
        tk.Label(hero, text=f"Planned budget: {money(trip['budget'])}",
                 bg=C["white"], fg=C["green"], font=("Arial", 10, "bold")).pack(
                     anchor="w", padx=15, pady=(7, 13)
                 )
        area = tk.Frame(self.content, bg=C["bg"])
        area.pack(fill="x", pady=(0, 14))
        for col in range(2):
            area.grid_columnconfigure(col, weight=1, uniform="day")
        for index, day in enumerate(trip["itinerary"]):
            day_card = self.card(area)
            day_card.grid(row=index//2, column=index % 2, sticky="nsew",
                          padx=6, pady=6)
            tk.Label(day_card, text=f"DAY {day['day']}  ·  {day['title']}",
                     bg=C["white"], fg=C["text"],
                     font=("Arial", 9, "bold")).pack(anchor="w", padx=13, pady=(13, 8))
            for activity_index, activity in enumerate(day["activities"]):
                times = ["09:00", "13:00", "17:00"]
                tk.Label(day_card,
                         text=f"{times[activity_index % 3]}   •   {activity}",
                         bg=C["white"], fg=C["muted"], font=("Arial", 8),
                         wraplength=360, justify="left").pack(
                             anchor="w", padx=13, pady=4
                         )
            tk.Frame(day_card, bg=C["white"], height=7).pack()

    def itineraries(self):
        self.heading("My itineraries",
                     "Your saved travel plans, ready to revisit and refine.")
        if not self.trips:
            empty = self.card(self.content)
            empty.pack(fill="x", pady=20)
            tk.Label(empty, text="Your travel journal starts here ✦",
                     bg=C["white"], fg=C["text"],
                     font=("Arial", 15, "bold")).pack(pady=(26, 8))
            tk.Label(empty, text="Create your first itinerary and it will appear here.",
                     bg=C["white"], fg=C["muted"], font=("Arial", 10)).pack(pady=(0, 16))
            self.primary_button(empty, "Plan a trip  →",
                                lambda: self.show_page("Plan a Trip")).pack(pady=(0, 23))
            return

        for trip in self.trips:
            item = self.card(self.content)
            item.pack(fill="x", pady=(0, 11))
            row = tk.Frame(item, bg=C["white"])
            row.pack(fill="x", padx=13, pady=13)
            destination = next(
                (d for d in DESTINATIONS if d["name"] == trip["destination"]),
                DESTINATIONS[0]
            )
            photo = self.load_photo(f"{destination['scene']}.jpg", (135, 82))
            if photo is not None:
                tk.Label(row, image=photo, bg=C["white"], bd=0).pack(
                    side="left", padx=(0, 13)
                )
            else:
                Scene(row, destination["scene"], height=82, width=135).pack(
                    side="left", padx=(0, 13)
                )
            info = tk.Frame(row, bg=C["white"])
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=trip["destination"], bg=C["white"], fg=C["text"],
                     font=("Arial", 11, "bold")).pack(anchor="w")
            tk.Label(info,
                     text=f"{trip['start_date']}  ·  {trip['days']} days  ·  {trip['travellers']} traveller(s)",
                     bg=C["white"], fg=C["muted"], font=("Arial", 8)).pack(
                         anchor="w", pady=4
                     )
            tk.Label(info, text=f"Budget {money(trip['budget'])}  ·  {trip['pace']} pace",
                     bg=C["white"], fg=C["green"],
                     font=("Arial", 9, "bold")).pack(anchor="w")
            actions = tk.Frame(row, bg=C["white"])
            actions.pack(side="right", padx=(8, 0))
            tk.Button(actions, text="View plan",
                      command=lambda t=trip: self.trip_detail(t),
                      bg=C["blue_soft"], fg=C["blue"], relief="flat", bd=0,
                      padx=11, pady=7, cursor="hand2",
                      font=("Arial", 8, "bold")).pack(pady=(0, 6))
            tk.Button(actions, text="Delete",
                      command=lambda t=trip: self.delete_trip(t["id"]),
                      bg=C["white"], fg=C["danger"], relief="flat", bd=0,
                      cursor="hand2", font=("Arial", 8)).pack()

    def delete_trip(self, trip_id):
        if not messagebox.askyesno("Delete itinerary", "Remove this saved trip?"):
            return
        self.trips = [trip for trip in self.trips if trip["id"] != trip_id]
        self.save_trips()
        self.show_page("My Itineraries")

    def budget(self):
        self.heading("Budget planner",
                     "Estimate trip costs before you go. These are planning estimates, not live quotes.")
        panel = self.card(self.content)
        panel.pack(fill="x", pady=(0, 14))
        tk.Label(panel, text="ESTIMATE YOUR TRIP", bg=C["white"], fg=C["blue"],
                 font=("Arial", 8, "bold")).pack(anchor="w", padx=17, pady=(16, 11))
        values = {
            key: tk.StringVar(value=value)
            for key, value in [
                ("days", "4"), ("people", "2"), ("stay", "2500"),
                ("food", "1000"), ("activities", "800"), ("transport", "1500")
            ]
        }
        labels = [
            ("days", "Trip days"), ("people", "Travellers"),
            ("stay", "Stay / person / day ₹"), ("food", "Food / person / day ₹"),
            ("activities", "Activities / person / day ₹"),
            ("transport", "Transport / person ₹"),
        ]
        form = tk.Frame(panel, bg=C["white"])
        form.pack(fill="x", padx=13, pady=(0, 13))
        for index, (key, label) in enumerate(labels):
            field = tk.Frame(form, bg=C["white"])
            field.grid(row=index//3, column=index % 3, sticky="ew", padx=5, pady=7)
            form.grid_columnconfigure(index % 3, weight=1)
            tk.Label(field, text=label, bg=C["white"], fg=C["muted"],
                     font=("Arial", 8, "bold")).pack(anchor="w", pady=(0, 5))
            tk.Entry(field, textvariable=values[key], bg=C["surface"], fg=C["text"],
                     relief="flat", highlightthickness=1,
                     highlightbackground=C["border"]).pack(fill="x", ipady=8)

        result = self.card(self.content)
        result.pack(fill="x")
        total_label = tk.Label(result, text="₹0", bg=C["white"], fg=C["text"],
                               font=("Arial", 27, "bold"))
        total_label.pack(anchor="w", padx=18, pady=(15, 2))
        tk.Label(result, text="Estimated total trip cost", bg=C["white"],
                 fg=C["muted"], font=("Arial", 9)).pack(anchor="w", padx=18)
        breakdown = tk.Label(result, text="", bg=C["white"], fg=C["green"],
                             font=("Arial", 9, "bold"), wraplength=850, justify="left")
        breakdown.pack(anchor="w", padx=18, pady=(9, 13))

        def calculate():
            try:
                days = int(values["days"].get())
                people = int(values["people"].get())
                stay = float(values["stay"].get())
                food = float(values["food"].get())
                activities = float(values["activities"].get())
                transport = float(values["transport"].get())
                if days < 1 or people < 1 or min(stay, food, activities, transport) < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid values",
                    "Enter positive days/travellers and non-negative costs."
                )
                return
            lodging = days * people * stay
            meals = days * people * food
            activity_cost = days * people * activities
            transport_cost = people * transport
            total = lodging + meals + activity_cost + transport_cost
            total_label.configure(text=money(total))
            breakdown.configure(
                text=f"Stay {money(lodging)}   ·   Food {money(meals)}   ·   "
                     f"Activities {money(activity_cost)}   ·   Transport {money(transport_cost)}"
            )
            self.status.set("Budget estimate updated")

        self.primary_button(panel, "Calculate estimate", calculate).pack(
            anchor="w", padx=17, pady=(0, 16)
        )
        calculate()

    def load_trips(self):
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else []
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def save_trips(self):
        try:
            DATA_FILE.write_text(
                json.dumps(self.trips, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except OSError as error:
            messagebox.showwarning("Save warning",
                                   f"Could not save locally:\n{error}")


if __name__ == "__main__":
    app = Tripora()
    app.mainloop()
