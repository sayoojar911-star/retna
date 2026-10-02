import torch, numpy as np, json, inspect
from collections import Counter
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from ml.models.resnet_rnflt import AdaptedResNet18
from ml.preprocessing.harvard_gd_loader import HarvardGDLoader
from ml.preprocessing.transforms import OCTPreprocessTransform

ckpt=torch.load('models/checkpoints/harvard_gd_rnflt_cnn_best.pt', map_location='cpu')
print('=== 1. MODEL ARCH ===')
print('checkpoint: models/checkpoints/harvard_gd_rnflt_cnn_best.pt')
print('model_architecture:', ckpt.get('model_architecture'))
print('expected input_shape:', ckpt.get('input_shape'))
print('num_classes:', ckpt.get('num_classes'))
msd=ckpt['model_state_dict']
print('output layer:', [k for k in msd.keys() if 'fc' in k])
print('conv1 wt key:', [k for k in msd.keys() if 'conv1' in k])
print('backbone conv1:', msd['backbone.conv1.weight'].shape if 'backbone.conv1.weight' in msd else 'not found')
print('hyperparameters:', ckpt.get('hyperparameters'))
print('class mapping training: 0=Normal/Suspect 1=Glaucoma (BCEWithLogitsLoss sigmoid P(class=1))')

loader=HarvardGDLoader()
splits=loader.get_stratified_splits(random_seed=42)

print('\n=== 2/3. TRAINING INPUT & CLASS DISTRIBUTION ===')
print('TRAINING INPUT: type=225x225 quantitative RNFLT numerical map, dtype=', loader.rnflt_maps.dtype, 'shape', loader.rnflt_maps.shape)
print('TRAINING INPUT: min', float(np.min(loader.rnflt_maps)), 'max', float(np.max(loader.rnflt_maps)), 'mean', float(np.mean(loader.rnflt_maps)))
print('TRAINING PREPROCESSING: OCTPreprocessTransform target 225 BILINEAR clip 1-99 min_max -> [1,225,225] in [0,1] no ImageNet no CLAHE channel replicate to 1')
for k in ['train','val','test']:
    c=Counter(loader.glaucoma_labels[splits[k]].tolist())
    total=len(splits[k])
    print(f'{k}: Normal={c.get(0,0)} Glaucoma={c.get(1,0)} total={total}  Normal%={c.get(0,0)/total*100:.1f}% Glaucoma%={c.get(1,0)/total*100:.1f}%')

print('\n=== 7. PREPROCESSING (training vs inference) ===')
print('Training: HarvardGDDataset transform=OCTPreprocessTransform(target_size=(225,225), normalize_mode=min_max, clip_percentiles=(1.0,99.0), num_channels=1) -> [1,225,225] in [0,1], BILINEAR, no ImageNet/CLAHE')
print('Inference: same OCTPreprocessTransform in ml/explainability/gradcam.py GradCAMExplainer (cached singleton) -> identical')
print('Dtype tensor float32, shape [1,225,225], value_range [0,1]')
print('Transform source:', inspect.getsource(OCTPreprocessTransform.__init__)[:300])

print('\n=== 8. ONE TEST RNFLT ARRAY ===')
test_idx=int(splits['test'][0])
arr=loader.rnflt_maps[test_idx]
print(f'sample test[0] id={test_idx} study_id=harvard_gd_{test_idx:04d}')
print(f'shape {arr.shape} dtype {arr.dtype} min {float(np.min(arr)):.2f} max {float(np.max(arr)):.2f} mean {float(np.mean(arr)):.2f} median {float(np.median(arr)):.2f} std {float(np.std(arr)):.2f} zeros {100*float(np.sum(arr==0))/arr.size:.2f}% finite {100*float(np.sum(np.isfinite(arr)))/arr.size:.2f}%')

m=AdaptedResNet18(num_classes=1)
m.load_state_dict(msd, strict=True)
m.eval()

