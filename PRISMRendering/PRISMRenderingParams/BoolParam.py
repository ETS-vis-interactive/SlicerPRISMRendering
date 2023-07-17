from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' boolean parameters

class BoolParam(Param):
  
  def __init__(self, name, display_name, defaultValue, optionalWidgets = []):
    Param.__init__(self, name, display_name)
    self.defaultValue = defaultValue
    self.value = defaultValue
    self.optionalWidgets = optionalWidgets
    self.widget = None

  def SetupGUI(self, widgetClass):
      addOptionCheckBox = qt.QCheckBox(self.display_name)
      addOptionCheckBox.setObjectName(widgetClass.CSName + self.name)
      addOptionCheckBox.toggled.connect(lambda value : widgetClass.logic.onCustomShaderParamChanged(value, self) )
      addOptionCheckBox.toggled.connect(lambda _,cbx = addOptionCheckBox, CSName = widgetClass.CSName : widgetClass.logic.enableOption(self, checkBox = cbx, CSName = CSName))     
      addOptionCheckBox.toggled.connect(lambda : self.updateParameterNodeFromGUI(widgetClass))
      addOptionCheckBox.setParent(widgetClass.ui.customShaderParametersLayout)
      if self.value == 1:
        addOptionCheckBox.setChecked(True)
      self.widget = addOptionCheckBox

      return addOptionCheckBox, self.name
  
  def setValue(self, value):
    if int(value) == 0 or value == 1:
      self.value = int(value)
    else:
      self.value = 0

  def setUniform(self, CustomShader):
    super(BoolParam, self).setUniform(CustomShader)
    CustomShader.shaderUniforms.SetUniformi(self.name, self.value)

  def updateGUIFromParameterNode(self, widgetClass, caller = None, event = None):
    parameterNode = widgetClass.logic.parameterNode

    value = parameterNode.GetParameter(self.widget.name)
    if value != '' :
      checked = (int(value) != 0)
      self.widget.setChecked(checked)
    
  def removeGUIObservers(self):
    self.widget.toggled.disconnect(self.updateParameterNodeFromGUI)

  def updateParameterNodeFromGUI(self, widgetClass):
      parameterNode = widgetClass.logic.parameterNode
      if widgetClass.ui.imageSelector.currentNode() is None:
        return 
      parameterNode.SetParameter(self.widget.name, "1") if self.widget.checked else parameterNode.SetParameter(self.widget.name, "0")
      
  def addGUIObservers(self, widgetClass):
    self.widget.toggled.connect(lambda value, w = self.widget : self.updateParameterNodeFromGUI(widgetClass, value))
    