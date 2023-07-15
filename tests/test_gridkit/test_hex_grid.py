import numpy
import pytest

from gridkit.hex_grid import BoundedHexGrid, HexGrid


@pytest.mark.parametrize(
    "shape, indices, expected_centroids",
    [
        ["pointy", (-1, -1), [0, -1.29903811]],
        ["pointy", (-1, 1), [0, 3.897114]],
        [
            "pointy",
            [(0, 0), (1, -1), (1, 1)],
            [
                [1.5, 1.29903811],
                [6, -1.29903811],
                [6, 3.89711432],
            ],
        ],
    ],
)
def test_centroid(shape, indices, expected_centroids):
    grid = HexGrid(size=3)
    centroids = grid.centroid(indices)
    numpy.testing.assert_allclose(centroids, expected_centroids)


@pytest.mark.parametrize(
    "shape, bounds, expected_ids, expected_shape",
    [
        ["pointy", (0, -2, 2, 2), [[0, 0], [-1, -1]], (2, 1)],
        ["pointy", (0, -2, 3, 2), [[0, 0], [-1, -1]], (2, 1)],
        ["pointy", (0, 0, 3, 5), [[-1, 1], [0, 0]], (2, 1)],
        [
            "pointy",
            (-2, -2, 2, 2),
            [
                [-1, 0],
                [0, 0],
                [-2, -1],
                [-1, -1],
            ],
            (2, 2),
        ],
        ["pointy", (-2, -2, 3, 2), [[-1, 0], [0, 0], [-2, -1], [-1, -1]], (2, 2)],
        ["pointy", (-2, 0, 2, 5), [[-2, 1], [-1, 1], [-1, 0], [0, 0]], (2, 2)],
        ["pointy", (-2, 0, 3, 5), [[-2, 1], [-1, 1], [-1, 0], [0, 0]], (2, 2)],
        ["flat", (-2, -2, 2, 2), [[-1, -1], [-1, -2], [0, 0], [0, -1]], (2, 2)],
        ["flat", (-2, -2, 2, 3), [[-1, -1], [-1, -2], [0, 0], [0, -1]], (2, 2)],
        ["flat", (0, -2, 5, 2), [[0, 0], [0, -1], [1, -1], [1, -2]], (2, 2)],
        ["flat", (0, -2, 5, 3), [[0, 0], [0, -1], [1, -1], [1, -2]], (2, 2)],
        ["flat", (-2, 0, 2, 2), [[-1, -1], [0, 0]], (2, 1)],
        ["flat", (-2, 0, 2, 3), [[-1, -1], [0, 0]], (2, 1)],
        ["flat", (-2, 2, 2, 5), [[-1, 0], [0, 1]], (2, 1)],
        ["flat", (0, 0, 5, 3), [[0, 0], [1, -1]], (2, 1)],
    ],
)
def test_cells_in_bounds(shape, bounds, expected_ids, expected_shape):
    grid = HexGrid(size=3, shape=shape)
    aligned_bounds = grid.align_bounds(bounds, mode="nearest")
    ids, shape = grid.cells_in_bounds(aligned_bounds)
    numpy.testing.assert_allclose(ids, expected_ids)
    numpy.testing.assert_allclose(shape, expected_shape)


@pytest.mark.parametrize(
    "shape, point, expected_nearby_cells",
    [
        ["pointy", (2.5, 1.5), [(0, 0), (0, 1), (1, 0)]],
        ["pointy", (1.5, 2.16), [(0, 0), (-1, 1), (0, 1)]],
        ["pointy", (0.5, 1.5), [(0, 0), (-1, 0), (-1, 1)]],
        ["pointy", (0.5, 1.0), [(0, 0), (-1, -1), (-1, 0)]],
        ["pointy", (1.5, 0.43), [(0, 0), (0, -1), (-1, -1)]],
        ["pointy", (2.5, 1.0), [(0, 0), (1, 0), (0, -1)]],
        [
            "pointy",
            [(4, 4.1), (3, 4.76), (2, 4.1), (2, 3.6), (3, 3.03), (4, 3.6)],
            [
                [[0, 1], [1, 2], [1, 1]],
                [[0, 1], [0, 2], [1, 2]],
                [[0, 1], [-1, 1], [0, 2]],
                [[0, 1], [0, 0], [-1, 1]],
                [[0, 1], [1, 0], [0, 0]],
                [[0, 1], [1, 1], [1, 0]],
            ],
        ],
        ["flat", (2.5, 1.5), [(0, 0), (1, -1), (1, 0)]],
        ["flat", (2.0, 2.5), [(0, 0), (1, 0), (0, 1)]],
        ["flat", (1.0, 2.5), [(0, 0), (0, 1), (-1, 0)]],
        ["flat", (0.0, 1.5), [(0, 0), (-1, 0), (-1, -1)]],
        ["flat", (1.0, 0.5), [(0, 0), (-1, -1), (0, -1)]],
        ["flat", (2.0, 0.5), [(0, 0), (0, -1), (1, -1)]],
        [
            "flat",
            [(5, 3), (4.5, 4), (3.5, 4), (2.5, 3), (3.5, 2), (4.5, 2)],
            [
                [[1, 0], [2, 0], [2, 1]],
                [[1, 0], [2, 1], [1, 1]],
                [[1, 0], [1, 1], [0, 1]],
                [[1, 0], [0, 1], [0, 0]],
                [[1, 0], [0, 0], [1, -1]],
                [[1, 0], [1, -1], [2, 0]],
            ],
        ],
    ],
)
def test_cells_near_point(shape, point, expected_nearby_cells):
    grid = HexGrid(size=3, shape=shape)
    nearby_cells = grid.cells_near_point(point)
    numpy.testing.assert_allclose(nearby_cells, expected_nearby_cells)


