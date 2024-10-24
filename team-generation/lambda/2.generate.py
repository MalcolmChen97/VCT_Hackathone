import json
import random
import math
import copy

# Agent to Role Mapping (if needed)
agent_role_mapping = {
    'jett': 'Duelist', 'raze': 'Duelist', 'reyna': 'Duelist', 'phoenix': 'Duelist',
    'yoru': 'Duelist', 'neon': 'Duelist', 'iso': 'Duelist', 'clove': 'Duelist',
    'sage': 'Sentinel', 'killjoy': 'Sentinel', 'cypher': 'Sentinel', 'chamber': 'Sentinel',
    'deadlock': 'Sentinel', 'vyse': 'Sentinel',
    'viper': 'Controller', 'brimstone': 'Controller', 'omen': 'Controller',
    'astra': 'Controller', 'harbor': 'Controller',
    'sova': 'Initiator', 'breach': 'Initiator', 'skye': 'Initiator',
    'kayo': 'Initiator', 'fade': 'Initiator', 'gekko': 'Initiator'
}

# Role-specific weights for scoring
role_weights = {
    'Duelist': {'acs': 0.3, 'kd_ratio': 0.25, 'map_awareness': 0.2, 'adr': 0.15, 'clutch_factor': 0.1},
    'Initiator': {'assist_score': 0.3, 'map_awareness': 0.25, 'team_survival_trade_efficiency': 0.2, 'acs': 0.15,
                  'clutch_factor': 0.1},
    'Controller': {'assist_score': 0.3, 'team_survival_trade_efficiency': 0.25, 'clutch_factor': 0.2,
                   'map_awareness': 0.15, 'acs': 0.1},
    'Sentinel': {'kd_ratio': 0.3, 'clutch_factor': 0.25, 'map_awareness': 0.2, 'team_survival_trade_efficiency': 0.15,
                 'acs': 0.1},
    'Flex': {'acs': 0.2, 'kd_ratio': 0.2, 'assist_score': 0.2, 'map_awareness': 0.2, 'clutch_factor': 0.2}
}

# League weights
league_weights = {
    'vct-international': 1.0,
    'vct-challengers': 0.7,
    'game-changers': 0.5
}


def load_preprocessed_data(file_path='preprocessed_players.json'):
    with open(file_path, 'r', encoding='utf-8') as f:
        players = json.load(f)
    return players


def normalize_player_stats(players):
    stats = ['acs', 'kd_ratio', 'assist_score', 'map_awareness',
             'team_survival_trade_efficiency', 'adr', 'clutch_factor']
    max_values = {stat: max([player.get(stat, 0) for player in players]) for stat in stats}
    for player in players:
        for stat in stats:
            if max_values[stat] > 0:
                player[stat] = player.get(stat, 0) / max_values[stat]
            else:
                player[stat] = 0.0
    return players


def calculate_player_scores(players):
    for player in players:
        player['role_scores'] = {}
        player_league_weight = league_weights.get(player.get('league'), 0.7)
        for role in ['Duelist', 'Initiator', 'Controller', 'Sentinel', 'Flex']:
            if role in player['roles'] or role == 'Flex':
                role_weight = role_weights[role]
                score = sum(player.get(stat, 0) * weight for stat, weight in role_weight.items())
                player['role_scores'][role] = score * player_league_weight
    return players


def calculate_chemistry(team):
    total_chemistry = 0
    pairs = [(team[i], team[j]) for i in range(len(team)) for j in range(i + 1, len(team))]
    for player1, player2 in pairs:
        chemistry = 0.1  # Base chemistry
        # Shared nationality
        if player1.get('nationality') and player2.get('nationality') and player1['nationality'] == player2[
            'nationality']:
            chemistry += 0.5
        # Same region
        if player1.get('current_region') and player2.get('current_region') and player1['current_region'] == player2[
            'current_region']:
            chemistry += 0.3
        # Past team overlap
        past_teams1 = [team['team_name'] for team in player1.get('past_teams', [])]
        past_teams2 = [team['team_name'] for team in player2.get('past_teams', [])]
        if set(past_teams1) & set(past_teams2):
            chemistry += 0.2
        total_chemistry += chemistry
    # Normalize chemistry score to 1-100 scale
    max_possible_pairs = len(pairs)
    if max_possible_pairs > 0:
        chemistry_score = (total_chemistry / max_possible_pairs) * 100
    else:
        chemistry_score = 0
    return chemistry_score


