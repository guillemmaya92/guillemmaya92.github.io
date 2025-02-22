# Libraries
# ===================================================
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
from io import StringIO
from scipy.interpolate import interp1d
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.patches as patches

# Manual Data
# ===================================================
btcprice = 100000

# Data Extraction
# ===================================================
url = "https://bitinfocharts.com/top-100-richest-bitcoin-addresses.html"
soup = BeautifulSoup(requests.get(url).text, "html.parser")
table = soup.find("table", {"class": "table table-condensed bb"})
df = pd.read_html(StringIO(str(table)))[0]

# Data Transformation
# ===================================================
# Select columns
df = df[['Balance, BTC', 'Addresses']]

# Extract start and end range
df['Start'] = df['Balance, BTC'].str.extract(r'[\[\(](\d[\d,\.]*)')
df['End'] = df['Balance, BTC'].str.extract(r'-\s([\d,\.]+)\)')

# Convert to values
df['Addresses'] = df['Addresses'].replace({',': ''}, regex=True).astype(int)
df['Start'] = df['Start'].replace({',': ''}, regex=True).astype(float)
df['End'] = df['End'].replace({',': ''}, regex=True).astype(float)

# Select columns
df = df[['Addresses', 'Start', 'End']]

# Change first and last value
df.loc[df.index[0], 'Start'] = 0.000001
df.loc[df.index[-1], 'End'] = 250000

# Create a list
result = []

# Iterate over each row 
for index, row in df.iterrows():
    n = int(row['Addresses'])
    start = row['Start']
    end = row['End']
    
    # Generate a distribution
    valores = np.logspace(np.log10(start), np.log10(end), n)
        
    # Add values to result list
    result.extend(valores)

# Crear a dataframe with all values
df = pd.DataFrame(result, columns=['btc'])

# USD Value, Filter >5000 and count
df['usd'] = df['btc'] * btcprice
df = df[df['usd'] > 5000]
df['count'] = 1

# Grouping by 100 percentiles
df['percentile'] = pd.qcut(df['btc'], 100, labels=False) + 1

# Grouping by 10 percentiles
df['percentile2'] = pd.cut(
    df['percentile'], 
    bins=range(1, 111, 10), 
    right=False, 
    labels=[i + 9 for i in range(1, 101, 10)]
).astype(int)

# Calculate GINI Index
def gini(x):
    x = np.array(x)
    x = np.sort(x)
    n = len(x)
    gini_index = (2 * np.sum(np.arange(1, n + 1) * x) - (n + 1) * np.sum(x)) / (n * np.sum(x))
    return gini_index
gini_value = gini(df['usd'])

# Summarizing data 
df = df.groupby(['percentile', 'percentile2'])[['usd', 'btc', 'count']].sum().reset_index()

# Average price
df['average_usd'] = df['usd'] / df['count']
df['percentage'] = df['usd'] / df['usd'].sum()

# Select columns
df = df[['percentile', 'percentile2', 'usd', 'count', 'average_usd', 'percentage']]

# Define palette
color_palette = {
    10: "#050407",
    20: "#07111e",
    30: "#15334b",
    40: "#2b5778",
    50: "#417da1",
    60: "#5593bb",
    70: "#5a7aa3",
    80: "#6d5e86",
    90: "#a2425c",
    100: "#D21E00"
}

# Map palette color
df['color'] = df['percentile2'].map(color_palette)

# Percentiles dataframe 2
df2 = df.copy()
df2 = df2.groupby(['percentile2', 'color'], as_index=False)[['usd', 'count']].sum()
df2['average_usd'] = df2['usd'] / df2['count']
df2['percentage'] = df2['usd'] / (df2['usd']).sum()
df2['count'] = 10

print(df)

# Data Visualization
# ===================================================
# Font Style
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Open Sans'], 'font.size': 10})

# Create the figure and suplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [10, 0.5]})

# First Plot
# ==================
# Plot Bars
bars = ax1.bar(df['percentile'], df['average_usd'], color=df['color'], edgecolor='darkgrey', linewidth=0.5, zorder=2)

