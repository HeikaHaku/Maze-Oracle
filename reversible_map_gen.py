def edge_from_index(idx: int, width: int, height: int) -> Point:
    """
    Maps an integer to a cell on the rectangle boundary. It walks around the boudrary starting from top left to right, then down     the right edge, to the left along the bottom, and then up on the left edge back to the start.

    The perimeter excludes duplicate corners by subtracting 4.
    """
    perim = 2 * width + 2 * height - 4
    i = idx % perim

    if i < width:
        return Point(i, 0)

    i -= width
    if i < height - 1:
        return Point(width - 1, i + 1)

    i -= height - 1
    if i < width - 1:
        return Point(width - 2 - i, height - 1)

    i -= width - 1
    return Point(0, height - 2 - i)


def cell_from_int(value: int, width: int, height: int) -> Point:
    """
    Maps an integer to a grid cell using row-major indexing.
    """
    value %= width * height
    return Point(value % width, value // width)


def generate_map(
    seed: int,
    width: int = 16,
    height: int = 16,
    bits: int = 16,
) -> ToyMap:
    """
    Fixed-output procedural generator:

        seed -> LCG outputs -> feature placements
        Right now it doesn't place walls and it's possible to lace features in the same cell, but we can work with that.
    """
    rng = lcg_stream(seed, bits)

    r_start = next(rng)
    r_exit = next(rng)
    r_key = next(rng)
    r_door = next(rng)
    r_treasure = next(rng)

    start = edge_from_index(r_start, width, height)
    exit_ = edge_from_index(r_exit, width, height)

    # Deterministically avoid identical start and exit.
    if exit_ == start:
        exit_ = edge_from_index(r_exit + 1, width, height)

    return Map(
        seed=seed,
        width=width,
        height=height,
        start=start,
        exit=exit_,
        key=cell_from_int(r_key, width, height),
        door=cell_from_int(r_door, width, height),
        treasure=cell_from_int(r_treasure, width, height),
    )