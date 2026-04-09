import functools
import re
import sys
from collections import Counter, defaultdict

import graphviz
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

from ocdskit.util import _split_camel_case

# Colorblind-friendly palette based on Okabe-Ito https://jfly.uni-koeln.de/color/
COLORS = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermilion
    "#CC79A7",  # reddish purple
    "#CCCCCC",  # gray
]
NEUTRAL_COLOR = "#999999"
DARKEN = 0.5


def _get_refs(schema, *, is_array=False):
    """Recursively yield (target, is_array) for all ``$refs`` in a ``properties`` schema."""
    if not isinstance(schema, dict):
        return
    for key, value in schema.items():
        if key == "$ref":
            yield value.rpartition("/")[2], is_array
        else:
            child_is_array = is_array or key in {"prefixItems", "additionalItems", "items"}
            if isinstance(value, dict):
                yield from _get_refs(value, is_array=child_is_array)
            elif isinstance(value, list):
                for item in value:
                    yield from _get_refs(item, is_array=child_is_array)


def _get_properties(schema):
    """Recursively yield (prop, subschema) from all ``properties`` mappings in a schema."""
    if not isinstance(schema, dict):
        return
    for key, value in schema.items():
        if key == "properties":
            yield from value.items()
        elif isinstance(value, dict):
            yield from _get_properties(value)
        elif isinstance(value, list):
            for item in value:
                yield from _get_properties(item)


def _get_schema_clusters(names, *, max_k, ignore_words=(), ignore_before=None, verbose=False):
    """
    Cluster schema names by TF-IDF similarity.

    Returns a cluster label (integer) for each schema name, or ``None`` if the name list is too small.
    """
    if len(names) < 4:  # need at least 2 clusters with 2 members each
        return None

    ignore = {word.capitalize() for word in ignore_words}  # same as _split_camel_case()
    tokens = (name.split(ignore_before, 1)[-1] for name in names) if ignore_before else names
    word_lists = [[word for word in _split_camel_case(token) if word not in ignore] for token in tokens]

    x = TfidfVectorizer().fit_transform(" ".join(words) for words in word_lists)

    best_score, best_labels = -1, None
    for k in range(2, min(max_k + 1, len(names))):
        labels = KMeans(n_clusters=k, random_state=0).fit_predict(x)
        if any(sum(labels == i) < 2 for i in range(k)):  # skip a clustering with any singletons
            continue
        score = silhouette_score(x, labels)
        if score > best_score:
            best_score, best_labels = score, labels

    if verbose and best_labels is not None:
        clusters = defaultdict(list)
        for name, words, label in zip(names, word_lists, best_labels, strict=True):
            clusters[label].append((name, words))
        for label, members in sorted(clusters.items()):
            print(f"Cluster {label}:", file=sys.stderr)  # noqa: T201
            for name, words in members:
                print(f"  {name}: {words}", file=sys.stderr)  # noqa: T201

    return best_labels


def _get_color_map(schemas, *, subgraph, manual_clusters=(), ignore_words=(), ignore_before=None, verbose=False):
    """
    Map each schema name to a fill color using clustering.

    ``manual_clusters`` is a list of regex patterns. Names matching pattern ``i`` are pinned to color ``i``.
    """
    color_map = {}

    names = [name for name in sorted(schemas) if name not in subgraph]
    cluster_index = 0

    # Manual clusters
    for pattern in manual_clusters:
        if matches := {name for name in names if re.search(pattern, name)}:
            names = [name for name in names if name not in matches]
            for name in matches:
                color_map[name] = COLORS[cluster_index]

            if verbose:
                print(f"Manual cluster {cluster_index} ({pattern!r}):", file=sys.stderr)  # noqa: T201
                for name in sorted(matches):
                    print(f"  {name}", file=sys.stderr)  # noqa: T201

            cluster_index += 1
            if cluster_index >= len(COLORS):
                break

    # Auto clusters
    if max_k := len(COLORS) - cluster_index:
        labels = _get_schema_clusters(
            names, max_k=max_k, ignore_words=ignore_words, ignore_before=ignore_before, verbose=verbose
        )
        if labels is None:
            for name in names:
                color_map[name] = NEUTRAL_COLOR
        else:
            largest_label = Counter(labels).most_common(1)[0][0]
            for name, label in zip(names, labels, strict=True):
                color_map[name] = COLORS[-1] if label == largest_label else COLORS[cluster_index + label]

    return color_map


