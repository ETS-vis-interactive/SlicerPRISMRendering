from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' point parameters

class FourFParam(Param):
  
  def __init__(self, name, display_name, defaultValue):
    Param.__init__(self, name, display_name)
    if isinstance(defaultValue, dict):
      self.defaultValue = defaultValue
    else:
      try :
        self.defaultValue = {'x': defaultValue[0], 'y': defaultValue[1], 'z': defaultValue[2], 'w': defaultValue[3]}
      except:
        self.defaultValue = {'x': defaultValue[0], 'y': defaultValue[1], 'z': defaultValue[2], 'w': 0}
    self.value = self.defaultValue
    self.widget = None

  def SetupGUI(self, widgetClass):
    if widgetClass.logic.customShader[widgetClass.logic.shaderIndex].customShaderPoints.pointIndexes.get("markup" + self.name) is None:
      targetPointButton = qt.QPushButton("Initialize " + self.display_name)
    else:
      targetPointButton = qt.QPushButton("Reset " + self.display_name)
    targetPointButton.setToolTip( "Place a markup" )
    targetPointButton.setObjectName(widgetClass.CSName + self.name)
    targetPointButton.clicked.connect(lambda : widgetClass.logic.customShader[widgetClass.logic.shaderIndex].customShaderPoints.setPlacingMarkups(self.name,"markup" + self.name,  targetPointButton,  interaction = 1))
    targetPointButton.clicked.connect(lambda : self.updateParameterNodeFromGUI(widgetClass))
    targetPointButton.setParent(widgetClass.ui.customShaderParametersLayout)
    self.widget = targetPointButton
    self.updateGUIFromParameterNode(widgetClass)
    return targetPointButton, self.name

  def setValue(self, value):
    if isinstance(value, dict):
      self.value = value
    else:
      self.value['x'] = value[0]
      self.value['y'] = value[1]
      self.value['z'] = value[2]
      try:
        self.value['w'] = value[3]
      except:
        self.value['w'] = 0
    pass

  def getValue(self):
    return self.value

  def toList(self):
    return [self.value['x'], self.value['y'], self.value['z'], self.value['w']]
  
  def setUniform(self, CustomShader):
    super(FourFParam, self).setUniform(CustomShader)
    x = self.value['x']
    y = self.value['y']
    z = self.value['z']
    w = self.value['w']
    CustomShader.shaderUniforms.SetUniform4f(self.name, [x, y, z, w])

  def updateGUIFromParameterNode(self, widgetClass, caller = None, event = None):
    parameterNode = widgetClass.logic.parameterNode
    value = parameterNode.GetParameter(self.widget.name)
    if value != '' :
      enabled = (int(value) != 0)
      self.widget.setEnabled(enabled)
    
  def removeGUIObservers(self):
    self.widget.clicked.disconnect(self.updateParameterNodeFromGUI)
    
  def updateParameterNodeFromGUI(self, widgetClass):
      parameterNode = widgetClass.logic.parameterNode
      oldModifiedState = parameterNode.StartModify()
      
      if widgetClass.ui.imageSelector.currentNode() is None:
        return 
      parameterNode.SetParameter(self.widget.name, "1") if self.widget.enabled else parameterNode.SetParameter(self.widget.name, "0")
      parameterNode.EndModify(oldModifiedState)
      
  def addGUIObservers(self, widgetClass):
    self.widget.clicked.connect(lambda : self.updateParameterNodeFromGUI(widgetClass))