"""Build a sectioned, visual notebook from the existing model-card analysis."""
from pathlib import Path
import nbformat as nbf

root = Path(__file__).resolve().parent
script = (root / 'model_card_core.py').read_text(encoding='utf-8')
nb = nbf.v4.new_notebook()
cells = []
def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))
def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))

md('''# Recruitment — Explainable AI Model Card
## วิเคราะห์การคัดเลือกผู้สมัครด้วยกราฟและคำอธิบาย
Notebook นี้แบ่งโค้ดเป็นส่วน ๆ แบบ Lab อ่านคำอธิบายแล้วรันเซลล์ตามลำดับจากบนลงล่าง
ใช้ข้อมูล `recruitment_data_cleaned.csv` และแสดงผลด้วยกราฟ แทนการพิมพ์ JSON ยาว ๆ

**คำถามหลัก:** โมเดลทำงานดีแค่ไหน ผิดพลาดแบบใด และตัวแปรใดมีผลต่อคำทำนาย?

**ขอบเขต:** ทำนาย `HiringDecision` ที่บันทึกอยู่ในข้อมูล ไม่ใช่ความสามารถจริงของผู้สมัคร
คำอธิบายโมเดลไม่ใช่หลักฐานเชิงเหตุและผล และไม่ควรใช้ผลนี้ตัดสินรับคนโดยอัตโนมัติ''')
md('''## 0. Setup — เตรียมเครื่องมือ
เปิด Notebook นี้ใน VS Code หรือ Jupyter แล้วเลือก Python kernel ที่ต้องการใช้
หากยังไม่มีแพ็กเกจ ให้เอา `#` หน้า `%pip` ในเซลล์ถัดไปออกแล้วรัน จากนั้น restart kernel
ชื่อบนแกนกราฟใช้ภาษาอังกฤษเพื่อให้แสดงได้โดยไม่ต้องติดตั้งฟอนต์ไทย''')
code('# %pip install numpy pandas "scikit-learn>=1.2" "matplotlib>=3.9" ipykernel "lime==0.2.0.1"')
imports = script[:script.index('root = Path')]
code(imports + '''
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from sklearn.metrics import PrecisionRecallDisplay, ConfusionMatrixDisplay

plt.rcParams.update({'figure.figsize': (9, 4.5), 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': False,
                     'font.size': 11, 'figure.dpi': 110})
COLORS = ['#a4acb8', '#4178a8', '#16877b', '#c97140']
''')
md('''## 1. โหลดและสำรวจข้อมูล
วาง CSV ไว้ในโฟลเดอร์เดียวกับ Notebook หรือแก้ `source` เป็นพาธของไฟล์
ตรวจชื่อคอลัมน์และค่าของเป้าหมายก่อนเริ่มวิเคราะห์''')
code('''root = Path.cwd()
source = root / 'recruitment_data_cleaned.csv'
seed = 42
data = pd.read_csv(source)
required = ['Age', 'Gender', 'EducationLevel', 'ExperienceYears',
            'InterviewScore', 'SkillScore', 'HiringDecision']
missing_columns = sorted(set(required) - set(data.columns))
if missing_columns:
    raise ValueError(f'Missing columns: {missing_columns}')
if data.HiringDecision.isna().any() or set(data.HiringDecision.unique()) != {0, 1}:
    raise ValueError('HiringDecision must contain both 0 and 1, with no missing values.')
duplicate_count = int(data.duplicated().sum())
if duplicate_count:
    raise ValueError(f'Found {duplicate_count} duplicate rows; resolve duplicates before CV.')
data['_csv_row'] = np.arange(len(data)) + 2
raw = data.copy()
display(data.head())
fig, ax = plt.subplots(figsize=(6, 4))
counts = data.HiringDecision.value_counts().reindex([0, 1])
ax.bar(['Not hired (0)', 'Hired (1)'], counts, color=[COLORS[0], COLORS[2]])
ax.set(title='Recorded hiring decisions', ylabel='Applicants')
plt.tight_layout()
plt.show()
''')
md('''## 2. เตรียมข้อมูลและกำหนดตัวแปร
ใช้ EducationLevel, ExperienceYears, InterviewScore และ SkillScore เพื่อทำนาย
เก็บ Age และ Gender ไว้ตรวจผลแยกกลุ่ม ไม่ใส่เป็นตัวแปรฝึกโมเดล

ใช้ค่าประสบการณ์จาก CSV โดยไม่ใช้ Age หรือ Gender แก้ไขตัวแปรที่ใช้ฝึก
Age และ Gender ใช้ตรวจข้อมูลและผลแยกกลุ่มเท่านั้น
เติมค่ามัธยฐานและแปลงข้อมูลภายในแต่ละชุดฝึก เพื่อลดข้อมูลรั่วไหล''')
code(script[script.index("features ="):script.index('def pipeline')])
code('''fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].bar(['CSV input', 'Training input'],
            [raw.ExperienceYears.isna().sum(), data.ExperienceYears.isna().sum()],
            color=[COLORS[0], COLORS[1]])
axes[0].set(title='Missing experience values', ylabel='Applicants')
for decision, label, color in [(0, 'Not hired', COLORS[0]), (1, 'Hired', COLORS[2])]:
    axes[1].hist(data.loc[data.HiringDecision == decision, 'SkillScore'],
                 bins=15, density=True, alpha=.6, label=label, color=color)
axes[1].set(title='Skill score by recorded outcome', xlabel='Skill score', ylabel='Density')
axes[1].legend()
plt.tight_layout()
plt.show()
''')
from notebook_sections import pretraining, advanced
pretraining(md, code)
md('''## 3. สร้าง Pipeline และฟังก์ชันช่วย
เปรียบเทียบ Dummy, Logistic Regression และ Gradient Boosting
ฟังก์ชันอธิบายรายบุคคลคำนวณ Shapley แบบครบทุกชุดของตัวแปรทั้ง 4 ตัว
โดยแทนค่าตัวแปรที่ยังไม่เปิดด้วยข้อมูลอ้างอิงจากชุดฝึก (interventional background)''')
code(script[script.index('def pipeline'):script.index('def threshold')])
code(script[script.index('def threshold'):script.index('def shap_values')])
code(script[script.index('def shap_values'):script.index('pred=np.zeros')])
md('''## 4. ฝึกและประเมินด้วย Nested Cross-validation
แบ่ง outer 5 folds และ inner 4 folds เลือกพารามิเตอร์ด้วย Average Precision (AP)
เลือก Gradient Boosting เมื่อ inner AP สูงกว่า Logistic Regression มากกว่า 0.01 มิฉะนั้นเลือก Logistic Regression
เลือก threshold จากผลทำนาย inner CV โดยตั้งเป้า recall อย่างน้อย 90%
เป้าหมายนี้ไม่ได้รับประกันว่า recall บน outer test จะถึง 90%

เซลล์นี้ใช้เวลาสักครู่ ผลประเมินต่อจากนี้ใช้คำทำนายของแถวที่ไม่ได้อยู่ในชุดฝึกของ outer fold นั้น''')
code(script[script.index('pred=np.zeros'):script.index('cases=[]')]
     + "\ndisplay(Markdown('**ฝึกครบแล้ว — ดูผลเปรียบเทียบในกราฟด้านล่าง**'))")
