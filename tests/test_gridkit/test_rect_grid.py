import numpy
import pytest

from gridkit.rect_grid import RectGrid


@pytest.mark.parametrize(
    "points, expected_ids",
    [
        [(340, -14.2), (68, -8)],  # test single point as tuple
        [[[14, 3], [-8, 1]], [[2, 1], [-2, 0]]],  # test multiple points as stacked list
        [
            numpy.array([[14, 3], [-8, 1]]),
            numpy.array([[2, 1], [-2, 0]]),
        ],  # test multiple points as numpy ndarray
    ],
)
def test_cell_at_point(points, expected_ids):
    # TODO: take offset into account
    ids = RectGrid(dx=5, dy=2).cell_at_point(points)
    numpy.testing.assert_allclose(ids, expected_ids)


def test_centroid():
    grid = RectGrid(dx=5, dy=2)
    indices = [(-1, 1), (1, -4)]
    expected_centroids = numpy.array([[-2.5, 3], [7.5, -7]])

    centroids = grid.centroid(indices)
    numpy.testing.assert_allclose(centroids, expected_centroids)


@pytest.mark.parametrize(
    "mode, expected_bounds",
    [
        ["expand", (-8, 1, -3, 6.5)],
        ["contract", (-7, 1.5, -4, 6)],
        ["nearest", (-7, 1.5, -3, 6.5)],
    ],
)
def test_align_bounds(mode, expected_bounds):
    grid = RectGrid(dx=1, dy=0.5)
    bounds = (-7.2, 1.4, -3.2, 6.4)

    new_bounds = grid.align_bounds(bounds, mode=mode)
    numpy.testing.assert_allclose(new_bounds, expected_bounds)


@pytest.mark.parametrize("mode", ("expand", "contract", "nearest"))
def test_align_bounds_with_are_bounds_aligned(mode):
    grid = RectGrid(dx=3, dy=6, offset=(1, 2))
    bounds = (-7, -5, -1, 6.4)
    new_bounds = grid.align_bounds(bounds, mode=mode)
    assert grid.are_bounds_aligned(new_bounds), "Bounds are not aligned"


def test_cells_in_bounds():
    grid = RectGrid(dx=1, dy=2)
    bounds = (-5.2, 1.4, -3.2, 2.4)

    expected_ids = numpy.array(
        [
            [-6.0, 1.0],
            [-5.0, 1.0],
            [-4.0, 1.0],
            [-6.0, 0.0],
            [-5.0, 0.0],
            [-4.0, 0.0],
        ]
    )

    aligned_bounds = grid.align_bounds(bounds, mode="expand")
    ids, shape = grid.cells_in_bounds(aligned_bounds)
    numpy.testing.assert_allclose(ids, expected_ids)
    assert shape == (2, 3)


@pytest.mark.parametrize(
    "index,expected_np_id,expected_value",
    [  # note, numpy id is in y,x
        [(0, 0), (2, 1), 7],
        [
            [(-1, 1), (1, -2)],  # index
            [(1, 4), (0, 2)],  # expected_np_id in [(y0, y1), (x0,x1)]
            [3, 14],  # expected_value
        ],
    ],
)
def test_grid_id_to_numpy_id(
    basic_bounded_rect_grid, index, expected_np_id, expected_value
):
    grid = basic_bounded_rect_grid
    result = grid.grid_id_to_numpy_id(index)

    numpy.testing.assert_almost_equal(result, expected_np_id)
    numpy.testing.assert_almost_equal(grid.data[result[0], result[1]], expected_value)


@pytest.mark.parametrize(
    "np_index,expected_grid_id",
    [  # note, numpy id is in y,x
        [(2, 1), (0, 0)],
        [
            [(1, 4), (0, 2)],  # np_index
            [(-1, 1), (1, -2)],  # expected_grid_id in [(y0, y1), (x0,x1)]
        ],
    ],
)
def test_numpy_id_to_grid_id(basic_bounded_rect_grid, np_index, expected_grid_id):
    grid = basic_bounded_rect_grid
    result = grid.numpy_id_to_grid_id(np_index)

    numpy.testing.assert_almost_equal(result, expected_grid_id)
    numpy.testing.assert_almost_equal(
        grid.data[np_index[0], np_index[1]], grid.value(result)
    )


