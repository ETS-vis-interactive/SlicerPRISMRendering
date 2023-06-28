from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' range parameters

class RangeParam(Param):
  
  def __init__(self, name, display_name, range):
    Param.__init__(self, name, display_name)
    self.range = range
    self.min = range[0]
    self.max = range[1]

  def SetupGUI(self, widgetClass):
    label = qt.QLabel(self.display_name)
    label.setMinimumWidth(80)
    slider = ctk.ctkRangeWidget()
    slider.minimum = self.range[0]
    slider.minimumValue = self.range[0]
    slider.maximum = self.range[1]
    slider.maximumValue = self.range[1]
    slider.singleStep = ( (slider.maximum - slider.minimum) * 0.01 )
    slider.setObjectName(widgetClass.CSName + self.name)
    slider.setParent(widgetClass.ui.customShaderParametersLayout)
    slider.valuesChanged.connect(lambda min, max : widgetClass.logic.onCustomShaderParamChanged([min, max], self) )
    slider.valuesChanged.connect(lambda value1, value2, w = slider : widgetClass.updateParameterNodeFromGUI([value1, value2], w))

    return slider, label, self.name
  
  def setValue(self, value):
    if value[0] < self.range[0]:
      self.min = self.range[0]
    elif value[0] > self.range[1]:
      self.min = self.range[1]
    else:
      self.min = value[0]
    if value[1] < self.range[0]:
      self.max = self.range[0]
    elif value[1] > self.range[1]:
      self.max = self.range[1]
    else:
      self.max = value[1]

  def setRange(self, range):
    self.range = range
    self.min = range[0]
    self.max = range[1]

  def setUniform(self, CustomShader):
    CustomShader.shaderUniforms.SetUniformf(self.name + "Min", self.min)
    CustomShader.shaderUniforms.SetUniformf(self.name + "Max", self.max)

