from collections import defaultdict
import random


def generate_cat1_paper(questions):
    # Group by unit and part
    by_unit = defaultdict(lambda: defaultdict(list))
    for q in questions:
        by_unit[q.unit][q.part].append(q)

    selected = {"PART_A": [], "PART_B": [], "PART_C": []}

    # PART A for CAT1: 2 from Unit 1, 2 from Unit 2, 1 from Unit 3
    for unit, count in [(1, 2), (2, 2), (3, 1)]:
        candidates = by_unit[unit]["A"]
        if len(candidates) < count:
            raise ValueError(
                f"Not enough PART A questions in Unit {unit} (need {count}, have {len(candidates)})"
            )
        selected["PART_A"].extend(random.sample(candidates, count))

    # PART B: Two OR questions (6 and 7) from two different units (1 and 2)
    numbers = [1, 2, 3]
    random.shuffle(numbers)

    b_units = numbers[:2]

    for unit in b_units:
        candidates = by_unit[unit]["B"]
        if len(candidates) < 2:
            raise ValueError(
                f"Not enough PART B questions in Unit {unit} for OR choice"
            )
        main, orr = random.sample(candidates, 2)
        main.text = f"(a) {main.text.strip()}"
        orr.text = f"(b) {orr.text.strip()}"
        selected["PART_B"].append({"main": main, "or": orr})

    # PART C: From Unit 3 (different from PART B units 1 & 2)
    c_unit = numbers[2]

    c_candidates = by_unit[c_unit]["C"]
    if not c_candidates:
        # Fallback to PART B if no C available in Unit 3
        c_candidates = by_unit[c_unit]["B"]
    if not c_candidates:
        raise ValueError("No suitable PART C questions in Unit 3")

    main_c = random.choice(c_candidates)
    selected["PART_C"].append(main_c)

    remaining = [q for q in c_candidates if q != main_c]
    if remaining:
        or_c = random.choice(remaining)
        selected["PART_C"].append(or_c)

    return selected


def generate_cat2_paper(questions):
    # Group by unit and part
    by_unit = defaultdict(lambda: defaultdict(list))
    for q in questions:
        by_unit[q.unit][q.part].append(q)

    selected = {"PART_A": [], "PART_B": [], "PART_C": []}

    # PART A for CAT2: 2 from Unit 4, 2 from Unit 5, 1 from Unit 3
    for unit, count in [(4, 2), (5, 2), (3, 1)]:
        candidates = by_unit[unit]["A"]
        if len(candidates) < count:
            raise ValueError(
                f"Not enough PART A questions in Unit {unit} (need {count}, have {len(candidates)})"
            )
        selected["PART_A"].extend(random.sample(candidates, count))

    # Available units for PART B and C: 3,4,5
    available_units = [u for u in [3, 4, 5] if by_unit[u]["B"]]
    if len(available_units) < 2:
        raise ValueError("Not enough units with PART B questions for CAT2")

    random.shuffle(available_units)
    b_units = available_units[:2]  # Two units for PART B (Q6 and Q7)
    remaining_units = [u for u in available_units if u not in b_units]
    c_unit = random.choice(
        remaining_units or b_units
    )  # Prefer different unit, fallback if needed

    # PART B: Two OR questions from two different units (4 and 5 preferred)
    for unit in b_units:
        candidates = by_unit[unit]["B"]
        if len(candidates) < 2:
            # Fallback: combine from all units
            fallback = []
            for u in [3, 4, 5]:
                fallback.extend(by_unit[u]["B"])
            candidates = list(set(fallback))
        if len(candidates) < 2:
            raise ValueError(f"Not enough PART B questions for selection")
        main, orr = random.sample(candidates, 2)
        main.text = f"(a) {main.text.strip()}"
        orr.text = f"(b) {orr.text.strip()}"
        selected["PART_B"].append({"main": main, "or": orr})

    # PART C: From a unit different from PART B units
    c_candidates = by_unit[c_unit]["C"]
    if not c_candidates:
        c_candidates = by_unit[c_unit]["B"]
    if not c_candidates:
        raise ValueError(f"No suitable PART C questions in Unit {c_unit}")

    main_c = random.choice(c_candidates)
    selected["PART_C"].append(main_c)

    remaining = [q for q in c_candidates if q != main_c]
    if remaining:
        or_c = random.choice(remaining)
        selected["PART_C"].append(or_c)

    return selected


def generate_endsem_paper(questions):
    # Group questions by unit and part
    by_unit = defaultdict(lambda: defaultdict(list))
    for q in questions:
        by_unit[q.unit][q.part].append(q)
    
    units = [1, 2, 3, 4, 5]
    
    selected = {
        "PART_A": [],
        "PART_B": [],
        "PART_C": []
    }
    
    # PART A: Flexible — aim for ~10 total, prefer 2 per unit
    all_a_questions = []
    for u in units:
        all_a_questions.extend(by_unit[u]['A'])
    
    if len(all_a_questions) < 10:
        raise ValueError(f"Not enough PART A questions (have {len(all_a_questions)}, need ~10)")
    
    # Try to take up to 2 per unit
    for u in units:
        candidates = by_unit[u]['A']
        take = min(2, len(candidates))
        if take > 0:
            selected["PART_A"].extend(random.sample(candidates, take))
    
    # Fill remaining to reach 10
    current = len(selected["PART_A"])
    if current < 10:
        remaining_pool = [q for q in all_a_questions if q not in selected["PART_A"]]
        needed = 10 - current
        selected["PART_A"].extend(random.sample(remaining_pool, min(needed, len(remaining_pool))))
    
    random.shuffle(selected["PART_A"])

    # === PART B and PART C ===
    all_long_questions = []
    unit_long_questions = {}
    used_question_texts = []  # Track used question text to avoid duplicates

    for u in units:
        combined = by_unit[u]['B'] + by_unit[u]['C']
        if len(combined) < 2:
            raise ValueError(f"Not enough long questions (B+C) in Unit {u}")
        random.shuffle(combined)
        unit_long_questions[u] = combined
        all_long_questions.extend(combined)

    random.shuffle(all_long_questions)

    # PART B: One OR pair per unit
    for u in units:
        unit_pool = unit_long_questions[u]
        main = unit_pool[0]
        orr = unit_pool[1]
        
        main.text = f"(a) {main.text.strip()}"
        orr.text = f"(b) {orr.text.strip()}"
        
        selected["PART_B"].append({"main": main, "or": orr})
        
        # Record the text to avoid reuse
        used_question_texts.append(main.text)
        used_question_texts.append(orr.text)

    # PART C: Pick 2 unused long questions from global pool
    available_for_c = [q for q in all_long_questions if q.text not in used_question_texts]
    
    if len(available_for_c) < 2:
        raise ValueError("Not enough unused long questions for PART C")
    
    main_c = available_for_c[0]
    or_c = available_for_c[1]
    
    selected["PART_C"].append(main_c)
    selected["PART_C"].append(or_c)
    
    return selected

