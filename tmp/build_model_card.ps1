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
$normal.Font.Name = 'Tahoma'
$normal.Font.Size = 11
$normal.Font.SizeBi = 11
$normal.Font.NameBi = 'Tahoma'
$normal.ParagraphFormat.SpaceAfter = 5
$normal.ParagraphFormat.LineSpacingRule = 0
$normal.ParagraphFormat.WidowControl = -1
Write-Output 'Setting styles'
$doc.Styles.Item(-2).Font.Name = 'Tahoma'
$doc.Styles.Item(-2).Font.Size = 14
$doc.Styles.Item(-2).Font.Color = 0
$doc.Styles.Item(-2).ParagraphFormat.SpaceBefore = 8
$doc.Styles.Item(-2).ParagraphFormat.SpaceAfter = 6
$doc.Styles.Item(-2).ParagraphFormat.KeepWithNext = -1
Write-Output 'Setting footer'
$footer = $doc.Sections.Item(1).Footers.Item(1).Range
$footer.Text = 'HCD302  |  Model Card  |  '
$footer.Font.Name = 'Tahoma'
$footer.Font.Size = 9
$footer.ParagraphFormat.Alignment = 2
$footer.Collapse(0)
[void]$footer.Fields.Add($footer,33)

function Paragraph([string]$text) {
    $selection.Style = $doc.Styles.Item(-1)
    $selection.Font.Size = 11
    $selection.Font.SizeBi = 11
    $selection.Font.NameBi = 'Tahoma'
    $selection.Font.Bold = 0
    $selection.ParagraphFormat.Alignment = 0
    $selection.TypeText($text)
    $selection.TypeParagraph()
}
function Heading([string]$text) {
    $selection.Style = $doc.Styles.Item(-2)
    $selection.TypeText($text)
    $selection.TypeParagraph()
    $selection.Style = $doc.Styles.Item(-1)
}
function Table($headers,$rows,$widths) {
    $table = $doc.Tables.Add($selection.Range,$rows.Count+1,$headers.Count)
    $table.AllowAutoFit = $false
    $table.Range.Font.Name = 'Tahoma'
    $table.Range.Font.Size = 9.5
    $table.Range.Font.SizeBi = 9.5
    $table.Range.Font.NameBi = 'Tahoma'
    $table.Range.ParagraphFormat.SpaceAfter = 3
    $table.Range.ParagraphFormat.SpaceBefore = 3
    $table.TopPadding = 3
    $table.BottomPadding = 3
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
    $selection.Font.Name = 'Tahoma'
    $selection.Font.Size = 19
    $selection.Font.SizeBi = 19
    $selection.Font.Color = 0
    $selection.Font.Bold = -1
    $selection.TypeText('Model Card การจัดลำดับแฟ้มผู้สมัครงาน')
    $selection.TypeParagraph()
    Paragraph 'HCD302 Creating Explainable AI | รุ่นเอกสาร 1.0 | 13 พฤศจิกายน 2569'
    Paragraph 'เอกสารนี้สรุปต้นแบบช่วยฝ่ายทรัพยากรบุคคลจัดลำดับแฟ้มหลังสัมภาษณ์และทดสอบทักษะ ผลนอกชุดฝึกให้ recall 90.1% แต่เสนอทบทวนถึง 73.5% ของแฟ้ม จึงต้องพิจารณาภาระงาน HR ควบคู่กับโอกาสพลาดผู้สมัคร โครงเอกสารประยุกต์จาก Mitchell et al. (2019) [1]'
    Heading '1 Model details'
    Paragraph 'โมเดลหลักคือ GradientBoostingClassifier สำหรับจำแนก HiringDecision แบบสองคลาส ใช้ scikit-learn 1.8.0 และ random_state 42 ผลการเลือกโมเดลในทั้ง 5 outer folds เป็น Gradient Boosting ต้นแบบนี้ประเมินกระบวนการเลือกโมเดลด้วย cross-validation และยังไม่ได้บันทึกโมเดลสุดท้ายสำหรับให้บริการ'
    Paragraph 'ผู้พัฒนา กลุ่มการคัดเลือกผู้สมัครงาน ได้แก่ นายภูจิตร จิรวิริยาภรณ์ 6730614005 นายปัญญพัฒน์ เปรียบปาน 6730614014 นายอภิวิชญ์ เลิศกมลรักษ์ 6730614015 นายษุภากรณ์ จิราจินดากุล 6730614020 และนายนพัทธ์ ฝอยทอง 6730614021'
    Paragraph 'พารามิเตอร์สำคัญของ Gradient Boosting คือ learning_rate 0.1 จูน max_depth ใน {1, 2, 3} และ n_estimators ใน {50, 100} ส่วน L2 Logistic Regression จูน C ใน {0.1, 1, 10} และตั้ง max_iter 1000 เลือก Logistic Regression เมื่อ inner AP ของ Gradient Boosting สูงกว่าไม่เกิน 0.01'
    Heading '2 Intended use'
    Paragraph 'ผู้ใช้คือฝ่าย HR และผู้จัดการตำแหน่งงาน ใช้คะแนนช่วยจัดลำดับแฟ้มที่มีผลสัมภาษณ์และทักษะแล้ว เพื่อให้เจ้าหน้าที่ทวนข้อมูลก่อนตัดสินใจ ผู้สมัครควรขอแก้ไขข้อมูลและขอให้ทบทวนได้ตามช่องทางที่หน่วยงานกำหนด'
    Paragraph 'Out-of-scope uses ครอบคลุมการรับหรือปฏิเสธงานโดยอัตโนมัติ การคัดกรองก่อนมีคะแนนสัมภาษณ์หรือทักษะ การประเมินความสามารถหรือผลงานจริง และการนำไปใช้กับประชากรหรือตำแหน่งงานจริงที่ยังไม่ผ่านการตรวจสอบ'
    Heading '3 Factors'
    Paragraph 'ตรวจผลตาม Gender 0/1 และอายุ 20–29, 30–39 และ 40 ปีขึ้นไป โดย Age และ Gender ใช้ตรวจข้อมูลและ fairness เท่านั้น ตัวแปรฝึกมี EducationLevel, ExperienceYears, InterviewScore และ SkillScore ปัจจัยที่อาจทำให้ผลต่างกัน ได้แก่ สัดส่วนฉลาก ข้อมูลประสบการณ์ที่หาย และรูปแบบคะแนนระหว่างกลุ่ม'

    PageBreak
    Write-Output 'Writing page 2'
    Heading '4 Metrics'
    Paragraph 'ใช้ sensitivity หรือ recall เป็นเป้าหมายหลักเพื่อลดการพลาดผู้สมัครที่มีฉลากรับเข้าทำงาน ตั้งเป้าอย่างน้อย 90% จากคำทำนาย inner CV และเลือก threshold ที่ให้ specificity สูงสุดในตัวเลือกที่ผ่านเกณฑ์ ใช้เกณฑ์เดียวกันกับทุกกลุ่มภายใน outer fold นั้น'
    Paragraph 'รายงาน PPV เพื่อประเมินความแม่นของแฟ้มที่เสนอทบทวน AP เพื่อเปรียบเทียบคุณภาพการจัดอันดับกับความชุกฉลากบวก 31.0% Brier score เพื่อวัดความคลาดเคลื่อนของค่าความน่าจะเป็น และ review rate เพื่อประเมินปริมาณงาน HR โดย AP สูงและ Brier ต่ำเป็นทิศทางที่ต้องการ'
    Paragraph 'False positive คือแฟ้มที่เสนอทบทวนก่อนแต่ฉลากจำลองระบุว่าไม่รับ ทำให้ใช้เวลาทบทวนเพิ่ม False negative คือแฟ้มที่ได้ลำดับต่ำแต่ฉลากระบุว่ารับ ซึ่งอาจเสียโอกาสเมื่อคิวมีจำกัด ทั้งสองกรณีวัดเทียบกับผลตัดสินใจในข้อมูลจำลอง'
    $foldRows = @()
    foreach($split in $results.splits) {
        $model = $split.models | Where-Object name -eq $split.chosen
        $foldRows += ,@([string]$split.fold,[string]$model.params.model__max_depth,[string]$model.params.model__n_estimators,('{0:N4}' -f [double]$model.cut))
    }
    Table @('Outer fold','max depth','จำนวนต้นไม้','Threshold') $foldRows @(90,100,130,206)
    Paragraph 'ทุก fold ใช้ learning_rate 0.1 ค่าทำนายตั้งแต่ threshold ขึ้นไปถูกเสนอให้ทบทวนก่อน ค่า threshold เป็นผลจากข้อมูลฝึกแต่ละ fold จึงยังไม่มีเกณฑ์สุดท้ายสำหรับระบบใช้งานจริง'
    Heading '5 Training data และ Evaluation data'
    Paragraph 'ใช้ไฟล์ recruitment_data_cleaned.csv จำนวน 1,500 แถว มีตัวแปรอธิบายเดิม 10 ตัวและเป้าหมาย HiringDecision โดยฉลาก 1 จำนวน 465 แถว และฉลาก 0 จำนวน 1,035 แถว แหล่งที่ระบุในข้อเสนอโครงการคือ Predicting Hiring Decisions in Recruitment Data ของ Rabie El Kharoua บน Kaggle [2] พร้อมใบอนุญาต CC BY 4.0 ตามเอกสารโครงการ'
    Paragraph 'ข้อมูลเป็นผู้สมัครสังเคราะห์ ตรวจแล้วไม่พบแถวซ้ำ ExperienceYears หาย 183 แถวหรือ 12.2% การทดลองนี้อ่านค่าจาก CSV โดยตรงและยกเลิกกฎใช้ Age แก้ประสบการณ์แล้ว ส่วนประวัติการทำความสะอาดก่อนเป็นไฟล์ cleaned และรายละเอียดใบอนุญาตต้องยืนยันกับต้นทางก่อนเผยแพร่ซ้ำ'
    Paragraph 'แบ่งด้วย nested stratified CV ชั้นนอก 5 folds แต่ละรอบมี train 1,200 และ test 300 แถว ชั้นใน 4 folds ใช้จูนพารามิเตอร์และเลือก threshold แล้วรวมคำทำนาย outer test ครบ 1,500 แถวเป็น out-of-fold evaluation ข้อมูลประเมินจึงมาจากชุดสังเคราะห์เดียวกันและยังไม่มี external test set'
    Paragraph 'Pipeline เติมค่ามัธยฐานตัวเลขจากชุดฝึก ทำ one-hot encoding ของ EducationLevel และ standardize ตัวเลขสำหรับ Logistic Regression กัน Age, Gender, PreviousCompanies, DistanceFromCompany, PersonalityScore และ RecruitmentStrategy ออกจากตัวแปรหลัก ต้องยืนยันเวลาเก็บ 4 ตัวแปรหลักว่าอยู่ก่อนการตัดสินใจจริง'

    PageBreak
    Write-Output 'Writing page 3'
    Heading '6 Quantitative analyses'
    Paragraph 'ผลต่อไปนี้เป็นคำทำนาย outer test ที่แต่ละแถวไม่ได้อยู่ในชุดฝึกของโมเดลที่ทำนายแถวนั้น Gradient Boosting ถูกเลือกครบทุก fold ผล Selected จึงตรงกับแถว Gradient Boosting'
    $metricRows = @()
    foreach($name in @('Dummy','Logistic Regression','Gradient Boosting')) {
        $m = $metrics | Where-Object model -eq $name
        $metricRows += ,@($name,('{0:N3}' -f [double]$m.AP),('{0:N3}' -f [double]$m.Brier),(Percent $m.sensitivity),(Percent $m.PPV),(Percent $m.review_rate))
    }
    Table @('โมเดล','AP','Brier','Recall','PPV','เสนอทบทวน') $metricRows @(145,55,60,80,75,111)
    Paragraph 'Gradient Boosting ได้ AP 0.614 เทียบ Dummy 0.310 และ Logistic Regression 0.571 มี TP 419, FP 683, FN 46 และ TN 352 เสนอทบทวน 1,102 จาก 1,500 แฟ้ม หรือ 73.5% และได้ specificity 34.0% ผลนี้สะท้อนต้นทุนด้านปริมาณงานเมื่อมุ่ง recall สูง'
    Paragraph 'ตารางรายกลุ่มแสดงตัวเศษ/ตัวส่วนของ FNR และ FPR ตามด้วย Wilson 95% CI ในวงเล็บ FNR ใช้ตัวส่วนเป็นฉลากบวก ส่วน FPR ใช้ฉลากลบ อัตราเสนอทบทวนใช้ผู้สมัครทั้งหมดในกลุ่ม'
    $groupRows = @()
    foreach($group in @('Gender 0','Gender 1','20–29','30–39','40+')) {
        $fnr = $fairness | Where-Object { $_.group -eq $group -and $_.metric -eq 'FNR' }
        $fpr = $fairness | Where-Object { $_.group -eq $group -and $_.metric -eq 'FPR' }
        $review = $fairness | Where-Object { $_.group -eq $group -and $_.metric -eq 'Review rate' }
        $fnText = "$($fnr.numerator)/$($fnr.denominator) = $(Percent $fnr.rate)`n$('{0:N1}–{1:N1}%' -f (100*[double]$fnr.ci_low),(100*[double]$fnr.ci_high))"
        $fpText = "$($fpr.numerator)/$($fpr.denominator) = $(Percent $fpr.rate)`n$('{0:N1}–{1:N1}%' -f (100*[double]$fpr.ci_low),(100*[double]$fpr.ci_high))"
        $groupRows += ,@($group,[string]$fnr.n,$fnText,$fpText,(Percent $review.rate))
    }
    Table @('กลุ่ม','n','FNR และ 95% CI','FPR และ 95% CI','เสนอทบทวน') $groupRows @(82,42,148,148,106)
    Paragraph 'Gender 0 มี FNR 12.66% และ Gender 1 มี FNR 7.02% ช่องว่าง 5.64 จุดเปอร์เซ็นต์ ส่วน FPR ต่างกัน 0.21 จุดเปอร์เซ็นต์ ช่องว่างอายุแบบสูงสุดลบต่ำสุดของ FNR เท่ากับ 5.80 และ FPR เท่ากับ 4.39 จุดเปอร์เซ็นต์'
    Paragraph 'รายงานรหัสเพศตาม CSV โดยข้อเสนอโครงการระบุ 0 ชาย และ 1 หญิง กลุ่มเพศมีสองรหัสและช่วงอายุจำกัด จึงยังครอบคลุมประชากรจริงไม่ครบ ช่วงความเชื่อมั่นนี้ใช้สมมติฐานข้อมูลอิสระและยังไม่รวมความไม่แน่นอนจากการฝึกใหม่หรือพิสูจน์ความเป็นธรรมของระบบ'

    PageBreak
    Write-Output 'Writing page 4'
    Heading '7 Explainability'
    Paragraph 'Global explanation ใช้ permutation feature importance บน outer test สลับตัวแปรต้นทาง 25 ครั้งต่อ fold แล้ววัด AP ที่ลดลง โมเดลพึ่ง EducationLevel มากที่สุด 0.169 ± 0.034 รองลงมาคือ InterviewScore 0.099 ± 0.035, SkillScore 0.096 ± 0.037 และ ExperienceYears 0.067 ± 0.023 ค่า ± เป็น SD รวมการสุ่มและ fold'
    $picture = $selection.InlineShapes.AddPicture((Join-Path $root 'model_card_charts\03_pfi.png'),$false,$true)
    $picture.LockAspectRatio = -1
    $picture.Width = 420
    $selection.SetRange($picture.Range.End,$picture.Range.End)
    $selection.TypeParagraph()
    Paragraph 'ALE แยก 5 folds พร้อมจำนวนข้อมูลแต่ละช่วง แสดงคะแนนที่สูงขึ้นเมื่อประสบการณ์เข้าสู่ช่วงประมาณ 7 ปีขึ้นไปในแบบจำลองที่เลือก PFI แบบกลุ่มสลับ InterviewScore กับ SkillScore พร้อมกันเพื่อตรวจ sensitivity ทั้งสองคำอธิบายต้องอ่านในบริบทข้อมูลรองรับ'
    Paragraph 'Local explanation ใช้ exact interventional Shapley ครบทุกชุดของ 4 ตัวแปร โดยใช้ชุดฝึกของ fold เป็น background และแสดง waterfall ค่าด้านล่างเป็นจุดเปอร์เซ็นต์ของค่าทำนาย'
    Table @('กรณีและแถว CSV','ค่าฐาน → ค่าทำนาย','Threshold','ปัจจัยเด่น') @(
        @('FN แถว 1400','31.00% → 16.68%','16.87%','Interview +10.30, Skill −10.16, Experience −8.53'),
        @('FP แถว 1011','31.01% → 16.05%','15.80%','Interview −8.16, Education −6.78, Experience +3.08')
    ) @(110,122,78,216)
    Paragraph 'FN แสดงว่าคะแนนสัมภาษณ์ที่เพิ่มค่าทำนายถูกหักล้างด้วยทักษะและประสบการณ์ ส่วน FP ยังผ่านเกณฑ์เพราะ threshold ต่ำ ตรวจค่าฐานบวกผลทุกตัวแปรตรงกับค่าทำนาย โดย residual สูงสุดในสองกรณีประมาณ 2.8×10⁻¹⁷ เมื่อสุ่ม background 100 รายซ้ำ 10 ครั้ง ตัวแปรเด่นตรงกับ full background 5/10 ครั้งสำหรับ FN และ 7/10 สำหรับ FP'
    Paragraph 'ใช้ lime 0.2.0.1 จริง สุ่ม 5,000 ตัวอย่างต่อ seed รวม 10 seeds ต่อกรณี ใช้ quartile bins และ categorical education ค่า weighted R² เฉลี่ยของ FN เท่ากับ 0.483 และ FP เท่ากับ 0.229 ตัวแปรเด่นของ LIME ตรงกัน 10/10 seeds ทั้งคู่ แต่ FP ให้ EducationLevel เด่น ขณะที่ SHAP ให้ InterviewScore เด่น'
    Paragraph 'ค่า R² มาจาก neighborhood ที่ใช้ fit ของแพ็กเกจ จึงต้องตีความ fidelity อย่างจำกัด ปัจจัยเด่นที่คงที่ข้าม seed ยังต้องพิจารณาร่วมกับ fidelity ต่ำ LIME อธิบายการอยู่ในช่วงค่า ส่วน SHAP อธิบายส่วนต่างจาก background'

    PageBreak
    Write-Output 'Writing page 5'
    Heading '8 Ethical considerations'
    Paragraph 'ผู้สมัครอาจเสียโอกาสจาก FN โดยเฉพาะเมื่อคิวทบทวนจำกัด ขณะที่ FP จำนวนมากเพิ่มภาระ HR และอาจทำให้รายอื่นรอนาน ผลลัพธ์เป็นความสอดคล้องกับฉลากการรับเข้าทำงานจำลอง จึงต้องให้ผู้รับผิดชอบพิจารณาความเหมาะสมของเกณฑ์ฉลากก่อนใช้กับบุคคลจริง'
    Paragraph 'พบ FNR ของ Gender 0 สูงกว่า Gender 1 อยู่ 5.64 จุดเปอร์เซ็นต์ และ FNR ในกลุ่มอายุ 40 ปีขึ้นไปสูงกว่ากลุ่ม 20–29 ปีอยู่ 5.80 จุดเปอร์เซ็นต์ แม้ Age และ Gender ถูกกันจากตัวแปรฝึก ผลที่ต่างกันยังต้องตรวจทั้งการแทนตัวผ่านตัวแปรอื่น ความชุก และความเป็นตัวแทนของข้อมูล'
    Paragraph 'สิ่งที่กลุ่มทำแล้วประกอบด้วยการกันตัวแปรอ่อนไหวออกจากการฝึก ยกเลิกกฎใช้ Age แก้ประสบการณ์ ใช้ Pipeline ที่เรียนรู้จากชุดฝึก ตั้งเป้า recall เพื่อลด FN และรายงานตัวเศษ ตัวส่วน ช่วงความเชื่อมั่น และข้อผิดพลาดรายกลุ่ม พร้อมตรวจความเสถียรของคำอธิบาย'
    Paragraph 'แนวทางลดผลกระทบก่อนทดลองจริงคือให้ HR ทบทวนแฟ้มคะแนนต่ำด้วย จัดช่องทางตรวจแก้ข้อมูลและอุทธรณ์ กำหนดผู้รับผิดชอบและเวลาทบทวน รวมทั้งจำกัดผู้เข้าถึงข้อมูลผู้สมัคร ข้อความสำหรับผู้สมัครที่สร้างไว้ยังอยู่ในขั้นรอ HR ตรวจและกำหนดช่องทางติดต่อจริง'
    Heading '9 Caveats and recommendations'
    Paragraph 'ข้อมูลมีเพียง 1,500 รายสังเคราะห์และไม่มี external test set จึงยังสรุปประสิทธิภาพกับผู้สมัครจริงไม่ได้ การแบ่งสุ่มถือว่าแต่ละแถวเป็นหน่วยอิสระ แต่ยังไม่มีหลักฐานเรื่องการเปลี่ยนแปลงตามเวลา ข้อมูลหลายตำแหน่งงาน หรือความสัมพันธ์ระหว่างผู้สมัครในองค์กรจริง'
    Paragraph 'Brier score ยังต้องใช้ร่วมกับ calibration analysis ส่วน Wilson CI รายกลุ่มไม่ครอบคลุมความไม่แน่นอนทั้งหมด คำอธิบาย PFI/ALE/SHAP/LIME ขึ้นกับข้อมูลอ้างอิง ความสัมพันธ์ของตัวแปร และบริเวณที่มีข้อมูล การสลับหรือสุ่มค่าบางชุดอาจไม่สอดคล้องกับผู้สมัครจริง'
    Paragraph 'ก่อนใช้จริงต้องยืนยันแหล่งข้อมูลและสิทธิใช้งาน ประวัติ preprocessing และความหมายรหัสเพศ ตรวจเวลาการเก็บตัวแปรกับ HR แล้วประเมินกับข้อมูลจริงที่ได้รับอนุญาต เลือก threshold ตามกำลังทบทวน ต้นทุน FN/FP และผลรายกลุ่ม ตรวจ calibration และ drift ตลอดจนทบทวน fidelity ของคำอธิบายก่อนส่งให้ผู้สมัคร'
    Paragraph 'หากพัฒนาต่อเป็นระบบให้บริการ ต้องฝึกและจัดเก็บโมเดลสุดท้ายพร้อมเวอร์ชันและ threshold กำหนดผู้รับผิดชอบ ระบบบันทึกการทบทวน และช่องทางอุทธรณ์ โดยใช้ผลใน Model Card นี้เป็นผลประเมินต้นแบบ'
    Heading 'เอกสารอ้างอิงและหลักฐานผลรัน'
    $selection.Font.Size = 9
    Paragraph '[1] Mitchell, M. et al. (2019). Model Cards for Model Reporting. FAT* 2019. DOI 10.1145/3287560.3287596. https://arxiv.org/abs/1810.03993'
    Paragraph '[2] Rabie El Kharoua. Predicting Hiring Decisions in Recruitment Data. Kaggle. https://www.kaggle.com/datasets/rabieelkharoua/predicting-hiring-decisions-in-recruitment-data แหล่งข้อมูลและ CC BY 4.0 อ้างตามข้อเสนอโครงการที่ได้รับ'
    Paragraph 'หลักฐานภายในประกอบด้วย recruitment_model_card_visual.ipynb, model_card_results.json, model_card_metrics_full.csv, model_card_fairness.csv, model_card_fairness_gaps.csv และ model_card_lime_stability.csv ค่า SHA256 ของ CSV คือ 1964f081f1d01fd3df9701d9a48cf3153782d43c75a290b6277074ec6e1ce7fc'
    $docPath = Join-Path $output 'HCD302_Model_Card.docx'
    $pdfPath = Join-Path $qa 'model_card_check_final.pdf'
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
