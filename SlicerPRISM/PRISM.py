#@file PRISM.py
import os, sys
import unittest
from PythonQt.QtCore import *
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np, math, time
import json
import imp
import shutil
import textwrap
import importlib.util
import inspect
from pathlib import Path
from distutils.util import strtobool
from inspect import signature 
import inspect
import traceback
from Resources.CustomShader import CustomShader

from PRISMLogic import PRISMLogic

try:
  import colorlog
except ImportError:
  pass
def get_function_name():
  return traceback.extract_stack(None, 2)[0][2]

def get_function_parameters_and_values():
  frame = inspect.currentframe().f_back
  args, _, _, values = inspect.getargvalues(frame)
  return ([(i, values[i]) for i in args])
  
log = logging.getLogger(__name__)

"""!@class PRISM
@brief class prism
@param ScriptedLoadableModule class: Uses ScriptedLoadableModule base class, available at: https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
""" 
class PRISM(ScriptedLoadableModule):
  
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PRISM"
    self.parent.categories = ["Projet"]
    self.parent.dependencies = []
    self.parent.contributors = ["Tiphaine RICHARD"]
    self.parent.helpText = """A scripted module to edit custom volume rendering shaders."""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText ="""This file was developped by Tiphaine RICHARD at Ecole de Technologie Superieure (Montreal, Canada)"""


