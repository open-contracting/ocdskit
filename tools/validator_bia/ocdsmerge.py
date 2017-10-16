import collections

NOT_FLATTEN_KEYS = ['additionalIdentifiers',
                    'additionalClassifications',
                    'suppliers',
                    'changes',
                    'tenderers'
                    ]


def flatten(path, flattened, obj):
    if isinstance(obj, dict):
        iterable = list(obj.items())
        if not iterable:
            flattened[path] = {}
    else:
        iterable = list(enumerate(obj))
        if not iterable:
            flattened[path] = []
    for key, value in iterable:
        if isinstance(value, (dict, list)) and key not in NOT_FLATTEN_KEYS:
            flatten(path + (key,), flattened, value)
        else:
            flattened[path + (key,)] = value
    return flattened


def unflatten(flattened):
    unflattened = {}
    for flat_key in flattened:
        current_pos = unflattened
        for num, item in enumerate(flat_key):
            if isinstance(item, tuple):
                if len(flat_key) - 1 == num:
                    current_pos.append(flattened[flat_key])
                else:
                    for obj in current_pos:
                        obj_id = obj.get('id')
                        if obj_id == item[0]:
                            current_pos = obj
                            break
                    else:
                        new_pos = {"id": item[0]}
                        current_pos.append(new_pos)
                        current_pos = new_pos
                continue
            new_pos = current_pos.get(item)
            if new_pos is not None:
                current_pos = new_pos
                continue
            if len(flat_key) - 1 == num:
                current_pos[item] = flattened[flat_key]
            elif isinstance(flat_key[num + 1], tuple):
                new_pos = []
                current_pos[item] = new_pos
                current_pos = new_pos
            else:
                new_pos = {}
                current_pos[item] = new_pos
                current_pos = new_pos
    return unflattened


def process_flattened(flattened):
    processed = collections.OrderedDict()
    for key in sorted(flattened.keys(), key=lambda a: (len(a),) + a):
        new_key = []
        for num, item in enumerate(key):
            if isinstance(item, int):
                id_value = flattened.get(tuple(key[:num + 1]) + ('id',))
                if id_value is None:
                    id_value = item
                new_key.append((id_value,))
                continue
            new_key.append(item)
        processed[tuple(new_key)] = flattened[key]
    return processed


def merge(releases):
    merged = collections.OrderedDict({("tag",): ['compiled']})
    for release in sorted(releases, key=lambda rel: rel["date"]):
        release = release.copy()
        release.pop('tag', None)

        flat = flatten((), {}, release)

        processed = process_flattened(flat)
        merged.update(processed)
    return unflatten(merged)


def merge_versioned(releases):
    merged = collections.OrderedDict({("tag",): ['compiled']})
    for release in sorted(releases, key=lambda rel: rel["date"]):
        release = release.copy()
        ocid = release.pop("ocid")
        merged[("ocid",)] = ocid

        releaseID = release.pop("id")
        date = release.pop("date")
        tag = release.pop('tag', None)
        flat = flatten((), {}, release)

        processed = process_flattened(flat)

        for key, value in processed.items():
            if key[-1] == 'id' and isinstance(key[-2], tuple):
                merged[key] = value
                continue
            new_value = {"releaseID": releaseID,
                         "releaseDate": date,
                         "releaseTag": tag[0],
                         "value": value}
            if key in merged:
                if value == merged[key][-1]['value']:
                    continue

            if key not in merged:
                merged[key] = []
            merged[key].append(new_value)

    return unflatten(merged)
