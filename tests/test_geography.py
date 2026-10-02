"""Small in-memory regressions for the documented Mesa-Geo 0.9.3 caveats."""

import pytest

pytestmark = pytest.mark.runtime


@pytest.fixture(autouse=True)
def offline_projection(monkeypatch):
    monkeypatch.setenv("PROJ_NETWORK", "OFF")


@pytest.fixture
def vector():
    import mesa
    from mesa_geo import GeoAgent, GeoSpace
    from shapely.geometry import box

    model = mesa.Model(rng=11)
    space = GeoSpace(crs="EPSG:32631")
    first = GeoAgent(model, box(0, 0, 1, 1), "EPSG:32631")
    second = GeoAgent(model, box(1, 0, 2, 1), "EPSG:32631")
    space.add_agents([first, second])
    return model, space, first, second


@pytest.fixture
def raster():
    import mesa
    import numpy as np
    from mesa_geo import RasterLayer

    layer = RasterLayer(width=3, height=2, crs="EPSG:32631",
                        total_bounds=[0, 0, 30, 20], model=mesa.Model(rng=11))
    values = np.array([[[-9999., 2., 3.], [4., 5., 6.]]])
    layer.apply_raster(values.copy(), attr_name="value")
    return layer, values


def test_coordinate_axes_and_projected_distance():
    import mesa
    from mesa_geo import GeoAgent, GeoSpace
    from pyproj import CRS, Transformer
    from shapely.geometry import Point

    forward = Transformer.from_crs(4326, 32631, always_xy=True)
    backward = Transformer.from_crs(32631, 4326, always_xy=True)
    assert forward.transform(3, 0) == pytest.approx((500000, 0), abs=1e-6)
    assert backward.transform(500000, 0) == pytest.approx((3, 0), abs=1e-8)
    assert CRS(32631).axis_info[0].unit_name == "metre"
    assert CRS(4326).axis_info[0].unit_name == "degree"
    model = mesa.Model(rng=11)
    space = GeoSpace(crs="EPSG:32631")
    a = GeoAgent(model, Point(500000, 0), space.crs)
    b = GeoAgent(model, Point(500300, 400), space.crs)
    assert space.distance(a, b) == pytest.approx(500)


def test_predicate_boundaries_and_self_inclusion(vector):
    _, space, first, second = vector
    assert list(space.agents_at((0.5, 0.5))) == [first]
    assert list(space.agents_at((1, 0.5))) == []  # shared boundary is excluded
    assert list(space.agents_at((3, 0.5))) == []
    assert list(space.get_relation(first, "touches")) == [second]
    assert first not in space.get_relation(first, "intersects")
    assert first in space.get_neighbors_within_distance(first, 2)


def test_safe_movement_refreshes_queries_but_not_cached_contiguity(vector):
    from shapely.geometry import box

    model, space, first, second = vector
    assert space.get_neighbors(first) == [second]
    space.remove_agent(second)  # remove using the geometry stored in the index
    second.geometry = box(10, 0, 11, 1)
    assert second.geometry.is_valid
    space.add_agents(second)
    assert list(space.agents_at((1.5, 0.5))) == []
    assert list(space.agents_at((10.5, 0.5))) == [second]
    assert list(space.get_relation(first, "touches")) == []
    assert space.get_neighbors(first) == [second]  # released stale-cache caveat
    space.remove_agent(second)
    second.remove()
    assert second not in space.agents
    assert second not in model.agents


def test_source_layer_preservation_and_detached_crs_copy():
    import geopandas as gpd
    import mesa
    from mesa_geo import GeoAgent, GeoSpace
    from shapely.geometry import Point

    source = gpd.GeoDataFrame({"name": ["anchor"]}, geometry=[Point(3, 0)], crs=4326)
    original = source.copy(deep=True)
    derived = source.copy(deep=True).to_crs(32631)
    model = mesa.Model(rng=11)
    space = GeoSpace(crs="EPSG:32631")
    agent = GeoAgent(model, Point(500000, 0), space.crs)
    space.add_agents(agent)
    space.add_layer(derived)
    assert space.layers[0] is derived
    assert source.equals(original) and source.crs == original.crs
    copied = space.to_crs(4326, inplace=False)
    detached = copied.agents[0]
    assert detached is not agent and detached.model is model
    assert detached.unique_id == agent.unique_id
    assert detached not in model.agents and agent in model.agents
    assert detached.geometry.x == pytest.approx(3, abs=1e-8)
    assert agent.geometry.equals(Point(500000, 0))
    assert derived.crs.to_epsg() == 32631 and space.crs.to_epsg() == 32631


