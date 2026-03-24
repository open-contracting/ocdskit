from collections import Counter
from itertools import chain

from concepts import Context

from ocdskit.util import _dedupe_with_counter, _get_prop_name, _split_camel_case, longest_common_subsequence


def get_base_class_name(class_names, prefix=""):
    """
    Derive a base class name from the longest common subsequence of words within class names.

    :param list[str] class_names: a list of class names
    :param str prefix: a prefix for the base class name
    :returns: a base class name
    :rtype: str or None
    """
    if len(class_names) < 2:
        return None

    sequences = [_split_camel_case(name) for name in class_names]

    lcs = sequences[0]
    for sequence in sequences[1:]:
        lcs = longest_common_subsequence(lcs, sequence)
        if not lcs:
            return None

    seen = set()
    unique = []
    for word in lcs:
        if word not in seen:
            seen.add(word)
            unique.append(word)

    return prefix + "".join(unique)


# https://en.wikipedia.org/wiki/Formal_concept_analysis
def get_base_classes_via_fca(classes, min_intent=2, min_extent=2, max_field_prevalence=1.0, base_class_name_prefix=""):
    """
    Identify base classes using `Formal Concept Analysis <https://en.wikipedia.org/wiki/Formal_concept_analysis>`__.

    Builds a concept lattice from the property sets of each class. Concepts are filtered to those with at least
    ``min_extent`` member classes and ``min_intent`` non-inherited, non-common properties. Properties found in more
    than ``max_field_prevalence`` of classes are considered common and ignored for the ``min_intent`` threshold.

    :param dict classes: mapping of definition names to sets of ``{prop}:{hash}`` strings
    :param int min_intent: minimum number of non-inherited, non-common properties for a base class
    :param int min_extent: minimum number of member classes for a base class
    :param float max_field_prevalence: fields found in more than this proportion of classes are considered common
    :param str base_class_name_prefix: a prefix to disambiguate base class names from existing class names
    :returns: a list of dicts with ``name``, ``members``, and ``props`` keys
    :rtype: list[dict]
    """
    # Sort the properties to achieve deterministic behavior.
    properties = sorted(set().union(*classes.values()))
    bools = [tuple(prop in classes[name] for prop in properties) for name in classes]
    context = Context(classes, properties, bools)

    # Determine the common fields.
    n = len(classes)
    counts = Counter(chain.from_iterable(classes.values()))
    common_properties = {prop for prop, count in counts.items() if count / n > max_field_prevalence}

    # Iterate general-to-specific (reversed lattice) so the most general concept claims the base name,
    # and more specific concepts get a minimal()-based suffix for disambiguation.
    names = set(classes)
    base_classes = []
    for concept in reversed(context.lattice):
        # `intent` is a tuple of the shared properties.
        intent = set(concept.intent)
        # `extent` is a tuple of the classes with the shared properties.
        extent = list(concept.extent)
        # Base classes must have at least `min_extent` specialized classes.
        if len(extent) < min_extent:
            continue

        # `upper_neighbors` are the concept's parents in the lattice (with strictly fewer `intent` properties).
        if concept.upper_neighbors:
            best_parent_properties = set(max(concept.upper_neighbors, key=lambda c: len(c.intent)).intent)
            inherited_properties = set().union(*(set(p.intent) for p in concept.upper_neighbors))
        else:
            best_parent_properties = set()
            inherited_properties = set()
        # Base classes must have at least `min_intent` non-common fields more than the best parent.
        if len(intent - common_properties - best_parent_properties) < min_intent:
            continue
        # Base classes must have at least one field not covered by any parent.
        if intent <= inherited_properties:
            continue

        name = get_base_class_name(extent, prefix=base_class_name_prefix)
        if name is None or name in names:
            suffix = "".join(word for prop in concept.minimal() for word in _split_camel_case(_get_prop_name(prop)))
            name = _dedupe_with_counter(f"{name or base_class_name_prefix}{suffix or 'Base'}", names)
        names.add(name)

        base_classes.append({"name": name, "members": extent, "props": intent})

    return base_classes
