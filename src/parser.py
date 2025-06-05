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
        K = None
        uld_list = None
        pkg_list = None

        with open(self.file_path, "r") as file:
            lines = file.readlines()

            if lines[0].startswith("For the challenge problem"):
                total_lines = len(lines)
                line_idx = 0
                while line_idx < total_lines:
                    line: str = lines[line_idx]

                    if line.startswith("K = "):
                        K = int(line.split(",")[0].split(" = ")[1])

                    elif line.startswith("ULD Identifier"):
                        uld_column_names = line.strip().split(",")
                        line_idx += 1
                        line = lines[line_idx]
                        uld_list = []

                        while not line.startswith("Package"):

                            if line.startswith("U"):
                                uld_list.append(line.strip().split(","))
                            line_idx += 1
                            line = lines[line_idx]
                            

                    elif line.startswith("Package Identifier"):
                        pkg_column_names = line.strip().split(",")
                        line_idx += 1
                        pkg_list = []

                        while line_idx < total_lines:
                            line = lines[line_idx]

                            if line.startswith("P"):
                                pkg_list.append(line.strip().split(","))
                            line_idx += 1

                    line_idx += 1

            else:
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
                                break
                        i = j + 1
                    line: str = lines[i]
                    if pkg_list is None and line.startswith("Package"):
                        pkg_list = [line.strip().split(",") for line in lines[i + 1 :]]
                        i = j + 1

        for row in range(len(uld_list)):
            first_idx_of_num = 1
            for idx, char in enumerate(uld_list[row][0]):
                if char.isdigit():
                    first_idx_of_num = idx
                    break
            uld_list[row][0] = uld_list[row][0][first_idx_of_num:]

        for row in range(len(pkg_list)):
            first_idx_of_num = 2
            for idx, char in enumerate(pkg_list[row][0]):
                if char.isdigit():
                    first_idx_of_num = idx
                    break
            pkg_list[row][0] = pkg_list[row][0][first_idx_of_num:]

        uld_list.sort(key=lambda x: int(x[0]))
        pkg_list.sort(key=lambda x: int(x[0]))

        self.K = K
        self.uld_list = uld_list
        self.pkg_list = pkg_list

    def get_K(self) -> int:
        return self.K

    def get_uld_list(self) -> list[list[str]]:
        return self.uld_list

    def get_pkg_list(self) -> list[list[str]]:
        return self.pkg_list