"""!@class PRISMWidget
@brief class PRISMWidget
@param ScriptedLoadableModuleWidget class: Uses ScriptedLoadableModuleWidget base class, available at: https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
"""
class PRISMWidget(ScriptedLoadableModuleWidget):

  def setup(self):
    """!@brief Function to setup the class.

    """   
    #log.info(get_function_name()+ str(get_function_parameters_and_values()))
    ScriptedLoadableModuleWidget.setup(self)

    ## Logic of module
    self.logic = PRISMLogic()
    ## All class names of shaders
    allShaderTypes = CustomShader.GetAllShaderClassNames()
    ## All classes of shaders
    self.allClasses = CustomShader.allClasses

    # Instantiate and connect widgets ..
    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/PRISM.ui'))
    self.layout.addWidget(uiWidget)
    ## Module's UI
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    #
    # Data Area
    #
    self.ui.imageSelector.setMRMLScene( slicer.mrmlScene )
    self.ui.imageSelector.currentNodeChanged.connect(lambda value, w = self.ui.imageSelector : self.onImageSelectorChanged(value, w))
     
    
    #
    # View Setup Area
    #

    self.ui.volumeRenderingCheckBox.toggled.connect(self.onVolumeRenderingCheckBoxToggled)
    self.ui.enableROICheckBox.toggled.connect(self.onEnableROICheckBoxToggled)
    self.ui.displayROICheckBox.toggled.connect(self.onDisplayROICheckBoxToggled)
    self.ui.enableScalingCheckBox.toggled.connect(self.onEnableScalingCheckBoxToggled)
    self.ui.enableRotationCheckBox.toggled.connect(self.onEnableRotationCheckBoxToggled)
    
    self.ui.enableROICheckBox.hide()
    self.ui.displayROICheckBox.hide()
    self.ui.enableScalingCheckBox.hide()
    self.ui.enableRotationCheckBox.hide()
    
    #
    # Custom Shader Area
    #
    self.ui.customShaderCollapsibleButton.hide()

    # Custom shader combobox to select a type of custom shader
    # Populate combobox with every types of shader available
    
    for shaderType in allShaderTypes:
      self.ui.customShaderCombo.addItem(shaderType)
    self.ui.customShaderCombo.setCurrentIndex(len(allShaderTypes)-1)
    self.ui.customShaderCombo.currentIndexChanged.connect(self.onCustomShaderComboIndexChanged)

    self.ui.reloadCurrentCustomShaderButton.clicked.connect(self.onReloadCurrentCustomShaderButtonClicked)
    self.ui.openCustomShaderButton.clicked.connect(self.onOpenCustomShaderButtonClicked)
    self.ui.duplicateCustomShaderButton.clicked.connect(self.onDuplicateCustomShaderButtonClicked)

    ## Error message (the created shader has the name of an existing shader)
    self.duplicateErrorMsg = qt.QLabel()
    self.duplicateErrorMsg.hide()
    self.duplicateErrorMsg.setStyleSheet("color: red")

    #
    # Modification and Creation of Custom Shader Area
    #

    with open(self.resourcePath('shaderTags.json'), 'r') as f:
      data = json.load(f)

    allShaderDecTags = data['allShaderDecTags']    
    allShaderInitTags = data['allShaderInitTags']
    allShaderImplTags = data['allShaderImplTags']
    allShaderExitTags = data['allShaderExitTags']
    allShaderPathCheckTags = data['allShaderPathCheckTags']

    ## List of shader tag types
    self.allShaderTagTypes = {
    "Declaration": allShaderDecTags,
    "Initialization": allShaderInitTags,
    "Exit": allShaderExitTags,
    "Implementation": allShaderImplTags,
    "Path Check": allShaderPathCheckTags,
    "None":"None"
    }
          
    # Populate comboboxes
    modifyCustomShaderItems = allShaderTypes.copy()
    modifyCustomShaderItems[len(modifyCustomShaderItems)-1] =  "Create new Custom Shader"
    self.updateComboBox(modifyCustomShaderItems, self.ui.modifyCustomShaderCombo, self.onModifyCustomShaderComboIndexChanged)
    self.updateComboBox(list(self.allShaderTagTypes.keys()), self.ui.shaderTagsTypeCombo, self.onShaderTagsTypeComboIndexChanged)
    
    self.ui.ModifyCSTabs.visible = False
    
    self.ui.editSourceButton.hide()
    self.ui.errorMsg.hide()
    self.ui.errorMsg.setStyleSheet("color: red")
    
    self.ui.addedMsg.hide()

    self.ui.shaderModifications.textChanged.connect(self.onModify)
    self.ui.shaderOpenFileButton.connect('clicked()', self.onShaderOpenFileButtonClicked)
    self.ui.modifyCustomShaderButton.connect('clicked()', self.onModifyCustomShaderButtonClicked)
    self.ui.newCustomShaderNameInput.textChanged.connect(self.onSelect)
    self.ui.newCustomShaderDisplayInput.textChanged.connect(self.onSelect)
    self.ui.createCustomShaderButton.clicked.connect(self.onNewCustomShaderButtonClicked)
    self.ui.editSourceButton.connect('clicked()', self.onEditSourceButtonClicked)
    
    ## Combobox to select the type of parameter to add to the shader
    self.addParamCombo = qt.QComboBox()
    ## Input to enter the name of the parameter to add to the shader
    self.addNameInput = qt.QLineEdit()
    ## Input to enter the display name of the shader
    self.addDisplayNameInput = qt.QLineEdit()

    ## Minimum value of the parameter
    self.addMinValueInput = qt.QDoubleSpinBox()
    ## Maximum value of the parameter
    self.addMaxValueInput = qt.QDoubleSpinBox()
    ## Default value of the parameter
    self.addDefaultValueInput = qt.QDoubleSpinBox()

    ## x value of the parameter
    self.addXInput = qt.QDoubleSpinBox()
    ## y value of the parameter
    self.addYInput = qt.QDoubleSpinBox()
    ## z value of the parameter
    self.addZInput = qt.QDoubleSpinBox()
    ## w value of the parameter
    self.addWInput = qt.QDoubleSpinBox()

    ## Button to add the parameter to the shader
    self.addParamButton = qt.QPushButton("Add parameter")
    ## Message to inform the user of the status of the current action
    self.addedMsg = qt.QLabel()
    ## Layout containing the combobox and message
    self.addParamLayout = qt.QFormLayout()
    ## Layout containing the parameters
    self.paramLayout = qt.QFormLayout()
    ## Display name of the shader
    self.shaderDisplayName = ""
    self.createParametersLayout()

    self.ui.emptyText.hide()
    self.ui.paramLayout.addLayout(self.addParamLayout, 0, 0)
    self.ui.paramLayout.addLayout(self.paramLayout, 1, 0)
    self.addParamCombo.show()
    self.addParamLayout.itemAt(0,0).widget().show()
    """
    # 
    # VR Actions Area
    #
    self.vrhelperActionsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.vrhelperActionsCollapsibleButton.text = "VR Actions"
    self.layout.addWidget(self.vrhelperActionsCollapsibleButton)

    VRActionsVBoxLayout = qt.QVBoxLayout(self.vrhelperActionsCollapsibleButton)

    # Activate VR
    self.setVRActiveButton = qt.QPushButton("Set VR Active")
    self.setVRActiveButton.setToolTip( "Set virtual reality Active." )
    self.setVRActiveButton.clicked.connect(self.logic.activateVR)
    VRActionsVBoxLayout.addWidget(self.setVRActiveButton)

    # Checkbox to display controls in VR
    self.displayControlsCheckBox = qt.QCheckBox()
    self.displayControlsCheckBox.toggled.connect(self.onDisplayControlsCheckBoxToggled)
    self.displayControlsCheckBox.text = "Display VR controls"
    VRActionsVBoxLayout.addWidget(self.displayControlsCheckBox)
    """

    # Initialize state
    self.onSelect()
    self.onModify()
    self.initState()

    ## Current x angle of the ROI
    self.currXAngle = 0.0
    ## Current y angle of the ROI 
    self.currYAngle = 0.0   
    ## Current z angle of the ROI
    self.currZAngle = 0.0
    ## Widget containing the transfer functions of the secondary volumes
    self.secondColorTransferFunctionWidget = {volumeID : {'color': None, 'scalarOpacity': None } for volumeID in range(20) } 
    ## All widgets of the UI that will be saved
    self.widgets = list(self.ui.centralWidget.findChildren(qt.QCheckBox())  \
    + self.ui.centralWidget.findChildren(qt.QPushButton()) \
    + self.ui.centralWidget.findChildren(qt.QComboBox()) \
    + self.ui.centralWidget.findChildren(slicer.qMRMLNodeComboBox()))

    ## Transfer function with its parameters
    self.transferFunctionParams = []

    ## Number of transfer function types
    self.numberOfTFTypes = 2

    ## Transfer function name
    self.transferFunctionParamsName = []

    # Set parameter node
    self.setAndObserveParameterNode()
    
    slicer.mrmlScene.AddNode(self.logic.parameterNode)
    if self.logic.parameterNode.GetParameterCount() != 0:
      volumePath = self.logic.parameterNode.GetParameter("volumePath")
      # Set volume node
      if len(volumePath) != 0 :
        volumeNode = slicer.util.loadVolume(volumePath)
        self.ui.imageSelector.setCurrentNode(volumeNode)
      
    self.addGUIObservers()
    # Update GUI  
    self.updateGUIFromParameterNode()

  def createParametersLayout(self) :
    """!@brief Function to create the parameters layout to enable adding new parameters to a file.

    """
    self.addParamCombo.addItem("Select type")
    self.addParamCombo.addItem("Integer")
    self.addParamCombo.addItem("Float")
    self.addParamCombo.addItem("Point")
    self.addParamCombo.setCurrentIndex(0)
    self.addParamCombo.activated.connect(self.onAddParamComboIndexChanged)
    self.addParamCombo.hide()

    self.addNameInput.textChanged.connect(self.addParamButtonState)

    self.addDisplayNameInput.textChanged.connect(self.addParamButtonState)

    # Values of the parameter if int or float
    self.addMinValueInput.setRange(-1000, 1000)
    self.addMinValueInput.valueChanged.connect(self.addParamButtonState)
    self.addMaxValueInput.setRange(-1000, 1000)
    self.addMaxValueInput.valueChanged.connect(self.addParamButtonState)
    self.addDefaultValueInput.valueChanged.connect(self.addParamButtonState)
    self.addDefaultValueInput.setRange(-1000, 1000)

    # Values of the parameter if point
    self.addXInput.setRange(-1000, 1000)
    self.addXInput.valueChanged.connect(self.addParamButtonState)
    self.addYInput.setRange(-1000, 1000)
    self.addYInput.valueChanged.connect(self.addParamButtonState)
    self.addZInput.setRange(-1000, 1000)
    self.addZInput.valueChanged.connect(self.addParamButtonState)
    self.addWInput.setRange(-1000, 1000)
    self.addWInput.valueChanged.connect(self.addParamButtonState)

    self.addParamButton.connect('clicked()', self.addParamButtonClicked)
    self.addedMsg.hide()
    
    self.addParamLayout.addRow("Add parameter", self.addParamCombo)
    self.addParamLayout.addRow("", self.addedMsg)
    self.addParamLayout.itemAt(0,0).widget().hide()

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


  def resetLayout(self, layout) :
    """!@brief Function to reset a specific layout.
    @param layout qLayout : layout to reset
    """

    self.addParamCombo.setCurrentIndex(0)
    self.clearLayout(layout)
    layout.itemAt(0, 1).widget().clear()
    layout.itemAt(1, 1).widget().clear()
    for i in range(2, 8) :
      layout.itemAt(i, 1).widget().setValue(0)
  
  def clearLayout(self, layout) :
    """!@brief Function to clear the widgets of a specific layout.
    @param layout qLayout : layout to clear

    """
    for i in range(layout.count()): 
      layout.itemAt(i).widget().hide()

  def showLayout(self, layout, nb) :
    """!@brief Function to show specific widgets of a layout.
    @param layout qLayout : layout to reset
    @param nb int : range of the widgets

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
    """!@brief Sets the current parameter type according to the combobox input.
    @param i int : index of the current input

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
      ## Type of the parameter added to the shader
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
    # TODO add the other types of parameters
    #"shaderbParams"
    #"shaderrParams"
    #"shadertfParams"
    #"shadervParams"

  def addParamButtonState(self):
    """!@brief Function to enable or disable the button to change the parametters.
 
    """
    self.addParamButton.enabled = len(self.addNameInput.text) > 0 and len(self.addDisplayNameInput.text) > 0

  def addParamButtonClicked(self) :
    """!@brief Function to get the current parameters and add them into a dictionnary.
    
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
    """!@brief Function to modify the specified dictionnary in the specified shader.

    @param shader string : name of the shader to be modified
    @param dictType string : name of the dictionnary to be modified
    @param value dict : dictionnary to be added

    """

    # Get selected shader path
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

  def setAndObserveParameterNode(self, caller=None, event=None):
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    """!@brief Function to set the parameter node.

    """
    # Remove observer to old parameter node
    if self.logic.parameterNode and self.logic.parameterNodeObserver:
      self.logic.parameterNode.RemoveObserver(self.logic.parameterNodeObserver)
      self.logic.parameterNodeObserver = None
    
    # Set and observe new parameter node
    self.logic.parameterNode = self.logic.getParameterNode()
    if self.logic.parameterNode:
      self.logic.parameterNodeObserver = self.logic.parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onParameterNodeModified)

  def getClassName(self, widget): 
    """!@brief Function to get the class name of a widget.

    @param widget QObject : wanted widget.

    @return str class name of the widget.
    """
    try :
      return widget.metaObject().getClassName()
    except :
      pass
    try :
      return widget.view().metaObject().getClassName()
    except :
      pass
    try :
      return widget.GetClassName()
    except :
      pass
  
  def updateGUIFromParameterNode(self, caller=None, event=None):
    """!@brief Function to update GUI from parameter node values

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    ##log.info(get_function_name()  + str(get_function_parameters_and_values()))
    if not self.logic.parameterNode:
      return
    parameterNode = self.logic.parameterNode
    if parameterNode.GetParameterCount() == 0:
      return
    
    # Disables updateParameterNodeFromGUI signal 
    self.removeGUIObservers()
    for w in self.widgets:
      widgetClassName = self.getClassName(w)
      value = parameterNode.GetParameter(w.name)
      if value != '' :
        if widgetClassName=="QPushButton":
          enabled = (int(value) != 0)
          w.setEnabled(enabled)
        elif widgetClassName=="QCheckBox":
          checked = (int(value) != 0)
          w.setChecked(checked)
        elif widgetClassName=="QComboBox":
          index = int(value)
          w.setCurrentIndex(index)
        elif widgetClassName=="ctkSliderWidget":
          value = float(value)
          w.setValue(value)
        elif widgetClassName=="ctkRangeWidget":
          values = value.split(',')     
          w.minimumValue = float(values[0])
          w.maximumValue = float(values[1])
        elif widgetClassName == "vtkColorTransferFunction" or widgetClassName == "vtkPiecewiseFunction":
          for i in range(w.GetSize()):
            values = self.logic.parameterNode.GetParameter(w.name+str(i))
            if values != "" :
              w.SetNodeValue(i, [int(float(k)) for k in values.split(",")])
      elif widgetClassName == "qMRMLNodeComboBox":
        w.setCurrentNodeID(parameterNode.GetNodeReferenceID(w.name))

    self.addGUIObservers()

  def updateParameterNodeFromGUI(self, value, w):
    """!@brief Function to update the parameter node from gui values.

    @param value float : Value of the widget. 
    @param w QObject : Widget being modified. 
    """   
    ##log.info(get_function_name()  + str(get_function_parameters_and_values()))
    parameterNode = self.logic.parameterNode
    oldModifiedState = parameterNode.StartModify()

    if self.ui.imageSelector.currentNode() is None:
      return 

    widgetClassName = self.getClassName(w)
    if widgetClassName=="QPushButton" :
      parameterNode.SetParameter(w.name, "1") if w.enabled else parameterNode.SetParameter(w.name, "0")
    elif widgetClassName == "QCheckBox":
      parameterNode.SetParameter(w.name, "1") if w.checked else parameterNode.SetParameter(w.name, "0")
    elif widgetClassName == "QComboBox":
      parameterNode.SetParameter(w.name, str(w.currentIndex))
    elif widgetClassName == "ctkSliderWidget":
      parameterNode.SetParameter(w.name, str(w.value))
    elif widgetClassName == "ctkRangeWidget":
      parameterNode.SetParameter(w.name, str(w.minimumValue) + ',' + str(w.maximumValue))
    elif widgetClassName == "vtkColorTransferFunction" or widgetClassName == "vtkPiecewiseFunction":
      parameterNode.SetParameter(w.name, "transferFunction")
      nbPoints = w.GetSize()
      if widgetClassName == "vtkColorTransferFunction" :
        values = [0,0,0,0,0,0]
      else :
        values = [0,0,0,0]
      if nbPoints > 0:
        for i in range(nbPoints):
          w.GetNodeValue(i, values)
          parameterNode.SetParameter(w.name+str(i), ",".join("{0}".format(n) for n in values))

        # If points are deleted, remove them from the parameter node
        i+=1
        val = parameterNode.GetParameter(w.name+str(i))
        while val != '':
          parameterNode.UnsetParameter(w.name+str(i))
          i+=1
          val = parameterNode.GetParameter(w.name+str(i))
    elif widgetClassName == "qMRMLNodeComboBox":
      parameterNode.SetNodeReferenceID(w.name, w.currentNodeID)
    parameterNode.EndModify(oldModifiedState)

      
  def addGUIObservers(self):
    """!@brief Function to add observers to the GUI's widgets.

    """   
    ##log.info(get_function_name()  + str(get_function_parameters_and_values()))
    for w in self.widgets:
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton" :
        w.clicked.connect(lambda value, w = w : self.updateParameterNodeFromGUI(value, w))
      elif widgetClassName == "QCheckBox":
        w.toggled.connect(lambda value, w = w : self.updateParameterNodeFromGUI(value, w))
      elif widgetClassName == "QComboBox":
        w.currentIndexChanged.connect(lambda value, w = w : self.updateParameterNodeFromGUI(value, w))
      elif widgetClassName == "ctkSliderWidget":
        w.valueChanged.connect(lambda value, w = w : self.updateParameterNodeFromGUI(value, w))
      elif widgetClassName == "ctkRangeWidget":
        w.valuesChanged.connect(lambda value1, value2, w = w : self.updateParameterNodeFromGUI([value2, value2], w))
      elif widgetClassName == "vtkColorTransferFunction" or widgetClassName == "vtkPiecewiseFunction":
        w.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = w : self.updateParameterNodeFromGUI([o,"add observers"], w))
      elif widgetClassName == "qMRMLNodeComboBox":
        w.currentNodeChanged.connect(lambda value, w = w : self.updateParameterNodeFromGUI(value, w))

  def removeGUIObservers(self):
    """!@brief Function to remove observers from the GUI's widgets.
    
    """  

    ##log.info(get_function_name()  + str(get_function_parameters_and_values())) 
    for w in self.widgets:
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton" :
        w.clicked.disconnect(self.updateParameterNodeFromGUI) 
      elif widgetClassName == "QCheckBox":
        w.toggled.disconnect(self.updateParameterNodeFromGUI) 
      elif widgetClassName == "QComboBox":
        w.currentIndexChanged.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "ctkSliderWidget":
        w.valueChanged.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "ctkRangeWidget":
        w.valuesChanged.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "vtkColorTransferFunction" or widgetClassName == "vtkPiecewiseFunction":
        #w.RemoveAllObservers()
        pass
      elif widgetClassName == "qMRMLNodeComboBox":
        w.currentNodeChanged.disconnect(self.updateParameterNodeFromGUI)
    
  def onParameterNodeModified(self, observer, eventid):
    """!@brief Function to update the parameter node.


        observer {[type]}  [description]
        eventid {[type]}  [description]
    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    self.updateGUIFromParameterNode()

  def getText(self):
    """!@brief Function to create a window with input to get the file name.

    @return str File name.
    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    text = qt.QInputDialog.getText(qt.QMainWindow(), "Duplicate file name","Enter file name:", qt.QLineEdit.Normal, "")
    if text != '':
      return text

  def onDuplicateCustomShaderButtonClicked(self) :
    """!@brief Function to duplicate custom shader file.

    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    duplicateShaderFileName = self.getText()
    copiedShaderFileName = str(CustomShader.GetClassName(self.ui.customShaderCombo.currentText).__name__ + ".py")

    # Duplicate the file
    if (duplicateShaderFileName != None):
      duplicatedFile = self.duplicateFile(copiedShaderFileName, duplicateShaderFileName)

      # If there was an error during the process, display it.
      if self.ui.errorMsgText != "" : 
        self.duplicateErrorMsg.text = self.ui.errorMsgText
        self.duplicateErrorMsg.show()
      else:
        # Else, open the file.
        qt.QDesktopServices.openUrl(qt.QUrl("file:///"+duplicatedFile, qt.QUrl.TolerantMode))
  

  def onOpenCustomShaderButtonClicked(self, caller=None, event=None) :
    """!@brief Function to open custom shader file.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    shaderPath = self.getPath(CustomShader.GetClassName(self.ui.customShaderCombo.currentText).__name__)
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+shaderPath, qt.QUrl.TolerantMode))

  def onEnableRotationCheckBoxToggled(self, caller=None, event=None) :
    """!@brief Function to enable rotating ROI box.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.ui.enableRotationCheckBox.isChecked():
      self.transformDisplayNode.SetEditorRotationEnabled(True)
    else :
      self.transformDisplayNode.SetEditorRotationEnabled(False)
  

  def onEnableScalingCheckBoxToggled(self, caller=None, event=None) :
    """!@brief Function to enable scaling ROI box.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.ui.enableScalingCheckBox.isChecked():
      self.transformDisplayNode.SetEditorScalingEnabled(True)
    else :
      self.transformDisplayNode.SetEditorScalingEnabled(False)


  def onEnableROICheckBoxToggled(self, caller=None, event=None):
    """!@brief Function to enable ROI cropping and show/hide ROI Display properties.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.ui.enableROICheckBox.isChecked():
      self.logic.volumeRenderingDisplayNode.SetCroppingEnabled(True)
      self.ui.displayROICheckBox.show()
    else:
      self.logic.volumeRenderingDisplayNode.SetCroppingEnabled(False)
      self.ui.displayROICheckBox.hide()
      self.ui.displayROICheckBox.setChecked(False)

  def onDisplayROICheckBoxToggled(self, caller=None, event=None):
    """!@brief Function to display ROI box and show/hide scaling and rotation parameters.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.ui.displayROICheckBox.isChecked():
      self.transformDisplayNode.EditorVisibilityOn()
      self.ui.enableScalingCheckBox.show()
      self.ui.enableRotationCheckBox.show()
    else :
      self.transformDisplayNode.EditorVisibilityOff()
      self.ui.enableScalingCheckBox.hide()
      self.ui.enableScalingCheckBox.setChecked(False)
      self.ui.enableRotationCheckBox.hide()
      self.ui.enableRotationCheckBox.setChecked(False)

  def onReloadCurrentCustomShaderButtonClicked(self, caller=None, event=None):
    """!@brief Function to reload the current custom shader.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ## Current shader display name
    currentShader = self.ui.customShaderCombo.currentText
    
    ## Current shader class name
    shaderName = CustomShader.GetClassName(currentShader).__name__

    ## Package name
    shaderPackageName = 'Resources.Shaders'
    
    ## Submodule name
    submoduleName = 'CustomShader'

    ## Submodule package name
    submodulePackageName = 'Resources'
    
    ## Path of the file containing the shader
    shaderPath = self.getPath(shaderName)
    ## Path of the file containing th modume
    modulePath = self.getPath(submoduleName, submodulePackageName)

    # Reload modules
    with open(shaderPath, "rt") as fp:
      ## Module containing the shader
      shaderModule = imp.load_module(shaderPackageName+'.'+shaderName, fp, shaderPath, ('.py', 'rt', imp.PY_SOURCE))
    
    with open(modulePath, "rt") as fp:
      customShaderModule = imp.load_module(submodulePackageName+'.'+submoduleName, fp, modulePath, ('.py', 'rt', imp.PY_SOURCE))

    # Update globals
    ## All of the shader modules
    clsmembers = inspect.getmembers(shaderModule, inspect.isclass)
    globals()[shaderName] = clsmembers[1][1]
    ## Custom shader module.
    clsmembers = inspect.getmembers(customShaderModule, inspect.isclass)
    globals()[submoduleName] = clsmembers[0][1]

    # Reset customShader
    self.logic.setupCustomShader()
    

  def onModifyCustomShaderButtonClicked(self, caller=None, event=None):
    """!@brief Function to add the new shader replacement to a file.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """

    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ## Type of the choosen shader tag
    shaderTagType = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    ## Choosen shader tag
    shaderTag = shaderTagType[self.modifiedShaderTag]
    
    ## Selected shader's path
    modifiedShaderPath = self.getPath(CustomShader.GetClassName(self.modifiedShader).__name__) 
    ## Shader code
    shaderCode = self.ui.shaderModifications.document().toPlainText()
    # Indent shader code
    shaderCode =  textwrap.indent(shaderCode, 3 * '\t')
    
    ## Tabulations to keep the code well indented.
    tab = "\t\t"
    ## String that will replace the tag in the code.
    shaderReplacement = (
    "replacement =  \"\"\"/*your new shader code here*/\n" +
    shaderCode + "\n" +
    tab + "\"\"\"\n"+
    tab + "self.shaderProperty.AddFragmentShaderReplacement(\""+shaderTag+"\", True, replacement, False)\n" +
    tab + "#shaderreplacement")

    # Modify file
    ## File containing the shader.
    fin = open(modifiedShaderPath, "rt")
    ## Data containted in the file of the shader.
    data = fin.read()
    data = data.replace('#shaderreplacement', shaderReplacement)
    fin.close()

    fin = open(modifiedShaderPath, "wt")
    fin.write(data)
    fin.close()
    
    # Open file window
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+modifiedShaderPath, qt.QUrl.TolerantMode))
    
    self.ui.addedMsg.setText("Code added to shader \""+self.modifiedShader+"\".")
    self.ui.addedMsg.show()

  def getPath(self, name, packageName = 'Resources/Shaders') :
    """!@brief Function to get a selected shader file path.


    @param name str : Name of the shader.

    
    @param packageName str : Name of the package in which the class in contained. (default: {'Resources/Shaders'})

    @return Path of the shader.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ## Class of the specified shader.
    class_ = CustomShader.GetClass(name)
    if class_ :
      ## Path of the class.
      path_ = os.path.join(self.prismPath(), packageName, str(class_.__name__) + '.py').replace("\\", "/")
      return path_
    
    return None

  def onShaderOpenFileButtonClicked(self, caller=None, event=None):
    """!@brief Function to open a file containing the new shader replacement.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ## Type of the selected shader tag
    shaderTagType = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    ## Selected shader tag
    shaderTag = shaderTagType[self.modifiedShaderTag]

    ## Selected shader path
    modifiedShaderPath = self.getPath(CustomShader.GetClassName(self.modifiedShader).__name__)

    ## Tabulations to keep the code well indented.
    tab = "\t\t"
    ## String that will replace the tag in the code.
    shaderReplacement = (
    "replacement = \"\"\"/*write your shader code here*/ \"\"\" \n " +
    tab + "self.shaderProperty.AddFragmentShaderReplacement(\""+shaderTag+"\", True, replacement, False) \n "+
    tab + "#shaderreplacement" )

    # Modify file
    ## File containing the shader.
    fin = open(modifiedShaderPath, "rt")
    ## Data containted in the file of the shader.
    data = data.replace('#shaderreplacement', shaderReplacement)
    fin.close()

    fin = open(modifiedShaderPath, "wt")
    fin.write(data)
    fin.close()
    
    # Open file window
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+modifiedShaderPath, qt.QUrl.TolerantMode))

  def updateComboBox(self, tab, comboBox, func):
    """!@brief Function to populate a combobox from an array.


    @param tab list : List to populate the combobox.
    @param comboBox QComboBox : ComboBox to be modified.
    @param func func : [Connect function when the ComboBox index is changed.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    
    comboBox.clear()  
    for e in tab:
      comboBox.addItem(e)
    comboBox.setCurrentIndex(len(tab)-1)
    comboBox.activated.connect(func)
    
  def onModifyCustomShaderComboIndexChanged(self, value):
    """!@brief Function to set which shader will be modified.


    @param value list : current value of the comboBox.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ## Display name of the shader.
    self.modifiedShader = self.ui.modifyCustomShaderCombo.currentText

    if (self.ui.modifyCustomShaderCombo.currentIndex == self.ui.modifyCustomShaderCombo.count-1):
      self.ui.createCustomShaderButton.show()
      self.ui.editSourceButton.show()
      self.ui.newCustomShaderDisplayInput.show()
      self.ui.newCustomShaderNameInput.show()
      if self.ui.editSourceButton.enabled == False:
        self.ui.ModifyCSTabs.visible = False
    else :
      self.ui.createCustomShaderButton.hide()
      self.ui.editSourceButton.hide()
      self.ui.errorMsg.hide()
      self.ui.newCustomShaderDisplayInput.hide()
      self.ui.newCustomShaderNameInput.hide()
      self.shaderDisplayName = self.ui.modifyCustomShaderCombo.currentText
      self.ui.ModifyCSTabs.visible = True

  def onShaderTagsTypeComboIndexChanged(self, value):
    """!@brief Function to set which shader tag type will be added to the shader.

    @param value list : current value of the comboBox.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    ## Type of the shader tag being modified
    self.modifiedShaderTagType = self.ui.shaderTagsTypeCombo.currentText
    self.ui.shaderTagsCombo.show()
    self.ui.shaderTagsComboLabel.show()
    ## All the shader tag that have the selected type.
    tab = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    self.updateComboBox(tab, self.ui.shaderTagsCombo, self.onShaderTagsComboIndexChanged)
 
  def onShaderTagsComboIndexChanged(self, value):
    """!@brief Function to set which shader tag will be added to the shader.


    @param value list : current value of the comboBox.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    ## Type of the shader tag being modified
    self.modifiedShaderTag = self.ui.shaderTagsCombo.currentText
    self.ui.shaderModificationsLabel.show()
    self.ui.shaderModifications.show()
    self.ui.shaderOpenFileButton.show()
    self.ui.modifyCustomShaderButton.show()


  def onNewCustomShaderButtonClicked(self):
    """!@brief Function to create a new file with the associated class.

    @return bool Returns False when an error occurs.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ## Name of the class that will be created (entered by user)
    self.className = self.ui.newCustomShaderNameInput.text
    ## Display name of the shader (entered by user)
    self.displayName = self.ui.newCustomShaderDisplayInput.text
    self.shaderDisplayName = self.ui.newCustomShaderDisplayInput.text
    ## New file created from a duplication of the template.
    self.newCustomShaderFile = self.duplicateFile("Template", self.className)
    # If there was an error during the proccess, display it.
    if self.ui.errorMsgText != "" : 
      self.ui.errorMsg.text = self.ui.errorMsgText
      self.ui.errorMsg.show()
      self.ui.createCustomShaderButton.enabled = False
      return False
    else:
      self.ui.createCustomShaderButton.enabled = True

    # If the file was created successfully
    if(self.newCustomShaderFile != False):
      self.ui.errorMsg.hide()
      # Show the options to add parameters to the file
      self.addParamCombo.show()
      self.addParamLayout.itemAt(0,0).widget().show()
      # Set up the file with the values entered.
      self.setup_file(self.newCustomShaderFile, self.className, self.displayName)
      self.ui.editSourceButton.show()
      CustomShader.GetAllShaderClassNames()
      self.modifiedShader = self.displayName
      self.ui.customShaderCombo.addItem(self.displayName)
      self.ui.createCustomShaderButton.enabled = False
      self.ui.newCustomShaderNameInput.setEnabled(False)
      self.ui.newCustomShaderDisplayInput.setEnabled(False)
      self.ui.ModifyCSTabs.visible = True

  def onEditSourceButtonClicked(self):
    """!@brief Function to create a new file with the custom shader and open the file in editor.

    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ## Name of the class that will be created
    new_file_name = self.className
    ## Path of the current file
    file_path = os.path.realpath(__file__)
    file_dir, filename = os.path.split(file_path)
    file_dir = os.path.join(file_dir, 'Resources', 'Shaders')
    dst_file = os.path.join(file_dir, new_file_name + ".py")

    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+self.newCustomShaderFile, qt.QUrl.TolerantMode))

  def onModify(self):
    """!@brief Function to activate or deactivate the button to modify a custom shader.

    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    self.ui.modifyCustomShaderButton.enabled = len(self.ui.shaderModifications.document().toPlainText()) > 0

  def onSelect(self):
    """!@brief Function to activate or deactivate the button to create a custom shader.

    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    self.ui.createCustomShaderButton.enabled = len(self.ui.newCustomShaderNameInput.text) > 0 and len(self.ui.newCustomShaderDisplayInput.text) > 0
    self.ui.errorMsg.hide()

  def duplicateFile(self, old_file_name, new_file_name):
    """!@brief Function to create a new class from the template.


    @param old_file_name str : Name of the file that is being duplicated.
    @param new_file_name str : Name of the file that is being created.

    @return str Path of the newly created file.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    ## Path of the current file
    file_path = os.path.realpath(__file__)
    file_dir, filename = os.path.split(file_path)
    ## Directory in which the file will be located
    file_dir = os.path.join(file_dir, 'Resources', 'Shaders')
    
    src_file = os.path.join(file_dir, old_file_name)
    dst_file = os.path.join(file_dir, new_file_name + ".py")
    
    # Check if file already exists
    if (os.path.exists(dst_file)):
      self.ui.errorMsgText = "The class \""+new_file_name+"\" exists already. Please check the name and try again."
      return False
    else:
      self.ui.errorMsgText = ""

    if (shutil.copy(src_file, dst_file)) :
      self.ui.errorMsgText = ""
      return dst_file
    else :
      self.ui.errorMsgText = "There is an error with the class name \""+new_file_name+"\". Please check the name and try again."

  def setup_file(self, file_, className, displayName):
    """!@brief Function to modify the new class with regex to match the given infos.


    @param file_ str : Path of the file being modified.
    @param className str : Name of the class being modified.
    @paramdisplayName str : Display name of the class being modified.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    import os, sys
    import re

    ## File containing the specified class
    classFile = open(file_, 'rt')
    data = classFile.read()
    dataClassName = re.sub(r'\bTemplate\b', className, data)
    classFile.close()

    classFile = open(file_, 'wt')
    classFile.write(dataClassName)
    classFile.close()

    classFile = open(file_, 'rt')
    data = classFile.read()
    dataDisplayName = re.sub(r'\bTemplateName\b', displayName, data)
    classFile.close()

    classFile = open(file_, 'wt')
    classFile.write(dataDisplayName)

    classFile.close()


  def initState(self):
    """!@brief Function to initialize the all user interface based on current scene.

    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    # Import shaders
    for c in self.allClasses:
      __import__('Resources.Shaders.' + str(c.__name__))
    
    # Init shader
    if self.ui.volumeRenderingCheckBox.isChecked() and self.ui.imageSelector.currentNode():
      self.logic.renderVolume(self.ui.imageSelector.currentNode())
      self.ui.imageSelector.currentNodeChanged.connect(lambda value, w = self.ui.imageSelector : self.onImageSelectorChanged(value, w))
      self.ui.imageSelector.currentNodeChanged.connect(lambda value, w = self.ui.imageSelector : self.updateParameterNodeFromGUI(value, w))
      self.ui.imageSelector.nodeAdded.disconnect()
      self.UpdateShaderParametersUI()    

  #
  # Data callbacks
  #

  def onImageSelectorChanged(self, node, widget, index=0):
    """!@brief Callback function when the volume node has been changed in the dedicated combobox.
    Setup slice nodes to display selected node and render it in the 3d view.

    @param node vtkMRMLVolumeNode : Volume node selected in the scene.
    @param widget QObject : Widget modified.
    @param index int : Index of the widget being modified.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    
    if not node:
      return
    
    # If the selector is a parameter of a shader
    if widget != self.ui.imageSelector :
      self.logic.currentVolume = index
      self.logic.renderVolume(widget.currentNode(), True)
      volumePropertyNode = self.logic.secondaryVolumeRenderingDisplayNodes[self.logic.currentVolume].GetVolumePropertyNode()

      volumeID = index
      TFID = volumeID * self.numberOfTFTypes

      for i, tf in enumerate(self.transferFunctionParams[TFID:TFID+self.numberOfTFTypes]):
        j = TFID + i
        self.createTransferFunctionWidget(volumePropertyNode, tf, self.transferFunctionParamsName[j], True, volumeID  )
      self.updateParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)
    elif self.ui.volumeRenderingCheckBox.isChecked():
      self.ui.volumeRenderingCheckBox.setChecked(False)
      self.ui.customShaderCombo.currentIndex = self.ui.customShaderCombo.count -1 
  #s
  # View setup callbacks
  #

  def onVolumeRenderingCheckBoxToggled(self, caller=None, event=None):
    """!@brief Callback function when the volume rendering check box is toggled. Activate or deactivate 
    the rendering of the selected volume
    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.ui.volumeRenderingCheckBox.isChecked():
      if self.ui.imageSelector.currentNode():

        self.logic.renderVolume(self.ui.imageSelector.currentNode())

        # Init ROI
        allTransformDisplayNodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLTransformDisplayNode','TransformDisplayNode')
        if allTransformDisplayNodes.GetNumberOfItems() > 0:
          ## Transforme Display node to apply transformations to the ROI
          self.transformDisplayNode = allTransformDisplayNodes.GetItemAsObject(0)
        else:
          self.transformDisplayNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformDisplayNode')
          self.transformDisplayNode.SetName('TransformDisplayNode')
          self.transformDisplayNode.SetEditorRotationEnabled(False)

        allTransformNodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLTransformNode','TransformNode')
        if allTransformNodes.GetNumberOfItems() > 0:
          ## Transform node to apply transformations to the ROI
          self.transformNode = allTransformNodes.GetItemAsObject(0)
        else:
          self.transformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
          self.transformNode.SetName('TransformNode')
          self.transformNode.SetAndObserveDisplayNodeID(self.transformDisplayNode.GetID())

        ## ROI of the current volume
        self.ROI = self.logic.volumeRenderingDisplayNode.GetROINode()
        self.ROI.SetAndObserveDisplayNodeID(self.transformDisplayNode.GetID())
        self.ROI.SetAndObserveTransformNodeID(self.transformNode.GetID())
        self.ROI.SetDisplayVisibility(0)
        self.resetROI()
        self.ui.enableROICheckBox.show()
        self.UpdateShaderParametersUI()
        self.ui.customShaderCollapsibleButton.show()
    else:
      if self.logic.volumeRenderingDisplayNode:
        self.logic.volumeRenderingDisplayNode.SetVisibility(False)
        if self.logic.secondaryVolumeRenderingDisplayNodes :
          for i in range(self.logic.numberOfVolumes):
            if self.logic.secondaryVolumeRenderingDisplayNodes[i] != None:
              self.logic.secondaryVolumeRenderingDisplayNodes[i].SetVisibility(False)
        self.ui.enableROICheckBox.setChecked(False)
        self.ui.displayROICheckBox.setChecked(False)
        self.ui.enableROICheckBox.hide()
        self.ui.displayROICheckBox.hide()
      self.ui.customShaderCollapsibleButton.hide()
      
  def resetROI(self):
    """!@brief Function to reset the ROI in the scene.

    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ## Node of the roi
    ROINode = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLAnnotationROINode','AnnotationROI')
    if ROINode.GetNumberOfItems() > 0:
      # Set node used before reload in the current instance
      ROINodes = ROINode.GetItemAsObject(0)
      ROINodes.ResetAnnotations()
      ROINodes.SetName("ROI")

  def onDisplayControlsCheckBoxToggled(self, caller=None, event=None):
    """!@brief Callback function triggered when the display controls check box is toggled.
        Show/hide in the VR view scene the controls at the location of the Windows Mixed Reality controllers.

    @param caller Caller of the function.
    @param event Event that triggered the function.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.displayControlsCheckBox.isChecked():
      self.logic.vrhelper.showVRControls()
    else:
      self.logic.hideVRControls()

  #
  # Volume rendering callbacks
  #

  def onCustomShaderComboIndexChanged(self, i):
    """!@brief Callback function when the custom shader combo box is changed.

    @param i int : Index of the element.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    self.logic.setCustomShaderType(self.ui.customShaderCombo.currentText)
    self.UpdateShaderParametersUI()
    self.updateParameterNodeFromGUI(self.ui.customShaderCombo.currentText, self.ui.customShaderCombo)
    self.updateGUIFromParameterNode()
    
    # If there is no selected shader, disables the buttons.
    if i == (self.ui.customShaderCombo.currentText == "None"):
      self.ui.openCustomShaderButton.setEnabled(False)
      self.ui.reloadCurrentCustomShaderButton.setEnabled(False)
      self.ui.duplicateCustomShaderButton.setEnabled(False)
    else :
      self.ui.openCustomShaderButton.setEnabled(True)
      self.ui.reloadCurrentCustomShaderButton.setEnabled(True)
      self.ui.duplicateCustomShaderButton.setEnabled(True)

  def appendList(self, widget, name):
    """!@brief Function to add a widget to self.widgets without duplicate.


    @param widget QObject : Widget to be added to the list.
    @param name str : Name of the widget.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
   
    ## Widget is in the list or not
    found = False
    # Check if the widget is in the list
    for i, w in enumerate(self.widgets):
      if w.name == name and name !="":
        found = True
        index = i
        break
      
    if found :
      self.widgets[index] = widget
    else:
      self.widgets.append(widget)


  def UpdateShaderParametersUI(self):
    """!@brief Updates the shader parameters on the UI.

    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    self.removeGUIObservers()

    if self.logic.customShader == None:
      return

    # Clear all the widgets except the combobox selector
    while self.ui.customShaderParametersLayout.count() != 1:
      ## Item of the combobox
      item = self.ui.customShaderParametersLayout.takeAt(self.ui.customShaderParametersLayout.count() - 1)
      if item != None:
        widget = item.widget()
        if widget != None:
          widget.setParent(None)
    try :
      self.logic.endPoints.RemoveAllMarkups()
    except :
      pass
    lenWidgets = len(self.widgets)
    
    ## Name of the current shader, without spaces
    self.CSName = self.ui.customShaderCombo.currentText.replace(" ", "")

    # Instanciate a slider for each floating parameter of the active shader
    ## Floating parameters
    params = self.logic.customShader.shaderfParams
    ## Names of the parameters
    paramNames = params.keys()
    for p in paramNames:
      label = qt.QLabel(params[p]['displayName'])
      label.setMinimumWidth(80)
      slider = ctk.ctkSliderWidget()
      slider.minimum = params[p]['min']
      slider.maximum = params[p]['max']
      f = str(params[p]['defaultValue'])
      slider.setDecimals(f[::-1].find('.'))
      slider.singleStep = ( (slider.maximum - slider.minimum) * 0.01 )
      slider.setObjectName(self.CSName + p)
      slider.setValue(self.logic.customShader.getShaderParameter(p, float))
      slider.valueChanged.connect(lambda value, p=p : self.logic.onCustomShaderParamChanged(value, p, float) )
      slider.valueChanged.connect(lambda value, w = slider : self.updateParameterNodeFromGUI(value, w))
      slider.setParent(self.ui.customShaderParametersLayout)
      self.ui.customShaderParametersLayout.addRow(label, slider)
      
      self.appendList(slider, self.CSName+p)

    # Instanciate a slider for each integer parameter of the active shader
    ## Int parameters
    params = self.logic.customShader.shaderiParams
    paramNames = params.keys()
    for p in paramNames:
      label = qt.QLabel(params[p]['displayName'])
      label.setMinimumWidth(80)
      slider = ctk.ctkSliderWidget()
      slider.minimum = params[p]['min']
      slider.maximum = params[p]['max']
      slider.singleStep = ( (slider.maximum - slider.minimum) * 0.05)
      slider.setObjectName(self.CSName+p)
      slider.setDecimals(0)
      slider.setValue(int(self.logic.customShader.getShaderParameter(p, int)))
      slider.valueChanged.connect(lambda value, p=p : self.logic.onCustomShaderParamChanged(value, p, int) )
      slider.valueChanged.connect(lambda value, w = slider : self.updateParameterNodeFromGUI(value, w))
      slider.setParent(self.ui.customShaderParametersLayout)
      self.ui.customShaderParametersLayout.addRow(label, slider)
      
      self.appendList(slider, self.CSName+p)
    
    # Instanciate a markup
    ## Point parameters
    params = self.logic.customShader.shader4fParams
    paramNames = params.keys()
    for p in paramNames:
      x = params[p]['defaultValue']['x']
      y = params[p]['defaultValue']['y']
      z = params[p]['defaultValue']['z']
      w = params[p]['defaultValue']['w']

      targetPointButton = qt.QPushButton("Initialize " + params[p]['displayName'])
      targetPointButton.setToolTip( "Place a markup" )
      targetPointButton.setObjectName(self.CSName+p)
      targetPointButton.clicked.connect(lambda _, name = p, btn = targetPointButton : self.logic.setPlacingMarkups(paramName = name, btn = btn,  interaction = 1))
      targetPointButton.clicked.connect(lambda value, w = slider : self.updateParameterNodeFromGUI(value, w))
      targetPointButton.setParent(self.ui.customShaderParametersLayout)
      self.ui.customShaderParametersLayout.addRow(qt.QLabel(params[p]['displayName']), targetPointButton)
      self.appendList(targetPointButton, self.CSName+p)
    
    ## Range parameter
    params = self.logic.customShader.shaderrParams
    paramNames = params.keys()
    for p in paramNames:
      label = qt.QLabel(params[p]['displayName'])
      label.setMinimumWidth(80)
      slider = ctk.ctkRangeWidget()
      slider.minimum = params[p]['defaultValue'][0]
      slider.minimumValue = params[p]['defaultValue'][0]
      slider.maximum = params[p]['defaultValue'][1]
      slider.maximumValue = params[p]['defaultValue'][1]
      slider.singleStep = ( (slider.maximum - slider.minimum) * 0.01 )
      slider.setObjectName(self.CSName+p)
      slider.setParent(self.ui.customShaderParametersLayout)
      slider.valuesChanged.connect(lambda min_, max_, p=p : self.logic.onCustomShaderParamChanged([min_, max_], p, "range") )
      slider.valuesChanged.connect(lambda value1, value2, w = slider : self.updateParameterNodeFromGUI([value1, value2], w))
      self.ui.customShaderParametersLayout.addRow(label, slider)

      self.appendList(slider, self.CSName+p)

    ## Transfer function of the first volume
    params = self.logic.customShader.shadertfParams
    paramNames = params.keys()
    if len(params) > self.numberOfTFTypes:
      log.error("Too many transfer function have been defined.")
    

    TFTypes = [params[p]['type'] for p in paramNames]
    # Check that each volume has only one of each type of transfer functions.
    if len(TFTypes) != len(set(TFTypes)) and len(TFTypes) > self.numberOfTFTypes:
      log.error("One transfer function has been assigned multiple times to the same volume2.")
    
    if paramNames:
      # If a transfer function is specified, add the widget
      if self.logic.volumeRenderingDisplayNode is None :
        return

      self.addTransferFunctions(params, paramNames, 0)

    else :
      # Keep the original transfert functions
      volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
      colorTransferFunction = vtk.vtkColorTransferFunction()
      colorTransferFunction.DeepCopy(self.logic.colorTransferFunction)
      colorTransferFunction.name = "Original" + colorTransferFunction.GetClassName() 
      colorTransferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = colorTransferFunction : self.updateParameterNodeFromGUI([o,e], w))
      volumePropertyNode.SetColor(colorTransferFunction)

      self.appendList(colorTransferFunction, colorTransferFunction.name)
      opacityTransferFunction = vtk.vtkPiecewiseFunction()
      opacityTransferFunction.DeepCopy(self.logic.opacityTransferFunction)
      opacityTransferFunction.name = "Original" + opacityTransferFunction.GetClassName()
      opacityTransferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = opacityTransferFunction : self.updateParameterNodeFromGUI([o,e], w))
      volumePropertyNode.SetScalarOpacity(opacityTransferFunction)
      self.appendList(opacityTransferFunction, colorTransferFunction.name)

    ## Volumes parameters
    params = self.logic.customShader.shadervParams
    paramNames = params.keys()

    if params :
      # Check that each volume is used only once
      volumes = [params[p]['defaultVolume'] for p in paramNames]
      if len(set(volumes)) != len(params):
        log.error("Multiples volumes defined.")
      self.logic.numberOfVolumes = len(volumes)
    else :
      if self.logic.secondaryVolumeRenderingDisplayNodes :
        for i in range(self.logic.numberOfVolumes):
          if self.logic.secondaryVolumeRenderingDisplayNodes[i] != None:
            self.logic.secondaryVolumeRenderingDisplayNodes[i].SetVisibility(False)

    for i, p in enumerate(paramNames):
      # Check that each volume has only one of each type of transfer functions.      

      label = qt.QLabel(params[p]['displayName'])
      imageSelector = slicer.qMRMLNodeComboBox()
      imageSelector.setMRMLScene( slicer.mrmlScene )
      imageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
      imageSelector.selectNodeUponCreation = True
      imageSelector.addEnabled = False
      imageSelector.removeEnabled = False
      imageSelector.noneEnabled = False
      imageSelector.showHidden = False
      imageSelector.showChildNodeTypes = False
      imageSelector.setObjectName(self.CSName+p)
      imageSelector.setCurrentNode(None)
      self.appendList(imageSelector, self.CSName+p)
      self.ui.customShaderParametersLayout.addRow(label, imageSelector)
      imageSelector.currentNodeChanged.connect(lambda value, w = imageSelector : self.updateParameterNodeFromGUI(value, w))
      imageSelector.currentNodeChanged.connect(lambda value, w = imageSelector, index = i : self.onImageSelectorChanged(value, w, index))
      
      if params[p]['transferFunctions'] != {} :
        tfParams = params[p]['transferFunctions']
        tfParamNames = tfParams.keys()
        TFTypes = [tfParams[p]['type'] for p in tfParamNames]
        if len(TFTypes) != len(set(TFTypes)) or len(TFTypes) > self.numberOfTFTypes:
          log.error("One transfer function has been assigned multiple times to the same volume.")
        self.addTransferFunctions(params[p]['transferFunctions'], params[p]['transferFunctions'].keys(), params[p]['defaultVolume'])

    ## Boolean parameters
    params = self.logic.customShader.shaderbParams
    paramNames = params.keys()
    for p in paramNames:
      self.addOptionCheckBox = qt.QCheckBox(params[p]['displayName'])
      self.addOptionCheckBox.setObjectName(self.CSName+p)
      self.addOptionCheckBox.toggled.connect(lambda _, name = p, cbx = self.addOptionCheckBox, CSName = self.CSName : self.logic.enableOption(paramName = name, type_ = "bool", checkBox = cbx, CSName = CSName))
      self.ui.customShaderParametersLayout.addRow(self.addOptionCheckBox)
      self.logic.optionEnabled = params[p]['defaultValue']
      self.addOptionCheckBox.toggled.connect(lambda value, w = self.addOptionCheckBox : self.updateParameterNodeFromGUI(value, w))
      self.appendList(self.addOptionCheckBox, self.CSName+p)

      # Hide widgets specified in boolean
      optionalWidgets = params[p]['optionalWidgets']
      if optionalWidgets != [] :
        for i in optionalWidgets:
          pos = self.getWidgetPosition(self.ui.customShaderParametersLayout, self.CSName+i)
          widget = self.ui.customShaderParametersLayout.itemAt(pos).widget()
          label = self.ui.customShaderParametersLayout.itemAt(pos-1).widget()
          widget.hide()
          label.hide()
          if str(self.CSName+p) in self.logic.optionalWidgets :
            self.logic.optionalWidgets[self.CSName+p] += [widget]
          else :
            self.logic.optionalWidgets[self.CSName+p] = [widget]
          self.logic.optionalWidgets[self.CSName+p] += [label]
    self.addGUIObservers()

  def addTransferFunctions(self, params, paramNames, volumeID):

    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    """!@brief Function to add transfer function widgets to the ui.

    @param params params : Dictionnary of transfert functions.
    @param params paramNames : Name of the transfert functions.
    @param params volumeID : ID of the volume.

    @return Null if error.
    """
    if volumeID == 0:
      volumePrincipal = True
    else :
      volumePrincipal = False
      #minus one because the array of TF starts at 0
      volumeID -=1
    for i, p in enumerate(paramNames):
      # IF this is the principal volume
      if volumePrincipal :
        volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
        self.createTransferFunctionWidget(volumePropertyNode, params[p], p, False, volumeID)
      else : 
        # If this is a secondary volume
        transferFunctionID = volumeID * self.numberOfTFTypes
        # If the volume of the transfer function is already rendered create the widget
        if self.logic.secondaryVolumeRenderingDisplayNodes[volumeID] is not None: 
          volumePropertyNode = self.logic.secondaryVolumeRenderingDisplayNodes[volumeID].GetVolumePropertyNode()
          self.createTransferFunctionWidget(volumePropertyNode, params[p], p, True, volumeID)
        else :
          # Add the transfer functions to a list, so when the volume is rendered the widgets can be created
          if len(self.transferFunctionParams) <= transferFunctionID + i:
            self.transferFunctionParams.append(params[p])
            self.transferFunctionParamsName.append(p)
          else :
            self.transferFunctionParams[transferFunctionID + i] = params[p]
            ## Name of the transfer function
            self.transferFunctionParamsName[transferFunctionID + i] = p

  def getWidgetPosition(self, layout, widgetName):
    """!@brief Function to get the widget's position in a layout.

    @param layout QObject : Layout in which the widget is containted.
    @param widgetName str : Name of the widget being searched.

    @return i int : Position of the widget.
    """
    for i in range(layout.count()):
      item = layout.itemAt(i)
      if item != None :
        widget = item.widget()
        if widget!= None :
          if (widget.name == widgetName):
            return i

  def createTransferFunctionWidget(self, volumePropertyNode, params, p, secondTf, volumeID) :
    """!@brief Function to create a transfert fuction widget.

    @param volumePropertyNode vtkMRMLVolumePropertyNode : Volume property node to be associated to the widget.
    @param param dict : Parameters to add to the widget.
    @param p str : Parameter's name.
    @param TFType str : Type of the transfer function, can be 'color', 'scalarOpacity'.
    @param params volumeID : ID of the volume.
    """
    ##log.info(get_function_name()  + str(get_function_parameters_and_values()))
    TFType = params['type']
    ## Transfer function of the volume
    if TFType == 'color':
      transferFunction = volumePropertyNode.GetColor()
    elif TFType == 'scalarOpacity':
      transferFunction = volumePropertyNode.GetScalarOpacity()
    
    # Check if the widget for the nth volume already exists
    if secondTf :
      widget = self.secondColorTransferFunctionWidget[volumeID][TFType]

      if widget is not None :
        # Remove widget and label
        widget.setParent(None)
        self.secondColorTransferFunctionWidget[volumeID][TFType] = None
        #widget = None
        label = self.ui.centralWidget.findChild(qt.QLabel, self.CSName + transferFunction.GetClassName() + p + "Label")
        if label != None:
          label.setParent(None)

    # Create the widget
    label = qt.QLabel(params['displayName'])
    label.setObjectName(self.CSName + transferFunction.GetClassName() + p + "Label")

    widget = ctk.ctkVTKScalarsToColorsWidget()
    widget.setObjectName(self.CSName + transferFunction.GetClassName() + p + "Widget")
    transferFunction.name = self.CSName + transferFunction.GetClassName() + p
    transferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = transferFunction : self.updateParameterNodeFromGUI([o,"add widget"], w))

    # Change the points to the ones specified in the shader
    if params['defaultColors'] != [] :
      colors = params['defaultColors']
      nbColors = len(colors)
      transferFunction.RemoveAllPoints()
      transferFunction.AdjustRange((0, colors[nbColors-1][0]))
      for i in range(nbColors):
        transferFunction.SetNodeValue(i, colors[i])  

    if TFType == 'color':
      widget.view().addColorTransferFunction(transferFunction)
    elif TFType == 'scalarOpacity':
      widget.view().addOpacityFunction(transferFunction)
    
    widget.view().setAxesToChartBounds()
    widget.setFixedHeight(100)
    self.appendList(transferFunction, transferFunction.name)

    self.ui.customShaderParametersLayout.addRow(label, widget)

    if secondTf :
      self.secondColorTransferFunctionWidget[volumeID][TFType] = widget

  def prismPath(self) :
    """!@brief Function to get the module's path.

    @return str Module's path.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    return os.path.dirname(eval('slicer.modules.prism.path'))

  def onReload(self):
    """!@brief Reload the modules.

    """
    ##log.info(get_function_name()  + str(get_function_parameters_and_values()))

    log.debug("Reloading Packages")
    packageName='Resources'
    submoduleNames = ['CustomShader']
    
    for submoduleName in submoduleNames :
      modulePath = self.getPath(submoduleName, packageName)

      with open(modulePath, "rt") as fp:
        imp.load_module(packageName+'.'+submoduleName, fp, modulePath, ('.py', 'rt', imp.PY_SOURCE))

    log.debug("Reloading Shaders")
    try :
      shaderNames = []
      for c in self.allClasses:
        shaderNames.append(c.__name__)
      
      shaderPackageName = "Resources.Shaders"
      
      for shaderName in shaderNames :
        shaderPath = self.getPath(shaderName)
        with open(shaderPath, "rt") as fp:
          imp.load_module(shaderPackageName+'.'+shaderName, fp, shaderPath, ('.py', 'rt', imp.PY_SOURCE))
    except:
      pass

    log.debug("Reloading PRISM")
    packageNames=['PRISM', 'PRISMLogic']
    
    for packageName in packageNames :
      path = os.path.join(self.prismPath(), packageName + '.py').replace("\\", "/")
      with open(path, "rt") as fp:
        imp.load_module(packageName, fp, self.prismPath(), ('.py', 'rt', imp.PY_SOURCE))

    globals()['PRISM'] = slicer.util.reloadScriptedModule('PRISM')


  def cleanup(self):
    """!@brief Function to clean up the scene.

    """
    ##log.info(get_function_name()  + str(get_function_parameters_and_values()))

    self.removeGUIObservers()
    if self.logic.parameterNode and self.logic.parameterNodeObserver:
      slicer.mrmlScene.RemoveObserver(self.logic.parameterNodeObserver)
    
    self.resetROI()
    self.ui.enableROICheckBox.setChecked(False)
    self.ui.displayROICheckBox.setChecked(False)
    try :
      slicer.mrmlScene.RemoveNode(self.transformNode)
      slicer.mrmlScene.RemoveNode(self.transformDisplayNode)
    except: 
      pass