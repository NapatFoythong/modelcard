"""Additional auditable notebook sections aligned to the project proposal."""

def pretraining(md, code):
    md('''### 2.1 ตรวจคุณภาพข้อมูลและอคติก่อนฝึก
ตรวจแถวซ้ำก่อนแบ่ง fold แล้ว (หากพบจะหยุดให้แก้ก่อน) ตรวจช่วงอายุ/คะแนน
ความชุกของฉลาก ข้อมูลหายรายกลุ่ม และกลยุทธ์รับสมัคร ตามแผนหน้า 2
รหัสเพศ 0/1 ใช้ตาม CSV; รายงานระบุ 0 ชาย/1 หญิง แต่ยังควรตรวจต้นทางก่อนใช้จริง
การตรวจนี้ไม่พิสูจน์ว่าไม่มีอคติ และคะแนน/ฉลากสังเคราะห์ยังต้องให้ HR ตรวจเกณฑ์
ที่มาที่ระบุในข้อเสนอ: Rabie El Kharoua, Predicting Hiring Decisions in Recruitment Data,
Kaggle, CC BY 4.0 (อ้างตามเอกสารที่ได้รับ ยังไม่ได้ยืนยันข้อมูลต้นทางออนไลน์)''')
    code('''display(Markdown(f'**ข้อมูล {len(data):,} แถว · แถวซ้ำ {duplicate_count} แถว**'))
display(data[['Age', 'ExperienceYears', 'InterviewScore', 'SkillScore']].agg(['min','max']))
audit_groups = {'Gender 0': data.Gender.eq(0), 'Gender 1': data.Gender.eq(1),
                '20–29': data.Age.between(20,29), '30–39': data.Age.between(30,39),
                '40+': data.Age.ge(40)}
rows = []
for name, mask in audit_groups.items():
    rows.append({'group': name, 'n': int(mask.sum()),
                 'positive_prevalence': data.loc[mask,'HiringDecision'].mean(),
                 'missing_experience_csv': raw.loc[mask,'ExperienceYears'].isna().mean(),
                 'missing_experience_training_input': data.loc[mask,'ExperienceYears'].isna().mean()})
data_audit = pd.DataFrame(rows).set_index('group')
display(data_audit.round(3))
strategy = data.groupby('RecruitmentStrategy').HiringDecision.agg(['mean','size'])
fig, axes = plt.subplots(1,2,figsize=(12,4))
data_audit[['positive_prevalence','missing_experience_training_input']].plot.bar(ax=axes[0],rot=35)
axes[0].set(title='Pre-training group audit',ylabel='Proportion',ylim=(0,1))
axes[1].bar(strategy.index.astype(str),strategy['mean'],color=COLORS[1])
axes[1].set(title='Label prevalence by recruitment strategy',xlabel='Strategy code',ylabel='Proportion',ylim=(0,1))
for i,n in enumerate(strategy['size']): axes[1].text(i,.02,f'n={n}',ha='center')
plt.tight_layout(); plt.show()
fig, axes = plt.subplots(1,2,figsize=(11,4))
for ax, feature in zip(axes,['InterviewScore','SkillScore']):
    values=[data.loc[data.Gender.eq(g),feature].dropna() for g in [0,1]]
    ax.boxplot(values, tick_labels=['Gender 0','Gender 1'])
    ax.set(title=f'{feature} by gender code',ylabel='Score')
plt.tight_layout(); plt.show()
outside_age = int((~data.Age.between(20,50)).sum())
display(Markdown(f'อายุนอกช่วง 20–50: **{outside_age} ราย**; ช่วงรายงาน fairness ใช้ 40 ปีขึ้นไป ไม่ตัดที่ 50'))
''')
    md('''### 2.2 ทำไมไม่มี epoch?
โมเดลนี้ไม่ใช่ neural network จึงไม่ใช้ลูป epoch
Logistic Regression ใช้ `max_iter=1000` เป็นเพดานรอบ solver ไม่จำเป็นต้องทำครบทุกครั้ง
Gradient Boosting เพิ่มต้นไม้ตาม `n_estimators` (จูน 50/100) และจำกัด `max_depth` (1/2/3)
5 outer × 4 inner folds เป็นการประเมิน/เลือกโมเดล ไม่ใช่ epoch
Dummy ไม่เรียนรู้แบบวน epoch; ใช้ความชุกในชุดฝึกเป็นคะแนนอ้างอิง''')


