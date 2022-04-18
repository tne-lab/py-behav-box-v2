def touch_in_region(coords, dim, touch):
    return coords[0] < touch[0] < coords[0] + dim[0] and coords[1] < touch[1] < coords[1] + dim[1]
