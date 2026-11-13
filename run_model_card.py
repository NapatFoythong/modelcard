"""Execute the notebook and save named PNG charts and a ZIP locally."""
from pathlib import Path
import argparse
import asyncio
import base64
import csv
import html
import re
import json
import sys
import zipfile

IMPORTANT_CHARTS = {
    'model_comparison', 'confusion_matrix', 'pfi', 'fairness_wilson',
    'ale_skill', 'shap_waterfall_fn', 'lime_fidelity_stability',
    'lime_vs_shap_near_threshold',
}
CHART_DIRECTORY = Path('output') / 'graphs'

def chart_labels(source, cases):
    """Name charts by their generating section, rather than global image order."""
    if source.startswith('root = Path.cwd()'):
        return [('hiring_decisions', 'สัดส่วนผลการรับเข้าทำงาน', 'จำนวนฉลากรับและไม่รับในข้อมูลสังเคราะห์')]
    if source.startswith('fig, axes = plt.subplots(1, 2, figsize=(12, 4))'):
        return [('missingness_skill_distribution', 'ข้อมูลหายและการกระจายคะแนนทักษะ', 'ค่าประสบการณ์ที่หายใน CSV และข้อมูลเข้าโมเดล โดยไม่ใช้ Age แก้ไขค่า พร้อมคะแนนทักษะตามฉลาก')]
    if source.startswith('display(Markdown(f'):
        return [('data_bias_audit', 'ตรวจข้อมูลและอคติก่อนฝึก', 'ความชุกฉลากและข้อมูลหายรายกลุ่ม พร้อมความชุกแยกกลยุทธ์รับสมัคร'),
                ('scores_by_gender', 'การกระจายคะแนนตามรหัสเพศ', 'Boxplot คะแนนสัมภาษณ์และทักษะ แยก Gender 0/1')]
    if source.startswith('model_names ='):
        return [('model_comparison', 'เปรียบเทียบคุณภาพโมเดล', 'Average Precision สูงดี ส่วน Brier score ต่ำดี'),
                ('precision_recall', 'Precision–Recall curves', 'ดูการแลกระหว่างความแม่นของฉลากบวกและ recall จากผลนอกชุดฝึก')]
    if source.startswith('fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))'):
        return [('confusion_matrix', 'ความผิดพลาดและการกระจายค่าทำนาย', 'Confusion matrix และค่าความน่าจะเป็นแยกตามฉลากจริง')]
    if source.startswith('importance_samples ='):
        return [('pfi', 'PFI — ความสำคัญของตัวแปร', 'AP ลดลงเท่าไรเมื่อสุ่มสลับตัวแปร แถบแสดง ±1 SD ไม่ใช่ confidence interval')]
    if source.startswith('groups ='):
        return [('group_rates', 'TPR และ FPR รายกลุ่ม', 'เปรียบเทียบ recall และอัตราผลบวกลวงตามเพศและอายุ')]
    if source.startswith('for case in cases:'):
        return [(f'shap_contributions_{c["type"]}', f'SHAP — ปัจจัยรายบุคคล: {c["type"]}',
                 f'แถว CSV {c["row"]}: ปัจจัยเพิ่ม/ลดค่าทำนาย และ SD จากการเปลี่ยน background') for c in cases]
    if source.startswith('def safe_rate'):
        return [('operational_metrics', 'ตัวชี้วัดสำหรับการทบทวนแฟ้ม', 'Sensitivity, specificity, PPV และสัดส่วนแฟ้มที่เสนอให้ HR ทบทวน'),
                ('fairness_wilson', 'Fairness พร้อม Wilson 95% CI', 'FNR, FPR และสัดส่วนเสนอทบทวนรายกลุ่ม ช่วงนี้ไม่รวมความไม่แน่นอนจากการฝึกใหม่')]
    if source.startswith('corr=X.corr'):
        return [('feature_correlations', 'ความสัมพันธ์ระหว่างตัวแปร', 'Spearman correlation ใช้สำรวจความสัมพันธ์ ไม่ใช่เหตุและผล'),
                ('grouped_pfi', 'PFI แบบกลุ่ม', 'ผลของการสลับตัวแปรพร้อมกัน แถบแสดง ±1 SD')]
    if source.startswith('ale_records='):
        return [('ale_experience', 'ALE — ประสบการณ์ทำงาน', 'รูปแบบคะแนนตามประสบการณ์ แยก fold พร้อมจำนวนข้อมูลในช่วง'),
                ('ale_skill', 'ALE — คะแนนทักษะ', 'รูปแบบคะแนนตามทักษะ แยก fold พร้อมจำนวนข้อมูลในช่วง; ไม่ใช่ผลเชิงเหตุและผล')]
    if source.startswith('shap_checks='):
        return [(f'shap_waterfall_{c["type"]}', f'SHAP waterfall — {c["type"]}',
                 f'แถว CSV {c["row"]}: จากค่าฐานชุดฝึก บวกผลตัวแปรจนถึงค่าทำนาย พร้อมเส้น threshold') for c in cases]
    if source.startswith('from lime.lime_tabular import LimeTabularExplainer'):
        return [('lime_fidelity_stability', 'LIME — Fidelity และความเสถียร', 'Weighted R² จากแพ็กเกจ lime บน neighborhood ที่ใช้ fit และ SD ของน้ำหนักข้าม 10 seeds')] + [
            (f'lime_vs_shap_{c["type"]}', f'LIME เทียบ SHAP — {c["type"]}',
             'ซ้ายคือน้ำหนักการอยู่ในช่วงค่าจากแพ็กเกจ lime จริง; ขวาคือ SHAP attribution ทั้งสองใช้คำถามอ้างอิงต่างกัน') for c in cases]
    return []


