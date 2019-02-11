import os
from functools import partial
from maya import cmds, OpenMaya, OpenMayaUI

from . import utils
from .classes.keyframeReduction import KeyframeReduction


# ----------------------------------------------------------------------------


# import pyside, do qt version check for maya 2017 >
qtVersion = cmds.about(qtVersion=True)
if qtVersion.startswith("4") or type(qtVersion) not in [str, unicode]:
    from PySide.QtGui import *
    from PySide.QtCore import *
    import shiboken
else:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    import shiboken2 as shiboken


# ----------------------------------------------------------------------------


FONT = QFont()
FONT.setFamily("Consolas")

BOLT_FONT = QFont()
BOLT_FONT.setFamily("Consolas")
BOLT_FONT.setWeight(100)


# ----------------------------------------------------------------------------

        
def mayaWindow():
    """
    Get Maya's main window.
    
    :rtype: QMainWindow
    """
    window = OpenMayaUI.MQtUtil.mainWindow()
    window = shiboken.wrapInstance(long(window), QMainWindow)
    
    return window


# ----------------------------------------------------------------------------


def getIconPath(name):
    """
    Get an icon path based on file name. All paths in the XBMLANGPATH variable
    processed to see if the provided icon can be found.

    :param str name:
    :return: Icon path
    :rtype: str/None
    """
    for path in os.environ.get("XBMLANGPATH").split(os.pathsep):
        iconPath = os.path.join(path, name)
        if os.path.exists(iconPath):
            return iconPath.replace("\\", "/")

# ----------------------------------------------------------------------------


class Header(QLabel):
    def __init__(self, parent, text):
        super(Header, self).__init__(parent)
        self.setFont(BOLT_FONT)
        self.setText(text)


class Divider(QFrame):
    def __init__(self, parent):
        super(Divider, self).__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class CheckBox(QCheckBox):
    def __init__(self, parent, text, state):
        super(CheckBox, self).__init__(parent)
        self.setFont(FONT)
        self.setText(text)
        self.setChecked(state)


# ----------------------------------------------------------------------------


class LabelWidget(QWidget):
    def __init__(self, parent, text, widget):
        super(LabelWidget, self).__init__(parent)

        # create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(5)

        # create label
        label = QLabel(self)
        label.setFont(FONT)
        label.setText(text)
        layout.addWidget(label)

        # create widget
        self.widget = widget(self)
        self.widget.setFont(FONT)
        layout.addWidget(self.widget)


# ----------------------------------------------------------------------------


