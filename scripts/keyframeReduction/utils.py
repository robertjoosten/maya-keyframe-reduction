import decimal
from maya import cmds


# ----------------------------------------------------------------------------


EPSILON = 12e-11
THRESHOLD = 12e-5


# ----------------------------------------------------------------------------


class UndoChunkContext(object):
    """
    The undo context is used to combine a chain of commands into one undo.
    Can be used in combination with the "with" statement.

    with UndoChunkContext():
        # code
    """

    def __enter__(self):
        cmds.undoInfo(openChunk=True)

    def __exit__(self, *exc_info):
        cmds.undoInfo(closeChunk=True)


# ----------------------------------------------------------------------------


def floatRange(start, end, step):
    """
    :param int/float start:
    :param int/float end:
    :param int/float step:
    :return: Float range
    :rtype: list
    """
    # store values
    values = []

    # convert step to decimal to ensure float precision
    step = decimal.Decimal(str(step))
    while start < end:
        values.append(float(start))
        start += step
        
    return values


# ----------------------------------------------------------------------------


def validateAnimationCurve(animationCurve):
    """
    Check if the parsed animation curve can be reduces. Set driven keyframes
    and referenced animation curves will be ignored.

    :param str animationCurve:
    :return: Validation state of the animation curve
    :rtype: bool
    """
    if cmds.listConnections("{}.input".format(animationCurve)):
        return False
    elif cmds.referenceQuery(animationCurve, isNodeReferenced=True):
        return False

    return True


# ----------------------------------------------------------------------------


def filterAnimationCurves(animationCurves):
    """
    Loop all the animation curves an run the validation function to make sure
    the animation curves are suitable for reduction.

    :param list animationCurves:
    :return: Animation curves
    :rtype: list
    """
    return [
        animationCurve
        for animationCurve in animationCurves
        if validateAnimationCurve(animationCurve)
    ]


def filterAnimationCurvesByPlug(animationCurves):
    """
    :param list animationCurves:
    :return: Filtered animation curves
    :rtype: dict
    """
    data = {}

    for animationCurve in animationCurves:
        # get plug
        plug = cmds.listConnections(
            "{}.output".format(animationCurve),
            plugs=True,
            source=False,
            destination=True,
            skipConversionNodes=True,
        )

        if not plug:
            continue

        # get attribute
        attribute = plug[0].split(".", 1)[-1]

        # add attribute as a key
        if attribute not in data.keys():
            data[attribute] = []

        # append animation curve to attribute list
        data[attribute].append(animationCurve)

    return data


# ----------------------------------------------------------------------------


def getAllAnimationCurves():
    """
    :return: All suitable animation curves in the current scene
    :rtype: list
    """
    return filterAnimationCurves(cmds.ls(type="animCurve") or [])


def getSelectionAnimationCurves():
    """
    :return: Selection animation curves
    :rtype: list
    """
    # get selection
    animationCurves = set()
    selection = cmds.ls(sl=True) or []

    # loop selection
    for sel in selection:
        # add selection is an animation curve
        if cmds.nodeType(sel).startswith("animCurve"):
            animationCurves.add(sel)
            continue

        # check if any animation curves are connected to node
        for animationCurve in cmds.listConnections(
            sel,
            type="animCurve",
            source=True,
            destination=False,
            skipConversionNodes=True,
        ) or []:
            animationCurves.add(animationCurve)

    # convert animation curves to list
    animationCurves = list(animationCurves)
    return filterAnimationCurves(animationCurves)
