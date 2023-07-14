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
    self.widget = None
    self.label = None

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

    self.widget = slider
    self.label = label

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
    if self.isShaderUpdater:
      self.customShader.onParamUpdater()


  def updateGUIFromParameterNode(self, widgetClass, caller = None, event = None):
    parameterNode = widgetClass.logic.parameterNode
    value = parameterNode.GetParameter(self.widget.name)
    if value != '' :
      value = float(value)
      self.widget.setValue(value)
    
  def removeGUIObservers(self):
    self.widget.valueChanged.disconnect(self.updateParameterNodeFromGUI)

  def updateParameterNodeFromGUI(self, widgetClass, value):
      parameterNode = widgetClass.logic.parameterNode
      if widgetClass.ui.imageSelector.currentNode() is None:
        return 
      parameterNode.SetParameter(self.widget.name, str(self.widget.value))
      
  def addGUIObservers(self, widgetClass):
    self.widget.valueChanged.connect(lambda value, : self.updateParameterNodeFromGUI(widgetClass, value))