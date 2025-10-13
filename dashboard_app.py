
import pandas as pd
import json
from flask import Flask, render_template, jsonify

app = Flask(__name__)

def process_data():
    """Reads and processes the patient data from the CSV file."""
    try:
        df = pd.read_csv("https://raw.githubusercontent.com/2510aaae4/12A-dashboard/refs/heads/main/12A_patient_list_selenium.csv")
    except FileNotFoundError:
        return None, None, None, None, {"error": "CSV file not found."}

    # --- Data Cleaning and Feature Engineering ---
    df['住院天數'] = df['入院日'].str.extract(r'\((\d+)日\)').fillna(0).astype(int)
    df['照顧者'] = df['Primary Care'].str.extract(r'([^\(]+)').fillna('N/A')
    df['MEWS'] = pd.to_numeric(df['MEWS'], errors='coerce').fillna(0)

    # --- Data Aggregation ---
    physicians = sorted(df['主治醫師'].unique().tolist())
    primary_care_counts = df.groupby('照顧者').size().reset_index(name='count').sort_values(by='count', ascending=False).to_dict('records')

    # --- Top 2 Physicians Stats ---
    physician_stats = df.groupby('主治醫師').agg(
        patient_count=('病歷號', 'count'),
        avg_stay=('住院天數', 'mean'),
        high_mews_count=('MEWS', lambda x: x[x >= 4].count())
    ).reset_index()
    
    top_physicians_stats = physician_stats.sort_values(by='patient_count', ascending=False).head(2).to_dict('records')
    
    # Set main physicians to be the top 2
    main_physician_names = [p['主治醫師'] for p in top_physicians_stats]

    # Round the average stay for cleaner display
    for stat in top_physicians_stats:
        stat['avg_stay'] = round(stat['avg_stay'], 1)

    patients_data = df.to_dict('records')
    
    return patients_data, physicians, primary_care_counts, top_physicians_stats, main_physician_names, None

@app.route('/')
def dashboard():
    """Renders the main dashboard page."""
    patients, physicians, primary_care_counts, top_physicians, main_physicians, error = process_data()
    
    if error:
        return jsonify(error), 404

    return render_template(
        'dashboard.html',
        patients_json=json.dumps(patients),
        physicians=physicians,
        primary_care_counts=primary_care_counts,
        top_physicians_stats=top_physicians,
        main_physician_names=main_physicians
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
