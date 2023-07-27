from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' range parameters

class RangeParam(Param):
  
  def __init__(self, name, display_name, range, default_value = None):
    Param.__init__(self, name, display_name)
    self.range = range
    if default_value == None:
      self.min = range[0]
      self.max = range[1]
      self.defaultValue = [self.min, self.max]
    else:
      self.min = default_value[0]
      self.max = default_value[1]
      self.defaultValue = [self.min, self.max]
    self.widget = None

  def SetupGUI(self, widgetClass):
    label = qt.QLabel(self.display_name)
    label.setMinimumWidth(80)
    slider = ctk.ctkRangeWidget()
    slider.minimum = self.range[0]
    slider.minimumValue = self.min
    slider.maximum = self.range[1]
    slider.maximumValue = self.max
    slider.singleStep = ( (slider.maximum - slider.minimum) * 0.01 )
    slider.setObjectName(widgetClass.CSName + self.name)
    slider.setParent(widgetClass.ui.customShaderParametersLayout)
    slider.valuesChanged.connect(lambda min, max : widgetClass.logic.onCustomShaderParamChanged([min, max], self) )
    slider.valuesChanged.connect(lambda : self.updateParameterNodeFromGUI(widgetClass))
    self.widget = slider
    self.label = label
    self.updateGUIFromParameterNode(widgetClass)
    return slider, label, self.name
  
  def setValue(self, value, updateGUI = False):
    if isinstance(value, str):
      parts = value.split(',')
      value = [float(parts[0]), float(parts[1])]
    else:
      value = [float(value[0]), float(value[1])]
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
    if updateGUI:
      self.updateGUIFromValue()

  def getValue(self):
    return [self.min, self.max]

  def setRange(self, range):
    self.range = range
    self.min = range[0]
    self.max = range[1]

  def setUniform(self, CustomShader):
    super(RangeParam, self).setUniform(CustomShader)
    CustomShader.shaderUniforms.SetUniformf(self.name + "Min", self.min)
    CustomShader.shaderUniforms.SetUniformf(self.name + "Max", self.max)

  def updateGUIFromParameterNode(self, widgetClass, caller = None, event = None):
    parameterNode = widgetClass.logic.parameterNode
    value = parameterNode.GetParameter(self.widget.name)
    if value != '' :
      self.setValue(value)
      self.setUniform(widgetClass.logic.customShader[widgetClass.logic.shaderIndex])
    
  def removeGUIObservers(self):
    self.widget.valuesChanged.disconnect(self.updateParameterNodeFromGUI)

  def updateParameterNodeFromGUI(self, widgetClass):
      
      parameterNode = widgetClass.logic.parameterNode
      oldModifiedState = parameterNode.StartModify()
      parameterNode.SetParameter(self.widget.name, str(self.widget.minimumValue) + ',' + str(self.widget.maximumValue))
      parameterNode.EndModify(oldModifiedState)

  def addGUIObservers(self, widgetClass):
    self.widget.valuesChanged.connect(lambda : self.updateParameterNodeFromGUI(widgetClass))

  def updateGUIFromValue(self):
    self.widget.minimumValue = self.min
    self.widget.maximumValue = self.max
