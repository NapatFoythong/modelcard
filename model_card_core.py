from pathlib import Path
from math import factorial
import hashlib
import json
import sys
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_curve
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

root = Path(__file__).resolve().parent
source = Path(sys.argv[1]) if len(sys.argv)>1 else root/'recruitment_data_cleaned.csv'
seed = 42
data = pd.read_csv(source)
raw = data.copy()
# Sensitive attributes are reserved for auditing; do not use Age to alter features.
features = ['EducationLevel','ExperienceYears','InterviewScore','SkillScore']
X, y = data[features], data.HiringDecision
numeric = features[1:]
names = ['Dummy','Logistic Regression','Gradient Boosting']
params = [{},{'model__C':[0.1,1,10]},{'model__max_depth':[1,2,3], 'model__n_estimators':[50,100]}]
def pipeline(i):
    steps = [SimpleImputer(strategy='median')]
    if i == 1:
        steps.append(StandardScaler())
    prep = ColumnTransformer([('education',OneHotEncoder(handle_unknown='ignore',sparse_output=False),[features[0]]),('numeric',make_pipeline(*steps),numeric)])
    model = [DummyClassifier(strategy='prior'),LogisticRegression(max_iter=1000),GradientBoostingClassifier(random_state=seed,learning_rate=.1)][i]
    return Pipeline([('prep',prep),('model',model)])
def threshold(y, p):
    fpr,tpr,cut=roc_curve(y,p,drop_intermediate=False)
    eligible=np.flatnonzero(tpr>=.9)
    return float(cut[eligible[np.argmin(fpr[eligible])]])
def summary(y,p,decision):
    y=np.asarray(y); d=np.asarray(decision)
    tp=int(sum((y==1)&d)); fp=int(sum((y==0)&d))
    fn=int(sum((y==1)&~d)); tn=int(sum((y==0)&~d))
    return dict(n=len(y),tp=tp,fp=fp,fn=fn,tn=tn,ap=float(average_precision_score(y,p)),brier=float(brier_score_loss(y,p)))
def shap_values(model, row, bg):
    k=len(features)
    values=[]
    for mask in range(1<<k):
        matrix=bg.copy()
        for j,feature in enumerate(features):
            if mask & (1<<j):
                matrix[feature]=row[feature]
        values.append(model.predict_proba(matrix)[:,1].mean())
    effects=np.zeros(k)
    for mask in range(1<<k):
        size=mask.bit_count()
        for j in range(k):
            if not mask & (1<<j):
                effects[j]+=factorial(size)*factorial(k-size-1)/factorial(k)*(values[mask | (1<<j)]-values[mask])
    return float(values[0]),effects

pred=np.zeros((len(data),4))
dec=np.zeros((len(data),4),dtype=bool)
records=[]; splits=[]; pfi=[]; fitted=[]
outer=StratifiedKFold(5,shuffle=True,random_state=seed)
for fold,(tr,te) in enumerate(outer.split(X,y),1):
    inner=StratifiedKFold(4,shuffle=True,random_state=seed+fold)
    candidates=[]; detail=[]
    for i in range(3):
        search=GridSearchCV(pipeline(i),params[i],scoring='average_precision',cv=inner)
        search.fit(X.iloc[tr],y.iloc[tr])
        model=search.best_estimator_
        inner_prob=cross_val_predict(model,X.iloc[tr],y.iloc[tr],cv=inner,method='predict_proba')[:,1]
        # Dummy has one constant score for each fitted model, so its threshold flags all.
        cut=threshold(y.iloc[tr],inner_prob) if i else float(model.named_steps['model'].class_prior_[1])
        prob=model.predict_proba(X.iloc[te])[:,1]
        pred[te,i]=prob; dec[te,i]=prob>=cut
        candidates.append(model)
        detail.append(dict(name=names[i],params=search.best_params_,cut=cut,inner_ap=float(search.best_score_)))
    chosen=2 if detail[2]['inner_ap']-detail[1]['inner_ap']>.01 else 1
    model=candidates[chosen]
    pred[te,3]=pred[te,chosen]; dec[te,3]=dec[te,chosen]
    importance=permutation_importance(model,X.iloc[te],y.iloc[te],scoring='average_precision',n_repeats=25,random_state=seed+fold)
    pfi.append(importance.importances)
    fitted.append((model,tr,te,detail[chosen]['cut']))
    splits.append(dict(fold=fold,train=len(tr),test=len(te),chosen=names[chosen],models=detail))
    for j in te:
        records.append(dict(row=int(j+2),fold=fold,y=int(y.iloc[j]),age=int(data.Age.iloc[j]),gender=int(data.Gender.iloc[j]),**{f'prob_{i}':pred[j,i] for i in range(4)},**{f'decision_{i}':int(dec[j,i]) for i in range(4)}))

cases=[]
for want in ('FN','FP'):
    hits=[]
    for fold,(model,tr,te,cut) in enumerate(fitted,1):
        for j in te:
            if (want=='FN' and y.iloc[j]==1 and not dec[j,3]) or (want=='FP' and y.iloc[j]==0 and dec[j,3]):
                hits.append((abs(pred[j,3]-cut),int(j),fold))
    if not hits:
        raise RuntimeError('Expected at least one '+want)
    _,j,fold=min(hits)
    model,tr,te,cut=fitted[fold-1]
    bg=X.iloc[tr]
    base,phi=shap_values(model,X.iloc[j],bg)
    replicas=np.array([shap_values(model,X.iloc[j],bg.sample(n=100,random_state=seed+n))[1] for n in range(10)])
    residual=abs(base+phi.sum()-pred[j,3])
    assert residual<1e-10
    cases.append(dict(type=want,row=j+2,fold=fold,cut=cut,p=float(pred[j,3]),base=base,phi=phi.tolist(),residual=float(residual),top_same=int(sum(np.argmax(abs(replicas),axis=1)==np.argmax(abs(phi)))),replica_sd=replicas.std(axis=0,ddof=1).tolist(),inputs={k:None if pd.isna(v) else float(v) for k,v in X.iloc[j].items()}))

groups={}
for label,mask in [('Gender 0',data.Gender==0),('Gender 1',data.Gender==1),('20–29',data.Age.between(20,29)),('30–39',data.Age.between(30,39)),('40–50',data.Age.between(40,50))]:
    groups[label]=summary(y[mask],pred[mask,3],dec[mask,3])
pfi=np.concatenate(pfi,axis=1)
result=dict(sklearn=sklearn.__version__,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),n=len(data),positive=int(y.sum()),missing=int(data.ExperienceYears.isna().sum()),splits=splits,metrics={name:summary(y,pred[:,i],dec[:,i]) for i,name in enumerate(names+['Selected'])},groups=groups,pfi_mean=pfi.mean(axis=1).tolist(),pfi_sd=pfi.std(axis=1,ddof=1).tolist(),features=features,cases=cases)
(root/'model_card_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
pd.DataFrame(records).sort_values('row').to_csv(root/'model_card_predictions.csv',index=False)
print(json.dumps(result,ensure_ascii=False))