@pytest.mark.parametrize("shape", ["pointy", "flat"])
@pytest.mark.parametrize("depth", list(range(1, 7)))
@pytest.mark.parametrize("index", [[2, 1], [1, 2]])
@pytest.mark.parametrize("multi_index", [False, True])
@pytest.mark.parametrize("include_selected", [False, True])
def test_neighbours(shape, depth, index, multi_index, include_selected):
    grid = HexGrid(size=3, shape=shape)

    if multi_index:
        index = [index, index]

    neighbours = grid.neighbours(index, depth=depth, include_selected=include_selected)

    if multi_index:
        numpy.testing.assert_allclose(
            *neighbours
        )  # make sure the neighbours are the same (since index was duplicated)
        neighbours = neighbours[0]  # continue to check single index
        index = index[0]

    if include_selected:
        # make sure the index is present and at the center of the neighbours array
        center_index = int(numpy.floor(len(neighbours) / 2))
        numpy.testing.assert_allclose(neighbours[center_index], index)
        # remove center index for further testing of other neighbours
        neighbours = numpy.delete(neighbours, center_index, axis=0)

    # If the neighbours are correct, there are always a multiple of 6 cells with the same distance to the center cell
    distances = numpy.linalg.norm(
        grid.centroid(neighbours) - grid.centroid(index), axis=1
    )
    for d in numpy.unique(distances):
        assert sum(distances == d) % 6 == 0

    # No cell can be further away than 'depth' number of cells * cell size
    assert all(distances <= grid.size * depth)


@pytest.mark.parametrize(
    "shape, method, expected_result, expected_bounds",
    (
        (
            "pointy",
            "nearest",
            [[2, 1], [2, 3], [4, 5], [6, 7]],
            (-1.0, -1.7320508075688776, 1.0, 1.7320508075688776),
        ),
        (
            "pointy",
            "bilinear",
            [
                [1.08333333, 1.75],
                [2.58333333, 3.25],
                [3.91666667, 4.58333333],
                [
                    5.41666667,
                    -827.66666667,
                ],  # FIXME: outlier value artifact of nodata value of -9999. Nodata should not be taken into account
            ],
            (-1.0, -1.7320508075688776, 1.0, 1.7320508075688776),
        ),
        (
            "flat",
            "nearest",
            [[0, 3], [0, 0], [1, 4], [1, 5]],
            (-1.0, -0.8660254037844388, 1.0, 2.5980762113533165),
        ),
        (
            "flat",
            "bilinear",
            [
                [-3.85752650e03, -6.60020632e00],
                [-2.69773379e03, 1.88397460e00],
                [1.11417424e00, 3.80847549e00],
                [-2.69684981e03, 3.03867513e00],
            ],
            (-1.0, -0.8660254037844388, 1.0, 2.5980762113533165),
        ),
    ),
)
def test_resample(
    basic_bounded_flat_grid,
    basic_bounded_pointy_grid,
    shape,
    method,
    expected_result,
    expected_bounds,
):
    new_grid = HexGrid(size=1)
    grid = basic_bounded_flat_grid if shape == "flat" else basic_bounded_pointy_grid

    resampled = grid.resample(new_grid, method=method)

    numpy.testing.assert_allclose(resampled.data, expected_result)
    numpy.testing.assert_allclose(resampled.bounds, expected_bounds)
