#人流トラジェクトリーデータ (横持）を縦持ちに整形後、ヒートマップの上に動線グラフを重ねる

import pandas as pd
import numpy as np
import os
from scipy.spatial import distance

import codecs
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

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
#df_list.head(3)


#グラフ作成
# =========================
# 分割するid数（人数）を指定
# =========================
group_size = 5

# =========================
# 動線色分け
# =========================  
clrs = [
    'red', 'green', 'blue', 
    'purple', 'orange', 'gold', 
    'lime', 'navy', 'pink', 
    'cyan', 'brown'
    ]
# =========================
# 背景ヒートマップデータ
# =========================
L_Len = len(df_result)

xedges = np.linspace(0,100,51)
yedges = np.linspace(0,100,51)

position_x = df_result['x']
position_y = df_result['y']

H, xedges, yedges = np.histogram2d(position_x, position_y, bins=(xedges, yedges))
H = (H / L_Len) * 100

# =========================
# 全IDを指定数ずつに分割
# =========================
id_list = list(df_d)

groups = [id_list[i:i+group_size] for i in range(0, len(id_list), group_size)]

# =========================
# 各グループでグラフ生成
# =========================
for grp_idx, id_group in enumerate(groups):
    fig, ax = plt.subplots(figsize=(14,12), dpi=130)

    # 背景ヒートマップ
    img = ax.imshow(
        H.T,
        origin='lower',
        cmap='PuRd',
        extent=[0,100,0,100],
        alpha=0.7,
        vmin=0.05
    )

    ax.set_xlim(0,100)
    ax.set_ylim(0,100)

    # カラーバー
    cbar = plt.colorbar(img, ax=ax)
    cbar.set_label('Presence Percentage (%)')

    # 動線描画
    for color_idx, current_id in enumerate(id_group):
        data_a = df_list.query('id == @current_id').sort_values('time_step')
        data_b = data_a.reset_index(drop=True)

        if len(data_b) > 0:
            line_color = clrs[color_idx % len(clrs)]
            oldx, oldy = None, None

            # スタート地点の座標
            startx = data_b.loc[0, 'x']
            starty = data_b.loc[0, 'y']

            # スタート地点にIDを描く
            ax.text(
                startx,
                starty,
                str(current_id),
                fontsize=12,
                color=line_color,
                weight='bold',
                ha='center',
                va='center',
                bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.3')
            )

            for idx, row in data_b.iterrows():
                newx = row['x']
                newy = row['y']

                if oldx is not None:
                    # 線
                    ax.plot(
                        [oldx, newx],
                        [oldy, newy],
                        color=line_color,
                        linewidth=2,
                        alpha=0.8
                    )
                    # 矢印
                    ax.annotate(
                        '',
                        xy=(newx, newy),
                        xytext=(oldx, oldy),
                        arrowprops=dict(
                            arrowstyle="->",
                            color=line_color,
                            lw= 1,   # ラインの太さ                         
                            mutation_scale=20  # 矢印のサイズ　10:小.20:中.30:大
                        )
                    )
                oldx, oldy = newx, newy

    # 軸タイトル
    ax.set_title(f"ID Group {grp_idx + 1} Movement Paths", fontsize=16)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    # 軸目盛りの刻み指定
    ax.set_xticks(np.arange(0, 110, 5))
    ax.set_yticks(np.arange(0, 110, 5))

    # 画像として保存
    plt.tight_layout()
    plt.savefig(f"{output_dpath}\\movement_group_{grp_idx+1}.png", dpi=130)
    plt.show()
    #plt.close()




