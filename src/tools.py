def merge_dicts(dest, src):
    """
    Merge the contents of 2 dictionaries/configs while preserving references
    Should be used instead of `dest = {**dest, **src}`

    Parameters
    ==========
    dest
        Destination dict/config object
    src
        Source dict/config object
    """

    dest.update(src)
