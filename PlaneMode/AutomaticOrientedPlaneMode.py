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
import CoplanarJointOrient.mayaUtil

import CoplanarJointOrient.PlaneMode.ChainDependantPlaneMode
import CoplanarJointOrient.MayaUIValue.NormalModeValue

class AutomaticOrientedPlaneMode(CoplanarJointOrient.PlaneMode.ChainDependantPlaneMode.ChainDependantPlaneMode):
    def __init__(self, coplanarizer):
        super(AutomaticOrientedPlaneMode, self).__init__(coplanarizer)
        
    def setupUI(self, parentUI):
        self.setupValues(None)
        self.planeNormalMode.setValue(CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_2POINT_VECTOR)
        
        if(parentUI):        
            label = cmds.text(label="Automatic from orientations plane mode set", parent=parentUI)
            
            cmds.formLayout(parentUI, edit=True, attachForm=[
                                                             (label, "left", 0),
                                                             (label, "top", 10),
                                                             ])
            
            self.advancedSettingsUI = parentUI
            
    def coplanarizerChainUpdated(self):
        super(AutomaticOrientedPlaneMode, self).coplanarizerChainUpdated()
        
        if(self.currentCoplanarizerChainRoot is not None and self.currentCoplanarizerChainEnd is not None):
            self.planePosition.computeFromNodes([self.currentCoplanarizerChainRoot])
            self.planeNormalVector.computeFromNodes(CoplanarJointOrient.mayaUtil.getWholeParentChain(self.currentCoplanarizerChainRoot, self.currentCoplanarizerChainEnd))
            self.planeNormalPoint0.computeFromNodes([self.currentCoplanarizerChainRoot])
            self.planeNormalPoint1.computeFromNodes([self.currentCoplanarizerChainEnd])