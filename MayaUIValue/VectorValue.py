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
import maya.api.OpenMaya as om
import maya.cmds as cmds
import CoplanarJointOrient.MayaUIValue.ValueBase
import functools

class VectorValue(CoplanarJointOrient.MayaUIValue.ValueBase.ValueBase):
    def __init__(self, label=None, parentUI=None):
        super(VectorValue, self).__init__()
        self.value = om.MVector()
        
        if(parentUI is not None):
            self.rootUI = cmds.rowLayout(numberOfColumns=5, parent=parentUI)
            
            self.label = cmds.text(label=label, parent=self.rootUI)
            self.xField = cmds.textFieldGrp(label="x", text="0", parent=self.rootUI, columnWidth2 = [10, 100],
                                            textChangedCommand = functools.partial(VectorValue.onXFieldChange, self))
            self.yField = cmds.textFieldGrp(label="y", text="0", parent=self.rootUI, columnWidth2 = [10, 100],
                                            textChangedCommand = functools.partial(VectorValue.onYFieldChange, self))
            self.zField = cmds.textFieldGrp(label="z", text="0", parent=self.rootUI, columnWidth2 = [10, 100],
                                            textChangedCommand = functools.partial(VectorValue.onZFieldChange, self))        
            self.fromSelectionsButton = cmds.button(label="From Selections", parent=self.rootUI)
        
    def setValue(self, value):
        if(self.rootUI is not None):
            cmds.textFieldGrp(self.xField, edit=True, text=str(value.x))
            cmds.textFieldGrp(self.yField, edit=True, text=str(value.y))
            cmds.textFieldGrp(self.zField, edit=True, text=str(value.z))
            
        self.value = value
        self.callChangeFunc()            
            
    def onXFieldChange(self, value):
        self.value.x = float(value)
        self.callChangeFunc()
        
    def onYFieldChange(self, value):
        self.value.y = float(value)
        self.callChangeFunc()
        
    def onZFieldChange(self, value):
        self.value.z = float(value)
        self.callChangeFunc()
        
    def setEnabled(self, enabled):
        if(self.rootUI is not None):        
            if(enabled):
                cmds.textFieldGrp(self.xField, edit=True, enable=True)
                cmds.textFieldGrp(self.yField, edit=True, enable=True)
                cmds.textFieldGrp(self.zField, edit=True, enable=True)
                cmds.button(self.fromSelectionsButton, edit=True, enable=True)
            else:
                cmds.textFieldGrp(self.xField, edit=True, enable=False)
                cmds.textFieldGrp(self.yField, edit=True, enable=False)
                cmds.textFieldGrp(self.zField, edit=True, enable=False)
                cmds.button(self.fromSelectionsButton, edit=True, enable=False)