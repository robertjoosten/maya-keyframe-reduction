import maya.cmds as cmds

if not cmds.about(batch=True):
    import keyframeReduction.install
    cmds.evalDeferred(keyframeReduction.install.shelf)
