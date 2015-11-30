"""
Coplanar joint orient tool 0.9.0
Ilya Seletsky 2015

TODO (known issues):
-Preview plane size setting (Width and Height)
-Handle when scene is closed while window open to reset things if possible
-Make the preview plane creation somehow not contribute to the undo history if possible or find a different way to display a preview plane
-Save settings between runs.
-Fix window not shrinking properly when switching between plane modes.
-Figure out what else crashes

Stretch goals:
-Joint preview.  Preview of how the joints will be oriented in real time without hitting apply button.
-Interactive plane mode.  Move a plane around in real time
-See if I can make UI more intuitive/self documenting and with a bunch of pretty pictures
-Auto compute preview plane size and position based on selected joints.
-Optimize UI change code to prevent unnecessary updates.  Not a real huge issue.
-Redo UI with pyQt to make the UI be more versatile and resizeable and strings localizeable, etc...
"""
import maya.cmds as cmds
import functools

import CoplanarJointOrient.PlaneMode.PlaneMode
import CoplanarJointOrient.mayaMathUtil

import CoplanarJointOrient.MayaUIValue.AxisValue
import CoplanarJointOrient.MayaUIValue.PositionValue

class AxisAlignedPlaneMode(CoplanarJointOrient.PlaneMode.PlaneMode.PlaneMode):
    def __init__(self, coplanarizer):
        super(AxisAlignedPlaneMode, self).__init__(coplanarizer)
        
        self.normalAxis = None
        self.worldOffset = None
        
    def setupUI(self, parentUI):
        self.normalAxis = CoplanarJointOrient.MayaUIValue.AxisValue.AxisValue(label="Normal Direction", parentUI=parentUI)
        self.worldOffset = CoplanarJointOrient.MayaUIValue.PositionValue.PositionValue(label="World Offset", parentUI=parentUI)
        
        self.normalAxis.onChangeFunc = functools.partial(CoplanarJointOrient.PlaneMode.AxisAlignedPlaneMode.AxisAlignedPlaneMode.onAxisChanged, self)
        self.worldOffset.onChangeFunc = functools.partial(CoplanarJointOrient.PlaneMode.AxisAlignedPlaneMode.AxisAlignedPlaneMode.onOffsetChanged, self)
                 
        if(parentUI is not None):
            separator = cmds.separator(style="in", height=3, parent=parentUI)        
            label = cmds.text(label="Axis Aligned Plane Mode Options", parent=parentUI)
            
            cmds.formLayout(parentUI, edit=True, attachForm=[
                                                             (separator, "left", 0),
                                                             (separator, "top", 5),
                                                             (separator, "right", 0),
                                                             
                                                             (label, "left", 0),
                                                             (label, "top", 10),
                                                             
                                                             (self.normalAxis.rootUI, "left", 0),
                                                             (self.normalAxis.rootUI, "top", 30),
                                                             
                                                             (self.worldOffset.rootUI, "right", 10),
                                                             (self.worldOffset.rootUI, "top", 50),
                                                             ])

        self.advancedSettingsUI = parentUI
        
    def updatePlane(self):
        self.alignmentPlanePreviewLocation = None

        self.alignmentPlane.setPlane(CoplanarJointOrient.mayaMathUtil.forwardVector(self.normalAxis.value), 
                                     self.worldOffset.value[self.normalAxis.value.axis] * (1 if self.normalAxis.value.negative else -1))
        
        super(AxisAlignedPlaneMode, self).updatePlane()
    
    def onAxisChanged(self, value):
        self.updatePlane()
        
    def onOffsetChanged(self, value):
        self.updatePlane()