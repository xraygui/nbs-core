import collections


def iterfy(x):
    """
    This function guarantees that a parameter passed will act like a list (or tuple) for the purposes of iteration,
    while treating a string as a single item in a list.

    Parameters
    ----------
    x : Any
        The input parameter to be iterfied.

    Returns
    -------
    Iterable
        The input parameter as an iterable.
    """
    if isinstance(x, collections.abc.Iterable) and not isinstance(x, (str, bytes)):
        return x
    else:
        return [x]
