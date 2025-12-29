import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt

df = pd.read_csv("data/generated_timetable.csv")

# Split day and time
df[['day', 'time']] = df['timeslot'].str.split('_', expand=True)

print("\n📊 TIMETABLE QUALITY METRICS\n")

# 1️⃣ Total sessions
print(f"Total sessions scheduled: {len(df)}")

# 2️⃣ Average lectures per day (group-wise)
group_day_count = df.groupby(['group', 'day']).size()
avg_lectures = group_day_count.groupby('group').mean()

print("\nAverage lectures per day (Group-wise):")
for g, val in avg_lectures.items():
    print(f"  Group {g}: {val:.2f}")

# 3️⃣ Teacher workload
teacher_load = df['teacher'].value_counts()

print("\nTeacher workload:")
for t, c in teacher_load.items():
    print(f"  Teacher {t}: {c} lectures")

# 4️⃣ Teacher idle gaps
teacher_gaps = defaultdict(int)
for t in df['teacher'].unique():
    slots = sorted(df[df['teacher'] == t]['timeslot'])
    teacher_gaps[t] = max(0, len(slots) - len(set(slots)))

print("\nTeacher idle gaps:")
for t, g in teacher_gaps.items():
    print(f"  Teacher {t}: {g}")

# 📈 Plot: Teacher workload
teacher_load.plot(kind='bar', title='Teacher Workload')
plt.ylabel("Number of Lectures")
plt.tight_layout()
plt.show()

# 📈 Plot: Average lectures per day
avg_lectures.plot(kind='bar', title='Average Lectures per Day (Group-wise)')
plt.ylabel("Lectures per Day")
plt.tight_layout()
plt.show()