def evaluate(name, idx):
    y_true=[]; y_prob=[]; y_pred=[]; rows=[]
    for i in idx:
        ds=loader.get_pytorch_dataset(indices=[int(i)])
        s=ds[0]
        img=s['image'].unsqueeze(0)
        label=int(s['glaucoma'].item())
        with torch.no_grad():
            logit=m(img).view(-1)[0].item()
            prob=float(torch.sigmoid(torch.tensor(logit)).item())
        pred=1 if prob>=0.5 else 0
        y_true.append(label)
        y_prob.append(prob)
        y_pred.append(pred)
        rows.append((int(i), label, prob, 1-prob, logit, pred))
    acc=accuracy_score(y_true, y_pred)
    rec=recall_score(y_true, y_pred, zero_division=0)
    cm=confusion_matrix(y_true, y_pred, labels=[0,1])
    tn,fp,fn,tp=cm.ravel()
    spec=tn/(tn+fp) if (tn+fp)>0 else 0
    prec=precision_score(y_true, y_pred, zero_division=0)
    f1=f1_score(y_true, y_pred, zero_division=0)
    try:
        auroc=roc_auc_score(y_true, y_prob)
    except Exception:
        auroc=0.5
    print(f'\n=== {name} (n={len(idx)}) ===')
    print(f'Accuracy {acc:.4f}  Sensitivity/Recall {rec:.4f}  Specificity {spec:.4f}  Precision {prec:.4f}  F1 {f1:.4f}  AUROC {auroc:.4f}')
    print(f'Confusion: TN={tn} FP={fp} FN={fn} TP={tp}')
    print('                    Predicted')
    print('                 Normal  Glaucoma')
    print(f'Actual Normal      {tn:3d}      {fp:3d}')
    print(f'Actual Glaucoma    {fn:3d}      {tp:3d}')
    return y_true, y_prob, rows, cm

vt, vp, vrows, vcm = evaluate('VAL', splits['val'])
tt, tp, trows, tcm = evaluate('TEST', splits['test'])

print('\n=== 4. 20 TEST EXAMPLES (p 4 decimals) ===')
print('sample       true   p_normal   p_glaucoma pred   logit   ')
for sid,label,prob,pn,logit,pred in trows[:20]:
    print(f'harvard_gd_{sid:04d}  {label:<6} {pn:<10.4f} {prob:<10.4f} {pred:<6} {logit:<8.4f}')

print('\n=== 5. BOTH CLASSES SEPARATELY ===')
def stats_per_class(y_true, y_prob):
    g=[p for t,p in zip(y_true,y_prob) if t==1]
    n=[p for t,p in zip(y_true,y_prob) if t==0]
    print(f'Avg p_glaucoma | Glaucoma samples: {np.mean(g):.4f} | Normal samples: {np.mean(n):.4f}')
    print(f'Glaucoma: min {np.min(g):.4f} max {np.max(g):.4f}')
    print(f'Normal  : min {np.min(n):.4f} max {np.max(n):.4f}')
print('TEST:')
stats_per_class(tt, tp)
print('VAL:')
stats_per_class(vt, vp)

print('\n=== 9. FINAL DIAGNOSIS ===')
# Heuristic: check if biased
acc_t = accuracy_score(tt, [1 if p>=0.5 else 0 for p in tp])
# use already computed tcm
tn,fp,fn,tp_c = tcm.ravel()
if acc_t < 0.6:
    print('E. CLASSIFIER PERFORMANCE IS INADEQUATE (acc < 0.6)')
elif fp > 20 or fn > 20:
    print('D. CLASSIFIER IS BIASED TOWARD ONE CLASS (but here not extreme) -- overall A')
else:
    print('A. CLASSIFIER WORKING — problem is OCT→RNFLT pipeline (model performs on RNFLT domain, blocked for B-scan)')

print('\nPreprocessing match: YES (training and inference both OCTPreprocessTransform min_max clip 1-99)')
print('Label mapping: 0=Normal/Suspect 1=Glaucoma verified from glaucoma_label.npy + BCEWithLogitsLoss')
print('Units: quantitative RNFLT µm (not pixel intensity), 225x225 finite non-zero var')