class AnimationCurvesFilterWidget(QWidget):
    def __init__(self, parent):
        super(AnimationCurvesFilterWidget, self).__init__(parent)

        # variables
        self._id = None
        self._plugStates = {}
        self._plugDefaults = [
            "translateX", "translateY", "translateZ",
            "rotateX", "rotateY", "rotateZ",
            "scaleX", "scaleY", "scaleZ",
        ]

        self._plugFilteredAnimationCurves = {}

        # set size policy
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        policy.setHorizontalStretch(2)
        self.setSizePolicy(policy)

        # create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # create scroll widget
        widget = QWidget(self)
        self._scroll = QVBoxLayout(widget)
        self._scroll.setContentsMargins(5, 5, 5, 5)
        self._scroll.setSpacing(5)

        # create spacer
        spacer = QSpacerItem(
            1,
            1,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )
        self._scroll.addItem(spacer)

        scroll = QScrollArea(self)
        scroll.setFocusPolicy(Qt.NoFocus)
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        layout.addWidget(scroll)

        # create select all button
        button = QPushButton(self)
        button.setText("Select All Animation Curves")
        button.setFont(FONT)
        button.released.connect(self.selectAllAnimationCurves)
        layout.addWidget(button)

        # update
        self.selectionChanged()

    # ------------------------------------------------------------------------

    def getAnimationCurves(self):
        """
        Loop over the selected animation curves and only return the ones that
        have the checked state set to true.

        :return: Animation curves
        :rtype: list
        """
        animationCurves = []
        for plug, curves in self.plugFilteredAnimationCurves.iteritems():
            if self.plugStates.get(plug, plug in self.plugDefaults):
                animationCurves.extend(curves)

        return animationCurves

    # ------------------------------------------------------------------------

    @property
    def plugFilteredAnimationCurves(self):
        """
        :return: Filtered animation curves
        :rtype: dict
        """
        return self._plugFilteredAnimationCurves

    @plugFilteredAnimationCurves.setter
    def plugFilteredAnimationCurves(self, data):
        """
        :param dict data:
        """
        self._plugFilteredAnimationCurves = data

    # ------------------------------------------------------------------------

    @property
    def plugStates(self):
        """
        A dictionary containing plugs as keys and its checked state as a
        value. This dictionary is used to maintain the checked state of plugs
        between selections.

        :return: Plug states
        :rtype: dict
        """
        return self._plugStates

    @property
    def plugDefaults(self):
        """
        A list of default plugs that are presented in order in case they are
        part of the selected plugs. This ensures the keys that are most likely
        to be reduced to appear on top.

        :return: Default plugs
        :rtype: list
        """
        return self._plugDefaults

    @property
    def plugMaxLength(self):
        """
        :return: Max length of plug string
        :rtype: int
        """
        return max(len(k) for k in self.plugFilteredAnimationCurves.keys())

    # ------------------------------------------------------------------------

    def addPlugCheckbox(self, plug):
        """
        Add a plug checkbox to the scroll layout. The checked state
        determines if the plugs animation curves are to be reduced.

        :param str plug:
        """
        # get variables
        num = len(self.plugFilteredAnimationCurves.get(plug))
        text = plug.ljust(self.plugMaxLength) + "    < {} >".format(num)
        state = self.plugStates.get(plug, plug in self.plugDefaults)

        # create widget
        checkbox = CheckBox(self, text, state)

        # set callback
        func = partial(self.updatePlugState, plug)
        checkbox.stateChanged.connect(func)

        # add to scroll layout
        self._scroll.insertWidget(self._scroll.count() - 1, checkbox)

    def updatePlugState(self, plug, state):
        """
        Update the plugStates dictionary of the provided plug with the
        provided value. This will help the state persist between selection.

        :param str plug:
        :param bool state:
        """
        self.plugStates[plug] = True if state == 2 else False

    # ------------------------------------------------------------------------

    def selectionChanged(self, *args):
        """
        This function gets called each time the selection is changed. It will
        update the UI to reflect the selected animation curves.
        """
        # clear widget
        self.clear()

        # get selected animation curves
        selection = utils.getSelectionAnimationCurves()
        filtered = utils.filterAnimationCurvesByPlug(selection)
        self.plugFilteredAnimationCurves = filtered

        # get plugs
        plugs = self.plugFilteredAnimationCurves.keys()

        # add default plugs first.
        for plug in self.plugDefaults:
            if plug not in plugs:
                continue

            self.addPlugCheckbox(plug)
            plugs.remove(plug)

        # add additional plugs
        for plug in sorted(plugs):
            self.addPlugCheckbox(plug)

    def selectAllAnimationCurves(self):
        """
        Get all suitable animation curves in the scene and select them.
        Suitable curves are curves that are not referenced and not driven
        keys.
        """
        animationCurves = utils.getAllAnimationCurves()
        cmds.select(animationCurves)

    # ------------------------------------------------------------------------

    def registerCallback(self):
        """
        Register callback that will update the ui everytime the selection has
        changed.
        """
        self._id = OpenMaya.MModelMessage.addCallback(
            OpenMaya.MModelMessage.kActiveListModified,
            self.selectionChanged
        )

    def removeCallback(self):
        if not self._id:
            return

        OpenMaya.MMessage.removeCallback(self._id)

    # ------------------------------------------------------------------------

    def clear(self):
        """
        Remove all of the widgets from the layout apart from the last item
        which is a spacer item.
        """
        for i in reversed(range(self._scroll.count() - 1)):
            item = self._scroll.itemAt(i)
            item.widget().deleteLater()


