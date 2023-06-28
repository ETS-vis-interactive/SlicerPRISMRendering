from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' float parameters

class FloatParam(Param):
  
  def __init__(self, name, display_name, defaultValue, min, max):
    Param.__init__(self, name, display_name)
    self.minValue = min
    self.maxValue = max
    self.defaultValue = defaultValue
    self.value = defaultValue

  def SetupGUI(self, widgetClass):
    label = qt.QLabel(self.display_name)
    label.setMinimumWidth(80)
    slider = ctk.ctkSliderWidget()
    slider.minimum = self.minValue
    slider.maximum = self.maxValue
    f = str(self.defaultValue)
    slider.setDecimals(f[::-1].find('.')+1)
    slider.singleStep = ( (slider.maximum - slider.minimum) * 0.01 )
    slider.setObjectName( widgetClass.CSName + self.name )
    slider.setValue( self.value )
    slider.valueChanged.connect(lambda value : widgetClass.logic.onCustomShaderParamChanged(value, self) )
    slider.valueChanged.connect(lambda value, w = slider : widgetClass.updateParameterNodeFromGUI(value, w))
    slider.setParent( widgetClass.ui.customShaderParametersLayout )

    return slider, label, self.name
  
  def setValue(self, value):
    if value < self.minValue:
      value = self.minValue
    elif value > self.maxValue:
      value = self.maxValue
    else:
      self.value = value

  def setUniform(self, CustomShader):
    CustomShader.shaderUniforms.SetUniformf(self.name, self.value)