def advanced(md, code):
    md('''## 9A. ตัวชี้วัดครบตามแผนและความเป็นธรรม
ใช้คำทำนาย out-of-fold และ threshold ที่เลือกในแต่ละ fold เดิม
“ผลบวก” หมายถึงเสนอแฟ้มให้ HR ทบทวนก่อน ไม่ใช่คำสั่งรับเข้าทำงาน
แสดง sensitivity, specificity, PPV, AP, Brier และสัดส่วนเสนอทบทวน
อัตรารายกลุ่มแสดงตัวเศษ/ตัวส่วน พร้อม Wilson 95% CI; ตัวส่วนเป็นศูนย์แสดง NaN
ช่องว่างเป็น max−min ภายในมิติเดียวกัน (จุดเปอร์เซ็นต์) ไม่ใช่การทดสอบนัยสำคัญ
Wilson สมมติการสังเกตอิสระ และไม่ได้รวมความไม่แน่นอนจากการฝึกโมเดลใหม่ทุกครั้ง''')
    code('''def safe_rate(a,b):
    return a/b if b else np.nan

def wilson(a,n,z=1.959963984540054):
    if not n: return np.nan,np.nan
    p=a/n; denominator=1+z*z/n
    center=(p+z*z/(2*n))/denominator
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return center-half,center+half

rows=[]
for name,m in metrics.iterrows():
    rows.append(dict(model=name,sensitivity=safe_rate(m.tp,m.tp+m.fn),
                     specificity=safe_rate(m.tn,m.tn+m.fp),PPV=safe_rate(m.tp,m.tp+m.fp),
                     AP=m.ap,prevalence=y.mean(),Brier=m.brier,
                     review_rate=(m.tp+m.fp)/m.n))
audit_metrics=pd.DataFrame(rows)
display(audit_metrics.round(3))
audit_metrics.set_index('model')[['sensitivity','specificity','PPV','review_rate']].plot.bar(
    figsize=(11,4),color=COLORS,rot=20,ylim=(0,1),title='Operational metrics: prioritise files for HR review')
plt.tight_layout(); plt.show()
fair_rows=[]
for name,mask in audit_groups.items():
    m=summary(y[mask],pred[mask,3],dec[mask,3])
    rates={'FNR':(m['fn'],m['fn']+m['tp']), 'FPR':(m['fp'],m['fp']+m['tn']),
           'Review rate':(m['tp']+m['fp'],m['n'])}
    for rate,(a,b) in rates.items():
        lo,hi=wilson(a,b)
        fair_rows.append(dict(group=name,dimension='Gender' if name.startswith('Gender') else 'Age',
            n=m['n'],metric=rate,numerator=a,denominator=b,rate=safe_rate(a,b),
            ci_low=lo,ci_high=hi,flag='no denominator' if not b else ('small denominator (<30)' if b<30 else '')))
fairness=pd.DataFrame(fair_rows)
display(fairness.round(3))
fairness_gaps=fairness.groupby(['dimension','metric'])['rate'].agg(['min','max','count']).reset_index()
fairness_gaps['gap_pp']=(fairness_gaps['max']-fairness_gaps['min'])*100
fairness_gaps.loc[fairness_gaps['count']<2,'gap_pp']=np.nan
display(fairness_gaps.round(2))
fig,axes=plt.subplots(1,3,figsize=(15,4))
for ax,metric in zip(axes,['FNR','FPR','Review rate']):
    t=fairness[fairness.metric.eq(metric)]
    ax.errorbar(np.arange(len(t)),t.rate,
                yerr=np.array([t.rate-t.ci_low,t.ci_high-t.rate]),fmt='o',capsize=4,color=COLORS[2])
    ax.set(xticks=np.arange(len(t)),xticklabels=t.group,title=metric+' (Wilson 95% CI)',ylim=(0,1))
    ax.tick_params(axis='x',rotation=35)
plt.tight_layout(); plt.show()
fold_choices=pd.DataFrame([{'fold':s['fold'],'model':s['chosen'],
                           'threshold':next(m['cut'] for m in s['models'] if m['name']==s['chosen'])}
                          for s in splits])
display(fold_choices)
''')
    md('''## 9B. PFI แบบกลุ่มสำหรับตัวแปรสัมพันธ์กัน
ตรวจ Spearman correlation บนตัวแปรหลัก แล้วสลับคู่ที่ |ρ| ≥ 0.30
เพิ่มคู่ InterviewScore/SkillScore เป็น sensitivity check ที่กำหนดไว้ล่วงหน้า แม้ความสัมพันธ์ต่ำ
สลับแถวเดียวกันพร้อมกันทั้งคู่เพื่อคงความสัมพันธ์ภายในกลุ่ม ใช้ outer test เท่านั้น
แถบ ±1 SD รวมการสุ่มซ้ำและความต่างระหว่าง fold ไม่ใช่ confidence interval''')
    code('''corr=X.corr(method='spearman')
fig,ax=plt.subplots(figsize=(6,5))
im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r')
ax.set(xticks=range(4),yticks=range(4),xticklabels=features,yticklabels=features,title='Spearman correlation')
plt.setp(ax.get_xticklabels(),rotation=35,ha='right')
for i in range(4):
    for j in range(4): ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center')
fig.colorbar(im,ax=ax); plt.tight_layout(); plt.show()
feature_groups=[(features[i],features[j]) for i in range(4) for j in range(i+1,4)
                if abs(corr.iloc[i,j])>=.30]
score_pair=('InterviewScore','SkillScore')
if score_pair not in feature_groups: feature_groups.append(score_pair)
group_records=[]
for fold,(model,tr,te,cut) in enumerate(fitted,1):
    baseline=average_precision_score(y.iloc[te],model.predict_proba(X.iloc[te])[:,1])
    rng=np.random.default_rng(seed+fold)
    for group in feature_groups:
        for repeat in range(25):
            shuffled=X.iloc[te].copy(); permutation=rng.permutation(len(te))
            shuffled.loc[:,list(group)]=X.iloc[te][list(group)].iloc[permutation].to_numpy()
            drop=baseline-average_precision_score(y.iloc[te],model.predict_proba(shuffled)[:,1])
            group_records.append(dict(fold=fold,repeat=repeat,group=' + '.join(group),drop=drop))
grouped_pfi=pd.DataFrame(group_records)
gt=grouped_pfi.groupby('group')['drop'].agg(['mean','std'])
fig,ax=plt.subplots(figsize=(10,max(3,len(gt)*.6)))
ax.barh(gt.index,gt['mean'],xerr=gt['std'],capsize=4,color=COLORS[1])
ax.set(title='Grouped permutation importance',xlabel='Decrease in AP (±1 SD)')
plt.tight_layout(); plt.show()
''')
    md('''## 9C. ALE — รูปแบบคะแนนตามประสบการณ์และทักษะ
คำนวณ first-order ALE แยก outer fold: ใช้ quantile bins จากชุดฝึก
แล้ววัดผลต่างคำทำนายที่ขอบช่วงกับผู้สมัคร outer test ที่อยู่ในช่วงนั้น
สะสมและจัดศูนย์ด้วยจำนวนข้อมูลในแต่ละช่วง เส้นแต่ละสีคือหนึ่ง fold
ไม่วาดช่วงที่ไม่มีตัวอย่าง; แสดงจำนวนผู้สมัครแต่ละช่วงด้านล่าง
ALE แสดงรูปแบบของโมเดล ไม่ใช่ผลจากการเปลี่ยนคุณสมบัติจริง''')
    code('''ale_records=[]
for feature in ['ExperienceYears','SkillScore']:
    fig,axes=plt.subplots(2,1,figsize=(9,6),sharex=True,gridspec_kw={'height_ratios':[3,1]})
    for fold,(model,tr,te,cut) in enumerate(fitted,1):
        edges=np.unique(np.quantile(X.iloc[tr][feature].dropna(),np.linspace(0,1,9)))
        values=X.iloc[te][feature].to_numpy()
        inside=np.isfinite(values)&(values>=edges[0])&(values<=edges[-1])
        bins=np.clip(np.searchsorted(edges,values,side='right')-1,0,len(edges)-2)
        effects=[]; counts=[]
        for b in range(len(edges)-1):
            mask=inside&(bins==b); part=X.iloc[te].loc[mask].copy(); counts.append(len(part))
            if len(part):
                low=part.copy(); high=part.copy()
                low[feature]=edges[b]; high[feature]=edges[b+1]
                effects.append(np.mean(model.predict_proba(high)[:,1]-model.predict_proba(low)[:,1]))
            else: effects.append(np.nan)
        effects=np.array(effects); counts=np.array(counts)
        supported=counts>0
        # Do not bridge empty intervals: each supported segment is centred separately.
        curve=np.full(len(effects),np.nan)
        for segment in np.split(np.flatnonzero(supported),np.flatnonzero(np.diff(np.flatnonzero(supported))>1)+1):
            if len(segment):
                z=np.cumsum(effects[segment])-.5*effects[segment]
                curve[segment]=z-np.average(z,weights=counts[segment])
        mid=(edges[:-1]+edges[1:])/2
        axes[0].plot(mid,curve*100,marker='o',label=f'Fold {fold}')
        axes[1].step(mid,counts,where='mid',alpha=.7,label=f'Fold {fold}')
        for b in range(len(mid)):
            ale_records.append(dict(feature=feature,fold=fold,low=edges[b],high=edges[b+1],
                                    n=int(counts[b]),ALE_pp=float(curve[b]*100)))
    axes[0].axhline(0,color='gray',linewidth=1)
    axes[0].set(title=f'ALE: {feature}',ylabel='Centred probability effect (pp)')
    axes[0].legend(ncol=5,fontsize=8)
    axes[1].set(xlabel=feature,ylabel='Bin count')
    plt.tight_layout(); plt.show()
ale_table=pd.DataFrame(ale_records)
ale_table.to_csv(root/'model_card_ale.csv',index=False)
''')
    md('''## 9D. SHAP waterfall และความเสถียรของ background
เลือก TP, FP, FN ที่ใกล้ threshold ที่สุด และรายใกล้เกณฑ์ที่สุดโดยไม่จำกัดชนิด
หนึ่งรายอาจซ้ำระหว่างหมวดได้ จึงไม่ถือว่าเป็นตัวอย่างอิสระ
Waterfall เริ่มจากค่าเฉลี่ยคำทำนายบนชุดฝึก แล้วบวกผลแต่ละตัวแปรจนถึงคำทำนาย
ตรวจ efficiency และแสดงความถี่ที่ตัวแปรอันดับหนึ่งตรงกันจาก background 10 ชุด''')
    code('''shap_checks=[]
for case in cases:
    phi=np.array(case['phi']); order=np.argsort(-abs(phi))
    fig,ax=plt.subplots(figsize=(10,4.5))
    current=case['base']*100
    ax.bar(0,current,color=COLORS[0])
    labels=['Train base']
    for k,j in enumerate(order,1):
        contribution=phi[j]*100; new=current+contribution
        ax.plot([k-1,k],[current,current],color='gray',linestyle=':',linewidth=1)
        ax.bar(k,abs(contribution),bottom=min(current,new),color=COLORS[2] if contribution>=0 else COLORS[3])
        ax.text(k,max(current,new)+1,f'{contribution:+.1f}',ha='center',fontsize=9)
        labels.append(features[j]); current=new
    ax.bar(5,case['p']*100,color=COLORS[1]); labels.append('Prediction')
    ax.axhline(case['cut']*100,color='gray',linestyle='--',label='Fold threshold')
    ax.set(xticks=range(6),xticklabels=labels,ylabel='Probability of label 1 (%)',
           title=f"SHAP waterfall · {case['type']} · CSV row {case['row']}")
    ax.tick_params(axis='x',rotation=20); ax.legend(); plt.tight_layout(); plt.show()
    assert abs(case['base']+phi.sum()-case['p'])<1e-10
    shap_checks.append(dict(case=case['type'],row=case['row'],efficiency_error=case['residual'],
                            same_top_feature_out_of_10=case['top_same']))
display(pd.DataFrame(shap_checks))
''')
    md('''## 9E. LIME — local surrogate, fidelity และความเสถียรข้าม seed
ใช้แพ็กเกจ `lime` จริงผ่าน `LimeTabularExplainer` โดยกำหนดพารามิเตอร์คงที่ก่อนดูผล
ใช้ข้อมูลฝึกของ fold นั้นเท่านั้น ตั้ง EducationLevel เป็น categorical และแบ่งตัวเลขเป็น quartile bins
เติม missing สำหรับข้อมูลอ้างอิงด้วยมัธยฐานชุดฝึก ไม่ใช้ Age/Gender; prediction wrapper เรียก Pipeline เดิม
สุ่ม 5,000 ตัวอย่างต่อครั้ง ใช้ kernel_width = 0.75 × √4 และทดสอบ seed 0–9
weighted R² ใช้ `Explanation.score` ของแพ็กเกจ ซึ่งวัดบน neighborhood ที่ใช้ fit surrogate
จึงไม่ใช่คะแนนบน neighborhood ที่กันไว้ และเทียบตรง ๆ กับ R² ของวิธีเดิมไม่ได้
บันทึกคำอธิบาย HTML จากแพ็กเกจสำหรับ seed 0 ของแต่ละกรณีใน `lime_explanations`
การสุ่มอาจสร้างข้อมูลที่ไม่สมจริง และการใช้แพ็กเกจจริงไม่รับประกันว่า fidelity จะสูง
เอกสารวิธีใช้: https://lime-ml.readthedocs.io/en/latest/lime.html''')
    code('''from lime.lime_tabular import LimeTabularExplainer
from importlib.metadata import version

def explain_with_lime(model,row,train,random_seed,n=5000):
    med=train.median()
    anchor=row.fillna(med)
    explainer=LimeTabularExplainer(
        training_data=train.fillna(med).to_numpy(dtype=float),
        feature_names=features,class_names=['Not hired','Hired'],
        categorical_features=[0],mode='classification',discretize_continuous=True,
        discretizer='quartile',kernel_width=.75*np.sqrt(len(features)),
        feature_selection='none',random_state=random_seed)
    def predict(values):
        return model.predict_proba(pd.DataFrame(values,columns=features))
    explanation=explainer.explain_instance(anchor.to_numpy(dtype=float),predict,
        labels=(1,),num_features=len(features),num_samples=n)
    coef=np.zeros(len(features))
    for j,weight in explanation.local_exp[1]: coef[j]=weight
    labels={j:text for (j,_),(text,_) in zip(explanation.local_exp[1],explanation.as_list(label=1))}
    model_pred=float(model.predict_proba(row.to_frame().T)[:,1][0])
    assert abs(float(explanation.predict_proba[1])-model_pred)<1e-10
    assert abs(explanation.intercept[1]+coef.sum()-float(explanation.local_pred[0]))<1e-10
    return dict(coef=coef,r2=float(explanation.score),local_pred=float(explanation.local_pred[0]),
                model_pred=model_pred,labels=labels,explanation=explanation)

lime_rows=[]; lime_coefs={}; lime_representative={}
lime_dir=root/'lime_explanations'; lime_dir.mkdir(exist_ok=True)
display(Markdown(f'ใช้แพ็กเกจ **lime {version("lime")}** — 5,000 samples × 10 seeds ต่อกรณี'))
for case in cases:
    model,tr,te,cut=fitted[case['fold']-1]
    row=X.iloc[case['row']-2]
    results=[explain_with_lime(model,row,X.iloc[tr],s) for s in range(10)]
    key=case['type']; lime_coefs[key]=np.array([r['coef'] for r in results]); lime_representative[key]=results[0]
    results[0]['explanation'].save_to_file(str(lime_dir/(key.replace(' ','_')+'.html')),labels=[1])
    for s,r in enumerate(results):
        lime_rows.append(dict(case=key,row=case['row'],seed=s,weighted_R2=r['r2'],
                              local_prediction=r['local_pred'],model_prediction=r['model_pred'],
                              absolute_error=abs(r['local_pred']-r['model_pred']),
                              score_basis='package_weighted_training_neighborhood',
                              lime_version=version('lime'),num_samples=5000))
lime_checks=pd.DataFrame(lime_rows)
stability_rows=[]
for case in cases:
    key=case['type']; coefs=lime_coefs[key]
    top=np.argmax(abs(coefs),axis=1); mode=int(np.bincount(top,minlength=4).argmax())
    shap_top=int(np.argmax(np.abs(case['phi'])))
    stability_rows.append(dict(case=key,most_common_top=features[mode],top_agreement=float(np.mean(top==mode)),
                               agreement_with_SHAP_top=float(np.mean(top==shap_top)),
                               mean_weighted_R2=lime_checks.loc[lime_checks['case'].eq(key),'weighted_R2'].mean()))
lime_stability=pd.DataFrame(stability_rows)
display(lime_checks.groupby('case')[['weighted_R2','absolute_error']].agg(['mean','min','max']).round(3))
display(lime_stability.round(3))
fig,axes=plt.subplots(1,2,figsize=(12,4))
case_names=list(lime_coefs)
axes[0].boxplot([lime_checks.loc[lime_checks['case'].eq(k),'weighted_R2'] for k in case_names],tick_labels=case_names)
axes[0].set(title='LIME package fidelity across seeds',ylabel='Weighted training-neighborhood R²')
for k in case_names:
    axes[1].plot(features,lime_coefs[k].std(axis=0,ddof=1),marker='o',label=k)
axes[1].set(title='Local coefficient variability',ylabel='Coefficient SD (probability units)')
axes[1].tick_params(axis='x',rotation=25); axes[1].legend()
plt.tight_layout(); plt.show()
# Bin-membership coefficients and SHAP attributions use different reference questions.
for case in cases:
    key=case['type']; c=lime_coefs[key]
    fig,axes=plt.subplots(1,2,figsize=(12,3.5))
    labels=[lime_representative[key]['labels'][j] for j in range(len(features))]
    axes[0].barh(labels,c.mean(axis=0)*100,xerr=c.std(axis=0,ddof=1)*100,color=COLORS[1],capsize=3)
    axes[0].set(title=f'{key}: LIME package explanation',xlabel='Bin-membership weight (pp; mean ±1 SD)')
    axes[1].barh(features,np.array(case['phi'])*100,color=COLORS[2])
    axes[1].set(title='Exact SHAP attribution',xlabel='Contribution (pp)')
    for ax in axes: ax.axvline(0,color='gray',linewidth=1)
    plt.tight_layout(); plt.show()
display(Markdown('หาก weighted R² ต่ำหรือคำอธิบายต่างกัน ให้ตรวจ neighborhood, background และความสัมพันธ์ของตัวแปรก่อนส่งให้ HR; ห้ามเลือกเฉพาะ seed ที่ดูดี'))
lo=lime_stability.mean_weighted_R2.min(); hi=lime_stability.mean_weighted_R2.max()
display(Markdown(f'**ผลที่พบ:** weighted R² เฉลี่ยของแต่ละกรณีอยู่ที่ {lo:.2f}–{hi:.2f} '
                 'จึงอธิบายความแปรปรวนใน neighborhood ได้เพียงบางส่วน ไม่ควรใช้ LIME เป็นเหตุผลรายบุคคลเพียงอย่างเดียว '
                 'LIME อธิบายการอยู่ในช่วงค่าของตัวแปร ขณะที่ SHAP แจกแจงส่วนต่างจาก background จึงไม่ควรเทียบเครื่องหมายราวกับเป็นคำถามเดียวกัน'))
''')
    md('''## 9F. ข้อความร่างสำหรับผู้สมัครและแนวทาง HR
ข้อความต่อไปนี้สร้างจากผลจริง แต่ **ยังไม่ได้รับการตรวจโดย HR** และไม่ใช่เหตุผลปฏิเสธงาน
ไม่อ้างว่าผู้สมัครจะได้งานหากเปลี่ยนตัวแปรใด ไม่สมมติช่องทางติดต่อที่ไม่มีอยู่จริง
ก่อนใช้จริงหน่วยงานต้องกำหนดชื่อผู้รับผิดชอบ ช่องทางติดต่อ และระยะเวลาทบทวน
HR ต้องทวนแฟ้มคะแนนต่ำด้วยเพื่อลดการเสียโอกาสเมื่อคิวมีจำกัด''')
    code('''candidate_drafts=[]
for case in cases:
    phi=np.array(case['phi']); order=np.argsort(-abs(phi))[:2]
    parts=[]
    for j in order:
        direction='เพิ่ม' if phi[j]>=0 else 'ลด'
        parts.append(f"{features[j]} (ค่าที่บันทึก {case['inputs'][features[j]]}) {direction}คะแนนประมาณ {abs(phi[j])*100:.1f} จุดเปอร์เซ็นต์")
    draft=(f"### ร่างสำหรับ HR ตรวจ — แถว CSV {case['row']} ({case['type']})\\n"
           'ระบบทดลองใช้ข้อมูลหลังสัมภาษณ์เพื่อช่วยจัดลำดับแฟ้มให้เจ้าหน้าที่ทบทวน ไม่ใช่การตัดสินรับหรือปฏิเสธงาน '
           + 'เมื่อเทียบกับกลุ่มอ้างอิงในข้อมูลฝึก ปัจจัยเด่นคือ '+ '; '.join(parts)+'. '
           'โปรดตรวจว่าระดับการศึกษา ประสบการณ์ และคะแนนที่บันทึกถูกต้อง หากต้องการแก้ไขหรือขอทบทวน '
           'ให้ติดต่อผู้รับผิดชอบการสรรหาผ่านช่องทางที่หน่วยงานประกาศ (ต้องกำหนดก่อนใช้งานจริง). '
           'คำอธิบายนี้สะท้อนรูปแบบในข้อมูลสังเคราะห์ ไม่ใช่ข้อสรุปเกี่ยวกับความสามารถจริงของผู้สมัคร')
    candidate_drafts.append(draft); display(Markdown(draft))
display(Markdown('**ข้อจำกัดก่อนใช้งาน:** ต้องยืนยันเวลาเก็บตัวแปรก่อนจุดตัด ตรวจเกณฑ์ฉลากกับ HR '
                 'ตรวจด้วยข้อมูลจริงที่ได้รับอนุญาต และกำหนดกำลังคน/เวลาสำหรับทบทวนแฟ้ม '
                 'ผลการทดลองและความเป็นธรรมในข้อมูลสังเคราะห์ไม่รับประกันผลในงานจริง'))
''')
