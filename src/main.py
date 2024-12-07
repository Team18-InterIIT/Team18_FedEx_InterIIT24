import argparse
import parser as _parser

from environment import Environment
from solvers.hybrid import Hybrid as PackingAlgorithm
from util import Util


def main():
    parser = argparse.ArgumentParser(description="FedEx Packing Algorithm")
    parser.add_argument(
        "test_file",
        nargs="?",
        default="test/Challenge_FedEx.txt",
        help="Path to the test file",
    )
    parser.add_argument("--plot", action="store_true", help="Plot the environment")
    parser.add_argument("--stress_plot", action="store_true", help="Plot the stress")
    parser.add_argument(
        "--animate", action="store_true", help="Animate the environment"
    )
    parser.add_argument(
        "--simulate", action="store_true", help="Simulate the environment"
    )
    args = parser.parse_args()
    test_file = args.test_file

    parser = _parser.Parser(test_file)
    K = parser.get_K()
    uld_list = parser.get_uld_list()
    pkg_list = parser.get_pkg_list()

    env = Environment(K, uld_list, pkg_list)

    model = PackingAlgorithm()

    model.solve(env, search="normal", layering=True, n_calls=100)
    # To read from a solution file, use the following line instead of the above line
    # env.read(file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}")

    env.global_stability_check()
    order = Util(env).order()
    env.pkg_addition_order = []
    for _, order_list in order.items():
        env.pkg_addition_order.extend(order_list)

    env.summary()
    if args.plot:
        env.plot(stress_plot=False)
    if args.stress_plot:
        env.plot(stress_plot=True)
    if args.animate:
        env.animate()
    if args.simulate:
        env.simulate()

    env.write(
        file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}"
    )

    # uncomment the below line to pickle the environment
    # env.save(str(PackingAlgorithm.__name__))


if __name__ == "__main__":
    main()
