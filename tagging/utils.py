"""
Tagging utilities - from user tag input parsing to tag cloud
calculation.
"""
import math

import six
from django.db.models.query import QuerySet
from django.utils.encoding import force_str
from django.utils.translation import gettext as _

# Font size distribution algorithms
LOGARITHMIC, LINEAR = 1, 2


def parse_tag_input(input):
    """
    Parses tag input, with multiple word input being activated and
    delineated by commas and double quotes. Quotes take precedence, so
    they may contain commas.

    Returns a sorted list of unique tag names.
    """
    if not input:
        return []

    input = force_str(input)

    words = list(set(split_strip(input, ',')))
    words.sort()
    return words


def split_strip(input, delimiter=','):
    """
    Splits ``input`` on ``delimiter``, stripping each resulting string
    and returning a list of non-empty strings.
    """
    words = [w.strip() for w in input.split(delimiter)]
    return [w for w in words if w]


def edit_string_for_tags(tags):
    """
    Given list of ``Tag`` instances, creates a string representation of
    the list suitable for editing by the user, such that submitting the
    given string representation back without changing it will give the
    same list of tags.

    Tag names which contain commas will be double quoted.

    If any tag name which isn't being quoted contains whitespace, the
    resulting string of tag names will be comma-delimited, otherwise
    it will be space-delimited.
    """
    names = []
    for tag in tags:
        name = tag.name
        names.append(name)
    return ', '.join(names)


def get_queryset_and_model(queryset_or_model):
    """
    Given a ``QuerySet`` or a ``Model``, returns a two-tuple of
    (queryset, model).

    If a ``Model`` is given, the ``QuerySet`` returned will be created
    using its default manager.
    """
    try:
        return queryset_or_model, queryset_or_model.model
    except AttributeError:
        return queryset_or_model._default_manager.all(), queryset_or_model


def get_tag_list(tags):
    """
    Utility function for accepting tag input in a flexible manner.

    If a ``Tag`` object is given, it will be returned in a list as
    its single occupant.

    If given, the tag names in the following will be used to create a
    ``Tag`` ``QuerySet``:

       * A string, which may contain multiple tag names.
       * A list or tuple of strings corresponding to tag names.
       * A list or tuple of integers corresponding to tag ids.

    If given, the following will be returned as-is:

       * A list or tuple of ``Tag`` objects.
       * A ``Tag`` ``QuerySet``.

    """
    from tagging.models import Tag
    if isinstance(tags, Tag):
        return [tags]
    elif isinstance(tags, QuerySet) and tags.model is Tag:
        return tags
    elif isinstance(tags, six.string_types):
        return Tag.objects.filter(name__in=parse_tag_input(tags))
    elif isinstance(tags, (list, tuple)):
        if len(tags) == 0:
            return tags
        contents = set()
        for item in tags:
            if isinstance(item, six.string_types):
                contents.add('string')
            elif isinstance(item, Tag):
                contents.add('tag')
            elif isinstance(item, six.integer_types):
                contents.add('int')
        if len(contents) == 1:
            if 'string' in contents:
                return Tag.objects.filter(name__in=[force_str(tag)
                                                    for tag in tags])
            elif 'tag' in contents:
                return tags
            elif 'int' in contents:
                return Tag.objects.filter(id__in=tags)
        else:
            raise ValueError(
                _('If a list or tuple of tags is provided, '
                  'they must all be tag names, Tag objects or Tag ids.'))
    else:
        raise ValueError(_('The tag input given was invalid.'))


def get_tag(tag):
    """
    Utility function for accepting single tag input in a flexible
    manner.

    If a ``Tag`` object is given it will be returned as-is; if a
    string or integer are given, they will be used to lookup the
    appropriate ``Tag``.

    If no matching tag can be found, ``None`` will be returned.
    """
    from tagging.models import Tag
    if isinstance(tag, Tag):
        return tag

    try:
        if isinstance(tag, six.string_types):
            return Tag.objects.get(name=tag)
        elif isinstance(tag, six.integer_types):
            return Tag.objects.get(id=tag)
    except Tag.DoesNotExist:
        pass

    return None


def _calculate_thresholds(min_weight, max_weight, steps):
    delta = (max_weight - min_weight) / float(steps)
    return [min_weight + i * delta for i in range(1, steps + 1)]


def _calculate_tag_weight(weight, max_weight, distribution):
    """
    Logarithmic tag weight calculation is based on code from the
    *Tag Cloud* plugin for Mephisto, by Sven Fuchs.

    http://www.artweb-design.de/projects/mephisto-plugin-tag-cloud
    """
    if distribution == LINEAR or max_weight == 1:
        return weight
    elif distribution == LOGARITHMIC:
        return min(
            math.log(weight) * max_weight / math.log(max_weight),
            max_weight)
    raise ValueError(
        _('Invalid distribution algorithm specified: %s.') % distribution)


def calculate_cloud(tags, steps=4, distribution=LOGARITHMIC):
    """
    Add a ``font_size`` attribute to each tag according to the
    frequency of its use, as indicated by its ``count``
    attribute.

    ``steps`` defines the range of font sizes - ``font_size`` will
    be an integer between 1 and ``steps`` (inclusive).

    ``distribution`` defines the type of font size distribution
    algorithm which will be used - logarithmic or linear. It must be
    one of ``tagging.utils.LOGARITHMIC`` or ``tagging.utils.LINEAR``.
    """
    if len(tags) > 0:
        counts = [tag.count for tag in tags]
        min_weight = float(min(counts))
        max_weight = float(max(counts))
        thresholds = _calculate_thresholds(min_weight, max_weight, steps)
        for tag in tags:
            font_set = False
            tag_weight = _calculate_tag_weight(
                tag.count, max_weight, distribution)
            for i in range(steps):
                if not font_set and tag_weight <= thresholds[i]:
                    tag.font_size = i + 1
                    font_set = True
    return tags
