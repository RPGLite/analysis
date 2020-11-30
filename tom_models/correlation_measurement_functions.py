from math import asin, sqrt, log2


def calculate_entropy_from_real_and_simulated_distributions(real, simulated):
    difference_distribution = dict()
    for index in range(len(real)):
        difference_distribution[index] = abs(real[index]-simulated[index])
    return calculate_entropy(difference_distribution)


def calculate_entropy(distributed_choices):
    def prob(num):
        return num/sum(distributed_choices)
    return -sum(list(map(lambda x: 0 if prob(x) == 0 else prob(x)-log2(prob(x)), distributed_choices)))

def distance_on_probability_dist_sphere(real, simulated):
    snd = lambda x: x[1]
    fst = lambda x: x[0]

    real_sorted = sorted(real.items(), key=fst)
    sim_sorted = sorted(simulated.items(), key=fst)

    real_vector = list(map(snd, real_sorted))
    sim_vector = list(map(snd, sim_sorted))

    assert len(real_vector) == len(sim_vector)

    dotprod = sum(real_vector[i]*sim_vector[i] for i in range(len(real_vector)))
    sphere_radius = sqrt(sum(map(lambda x: x**2, real_vector)))

    # geodesic length is effectively r*angle, where angle is 2 * arcsin( length / 2r )
    # https://math.stackexchange.com/questions/225323/length-of-arc-connecting-2-points-in-n-dimensions
    theta = 2*asin(sqrt(dotprod)/(2*sphere_radius))
    distance = sphere_radius * theta

    return distance

