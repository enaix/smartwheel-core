

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

    if type(src) == dict or type(dest) == dict:
        for key, _ in src.items():
            dest[key] = src[key]
    else:
        for key, _ in src.items():
            dest.c[key] = src.c[key]
