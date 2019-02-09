# maya-keyframe-reduction
Keyframe Reduction for Maya using least-squares method.

<p align="center"><img src="docs/_images/keyframeReductionExample.gif?raw=true"></p>

## Installation
* Extract the content of the .rar file anywhere on disk.
* Drag the keyframeReduction.mel file in Maya to permanently install the script.

## Usage
A button on the MiscTools shelf will be created that will allow easy access to
the ui, this way the user doesn't need to worry about any of the code. If user
wishes to not use the shelf button the following commands can be used.

The ui responds to the current selection where it finds all of the suitable
animation curves for reduction. You will be able to filter the animation
curves based on the plug it is connected to. This will make it easier to
target exactly the curves you want to reduce.

After an animation curve is reduced the reduction percentage will be printed
to the console. This can give you an idea if you would like to increase or
decrease the error rate to get the desired results.

### UI
<p align="center"><img src="docs/_images/keyframeReductionUI.png?raw=true"></p>

Display the UI with the following code.
```python
import keyframeReduction.ui
keyframeReduction.ui.show()
```

### Command Line
Use the KeyframeReduction class on individual animation curves.
```python
from keyframeReduction import KeyframeReduction
obj = KeyframeReduction(pathToAnimCurve)
obj.reduce(error=0.1)
```

### Options
* **error**: The maximum amount the reduced curve is allowed to deviate from the sampled curve.
* **step**: The step size to sample the curve, default is set to one.
* **weightedTangents**: Reduce curve using weighted tangents, using weighted tangents will result in less keyframes.
* **tangentSplitAuto**: Automatically split tangents.
* **tangentSplitExisting**: Use existing keyframes that have split tangents.
* **tangentSplitAngleThreshold**: Split tangents based on an angle threshold.
* **tangentSplitAngleThresholdValue**: Split tangent angle value.