def generate_initial_population(players, constraints, population_size=50):
    population = []
    eligible_players = filter_players_by_constraints(players, constraints)
    if not eligible_players:
        return population  # No eligible players
    for _ in range(population_size * 2):  # Try more times to find valid teams
        team = create_random_team(eligible_players, constraints)
        if team:
            population.append(team)
        if len(population) >= population_size:
            break
    return population


def filter_players_by_constraints(players, constraints):
    filtered_players = players
    # Apply league constraints
    if 'league' in constraints:
        leagues = constraints['league']
        required_leagues = set(leagues.keys())
        filtered_players = [p for p in filtered_players if p.get('league') in required_leagues]
    # Apply region constraints
    if 'region' in constraints and 'region_list' in constraints['region']:
        region_list = constraints['region']['region_list']
        filtered_players = [p for p in filtered_players if p.get('current_region') in region_list]
    # Apply player inclusion constraints
    if 'player' in constraints and constraints['player']:
        included_players = [p for p in players if p.get('handle') in constraints['player']]
        # Combine filtered_players and included_players, removing duplicates based on 'player_id'
        all_players = filtered_players + included_players
        unique_players = {p['player_id']: p for p in all_players}
        filtered_players = list(unique_players.values())
    return filtered_players


def create_random_team(players, constraints):
    team = []
    roles_needed = ['Duelist', 'Initiator', 'Controller', 'Sentinel', 'Flex']
    included_handles = constraints.get('player', [])
    included_players = [p for p in players if p.get('handle') in included_handles]

    # Ensure included players are unique
    included_player_ids = set()
    unique_included_players = []
    for player in included_players:
        if player['player_id'] not in included_player_ids:
            included_player_ids.add(player['player_id'])
            unique_included_players.append(copy.deepcopy(player))
    included_players = unique_included_players

    roles_assigned = []
    assigned_player_ids = set()

    # Assign roles to included players
    for player in included_players:
        assigned = False
        for role in player['roles']:
            if role not in roles_assigned:
                player['assigned_role'] = role
                roles_assigned.append(role)
                assigned_player_ids.add(player['player_id'])
                assigned = True
                break
        if not assigned and 'Flex' not in roles_assigned and len(player['roles']) >= 2:
            # Assign to 'Flex' if possible
            player['assigned_role'] = 'Flex'
            roles_assigned.append('Flex')
            assigned_player_ids.add(player['player_id'])
            assigned = True
        if not assigned:
            return None  # Cannot assign a role to this player
        team.append(player)

    # Remove assigned roles from roles_needed
    roles_needed = [role for role in roles_needed if role not in roles_assigned]

    # Fill remaining roles
    random.shuffle(players)
    for role in roles_needed:
        if role == 'Flex':
            # For 'Flex', select players who can play multiple roles
            eligible_players = [p for p in players if
                                p['player_id'] not in assigned_player_ids and len(p['roles']) >= 2]
        else:
            eligible_players = [p for p in players if p['player_id'] not in assigned_player_ids and role in p['roles']]
        if not eligible_players:
            return None  # Cannot fill this role
        # Select the best player based on role score
        eligible_players.sort(key=lambda p: p['role_scores'].get(role, 0), reverse=True)
        player = copy.deepcopy(eligible_players[0])
        player['assigned_role'] = role
        team.append(player)
        roles_assigned.append(role)
        assigned_player_ids.add(player['player_id'])

    if len(team) != 5:
        return None
    return team


def fitness_function(team, constraints, α=0.7, β=0.3, γ=1.0):
    team_score = sum(player['role_scores'][player['assigned_role']] for player in team)
    chemistry_score = calculate_chemistry(team)
    penalties = calculate_penalties(team, constraints)
    fitness = α * team_score + β * (chemistry_score / 100) - γ * penalties
    return fitness


def calculate_penalties(team, constraints):
    penalties = 0
    # Check role constraints
    roles = [player['assigned_role'] for player in team]
    required_roles = ['Duelist', 'Initiator', 'Controller', 'Sentinel', 'Flex']
    for role in required_roles:
        if role not in roles:
            penalties += 10  # Penalty for missing role
    # Check league constraints
    if 'league' in constraints:
        league_requirements = constraints['league']
        league_counts = {}
        for player in team:
            league = player.get('league')
            league_counts[league] = league_counts.get(league, 0) + 1
        for league, req in league_requirements.items():
            min_count = req.get('min', 0)
            max_count = req.get('max', 5)  # Default max to team size
            count = league_counts.get(league, 0)
            if count < min_count:
                penalties += 25 * (min_count - count)
            if count > max_count:
                penalties += 25 * (count - max_count)
    # Check region diversity constraints
    if 'region' in constraints and 'diversity' in constraints['region']:
        regions = set(player.get('current_region') for player in team if player.get('current_region'))
        if len(regions) < constraints['region']['diversity']:
            penalties += 25 * (constraints['region']['diversity'] - len(regions))
    # Check included players
    included_handles = constraints.get('player', [])
    team_handles = [player.get('handle') for player in team]
    for handle in included_handles:
        if handle not in team_handles:
            penalties += 25  # Penalty for missing required player
    return penalties