# Title and labels
ax1.text(0, 1.1, 'Bitcoin Wealth Distribution', fontsize=13, fontweight='bold', ha='left', transform=ax1.transAxes)
ax1.text(0, 1.06, 'Intrapercentile Analysis of Wealth Concentration (excluding < 5000$ wallets)', fontsize=9, color='#262626', ha='left', transform=ax1.transAxes)
ax1.set_xlabel('% Wallets', fontsize=10, weight='bold')
ax1.set_ylabel('Wealth ($)', fontsize=10, weight='bold')

# Configuration
ax1.grid(axis='x', linestyle='-', alpha=0.5, zorder=1)
ax1.set_xlim(0, 101)
ax1.set_ylim(0, 3000000)
ax1.set_xticks(np.arange(0, 101, step=10))
ax1.set_yticks(np.arange(0, 3000001, step=500000))
ax1.tick_params(axis='x', labelsize=10)
ax1.tick_params(axis='y', labelsize=10)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Function to format Y axis
def format_func(value, tick_number):
    if value >= 1e6:
        return '{:,.1f}M'.format(value / 1e6)
    else:
        return '{:,.0f}K'.format(value / 1e3)

# Formatting x and y axis
ax1.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.0f}%'))
ax1.yaxis.set_major_formatter(FuncFormatter(format_func))

# Lines and area to separate outliers
ax1.axhline(y=2770000, color='black', linestyle='--', linewidth=0.5, zorder=4)
ax1.axhline(y=2730000, color='black', linestyle='--', linewidth=0.5, zorder=4)
ax1.add_patch(patches.Rectangle((0, 2730000), 105, 40000, linewidth=0, edgecolor='none', facecolor='white', zorder=3))

# Y Axis modify the outlier value
labels = [item.get_text() for item in ax1.get_yticklabels()]
labels[-1] = '31M'
ax1.set_yticklabels(labels)

# Show labels each 10 percentile
for i, (bar, value) in enumerate(zip(bars, df['average_usd'])):
    value_rounded = round(value, -3)
    if i % 10 == 0:
        ax1.text(bar.get_x() + bar.get_width() / 2, 
                 abs(bar.get_height()) * 1.4 + 50000,
                 f'{value_rounded:,.0f}',
                 ha='center', 
                 va='bottom', 
                 fontsize=8.5,
                 color='#2c2c2c', 
                 rotation=90)

# Show GINI Index
ax1.text(
    0.09, 0.97, f"Gini Index: {gini_value:.2f}", 
    transform=ax1.transAxes,
    fontsize=8.5,
    color='black',
    ha='right',
    va='top', 
    bbox=dict(boxstyle="round,pad=0.3", edgecolor='gray', facecolor='white')
)

# Second Plot
# ==================
# Plot Bars
ax2.barh([0] * len(df2), df2['count'], left=df2['percentile2'] - df2['count'], color=df2['color'])

# Configuration
ax2.grid(axis='x', linestyle='-', color='white', alpha=1, linewidth=0.5)
ax2.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
ax2.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.spines['bottom'].set_visible(False)
x_ticks = np.linspace(df2['percentile2'].min(), df2['percentile2'].max(), 10)
ax2.set_xticks(x_ticks)
ax2.set_xlim(0, 101)

# Add label values
for i, row in df2.iterrows():
    plt.text(row['percentile2'] - row['count'] + row['count'] / 2, 0, 
             f'{row["percentage"] * 100:.2f}%', ha='center', va='center', color='white', fontweight='bold')
    
 # Add Year label
formatted_date = 2024 
ax1.text(1, 1.1, f'{formatted_date}',
    transform=ax1.transAxes,
    fontsize=22, ha='right', va='top',
    fontweight='bold', color='#D3D3D3')

# Add Data Source
ax2.text(0, -0.5, 'Data Source: BitInfoCharts. "Top 100 Richest Bitcoin Addresses."',
         transform=ax2.transAxes,
         fontsize=8,
         color='#2c2c2c')

# Adjust layout
plt.tight_layout()

# Save it...
plt.savefig("C:/Users/guill/Downloads/FIG_BITINFO_Bitcoin_Wealth_Distribution.png", dpi=300, bbox_inches='tight') 

# Plot it!
plt.show()