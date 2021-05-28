def rebuild_indexes(group):
    for i in range(len(group)):
        group[i].index = i


def get_id(item, default=0xff):
    return item.index if item else default
