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

"""
Wrapper around some value and its associated UI, and makes the two stay in sync
"""
class ValueBase(object):
    def __init__(self):        
        self.value = None
        self.rootUI = None
        self.onChangeFunc = None
                
    def setValue(self, value):
        pass
    
    def callChangeFunc(self):
        if(self.onChangeFunc is not None):
            self.onChangeFunc(self.value)
            
    def setEnabled(self, enabled):
        pass