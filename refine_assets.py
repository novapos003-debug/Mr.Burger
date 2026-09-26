import os
from PIL import Image, ImageFilter

im1 = Image.open(r"figuras\lado1.jpeg")
W1, H1 = im1.size

out_dir = r"frontend\public\assets\images"
os.makedirs(out_dir, exist_ok=True)

# 1. LOGO REFINEMENT
# In test_logo: (int(W*0.02), int(H*0.05), int(W*0.25), int(H*0.28))
# Let's crop exact logo region:
logo_crop = im1.crop((70, 200, 930, 800))
logo_crop.save(os.path.join(out_dir, "logo_raw.png"))

# Let's also create an isolated/clean transparent logo if possible, or high-contrast clean logo:
# Convert to RGBA
logo_rgba = logo_crop.convert("RGBA")
pixels = logo_rgba.load()
w_l, h_l = logo_rgba.size

# Notice the background is dark charcoal / near black (RGB around 20-35, 20-35, 20-35)
# Let's make near-black pixels transparent or keep a dark-badge version and transparent version
clean_logo = Image.new("RGBA", (w_l, h_l), (0, 0, 0, 0))
clean_pixels = clean_logo.load()

# Also let's inspect the bottom edge: if y > h_l - 60 and there's the orange arc, we can erase it
for y in range(h_l):
    for x in range(w_l):
        r, g, b, a = pixels[x, y]
        # Check if it's the bottom orange arc (around y > 520, where orange arc starts)
        # The swoosh underline has yellow (high R, high G, low B) and red (high R, low G, low B)
        # Orange arc is an isolated line near the bottom
        if y > 530 and (r > 130 and g > 50 and b < 50 and x > 250 and x < 800):
            # Might be orange circle arc below the swoosh
            # Check if this pixel is part of the arc vs the swoosh:
            pass
        
        # Detect dark background: r < 55 and g < 55 and b < 55
        if r < 55 and g < 55 and b < 55:
            clean_pixels[x, y] = (0, 0, 0, 0)
        else:
            clean_pixels[x, y] = (r, g, b, 255)

clean_logo.save(os.path.join(out_dir, "logo_transparent_test.png"))

# 2. BURGERS
# Burger 1 (Especial con queso fundido)
# Let's crop centered square
b1_crop = im1.crop((280, 720, 960, 1400))
b1_crop.save(os.path.join(out_dir, "burger_especial.png"))

# Burger 2 (Angus / Doble)
b2_crop = im1.crop((1500, 160, 2220, 880))
b2_crop.save(os.path.join(out_dir, "burger_angus.png"))

# Perro Caliente
perro_crop = im1.crop((3420, 1980, 4030, 2660))
perro_crop.save(os.path.join(out_dir, "perro_caliente.png"))

# LADO 2 ASSETS
im2 = Image.open(r"figuras\lado2.jpeg")
# Asado
asado_crop = im2.crop((1650, 360, 2250, 980))
asado_crop.save(os.path.join(out_dir, "asado.png"))

# Bebida
bebida_crop = im2.crop((3370, 420, 3980, 1060))
bebida_crop.save(os.path.join(out_dir, "bebida.png"))

# Desgranado
desgranado_crop = im2.crop((440, 2250, 1080, 2800))
desgranado_crop.save(os.path.join(out_dir, "desgranado.png"))

print("Refined assets saved to", out_dir)
