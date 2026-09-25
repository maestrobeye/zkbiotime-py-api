import marshal
import dis
import types
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
PATH = r"C:\ZKBioTime\mysite\tools\image_utils.pyc"

with open(PATH, "rb") as f:
    f.read(16)
    code = marshal.load(f)


def find_function(code, name):
    if code.co_name == name:
        return code

    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result = find_function(const, name)
            if result:
                return result

    return None


func = find_function(code, "encrypt_image")

if func:
    print("===== encrypt_image =====")
    dis.dis(func)

    print("\n===== CONSTANTES =====")
    for c in func.co_consts:
        print(repr(c))

    print("\n===== VARIABLES =====")
    print(func.co_varnames)

else:
    print("Fonction introuvable")



