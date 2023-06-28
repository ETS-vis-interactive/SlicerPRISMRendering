from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' transfer function parameters

class TransferFunctionParam(Param):

  def __init__(self, name, display_name, type, default_colors = []):
    Param.__init__(self, name, display_name)
    self.type = type
    self.default_colors = default_colors