import sys
import time
import parser
from environment import Environment
from util import Util
from insert_package import PackageInserter
from entity import Package

# The following import statement should be replaced with the correct import statement
# from solvers.layerstratwithOR import LayerPacking as PackingAlgorithm

# For Example:
from solvers.Caving_COA import COA as PackingAlgorithm

if len(sys.argv) == 2:
    test_file = sys.argv[1]
else:
    test_file = "test/Challenge_FedEx.txt"

parser = parser.Parser(test_file)
K = parser.get_K()
uld_list = parser.get_uld_list()
pkg_list = parser.get_pkg_list()

env = Environment(K, uld_list, pkg_list)

model = PackingAlgorithm()

model.solve(env)
# To read from a solution file, use the following line instead of the above line
# env.read(file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}")

newPackage = Package(["401", "70", "70", "70", "0", "Priority", "0"])
start_time = time.time()
# for uld in range(1, 2):
#     PackageInserter(env).insert_package(uld, newPackage)
PackageInserter(env).parallel_replace_package(newPackage)
end_time = time.time() 
print(f"Time taken to insert package: {end_time - start_time} seconds")

order = Util(env).order()
env.pkg_addition_order = []
for uld_id, order_list in order.items():
    env.pkg_addition_order.extend(order_list)

# env.summary()
# env.plot()
env.animate()
env.write(
    file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}"
)
