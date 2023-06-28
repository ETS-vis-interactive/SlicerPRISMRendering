from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' boolean parameters

class BoolParam(Param):
  
  def __init__(self, name, display_name, defaultValue, optionalWidgets = []):
    Param.__init__(self, name, display_name)
    self.defaultValue = defaultValue
    self.value = defaultValue
    self.optionalWidgets = optionalWidgets

  def SetupGUI(self, widgetClass):
      addOptionCheckBox = qt.QCheckBox(self.display_name)
      addOptionCheckBox.setObjectName(widgetClass.CSName + self.name)
      addOptionCheckBox.toggled.connect(lambda value : widgetClass.logic.onCustomShaderParamChanged(value, self) )
      addOptionCheckBox.toggled.connect(lambda _,cbx = addOptionCheckBox, CSName = widgetClass.CSName : widgetClass.logic.enableOption(self, checkBox = cbx, CSName = CSName))     
      addOptionCheckBox.toggled.connect(lambda value, w = addOptionCheckBox : widgetClass.updateParameterNodeFromGUI(value, w))
      addOptionCheckBox.setParent(widgetClass.ui.customShaderParametersLayout)

      return addOptionCheckBox, self.name
  
  def setValue(self, value):
    if int(value) == 0 or value == 1:
      self.value = int(value)
    else:
      self.value = 0

  def setUniform(self, CustomShader):
    CustomShader.shaderUniforms.SetUniformi(self.name, self.value)