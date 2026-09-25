import marshal
import types
import dis

PATH = r"C:\ZKBioTime\mysite\base\management\commands\migrate_photo.pyc"

with open(PATH, "rb") as f:
    f.read(16)  # header Python 3.11
    code = marshal.load(f)


def inspect(code, level=0):
    indent = " " * level

    print(f"\n{indent}===== {code.co_name} =====")

    if code.co_names:
        print(f"{indent}NAMES:")
        for name in code.co_names:
            print(f"{indent}  {name}")

    if code.co_consts:
        print(f"{indent}CONSTANTS:")
        for value in code.co_consts:
            if isinstance(value, (str, bytes, int, float)):
                print(f"{indent}  {value!r}")

    print(f"\n{indent}BYTECODE:")
    dis.dis(code)

    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            inspect(const, level + 4)


inspect(code)
