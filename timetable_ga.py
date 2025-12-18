"""
timetable_ga.py
CSV-driven Genetic Algorithm timetable generator.

Place CSVs in ./data/ as described in README.
Run: python timetable_ga.py
Output: data/generated_timetable.csv
"""

import random
import copy
import math
import pandas as pd
from collections import defaultdict, Counter
import argparse
import sys


POP_SIZE = 100
GENERATIONS = 800
TOURNAMENT_K = 3
MUTATION_RATE = 0.2
ELITE = 4
HARD_PENALTY = 10**6   
SOFT_PENALTY = 5       
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


def load_data(data_dir="data"):
    courses = pd.read_csv(f"{data_dir}/courses.csv", dtype=str).fillna("")
    teachers = pd.read_csv(f"{data_dir}/teachers.csv", dtype=str).fillna("")
    groups = pd.read_csv(f"{data_dir}/groups.csv", dtype=str).fillna("")
    rooms = pd.read_csv(f"{data_dir}/rooms.csv", dtype=str).fillna("")
    timeslots = pd.read_csv(f"{data_dir}/timeslots.csv", dtype=str).fillna("")
    # convert types where needed
    courses['lectures_per_week'] = courses['lectures_per_week'].astype(int)
    courses['expected_size'] = courses['expected_size'].astype(int)
    rooms['capacity'] = rooms['capacity'].astype(int)
    return courses, teachers, groups, rooms, timeslots

# ---------- Preprocessing ----------
def preprocess(courses, teachers_df, groups_df, rooms_df, timeslots_df):
    # dicts for fast lookup
    courses_d = courses.to_dict(orient='records')
    teachers = {}
    for r in teachers_df.to_dict(orient='records'):
        teachers[r['teacher_id']] = {
            'name': r['teacher_name'],
            'qualified': r['qualified_courses'].split(';') if r['qualified_courses'] else [],
            'available': r['available_timeslots'].split(';') if r['available_timeslots'] else [],
            'preferred': r['preferred_timeslots'].split(';') if r['preferred_timeslots'] else []
        }
    groups = {}
    for r in groups_df.to_dict(orient='records'):
        groups[r['group_id']] = {
            'size': int(r['students_count']),
            'enrolled': r['enrolled_courses'].split(';') if r['enrolled_courses'] else []
        }
    rooms = [{'id': r['room_id'], 'cap': int(r['capacity']), 'features': r.get('features','')} for r in rooms_df.to_dict(orient='records')]
    timeslots = [r['ts_id'] for r in timeslots_df.to_dict(orient='records')]
    return courses_d, teachers, groups, rooms, timeslots

# ---------- Chromosome representation ----------
# Each gene = dict: {session_id, course_id, group_id, timeslot, room, teacher}
# session_id: unique id for each lecture occurrence (course_id + index)

def build_session_list(courses):
    sessions = []
    for c in courses:
        cid = c['course_id']
        g = c['group_id']
        lectures = int(c['lectures_per_week'])
        size = int(c['expected_size'])
        for i in range(lectures):
            sessions.append({'session_id': f"{cid}_{i+1}", 'course': cid, 'group': g, 'size': size})
    return sessions

# ---------- Initialization ----------
def random_gene(session, timeslots, rooms, teachers):
    # pick teacher who is qualified for course
    qualified_teachers = [tid for tid,t in teachers.items() if session['course'] in t['qualified']]
    if not qualified_teachers:
        qualified_teachers = list(teachers.keys())
    teacher = random.choice(qualified_teachers)
    ts = random.choice(timeslots)
    room = random.choice(rooms)['id']
    return {'session_id': session['session_id'], 'course': session['course'], 'group': session['group'], 'size': session['size'],
            'timeslot': ts, 'room': room, 'teacher': teacher}

def init_individual(sessions, timeslots, rooms, teachers):
    return [random_gene(s, timeslots, rooms, teachers) for s in sessions]

