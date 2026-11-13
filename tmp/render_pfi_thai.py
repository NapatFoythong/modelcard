from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

root = Path(__file__).resolve().parents[1]
font_file = Path.home() / 'AppData/Local/Microsoft/Windows/Fonts/THSarabunNew.ttf'
font_manager.fontManager.addfont(str(font_file))
font = font_manager.FontProperties(fname=str(font_file))
plt.rcParams.update({'font.family': font.get_name(), 'font.size': 20})
result = json.loads((root / 'model_card_results.json').read_text(encoding='utf-8'))
means = np.array(result['pfi_mean'])
sd = np.array(result['pfi_sd'])
labels = np.array(['ระดับการศึกษา', 'ประสบการณ์ทำงาน', 'คะแนนสัมภาษณ์', 'คะแนนทักษะ'])
order = np.argsort(means)
fig, ax = plt.subplots(figsize=(9, 3.5))
ax.barh(labels[order], means[order], xerr=sd[order], color='#16877b', capsize=4)
ax.set_xlabel('คะแนนการจัดอันดับที่ลดลงเมื่อสลับข้อมูล (AP)')
ax.set_title('ข้อมูลที่โมเดลพึ่งพาในการให้คะแนน')
ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(root / 'tmp/model_card_qa/pfi_thai.png', dpi=200)
plt.close(fig)
