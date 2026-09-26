import os
from PIL import Image

im1 = Image.open(r"figuras\lado1.jpeg")
W, H = im1.size

out_dir = r"figuras\extracted"
os.makedirs(out_dir, exist_ok=True)

# Let's inspect coordinates in percentages:
# Menu roughly fills x: 0.05 to 0.95, y: 0.05 to 0.95
# Logo is in top-left:
# x: 0% to 25%, y: 5% to 30%
box_logo = (int(W * 0.02), int(H * 0.05), int(W * 0.25), int(H * 0.28))
im1.crop(box_logo).save(os.path.join(out_dir, "test_logo.png"))

# Burger 1 (under logo):
# x: 6% to 24%, y: 22% to 42%
box_burger1 = (int(W * 0.06), int(H * 0.22), int(W * 0.24), int(H * 0.43))
im1.crop(box_burger1).save(os.path.join(out_dir, "test_burger1.png"))

# Burger 2 (center top):
# x: 37% to 55%, y: 5% to 24%
box_burger2 = (int(W * 0.37), int(H * 0.05), int(W * 0.55), int(H * 0.24))
im1.crop(box_burger2).save(os.path.join(out_dir, "test_burger2.png"))

# Hotdog (bottom right):
# x: 84% to 100%, y: 64% to 88%
box_perro = (int(W * 0.84), int(H * 0.64), int(W * 1.0), int(H * 0.88))
im1.crop(box_perro).save(os.path.join(out_dir, "test_perro.png"))

im2 = Image.open(r"figuras\lado2.jpeg")
W2, H2 = im2.size

# Asado (top center):
# x: 40% to 56%, y: 11% to 33%
box_asado = (int(W2 * 0.40), int(H2 * 0.11), int(W2 * 0.56), int(H2 * 0.33))
im2.crop(box_asado).save(os.path.join(out_dir, "test_asado.png"))

# Bebida (top right):
# x: 83% to 99%, y: 13% to 35%
box_bebida = (int(W2 * 0.83), int(H2 * 0.13), int(W2 * 0.99), int(H2 * 0.35))
im2.crop(box_bebida).save(os.path.join(out_dir, "test_bebida.png"))

# Desgranado (bottom left):
# x: 10% to 27%, y: 72% to 90%
box_desgranado = (int(W2 * 0.10), int(H2 * 0.72), int(W2 * 0.27), int(H2 * 0.90))
im2.crop(box_desgranado).save(os.path.join(out_dir, "test_desgranado.png"))

print("Test crops generated successfully.")