md('''## 5. เปรียบเทียบคุณภาพโมเดล
AP ยิ่งสูงยิ่งดี ส่วน Brier score ยิ่งต่ำยิ่งดี
เส้น Precision–Recall แสดงการแลกระหว่างความแม่นของคำทำนายบวกกับการค้นหาผู้ที่มี label 1
Selected คือขั้นตอนเลือกโมเดลภายในแต่ละ fold จึงอาจให้ผลซ้ำกับโมเดลตัวใดตัวหนึ่ง''')
code('''model_names = names + ['Selected']
metrics = pd.DataFrame({name: summary(y, pred[:, i], dec[:, i])
                        for i, name in enumerate(model_names)}).T
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for ax, column, title in zip(axes, ['ap', 'brier'],
                            ['Average precision (higher is better)', 'Brier score (lower is better)']):
    ax.barh(model_names, metrics[column], color=COLORS)
    ax.set(title=title, xlabel='Score', xlim=(0, 1))
plt.tight_layout()
plt.show()
fig, ax = plt.subplots(figsize=(8, 5))
for i, name in enumerate(model_names):
    PrecisionRecallDisplay.from_predictions(y, pred[:, i], name=name, ax=ax,
                                           color=COLORS[i], linestyle='--' if i == 3 else '-')
ax.axhline(y.mean(), color='gray', linestyle=':', label='Positive-label prevalence')
ax.set_title('Out-of-fold precision–recall curves')
ax.legend(fontsize=9)
plt.tight_layout()
plt.show()
''')
md('''## 6. โมเดลผิดพลาดแบบใด?
FN = ข้อมูลระบุว่ารับเข้าทำงาน แต่โมเดลทำนายว่าไม่รับ
FP = ข้อมูลระบุว่าไม่รับ แต่โมเดลทำนายว่ารับ
คำว่า “ผิด” หมายถึงไม่ตรงกับ label ในข้อมูล ไม่ได้พิสูจน์ว่าการตัดสินใจเดิมถูกต้อง''')
code('''fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
ConfusionMatrixDisplay.from_predictions(y, dec[:, 3].astype(int),
    display_labels=['Not hired', 'Hired'], cmap='Blues', colorbar=False, ax=axes[0])
axes[0].set_title('Selected: out-of-fold confusion matrix')
for label, value, color in [(0, 'Not hired', COLORS[0]), (1, 'Hired', COLORS[2])]:
    axes[1].hist(pred[np.asarray(y) == label, 3], bins=20, alpha=.65, label=value, color=color)
axes[1].set(title='Predicted probabilities by recorded outcome',
            xlabel='Predicted probability of label 1', ylabel='Applicants')
axes[1].legend()
plt.tight_layout()
plt.show()
''')
md('''## 7. ตัวแปรใดสำคัญต่อโมเดลโดยรวม?
Permutation importance คือ AP ที่ลดลงเมื่อสุ่มสลับค่าตัวแปรใน outer test fold
แท่งยิ่งยาว โมเดลยิ่งพึ่งพาตัวแปรนั้น แถบแสดง ±1 SD จาก fold และการสุ่มซ้ำรวมกัน
แถบนี้ไม่ใช่ช่วงความเชื่อมั่น และความสำคัญไม่ใช่ผลเชิงเหตุและผล''')
code('''importance_samples = np.concatenate(pfi, axis=1)
order = np.argsort(importance_samples.mean(axis=1))
fig, ax = plt.subplots(figsize=(9, 4))
ax.barh(np.array(features)[order], importance_samples.mean(axis=1)[order],
        xerr=importance_samples.std(axis=1, ddof=1)[order], color=COLORS[2], capsize=4)
ax.axvline(0, color='gray', linewidth=1)
ax.set(title='Permutation feature importance', xlabel='Decrease in average precision (±1 SD)')
plt.tight_layout()
plt.show()
''')
md('''## 8. ตรวจผลแยกกลุ่ม
เปรียบเทียบ TPR (recall) กับ FPR แยกตามรหัส Gender และช่วงอายุเดิมของสคริปต์
ไม่ตีความรหัส Gender 0/1 เป็นชื่อเพศ เพราะไม่มี data dictionary ยืนยัน
กราฟนี้เป็นการตรวจเบื้องต้น ไม่มีช่วงความเชื่อมั่น และยังสรุปความเป็นธรรมไม่ได้
แม้ไม่ใช้ Age/Gender ในการฝึก ตัวแปรอื่นก็อาจสัมพันธ์กับกลุ่มเหล่านี้''')
code('''groups = {}
for label, mask in [('Gender 0', data.Gender == 0), ('Gender 1', data.Gender == 1),
                    ('20–29', data.Age.between(20, 29)), ('30–39', data.Age.between(30, 39)),
                    ('40–50', data.Age.between(40, 50))]:
    if mask.any():
        groups[label] = summary(y[mask], pred[mask, 3], dec[mask, 3])
group_table = pd.DataFrame(groups).T
group_table['TPR'] = group_table.tp.div((group_table.tp + group_table.fn).replace(0, np.nan))
group_table['FPR'] = group_table.fp.div((group_table.fp + group_table.tn).replace(0, np.nan))
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for ax, subset, title in [(axes[0], ['Gender 0', 'Gender 1'], 'Recorded gender codes'),
                           (axes[1], ['20–29', '30–39', '40–50'], 'Age groups')]:
    subset = [s for s in subset if s in group_table.index]
    group_table.loc[subset, ['TPR', 'FPR']].plot.bar(ax=ax, color=[COLORS[2], COLORS[3]], rot=0)
    ax.set(title=title, ylabel='Rate', ylim=(0, 1))
    ax.set_xticklabels([f'{s}\\n(n={int(group_table.loc[s, "n"])})' for s in subset])
plt.tight_layout()
plt.show()
''')
md('''## 9. อธิบายผู้สมัครรายบุคคลด้วย Exact Shapley
เลือก FN และ FP ที่อยู่ใกล้ threshold ที่สุด อย่างละหนึ่งราย ตามวิธีเดิม
อ้างอิงผู้สมัครจากชุดฝึกของ fold นั้น สีเขียวเพิ่มและสีส้มลดความน่าจะเป็นของ label 1
ค่าฐานบวกผลรวมของทุกตัวแปรต้องเท่ากับค่าทำนาย

กราฟใช้หน่วยจุดเปอร์เซ็นต์ของความน่าจะเป็น และแถบแสดง SD จากการสุ่ม background 10 ครั้ง
ตัวอย่างเหล่านี้ไม่ใช่ตัวแทนของข้อผิดพลาดทั้งหมด และตัวแปรที่สัมพันธ์กันอาจทำให้การแทนค่าผสมไม่สมจริง''')
case_code = script[script.index('cases=[]'):script.index('groups={}')]
case_code = case_code.replace("for want in ('FN','FP'):", "for want in ('TP','FP','FN','Near threshold'):")
case_code = case_code.replace("if (want=='FN'", "if want == 'Near threshold' or (want == 'TP' and y.iloc[j] == 1 and dec[j,3]) or (want=='FN'")
case_code = case_code.replace("    if not hits:\n        raise RuntimeError('Expected at least one '+want)",
                              "    if not hits:\n        display(Markdown(f'ไม่มีตัวอย่าง {want} ในผลการประเมินนี้'))\n        continue")
