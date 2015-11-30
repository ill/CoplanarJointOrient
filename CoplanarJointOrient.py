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
import functools

import mayaUtil

import PlaneMode.AdvancedPlaneMode
import PlaneMode.Automatic3PointPlaneMode
import PlaneMode.AutomaticOrientedPlaneMode
import PlaneMode.AxisAlignedPlaneMode

import MayaUIValue.AxisValue
import MayaUIValue.BoolValue
import MayaUIValue.JointValue
import MayaUIValue.NormalModeValue

import mayaMathUtil

SELECTION_MESSAGE = "Select 2 joints, one of which is a descendant of another in the parent heirarchy"
WINDOW_WIDTH = 600
   
maya_useNewAPI = True
   
"""
Creates a plane in the maya scene for visualization
"""
def createDebugVisualizerPlane(plane, position = None, name = None):
    if(plane is None):
        return None

    #TODO: for now this creates a plane that ends up affecting the scene history, so undo/redo actions end up recreating the plane
    #figure out how to draw this plane without this happening
    debugPlane = cmds.polyPlane(name = name if name else "debugPlane", width=100, height=100, axis=[plane.normal().x, plane.normal().y, plane.normal().z], constructionHistory=False)
    cmds.toggle(debugPlane, state=True, template=True)  #make plane unselectable and undeletable so users can't accidentally delete it and break things

    createPos = om.MVector()

    if(position is None):
        if(plane.normal().x != 0):
            #automatically compute a position where we find x for if y and z were 0
            createPos = om.MVector(-plane.distance() / plane.normal().x, 0, 0)
        elif(plane.normal().y != 0):
            #automatically compute a position where we find y for if x and z were 0
            createPos = om.MVector(0, -plane.distance() / plane.normal().y, 0)
        elif(plane.normal().z != 0):
            #automatically compute a position where we find z for if x and y were 0
            createPos = om.MVector(0, 0, -plane.distance() / plane.normal().z)
        else:
            print("Invalid plane normal, all components are 0")
    else:
        createPos = position  

    cmds.xform(debugPlane, absolute=True, worldSpace=True, translation=[createPos.x, createPos.y, createPos.z])

    return debugPlane

"""
Now that the UI did all the hard work of configuring the alignment plane, requiring like > 1000 lines of code, all the real work happens here in this one function
(Well technically a few outside util methods are called as well...)
"""
def coplanarizeJoints(chainEnd, chainRoot, plane, forwardAxis = mayaMathUtil.Axis(axis=0), rotationAxis = mayaMathUtil.Axis(axis=2)):    
    if(chainRoot is None or chainEnd is None or plane is None):
        return

    currJoint = chainEnd
    lastJoint = None
    
    while currJoint:        
        currChildren = mayaUtil.getObjectChildren(currJoint)
        
        #unparent all children so this joint can move safely without affecting children
        if(currChildren is not None):
            for child in currChildren:
                cmds.parent(child, world=True)
                
        oldPos = mayaUtil.getJointWorldPosition(currJoint)
        oldOrient = mayaUtil.getObjectWorldOrientation(currJoint)
                
        #cmds.makeIdentity(currJoint, apply=True, translate=True, rotate=True, scale=True, jointOrient=True)
        
        #project the joint to the plane
        newPos = mayaMathUtil.closestPointOnPlane(plane=plane, point=oldPos)
                        
        cmds.xform(currJoint, absolute=True, worldSpace=True, translation=[newPos.x, newPos.y, newPos.z])
                                
        #now orient the joint
        #don't orient if this is the last child in the chain and it has children of its own
        if(lastJoint is not None or (lastJoint is None and currChildren is None)):
            deleteAimTarget = False
            aimTarget = lastJoint
            
            #if no lastJoint, this is the last child in the joint chain so project its previous aim direction to a point on the plane and aim it in that direction to keep it approximately the same
            #there's probably a more mathematically correct way to do this but whatever...
            if(lastJoint is None):
                deleteAimTarget = True
                aimLocation = mayaMathUtil.closestPointOnPlane(plane=plane, point=oldPos + mayaMathUtil.eulerToDirectionVector(oldOrient, forwardAxis) * 10)
                aimTarget = cmds.spaceLocator()
                cmds.xform(aimTarget, worldSpace=True, absolute=True, translation=[aimLocation.x, aimLocation.y, aimLocation.z])
            
            aimVector = mayaMathUtil.forwardVector(forwardAxis)
            turnVector = mayaMathUtil.forwardVector(rotationAxis)
    
            #not sure how else to do this easily, the idea is taken from Comet Joint Orient
            tempAimConstraint = cmds.aimConstraint(aimTarget, currJoint, weight=1, aimVector=[aimVector.x, aimVector.y, aimVector.z], upVector=[turnVector.x, turnVector.y, turnVector.z], worldUpVector=[plane.normal().x, plane.normal().y, plane.normal().z], worldUpType="vector")        
            cmds.delete(tempAimConstraint)
            
            #delete the temporary locator we created if lastJoint was None
            if(deleteAimTarget):
                cmds.delete(aimTarget)
        
        cmds.joint(currJoint, edit=True, zeroScaleOrient=True)
                
        if(currChildren is not None):
            for child in currChildren:
                cmds.parent(child, currJoint)
                cmds.makeIdentity(child, apply=True, jointOrient=False)
        
        if(currJoint == chainRoot):
            return
            
        lastJoint = currJoint
        currJoint = mayaUtil.getObjectParent(currJoint)

    return


