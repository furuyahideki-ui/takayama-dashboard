import pandas as pd
import json

df = pd.read_excel('Overnights/2025.xlsx')
with open('cols.json', 'w', encoding='utf-8') as f:
    json.dump(df.columns.tolist(), f, ensure_ascii=False)