def test_raster_coordinates_order_and_explicit_nodata_mask_round_trip(raster):
    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import array_bounds

    layer, values = raster
    assert layer[0, 0].rowcol == (1, 0)
    assert layer[2, 1].rowcol == (0, 2)
    assert layer[0, 0].xy == pytest.approx((5, 5))
    assert layer[2, 1].xy == pytest.approx((25, 15))
    assert array_bounds(2, 3, layer.transform) == pytest.approx((0, 0, 30, 20))
    layer.apply_raster(values + 1, attr_name="aux")
    ordered = layer.get_raster(attr_name=["aux", "value"])
    np.testing.assert_array_equal(ordered, np.concatenate([values + 1, values]))
    mask = np.array([[0, 255, 255], [255, 0, 255]], dtype="uint8")
    # A deliberate Rasterio path owns nodata and masks; Mesa-Geo is not relied on.
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True), MemoryFile() as memory:
        with memory.open(driver="GTiff", count=1, height=2, width=3,
                         dtype="float64", crs=layer.crs, transform=layer.transform,
                         nodata=-9999) as output:
            output.write(layer.get_raster(attr_name="value"))
            output.write_mask(mask)
        with memory.open() as restored:
            np.testing.assert_array_equal(restored.read(), values)
            np.testing.assert_array_equal(restored.read_masks(1), mask)
            assert restored.nodata == -9999
            assert restored.transform == layer.transform and restored.shape == (2, 3)
            assert restored.crs == layer.crs
            valid = restored.read(1, masked=True)
            assert valid.count() == 4 and valid.mean() == pytest.approx(3.75)


def test_passive_raster_cells_need_type_filtered_activation(raster, monkeypatch):
    from mesa_geo import GeoAgent
    from shapely.geometry import Point

    layer, _ = raster
    cells = list(layer)
    assert set(layer.model.agents) == set(cells)
    assert len({cell.unique_id for cell in cells}) == 6

    class Walker(GeoAgent):
        activations = 0

        def step(self):
            self.activations += 1

    walker = Walker(layer.model, Point(5, 5), layer.crs)
    assert walker.unique_id not in {cell.unique_id for cell in cells}
    for cell in cells:
        monkeypatch.setattr(cell, "step", lambda: pytest.fail("passive cell stepped"))
    layer.model.agents_by_type[Walker].do("step")
    assert walker.activations == 1 and len(layer.model.agents) == 7
    cells[0].remove()
    assert cells[0] not in layer.model.agents and cells[0] in list(layer)


@pytest.mark.parametrize("kind", ["raster", "image"])
def test_reprojection_preserves_source_and_exposes_dual_footprints(raster, kind):
    import numpy as np
    from mesa_geo import ImageLayer
    from rasterio.transform import array_bounds, from_bounds, xy
    from rasterio.warp import transform_bounds

    source, values = raster
    target_crs = 3857
    if kind == "image":
        values = np.arange(6, dtype=float).reshape(1, 2, 3)
        source = ImageLayer(values=values.copy(), crs=4326,
                            total_bounds=[-120, 30, -110, 50])
        target_crs = 32611
    before = (source.crs, source.transform, tuple(source.total_bounds))
    transformed = source.to_crs(target_crs, inplace=False)
    assert (source.crs, source.transform, tuple(source.total_bounds)) == before
    if kind == "raster":
        np.testing.assert_array_equal(source.get_raster(attr_name="value"), values)
        np.testing.assert_array_equal(transformed.get_raster(attr_name="value"), values)
        assert transformed.model is not source.model
        assert set(transformed.model.agents) == set(transformed)
        cell = transformed[0, 0]
        assert cell.xy == pytest.approx(xy(transformed.transform, *cell.rowcol))
    else:
        np.testing.assert_array_equal(source.values, values)
        np.testing.assert_array_equal(transformed.values, [[[1.], [1.], [4.]]])
    expected_envelope = transform_bounds(source.crs, target_crs, *source.total_bounds)
    assert transformed.total_bounds == pytest.approx(expected_envelope, abs=1e-6)
    grid = array_bounds(transformed.height, transformed.width, transformed.transform)
    assert not np.allclose(grid, transformed.total_bounds, rtol=1e-12, atol=1e-6)
    reconstructed = from_bounds(*transformed.total_bounds,
                                width=transformed.width, height=transformed.height)
    assert not np.allclose(tuple(reconstructed), tuple(transformed.transform),
                           rtol=1e-12, atol=1e-6)
