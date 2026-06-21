nights = 5
acts_for_city = [1, 2, 3, 4, 5]
acts_distribution = [[] for _ in range(nights)]
for i, act in enumerate(acts_for_city):
    idx = i % nights
    if len(acts_distribution[idx]) < 3:
        acts_distribution[idx].append(act)
print(acts_distribution)
