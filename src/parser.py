file_path = "test/Challenge_FedEx.txt"
with open(file_path, "r") as file:
    lines = file.readlines()

    K = int(lines[0].strip())
    uld_list = None
    pkg_list = None

    for i in range(1, len(lines)):
        line: str = lines[i]
        if uld_list is None and line.startswith("ULD"):
            uld_start = i
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "":
                    uld_list = [line.strip().split(",") for line in lines[i + 1 : j]]
                    break
            i = j + 1
        line: str = lines[i]
        if pkg_list is None and line.startswith("Package"):
            pkg_list = [line.strip().split(",") for line in lines[i + 1 :]]
            i = j + 1

def get_K():
    return K

def get_uld_list():
    return uld_list


def get_pkg_list():
    return pkg_list
