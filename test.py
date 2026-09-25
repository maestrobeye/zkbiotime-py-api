# import sys
# import os

# BIOTIME = r"C:\ZKBioTime"

# sys.path.insert(0, BIOTIME)

# os.environ.setdefault(
#     "DJANGO_SETTINGS_MODULE",
#     "mysite.settings"
# )

# import django
# django.setup()

# from mysite.tools.image_utils import encrypt_image

# print("encrypt_image =", encrypt_image)


# from mysite.tools.image_utils import encrypt_image, decrypt_image

# SOURCE = r"C:\Users\User\Desktop\ZK-BD\test.jpg"

# data = encrypt_image(SOURCE, is_path=True)

# with open(r"C:\ZKBioTime\auth_files\photo\test1.jpg", "wb") as f:
#     f.write(data)
import sys
import os
from PIL import Image

BIOTIME = r"C:\ZKBioTime"

sys.path.insert(0, BIOTIME)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "mysite.settings"
)

import django
django.setup()

from mysite.tools.image_utils import encrypt_image


SOURCE = r"C:\Users\User\Desktop\ZK-BD\test.jpg"

# Fichier JPEG temporaire après compression
COMPRESSED = r"C:\Users\User\Desktop\ZK-BD\test_compressed.jpg"

# Fichier chiffré ZKBioTime
DEST = r"C:\ZKBioTime\auth_files\photo\test1.jpg"


# --------------------------------------------------
# 1. Compression / redimensionnement
# --------------------------------------------------

img = Image.open(SOURCE)

# Corriger l'orientation EXIF si nécessaire
try:
    from PIL import ImageOps
    img = ImageOps.exif_transpose(img)
except Exception:
    pass

# Conversion obligatoire pour JPEG
if img.mode != "RGB":
    img = img.convert("RGB")

# Maximum 320x320 en conservant les proportions
img.thumbnail((320, 320), Image.Resampling.LANCZOS)

# Compression JPEG
img.save(
    COMPRESSED,
    format="JPEG",
    quality=85,
    optimize=True
)

print("Photo originale :", os.path.getsize(SOURCE), "octets")
print("Photo compressée :", os.path.getsize(COMPRESSED), "octets")
print("Dimensions :", img.size)


# --------------------------------------------------
# 2. Chiffrement ZKBioTime
# --------------------------------------------------

data = encrypt_image(COMPRESSED, is_path=True)

print("Photo chiffrée :", len(data), "octets")
print("Header :", data[:16])


# --------------------------------------------------
# 3. Stockage dans ZKBioTime
# --------------------------------------------------

with open(DEST, "wb") as f:
    f.write(data)

print("Fichier ZKBioTime :", DEST)
