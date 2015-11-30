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
import maya.api.OpenMaya as om
import functools

import CoplanarJointOrient.PlaneMode.PlaneMode
import CoplanarJointOrient.MayaUIValue.NormalModeValue
import CoplanarJointOrient.MayaUIValue.PositionValue
import CoplanarJointOrient.MayaUIValue.DirectionVectorValue

import CoplanarJointOrient.mayaMathUtil

class AdvancedPlaneMode(CoplanarJointOrient.PlaneMode.PlaneMode.PlaneMode):    
    def __init__(self, coplanarizer):
        super(AdvancedPlaneMode, self).__init__(coplanarizer)

        self.planePosition = None
        
        self.planeNormalVector = None
        
        self.planeNormalPoint0 = None
        self.planeNormalPoint1 = None
        self.planeNormalPoint2 = None
                
        self.planeNormalMode = None
        
    def setupUI(self, parentUI):
        self.setupValues(parentUI)

        if(parentUI is not None):
            separator = cmds.separator(style="in", height=3, parent=parentUI)        
            label = cmds.text(label="Advanced Plane Mode Options", parent=parentUI)
            
            cmds.formLayout(parentUI, edit=True, attachForm=[
                                                             (separator, "left", 0),
                                                             (separator, "top", 5),
                                                             (separator, "right", 0),
                                                             
                                                             (label, "left", 0),
                                                             (label, "top", 10),
                                                             
                                                             (self.planePosition.rootUI, "right", 10),
                                                             (self.planePosition.rootUI, "top", 35),
                                                             
                                                             (self.planeNormalMode.rootUI, "left", 0),
                                                             (self.planeNormalMode.rootUI, "top", 65),
                                                             
                                                             (self.planeNormalVector.rootUI, "right", 10),
                                                             (self.planeNormalVector.rootUI, "top", 90),
                                                             
                                                             (self.planeNormalPoint0.rootUI, "right", 10),
                                                             (self.planeNormalPoint0.rootUI, "top", 120),
                                                             
                                                             (self.planeNormalPoint1.rootUI, "right", 10),
                                                             (self.planeNormalPoint1.rootUI, "top", 150),
                                                             
                                                             (self.planeNormalPoint2.rootUI, "right", 10),
                                                             (self.planeNormalPoint2.rootUI, "top", 180),                                                                    
                                                             ])

        self.advancedSettingsUI = parentUI

    def setupValues(self, parentUI):
        self.planePosition = CoplanarJointOrient.MayaUIValue.PositionValue.PositionValue(label="Position", parentUI=parentUI)
        self.planePosition.onChangeFunc = functools.partial(CoplanarJointOrient.PlaneMode.AdvancedPlaneMode.AdvancedPlaneMode.onPositionChange, self)
        
        self.planeNormalMode = CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue(parentUI=parentUI)
        self.planeNormalMode.onChangeFunc = functools.partial(CoplanarJointOrient.PlaneMode.AdvancedPlaneMode.AdvancedPlaneMode.onNormalModeChange, self)
        
        self.planeNormalVector = CoplanarJointOrient.MayaUIValue.DirectionVectorValue.DirectionVectorValue(label="Direction", parentUI=parentUI)
        self.planeNormalVector.onChangeFunc = functools.partial(CoplanarJointOrient.PlaneMode.AdvancedPlaneMode.AdvancedPlaneMode.onNormalVectorChange, self)
        
        self.planeNormalPoint0 = CoplanarJointOrient.MayaUIValue.PositionValue.PositionValue(label="Point 1", parentUI=parentUI)
        self.planeNormalPoint1 = CoplanarJointOrient.MayaUIValue.PositionValue.PositionValue(label="Point 2", parentUI=parentUI)
        self.planeNormalPoint2 =CoplanarJointOrient. MayaUIValue.PositionValue.PositionValue(label="Point 3", parentUI=parentUI)
        
        self.planeNormalPoint0.onChangeFunc = functools.partial(CoplanarJointOrient.PlaneMode.AdvancedPlaneMode.AdvancedPlaneMode.onPoint01Change, self)
        self.planeNormalPoint1.onChangeFunc = functools.partial(CoplanarJointOrient.PlaneMode.AdvancedPlaneMode.AdvancedPlaneMode.onPoint01Change, self)
        self.planeNormalPoint2.onChangeFunc = functools.partial(CoplanarJointOrient.PlaneMode.AdvancedPlaneMode.AdvancedPlaneMode.onPoint2Change, self)

    def updatePlane(self):
        planeNormal = om.MVector(om.MVector.kXaxisVector)
        
        if(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_VECTOR):
            planeNormal = self.planeNormalVector.value
        elif(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_3POINT):
            planeNormal = CoplanarJointOrient.mayaMathUtil.get3PointNormal(self.planeNormalPoint0.value, self.planeNormalPoint1.value, self.planeNormalPoint2.value)
        elif(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_2POINT_VECTOR):
            planeNormal = CoplanarJointOrient.mayaMathUtil.get2PointNormal(self.planeNormalPoint0.value, self.planeNormalPoint1.value, self.planeNormalVector.value)
        else:
            cmds.error("Invalid normal mode" + str(self.planeNormalMode.value) + "in AdvancedPlaneMode")
            
        #see what the average normal is and if it's opposite the planeNormal flip it
        if(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_3POINT or
           self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_2POINT_VECTOR):            
            if(self.coplanarizer.chainRoot is not None and self.coplanarizer.chainEnd is not None):
                averageNormal = CoplanarJointOrient.mayaUtil.getAverageNodeDirectionVector(CoplanarJointOrient.mayaUtil.getWholeParentChain(self.coplanarizer.chainRoot, self.coplanarizer.chainEnd), self.coplanarizer.turnAxis.value)
                
                #just a dot product
                if(planeNormal * averageNormal < 0):
                    planeNormal *= -1
        
        self.alignmentPlane.setPlane(planeNormal, 0)
        self.alignmentPlanePreviewLocation = self.planePosition.value
        CoplanarJointOrient.mayaMathUtil.setPlaneWorldPosition(self.alignmentPlane, self.planePosition.value)
        
        super(AdvancedPlaneMode, self).updatePlane()
        
    def onNormalModeChange(self, value):
        if(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_VECTOR):
            self.planeNormalVector.setEnabled(True)
            self.planeNormalPoint0.setEnabled(False)
            self.planeNormalPoint1.setEnabled(False)
            self.planeNormalPoint2.setEnabled(False)
        elif(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_3POINT):
            self.planeNormalVector.setEnabled(False)
            self.planeNormalPoint0.setEnabled(True)
            self.planeNormalPoint1.setEnabled(True)
            self.planeNormalPoint2.setEnabled(True)
        elif(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_2POINT_VECTOR):
            self.planeNormalVector.setEnabled(True)
            self.planeNormalPoint0.setEnabled(True)
            self.planeNormalPoint1.setEnabled(True)
            self.planeNormalPoint2.setEnabled(False)
        else:
            cmds.error("Invalid normal mode" + str(self.planeNormalMode.value) + "in AdvancedPlaneMode")
        
        self.updatePlane()
        
    def onNormalVectorChange(self, value):
        if(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_VECTOR 
           or self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_2POINT_VECTOR):
            self.updatePlane()
            
    def onPositionChange(self, value):
        self.updatePlane()
        
    def onPoint01Change(self, value):
        if(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_2POINT_VECTOR 
           or self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_3POINT):
            self.updatePlane()
            
    def onPoint2Change(self, value):
        if(self.planeNormalMode.value == CoplanarJointOrient.MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_3POINT):
            self.updatePlane()