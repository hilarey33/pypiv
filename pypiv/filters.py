import numpy as np

from numpy.lib.stride_tricks import as_strided
from scipy.ndimage import median_filter
from scipy.interpolate import CloughTocher2DInterpolator as CT_intp

from skimage.filters.rank import median
from skimage.morphology import disk
from scipy.ndimage import median_filter as mf

def median_filter(piv, size=2):
    """Computes a median filter on u and v"""
    piv.u = mf(piv.u, footprint=disk(size))
    piv.v = mf(piv.v, footprint=disk(size))

def replace_outliers(piv):
    """Replaces the detected outliers according to the mask"""
    mask = np.isnan(piv.u) + np.isnan(piv.v)
    piv.u = replace_field(piv.u, mask)
    piv.v = replace_field(piv.v, mask)

def replace_field(f, mask):
    """Interpolates positions in field according to mask with a 2D cubic interpolator"""
    lx, ly = f.shape
    x, y = np.mgrid[0:lx, 0:ly]
    C = CT_intp((x[~mask],y[~mask]),f[~mask], fill_value=0)
    return C(x, y)

def outlier_from_local_median(piv, treshold=2.0):
    """Outlier detection algorithm for mask creation.

    The calculated residual is compared to a threshold which produces a mask.
    The mask consists of nan values at the outlier positions.
    This mask can be interpolated to remove the outliers.

    :param object piv: Piv Class Object
    :param double threshold: threshold for identifying outliers

    """
    u_res = get_normalized_residual(piv.u)
    v_res = get_normalized_residual(piv.v)
    res_total = np.sqrt(u_res**2 + v_res**2)
    mask =  res_total > treshold
    piv.u[mask] = np.nan
    piv.v[mask] = np.nan

def get_normalized_residual(f, epsilon=0.1):
    """
    Compute Residual for a Flow field

    Implementation of a local median filter according to
    "J. Westerweel, F. Scarano, Universalo outlier detection for PIV data,
    Experiments in Fluids, 2005"


    :param f: field
    :param double epsilon: small tolerance value
    :returns: calculated residual for field
    """
    lx, ly = f.shape
    fn = np.pad(f, (1, 1), 'edge')

    uis     = np.zeros((lx*ly, 8))
    um, rm  = np.zeros((lx*ly)), np.zeros((lx*ly))

    mapping = [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)]
    for i, (k, l) in enumerate(mapping):
        uis[:, i] = np.copy(fn[k:k+lx, l:l+ly]).flatten()

    uis = np.sort(uis, 1)
    um  = np.copy(np.mean(uis[:, 3:5], axis=1))[:, np.newaxis]

    ris = np.abs(uis - um)
    rm  = np.sort(ris, 1)
    rm = np.copy(np.mean(rm[:, 3:5], axis=1))[:, np.newaxis]

    return np.abs((f - um.reshape((lx, ly)))/(rm.reshape((lx, ly)) + epsilon))