def select_parents(population, fitnesses):
    total_fitness = sum(fitnesses)
    if total_fitness == 0:
        if len(fitnesses) == 0:
            return None, None  # Cannot select parents from empty population
        selection_probs = [1 / len(fitnesses)] * len(fitnesses)
    else:
        selection_probs = [f / total_fitness for f in fitnesses]
    if len(selection_probs) < 2:
        return None, None  # Need at least two parents
    parents = random.choices(population, weights=selection_probs, k=2)
    return parents


def crossover(parent1, parent2):
    # Swap players without introducing duplicates
    child1_players = {p['player_id']: p for p in parent1}
    child2_players = {p['player_id']: p for p in parent2}

    swap_indices = random.sample(range(5), 2)
    for idx in swap_indices:
        p1 = parent1[idx]
        p2 = parent2[idx]

        # Ensure swapping doesn't introduce duplicates
        if p2['player_id'] not in child1_players and p1['player_id'] not in child2_players:
            # Swap in child1
            del child1_players[p1['player_id']]
            child1_players[p2['player_id']] = p2
            # Swap in child2
            del child2_players[p2['player_id']]
            child2_players[p1['player_id']] = p1

    child1 = list(child1_players.values())
    child2 = list(child2_players.values())
    return child1, child2


def mutate(team, players, constraints, mutation_rate=0.1):
    if random.random() < mutation_rate:
        idx = random.randint(0, 4)
        role = team[idx]['assigned_role']
        assigned_player_ids = set(p['player_id'] for p in team)
        if role == 'Flex':
            # For 'Flex', select players who can play multiple roles
            eligible_players = [p for p in players if
                                p['player_id'] not in assigned_player_ids and len(p['roles']) >= 2]
        else:
            eligible_players = [p for p in players if p['player_id'] not in assigned_player_ids and role in p['roles']]
        if eligible_players:
            new_player = copy.deepcopy(random.choice(eligible_players))
            new_player['assigned_role'] = role
            team[idx] = new_player
    return team


def genetic_algorithm(players, constraints, generations=50, population_size=50):
    population = generate_initial_population(players, constraints, population_size)
    if not population:
        return None  # Cannot proceed without initial population
    best_team = None
    best_fitness = -math.inf
    for generation in range(generations):
        fitnesses = [fitness_function(team, constraints) for team in population]
        new_population = []
        for _ in range(population_size // 2):
            parent1, parent2 = select_parents(population, fitnesses)
            if parent1 is None or parent2 is None:
                continue  # Cannot select parents, skip
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1, players, constraints)
            child2 = mutate(child2, players, constraints)
            new_population.extend([child1, child2])
        if not new_population:
            break  # Cannot generate new population, exit loop
        population = new_population
        # Update best team
        for team in population:
            fitness = fitness_function(team, constraints)
            if fitness > best_fitness:
                best_fitness = fitness
                best_team = team
    return best_team


def construct_output(team):
    output = {}
    for player in team:
        role = player['assigned_role']
        output[role] = player
    chemistry_score = calculate_chemistry(team)
    output['chemistry_score'] = round(chemistry_score)
    return output


def lambda_handler(event, context):
    # Load constraints from the event
    constraints = event.get('constraints', {})
    # Load preprocessed player data
    players = load_preprocessed_data()
    players = normalize_player_stats(players)
    players = calculate_player_scores(players)
    # Run genetic algorithm to find the best team
    best_team = genetic_algorithm(players, constraints)
    if best_team:
        output = construct_output(best_team)
        return {
            'statusCode': 200,
            'body': json.dumps(output)
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Could not find a suitable team with the given constraints.'})
        }


# For local testing
if __name__ == '__main__':
    # Example constraints
    event = {
        'constraints': {
            'region': {
                'diversity': 3
            },
            'league': {
                'game-changers': {'min': 2, 'max': 2},
                'vct-international': {'min': 3, 'max': 3}
            },
            'player': ['Didii']
        }
    }
    result = lambda_handler(event, None)
    print(json.dumps(result, indent=4, ensure_ascii=False))
