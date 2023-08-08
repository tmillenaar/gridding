import inspect
import operator
from typing import Union

import numpy


class _IndexMeta(type):
    """Metaclass for GridIndex which implements the basic operators"""

    def __new__(cls, name, bases, namespace):
        # numpys with a nan-base
        def normal_op(op):
            return lambda l, r: GridIndex(op(l.index.astype(float), r))

        def reverse_op(op):
            return lambda l, r: GridIndex(op(r, l.index.astype(float)))

        for op, name_ in (
            (numpy.add, "add"),
            (numpy.subtract, "sub"),
            (numpy.multiply, "mul"),
            (numpy.true_divide, "truediv"),
            (numpy.floor_divide, "floordiv"),
            (numpy.power, "pow"),
            (numpy.mod, "mod"),
            (numpy.greater_equal, "ge"),
            (numpy.less_equal, "le"),
            (numpy.greater, "gt"),
            (numpy.less, "lt"),
            (numpy.equal, "eq"),
            (numpy.not_equal, "ne"),
        ):
            opname = "__{}__".format(name_)
            opname_reversed = "__r{}__".format(name_)
            namespace[opname] = normal_op(op)
            namespace[opname_reversed] = reverse_op(op)
        return super().__new__(cls, name, bases, namespace)


class GridIndex(metaclass=_IndexMeta):
    """Index to be used with grid classes.
    These GridIndex class instances contain the references to the grid cells by ID (idx, idy).
    Several methods are implemented to treat the indices as sets, where one (idx, idy) pair is considered one unit, one cell-ID.
    The GridIndex class also allows for generic operators such as: (+, -, *, /, //, **, %, >=, <=, >, <)

    Parameters
    ----------
    index: Union[numpy.ndarray, list, tuple, GridIndex]
        The index containing the cell-id.
        This is assumed to either be a single (idx, idy) pair or a list, tuple or ndarray containing multiple of such pairs.

    Raises
    ------
    ValueError
        When the shape of the index does not match the expected shape of (2,) or (N,2) where N is the number of cells, a ValuError is raised.
    """

    def __init__(self, index):
        self.index = numpy.array(index, dtype=int)

        if self.index.shape == (2,):
            self.index = self.index[numpy.newaxis]

    def __len__(self):
        """The number of indices"""
        return len(self._1d_view)

    def __iter__(self):
        self._iter_id = 0
        return self

    def __next__(self):
        if self._iter_id == len(self.index):
            raise StopIteration
        id = GridIndex(self.index[self._iter_id])
        self._iter_id += 1
        return id

    def __getitem__(self, item):
        return self.index[item]

    @property
    def x(self):
        """The X-component of the cell-IDs"""
        return self.index[..., 0]

    @x.setter
    def x(self, value):
        self.index[..., 0] = value
        return self

    @property
    def y(self):
        """The Y-component of the cell-IDs"""
        return self.index[..., 1]

    @y.setter
    def y(self, value):
        self.index[..., 1] = value
        return self

    def unique(self, **kwargs):
        """The unique IDs contained in the index. Remove duplicate IDs.

        Parameters
        ----------
        **kwargs:
            The keyword arguments to pass to numpy.unique
        """
        if kwargs:
            # kwargs to numpy.unique can result in multiple return arguments, return these too
            unique, *other = numpy.unique(self._1d_view, axis=0, **kwargs)
            return _nd_view(unique), *other
        unique = numpy.unique(self._1d_view, axis=0, **kwargs)
        return _nd_view(unique)

    def intersection(self, other):
        """The intersection of two GridIndex instances. Keep the IDs contained in both.

        Parameters
        ----------
        **other:
            The GridIndex instance to compare with
        """
        if not isinstance(other, GridIndex):
            other = GridIndex(other)
        intersection = numpy.intersect1d(self._1d_view, other._1d_view)
        return _nd_view(intersection)

    def difference(self, other):
        """The differenceof two GridIndex instances. Keep the IDs contained in ``self`` that are not in ``other``.

        Parameters
        ----------
        **other:
            The GridIndex instance to compare with
        """
        if not isinstance(other, GridIndex):
            other = GridIndex(other)
        difference = numpy.setdiff1d(self._1d_view, other._1d_view)
        return _nd_view(difference)

    def isdisjoint(self, other):
        """True if none of the IDs in ``self`` are in ``other``. False if any ID in ``self`` is also in ``other``.

        Parameters
        ----------
        **other:
            The GridIndex instance to compare with
        """
        return ~numpy.isin(self._1d_view, other._1d_view).any()

    def issubset(self, other):
        """True if all of the IDs in ``self`` are in ``other``. False if not all IDs in ``self`` is also in ``other``.

        Parameters
        ----------
        **other:
            The GridIndex instance to compare with
        """
        return numpy.isin(self._1d_view, other._1d_view).all()

    def issuperset(self, other):
        """True if all of the IDs in ``other`` are in ``self``. False if not all IDs in ``other`` is also in ``self``.

        Parameters
        ----------
        **other:
            The GridIndex instance to compare with
        """
        return numpy.isin(other._1d_view, self._1d_view).all()

    def __array__(self, dtype=None):
        return self.index

    @property
    def _1d_view(self):
        """Create a structured array where each (x,y) pair is seen as a single entitiy"""
        raveled_index = self.index.reshape((-1, 2))
        formats = (
            numpy.full(len(raveled_index), raveled_index.dtype)
            if raveled_index.shape[0] > 1
            else 2 * [raveled_index.dtype]
        )
        dtype = {"names": ["f0", "f1"], "formats": formats}
        if raveled_index.flags["F_CONTIGUOUS"]:  # https://stackoverflow.com/a/63196035
            raveled_index = numpy.require(raveled_index, requirements=["C"])
        return raveled_index.view(dtype)

    def copy(self):
        """Return an immutable copy of self."""
        return GridIndex(self.index.copy())


def _nd_view(index):
    """Turn 1d-view into ndarray"""
    if index.shape[0] == 0:  # return index if empty
        return index
    return index.view(int).reshape(-1, 2)


def validate_index(func):
    """Decorator to convert the index argument of a function to a GridIndex object."""

    def wrapper(*args, **kwargs):
        """Inner function to convert the index argument to a GridIndex object.

        Parameters
        ----------
        index: Union[numpy.ndarray, list, tuple, GridIndex]
            The index referring to the grid IDs
        *args:
            The arguments to be passed to the wrapped function
        *kwargs:
            The keyword arguments to be passed to the wrapped function
        """
        arg_names = inspect.signature(func).parameters
        new_args = []
        for key, value in zip(arg_names, args):
            if key == "index" and value is not None:
                value = GridIndex(value)
            new_args.append(value)
        new_kwargs = {}
        for key, value in kwargs.items():
            if key == "index" and value is not None:
                value = GridIndex(value)
            new_kwargs[key] = value

        return func(*new_args, **new_kwargs)

    return wrapper