def export_charts(nb, root, include_all=False, include_html=False):
    directory = root / CHART_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    results = json.loads((root / 'model_card_results.json').read_text(encoding='utf-8'))
    charts = []
    for cell in nb.cells:
        images = [o['data']['image/png'] for o in cell.get('outputs', []) if 'image/png' in o.get('data', {})]
        if not images:
            continue
        labels = chart_labels(cell.source, results['cases'])
        if len(labels) != len(images):
            raise ValueError('Chart labels do not match outputs; update chart_labels for this notebook section.')
        for encoded, (slug, title, description) in zip(images, labels):
            number = len(charts) + 1
            slug = re.sub(r'[^a-z0-9]+', '_', slug.lower()).strip('_')
            if not include_all and slug not in IMPORTANT_CHARTS:
                continue
            readable_title = re.sub(r'[<>:"/\\|?*]', '', title).strip()
            filename = f'{number:02d}_{readable_title}.png'
            (directory / filename).write_bytes(base64.b64decode(encoded))
            charts.append(dict(number=number, filename=filename, title=title, description=description))
    with (directory / 'chart_index.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['number', 'filename', 'title', 'description'])
        writer.writeheader(); writer.writerows(charts)
    (directory / 'README.md').write_text('# รายชื่อกราฟ\n\n' + '\n\n'.join(
        f"## {c['number']}. {c['title']}\nไฟล์: {c['filename']}\n\n{c['description']}" for c in charts), encoding='utf-8')
    gallery = '<!doctype html><meta charset="utf-8"><title>รายชื่อกราฟ</title><style>body{font:18px/1.7 Tahoma,sans-serif;max-width:1100px;margin:35px auto;padding:20px}img{max-width:100%}section{margin-bottom:50px}</style><h1>กราฟพร้อมชื่อและคำอธิบาย</h1>'
    for c in charts:
        gallery += f'<section><h2>{c["number"]}. {html.escape(c["title"])}</h2><p>{html.escape(c["description"])}</p><a download href="{c["filename"]}">ดาวน์โหลด PNG</a><img alt="{html.escape(c["title"])}" src="{c["filename"]}"></section>'
    if include_html:
        (directory / 'index.html').write_text(gallery, encoding='utf-8')
    names = [c['filename'] for c in charts] + ['README.md', 'chart_index.csv']
    if include_html:
        names.append('index.html')
    with zipfile.ZipFile(root / 'output' / 'graphs.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(directory / name, arcname=f'graphs/{name}')
    return charts


def render_markdown(source):
    lines = []
    for line in source.splitlines():
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match[1])
            lines.append(f'<h{level}>{html.escape(match[2])}</h{level}>')
        elif line.strip():
            text = html.escape(line)
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
            lines.append(f'<p>{text}</p>')
    return '\n'.join(lines)


def export_html(nb, target, charts=None, include_all=False):
    body = []
    captions = iter(charts or [])
    if charts:
        body.append('<p><a download href="output/graphs.zip">ดาวน์โหลดกราฟทั้งหมด (ZIP)</a> · <a href="output/graphs/index.html">ดูรายการรูปพร้อมชื่อ</a></p>')
    metrics_path = target.parent / 'model_card_metrics_full.csv'
    if metrics_path.is_file():
        with metrics_path.open(encoding='utf-8', newline='') as stream:
            selected = next((row for row in csv.DictReader(stream) if row['model'] == 'Selected'), None)
        if selected:
            body.append('<h1>สรุปผลการจัดลำดับแฟ้มผู้สมัคร</h1><p>ผลประเมินจากผู้สมัครสังเคราะห์ 1,500 ราย ใช้ช่วย HR ทบทวนแฟ้ม</p>')
            body.append('<table><tr><th>ตัวชี้วัด</th><th>ผล</th></tr>')
            for label, key in [('ค้นพบผู้ที่มีฉลากรับเข้าทำงาน (Recall)', 'sensitivity'),
                               ('ความแม่นของแฟ้มที่เสนอทบทวน (PPV)', 'PPV'),
                               ('สัดส่วนแฟ้มที่เสนอให้ทบทวน', 'review_rate')]:
                body.append(f'<tr><td>{label}</td><td>{float(selected[key]):.1%}</td></tr>')
            body.append(f'<tr><td>Average Precision (สูงดี)</td><td>{float(selected["AP"]):.3f}</td></tr>')
            body.append(f'<tr><td>Brier score (ต่ำดี)</td><td>{float(selected["Brier"]):.3f}</td></tr></table>')
            body.append('<p>โมเดลค้นพบฉลากบวกได้มาก แต่เสนอแฟ้มให้ทบทวนจำนวนมากด้วย จึงต้องพิจารณากำลังคนของ HR; คะแนนไม่ใช่คำตัดสินรับหรือปฏิเสธงาน</p>')
    if not include_all:
        body.append('<h2>กราฟสำคัญ 8 หัวข้อ</h2><p>คัดเฉพาะผลโมเดล ความผิดพลาด ความเป็นธรรม และคำอธิบาย PFI / ALE / SHAP / LIME รายละเอียดเพิ่มเติมอยู่ใน Notebook</p>')
        for chart in charts or []:
            encoded = base64.b64encode((target.parent / CHART_DIRECTORY / chart['filename']).read_bytes()).decode('ascii')
            title = html.escape(chart['title'])
            description = html.escape(chart['description'])
            body.append(f'<figure><h3>{chart["number"]}. {title}</h3><p>{description}</p><img alt="{title}" src="data:image/png;base64,{encoded}"><figcaption><a download="{chart["filename"]}" href="data:image/png;base64,{encoded}">ดาวน์โหลดรูป PNG</a></figcaption></figure>')
        body.append('<p><strong>ข้อจำกัด:</strong> ข้อมูลเป็นข้อมูลสังเคราะห์ ผลไม่ใช่คำตัดสินรับงาน; ช่วงความเชื่อมั่นรายกลุ่มไม่รวมความไม่แน่นอนจากการฝึกใหม่ และ LIME มี fidelity จำกัด จึงต้องให้ HR ตรวจคำอธิบายก่อนใช้</p>')
    for cell in nb.cells if include_all else []:
        if cell.cell_type == 'markdown':
            body.append(render_markdown(cell.source))
        elif cell.cell_type == 'code':
            body.append('<details><summary>ดูโค้ดส่วนนี้</summary><pre>' + html.escape(cell.source) + '</pre></details>')
            for output in cell.get('outputs', []):
                data = output.get('data', {})
                if 'image/png' in data:
                    caption = next(captions, None)
                    title = html.escape(caption['title']) if caption else 'Analysis chart'
                    description = html.escape(caption['description']) if caption else ''
                    download = f'<a download="{caption["filename"]}" href="data:image/png;base64,{data["image/png"]}">ดาวน์โหลดรูป PNG</a>' if caption else ''
                    body.append(f'<figure><h3>{title}</h3><p>{description}</p><img alt="{title}" src="data:image/png;base64,{data["image/png"]}"><figcaption>{download}</figcaption></figure>')
                elif 'text/html' in data:
                    body.append('<div class="table-wrap">' + data['text/html'] + '</div>')
                elif 'text/markdown' in data:
                    body.append(render_markdown(data['text/markdown']))
                elif output.output_type == 'stream' and output.get('text', '').strip():
                    body.append('<pre>' + html.escape(output.text) + '</pre>')
    template = '''<!doctype html><html lang="th"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recruitment — Visual Model Card</title><style>
body{font:17px/1.7 "Segoe UI",Tahoma,sans-serif;color:#213547;background:#edf2f5;margin:0}
main{max-width:1120px;margin:35px auto;background:white;padding:45px;border-radius:14px}
h1,h2,h3{color:#146c63;line-height:1.35}h2{margin-top:42px;border-top:1px solid #dde5e8;padding-top:25px}
p{margin:10px 0}figure{margin:22px 0}img{max-width:100%;height:auto;display:block;margin:auto}
details{background:#f5f7f9;padding:12px 18px;margin:14px 0;border-radius:8px}summary{cursor:pointer;color:#366480}
pre{overflow:auto;font-size:13px;line-height:1.5}code{background:#edf2f5;padding:2px 5px}
.table-wrap{overflow:auto;margin:20px 0}table{border-collapse:collapse;font-size:14px;width:100%}
th,td{padding:9px 12px;border-bottom:1px solid #dce5e7;text-align:right}th{background:#f2f6f7}
.banner{padding:20px;background:#e8f5f0;border-left:5px solid #16877b;margin-bottom:30px}
@media(max-width:700px){main{margin:0;padding:18px}body{font-size:15px}}
</style><main><div class="banner"><strong>รายงานพร้อมกราฟ</strong><br>
อ่านสรุปและกราฟสำคัญด้านล่าง ไฟล์นี้เปิดดูได้โดยไม่ต้องรัน Python ใหม่</div>BODY</main></html>'''
    target.write_text(template.replace('BODY', '\n'.join(body)), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', nargs='?')
    parser.add_argument('--no-open', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--html', action='store_true', help='Also save an optional HTML report')
    parser.add_argument('--saved', action='store_true', help='View saved outputs without retraining')
    parser.add_argument('--all-charts', action='store_true', help='Export the full report instead of the 8 key charts')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    import nbformat
    from nbclient import NotebookClient
    notebook = root / 'recruitment_model_card_visual.ipynb'
    nb = nbformat.read(notebook, as_version=4)
    if args.saved and args.dataset:
        parser.error('--saved cannot be combined with a dataset')
    if not args.saved:
        source = Path(args.dataset).resolve() if args.dataset else root / 'recruitment_data_cleaned.csv'
        if not source.is_file():
            parser.error(f'Dataset not found: {source}')
        for cell in nb.cells:
            if cell.cell_type == 'code' and cell.source.startswith('root = Path.cwd()'):
                cell.source = re.sub(r'^source = .*$', lambda _: f'source = Path({str(source)!r})', cell.source, flags=re.M)
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print('Running analysis and building charts. Please wait...', flush=True)
        NotebookClient(nb, timeout=600, kernel_name='python3',
                       resources={'metadata': {'path': str(root)}}).execute()
        nbformat.write(nb, notebook)
    if any(o.output_type == 'error' for c in nb.cells for o in c.get('outputs', [])):
        raise RuntimeError('Notebook contains errors. Run again without --saved.')
    charts = sum('image/png' in o.get('data', {}) for c in nb.cells for o in c.get('outputs', []))
    if not charts:
        raise RuntimeError('No saved charts found. Run again without --saved.')
    report = root / 'recruitment_model_card_report.html'
    chart_files = export_charts(nb, root, include_all=args.all_charts, include_html=args.html)
    if args.html:
        export_html(nb, report, chart_files, include_all=args.all_charts)
    print(f'Complete: {len(chart_files)} charts saved.\nNotebook: {notebook}', flush=True)
    print(f'PNG files: {root / CHART_DIRECTORY}\nZIP: {root / "output" / "graphs.zip"}', flush=True)


if __name__ == '__main__':
    main()
