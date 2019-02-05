from maya import OpenMaya


class Vector2D(OpenMaya.MVector):
    def __init__(self, *args):
        if len(args) == 1:
            OpenMaya.MVector.__init__(self, args[0])
        elif len(args) == 2:
            OpenMaya.MVector.__init__(self, args[0], args[1], 0)

    def __str__(self):
        return "{}, {}".format(self.x, self.y)

    def __repr__(self):
        return "< Vector2D object | point: {} >".format(str(self))

    # ------------------------------------------------------------------------

    def distanceBetween(self, other):
        """
        :return: Distance between two points
        :rtype: float
        """
        return (self - other).length()

    def signedAngle(self, other):
        """
        :return: Signed angle between points
        :rtype: float
        """
        angle = self.angle(other)
        cross = self ^ other

        if cross.z < 0:
            return -angle

        return angle
