import pandas as pd
from collections import defaultdict

df = pd.read_csv("data/generated_timetable.csv")

teacher_clash = defaultdict(int)
room_clash = defaultdict(int)
group_clash = defaultdict(int)

for _, row in df.iterrows():
    key_t = (row['teacher'], row['timeslot'])
    key_r = (row['room'], row['timeslot'])
    key_g = (row['group'], row['timeslot'])

    teacher_clash[key_t] += 1
    room_clash[key_r] += 1
    group_clash[key_g] += 1

print("\n📋 VALIDATION REPORT\n")

print("Teacher Clashes:")
print("✔ 0 clashes" if all(v == 1 for v in teacher_clash.values()) else "❌ Clash detected")

print("\nRoom Clashes:")
print("✔ 0 clashes" if all(v == 1 for v in room_clash.values()) else "❌ Clash detected")

print("\nGroup Clashes:")
print("✔ 0 clashes" if all(v == 1 for v in group_clash.values()) else "❌ Clash detected")
