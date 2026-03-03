import pandas as pd
import json

df = pd.read_excel('Overnights/2025.xlsx')
# Replace NA with empty string for JSON serialization
df = df.fillna("")
with open('data.json', 'w', encoding='utf-8') as f:
    df.to_json(f, orient='records', force_ascii=False)
