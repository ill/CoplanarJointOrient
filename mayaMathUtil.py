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

"""
Axis is used to track if something is on the x, y, or z axis and if it's pointing in the negative direction
"""
class Axis(object):
    def __init__(self, axis=0, negative=False):
        self.axis = axis
        self.negative = negative

"""
Given a rotation order string like xyz, zxy, etc...
Returns the EulerRotation rot order enum value
"""
def nodeRotOrderToEulerRotOrder(rotOrderStr="XYZ"):
    return vars(om.MEulerRotation)["k" + rotOrderStr.upper()]

"""
Returns a direction vector oriented by an MEulerRotation
You can also specify which axis is forward (default:0 or x)
0:x, 1:y, 2:z
negative is whether or not the vector faces in the negative direction of the axis
"""
def eulerToDirectionVector(orientation, axis=Axis()):
    if(orientation is None):
        return None
    
    return forwardVector(axis).rotateBy(orientation).normalize()
   
"""
Returns a normalized vector with just one axis pointing in some direction with magnitude 1
"""
def forwardVector(axis=Axis()):
    components = [0, 0, 0]
    components[axis.axis] = -1 if axis.negative else 1
    
    return om.MVector(components[0], components[1], components[2])

"""
Returns a normal for a plane that would be formed from 3 points
"""
def get3PointNormal(point0, point1, point2):
    if(point0 is None or point1 is None or point2 is None):
        return None
    
    return ((point2 - point1) ^ (point1 - point0)).normalize()

"""
Returns a plane that would be formed from 2 points and an additional normal vector
"""
def get2PointNormal(point0, point1, normal):
    if(point0 is None or point1 is None or normal is None):
        return None
        
    lineVec = point1 - point0
    
    #find the normal between the line formed by 2 points and the passed in normal
    firstNorm = (normal ^ lineVec).normalize()
            
    #now the cross between the line and firstNorm is the result    
    return (firstNorm ^ lineVec).normalize()    

"""
Gets a plane from 3 points in space
"""
def get3PointPlane(point0, point1, point2):
    if(point0 is None or point1 is None or point2 is None):
        return None
    
    plane = om.MPlane()
    plane.setPlane(get3PointNormal(point0, point1, point2), 0)
    
    return setPlaneWorldPosition(plane, point0)

"""
Gets the closest point on a plane to some other point in space.
AKA projecting a point onto a plane
"""
def closestPointOnPlane(point, plane):
    if(point is None or plane is None):
        return None
        
    return point - (plane.normal() * plane.distanceToPoint(point, signed=True))

"""
Takes an existing plane with a normal and puts it at some world position
"""
def setPlaneWorldPosition(plane, position):
    if(plane is None or position is None):
        return None

    plane.setPlane(plane.normal(), -plane.normal() * position)

    return plane
