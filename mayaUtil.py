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
import mayaMathUtil

import math

"""
Gets the first selected object
"""
def getFirstSelectedObject():
    selections = cmds.ls(orderedSelection=True, type="joint")
    
    if(len(selections) > 0):
        return selections[0]
    else:
        return None

"""
Name of an object's parent or None if no parent
"""
def getObjectParent(joint):
    if(joint is None):
        return None

    parents = cmds.listRelatives(joint, parent=True)

    if(parents):
        return parents[0]
    else:
        return None
       
"""
Name of an object's children as a list, or empty if no children
"""
def getObjectChildren(joint):
    if(joint is None):
        return None

    return cmds.listRelatives(joint, children=True)

"""
Returns whether or not a child is a descendant of a parent object
"""
def isDescendant(child, parent):
    if(parent is None or child is None or parent == child):
        return False
    
    currJoint = child

    while currJoint:
        currJoint = getObjectParent(currJoint)

        if(currJoint == parent):
            return True

    return False

"""
Returns a list of object names between the root and end of a parent heirarchy in order from end to root.
Doesn't include end and root.
"""
def getInnerParentChain(parent, child):
    if(parent is None or child is None or parent == child):
        return None
    
    currNode = getObjectParent(child)
    
    res = []

    while currNode and currNode != parent:
        res.append(currNode)    
        currNode = getObjectParent(currNode)
        
    return res

"""
Returns a list of object names between the root and end of a parent heirarchy in order from end to root.
Includes end and root.
"""
def getWholeParentChain(parent, child):
    if(parent is None or child is None or parent == child):
        return None
        
    currNode = getObjectParent(child)
    
    res = [child]

    while currNode and currNode != parent:
        res.append(currNode)
        currNode = getObjectParent(currNode)
        
    res.append(parent)
    
    return res

def getAverageNodePositions(nodes):
    centroid = om.MVector()
    numPoints = 0
    
    for node in nodes:
        position = cmds.xform(node, query=True, translation=True, absolute=True, worldSpace = True)
        centroid.x += position[0]
        centroid.y += position[1]
        centroid.z += position[2]
        numPoints += 1
        
    if(numPoints > 0):
        centroid /= numPoints
        
    return centroid

def getAverageNodeDirectionVector(nodes, axis = mayaMathUtil.Axis()):
    averageDir = om.MVector()
    
    for node in nodes:
        orientation = mayaMathUtil.eulerToDirectionVector(getObjectWorldOrientation(node), axis)
        averageDir.x += orientation[0]
        averageDir.y += orientation[1]
        averageDir.z += orientation[2]
                    
    averageDir.normalize()
    
    #force a direction vector if one isn't found
    if(averageDir.x == 0 and averageDir.y == 0 and averageDir.z == 0):
        averageDir.x = 1
                    
    return averageDir

def isJoint(node):
    if(node is None):
        return None
    
    return cmds.objectType(node, isAType="joint")

"""
World position of a joint
"""
def getJointWorldPosition(joint):
    if(joint is None):
        return None

    jointPos = cmds.joint(joint, query=True, position=True, absolute=True)

    return om.MVector(jointPos[0], jointPos[1], jointPos[2])

"""
Returns an MEulerRotation representing the world orientation of a joint
"""
def getJointWorldOrientation(joint):
    if(joint is None):
        return None

    #small hack to create a duplicate joint so we don't mess with the original to get its world orientation
    #TODO: turns out I might not need to do this?  Since world orientation is object world transformed by joint orientation.  Investigate later...
    dupJoint = cmds.duplicate(joint, upstreamNodes=False, inputConnections=False, parentOnly=True)

    if(getObjectParent(dupJoint) is not None):
        cmds.parent(dupJoint, world=True)

    jointRot = cmds.joint(dupJoint, query=True, position=False, orientation=True)
    jointRotOrder = mayaMathUtil.nodeRotOrderToEulerRotOrder(cmds.joint(dupJoint, query=True, rotationOrder=True, absolute=True))

    cmds.delete(dupJoint)

    return om.MEulerRotation(math.radians(jointRot[0]), math.radians(jointRot[1]), math.radians(jointRot[2]), jointRotOrder)

"""
Gets an MEulerRotation representing the world orientation of an object
"""
def getObjectWorldOrientation(node):
    if(node is None):
        return None
        
    jointRot = getJointWorldOrientation(node) if isJoint(node) else om.MEulerRotation()
    
    rot = cmds.xform(node, query=True, translation=False, rotation=True, absolute=True)
    rotOrder = mayaMathUtil.nodeRotOrderToEulerRotOrder(cmds.xform(node, query=True, rotateOrder=True, absolute=True))
    
    objRot = om.MEulerRotation(math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2]), rotOrder)
    
    return objRot * jointRot