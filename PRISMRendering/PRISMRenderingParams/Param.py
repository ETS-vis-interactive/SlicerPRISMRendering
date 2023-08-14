# Base class for every parameters
import vtk, qt, ctk, slicer

#Base class for shaders' parameters

class Param:
  
  def __init__(self, name,display_name):
    self.name = name
    self.display_name = display_name
    self.customShader = None
    self.isShaderUpdater = False

  def setUniform(self, CustomShader):
    if self.isShaderUpdater:
      self.customShader.onParamUpdater()
  
  def addCustomShaderUpdater(self, customShader):
    self.isShaderUpdater = True
    self.customShader = customShader

  def setValue(self, value, updateGUI = False):
    pass

  def getValue(self):
    return None
  
  def show(self):
    return
  
  def hide(self):
    return