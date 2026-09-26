import cv2

# Clean burger_angus
b2 = cv2.imread(r"frontend\public\assets\images\burger_angus.png")
# The burger is in rows 20 to 510, cols 80 to 640
b2_clean = b2[20:510, 80:640]
cv2.imwrite(r"frontend\public\assets\images\burger_angus_clean.png", b2_clean)

# Clean burger_especial
b1 = cv2.imread(r"frontend\public\assets\images\burger_especial.png")
# The burger is in rows 80 to 450, cols 140 to 580
b1_clean = b1[80:450, 140:580]
cv2.imwrite(r"frontend\public\assets\images\burger_especial_clean.png", b1_clean)

# Clean asado
asado = cv2.imread(r"frontend\public\assets\images\asado.png")
# Asado has a circular border, rows 40 to 580, cols 40 to 560
asado_clean = asado[40:580, 40:560]
cv2.imwrite(r"frontend\public\assets\images\asado_clean.png", asado_clean)

# Clean desgranado
desg = cv2.imread(r"frontend\public\assets\images\desgranado.png")
# Rows 100 to 500, cols 60 to 580
desg_clean = desg[100:500, 60:580]
cv2.imwrite(r"frontend\public\assets\images\desgranado_clean.png", desg_clean)

# Clean bebida
bebida = cv2.imread(r"frontend\public\assets\images\bebida.png")
bebida_clean = bebida[30:590, 50:580]
cv2.imwrite(r"frontend\public\assets\images\bebida_clean.png", bebida_clean)

print("Food photos cleaned successfully.")
