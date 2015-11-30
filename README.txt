# CoplanarJointOrient
Maya script to help riggers fix joints with a click of a button and make the animator's job down the pipeline easier.

# Coplanar joint orient tool 0.9.0
Ilya Seletsky 2015

# Install instructions
Requires Maya not Maya LT since this is written in Python, unless in the future Autodesk adds Python scripting to LT.  (I sure hope they do ;D)
I personally have tested this on Maya 2016 but I think it should work on some older versions if you don't go too far back.

The steps to set this up are the same as for other plugins so I'll keep this brief.

Copy into scripts folder for Maya.
Make sure these files copied into the scripts folder are contained in a folder called CoplanarJointOrient.
On Windows, one example of a scripts folder is C:\Users\<yourUserNameGoesHere>\Documents\maya\scripts\CoplanarJointOrient

Run this command in the script editor or make a shelf button to easily bring up the UI any time:
import CoplanarJointOrient.CoplanarJointOrient
CoplanarJointOrient.CoplanarJointOrient.main()

# Usage
Select two joints in the skeleton, one of which is a descendant of the other in the parent heirarchy.  The joints between these two will be oriented, including the selected joints.
It won't reorient the last child if that child has its own children, but it will reposition it so its aligned to the plane.  Its children should follow.

If you enable Display->Transform Display->Local Rotation Axes on the joints of interest you will be able to visualize their orientations better.
Aim axis determines which joint orientation axis faces the child.  X is default since I'm working primarily with Unreal Engine 4.  Depending on the body part you may need to toggle the negative setting if the original joints face away from their child rather than towards it.
Turn axis determines the primary axis along which the joint turns.  This is the axis that will reorient to face the alignment plane.  Z is the default.

Select a plane mode.  The two automatic modes should be great for most situations where the body part is oriented arbitrarily in space.

## Automatic from positions:
This is great for things like arms, legs, or fingers.  Anything that is about 3 to 5 joints in length and are already approximately coplanar but not quite.
This will keep the 2 end joints in the same location and move around the joints in between to be coplanar.  All joints will be reoriented.

If you're familiar with how 3D math works, it derives a plane from 3 points.  2 of the points are the end joints.  And the third point is the centroid of the joints between the two end joints.

## Automatic from orientations:
This is great for things that got a bit crooked position-wise but are all facing approximately the same direction.
From positions mode won't work too well here since the final orientation will be way off.
This will keep the 2 end joints in the same location but it will determine the plane orientation from the current average orientation of all joints.
It will also move the joints between the 2 end joints.

If you're familiar with how 3D math works, it derives a plane from 2 points and a normal vector.  It's very similar to how you derive a plane from 3 points, only you use 2 points to determine one vector, and you already have the second vector from the normal.  You find the cross product of the cross product of those two vectors to get the correct plane orientation.

## Axis Aligned
This is great for things like spines or other already axis aligned body parts.
This is a nice quick way to fix odd issues and in my opinion is much easier to use than the built in joint orient tool since it's guranteed to have correct results without playing around with up vectors and other settings.

(In fact the up vector is determined from the plane orientation and this is how the turn axis is oriented to face the plane.)

## Advanced
This is a way to create an alignment plane if you really know what your're doing.
Using advanced mode you can have more fine grained control of how the alignment plane is computed for orienting the joints.
The automatic modes described above are simply derived from advanced mode, but compute the values for you automatically based on the end joint selections.

Automatic from positions sets plane position from the position of the root-most joint in the chain.
It sets plane mode to 3 point.
It sets point 1 to the location of the root-most joint.
Point 2 is computed from the centroid of all joints in between the root and end.
Point 3 is set to the location of the child-most joint.

Automatic from orientations sets plane position from the position of the root-most joint in the chain.
It sets plane mode to 2 point and direction vector.
It sets point 1 to the location of the root-most joint.
Point 2 is set to the location of the child-most joint.
Direction is computed from the average facing direction of all joints between the root and end.

You can actually set direction vector and other positions to arbitrary values not related to any of the joints you are trying to orient, such as a random box that may exist in the scene.

# TODO (known issues):
-Preview plane size setting (Width and Height)
-Handle when scene is closed while window open to reset things if possible
-Make the preview plane creation somehow not contribute to the undo history if possible or find a different way to display a preview plane
-Save settings between runs.
-Fix window not shrinking properly when switching between plane modes.
-Figure out what else crashes

# Stretch goals:
-Joint preview.  Preview of how the joints will be oriented in real time without hitting apply button.
-Interactive plane mode.  Move a plane around in real time
-See if I can make UI more intuitive/self documenting and with a bunch of pretty pictures
-Auto compute preview plane size and position based on selected joints.
-Optimize UI change code to prevent unnecessary updates.  Not a real huge issue.
-Redo UI with pyQt to make the UI be more versatile and resizeable and strings localizeable, etc...