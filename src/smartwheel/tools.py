def merge_dicts(dest, src, include_only=None):
    """
    Merge the contents of 2 dictionaries/configs while preserving references

    Should be used instead of `dest = {**dest, **src}`

    Note: references in dict objects are not preserved, please use Config object instead

    Parameters
    ==========
    dest
        Destination dict/config object
    src
        Source dict/config object
    include_only
        (Optional) Merge only this values from src
    """

    if type(dest) == dict:
        dest.update(src)
    else:
        dest.update(src, include_only=include_only)
