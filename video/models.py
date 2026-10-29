"""Three ways to combine the feature blocks into a trending probability.

linear   class-weighted logistic regression on full-resolution blocks (early fusion by concatenation),
         C chosen by 3-fold cross-validation on the training rows. This is the Passioné v2 baseline.
boosting histogram gradient-boosted trees on compact blocks (PCA/SVD), early stopping on an inner validation
         split. Captures non-linear interactions between modalities.
fusion   a small PyTorch network: one encoder per modality, then a shared head (intermediate fusion), with
         modality dropout so it cannot lean on a single input. Early stopping on inner validation ROC-AUC.
"""

import numpy as np
import torch
from scipy.sparse import csr_matrix, hstack, issparse
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, train_test_split

from common import Blocks

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def _stack(blocks: dict) -> np.ndarray | csr_matrix:
    parts = [blocks[k] for k in sorted(blocks)]
    if any(issparse(p) for p in parts):
        return hstack([p if issparse(p) else csr_matrix(p) for p in parts]).tocsr()
    return np.hstack(parts)


def linear(b: Blocks, y_tr: np.ndarray, seed: int) -> np.ndarray:
    search = GridSearchCV(
        LogisticRegression(max_iter=3000, class_weight="balanced"),
        {"C": [0.1, 0.3, 1.0, 3.0]},
        scoring="roc_auc",
        cv=3,
        n_jobs=4,  # each worker copies the data; more would strain 8 GB of RAM
    ).fit(_stack(b.train), y_tr)
    return search.predict_proba(_stack(b.test))[:, 1]


def boosting(b: Blocks, y_tr: np.ndarray, seed: int, learning_rate: float = 0.05, max_leaf_nodes: int = 31,
             l2_regularization: float = 1.0) -> np.ndarray:
    model = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_iter=1500,
        max_leaf_nodes=max_leaf_nodes,
        l2_regularization=l2_regularization,
        class_weight="balanced",
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=30,
        scoring="roc_auc",
        random_state=seed,
    )
    return model.fit(_stack(b.train), y_tr).predict_proba(_stack(b.test))[:, 1]


class FusionNet(torch.nn.Module):
    def __init__(self, widths: dict[str, int], hidden: int = 128, p_drop: float = 0.3, p_modality: float = 0.2):
        super().__init__()
        self.names = sorted(widths)
        self.p_modality = p_modality
        self.encoders = torch.nn.ModuleDict({
            n: torch.nn.Sequential(torch.nn.Linear(widths[n], hidden), torch.nn.GELU(), torch.nn.Dropout(p_drop))
            for n in self.names
        })
        self.head = torch.nn.Sequential(
            torch.nn.Linear(hidden * len(self.names), hidden), torch.nn.GELU(), torch.nn.Dropout(p_drop),
            torch.nn.Linear(hidden, 1),
        )

    def forward(self, xs: dict[str, torch.Tensor]) -> torch.Tensor:
        parts = []
        for n in self.names:
            h = self.encoders[n](xs[n])
            if self.training and len(self.names) > 1:  # modality dropout: sometimes hide a whole input
                keep = (torch.rand(h.shape[0], 1, device=h.device) > self.p_modality).float()
                h = h * keep
            parts.append(h)
        return self.head(torch.cat(parts, dim=1)).squeeze(1)


def fusion(b: Blocks, y_tr: np.ndarray, seed: int, hidden: int = 128, lr: float = 1e-3, p_drop: float = 0.3,
           weight_decay: float = 1e-2, epochs: int = 120, patience: int = 15) -> np.ndarray:
    torch.manual_seed(seed)
    idx_fit, idx_val = train_test_split(np.arange(len(y_tr)), test_size=0.15, stratify=y_tr, random_state=seed)
    to = lambda m, rows: torch.tensor(m[rows], dtype=torch.float32, device=DEVICE)
    fit = {n: to(m, idx_fit) for n, m in b.train.items()}
    val = {n: to(m, idx_val) for n, m in b.train.items()}
    test = {n: torch.tensor(m, dtype=torch.float32, device=DEVICE) for n, m in b.test.items()}
    y_fit = torch.tensor(y_tr[idx_fit], dtype=torch.float32, device=DEVICE)

    net = FusionNet({n: m.shape[1] for n, m in b.train.items()}, hidden=hidden, p_drop=p_drop).to(DEVICE)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=weight_decay)
    pos_weight = torch.tensor(float((1 - y_tr.mean()) / y_tr.mean()), dtype=torch.float32, device=DEVICE)  # = class_weight
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    gen = torch.Generator().manual_seed(seed)

    best, best_state, waited = -1.0, None, 0
    for _ in range(epochs):
        net.train()
        for batch in torch.randperm(len(idx_fit), generator=gen).split(256):
            batch = batch.to(DEVICE)
            opt.zero_grad()
            loss_fn(net({n: x[batch] for n, x in fit.items()}), y_fit[batch]).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            auc = roc_auc_score(y_tr[idx_val], net(val).cpu().numpy())
        if auc > best + 1e-4:
            best, waited = auc, 0
            best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
        else:
            waited += 1
            if waited >= patience:
                break
    net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad():
        return torch.sigmoid(net(test)).cpu().numpy()


MODELS = {"linear": linear, "boosting": boosting, "fusion": fusion}
