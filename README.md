# Tripora | Explore Beyond

A local-first travel planner built with Python and Tkinter (Pillow for images).

## Run it
```bash
python3 -m pip install -r requirements.txt
python3 main.py        # run from this folder
```
Requires Python 3.10+ with Tkinter (bundled with the python.org installers; on Debian/Ubuntu: `sudo apt install python3-tk`).

## Brand images (all local, no network needed)
| File | Used for |
|---|---|
| `assets/images/tripora_logo.png` | Blue circle + white airplane, top-left of the sidebar (the "Tripora / EXPLORE BEYOND" text is live Tk text beside it) |
| `assets/images/hero_airplane.jpg` (real photo) / `hero_airplane.png` (fallback) | On first launch with internet, a real airliner photo is downloaded to `hero_airplane.jpg` and used from then on. You can also put your own photo at that path. `hero_airplane.png` is the offline fallback illustration. Cover-cropped (never stretched), rounded corners, subtle dark overlay on the left so the headline stays readable |
| `assets/images/sidebar_mountains.png` | Mountains, pines and airplane filling the lower sidebar; fades into the white sidebar |

The destination photos still download once into `assets/` on first run, exactly as before.
To regenerate the logo / mountains / fallback hero: `python tools/generate_assets.py` (Pillow only).
To rebuild the hero from another head-on plane photo: `python tools/make_hero_from_photo.py your_photo.jpg` (writes `assets/images/hero_airplane.jpg`; higher-resolution photos look sharper).

## Notes
- Saved itineraries live in `~/.tripora_trips.json`.
- Hero height and text size scale with the window; the sidebar illustration fills whatever space is left under the navigation.
