import math
import time
from maya import cmds

from .vector import Vector2D
from .fit import FitBezier
from ..utils import floatRange, THRESHOLD


class KeyframeReduction(object):
    def __init__(self, path):
        """
        :param str path:
        """
        self._path = path

    def __repr__(self):
        return "< KeyframeReduction object | path: {} >".format(self.path)

    # ------------------------------------------------------------------------

    @property
    def path(self):
        """
        :return: Animation curve path
        :rtype: str
        """
        return self._path

    # ------------------------------------------------------------------------

    def getIndices(self):
        """
        :return: List of keyframe indices
        :rtype: list
        """
        return cmds.keyframe(self.path, query=True, indexValue=True)

    def getFrames(self):
        """
        :return: List of keyframe frames
        :rtype: list
        """
        indices = self.getIndices()
        return cmds.keyframe(
            self.path,
            query=True,
            index=(indices[0], indices[-1])
        ) or []

    def getValues(self, frames):
        """
        :param list frames: Frames to sample
        :return: List of values
        :rtype: list
        """
        return [
            cmds.keyframe(self.path, query=True, eval=True, time=(frame,))[0]
            for frame in frames
        ]

    # ------------------------------------------------------------------------

    def _findTangentSplitAuto(self, angles):
        """
        The automatic tangent split will take the average of all values and
        the average of just the minimum and maximum value and remaps that on
        a logarithmic scale, this will give a predicted split angle value.
        All angles will be processed to see if they fall in or outside that
        threshold.

        :param list angles:
        :return: Split indices
        :rtype: list
        """
        # get angles from points
        splits = []

        # get average variables
        minAngle = min(angles) or 0.00001
        maxAngle = max(angles)
        average = (minAngle + maxAngle) * 0.5
        mean = sum(angles) / len(angles) * 0.5

        # get value at which to split
        threshold = (math.log(average) - math.log(mean)) / (math.log(maxAngle) - math.log(minAngle)) * average

        # if curve is relatively smooth don't split
        if mean * 10 > average:
            return []

        # split based on angles
        for i, angle in enumerate(angles):
            if angle > threshold:
                splits.append(i + 1)

        return splits

    def _findTangentSplitExisting(self, frames, start, end, step):
        """
        Loop existing frames and see if any keyframes contain tangents that
        are not unified. If this is the case the index of the closest sampled
        point will be returned.

        :param list frames:
        :param int start:
        :param int end:
        :param int/float step:
        :return: Split indices
        :rtype: list
        """
        splits = []
        inTangentType = "step"
        outTangentType = "stepnext"

        inAngles = cmds.keyTangent(self.path, query=True, time=(start, end), inAngle=True)
        outAngles = cmds.keyTangent(self.path, query=True, time=(start, end), outAngle=True)
        inTangentTypes = cmds.keyTangent(self.path, query=True, time=(start, end), inTangentType=True)
        outTangentTypes = cmds.keyTangent(self.path, query=True, time=(start, end), outTangentType=True)

        iterator = zip(frames, inAngles, outAngles, inTangentTypes, outTangentTypes)
        for frame, inAngle, outAngle, inType, outType in iterator:
            # get closest index
            index = int((frame - start) / step)

            # validate split
            if abs(inAngle - outAngle) > THRESHOLD:
                splits.append(index)
            elif inType == inTangentType:
                splits.append(index)
            elif outType == outTangentType:
                splits.append(index)

        return splits

    def _findTangentSplitThreshold(self, angles, threshold):
        """
        The threshold tangent split will process all angles and check if that
        angle falls in or outside of user provided threshold.

        :param list angles:
        :param int/float threshold:
        :return: Split indices
        :rtype: list
        """
        splits = []

        # split based on angles
        for i, angle in enumerate(angles):
            if angle > threshold:
                splits.append(i + 1)

        return splits

    # ------------------------------------------------------------------------

    def _splitPoints(self, points, split):
        """
        Split provided points list based on the split indices provided. The
        lists will have a duplicate end and start points relating to each
        other.

        :param list points:
        :param list split:
        :return: Split points
        :rtype: list
        """
        # validate split
        if not split:
            return [points]

        # complete split with adding start and end frames
        if split[0] != 0:
            split.insert(0, 0)

        if split[-1] != len(points):
            split.append(len(points))

        # make sure split is sorted and doesn't contain any duplicates
        split = list(set(split))
        split.sort()

        # split range for looping
        splitA = split[:-1]
        splitB = split[1:]

        # get lists
        return [points[a:b + 1] for a, b in zip(splitA, splitB)]

    # ------------------------------------------------------------------------

    def _removeKeys(self, frames, start):
        """
        Remove all keys appart from the start key and move this start key to
        the start frame. This needs to be done to make sure the start frame
        is on an even frame.

        :param list frames:
        :param int start:
        """
        # remove keys
        cmds.cutKey(self.path, time=(frames[0] + 0.01, frames[-1]), option="keys")

        # move first key to start position in case start position is not on
        # an even frame.
        cmds.keyframe(self.path, edit=True, index=(0,), timeChange=start)

    def _addKeys(self, keyframes, weightedTangents):
        """
        Loop all the keyframes and create a keyframe and set the correct
        tangent information.

        :param list keyframes:
        :param bool weightedTangents:
        """
        # variables
        inAngle = Vector2D(-1, 0)
        outAngle = Vector2D(1, 0)

        # loop keyframes
        for keyframe in keyframes:
            # create keyframe point
            cmds.setKeyframe(self.path, time=keyframe.point.x, value=keyframe.point.y)

            # set keyframe tangent variable
            arguments = {"edit": True, "absolute": True, "time": (keyframe.point.x,)}

            # set weighted tangents
            cmds.keyTangent(self.path, weightedTangents=weightedTangents, **arguments)

            # unlock tangents if either in our out handle is not defined.
            if not keyframe.inHandle or not keyframe.outHandle:
                cmds.keyTangent(self.path, lock=False, **arguments)

                # add in tangent to arguments
            if keyframe.inHandle:
                arguments["inAngle"] = math.degrees(inAngle.signedAngle(keyframe.inHandle))
                arguments["inWeight"] = keyframe.inHandle.length()

            # add out tangent to arguments
            if keyframe.outHandle:
                arguments["outAngle"] = math.degrees(outAngle.signedAngle(keyframe.outHandle))
                arguments["outWeight"] = keyframe.outHandle.length()

            # set keyframe tangent
            cmds.keyTangent(self.path, **arguments)

    # ------------------------------------------------------------------------

    def sample(self, start, end, step):
        """
        Sample the current animation curve based on the start and end frame,
        and the provided step size. Vector2Ds and angles will be returned.

        :param int start:
        :param int end:
        :param int/float step:
        :return: Sample points and angles
        :rtype: list
        """
        # get frames and values
        frames = floatRange(start, end, step)
        values = self.getValues(frames)

        # get points and angles
        angles = []
        points = [Vector2D(*coord) for coord in zip(frames, values)]

        for i in range(1, len(points) - 2):
            v1 = points[i - 1] - points[i]
            v2 = points[i + 1] - points[i]
            angles.append(math.degrees(math.pi - v1.angle(v2)))

        return [points, angles]

    # ------------------------------------------------------------------------

    def reduce(
            self,
            error=1,
            step=1,
            weightedTangents=True,
            tangentSplitAuto=False,
            tangentSplitExisting=False,
            tangentSplitAngleThreshold=False,
            tangentSplitAngleThresholdValue=15.0,
    ):
        """
        Reduce the number of keyframes on the animation curve. Useful when
        you are working with baked curves.

        :param int/float error:
        :param int/float step:
        :param bool weightedTangents:
        :param bool tangentSplitAuto:
        :param bool tangentSplitExisting:
        :param bool tangentSplitAngleThreshold:
        :param int/float tangentSplitAngleThresholdValue:
        :return: Reduction rate
        :rtype: float
        """
        # get existing frames
        t = time.time()
        original = self.getFrames()

        # get start and end frames
        start = int(math.floor(original[0]))
        end = int(math.ceil(original[-1])) + 1

        # get sample frames and values
        points, angles = self.sample(start, end, step)

        # get split indices
        split = []

        if tangentSplitAuto:
            split.extend(self._findTangentSplitAuto(angles))
        if tangentSplitExisting:
            split.extend(self._findTangentSplitExisting(original, start, end, step))
        if tangentSplitAngleThreshold:
            split.extend(self._findTangentSplitThreshold(angles, tangentSplitAngleThresholdValue))

        # get split points
        points = self._splitPoints(points, split)

        # fit points and get keyframes
        keyframes = [
            keyframe
            for p in points
            for keyframe in FitBezier(p, error, weightedTangents).fit()
        ]

        # only set values if the curve can be optimized.
        if len(keyframes) >= len(original):
            print "< KeyframeReduction.reduce() " \
                "| path: {0} " \
                "| process-time: {1:,.2f} seconds " \
                "| unable-to-reduce >".format(self.path, time.time() - t)
            return 0

        # remove all keys but the first one and add keyframes
        self._removeKeys(original, start)
        self._addKeys(keyframes, weightedTangents)

        # print reduction rate
        rate = 100 - ((len(keyframes) / float(len(original))) * 100)
        print "< KeyframeReduction.reduce() " \
            "| path: {0} " \
            "| process-time: {1:,.2f} seconds " \
            "| reduction-rate: {2:,.2f}%  >".format(
                self.path,
                time.time() - t,
                rate
            )

        return rate
