import vtk, qt, ctk, slicer
from Resources.CustomShader import CustomShader
import imp
import importlib.util
import os, sys

class ModifyParamWidget():
  def __init__ (self):
    self.addParamCombo = qt.QComboBox()
    self.addParamCombo.addItem("Select type")
    self.addParamCombo.addItem("Integer")
    self.addParamCombo.addItem("Float")
    self.addParamCombo.addItem("Point")
    self.addParamCombo.setCurrentIndex(0)
    self.addParamCombo.activated.connect(self.onAddParamComboIndexChanged)
    self.addParamCombo.hide()

    self.addNameInput = qt.QLineEdit()
    self.addNameInput.textChanged.connect(self.addParamButtonState)
    self.addDisplayNameInput = qt.QLineEdit()
    self.addDisplayNameInput.textChanged.connect(self.addParamButtonState)
    self.addMinValueInput = qt.QDoubleSpinBox()
    self.addMinValueInput.setRange(-1000, 1000)
    self.addMinValueInput.valueChanged.connect(self.addParamButtonState)
    self.addMaxValueInput = qt.QDoubleSpinBox()
    self.addMaxValueInput.setRange(-1000, 1000)
    self.addMaxValueInput.valueChanged.connect(self.addParamButtonState)
    self.addDefaultValueInput = qt.QDoubleSpinBox()
    self.addDefaultValueInput.valueChanged.connect(self.addParamButtonState)
    self.addDefaultValueInput.setRange(-1000, 1000)

    self.addXInput = qt.QDoubleSpinBox()
    self.addXInput.setRange(-1000, 1000)
    self.addXInput.valueChanged.connect(self.addParamButtonState)
    self.addYInput = qt.QDoubleSpinBox()
    self.addYInput.setRange(-1000, 1000)
    self.addYInput.valueChanged.connect(self.addParamButtonState)
    self.addZInput = qt.QDoubleSpinBox()
    self.addZInput.setRange(-1000, 1000)
    self.addZInput.valueChanged.connect(self.addParamButtonState)
    self.addWInput = qt.QDoubleSpinBox()
    self.addWInput.setRange(-1000, 1000)
    self.addWInput.valueChanged.connect(self.addParamButtonState)

    self.addParamButton = qt.QPushButton("Add parameter")
    self.addParamButton.connect('clicked()', self.addParamButtonClicked)
    self.addedMsg = qt.QLabel()
    self.addedMsg.hide()
    
    self.addParamLayout = qt.QFormLayout()
    self.addParamLayout.addRow("Add parameter", self.addParamCombo)
    self.addParamLayout.addRow("", self.addedMsg)
    self.addParamLayout.itemAt(0,0).widget().hide()

    self.paramLayout = qt.QFormLayout()
    self.paramLayout.addRow("Name :", self.addNameInput)
    self.paramLayout.addRow("Display name :", self.addDisplayNameInput)
    self.paramLayout.addRow("Min value : ", self.addMinValueInput)
    self.paramLayout.addRow("Max value", self.addMaxValueInput)
    self.paramLayout.addRow("Default value :", self.addDefaultValueInput)
    self.paramLayout.addRow("x : ", self.addXInput)
    self.paramLayout.addRow("y : ", self.addYInput)
    self.paramLayout.addRow("z : ", self.addZInput)
    self.paramLayout.addRow("w : ", self.addWInput)
    self.paramLayout.addRow(self.addParamButton)
    self.clearLayout(self.paramLayout)

    self.shaderDisplayName = ""

  def resetLayout(self, layout) :
    """ Function to reset a specific layout.
    Args:
      layout(qLayout) : layout to reset
    """

    self.addParamCombo.setCurrentIndex(0)
    self.clearLayout(layout)
    layout.itemAt(0, 1).widget().clear()
    layout.itemAt(1, 1).widget().clear()
    for i in range(2, 8) :
      layout.itemAt(i, 1).widget().setValue(0)
  
  def clearLayout(self, layout) :
    """ Function to clear the widgets of a specific layout.
    Args:
      layout(qLayout) : layout to clear

    """
    for i in range(layout.count()): 
      layout.itemAt(i).widget().hide()

  def showLayout(self, layout, nb) :
    """ Function to show specific widgets of a layout.
    Args:
      layout(qLayout) : layout to reset
      nb (int) : range of the widgets

    """
    if nb  == 11 :
      for i in range(0, nb - 1): 
        layout.itemAt(i).widget().show()
    else:
      for i in range(0, 4): 
        layout.itemAt(i).widget().show()
      for i in range(10, 10 + nb): 
        layout.itemAt(i).widget().show()
    layout.itemAt(layout.count()-1).widget().show()

  def onAddParamComboIndexChanged(self, i):
    """ Sets the current parameter type according to the combobox input.
    Args:
      i(int) : index of the current input

    """
    self.clearLayout(self.paramLayout)
    self.addedMsg.hide()
    self.paramLayout.itemAt(0, 1).widget().clear()
    self.paramLayout.itemAt(1, 1).widget().clear()
    
    param = self.addParamCombo.currentText
    if param == "Integer" :
      self.showLayout(self.paramLayout, 11)
      for i in range(2, 5) :
        self.paramLayout.itemAt(i, 1).widget().setDecimals(0)
      self.addParamType = "shaderiParams"
    elif param == "Float" : 
      self.showLayout(self.paramLayout, 11)
      for i in range(2, 5) :
        self.paramLayout.itemAt(i, 1).widget().setDecimals(3)
      self.addParamType = "shaderfParams"
    elif param == "Point" :
      self.showLayout(self.paramLayout, 8)
      for i in range(5, 9) :
        self.paramLayout.itemAt(i, 1).widget().setDecimals(3)
      self.addParamType = "shader4fParams"

  def addParamButtonState(self):
    """ Function to enable or disable the button to change the parametters.
 
    """
    self.addParamButton.enabled = len(self.addNameInput.text) > 0 and len(self.addDisplayNameInput.text) > 0

  def addParamButtonClicked(self) :
    """ Function to get the current parameters and add them into a dictionnary.
    
    """
    name = self.paramLayout.itemAt(0, 1).widget().text
    displayName = self.paramLayout.itemAt(1, 1).widget().text

    if self.addParamType == "shaderiParams" :
      min_ = int(self.paramLayout.itemAt(2, 1).widget().value)
      max_ = int(self.paramLayout.itemAt(3, 1).widget().value)
      default = int(self.paramLayout.itemAt(4, 1).widget().value)
      newValue = {name : { 'displayName' : displayName, 'min' : min_, 'max' : max_, 'defaultValue' : default }}
    elif self.addParamType == "shaderfParams" :
      min_ = self.paramLayout.itemAt(2, 1).widget().value
      max_ = self.paramLayout.itemAt(3, 1).widget().value
      default = self.paramLayout.itemAt(4, 1).widget().value
      newValue = {name : { 'displayName' : displayName, 'min' : min_, 'max' : max_, 'defaultValue' : default }}
    else:
      x = self.paramLayout.itemAt(5, 1).widget().value
      y = self.paramLayout.itemAt(6, 1).widget().value
      z = self.paramLayout.itemAt(7, 1).widget().value
      w = self.paramLayout.itemAt(8, 1).widget().value
      newValue = { name : { 'displayName' : displayName, 'defaultValue' : {'x' : x, 'y' : y, 'z' : z, "w" : w }}}

    self.addedMsg.setText("Parameter \"" + displayName +"\" added to shader \""+self.shaderDisplayName+"\".")
    self.modifyDict(self.shaderDisplayName, self.addParamType, newValue)
    self.addedMsg.show()
    self.resetLayout(self.paramLayout)

  def modifyDict(self, shader, dictType, value):
    """Function to modify the specified dictionnary in the specified shader.

    Args:
      shader (string) : name of the shader to be modified
      dictType (string) : name of the dictionnary to be modified
      value (dict) : dictionnary to be added

    """

    #get selected shader path
    modifiedShaderClass = CustomShader.GetClassName(shader)
    modifiedShaderModule = modifiedShaderClass.__module__
    packageName = "Resources"
    f, filename, description = imp.find_module(packageName)
    packagePath = imp.load_module(packageName, f, filename, description).__path__[0]
    modifiedShaderPath = packagePath+'\\Shaders\\'+ modifiedShaderModule
    currentDict = str(getattr(modifiedShaderClass, dictType))
    modifiedDict = getattr(modifiedShaderClass, dictType)
    modifiedDict.update(value)

    fin = open(modifiedShaderPath, "rt")
    data = fin.read()
    data = data.replace(dictType + " = " +currentDict, dictType + " = " +str(modifiedDict))
    fin.close()

    fin = open(modifiedShaderPath, "wt")
    fin.write(data)
    fin.close()