class CoplanarJointOrient(object):
    def __init__(self):
        #for the UI
        self.joint1 = None
        self.joint2 = None
        
        #the top most ancestor in the chain of joints being coplanarized
        self.chainRoot = None
        
        #the last descendant in the chain of joints being coplanarized
        self.chainEnd = None
        
        #which axis is used as the forward aim axis of a joint
        self.aimAxis = None      
        
        #which axis does the joint turn along by default, the plane normal controls this
        self.turnAxis = None
        
        self.advancedPlaneMode = PlaneMode.AdvancedPlaneMode.AdvancedPlaneMode(self)
        self.axisAlignedPlaneMode = PlaneMode.AxisAlignedPlaneMode.AxisAlignedPlaneMode(self)
        self.automatic3PointPlaneMode = PlaneMode.Automatic3PointPlaneMode.Automatic3PointPlaneMode(self)
        self.automaticOrientedPlaneMode = PlaneMode.AutomaticOrientedPlaneMode.AutomaticOrientedPlaneMode(self)
        
        self.currentPlaneMode = None

        self.previewPlaneSetting = None
        self.previewJointsSetting = None

        #preview plane should be deleted on cancel or when the tick mark is turned off
        self.previewPlane = None
        self.previewJoints = None
        
        self.setupUI()
        self.loadSettings()
                
    def setupUI(self):
        self.mainWindow = cmds.window(title="Coplanar Joint Orient Tool", sizeable=True, maximizeButton=False, minimizeButton=False, width=WINDOW_WIDTH, resizeToFitChildren=True)

        mainColLayout = cmds.columnLayout(width=WINDOW_WIDTH)

        #end joints    
        endJoints_layout = cmds.formLayout(parent=mainColLayout, width=WINDOW_WIDTH)
                    
        endJoints_label = cmds.text(label="Joint chain to orient")
        self.endJoints_instructions = cmds.text(label=SELECTION_MESSAGE, backgroundColor=[1, 0, 0])

        self.joint1 = MayaUIValue.JointValue.JointValue(label="Joint 1", parentUI=endJoints_layout)
        self.joint2 = MayaUIValue.JointValue.JointValue(label="Joint 2", parentUI=endJoints_layout)
        
        self.joint1.onChangeFunc = functools.partial(CoplanarJointOrient.onJointNameChanged, self)
        self.joint2.onChangeFunc = functools.partial(CoplanarJointOrient.onJointNameChanged, self)

        cmds.formLayout(endJoints_layout, edit=True, attachForm=[ (endJoints_label, "left", 0),
                                                                    (endJoints_label, "top", 0),
                                                                    
                                                                    (self.endJoints_instructions, "left", 0), 
                                                                    (self.endJoints_instructions, "top", 20),
                                                                    
                                                                    (self.joint1.rootUI, "left", 0),
                                                                    (self.joint1.rootUI, "top", 40),
                                                                    
                                                                    (self.joint2.rootUI, "left", 0),
                                                                    (self.joint2.rootUI, "top", 65)
                                                                    ])
        
                        
        #options
        options_layout = cmds.formLayout(parent=mainColLayout, width=WINDOW_WIDTH)
        options_separator = cmds.separator(style="in", height=3)
        
        options_label = cmds.text(label="Options")
        
        self.aimAxis = MayaUIValue.AxisValue.AxisValue(label="Aim Axis", parentUI=options_layout)
        self.turnAxis = MayaUIValue.AxisValue.AxisValue(label="Turn Axis", parentUI=options_layout)
        self.aimAxis.onChangeFunc = functools.partial(CoplanarJointOrient.onAimAxisChanged, self)
        self.turnAxis.onChangeFunc = functools.partial(CoplanarJointOrient.onTurnAxisChanged, self)
        
        self.previewPlaneSetting = MayaUIValue.BoolValue.BoolValue(label="Preview Plane", parentUI=options_layout)
        self.previewPlaneSetting.onChangeFunc = functools.partial(CoplanarJointOrient.onPreviewPlaneChanged, self)
        
        #TODO: I currently am not displaying a preview of joints yet
        #self.previewJointsSetting = MayaUIValue.BoolValue.BoolValue(label="Preview Joints", parentUI=options_layout)
        
        cmds.formLayout(options_layout, edit=True, attachForm=[(options_separator, "left", 0),
                                                                    (options_separator, "top", 5),
                                                                    (options_separator, "right", 0),
                                                                 
                                                                    (options_label, "left", 0),
                                                                    (options_label, "top", 10),
                                                                    
                                                                    (self.aimAxis.rootUI, "left", 0),
                                                                    (self.aimAxis.rootUI, "top", 30),
                                                                    
                                                                    (self.turnAxis.rootUI, "left", 0),
                                                                    (self.turnAxis.rootUI, "top", 50),
                                                                                                                                        
                                                                    (self.previewPlaneSetting.rootUI, "right", 20),
                                                                    (self.previewPlaneSetting.rootUI, "top", 30),
                                                                    
                                                                    #(self.previewJointsSetting.rootUI, "right", 20),
                                                                    #(self.previewJointsSetting.rootUI, "top", 50),
                                                                    ])
        
        #plane mode
        planeMode_layout = cmds.formLayout(parent=mainColLayout, width=WINDOW_WIDTH)        
        planeMode_separator = cmds.separator(style="in", height=3)
        
        planeMode_label = cmds.text(label="Plane Mode")                
                        
        planeMode_autoPos = cmds.button(label="Automatic from positions", width = WINDOW_WIDTH * .4, height = 30, 
                                        command = functools.partial(CoplanarJointOrient.updatePlaneMode, self, self.automatic3PointPlaneMode))
        planeMode_autoOrient = cmds.button(label="Automatic from orientations", width = WINDOW_WIDTH * .4, height = 30, 
                                           command = functools.partial(CoplanarJointOrient.updatePlaneMode, self, self.automaticOrientedPlaneMode))
        planeMode_axisAligned = cmds.button(label="Axis aligned", width = WINDOW_WIDTH * .4, height = 30, 
                                            command = functools.partial(CoplanarJointOrient.updatePlaneMode, self, self.axisAlignedPlaneMode))
        planeMode_advanced = cmds.button(label="Advanced", width = WINDOW_WIDTH * .4, height = 30, 
                                         command = functools.partial(CoplanarJointOrient.updatePlaneMode, self, self.advancedPlaneMode))
                
        cmds.formLayout(planeMode_layout, edit=True, attachForm=[ (planeMode_separator, "left", 0),
                                                                    (planeMode_separator, "top", 5),
                                                                    (planeMode_separator, "right", 0),
                                                                   
                                                                    (planeMode_label, "left", 0),
                                                                    (planeMode_label, "top", 10),
                                                                   
                                                                    (planeMode_autoPos, "left", WINDOW_WIDTH * .05),
                                                                    (planeMode_autoPos, "top", 30),
                                                                    
                                                                    (planeMode_autoOrient, "right", WINDOW_WIDTH * .05), 
                                                                    (planeMode_autoOrient, "top", 30),
                                                                    
                                                                    (planeMode_axisAligned, "left", WINDOW_WIDTH * .05),
                                                                    (planeMode_axisAligned, "top", 65),
                                                                    
                                                                    (planeMode_advanced, "right", WINDOW_WIDTH * .05),
                                                                    (planeMode_advanced, "top", 65)
                                                                    ])
        
        #auto position plane options
        autoPosOpts_layout = cmds.formLayout(parent=mainColLayout, width=WINDOW_WIDTH, visible=False)
        self.automatic3PointPlaneMode.setupUI(autoPosOpts_layout)
        
        #auto orientation plane options
        autoOrientOpts_layout = cmds.formLayout(parent=mainColLayout, width=WINDOW_WIDTH, visible=False)
        self.automaticOrientedPlaneMode.setupUI(autoOrientOpts_layout)
        
        #axis aligned plane options
        axisAlignedOpts_layout = cmds.formLayout(parent=mainColLayout, width=WINDOW_WIDTH, visible=False)
        self.axisAlignedPlaneMode.setupUI(axisAlignedOpts_layout)
        
        #advanced plane options
        advancedOpts_layout = cmds.formLayout(parent=mainColLayout, width=WINDOW_WIDTH, visible=False)
        self.advancedPlaneMode.setupUI(advancedOpts_layout)
        
        #bottom buttons
        cmds.text(parent=mainColLayout, label="") #Hack label to add space  
        self.applyButton = cmds.button(parent=mainColLayout, width=WINDOW_WIDTH, label="Apply", height=60,
                                       command = functools.partial(CoplanarJointOrient.apply, self))

        cmds.showWindow(self.mainWindow)
        
    def loadSettings(self):
        #For now just set things to default values
        self.aimAxis.setValue(mayaMathUtil.Axis(axis=0, negative=False))
        self.turnAxis.setValue(mayaMathUtil.Axis(axis=2, negative=False))
        
        self.previewPlaneSetting.setValue(True)
        #self.previewJointsSetting.setValue(True)
        
        self.axisAlignedPlaneMode.normalAxis.setValue(mayaMathUtil.Axis())
        self.axisAlignedPlaneMode.worldOffset.setValue(om.MVector())
        
        self.advancedPlaneMode.planeNormalMode.setValue(MayaUIValue.NormalModeValue.NormalModeValue.PLANE_NORMAL_MODE_VECTOR)
        self.advancedPlaneMode.planePosition.setValue(om.MVector())
        self.advancedPlaneMode.planeNormalVector.setValue(om.MVector(om.MVector.kXaxisVector))
        self.advancedPlaneMode.planeNormalPoint0.setValue(om.MVector())
        self.advancedPlaneMode.planeNormalPoint1.setValue(om.MVector())
        self.advancedPlaneMode.planeNormalPoint2.setValue(om.MVector())
        
        self.updatePlaneMode(self.automatic3PointPlaneMode, None)
        
    def onAimAxisChanged(self, value):
        #see if turn axis is same, and force it to change
        if(self.turnAxis.value.axis == value.axis):
            self.turnAxis.setValue(mayaMathUtil.Axis(axis = (0 if value.axis != 0 else 1), negative=self.turnAxis.value.negative))
    
    def onTurnAxisChanged(self, value):
        #see if aim axis is same, and force it to change
        if(self.aimAxis.value.axis == value.axis):
            self.aimAxis.setValue(mayaMathUtil.Axis(axis = (0 if value.axis != 0 else 1), negative=self.aimAxis.value.negative))
        
        self.advancedPlaneMode.planeNormalVector.forwardDirectionAxis = value
        self.automaticOrientedPlaneMode.planeNormalVector.forwardDirectionAxis = value
    
    def onJointNameChanged(self, unusedChange):                
        if(self.joint1.value is None or self.joint2.value is None):
            self.chainRoot = None
            self.chainEnd = None
        else:    
            if(mayaUtil.isDescendant(parent = self.joint1.value, child = self.joint2.value)):
                self.chainRoot = self.joint1.value
                self.chainEnd = self.joint2.value
            elif(mayaUtil.isDescendant(parent = self.joint2.value, child = self.joint1.value)):
                self.chainRoot = self.joint2.value
                self.chainEnd = self.joint1.value
            else:
                self.chainRoot = None
                self.chainEnd = None
                
        self.axisAlignedPlaneMode.coplanarizerChainUpdated()
        self.advancedPlaneMode.coplanarizerChainUpdated()
        self.automatic3PointPlaneMode.coplanarizerChainUpdated()
        self.automaticOrientedPlaneMode.coplanarizerChainUpdated()
                
        if(self.chainRoot is None or self.chainEnd is None):
            cmds.text(self.endJoints_instructions, edit=True, enableBackground=True)
            cmds.button(self.applyButton, edit=True, enable=False)
        else:
            cmds.text(self.endJoints_instructions, edit=True, enableBackground=False)
            cmds.button(self.applyButton, edit=True, enable=True)
            
    def onPreviewPlaneChanged(self, value):
        self.updatePreviewPlane()
            
    def updatePlaneMode(self, planeMode, unused):        
        if(self.currentPlaneMode == planeMode):
            return
        
        #hide advanced options UI
        if(self.currentPlaneMode is not None and self.currentPlaneMode.advancedSettingsUI is not None):
            cmds.layout(self.currentPlaneMode.advancedSettingsUI, edit=True, visible=False)
        
        self.currentPlaneMode = planeMode
        
        #show advanced options UI
        if(self.currentPlaneMode.advancedSettingsUI is not None):
            cmds.layout(self.currentPlaneMode.advancedSettingsUI, edit=True, visible=True)
            
        self.updatePreviewPlane()
            
    def planeUpdated(self, planeMode):        
        if(planeMode == self.currentPlaneMode):
            self.updatePreviewPlane()
            
    def apply(self, unused):        
        #This is where the magic happens.  FINALLY!!!!
        if(self.chainEnd is not None and self.chainRoot is not None):
            coplanarizeJoints(chainEnd=self.chainEnd, chainRoot=self.chainRoot, plane=self.currentPlaneMode.alignmentPlane, forwardAxis=self.aimAxis.value, rotationAxis=self.turnAxis.value)
    
    def updatePreviewPlane(self):
        self.deletePreviewPlane()
            
        if(self.previewPlaneSetting.value and self.currentPlaneMode is not None):
            self.previewPlane = createDebugVisualizerPlane(self.currentPlaneMode.alignmentPlane, self.currentPlaneMode.alignmentPlanePreviewLocation)
        else:
            self.previewPlane = None
    
    def cancel(self):
        self.deletePreviewPlane()
            
    def deletePreviewPlane(self):
        #delete current plane
        if(self.previewPlane is not None):
            try:
                #It's possible a new scene was opened while this window is still open and the preview plane no longer exists
                cmds.delete(self.previewPlane)
            except:
                pass


####### Main script #######
def main():
    #auto populate selected joints fields
    selection = cmds.ls(orderedSelection=True, type="joint")
    
    tool = CoplanarJointOrient()

    #automatically populate selections
    if(len(selection) > 0):
        tool.joint1.setValue(selection[0])
                
    if(len(selection) > 1):
        tool.joint2.setValue(selection[1])
                
    #set up so the cancel button is auto pressed on window close
    cmds.scriptJob(uiDeleted=[tool.mainWindow, functools.partial(CoplanarJointOrient.cancel, tool)])