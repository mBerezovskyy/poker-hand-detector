card_weight = {}

for i in range(2, 11):
    card_weight[str(i)] = i

card_weight['J'] = 11
card_weight['Q'] = 12
card_weight['K'] = 13
card_weight['A'] = 14


def check_for_repeating_ranks_combinations(cards):
    pairs = []
    threes = []
    fourth = []
    full_house = []

    ranks = {}

    for card in cards:
        rank = card[1]
        if rank not in ranks:
            ranks[rank] = [card]
        else:
            ranks[rank].append(card)

    for rank, cards in ranks.items():
        if len(cards) > 1:
            if len(cards) % 2 == 0:
                for card_idx in range(0, len(cards), 2):
                    pairs.append(cards[card_idx:card_idx + 2])
            else:
                pairs.append(cards[:2])

        if len(cards) > 2:
            if len(cards) > 3:
                threes.append(cards[:3])
            else:
                threes.append(cards)

        if len(cards) > 3:
            fourth.append(cards)

    combinations = {
        'Pair': pairs,
        'Three of a kind': threes,
        'Four of a kind': fourth
    }

    if len(combinations['Pair']) > 0 and len(combinations['Three of a kind']) > 0 and len(
            combinations['Four of a kind']) == 0:

        for pair in combinations['Pair']:
            for card in pair:
                if card in combinations['Three of a kind'][0]:
                    break
                else:
                    full_house.append(card)

        full_house.append(combinations['Three of a kind'][0])

        combinations['Full House'] = full_house
    else:
        combinations['Full House'] = None

    return combinations


def check_for_flush(cards):
    suits = {}
    flush = None

    for card in cards:
        suit = card[0]
        if suit not in suits:
            suits[suit] = [card]
        else:
            suits[suit].append(card)

    for suit, cards in suits.items():
        if len(cards) >= 5:
            flush = cards[:5]

    return flush


def check_for_sequential_ranks_combinations(cards):
    sorted_cards = sorted(cards, key=lambda x: card_weight[x[1:]])

    all_cards_sorted = ' '.join(sorted(card_weight.keys(), key=lambda x: card_weight[x]))

    sorted_cards_ranks = [card[1:] for card in sorted_cards]

    ranks_to_cards_mapping = {}

    for rank, card in zip(sorted_cards_ranks, sorted_cards):
        ranks_to_cards_mapping[rank] = card

    straights_with_ranks = []

    for idx in range(len(sorted_cards_ranks)):
        substring = sorted_cards_ranks[idx: idx + 5]
        num_of_ranks = len(substring)

        if num_of_ranks < 5:
            continue
        if " ".join(substring) in all_cards_sorted:
            straights_with_ranks.append(substring)

    if straights_with_ranks:
        straight = [ranks_to_cards_mapping[rank] for rank in straights_with_ranks[0]]
        return straight

    return None


def check_hand(cards):
    combinations = {}

    repeating_ranks = check_for_repeating_ranks_combinations(cards)
    flush = check_for_flush(cards)
    sequential_ranks = check_for_sequential_ranks_combinations(cards)

    if len(repeating_ranks['Pair']) > 0 and len(repeating_ranks['Pair']) < 2:
        combinations['Pair'] = repeating_ranks['Pair'][0]

    if len(repeating_ranks['Pair']) > 1:
        two_pairs = []
        for cards in repeating_ranks['Pair']:
            two_pairs.extend(cards)
        combinations['Two Pairs'] = two_pairs

    if len(repeating_ranks['Three of a kind']) > 0:
        combinations['Three of a kind'] = repeating_ranks['Three of a kind']

    if sequential_ranks and len(sequential_ranks) > 0:
        combinations['Straight'] = sequential_ranks

    if flush and len(flush) > 0:
        combinations['Flush'] = flush

    if repeating_ranks['Full House'] and len(repeating_ranks['Full House']) > 0:
        full_house = []
        for card in repeating_ranks['Full House']:
            if type(card) != list:
                full_house.append(card)
            else:
                for c in card:
                    full_house.append(c)
        combinations['Full House'] = full_house

    if len(repeating_ranks['Four of a kind']) > 0:
        combinations['Four of a kind'] = repeating_ranks['Four of a kind'][0]

    if flush and check_for_sequential_ranks_combinations(flush):
        combinations['Straight Flush'] = check_for_sequential_ranks_combinations(flush)

    sorted_cards = sorted(cards, key=lambda x: card_weight[x[1:]])
    sorted_cards_ranks = ''.join([card[1:] for card in sorted_cards])

    if '10JQKA' in sorted_cards_ranks:
        if check_for_sequential_ranks_combinations(cards):
            combinations['Royal Flush'] = check_for_sequential_ranks_combinations(cards)

    return combinations


def get_higher_card(cards):
    return sorted(cards, key=lambda x: card_weight[x[1]], reverse=True)[0]


def get_best_hand(combinations):
    rankings = {
        'Pair': 0,
        'Two Pairs': 1,
        'Three of a kind': 2,
        'Straight': 3,
        'Flush': 4,
        'Full House': 5,
        'Four of a kind': 6,
        'Straight Flush': 7,
        'Royal Flush': 8
    }

    best_score = -1
    best_combination = None

    for combination in combinations:
        score = rankings[combination]

        if score > best_score:
            best_score = score
            best_combination = combination

    return best_score, best_combination
