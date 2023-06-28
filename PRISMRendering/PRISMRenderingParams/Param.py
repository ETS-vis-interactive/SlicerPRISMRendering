# Base class for every parameters
import vtk, qt, ctk, slicer

#Base class for shaders' parameters

class Param:
  
  def __init__(self, name,display_name):
    self.name = name
    self.display_name = display_name

  def setUniform(self, CustomShader):
    return