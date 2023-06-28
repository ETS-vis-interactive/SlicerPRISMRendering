from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer

#Class for shaders' point parameters

class FourFParam(Param):
  
  def __init__(self, name, display_name, defaultValue):
    Param.__init__(self, name, display_name)
    if isinstance(defaultValue, dict):
      self.defaultValue = defaultValue
    else:
      self.defaultValue = {'x': defaultValue[0], 'y': defaultValue[1], 'z': defaultValue[2], 'w': defaultValue[3]}
    self.value = self.defaultValue

  def SetupGUI(self, widgetClass):
    targetPointButton = qt.QPushButton("Initialize " + self.display_name)
    targetPointButton.setToolTip( "Place a markup" )
    targetPointButton.setObjectName(widgetClass.CSName + self.name)
    targetPointButton.clicked.connect(lambda : widgetClass.logic.setPlacingMarkups(self.name,"markup" + self.name,  targetPointButton,  interaction = 1))
    targetPointButton.clicked.connect(lambda value, w = targetPointButton : widgetClass.updateParameterNodeFromGUI(value, w))
    targetPointButton.setParent(widgetClass.ui.customShaderParametersLayout)
    return targetPointButton, self.name

  def setValue(self, value):
    if isinstance(value, dict):
      self.value = value
    else:
      self.value['x'] = value[0]
      self.value['y'] = value[1]
      self.value['z'] = value[2]
      self.value['w'] = value[3]

  def toList(self):
    return [self.value['x'], self.value['y'], self.value['z'], self.value['w']]
  
  def setUniform(self, CustomShader):
    x = self.value['x']
    y = self.value['y']
    z = self.value['z']
    w = self.value['w']
    CustomShader.shaderUniforms.SetUniform4f(self.name, [x, y, z, w])