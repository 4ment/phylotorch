import numpy as np
import pytest
import torch

from phylotorch.substmodel import JC69, HKY, GTR

# r=c(0.060602,0.402732,0.028230,0.047910,0.407249,0.053277)
# f=c(0.479367,0.172572,0.140933,0.207128)
# R=matrix(c(0,r[1],r[2],r[3],
#        r[1],0,r[4],r[5],
#        r[2],r[4],0,r[6],
#        r[3],r[5],r[6],0),nrow=4)
# Q=R %*% diag(f,4,4)
# diag(Q)=-apply(Q, 1, sum)
# Q=-Q/sum(diag(Q)*f)
# e=eigen(Q)
# e$vectors %*% diag(exp(e$values*0.1)) %*% solve(e$vectors)


def test_GTR():
    rates = torch.tensor(np.array([0.060602, 0.402732, 0.028230, 0.047910, 0.407249, 0.053277]))
    pi = torch.tensor(np.array([0.479367, 0.172572, 0.140933, 0.207128]))
    subst_model = GTR(('rates', rates), ('pi', pi))
    P = subst_model.p_t(torch.tensor(np.array([[0.1]])))
    P_expected = np.array(
        [[0.93717830, 0.009506685, 0.047505899, 0.005809115],
         [0.02640748, 0.894078744, 0.006448058, 0.073065722],
         [0.16158572, 0.007895626, 0.820605951, 0.009912704],
         [0.01344433, 0.060875872, 0.006744752, 0.918935042]])
    np.testing.assert_allclose(P.squeeze(), P_expected, rtol=1e-06)


def test_HKY():
    # r=c(1,3,1,1,3,1)
    kappa = torch.tensor(np.array([3.]))
    pi = torch.tensor(np.array([0.479367, 0.172572, 0.140933, 0.207128]))
    subst_model = HKY(('kappa', kappa), ('pi', pi))
    P = subst_model.p_t(torch.tensor(np.array([[0.1], [0.001]])))
    P_expected = np.array([[
        [0.93211187, 0.01511617, 0.03462891, 0.01814305],
        [0.04198939, 0.89405292, 0.01234480, 0.05161289],
        [0.11778615, 0.01511617, 0.84895463, 0.01814305],
        [0.04198939, 0.04300210, 0.01234480, 0.90266370]],
        [
        [0.9992649548, 0.0001581235, 0.0003871353, 0.0001897863],
        [0.0004392323, 0.9988625812, 0.0001291335, 0.0005690531],
        [0.0013167952, 0.0001581235, 0.9983352949, 0.0001897863],
        [0.0004392323, 0.0004741156, 0.0001291335, 0.9989575186]]])
    print(P.squeeze())
    print(P_expected)
    np.testing.assert_allclose(P.squeeze(), P_expected, rtol=1e-06)

    P = super(HKY, subst_model).p_t(torch.tensor(np.array([[0.1], [0.001]])))
    np.testing.assert_allclose(P.squeeze(), P_expected, rtol=1e-06)


@pytest.mark.parametrize("t", [0.001, 0.1])
def test_JC69(t):
    ii = 1. / 4. + 3. / 4. * np.exp(- 4. / 3. * t)
    ij = 1./4. - 1./4. * np.exp(- 4./3. * t)
    subst_model = JC69()
    P = torch.squeeze(subst_model.p_t(torch.tensor(np.array([t]))))
    assert ii == pytest.approx(P[0, 0].item(), 1.0e-6)
    assert ij == pytest.approx(P[0, 1].item(), 1.0e-6)
