$ErrorActionPreference = 'Stop'
$root = 'C:\Users\ggez4\Downloads\explanai'
$output = Join-Path $root 'output'
$qa = Join-Path $root 'tmp\model_card_qa'
New-Item -ItemType Directory -Path $output,$qa -Force | Out-Null
$results = Get-Content -LiteralPath (Join-Path $root 'model_card_results.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$metrics = Import-Csv -LiteralPath (Join-Path $root 'model_card_metrics_full.csv')
$fairness = Import-Csv -LiteralPath (Join-Path $root 'model_card_fairness.csv')
$lime = Import-Csv -LiteralPath (Join-Path $root 'model_card_lime_stability.csv')
Write-Output 'Opening Word'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Add()
$selection = $word.Selection
$doc.PageSetup.PaperSize = 2 # US Letter
$doc.PageSetup.TopMargin = 40
$doc.PageSetup.BottomMargin = 40
$doc.PageSetup.LeftMargin = 43
$doc.PageSetup.RightMargin = 43
$doc.PageSetup.HeaderDistance = 18
$doc.PageSetup.FooterDistance = 18
$normal = $doc.Styles.Item(-1)
$normal.Font.Name = 'TH Sarabun New'
$normal.Font.Size = 16
$normal.Font.SizeBi = 16
$normal.Font.NameBi = 'TH Sarabun New'
$normal.ParagraphFormat.SpaceAfter = 3
$normal.ParagraphFormat.LineSpacingRule = 4
$normal.ParagraphFormat.LineSpacing = 18
$normal.ParagraphFormat.WidowControl = -1
Write-Output 'Setting styles'
$doc.Styles.Item(-2).Font.Name = 'TH Sarabun New'
$doc.Styles.Item(-2).Font.Size = 18
$doc.Styles.Item(-2).Font.SizeBi = 18
$doc.Styles.Item(-2).Font.NameBi = 'TH Sarabun New'
$doc.Styles.Item(-2).Font.Bold = -1
$doc.Styles.Item(-2).Font.BoldBi = -1
$doc.Styles.Item(-2).Font.Color = 0
$doc.Styles.Item(-2).ParagraphFormat.SpaceBefore = 8
$doc.Styles.Item(-2).ParagraphFormat.SpaceAfter = 6
$doc.Styles.Item(-2).ParagraphFormat.KeepWithNext = -1
Write-Output 'Setting footer'
$footer = $doc.Sections.Item(1).Footers.Item(1).Range
$footer.Text = 'HCD302  |  Model Card  |  '
$footer.Font.Name = 'TH Sarabun New'
$footer.Font.Size = 9
$footer.ParagraphFormat.Alignment = 2
$footer.Collapse(0)
[void]$footer.Fields.Add($footer,33)

function Paragraph([string]$text) {
    $selection.Style = $doc.Styles.Item(-1)
    $selection.Font.Size = 16
    $selection.Font.SizeBi = 16
    $selection.Font.NameBi = 'TH Sarabun New'
    $selection.Font.Bold = 0
    $selection.Font.BoldBi = 0
    $selection.ParagraphFormat.LineSpacingRule = 4
    $selection.ParagraphFormat.LineSpacing = 18
    $selection.ParagraphFormat.Alignment = 0
    $selection.TypeText($text)
    $selection.TypeParagraph()
}
function Heading([string]$text) {
    $selection.Style = $doc.Styles.Item(-2)
    $selection.Font.Name = 'TH Sarabun New'
    $selection.Font.NameBi = 'TH Sarabun New'
    $selection.Font.Size = 18
    $selection.Font.SizeBi = 18
    $selection.Font.Bold = -1
    $selection.Font.BoldBi = -1
    $selection.ParagraphFormat.LineSpacingRule = 4
    $selection.ParagraphFormat.LineSpacing = 21
    $selection.TypeText($text)
    $selection.TypeParagraph()
    $selection.Style = $doc.Styles.Item(-1)
}
function Table($headers,$rows,$widths) {
    $table = $doc.Tables.Add($selection.Range,$rows.Count+1,$headers.Count)
    $table.AllowAutoFit = $false
    $table.Range.Font.Name = 'TH Sarabun New'
    $table.Range.Font.Size = 16
    $table.Range.Font.SizeBi = 16
    $table.Range.Font.NameBi = 'TH Sarabun New'
    $table.Range.ParagraphFormat.SpaceAfter = 0
    $table.Range.ParagraphFormat.SpaceBefore = 0
    $table.Range.ParagraphFormat.LineSpacingRule = 4
    $table.Range.ParagraphFormat.LineSpacing = 18
    $table.TopPadding = 2
    $table.BottomPadding = 2
    $table.LeftPadding = 5
    $table.RightPadding = 5
    $table.Borders.Enable = 1
    $table.Borders.OutsideColor = 14277081
    $table.Borders.InsideColor = 14277081
    $table.Rows.AllowBreakAcrossPages = 0
    $table.Rows.Item(1).HeadingFormat = -1
    for ($j=0;$j -lt $headers.Count;$j++) {
        $table.Cell(1,$j+1).Range.Text = [string]$headers[$j]
        $table.Columns.Item($j+1).Width = $widths[$j]
    }
    $table.Rows.Item(1).Range.Bold = -1
    $table.Rows.Item(1).Range.Font.BoldBi = -1
    $table.Rows.Item(1).Shading.BackgroundPatternColor = 15921906
    for($i=0;$i -lt $rows.Count;$i++) {
        for($j=0;$j -lt $headers.Count;$j++) {
            $table.Cell($i+2,$j+1).Range.Text = [string]$rows[$i][$j]
        }
    }
    $selection.SetRange($table.Range.End,$table.Range.End)
    $selection.TypeParagraph()
}
function PageBreak { $selection.InsertBreak(7) }
function Percent([double]$value) { return ('{0:N1}%' -f ($value*100)) }

try {
    Write-Output 'Writing page 1'
    $selection.Style = $doc.Styles.Item(-63) # Title
    $selection.Font.Name = 'TH Sarabun New'
    $selection.Font.Size = 18
    $selection.Font.SizeBi = 18
    $selection.Font.Color = 0
    $selection.Font.Bold = -1
    $selection.TypeText('Model Card การจัดลำดับแฟ้มผู้สมัครงาน')
    $selection.TypeParagraph()
    Paragraph 'HCD302 Creating Explainable AI | รุ่นเอกสาร 1.0 | 13 พฤศจิกายน 2569'
    Paragraph 'ต้นแบบนี้ช่วยฝ่ายทรัพยากรบุคคล (HR) จัดลำดับแฟ้มหลังสัมภาษณ์และทดสอบทักษะ เมื่อตรวจเทียบกับข้อมูลจำลอง ระบบค้นพบผู้ที่ข้อมูลระบุว่ารับเข้าทำงานได้ 90.1% และเสนอทบทวนแฟ้ม 73.5% ของทั้งหมด HR จึงต้องประเมินกำลังคนในการทบทวน เอกสารประยุกต์จาก Mitchell et al. (2019) [1]'
    Heading '1 รายละเอียดโมเดล Model details'
    Paragraph 'ใช้ Gradient Boosting ซึ่งรวมต้นไม้ตัดสินใจหลายต้นเพื่อให้คะแนนแฟ้มจากรูปแบบผลรับหรือไม่รับที่บันทึกไว้ โมเดลนี้ถูกเลือกในการทดสอบทั้ง 5 รอบ ใช้โปรแกรม scikit-learn 1.8.0 และกำหนดจุดเริ่มสุ่ม random_state 42 เพื่อให้รันซ้ำได้ ขณะนี้อยู่ในขั้นต้นแบบ'
    Paragraph 'ผู้พัฒนา กลุ่มการคัดเลือกผู้สมัครงาน ได้แก่ นายภูจิตร จิรวิริยาภรณ์ 6730614005 นายปัญญพัฒน์ เปรียบปาน 6730614014 นายอภิวิชญ์ เลิศกมลรักษ์ 6730614015 นายษุภากรณ์ จิราจินดากุล 6730614020 และนายนพัทธ์ ฝอยทอง 6730614021'
    Paragraph 'ค่าตั้งที่ทดลอง ได้แก่ จำนวนต้นไม้ n_estimators 50/100 ระดับการตัดสินใจ max_depth 1/2/3 และอัตราการเพิ่มผลแต่ละต้น learning_rate 0.1 ส่วน Logistic Regression ใช้ L2 เพื่อลดความซับซ้อน ทดลองค่าควบคุม C 0.1/1/10 และจำกัดรอบคำนวณ max_iter 1000 เลือกวิธีหลังเมื่อคะแนนการจัดอันดับ AP ต่างกันไม่เกิน 0.01 ตามเกณฑ์ที่ตั้งก่อนทดสอบ'
    Heading '2 ผู้ใช้และวิธีใช้ Intended use'
    Paragraph 'ผู้ใช้คือ HR และผู้จัดการตำแหน่งงาน ใช้เมื่อบันทึกผลสัมภาษณ์และทักษะแล้ว เรียงแฟ้มตามคะแนนเพื่อให้เจ้าหน้าที่ตรวจข้อมูลก่อนตัดสินใจ พร้อมเปิดให้ผู้สมัครขอแก้ข้อมูลและขอทบทวนตามช่องทางของหน่วยงาน'
    Paragraph 'กรณีที่ไม่ควรใช้ ได้แก่ การรับหรือปฏิเสธงานอัตโนมัติ การคัดกรองก่อนมีคะแนนครบ การตัดสินความสามารถหรือผลงานจริง และการใช้กับผู้สมัครจริงหรือตำแหน่งงานอื่นที่ยังไม่ได้ทดสอบความเหมาะสม'
    Heading '3 กลุ่มที่ควรตรวจผล Factors'
    Paragraph 'ตรวจแยกตามรหัสเพศ Gender 0/1 และอายุ 20–29, 30–39 และ 40 ปีขึ้นไป เพศและอายุใช้ตรวจความแตกต่างระหว่างกลุ่ม ส่วนข้อมูลที่ใช้ให้คะแนนมีระดับการศึกษา ประสบการณ์ คะแนนสัมภาษณ์ และคะแนนทักษะ ผลอาจต่างกันตามสัดส่วนผลรับเดิม ข้อมูลที่ขาดหาย และรูปแบบคะแนนของแต่ละกลุ่ม'

    Paragraph 'ข้อเสนอโครงการระบุรหัสเพศ 0 ชาย และ 1 หญิง ต้องยืนยันความหมายกับต้นทางก่อนใช้จริง ข้อมูลมีเพียงสองรหัสและช่วงอายุจำกัด ผลจึงยังครอบคลุมผู้สมัครจริงไม่ครบ ช่วงความเชื่อมั่นนี้ยังไม่รวมความเปลี่ยนแปลงจากการสร้างโมเดลใหม่'
    PageBreak
    Write-Output 'Writing page 2'
    Heading '4 เกณฑ์วัดผล Metrics'
    Paragraph 'Recall หรือ sensitivity วัดว่าค้นพบผู้ที่ข้อมูลระบุว่ารับเข้าทำงานได้กี่เปอร์เซ็นต์ ตั้งเป้าอย่างน้อย 90% ในช่วงเลือกโมเดล แล้วเลือกคะแนนเกณฑ์ (threshold) ที่คัดแฟ้มซึ่งข้อมูลระบุว่าไม่รับออกได้มากที่สุด ใช้เกณฑ์เดียวกันกับทุกกลุ่มในรอบทดสอบนั้น'
    Paragraph 'PPV วัดว่าในแฟ้มที่เสนอทบทวน มีผลรับเดิมตรงกันกี่เปอร์เซ็นต์ AP วัดคุณภาพการจัดอันดับ ค่ายิ่งสูงยิ่งดี โดยเทียบกับสัดส่วนรับเดิม 31.0% ของข้อมูล ส่วน Brier score วัดความคลาดเคลื่อนของคะแนนความน่าจะเป็น ค่ายิ่งต่ำยิ่งดี สัดส่วนเสนอทบทวนใช้ประเมินภาระงาน HR'
    Paragraph 'ความผิดพลาดมีสองแบบ FP คือเสนอแฟ้มที่ข้อมูลระบุว่าไม่รับ ทำให้ทบทวนเพิ่ม ส่วน FN คือพลาดแฟ้มที่ข้อมูลระบุว่ารับ ซึ่งอาจทำให้ผู้สมัครเสียโอกาสเมื่อคิวมีจำกัด'
    $foldRows = @()
    foreach($split in $results.splits) {
        $model = $split.models | Where-Object name -eq $split.chosen
        $foldRows += ,@([string]$split.fold,[string]$model.params.model__max_depth,[string]$model.params.model__n_estimators,('{0:N2}%' -f (100*[double]$model.cut)))
    }
    Table @('รอบทดสอบ','ระดับต้นไม้','จำนวนต้นไม้','คะแนนเกณฑ์') $foldRows @(90,100,130,206)
    Paragraph 'แฟ้มที่ได้คะแนนตั้งแต่เกณฑ์ขึ้นไปถูกเสนอทบทวนก่อน แต่ละรอบเลือกเกณฑ์จากข้อมูลที่ใช้สร้างโมเดล จึงต้องเลือกเกณฑ์สำหรับใช้งานจริงอีกครั้งตามกำลังคนของ HR'
    Heading '5 ข้อมูลที่ใช้สร้างและทดสอบโมเดล'
    Paragraph 'ใช้ recruitment_data_cleaned.csv ซึ่งเป็นข้อมูลผู้สมัครจำลอง 1,500 ราย เดิมมีข้อมูลประกอบ 10 ตัวและผลรับหรือไม่รับ HiringDecision แบ่งเป็นรับ 465 ราย (31.0%) และไม่รับ 1,035 ราย แหล่งข้อมูลตามข้อเสนอคือ Rabie El Kharoua บน Kaggle [2] ใบอนุญาต CC BY 4.0 อ้างตามข้อเสนอโครงการ'
    Paragraph 'ไม่พบแถวซ้ำ แต่ประสบการณ์หาย 183 ราย (12.2%) ใช้ค่าจาก CSV โดยตรง แล้วเติมค่าที่หายด้วยค่ากลางหรือมัธยฐานของชุดสร้างโมเดล ต้องยืนยันขั้นตอนทำความสะอาดไฟล์ก่อนหน้านี้และสิทธิใช้ข้อมูลกับต้นทางก่อนเผยแพร่ซ้ำ'
    Paragraph 'หมุนเวียนแบ่งข้อมูลทดสอบ 5 รอบ แต่ละรอบใช้สร้างโมเดล 1,200 รายและทดสอบอีก 300 ราย ภายในชุดสร้างโมเดลแบ่งย่อย 4 ส่วนเพื่อเลือกค่าตั้งและคะแนนเกณฑ์ วิธีนี้เรียก nested cross-validation รวมผลครบ 1,500 ราย โดยแต่ละรายถูกทดสอบด้วยโมเดลที่ไม่ได้เรียนจากรายนั้น ยังต้องทดสอบกับข้อมูลจากแหล่งอื่น'
    Paragraph 'ขั้นตอนเตรียมข้อมูลเรียนรู้จากชุดสร้างโมเดลของแต่ละรอบ แปลงระดับการศึกษาเป็นช่องแยกหมวด และปรับตัวเลขให้เทียบกันได้สำหรับ Logistic Regression ใช้เพียงระดับการศึกษา ประสบการณ์ คะแนนสัมภาษณ์ และคะแนนทักษะ ซึ่งต้องเก็บก่อนตัดสินใจรับงาน'

    PageBreak
    Write-Output 'Writing page 3'
    Heading '6 ผลการทดสอบ Quantitative analyses'
    Paragraph 'ผลทดสอบรวม 5 รอบ เปรียบเทียบกับ Dummy ที่ให้คะแนนทุกแฟ้มเท่ากับสัดส่วนผลรับเดิม และ Logistic Regression ซึ่งเป็นวิธีสถิติที่อ่านความสัมพันธ์ได้ง่ายกว่า'
    $metricRows = @()
    foreach($name in @('Dummy','Logistic Regression','Gradient Boosting')) {
        $m = $metrics | Where-Object model -eq $name
        $metricRows += ,@($name,('{0:N3}' -f [double]$m.AP),('{0:N3}' -f [double]$m.Brier),(Percent $m.sensitivity),(Percent $m.PPV),(Percent $m.review_rate))
    }
    Table @('โมเดล','AP','Brier','Recall','PPV','เสนอทบทวน') $metricRows @(145,55,60,80,75,111)
    $selection.ParagraphFormat.LineSpacingRule = 0
    $metricPicture = $selection.InlineShapes.AddPicture((Join-Path $root 'output\graphs\09_กราฟตัวชี้วัดสำหรับรายงาน.png'),$false,$true)
    $metricPicture.LockAspectRatio = -1
    $metricPicture.Width = 440
    $selection.SetRange($metricPicture.Range.End,$metricPicture.Range.End)
    $selection.TypeParagraph()
    Paragraph 'Gradient Boosting ได้ AP 0.614 สูงกว่า Dummy 0.310 และ Logistic Regression 0.571 เสนอทบทวน 1,102 จาก 1,500 แฟ้ม ในจำนวนนี้ตรงกับผลรับเดิม 419 ราย และผลไม่รับเดิม 683 ราย อีก 398 แฟ้มที่ไม่ถูกเสนอมีผู้รับเดิมตกหล่น 46 ราย และผลไม่รับเดิม 352 ราย'
    Paragraph 'กราฟซ้าย AP สูงดีกว่า กราฟขวา Brier ต่ำดีกว่า ตารางรายกลุ่มด้านล่างแสดง FNR หรืออัตราพลาดผลรับ และ FPR หรืออัตราเสนอเกิน โดยมีจำนวนจริง อัตรา และช่วงความเชื่อมั่น 95% แบบ Wilson ในบรรทัดถัดมา'
    $groupRows = @()
    foreach($group in @('Gender 0','Gender 1','20–29','30–39','40+')) {
        $fnr = $fairness | Where-Object { $_.group -eq $group -and $_.metric -eq 'FNR' }
        $fpr = $fairness | Where-Object { $_.group -eq $group -and $_.metric -eq 'FPR' }
        $review = $fairness | Where-Object { $_.group -eq $group -and $_.metric -eq 'Review rate' }
        $fnText = "$($fnr.numerator)/$($fnr.denominator) = $(Percent $fnr.rate)`n$('{0:N1}–{1:N1}%' -f (100*[double]$fnr.ci_low),(100*[double]$fnr.ci_high))"
        $fpText = "$($fpr.numerator)/$($fpr.denominator) = $(Percent $fpr.rate)`n$('{0:N1}–{1:N1}%' -f (100*[double]$fpr.ci_low),(100*[double]$fpr.ci_high))"
        $groupRows += ,@($group,[string]$fnr.n,$fnText,$fpText,(Percent $review.rate))
    }
    Table @('กลุ่ม','จำนวน','พลาดผลรับ FNR','เสนอเกิน FPR','เสนอทบทวน') $groupRows @(82,42,148,148,106)
    Paragraph 'กลุ่มเพศรหัส 0 พลาดผลรับเดิม 12.66% เทียบกับรหัส 1 ที่ 7.02% ต่างกัน 5.64 จุดเปอร์เซ็นต์ ส่วนอัตราเสนอทั้งที่ไม่รับต่างกัน 0.21 จุดเปอร์เซ็นต์ สำหรับอายุ ช่องว่างระหว่างกลุ่มสูงสุดและต่ำสุดเท่ากับ 5.80 และ 4.39 จุดเปอร์เซ็นต์ตามลำดับ'

    PageBreak
    Write-Output 'Writing page 4'
    Heading '7 คำอธิบายคะแนน Explainability'
    Paragraph 'PFI ใช้ดูว่าโมเดลพึ่งข้อมูลใด โดยสลับค่าข้อมูลแต่ละชนิด 25 ครั้งต่อรอบแล้ววัด AP ที่ลดลง ระดับการศึกษามีผลมากสุด 0.169 ± 0.034 ตามด้วยสัมภาษณ์ 0.099 ± 0.035 ทักษะ 0.096 ± 0.037 และประสบการณ์ 0.067 ± 0.023 ค่า ± บอกความแกว่งของผลจากการสุ่มและรอบทดสอบ'
    $selection.ParagraphFormat.LineSpacingRule = 0
    $picture = $selection.InlineShapes.AddPicture((Join-Path $root 'tmp\model_card_qa\pfi_thai.png'),$false,$true)
    $picture.LockAspectRatio = -1
    $picture.Width = 330
    $selection.SetRange($picture.Range.End,$picture.Range.End)
    $selection.TypeParagraph()
    Paragraph 'แท่งในกราฟยิ่งยาว แสดงว่าโมเดลพึ่งข้อมูลนั้นมาก ส่วน ALE ใช้ดูแนวโน้มคะแนน พบว่าคะแนนสูงขึ้นเมื่อประสบการณ์เข้าสู่ช่วงประมาณ 7 ปีขึ้นไป พร้อมตรวจจำนวนข้อมูลที่รองรับแต่ละช่วง และได้สลับคะแนนสัมภาษณ์กับทักษะพร้อมกันเพื่อตรวจผลเมื่อเปลี่ยนข้อมูลเป็นกลุ่ม'
    Paragraph 'SHAP ใช้อธิบายแฟ้มรายบุคคล เริ่มจากคะแนนเฉลี่ยที่โมเดลให้กลุ่มอ้างอิง แล้วแจกแจงว่าข้อมูลใดเพิ่มหรือลดคะแนน ตัวอย่างสองรายต่อไปนี้เลือกจากความผิดพลาดที่อยู่ใกล้คะแนนเกณฑ์ หน่วยผลของแต่ละปัจจัยเป็นจุดเปอร์เซ็นต์'
    Table @('กรณีและแถวข้อมูล','กลุ่มอ้างอิง → รายนี้','คะแนนเกณฑ์','ปัจจัยเพิ่มหรือลดคะแนน') @(
        @('พลาดผลรับ FN แถว 1400','31.00% → 16.68%','16.87%','สัมภาษณ์ +10.30 ทักษะ −10.16 ประสบการณ์ −8.53'),
        @('เสนอเกิน FP แถว 1011','31.01% → 16.05%','15.80%','สัมภาษณ์ −8.16 การศึกษา −6.78 ประสบการณ์ +3.08')
    ) @(110,122,78,216)
    Paragraph 'รายที่พลาดมีผลเพิ่มจากสัมภาษณ์ แต่ผลลดจากทักษะและประสบการณ์มากกว่า ส่วนรายที่เสนอเกินมีคะแนนสูงกว่าเกณฑ์เล็กน้อย ตรวจแล้วค่าฐานบวกผลทุกปัจจัยได้คะแนนทำนายตรงกัน เมื่อเปลี่ยนกลุ่มอ้างอิง 10 ครั้ง ปัจจัยอันดับแรกตรงกับเดิม 5/10 ครั้งในรายที่พลาด และ 7/10 ในรายที่เสนอเกิน'
    Paragraph 'LIME 0.2.0.1 อธิบายโมเดลโดยลองข้อมูลใกล้เคียง 5,000 ตัวอย่างและเปลี่ยนจุดเริ่มสุ่ม 10 แบบ คะแนนเลียนแบบพฤติกรรมโมเดล (weighted R²) ยิ่งใกล้ 1 ยิ่งดี ได้เฉลี่ย 0.483 ในรายที่พลาด และ 0.229 ในรายที่เสนอเกิน จึงยังอธิบายคะแนนได้เพียงบางส่วน'
    Paragraph 'LIME ให้ปัจจัยเด่นตรงกันทั้ง 10 ครั้งในสองราย แต่รายที่เสนอเกินให้การศึกษาเด่น ส่วน SHAP ให้สัมภาษณ์เด่น ทั้งสองวิธีใช้วิธีเปรียบเทียบต่างกัน และ R² นี้วัดกับข้อมูลที่ใช้สร้างคำอธิบาย จึงต้องให้ HR ตรวจคำอธิบายก่อนส่งให้ผู้สมัคร'

    PageBreak
    Write-Output 'Writing page 5'
    Heading '8 ผลกระทบต่อผู้สมัคร Ethical considerations'
    Paragraph 'ผู้สมัครอาจเสียโอกาสหากแฟ้มถูกจัดลำดับต่ำ โดยเฉพาะเมื่อคิวทบทวนจำกัด ส่วนแฟ้มที่เสนอเกินเพิ่มภาระ HR และทำให้รายอื่นรอนาน ผลการทดลองเปรียบเทียบกับการรับงานในข้อมูลจำลอง ผู้รับผิดชอบจึงต้องตรวจว่าเกณฑ์เดิมเหมาะสมก่อนใช้กับบุคคลจริง'
    Paragraph 'ผลที่พบคือกลุ่มเพศรหัส 0 พลาดผลรับเดิมมากกว่ารหัส 1 อยู่ 5.64 จุดเปอร์เซ็นต์ และกลุ่มอายุ 40 ปีขึ้นไปพลาดมากกว่ากลุ่ม 20–29 ปีอยู่ 5.80 จุดเปอร์เซ็นต์ ต้องตรวจว่าความต่างเกี่ยวข้องกับข้อมูลที่ใช้ ความครบถ้วนของข้อมูล หรือสัดส่วนรับเดิมของแต่ละกลุ่มอย่างไร'
    Paragraph 'สิ่งที่ทำแล้วคือใช้เพศและอายุตรวจผลแยกกลุ่ม ใช้ข้อมูลสร้างโมเดลเพียงสี่ชนิด เตรียมข้อมูลภายในชุดสร้างโมเดลแต่ละรอบ ตั้งเป้าลดการพลาดผลรับเดิม และแสดงจำนวนจริงพร้อมช่วงความเชื่อมั่น นอกจากนี้ยังตรวจว่าคำอธิบายเปลี่ยนมากเพียงใดเมื่อสุ่มใหม่'
    Paragraph 'ก่อนทดลองจริง HR ควรทบทวนแฟ้มคะแนนต่ำด้วย จัดช่องทางแก้ข้อมูลและขอทบทวน กำหนดผู้รับผิดชอบและเวลาตอบกลับ รวมทั้งจำกัดผู้เข้าถึงข้อมูลผู้สมัคร ข้อความสำหรับผู้สมัครที่เตรียมไว้ยังรอ HR ตรวจและกำหนดช่องทางติดต่อจริง'
    Heading '9 ข้อจำกัดและคำแนะนำก่อนใช้'
    Paragraph 'ข้อมูลเป็นผู้สมัครจำลอง 1,500 ราย และยังไม่มีผลทดสอบกับข้อมูลภายนอก จึงยังบอกความแม่นกับผู้สมัครจริงไม่ได้ รวมถึงยังไม่ได้ทดสอบผลต่างระหว่างตำแหน่งงาน ช่วงเวลา หรือองค์กรที่มีวิธีคัดเลือกต่างกัน'
    Paragraph 'แม้มี Brier score แล้ว ยังต้องตรวจว่าคะแนนความน่าจะเป็นสอดคล้องกับอัตรารับที่พบจริงเพียงใด คำอธิบายยังขึ้นกับกลุ่มที่นำมาเทียบ ความสัมพันธ์ของข้อมูล และจำนวนตัวอย่างในแต่ละช่วง การสุ่มข้อมูลอาจสร้างชุดคุณสมบัติที่ไม่พบในผู้สมัครจริง'
    Paragraph 'ก่อนใช้จริงต้องยืนยันแหล่งข้อมูล สิทธิใช้งาน ขั้นตอนทำความสะอาด และความหมายรหัสเพศ ตรวจว่าข้อมูลให้คะแนนถูกเก็บก่อนตัดสินใจ แล้วทดสอบกับข้อมูลจริงที่ได้รับอนุญาต เลือกคะแนนเกณฑ์ตามกำลัง HR ต้นทุนความผิดพลาด และผลรายกลุ่ม พร้อมติดตามเมื่อข้อมูลใหม่เปลี่ยนไป'
    Paragraph 'หากพัฒนาเป็นระบบให้บริการ ต้องบันทึกโมเดลและคะแนนเกณฑ์รุ่นที่จะใช้จริง กำหนดผู้รับผิดชอบ ประวัติการทบทวน และช่องทางขอแก้ไข ผู้ใช้ควรอ่านผลการทดลองนี้ร่วมกับข้อจำกัดของข้อมูลและคำอธิบาย'
    Heading 'เอกสารอ้างอิงและหลักฐานผลรัน'
    $selection.Font.Size = 9
    Paragraph '[1] Mitchell, M. et al. (2019). Model Cards for Model Reporting. FAT* 2019. DOI 10.1145/3287560.3287596. https://arxiv.org/abs/1810.03993'
    Paragraph '[2] Rabie El Kharoua. Predicting Hiring Decisions in Recruitment Data. Kaggle. https://www.kaggle.com/datasets/rabieelkharoua/predicting-hiring-decisions-in-recruitment-data แหล่งข้อมูลและ CC BY 4.0 อ้างตามข้อเสนอโครงการที่ได้รับ'
    Paragraph 'ตรวจที่มาของตัวเลขได้จาก model_card_results.json และตารางผลประเมินรายกลุ่มกับ LIME วิธีคำนวณและผลแต่ละขั้นอยู่ใน recruitment_model_card_visual.ipynb รันซ้ำผ่าน run_model_card.py'
    $docPath = Join-Path $output 'Model_Card_With_Metrics.docx'
    $pdfPath = Join-Path $qa 'model_card_with_metrics.pdf'
    Write-Output 'Saving DOCX'
    [object]$savePath = [string]$docPath
    [object]$saveFormat = 16
    $doc.SaveAs([ref]$savePath,[ref]$saveFormat)
    Write-Output 'Rendering PDF'
    [object]$pdfSavePath = [string]$pdfPath
    [object]$pdfSaveFormat = 17
    $doc.SaveAs([ref]$pdfSavePath,[ref]$pdfSaveFormat)
    $pages = $doc.ComputeStatistics(2)
    Write-Output "DOCX $docPath"
    Write-Output "PAGES $pages"
    Write-Output "QA PDF $pdfPath"
} finally {
    $doc.Close(0)
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc)
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
