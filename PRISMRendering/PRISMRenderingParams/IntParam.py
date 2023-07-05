from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' integer parameters

class IntParam(Param):
  
  def __init__(self, name, display_name, defaultValue, min, max):
    Param.__init__(self, name, display_name)
    self.minValue = int(min)
    self.maxValue = int(max)
    self.defaultValue = int(defaultValue)
    self.value = self.defaultValue

  def SetupGUI(self, widgetClass):
    label = qt.QLabel(self.display_name)
    label.setMinimumWidth(80)
    slider = ctk.ctkSliderWidget()
    slider.minimum = self.minValue
    slider.maximum = self.maxValue
    slider.singleStep = ( (slider.maximum - slider.minimum) * 0.05 )
    slider.setObjectName(widgetClass.CSName + self.name )
    slider.setDecimals(0)
    slider.setValue( self.value )
    slider.valueChanged.connect(lambda value : widgetClass.logic.onCustomShaderParamChanged(value, self) )
    slider.valueChanged.connect(lambda value, w = slider : widgetClass.updateParameterNodeFromGUI(value, w))
    slider.setParent( widgetClass.ui.customShaderParametersLayout )

    return slider, label, self.name
  
  def setValue(self, value):
    if value < self.minValue:
      self.value = self.minValue
    elif value > self.maxValue:
      self.value = self.maxValue
    else:
      self.value = int(value)

  def setUniform(self, CustomShader):
    CustomShader.shaderUniforms.SetUniformi(self.name, self.value)