def _add_node(graph, name, schema, *, no_properties=False, max_properties=None, fillcolor="white", is_base=False):
    lines = [name, ""]

    if not no_properties:
        properties = sorted(_get_properties(schema))

        for prop, subschema in properties[:max_properties]:
            if refs := list(_get_refs(subschema)):
                description = "|".join(f"{target}{'[]' if is_array else ''}" for target, is_array in sorted(refs))
            elif "items" in subschema:
                description = f"{subschema['items'].get('type', 'any')}[]"
            else:
                description = subschema.get("type", "any")
            lines.append(f"{prop}: {description}")

        if max_properties is not None and (remaining := len(properties[max_properties:])):
            lines.append(f"... +{remaining} more")

    label = "\\l".join(lines) + "\\l"

    attrs = {"style": "filled", "fillcolor": fillcolor}
    if is_base:
        attrs["shape"] = "box"
        attrs["penwidth"] = "3"

    # Braces flip orientation from horizontal to vertical.
    # https://graphviz.org/doc/info/shapes.html#record
    graph.node(name, label=label if is_base else f"{{{label}}}", **attrs)


def get_erd(
    schemas,
    *,
    no_properties=False,
    no_inheritance=False,
    only_inheritance=False,
    max_properties=None,
    subgraph=(),
    manual_clusters=(),
    ignore_words=(),
    ignore_before=None,
    base_class_name_prefix="",
    verbose=False,
):
    """Generate Graphviz DOT format."""
    _add = functools.partial(_add_node, no_properties=no_properties, max_properties=max_properties)

    color_map = _get_color_map(
        schemas,
        subgraph=subgraph,
        manual_clusters=manual_clusters,
        ignore_words=ignore_words,
        ignore_before=ignore_before,
        verbose=verbose,
    )

    all_relationships = []  # (source, target, is_array, label) tuples
    for name, schema in schemas.items():
        all_relationships.extend(  # inheritance
            (name, subschema["$ref"].rpartition("/")[2], "", None)
            for subschema in schema.get("allOf", [])
            if "$ref" in subschema
        )
        all_relationships.extend(  # reference
            (name, target, prop, is_array)
            for prop, subschema in _get_properties(schema)
            for target, is_array in _get_refs(subschema)
        )

    dot = graphviz.Digraph(
        "ERD",
        graph_attr={"rankdir": "LR", "splines": "ortho", "nodesep": "0.35"},
        node_attr={"fontname": "Helvetica", "fontsize": "10", "shape": "record", "style": "filled"},
        edge_attr={"fontname": "Helvetica", "fontsize": "9"},
    )

    # Generate nodes in root graph.
    for name, schema in sorted(schemas.items()):
        if name not in subgraph:
            is_base = base_class_name_prefix and name.startswith(base_class_name_prefix)
            _add(dot, name, schema, fillcolor=color_map[name], is_base=is_base)

    # Generate nodes in subgraph.
    if subgraph:
        # https://www.graphviz.org/doc/info/lang.html#subgraphs-and-clusters
        with dot.subgraph(name="cluster_subgraph") as cluster:
            cluster.attr(label="Base schemas", style="filled", fillcolor="#EEEEEE")
            for name in sorted(subgraph):
                _add(cluster, name, schemas[name])

    # Generate edges.
    seen_relationships = set()
    for source, target, label, is_array in sorted(all_relationships):
        # Skip edges that cross between the root graph and subgraph.
        if (source in subgraph) != (target in subgraph):
            continue

        relationship_key = (source, target, label)
        if relationship_key not in seen_relationships:
            attrs = {}
            if is_array is None:  # inheritance
                attrs["style"] = "invis" if no_inheritance else "dashed"  # default "solid"
            elif only_inheritance:
                attrs["style"] = "invis"
            elif is_array:
                attrs["arrowhead"] = "crow"  # default "normal"
            if label:  # inheritance uses no label
                attrs["xlabel"] = label
            if color := color_map.get(target):  # subgraph uses no color
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                attrs["color"] = f"#{round(r * DARKEN):02x}{round(g * DARKEN):02x}{round(b * DARKEN):02x}"

            dot.edge(source, target, **attrs)
            seen_relationships.add(relationship_key)

    return dot.source