# ---------- Fitness ----------
def fitness(ind, rooms_map, teachers, groups):
    penalty = 0
    # maps to detect conflicts
    ts_teacher = defaultdict(list)
    ts_room = defaultdict(list)
    ts_group = defaultdict(list)

    for g in ind:
        key_t = (g['timeslot'], g['teacher'])
        key_r = (g['timeslot'], g['room'])
        key_g = (g['timeslot'], g['group'])
        ts_teacher[key_t].append(g)
        ts_room[key_r].append(g)
        ts_group[key_g].append(g)
        # capacity check (room capacity >= class size)
        room_cap = rooms_map.get(g['room'], 0)
        if g['size'] > room_cap:
            penalty += HARD_PENALTY

    # hard conflicts (teacher, room, group)
    for d in (ts_teacher, ts_room, ts_group):
        for key, lst in d.items():
            if len(lst) > 1:
                # for each extra booking add HARD_PENALTY
                penalty += HARD_PENALTY * (len(lst) - 1)

    # hard: teacher must be qualified for course
    for g in ind:
        if g['course'] not in teachers[g['teacher']]['qualified']:
            penalty += HARD_PENALTY

    # soft: teacher availability preferences (penalize if timeslot not available)
    for g in ind:
        if g['timeslot'] not in teachers[g['teacher']]['available']:
            penalty += SOFT_PENALTY

        # small reward for preferred timeslot (we model as negative penalty)
        if g['timeslot'] in teachers[g['teacher']]['preferred']:
            penalty -= 1  # small reduction

    # soft: minimize teacher gaps (approximate by counting gaps per teacher)
    # we can approximate by counting distinct timeslots per teacher and expected lectures count
    teacher_sessions = defaultdict(list)
    for g in ind:
        teacher_sessions[g['teacher']].append(g['timeslot'])
    for t, slots in teacher_sessions.items():
        # more spread-out timeslots -> small penalty proportional to number of unique slots
        unique = len(set(slots))
        # fewer sessions with same teacher increases fragmentation—this is a light soft penalty
        penalty += max(0, unique - 3) * 0.5

    # convert to fitness (higher is better)
    if penalty >= HARD_PENALTY:
        return 1.0 / (1 + penalty)  # tiny fitness if hard violated
    return 1.0 / (1 + penalty)

# ---------- Genetic operators ----------
def tournament(pop, fitnesses, k=TOURNAMENT_K):
    inds = random.sample(range(len(pop)), k)
    best = max(inds, key=lambda i: fitnesses[i])
    return copy.deepcopy(pop[best])

def crossover(a, b):
    n = len(a)
    if n < 2:
        return copy.deepcopy(a), copy.deepcopy(b)
    pt = random.randint(1, n-1)
    child1 = copy.deepcopy(a[:pt] + b[pt:])
    child2 = copy.deepcopy(b[:pt] + a[pt:])
    return child1, child2

def mutate(ind, timeslots, rooms_ids, teachers, mutation_rate=MUTATION_RATE):
    for i in range(len(ind)):
        if random.random() < mutation_rate:
            gene = ind[i]
            # mutate one of timeslot/room/teacher randomly (smart-ish choices)
            choice = random.choice(['timeslot','room','teacher'])
            if choice == 'timeslot':
                # prefer teacher's available timeslots if possible
                avail = teachers[gene['teacher']]['available']
                if avail:
                    gene['timeslot'] = random.choice(avail)
                else:
                    gene['timeslot'] = random.choice(timeslots)
            elif choice == 'room':
                gene['room'] = random.choice(rooms_ids)
            else:
                # choose a qualified teacher if available else any teacher
                qualified = [tid for tid,t in teachers.items() if gene['course'] in t['qualified']]
                gene['teacher'] = random.choice(qualified) if qualified else random.choice(list(teachers.keys()))
    return ind

