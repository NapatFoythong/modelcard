01_model_comparison.png
เปรียบเทียบคุณภาพโมเดล
Average Precision สูงดี ส่วน Brier score ต่ำดี

02_confusion_matrix.png
ความผิดพลาดและการกระจายค่าทำนาย
Confusion matrix และค่าความน่าจะเป็นแยกตามฉลากจริง

03_pfi.png
PFI — ความสำคัญของตัวแปร
AP ลดลงเท่าไรเมื่อสุ่มสลับตัวแปร แถบแสดง ±1 SD ไม่ใช่ confidence interval

04_fairness_wilson.png
Fairness พร้อม Wilson 95% CI
FNR, FPR และสัดส่วนเสนอทบทวนรายกลุ่ม ช่วงนี้ไม่รวมความไม่แน่นอนจากการฝึกใหม่

05_ale_experience.png
ALE — ประสบการณ์ทำงาน
รูปแบบคะแนนตามประสบการณ์ แยก fold พร้อมจำนวนข้อมูลในช่วง

06_shap_waterfall_fn.png
SHAP waterfall — FN
แถว CSV 1400: จากค่าฐานชุดฝึก บวกผลตัวแปรจนถึงค่าทำนาย พร้อมเส้น threshold

07_shap_waterfall_fp.png
SHAP waterfall — FP
แถว CSV 1011: จากค่าฐานชุดฝึก บวกผลตัวแปรจนถึงค่าทำนาย พร้อมเส้น threshold

08_lime_fidelity_stability.png
LIME — Fidelity และความเสถียร
Weighted R² จากแพ็กเกจ lime บน neighborhood ที่ใช้ fit และ SD ของน้ำหนักข้าม 10 seeds