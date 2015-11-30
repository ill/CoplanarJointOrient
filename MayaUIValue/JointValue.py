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
import CoplanarJointOrient.MayaUIValue.ValueBase
import functools
import CoplanarJointOrient.mayaUtil
import CoplanarJointOrient.CoplanarJointOrient

class JointValue(CoplanarJointOrient.MayaUIValue.ValueBase.ValueBase):
    def __init__(self, label=None, parentUI=None):
        super(JointValue, self).__init__()
        
        if(parentUI is not None):
            #TODO: figure out how to make eclipse stop complaining about WINDOW_WIDTH, has no issues with maya though
            self.rootUI = cmds.textFieldButtonGrp(label=label, parent=parentUI, buttonLabel="Selection", columnWidth3 = [50, CoplanarJointOrient.CoplanarJointOrient.WINDOW_WIDTH - 150, 100],
                                                                buttonCommand = functools.partial(JointValue.onSelectionPressed, self), 
                                                                textChangedCommand = functools.partial(JointValue.onJointNameChanged, self))
                        
    def setValue(self, value):
        if(self.rootUI is not None):
            cmds.textFieldButtonGrp(self.rootUI, edit=True, text=value)
            
        self.value = value
        self.callChangeFunc()
            
    def onSelectionPressed(self):
        selection = CoplanarJointOrient.mayaUtil.getFirstSelectedObject()
        
        if(CoplanarJointOrient.mayaUtil.isJoint(selection)):                    
            cmds.textFieldButtonGrp(self.rootUI, edit=True, text=selection)
            
    def onJointNameChanged(self, value):
        self.value = value
        self.callChangeFunc()
        
    def setEnabled(self, enabled):
        if(self.rootUI is not None):        
            if(enabled):
                cmds.textFieldButtonGrp(self.rootUI, edit=True, enable=True)
            else:
                cmds.textFieldButtonGrp(self.rootUI, edit=True, enable=False)