# ---------- Repair heuristic ----------
def repair(ind, timeslots, rooms_ids, teachers, rooms_map):
    # naive repair: reassign conflicting genes iteratively
    def conflicts_count(gene, index, current):
        cnt = 0
        for j,other in enumerate(current):
            if j == index: continue
            if gene['timeslot'] == other['timeslot']:
                if gene['teacher'] == other['teacher']:
                    cnt += 1
                if gene['room'] == other['room']:
                    cnt += 1
                if gene['group'] == other['group']:
                    cnt += 1
        # capacity conflict
        if gene['size'] > rooms_map.get(gene['room'], 0):
            cnt += 1
        # qualification conflict
        if gene['course'] not in teachers[gene['teacher']]['qualified']:
            cnt += 1
        return cnt

    # attempt to fix each gene with conflicts by trying alternatives
    current = ind
    for i,g in enumerate(current):
        if conflicts_count(g, i, current) > 0:
            fixed = False
            # try teacher's available slots first
            candidate_teachers = [tid for tid,t in teachers.items() if g['course'] in t['qualified']]
            candidate_teachers = candidate_teachers if candidate_teachers else list(teachers.keys())
            # try combinations
            attempts = []
            for t in random.sample(candidate_teachers, min(len(candidate_teachers), 4)):
                avail = teachers[t]['available'] if teachers[t]['available'] else timeslots
                for ts in random.sample(avail, min(len(avail), 5)):
                    for r in random.sample(rooms_ids, min(len(rooms_ids), 3)):
                        attempts.append((t,ts,r))
            for (t,ts,r) in attempts:
                g_try = dict(g)
                g_try['teacher'] = t
                g_try['timeslot'] = ts
                g_try['room'] = r
                if conflicts_count(g_try, i, current) == 0 and g_try['size'] <= rooms_map.get(r,0):
                    current[i] = g_try
                    fixed = True
                    break
            if not fixed:
                # last resort: randomize
                g['teacher'] = random.choice(list(teachers.keys()))
                g['timeslot'] = random.choice(timeslots)
                g['room'] = random.choice(rooms_ids)
    return current

# ---------- GA main ----------
def run_ga(sessions, timeslots, rooms, teachers, groups,
           pop_size=POP_SIZE, generations=GENERATIONS):
    rooms_map = {r['id']: r['cap'] for r in rooms}
    rooms_ids = [r['id'] for r in rooms]
    # init population
    pop = [init_individual(sessions, timeslots, rooms, teachers) for _ in range(pop_size)]
    best_ind = None
    best_fit = -1
    for gen in range(generations):
        fitnesses = [fitness(ind, rooms_map, teachers, groups) for ind in pop]
        # track best
        for i,fv in enumerate(fitnesses):
            if fv > best_fit:
                best_fit = fv
                best_ind = copy.deepcopy(pop[i])
        # logging
        if gen % 20 == 0 or gen == generations-1:
            print(f"Gen {gen:4d} best_fitness {best_fit:.9f}")
        # early exit if ideal (no penalty)
        if best_fit > 0.999999:
            print("Found near-perfect solution.")
            break
        # make next generation
        newpop = []
        # elitism
        sorted_idx = sorted(range(len(pop)), key=lambda i: fitnesses[i], reverse=True)
        for idx in sorted_idx[:ELITE]:
            newpop.append(copy.deepcopy(pop[idx]))
        while len(newpop) < pop_size:
            p1 = tournament(pop, fitnesses, k=TOURNAMENT_K)
            p2 = tournament(pop, fitnesses, k=TOURNAMENT_K)
            c1, c2 = crossover(p1, p2)
            c1 = mutate(c1, timeslots, rooms_ids, teachers)
            c2 = mutate(c2, timeslots, rooms_ids, teachers)
            c1 = repair(c1, timeslots, rooms_ids, teachers, rooms_map)
            c2 = repair(c2, timeslots, rooms_ids, teachers, rooms_map)
            newpop.append(c1)
            if len(newpop) < pop_size:
                newpop.append(c2)
        pop = newpop
    return best_ind, best_fit

# ---------- Output writer ----------
def write_output(ind, out_csv="data/generated_timetable.csv"):
    rows = []
    for g in ind:
        rows.append({
            'session_id': g['session_id'],
            'course': g['course'],
            'group': g['group'],
            'timeslot': g['timeslot'],
            'room': g['room'],
            'teacher': g['teacher']
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"Wrote timetable to {out_csv}")

# ---------- main ----------
def main(data_dir="data"):
    courses_df, teachers_df, groups_df, rooms_df, timeslots_df = load_data(data_dir)
    courses, teachers, groups, rooms, timeslots = preprocess(courses_df, teachers_df, groups_df, rooms_df, timeslots_df)
    sessions = build_session_list(courses)
    print(f"Sessions to schedule: {len(sessions)}")
    best, best_fit = run_ga(sessions, timeslots, rooms, teachers, groups)
    if best is None:
        print("GA failed to find a solution.")
        sys.exit(1)
    write_output(best)
    print("Best fitness:", best_fit)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", "-d", default="data", help="data directory with CSVs")
    args = parser.parse_args()
    main(args.data)