def test_nodata_value(basic_bounded_rect_grid):
    grid = basic_bounded_rect_grid
    grid.nodata_value = None

    # test no data are nodata
    assert grid.nodata_value is None
    assert grid.nodata() is None

    # test only one value is nodata
    grid.nodata_value = 6
    numpy.testing.assert_allclose(grid.nodata(), [[-1, 0]])

    # test all values are nodata
    grid = grid.update(numpy.ones((grid.height, grid.width)))
    assert grid.nodata_value == 6  # make sure nodata is inhertied after update
    grid.nodata_value = 1
    numpy.testing.assert_allclose(grid.nodata(), grid.cells_in_bounds(grid.bounds)[0])


@pytest.mark.parametrize("method", ["nearest", "linear", "cubic"])
def test_interp_nodata(basic_bounded_rect_grid, method):
    grid = basic_bounded_rect_grid.copy()
    grid.data[1:4, 0:4] = grid.nodata_value
    result_grid = grid.interp_nodata(method=method)

    if method == "nearest":
        numpy.testing.assert_allclose(
            result_grid, numpy.vstack([3 * [[0, 1, 2]], 2 * [[12, 13, 14]]])
        )
    else:
        numpy.testing.assert_allclose(result_grid, basic_bounded_rect_grid)


@pytest.mark.parametrize("depth", list(range(1, 7)))
@pytest.mark.parametrize("index", [[2, 1], [1, 2]])
@pytest.mark.parametrize("include_selected", [False, True])
@pytest.mark.parametrize("connect_corners", [False, True])
def test_neighbours(depth, index, include_selected, connect_corners):
    grid = RectGrid(dx=3, dy=3)
    neighbours = grid.neighbours(
        index,
        depth=depth,
        connect_corners=connect_corners,
        include_selected=include_selected,
    )

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
        assert sum(distances == d) % 4 == 0

    if connect_corners:
        # No cell can be further away than 'depth' number of cells * diagonal
        assert all(
            distances <= (grid.dx**2 + grid.dy**2) ** 0.5 * depth + 1e-14
        )  # add 1e-14 in absence of atol
    else:
        # No cell can be further away than 'depth' number of cells * cell size
        assert all(distances <= grid.dx * depth)


@pytest.mark.parametrize("include_selected", [False, True])
@pytest.mark.parametrize(
    "connect_corners, expected_cell_ids",
    [
        (
            False,
            [
                [
                    [-1, 1],
                    [-2, 0],
                    [-1, 0],  # selected id
                    [0, 0],
                    [-1, -1],
                ],
                [
                    [2, 2],
                    [1, 1],
                    [2, 1],  # selected id
                    [3, 1],
                    [2, 0],
                ],
            ],
        ),
        (
            True,
            [
                [
                    [-2, 1],
                    [-1, 1],
                    [0, 1],
                    [-2, 0],
                    [-1, 0],  # selected id
                    [0, 0],
                    [-2, -1],
                    [-1, -1],
                    [0, -1],
                ],
                [
                    [1, 2],
                    [2, 2],
                    [3, 2],
                    [1, 1],
                    [2, 1],  # selected id
                    [3, 1],
                    [1, 0],
                    [2, 0],
                    [3, 0],
                ],
            ],
        ),
    ],
)
def test_neighbours_multiple_indices(
    include_selected, connect_corners, expected_cell_ids
):
    expected_cell_ids = numpy.array(expected_cell_ids)
    testgrid = RectGrid(dx=1, dy=2)

    neighbours = testgrid.neighbours(
        [[-1, 0], [2, 1]],
        connect_corners=connect_corners,
        include_selected=include_selected,
    )
    if not include_selected:
        # exclude fourth cell (center)
        center_cell = int(expected_cell_ids.shape[1] / 2)
        remaining_cells = numpy.delete(
            numpy.arange(expected_cell_ids.shape[1]), center_cell
        )
        expected_cell_ids = expected_cell_ids[:, remaining_cells]

    numpy.testing.assert_allclose(neighbours, expected_cell_ids)
    neighbours_one_point = testgrid.neighbours(
        [-1, 0], connect_corners=connect_corners, include_selected=include_selected
    )
    numpy.testing.assert_allclose(neighbours_one_point, expected_cell_ids[0])
