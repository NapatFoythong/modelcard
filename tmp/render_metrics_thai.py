from pathlib import Path
import csv
import matplotlib.pyplot as plt
from matplotlib import font_manager

root = Path(__file__).resolve().parents[1]
font_file = Path.home() / 'AppData/Local/Microsoft/Windows/Fonts/THSarabunNew.ttf'
font_manager.fontManager.addfont(str(font_file))
font_name = font_manager.FontProperties(fname=str(font_file)).get_name()
plt.rcParams.update({'font.family': font_name, 'font.size': 19})
with (root / 'model_card_metrics_full.csv').open(encoding='utf-8', newline='') as stream:
    rows = [r for r in csv.DictReader(stream) if r['model'] != 'Selected']
names = [r['model'] for r in rows]
fig, axes = plt.subplots(1, 2, figsize=(11, 2.8))
for ax, key, title in zip(axes, ['AP', 'Brier'], ['คุณภาพการจัดอันดับ AP สูงดีกว่า', 'ความคลาดเคลื่อน Brier ต่ำดีกว่า']):
    values = [float(r[key]) for r in rows]
    ax.barh(names, values, color=['#a4acb8', '#4178a8', '#16877b'])
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlim(0, max(values) * 1.25)
    for i, value in enumerate(values):
        ax.text(value + max(values) * .025, i, f'{value:.3f}', va='center')
    ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(root / 'output/graphs/09_กราฟตัวชี้วัดสำหรับรายงาน.png', dpi=220)
plt.close(fig)
