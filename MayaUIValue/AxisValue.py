import maya.cmds as cmds
import CoplanarJointOrient.MayaUIValue.ValueBase
import functools
import CoplanarJointOrient.mayaMathUtil

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

class AxisValue(CoplanarJointOrient.MayaUIValue.ValueBase.ValueBase):
    def __init__(self, label=None, parentUI=None):
        super(AxisValue, self).__init__()
        self.value = CoplanarJointOrient.mayaMathUtil.Axis()
        
        if(parentUI is not None):
            self.rootUI = cmds.rowLayout(numberOfColumns=2, parent=parentUI)
            
            self.axisRadio = cmds.radioButtonGrp(label=label, parent=self.rootUI, numberOfRadioButtons=3, labelArray3=("X","Y","Z"), select=1, columnWidth4=(100,40,40,40),
                                                 onCommand1 = functools.partial(AxisValue.onAxisChange, self, 0),
                                                 onCommand2 = functools.partial(AxisValue.onAxisChange, self, 1),
                                                 onCommand3 = functools.partial(AxisValue.onAxisChange, self, 2))
            self.negativeCheck = cmds.checkBox(label="Negative", parent=self.rootUI,
                                               changeCommand = functools.partial(AxisValue.onNegativeChange, self))
        
    def setValue(self, value):
        if(self.rootUI is not None):
            cmds.radioButtonGrp(self.axisRadio, edit=True, select=value.axis + 1)
            cmds.checkBox(self.negativeCheck, edit=True, value=value.negative)
            
        self.value = value
        self.callChangeFunc()
            
    def onAxisChange(self, axis, unused):
        self.value.axis = axis
        self.callChangeFunc()
        
    def onNegativeChange(self, value):
        self.value.negative = value
        self.callChangeFunc()
        
    def setEnabled(self, enabled):
        if(self.rootUI is not None):        
            if(enabled):
                cmds.radioButtonGrp(self.axisRadio, edit=True, enable=True)
                cmds.checkBox(self.negativeCheck, edit=True, enable=True)
            else:
                cmds.radioButtonGrp(self.axisRadio, edit=True, enable=False)
                cmds.checkBox(self.negativeCheck, edit=True, enable=False)