code(case_code)
code('''for case in cases:
    phi = np.array(case['phi']) * 100
    error = np.array(case['replica_sd']) * 100
    order = np.argsort(abs(phi))
    labels = [f"{f} = {case['inputs'][f]}" for f in np.array(features)[order]]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.barh(labels, phi[order], xerr=error[order], capsize=4,
            color=[COLORS[2] if v >= 0 else COLORS[3] for v in phi[order]])
    ax.axvline(0, color='gray', linewidth=1)
    ax.set(title=f"{case['type']} · CSV row {case['row']} · fold {case['fold']}",
            xlabel='Contribution to predicted probability (percentage points; ±1 background SD)')
    plt.tight_layout()
    plt.show()
    display(Markdown(f"**ค่าฐาน {case['base']:.1%} → ค่าทำนาย {case['p']:.1%}** "
                     f"เทียบกับ threshold {case['cut']:.1%} ของ fold นี้"))
''')
advanced(md, code)
md('''## 10. สรุปผลและข้อจำกัด
เซลล์นี้สรุปจากผลที่รันจริง ไม่ใช้ข้อความสรุปที่กำหนดตัวเลขไว้ล่วงหน้า
AP และ Brier วัดคนละด้าน ส่วน threshold ที่มุ่ง recall สูงอาจเพิ่ม FP
ข้อมูลนี้ยังไม่มีหลักฐานสำหรับยืนยันความถูกต้องของ label ความเป็นตัวแทนของผู้สมัครจริง
หรือประสิทธิภาพในอนาคต ต้องตรวจข้อมูลและบริบทก่อนนำไปใช้งาน''')
code('''selected = metrics.loc['Selected']
top_feature = features[int(np.argmax(importance_samples.mean(axis=1)))]
recall = selected.tp / (selected.tp + selected.fn)
fpr = selected.fp / (selected.fp + selected.tn)
display(Markdown(
    f"- ผลประเมินนอกชุดฝึก: AP **{selected.ap:.3f}**, Brier **{selected.brier:.3f}**\\n"
    f"- Recall **{recall:.1%}**, FPR **{fpr:.1%}** ณ threshold ที่เลือกภายในแต่ละ fold\\n"
    f"- โมเดลพึ่งพา **{top_feature}** มากที่สุดตาม permutation importance\\n"
    "- ใช้กราฟรายบุคคลเพื่ออธิบายคำทำนาย และตรวจความผิดพลาดร่วมกับผู้เชี่ยวชาญ"
))
''')
md('''## 11. บันทึกผลสำหรับใช้งานต่อ
บันทึก JSON และ CSV เหมือนสคริปต์เดิม โดยไม่พิมพ์เนื้อหา JSON ทั้งหมดออกหน้าจอ
กราฟและคำอธิบายจะอยู่ใน Notebook เมื่อกด Save หลัง Run All''')
export = script[script.index('pfi=np.concatenate'):script.index('print(json.dumps')]
export = export.replace('pfi=np.concatenate(pfi,axis=1)', 'pfi_export=importance_samples').replace('pfi.mean(axis=1)', 'pfi_export.mean(axis=1)').replace('pfi.std(axis=1,ddof=1)', 'pfi_export.std(axis=1,ddof=1)')
code(export + "\ndisplay(Markdown('บันทึก **model_card_results.json** และ **model_card_predictions.csv** แล้ว'))")
code('''audit_metrics.to_csv(root / 'model_card_metrics_full.csv', index=False)
fairness.to_csv(root / 'model_card_fairness.csv', index=False)
fairness_gaps.to_csv(root / 'model_card_fairness_gaps.csv', index=False)
grouped_pfi.to_csv(root / 'model_card_grouped_pfi.csv', index=False)
lime_checks.to_csv(root / 'model_card_lime_checks.csv', index=False)
lime_stability.to_csv(root / 'model_card_lime_stability.csv', index=False)
(root / 'candidate_review_drafts.md').write_text('\\n\\n'.join(candidate_drafts), encoding='utf-8')
display(Markdown('บันทึกตารางตรวจสอบและข้อความร่างสำหรับ HR แล้ว'))
''')
# Replace the preliminary group chart with the full fairness audit below.
for cell in cells:
    if cell.cell_type == 'code':
        cell.source = cell.source.replace("data.Age.between(40, 50)", "data.Age.ge(40)").replace("40–50", "40+")
    else:
        cell.source = cell.source.replace('40–50', '40 ปีขึ้นไป')
nb.cells = cells
nb.metadata = {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
               'language_info': {'name': 'python'}}
nbf.write(nb, root / 'recruitment_model_card_visual.ipynb')
print('Created recruitment_model_card_visual.ipynb')
