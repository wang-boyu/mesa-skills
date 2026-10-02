# Geography: semantics and version caveats

Read only when geography matters to the requested model, documentation or
evaluation. Keep it in the same model and analysis; do not substitute a
non-geographic problem. Missing GIS dependencies may prevent execution but
need not prevent truthful static documentation, planning or evidence review.

## Coordinates and representations

State CRS, axis order and units for interacting vector, raster, network,
discrete or hybrid objects. Assigning CRS metadata with `set_crs` does not
transform coordinates; `to_crs` does. For traditional manual x/y transforms,
use `always_xy=True`. Degrees are angular units, not metres.

Use a suitable projected CRS for planar physical distance, area and buffering;
justify a geodesic method and ellipsoid when projection distortion is material.
EPSG:3857 is not a universal measurement CRS. Check a known coordinate or
distance, transformation direction and units, not only a map's appearance.

Define geometry types, validity, empty/missing and multipart handling, repairs,
predicate direction, boundary inclusion and self inclusion. Check inside,
on-boundary and outside examples. Specify network connectivity, edge direction,
weights and snapping; for mixed representations, define crosswalks, update
order and conservation or consistency rules. When query result order affects
behavior, define an explicit ordering and tie policy; do not rely on incidental
spatial-index order. Preserve its effects on activation and random draw order.

## Movement, membership and source ownership

Keep model registration and spatial membership consistent; removing an agent
from one does not remove it from the other. For indexed movement, remove under
the old geometry, change and validate geometry, then re-add before querying.
Check neighborhood results after movement and membership changes. Verify public
union bounds across agents and static layers, including empty-space behavior;
recheck bounds and query behavior after transformations and membership changes.

Preserve input data: identify caller-owned objects before APIs that may mutate
them. Record source and derived CRS, fields, feature ordering, transform history,
I/O driver and provenance. Copy only with permission and respect access,
licensing and redistribution limits. Runtime success does not establish data
fitness, valid spatial inference or scientific adequacy. When performance matters
to the stated purpose, measure relevant spatial query, movement/index update,
raster I/O or memory costs at a representative scale within the authorized
budget. Report the environment and scale, preserve semantic checks, and leave
unmeasured requirements explicit; this does not authorize extra experiments.

## Raster semantics

Record shape, bands/attributes and their order, affine transform, resolution,
cell centres, bounds, dtype, value units, nodata, masks and alignment. Distinguish
upper-left row/column coordinates from lower-left model positions and CRS-space
x/y. Choose resampling according to data meaning; categorical and continuous
values usually need different treatment. Verify output nodata/masks and value
alignment rather than assuming that metadata survives a round trip.

Declare whether cells are active agents or a passive environment. Distinguish
total registered agents from the population used for activation and metrics.
In evaluation, preserve valid-cell denominators, area weighting and the actual
independent sampling unit. Nearby cells and repeated observations can be
dependent; consider spatial leakage, edge effects, resolution and aggregation
sensitivity, including the modifiable areal unit problem.

## Mesa-Geo 0.9.3 caveats

These retained caveats describe released 0.9.3 with Mesa 3.5.x, not other
Mesa-Geo versions. Inspect the project's actual environment and version-matched
primary sources. No 0.9.4 or newer-runtime support follows from a parseable
version or successful installation.

- `get_relation` excludes the focal agent; distance-neighbor queries may include
  it. Filter self explicitly when required. `agents_at` uses contains-style
  behavior, excluding points exactly on geometry boundaries.
- `get_neighbors` caches Queen contiguity and can stay stale after geometry or
  membership changes, even after spatial-index refresh. For dynamic topology,
  use current-geometry `get_relation(agent, "touches")` after safe movement,
  or deliberately rebuild a public GeoSpace. Do not call private invalidation.
- Adding a same-CRS GeoDataFrame retains it. Mismatched-CRS addition warns and
  may reproject the caller's frame in place. Preserve sources by explicitly
  copying/reprojecting an authorized derived frame before adding it.
- A non-inplace `GeoSpace.to_crs` copy is a detached spatial view: its copied
  agents retain source model/IDs but are not newly registered in
  `model.agents`. It is not an active replacement model. For an active
  source-preserving transform, create a separate model and fresh registered
  agents, reconciling source identity, scheduling, collection and space membership.
- Raster cells are registered Mesa agents and consume model-global IDs. Use
  type-filtered activation and counts for passive cells. Removing a cell from
  model registration does not automatically remove it from the raster layer.
  Prefer `rowcol` over deprecated `Cell.indices`.
- `RasterLayer.to_crs` changes georeferencing without resampling cell values;
  `ImageLayer.to_crs` reprojects values with nearest-neighbor resampling.
  After either, affine plus shape and CRS defines the actual grid footprint,
  centres and export. Stored `total_bounds` can instead be a transformed-source
  envelope used for reporting and GeoSpace bounds. Keep both distinct; do not
  rebuild the affine from that envelope or reset transformed-grid dimensions/
  bounds/values without an explicit new-grid and resampling decision.
- Nodata, masks and attribute order are not automatically preserved in every
  0.9.3 path. Own them explicitly through documented I/O or sidecar metadata,
  and verify the resulting values, shape and alignment.

Primary implementation references:
[GeoSpace 0.9.3](https://github.com/projectmesa/mesa-geo/blob/v0.9.3/mesa_geo/geospace.py)
and [raster layers 0.9.3](https://github.com/projectmesa/mesa-geo/blob/v0.9.3/mesa_geo/raster_layers.py).