class ReductionSettingsWidget(QWidget):
    reduceReleased = Signal()

    def __init__(self, parent):
        super(ReductionSettingsWidget, self).__init__(parent)

        # set size policy
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        policy.setHorizontalStretch(3)
        self.setSizePolicy(policy)

        # create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # create settings
        settings = Header(self, "Settings")
        layout.addWidget(settings)

        # create max error
        self.error = LabelWidget(self, "Maximum Error:", QDoubleSpinBox)
        self.error.setToolTip("Maximum allowed error when reducing the animation curves.")
        self.error.widget.setRange(0, 1000)
        self.error.widget.setValue(0.1)
        self.error.widget.setSingleStep(0.1)
        layout.addWidget(self.error)

        # create step size
        self.step = LabelWidget(self, "Step Size:", QDoubleSpinBox)
        self.step.setToolTip("Step size at which to sample the animation curves.")
        self.step.widget.setRange(0.1, 100)
        self.step.widget.setValue(1)
        self.step.widget.setSingleStep(1)
        layout.addWidget(self.step)

        # create divider
        divider = Divider(self)
        layout.addWidget(divider)

        # create tangent settings
        settings = Header(self, "Tangent Settings < Weighted >")
        layout.addWidget(settings)

        # create weighted tangents
        self.weighted = LabelWidget(self, "Weighted:", QCheckBox)
        self.weighted.setToolTip("Created keyframes have weighted or non-weighted tangents.")
        layout.addWidget(self.weighted)

        # create divider
        divider = Divider(self)
        layout.addWidget(divider)

        # create tangent settings
        settings = Header(self, "Tangent Settings < Split >")
        layout.addWidget(settings)

        self.splitAuto = LabelWidget(self, "Auto:", QCheckBox)
        self.splitAuto.setToolTip("Split tangents automatically, works on estimation.")
        layout.addWidget(self.splitAuto)

        self.splitExisting = LabelWidget(self, "Existing:", QCheckBox)
        self.splitExisting.setToolTip("Split tangents where the tangents of original keys are already split.")
        layout.addWidget(self.splitExisting)

        self.splitThreshold = LabelWidget(self, "Threshold:", QCheckBox)
        self.splitThreshold.setToolTip("Split tangents of the angle is higher than the provided threshold.")
        layout.addWidget(self.splitThreshold)

        self.splitThresholdValue = LabelWidget(self, "Threshold Value:", QDoubleSpinBox)
        self.splitThresholdValue.widget.setRange(0.01, 180)
        self.splitThresholdValue.widget.setValue(15)
        self.splitThresholdValue.widget.setSingleStep(1)
        layout.addWidget(self.splitThresholdValue)

        # create spacer
        spacer = QSpacerItem(
            1,
            1,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )
        layout.addItem(spacer)

        # create select all button
        button = QPushButton(self)
        button.setText("Reduce")
        button.setFont(BOLT_FONT)
        button.released.connect(self.reduceReleased.emit)
        layout.addWidget(button)

    # ------------------------------------------------------------------------

    def getSettings(self):
        """
        :return: Reduce settings
        :rtype: dict
        """
        return {
            "error": self.error.widget.value(),
            "step": self.step.widget.value(),
            "weightedTangents": self.weighted.widget.isChecked(),
            "tangentSplitAuto": self.splitAuto.widget.isChecked(),
            "tangentSplitExisting": self.splitExisting.widget.isChecked(),
            "tangentSplitAngleThreshold": self.splitThreshold.widget.isChecked(),
            "tangentSplitAngleThresholdValue": self.splitThresholdValue.widget.value(),
        }


class KeyframeReductionWidget(QWidget):
    def __init__(self, parent):
        super(KeyframeReductionWidget, self).__init__(parent)
        
        # set ui
        self.setParent(parent)   

        self.setWindowTitle("Keyframe Reduction")
        self.resize(500, 300)
        
        # set icon
        self.setWindowFlags(Qt.Window)   
        self.setWindowIcon(QIcon(getIconPath("KR_icon.png")))

        # create layouts
        vLayout = QVBoxLayout(self)
        vLayout.setContentsMargins(5, 5, 5, 5)
        vLayout.setSpacing(5)
                
        hLayout = QHBoxLayout(self)
        hLayout.setContentsMargins(0, 0, 0, 0)
        hLayout.setSpacing(5)

        vLayout.addLayout(hLayout)

        # add filter
        self.filter = AnimationCurvesFilterWidget(self)
        self.filter.registerCallback()
        hLayout.addWidget(self.filter)

        # add settings
        self.settings = ReductionSettingsWidget(self)
        self.settings.reduceReleased.connect(self.reduce)
        hLayout.addWidget(self.settings)

        # add progress
        self.progress = QProgressBar(self)
        self.progress.setFont(FONT)
        vLayout.addWidget(self.progress)

    # ------------------------------------------------------------------------

    def reduce(self):
        """
        Get the animation curves and settings from the ui and reduce the
        keyframes on each of those animation curves using the provided
        settings.
        """
        # get animation curves and settings
        animationCurves = self.filter.getAnimationCurves()
        settings = self.settings.getSettings()

        # setup progress
        rate = 0
        num = len(animationCurves)
        self.progress.setRange(0, num)

        # wrap reduction in undo chunk
        with utils.UndoChunkContext():
            # reduce keyframes
            for i, animationCurve in enumerate(animationCurves):
                r = KeyframeReduction(animationCurve)
                rate += r.reduce(**settings)

                # increment progress
                self.progress.setFormat(animationCurve)
                self.progress.setValue(i+1)

        print "< KeyframeReductionWidget.reduce() " \
              "| overall-reduction-rate: {0:,.2f}% >".format(rate/num)

    # ------------------------------------------------------------------------

    def closeEvent(self, event):
        self.filter.removeCallback()
        super(KeyframeReductionWidget, self).closeEvent(event)


# ----------------------------------------------------------------------------


def show():
    keyframeReduction = KeyframeReductionWidget(mayaWindow())
    keyframeReduction.show()
