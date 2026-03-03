import pandas as pd
import glob

csv_files = glob.glob("irikomi/city*.csv")
df_list = []
for file in csv_files:
    df_temp = pd.read_csv(file, encoding="shift_jis", low_memory=False)
    df_list.append(df_temp)

df = pd.concat(df_list, ignore_index=True)

required_columns = ['年', '月', '地域名称', '人数']
df = df[required_columns]
df['人数'] = pd.to_numeric(df['人数'], errors='coerce').fillna(0)

# 高山市
df_taka = df[df['地域名称'] == '高山市'].groupby(['年', '月'], as_index=False)['人数'].sum()
df_taka_24 = df_taka[df_taka['年']==2024].rename(columns={'人数':'前年人数'})
df_taka_24['年'] = 2025
df_taka_25 = df_taka[df_taka['年']==2025]
df_m = pd.merge(df_taka_25, df_taka_24[['年','月','前年人数']], on=['年','月'], how='left')
df_m['高山対前年比'] = (df_m['人数']/df_m['前年人数']*100).round(1)

# 全国
df_all = df.groupby(['年', '月'], as_index=False)['人数'].sum()
df_all_24 = df_all[df_all['年']==2024].rename(columns={'人数':'全国前年人数'})
df_all_24['年'] = 2025
df_all_25 = df_all[df_all['年']==2025]
df_all_m = pd.merge(df_all_25, df_all_24[['年','月','全国前年人数']], on=['年','月'], how='left')
df_all_m['全国対前年比'] = (df_all_m['人数']/df_all_m['全国前年人数']*100).round(1)

res = pd.merge(df_m[['月','人数','前年人数','高山対前年比']], df_all_m[['月','全国対前年比']], on='月', how='left')
print(res)
