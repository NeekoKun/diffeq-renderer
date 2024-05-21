from attractor import Attractor
import matplotlib.pyplot as plt
import random
import torch
import time

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

n_attractors = 10
n_point = round((1920*1200) / (10**2))

attractors = [
    Attractor(
        random.uniform(10, 20),
        random.randint(-1920//2, 1920//2),
        random.randint(-1200//2, 1200//2),
        random.choice([-1, 1])
    ) for _ in range(n_attractors)
]

attractors_list = [[], [], [], []]

for attractor in attractors:
    attractors_list[0].append(attractor.q)
    attractors_list[1].append(attractor.x)
    attractors_list[2].append(attractor.y)
    attractors_list[3].append(attractor.sign)

points = torch.rand((2, n_point)).to(device)
attractors_tensor = torch.Tensor(attractors_list)

points = points.mul(2)
points = points.add(-1)

plt.scatter(points[0].cpu(), points[1].cpu(), s=[1 for _ in range(int(1920*1200/100))])
plt.show()