import pandas as pd
import os

# Load timetable
df = pd.read_csv("../data/generated_timetable.csv")

# Split day and time
df[['day', 'time']] = df['timeslot'].str.split('_', expand=True)

# Create output directory
os.makedirs(".", exist_ok=True)

def generate_html(filtered_df, title, filename):
    days = sorted(filtered_df['day'].unique())
    times = sorted(filtered_df['time'].unique())

    table = {}

    for _, row in filtered_df.iterrows():
        key = (row['day'], row['time'])
        table[key] = f"""
        <b>{row['course']}</b><br>
        Room: {row['room']}<br>
        Teacher: {row['teacher']}
        """

    html = f"""
    <html>
    <head>
        <title>{title}</title>
        <style>
            table {{ border-collapse: collapse; width: 100%; text-align: center; }}
            th, td {{ border: 1px solid black; padding: 10px; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h2 align="center">{title}</h2>
        <table>
            <tr>
                <th>Time / Day</th>
    """

    for d in days:
        html += f"<th>{d}</th>"
    html += "</tr>"

    for t in times:
        html += f"<tr><th>{t}</th>"
        for d in days:
            html += f"<td>{table.get((d, t), '-')}</td>"
        html += "</tr>"

    html += """
        </table>
    </body>
    </html>
    """

    with open(filename, "w") as f:
        f.write(html)

    print(f"✅ Generated {filename}")

# 1️⃣ Global timetable
generate_html(df, "Automated Timetable Generator", "timetable.html")

# 2️⃣ Group-wise timetables
for group in df['group'].unique():
    group_df = df[df['group'] == group]
    generate_html(group_df, f"Timetable for Group {group}", f"group_{group}.html")
