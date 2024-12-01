import os


class Parser:
    def __init__(self, file_path="test/Challenge_FedEx.txt"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.file_path = os.path.join(project_root, file_path)

        self.K = None
        self.uld_list = None
        self.pkg_list = None

        self.parse()

    def parse(self):
        with open(self.file_path, "r") as file:
            lines = file.readlines()

            K = int(lines[0].strip())
            uld_list = None
            pkg_list = None

            for i in range(1, len(lines)):
                line: str = lines[i]
                if uld_list is None and line.startswith("ULD"):
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() == "":
                            uld_list = [
                                line.strip().split(",") for line in lines[i + 1 : j]
                            ]
                            for row in range(len(uld_list)):
                                uld_list[row][0] = uld_list[row][0][1]
                            break
                    i = j + 1
                line: str = lines[i]
                if pkg_list is None and line.startswith("Package"):
                    pkg_list = [line.strip().split(",") for line in lines[i + 1 :]]
                    for row in range(len(pkg_list)):
                        pkg_list[row][0] = pkg_list[row][0][2:]
                    i = j + 1

        uld_list.sort(key=lambda x: int(x[0]))
        pkg_list.sort(key=lambda x: int(x[0]))

        self.K = K
        self.uld_list = uld_list
        self.pkg_list = pkg_list

    def get_K(self):
        return self.K

    def get_uld_list(self):
        return self.uld_list

    def get_pkg_list(self):
        return self.pkg_list
