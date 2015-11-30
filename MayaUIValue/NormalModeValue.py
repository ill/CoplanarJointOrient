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

class NormalModeValue(CoplanarJointOrient.MayaUIValue.ValueBase.ValueBase):
    PLANE_NORMAL_MODE_VECTOR = 0    
    PLANE_NORMAL_MODE_2POINT_VECTOR = 1
    PLANE_NORMAL_MODE_3POINT = 2
    
    def __init__(self, parentUI=None):
        super(NormalModeValue, self).__init__()
        self.value = NormalModeValue.PLANE_NORMAL_MODE_VECTOR
        
        if(parentUI is not None):            
            self.rootUI = cmds.radioButtonGrp(label="Normal Mode:", parent=parentUI, numberOfRadioButtons=3, labelArray3=("Direction Vector", "2 Points and Direction Vector", "3 Points"), select=1, columnWidth4=(75,110,180,75),
                                              onCommand1 = functools.partial(NormalModeValue.onRadioChange, self, NormalModeValue.PLANE_NORMAL_MODE_VECTOR),
                                              onCommand2 = functools.partial(NormalModeValue.onRadioChange, self, NormalModeValue.PLANE_NORMAL_MODE_2POINT_VECTOR),
                                              onCommand3 = functools.partial(NormalModeValue.onRadioChange, self, NormalModeValue.PLANE_NORMAL_MODE_3POINT))
                    
    def setValue(self, value):
        if(self.rootUI is not None):
            cmds.radioButtonGrp(self.rootUI, edit=True, select=value + 1)
            
        self.value = value
        self.callChangeFunc()
            
    def onRadioChange(self, value, unused):
        self.value = value
        self.callChangeFunc()
        
    def setEnabled(self, enabled):
        if(self.rootUI is not None):        
            if(enabled):
                cmds.radioButtonGrp(self.rootUI, edit=True, enable=True)
            else:
                cmds.radioButtonGrp(self.rootUI, edit=True, enable=False)