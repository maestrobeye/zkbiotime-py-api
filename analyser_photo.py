from PIL import Image
import os

path = r"C:\ZKBioTime\auth_files\photo\2.jpg"

print("================================")
print("ANALYSE PHOTO")
print("================================")

print("Existe :", os.path.exists(path))

if not os.path.exists(path):
    exit()

size = os.path.getsize(path)

print("Taille :", size, "octets")
print("Taille :", round(size / 1024, 2), "Ko")

with open(path, "rb") as f:
    data = f.read()

print("Header HEX :", data[:32].hex(" "))
print("Footer HEX :", data[-32:].hex(" "))

try:
    image = Image.open(path)

    print("Format :", image.format)
    print("Largeur :", image.width)
    print("Hauteur :", image.height)
    print("Mode :", image.mode)

    image.verify()

    print("Pillow : OK")

except Exception as e:
    print("Pillow : ERREUR")
    print(str(e))
