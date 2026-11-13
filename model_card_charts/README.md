# รายชื่อกราฟ

## 1. เปรียบเทียบคุณภาพโมเดล
ไฟล์: 01_model_comparison.png

Average Precision สูงดี ส่วน Brier score ต่ำดี

## 2. ความผิดพลาดและการกระจายค่าทำนาย
ไฟล์: 02_confusion_matrix.png

Confusion matrix และค่าความน่าจะเป็นแยกตามฉลากจริง

## 3. PFI — ความสำคัญของตัวแปร
ไฟล์: 03_pfi.png

AP ลดลงเท่าไรเมื่อสุ่มสลับตัวแปร แถบแสดง ±1 SD ไม่ใช่ confidence interval

## 4. Fairness พร้อม Wilson 95% CI
ไฟล์: 04_fairness_wilson.png

FNR, FPR และสัดส่วนเสนอทบทวนรายกลุ่ม ช่วงนี้ไม่รวมความไม่แน่นอนจากการฝึกใหม่

## 5. ALE — คะแนนทักษะ
ไฟล์: 05_ale_skill.png

รูปแบบคะแนนตามทักษะ แยก fold พร้อมจำนวนข้อมูลในช่วง; ไม่ใช่ผลเชิงเหตุและผล

## 6. SHAP waterfall — FN
ไฟล์: 06_shap_waterfall_fn.png

แถว CSV 1400: จากค่าฐานชุดฝึก บวกผลตัวแปรจนถึงค่าทำนาย พร้อมเส้น threshold

## 7. LIME — Fidelity และความเสถียร
ไฟล์: 07_lime_fidelity_stability.png

Weighted R² จากแพ็กเกจ lime บน neighborhood ที่ใช้ fit และ SD ของน้ำหนักข้าม 10 seeds

## 8. LIME เทียบ SHAP — Near threshold
ไฟล์: 08_lime_vs_shap_near_threshold.png

ซ้ายคือน้ำหนักการอยู่ในช่วงค่าจากแพ็กเกจ lime จริง; ขวาคือ SHAP attribution ทั้งสองใช้คำถามอ้างอิงต่างกัน