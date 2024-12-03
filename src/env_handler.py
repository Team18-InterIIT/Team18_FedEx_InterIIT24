from environment import Environment
from solvers.flatbedLayering import LayerPacking as PackingAlgorithm


model = PackingAlgorithm()

env = Environment.init("COA_29925")
env.summary()
print("END _______________________________________________________________")
model.improve(env)
env.summary()
