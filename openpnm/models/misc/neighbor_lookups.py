r"""

.. autofunction:: openpnm.models.misc.neighbor_lookups.from_neighbor_throats
.. autofunction:: openpnm.models.misc.neighbor_lookups.from_neighbor_pores

"""

import numpy as np
from openpnm.utils import logging
logger = logging.getLogger(__name__)


def from_neighbor_throats(target, prop=None, throat_prop='pore.seed',
                          mode='min', ignore_nans=True):
    r"""
    Adopt a value from the values found in neighboring throats

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.
    prop : string
        The dictionary key of the array containing the throat property to be
        used in the calculation.  The default is 'throat.seed'.
    throat_prop : string
        Same as ``prop``, but will be deprecated.
    mode : string
        Controls how the pore property is calculated.  Options are 'min',
        'max' and 'mean'.

    Returns
    -------
    value : ND-array
        Array containing customized values based on those of adjacent throats.

    """
    prj = target.project
    network = prj.network
    boss = prj.find_full_domain(target)
    if prop is not None:
        throat_prop = prop
    data = boss[throat_prop]
    # This functionality needs to be removed since masked arrays don't seem
    # to support the 'at' method, which is essential for speed.
    # if ignore_nans:
    #     data = np.ma.MaskedArray(data=data, mask=np.isnan(data))
    im = network.create_incidence_matrix()
    if mode == 'min':
        values = np.ones((network.Np, ))*np.inf
        np.minimum.at(values, im.row, data[im.col])
    if mode == 'max':
        values = np.ones((network.Np, ))*-np.inf
        np.maximum.at(values, im.row, data[im.col])
    if mode == 'mean':
        values = np.zeros((network.Np, ))
        np.add.at(values, im.row, data[im.col])
        counts = np.zeros((network.Np, ))
        np.add.at(counts, im.row, np.ones((network.Nt, ))[im.col])
        values = values/counts
    Ps = boss.map_pores(target.pores(), target)
    return np.array(values)[Ps]


def from_neighbor_pores(target, prop=None, pore_prop='pore.seed', mode='min',
                        ignore_nans=True):
    r"""
    Adopt a value based on the values in neighboring pores

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.
    prop : string
        The dictionary key to the array containing the pore property to be
        used in the calculation.  Default is 'pore.seed'.
    pore_prop : string
        Same as ``prop`` but will be deprecated.
    mode : string
        Controls how the throat property is calculated.  Options are 'min',
        'max' and 'mean'.
    ignore_nans : boolean (default is ``True``)
        If ``True`` the result will ignore ``nans`` in the neighbors

    Returns
    -------
    value : ND-array
        Array containing customized values based on those of adjacent pores.

    """
    prj = target.project
    lookup = prj.find_full_domain(target)
    network = prj.network
    throats = network.map_throats(target.throats(), target)
    P12 = network.find_connected_pores(throats)
    if prop is not None:
        pore_prop = prop
    pvalues = lookup[pore_prop][P12]
    if ignore_nans:
        pvalues = np.ma.MaskedArray(data=pvalues, mask=np.isnan(pvalues))
    try:  # If pvalues is not empty
        if mode == 'min':
            value = np.amin(pvalues, axis=1)
        if mode == 'max':
            value = np.amax(pvalues, axis=1)
        if mode == 'mean':
            value = np.mean(pvalues, axis=1)
    except np.AxisError:  # Handle case of empty pvalues
        value = []
    return np.array(value)
