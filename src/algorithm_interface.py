from abc import ABC, abstractmethod


class PackingAlgorithm(ABC):
    @abstractmethod
    def solve(self, environment):
        """
        Solve the bin-packing problem for the given environment.

        Parameters:
        - environment: An instance of the Environment class.

        Returns:
        - Solution or None if infeasible.
        """
        print("This method should be implemented by a subclass.")
        pass
