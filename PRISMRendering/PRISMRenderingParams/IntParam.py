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
    self.widget = None
    self.label = None

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
    slider.valueChanged.connect(lambda value : widgetClass.logic.volumes[widgetClass.logic.volumeIndex].onCustomShaderParamChanged(value, self) )
    slider.valueChanged.connect(lambda : self.updateParameterNodeFromGUI(widgetClass))
    slider.setParent( widgetClass.ui.customShaderParametersLayout )
    self.widget = slider
    self.label = label

    self.updateGUIFromParameterNode(widgetClass)
    
    return slider, label, self.name
  
  def setValue(self, value, updateGUI = False):
    if value < self.minValue:
      self.value = self.minValue
    elif value > self.maxValue:
      self.value = self.maxValue
    else:
      self.value = int(value)
    if updateGUI:
      self.updateGUIFromValue()
  
  def getValue(self):
    return self.value

  def setUniform(self, CustomShader):
    super(IntParam, self).setUniform(CustomShader)
    CustomShader.shaderUniforms.SetUniformi(self.name, self.value)

  def updateGUIFromParameterNode(self, widgetClass, caller = None, event = None):
    parameterNode = widgetClass.logic.parameterNode
    value = parameterNode.GetParameter(self.widget.name)
    if value != '' :
      value = int(value)
      self.setValue(value)
      self.setUniform(widgetClass.logic.volumes[widgetClass.logic.volumeIndex].customShader[widgetClass.logic.volumes[widgetClass.logic.volumeIndex].shaderIndex])
    
  def removeGUIObservers(self):
    self.widget.valueChanged.disconnect(self.updateParameterNodeFromGUI)

  def updateParameterNodeFromGUI(self, widgetClass):
      
      parameterNode = widgetClass.logic.parameterNode
      oldModifiedState = parameterNode.StartModify()
      
      if widgetClass.ui.imageSelector.currentNode() is None:
        return 
      parameterNode.SetParameter(self.widget.name, str(self.widget.value))
      parameterNode.EndModify(oldModifiedState)
      
  def addGUIObservers(self, widgetClass):
    self.widget.valueChanged.connect(lambda : self.updateParameterNodeFromGUI(widgetClass))

  def updateGUIFromValue(self):
    self.widget.setValue(self.value)

  def show(self):
    self.widget.show()
    self.label.show()

  def hide(self):
    self.widget.hide()
    self.label.hide()
    