import sys
import parser as _parser

from environment import Environment

# The following import statement should be replaced with the correct import statement
from algorithm_interface import PackingAlgorithm as PackingAlgorithm

# For Example:
from solvers.hybrid import Hybrid as PackingAlgorithm
from util import Util


def main():
    if len(sys.argv) == 2:
        test_file = sys.argv[1]
    else:
        test_file = "test/Challenge_FedEx.txt"

    parser = _parser.Parser(test_file)
    K = parser.get_K()
    uld_list = parser.get_uld_list()
    pkg_list = parser.get_pkg_list()

    env = Environment(K, uld_list, pkg_list)

    model = PackingAlgorithm()

    model.solve(env, search="normal", layering=True, n_calls=10)
    # To read from a solution file, use the following line instead of the above line
    # env.read(file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}")

    env.global_stability_check()
    order = Util(env).order()
    env.pkg_addition_order = []
    for uld_id, order_list in order.items():
        env.pkg_addition_order.extend(order_list)

    env.summary()
    env.plot(stress_plot=False)
    # env.animate()
    # env.simulate()
    env.write(
        file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}"
    )

    # uncomment the below line to pickle the environment
    # env.save(str(PackingAlgorithm.__name__))


if __name__ == "__main__":
    main()
