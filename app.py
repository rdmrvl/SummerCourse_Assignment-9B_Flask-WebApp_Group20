import pandas as pd
from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Load the dataset, skipping the first row
file_path = 'Data_Timbulan_Sampah_SIPSN_KLHK.xlsx'
data = pd.read_excel(file_path, skiprows=1)

# Clean column names by stripping any whitespace
data.columns = data.columns.str.strip()

# Get unique provinces and years
provinces = sorted(data['Provinsi'].unique())
years = sorted(data['Tahun'].unique())

@app.route('/')
def index():
    return render_template('index.html', provinces=provinces, years=years)

def generate_stats(selected_provinces, start_year, end_year):
    # Filter data for selected provinces and year range
    filtered_data = data[(data['Provinsi'].isin(selected_provinces)) & (data['Tahun'].between(start_year, end_year))]

    # Total annual waste generation per province
    total_annual = filtered_data.groupby(['Tahun', 'Provinsi'])['Timbulan Sampah Tahunan(ton)'].sum().reset_index()

    # Average annual waste generation per province
    avg_annual = total_annual.groupby('Provinsi')['Timbulan Sampah Tahunan(ton)'].mean().reset_index()

    # Province producing the most and least annual waste 
    most_waste = total_annual.loc[total_annual.groupby('Tahun')['Timbulan Sampah Tahunan(ton)'].idxmax()]
    least_waste = total_annual.loc[total_annual.groupby('Tahun')['Timbulan Sampah Tahunan(ton)'].idxmin()]

    # Categorize provinces based on average annual waste
    def categorize(waste):
        if waste <= 100000:
            return "GREEN"
        elif 100000 < waste <= 700000:
            return "ORANGE"
        else:
            return "RED"

    avg_annual['Category'] = avg_annual['Timbulan Sampah Tahunan(ton)'].apply(categorize)
    avg_annual['Timbulan Sampah Tahunan(ton)'] = avg_annual['Timbulan Sampah Tahunan(ton)'].map('{:.2f}'.format)

    # Create plots for visualizations
    # Plot 1: Total Annual Waste by Province
    plt.figure(figsize=(10, 5))
    for prov in total_annual['Provinsi'].unique():
        province_data = total_annual[total_annual['Provinsi'] == prov]
        plt.plot(province_data['Tahun'], province_data['Timbulan Sampah Tahunan(ton)'], label=prov)
    plt.legend()
    plt.title('Total Annual Waste by Province')
    plt.xlabel('Year')
    plt.ylabel('Total Annual Waste (tons)')
    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plot_url1 = base64.b64encode(img1.getvalue()).decode()

    # Plot 2: Categorization of Average Annual Waste Generation 
    avg_annual_counts = avg_annual['Category'].value_counts().reindex(['GREEN', 'ORANGE', 'RED'], fill_value=0)
    plt.figure(figsize=(10, 5))
    avg_annual_counts.plot(kind='bar', color=avg_annual_counts.index.map({'GREEN': 'green', 'ORANGE': 'orange', 'RED': 'red'}))
    plt.title('Categorization of Average Annual Waste Generation')
    plt.xlabel('Category')
    plt.ylabel('Number of Provinces')
    plt.xticks(rotation=0)
    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    plot_url2 = base64.b64encode(img2.getvalue()).decode()

    return {
        'total_annual': total_annual.to_html(index=False),
        'avg_annual': avg_annual.to_html(index=False),
        'most_waste': most_waste.to_html(index=False),
        'least_waste': least_waste.to_html(index=False),
        'plot_url1': plot_url1,
        'plot_url2': plot_url2
    }

@app.route('/stats', methods=['POST'])
def stats():
    selected_provinces = request.form.getlist('provinces')
    start_year = int(request.form['start_year'])
    end_year = int(request.form['end_year'])
    stats = generate_stats(selected_provinces, start_year, end_year)
    return render_template('stats.html', **stats)

if __name__ == '__main__':
    app.run(debug=True)
