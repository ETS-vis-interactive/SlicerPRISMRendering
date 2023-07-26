from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' transfer function parameters

class TransferFunctionParam(Param):

  def __init__(self, name, display_name, type, defaultValue = []):
    Param.__init__(self, name, display_name)
    self.type = type
    self.defaultValue = defaultValue