import parameters
import internal
import game
import numpy as np
import silent_game

def crossover(genome1, genome2):
    """Implements the crossover functionality of the NEAT algorithm."""
    genes1 = genome1.genes
    genes2 = genome2.genes
    better = max([genome1, genome2], key=lambda x: x.fitness)
    composite_genes = {}
    composite_nodes = {}

    largest_innovation_number = max(list(genes1.keys()) + list(genes2.keys()))
    for i in range(largest_innovation_number + 1):
        g1 = get_dict_value(i, genes1)
        g2 = get_dict_value(i, genes2)

        if not (g1 or g2):
            continue
        elif g1 and not g2 and better == genome1:
            gene = g1.copy()
        elif g2 and not g1 and better == genome2:
            gene = g2.copy()
        elif g1 and g2:
            gene = np.random.choice([g1, g2]).copy()
            if not g1.enable and not g2.enable and np.random.rand() < parameters.p_enable_if_both_parents_disabled:
                gene.enable = True

        composite_genes[i] = gene
        # Generate nodes from gene
        if gene.in_node not in composite_nodes:
            composite_nodes[gene.in_node] = internal.Node(gene.in_node)
        composite_nodes[gene.in_node].out_nodes.append(gene.out_node)
        if gene.out_node not in composite_nodes:
            composite_nodes[gene.out_node] = internal.Node(gene.out_node)
        composite_nodes[gene.out_node].in_nodes.append(gene.in_node)

    return internal.Genome(composite_nodes, composite_genes)


def get_dict_value(val, dict):
    try:
        return dict[val]
    except KeyError:
        return None


def delta(genome1, genome2):
    g1 = set(genome1.genes.keys())
    g2 = set(genome2.genes.keys())
    max1 = max(g1)
    max2 = max(g2)

    excess = 0
    disjoint = 0
    sum_of_differences = 0
    N = min(len(g1), len(g2))
    # if N < 20:
        # N = 1

    for current in g1.union(g2):
        if current in g1 and current in g2:
            sum_of_differences += abs(genome1.genes[current].weight - genome2.genes[current].weight)
        elif current in g1 and current not in g2:
            if current > max2:
                excess += 1
            else:
                disjoint += 1
        elif current in g2 and current not in g1:
            if current > max1:
                excess += 1
            else:
                disjoint += 1
    return parameters.c1*excess/N + parameters.c2*disjoint/N + parameters.c3*sum_of_differences/N


def find_species(population, genome):
    """population is a list of species. Returns the species that the genome belongs to. If
    there aren't any species that it belongs to, it returns None. """
    for s in population:
        if delta(s.representative, genome) < parameters.delta_threshold:
            return s
    return None


def get_genome_fitness(genome):
    nn = internal.NeuralNetwork(genome)
    game = silent_game.Game(nn.evaluate)
    game_time = 0
    while game_time < 10000 and game.get_continue_status():  # Run the game
        game.step()
        genome.fitness = 15 * game.snake.fitness + 0.5 * (game.manhattan_distance_to_food())
        game_time += 1


def evaluate_population(population):
    for species in population:
        for genome in species.genomes:
            get_genome_fitness(genome)


def init_population():
    """Returns a one-element list of one species. This species contains the entire population
    for the first generation. """
    all_genomes = []
    for _ in range(parameters.population_size):
        genome = internal.Genome()
        all_genomes.append(genome)
    species = internal.Species(np.random.choice(all_genomes))
    species.genomes = all_genomes
    return [species]


def update_spawn_amounts(population):
    """Finding spawn amounts. Each species' spawn amount is proportional to the sum of its
    genomes' adjusted fitness."""
    stagnated = set()
    total_sum_adj_fitness = 0
    for species in population:
        N = len(species.genomes)
        for genome in species.genomes:
            species.sum_adj_fitness += genome.fitness/N

        species.best_genome = max(species.genomes, lambda x: x.fitness)
        max_fitness = species.best_genome.fitness
        if max_fitness <= species.best_fitness_so_far:  # Species didn't improve
            species.stagnate_generations += 1
        else:
            species.stagnate_generations = 0  # Restart stagnate count
            species.best_fitness_so_far = max_fitness
        if species.stagnate_generations >= parameters.stagnate_threshold:  # Species has stagnated
            stagnated.add(species)
        else:
            total_sum_adj_fitness += species.sum_adj_fitness

    for species in stagnated:
        population.remove(species)
    for species in population:
        species.spawn_amount = int(parameters.population * species.sum_adj_fitness/total_sum_adj_fitness)

def next_generation_species(species):
    """Returns the next generation (list) of genomes given the species. The size of the next generation
    will be species.spawn_amount"""
    spawn_amount = species.spawn_amount
    sorted_genomes = sorted(species.genomes, key=lambda g: g.fitness, reverse=True)
    probability_chosen = np.array([g.fitness for g in species.genomes])
    probability_chosen = probability_chosen / sum(probability_chosen)  # Normalize

    N = len(species.genomes)
    new_generation = sorted_genomes[0:int(parameters.keep_best_amount*N)]  # Keep top fraction of species
    while len(new_generation) < spawn_amount:
        g1 = np.random.choice(species.genomes, p=probability_chosen)
        g2 = np.random.choice(species.genomes, p=probability_chosen)
        new_generation.append(crossover(g1, g2))

    for i in range(1, len(new_generation)):  # The top genome does not get mutated
        new_generation[i].mutate()
    return new_generation



x = init_population()[0]
print('asdf')