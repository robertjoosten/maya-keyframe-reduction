class Keyframe(object):
    def __init__(self, point, inHandle=None, outHandle=None):
        """
        :param Vector2D point:
        :param Vector2D inHandle:
        :param Vector2D outHandle:
        """
        self._point = point
        self._inHandle = inHandle
        self._outHandle = outHandle

    def __repr__(self):
        return "< Keyframe object | point: {} | in-handle: {} | out-handle: {} >".format(
            str(self.point),
            str(self.inHandle),
            str(self.outHandle)
        )

    # ------------------------------------------------------------------------

    @property
    def point(self):
        """
        :return: Vector2D
        :rtype: Vector2D
        """
        return self._point

    @point.setter
    def point(self, p):
        """
        :param Vector2D p:
        """
        self._point = p

    # ------------------------------------------------------------------------

    @property
    def inHandle(self):
        """
        :return: In handle
        :rtype: Vector2D
        """
        return self._inHandle

    @inHandle.setter
    def inHandle(self, p):
        """
        :param Vector2D p:
        """
        self._inHandle = p

    @property
    def outHandle(self):
        """
        :return: Out handle
        :rtype: Vector2D
        """
        return self._outHandle

    @outHandle.setter
    def outHandle(self, p):
        """
        :param Vector2D p:
        """
        self._outHandle = p
