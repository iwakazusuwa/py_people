import pandas as pd
import numpy as np
import os
from scipy.spatial import distance
#=============================================
# Inputファイル情報
#=============================================
INPUT_DNAME = "人流データ.csv"
INPUT_folder = "2_data"        
#=============================================
# Outputファイル情報
#=============================================
OUTPUT_DNAME = "データ縦持ち整形.csv"
OUTPUT_DIS = "データ縦持ち整形_距離追加.csv"
OUTPUT_folder = "3_output"
#=============================================
# カレントパス
#=============================================
current_dpath = os.getcwd()
#print("INFO:カレントパス:" + current_dpath)
#=============================================
# パレントパス
#=============================================
parent_dpath =os.path.sep.join(current_dpath.split(os.path.sep)[:-1])
#print("INFO:パレントパス:" + parent_dpath)   
#=============================================
# Inputデータファイル Path
#=============================================
input_dpath =os.path.sep.join([parent_dpath + '\\' + INPUT_folder,INPUT_DNAME])
#print("INFO:データファイルパス:" + input_dpath) 
#=============================================
# Outputデータファイル Path
#=============================================
output_dpath =parent_dpath + '\\' + OUTPUT_folder
#print("INFO:出力先のフォルダパス:" + output_dpath)
#=============================================
# Inputデータ読み込む
#=============================================
df = pd.read_csv(input_dpath,encoding='shift-JIS')
df.head(3)


#=============================================
# 検知数が0件の行は削除
#=============================================
df = df.query('0 < 検知数')

 #--index振りなおす
df_a = df.reset_index(drop=True)

#=============================================
# データを縦持ちにする
#=============================================
df_list = pd.DataFrame()

#　1行ずつ処理を行っていく
for index, row in df_a.iterrows():
    df_b = df_a.loc[[index]]  #　1行抜き出す
    
    if df_b.empty:
        continue  # もし何もなければスキップ

    # 検知数（人数）を取得
    Lop_cnt = df_b['検知数'].iloc[0]

    # 最初の idのカラム位置
    col = 2
    #検知数だけ処理を繰り返す
    for i in range(Lop_cnt):
        try:
            new_row = {
                '検知数': df_b.iloc[0, 0],
                'time_step': df_b.iloc[0, 1],
                'id': df_b.iloc[0, col],
                'x': df_b.iloc[0, col + 1],
                'y': df_b.iloc[0, col + 2]
            }
            # 記憶
            df_list = pd.concat([df_list, pd.DataFrame([new_row])], ignore_index=True)
            # 次のidカラム位置
            col += 3
        except IndexError:
            print(f"列不足エラー: index={index}, col={col}")
            continue
            
#=============================================
# csvファイルに出力
#=============================================            
df_list.to_csv(output_dpath + "\\" + OUTPUT_DNAME ,encoding='cp932',index =False)
#======================================================
#　idのデータを取り出して、time_stepソート、移動距離追加
#======================================================  
df_c = df_list['id']
df_d = df_c.drop_duplicates()

result_rows = []

for current_id in df_d:
    df_e = df_list.query('id == @current_id').sort_values('time_step')
    df_f = df_e.reset_index(drop=True)

    for index in range(len(df_f)):
        row = df_f.iloc[index]
        
        if index == 0:
            oldx = row['x']
            oldy = row['y']
            dis_c = 0
            moji = 0
        else:
            newx = row['x']
            newy = row['y']
            dis_c = distance.euclidean((oldx, oldy), (newx, newy))
            idokaku = np.rad2deg(np.arctan2(newy - oldy, newx - oldx))
            oldx, oldy = newx, newy

        result_rows.append({
            'time_step': row['time_step'],
            'id': current_id,
            'x': row['x'],
            'y': row['y'],
            '移動距離': dis_c,
        })
        
df_result = pd.DataFrame(result_rows)
#=============================================
# csvファイルに出力
#=============================================    
df_result.to_csv(output_dpath + "\\" + OUTPUT_DIS ,encoding='cp932',index =False)
df_list.head(3)