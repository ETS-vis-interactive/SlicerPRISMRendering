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
from Resources.ModifyParamWidget import ModifyParamWidget
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
    self.parent.contributors = ["Simon Drouin"]
    self.parent.helpText = """A scripted module to edit custom volume rendering shaders."""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText ="""This file was developped by Simon Drouin at Ecole de Technologie Superieure (Montreal, Canada)"""


"""!@class PRISMWidget
@brief class PRISMWidget
@param ScriptedLoadableModuleWidget class: Uses ScriptedLoadableModuleWidget base class, available at: https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
"""
class PRISMWidget(ScriptedLoadableModuleWidget):

  def setup(self):
    """!@brief Function to setup the class.

    """   
    log.info(get_function_name()+ str(get_function_parameters_and_values()))
    ScriptedLoadableModuleWidget.setup(self)

    self.logic = PRISMLogic()
    allShaderTypes = CustomShader.GetAllShaderClassNames()
    self.allClasses = CustomShader.allClasses

    # Instantiate and connect widgets ..
    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/PRISM.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    #
    # Data Area
    #
    self.ui.imageSelector.setMRMLScene( slicer.mrmlScene )
    #self.ui.imageSelector.connect("nodeAdded(vtkMRMLNode*)", self.onImageSelectorNodeAdded) #FIXME
    self.ui.imageSelector.currentNodeChanged.connect(lambda value, w = self.ui.imageSelector : self.onImageSelectorChanged(value, w))
    self.ui.parametersNodeSelector.setMRMLScene( slicer.mrmlScene )
    self.ui.parametersNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.setAndObserveParameterNode)
    self.ui.parametersNodeSelector.addAttribute( "vtkMRMLScriptedModuleNode", "ModuleName", "PRISM" )
    
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

    self.duplicateErrorMsg = qt.QLabel()
    self.duplicateErrorMsg.hide()
    self.duplicateErrorMsg.setStyleSheet("color: red")

    #
    # Modification of Custom Shader Area
    #

    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(dir_path+'/shaderTags.json', 'r') as f:
      data = json.load(f)

    allShaderDecTags = data['allShaderDecTags']    
    allShaderInitTags = data['allShaderInitTags']
    allShaderImplTags = data['allShaderImplTags']
    allShaderExitTags = data['allShaderExitTags']
    allShaderPathCheckTags = data['allShaderPathCheckTags']

    self.allShaderTagTypes = {
    "Declaration": allShaderDecTags,
    "Initialization": allShaderInitTags,
    "Exit": allShaderExitTags,
    "Implementation": allShaderImplTags,
    "Path Check": allShaderPathCheckTags,
    "None":"None"
    }
          
    # populate comboboxes
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
    
    self.addParamModifyShader = ModifyParamWidget()
    self.ui.emptyText.hide()
    self.ui.paramLayout.addLayout(self.addParamModifyShader.addParamLayout, 0, 0)
    self.ui.paramLayout.addLayout(self.addParamModifyShader.paramLayout, 1, 0)
    self.addParamModifyShader.addParamCombo.show()
    self.addParamModifyShader.addParamLayout.itemAt(0,0).widget().show()
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
    self.currXAngle = 0.0
    self.currYAngle = 0.0
    self.currZAngle = 0.0
    #save widgets
    self.widgets = list(self.ui.centralWidget.findChildren(qt.QCheckBox())  \
    + self.ui.centralWidget.findChildren(qt.QPushButton()) \
    + self.ui.centralWidget.findChildren(qt.QComboBox()))
    self.nodeSelectorWidgets = [self.ui.imageSelector, self.ui.parametersNodeSelector]
    self.init = 0
    # Set parameter node (widget will observe it)
    self.updateNodeSelector()
    self.setAndObserveParameterNode()
    self.addGUIObservers()
    # Update GUI  
    self.updateGUIFromParameterNode()
  
  def updateNodeSelector(self):
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    """!@brief Function to update the node selectors.

    """
    if self.ui.parametersNodeSelector.currentNode() is None:
      parameterNode = self.logic.getParameterNode()
      slicer.mrmlScene.AddNode(parameterNode)
      self.ui.parametersNodeSelector.setCurrentNode(parameterNode)
      if self.ui.imageSelector.currentNode() is None and parameterNode.GetParameterCount() != 0:
        volumePath = self.logic.parameterNode.GetParameter("volumePath")
        if len(volumePath) != 0 :
          volumeNode = slicer.util.loadVolume(volumePath)
          self.ui.imageSelector.setCurrentNode(volumeNode)
  
  def cleanup(self):
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    """!@brief Function to clean up the scene.

    """
    self.removeGUIObservers()

    if self.logic.parameterNode and self.logic.parameterNodeObserver:
      slicer.mrmlScene.RemoveObserver(self.logic.parameterNodeObserver)
  
  def setAndObserveParameterNode(self, caller=None, event=None):
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    """!@brief Function to set the parameter node.

    """
    # Remove observer to old parameter node
    if self.logic.parameterNode and self.logic.parameterNodeObserver:
      self.logic.parameterNode.RemoveObserver(self.logic.parameterNodeObserver)
      self.logic.parameterNodeObserver = None
    # Set and observe new parameter node
    self.logic.parameterNode = self.ui.parametersNodeSelector.currentNode()
    if self.logic.parameterNode:
      self.logic.parameterNodeObserver = self.logic.parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onParameterNodeModified)

  def getClassName(self, widget): 
    """!@brief Function to get the class name of a widget.

    @param widget QObject : wanted widget.

    @return str class name of the widget.
    """
    import sys
    if sys.version_info.  major == 2:
      return widget.metaObject().className()
    else:
      try :
        return widget.metaObject().getClassName()
      except:
        return widget.view().metaObject().getClassName()
  
  def updateGUIFromParameterNode(self, caller=None, event=None):
    """!@brief Function to update GUI from parameter node values

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    if not self.logic.parameterNode:
      return
    parameterNode = self.logic.parameterNode

    if parameterNode.GetParameterCount() == 0:
      return
    
    #disables updateParameterNodeFromGUI signal 
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
        elif widgetClassName=="QComboBox" or widgetClassName == "ctkComboBox":
          index = int(value)
          w.setCurrentIndex(index)
        elif widgetClassName=="ctkSliderWidget":
          value = float(value)
          w.setValue(value)
        elif widgetClassName=="ctkRangeWidget":
          values = value.split(',')     
          w.minimumValue = float(values[0])
          w.maximumValue = float(values[1])
        elif widgetClassName == "ctkVTKScalarsToColorsWidget":
          volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
          transfertFunction = volumePropertyNode.GetColor()
          i = 0
          values = self.logic.parameterNode.GetParameter(w.name+str(i))
          while values != '':
            transfertFunction.SetNodeValue(i,[int(float(i)) for i in values.split(",")])
            i+=1
            values = self.logic.parameterNode.GetParameter(w.name+str(i))
        elif widgetClassName == "qMRMLNodeComboBox":
          pass #TODO changer dans self.nodeSelectorWidgets

    for w in self.nodeSelectorWidgets:
      oldBlockSignalsState = w.blockSignals(True)
      w.setCurrentNodeID(parameterNode.GetNodeReferenceID(w.name))
      w.blockSignals(oldBlockSignalsState)

    self.addGUIObservers()

  def updateParameterNodeFromGUI(self, value, widget):
    """!@brief Function to update the parameter node from gui values.

    @param value float : value of the widget. 
    @param widget QObject : widget being modified. 
    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    parameterNode = self.logic.parameterNode
    oldModifiedState = parameterNode.StartModify()

    if self.ui.imageSelector.currentNode() is None:
      return 
    
    widgetClassName = self.getClassName(widget)
    if widgetClassName=="QPushButton" :
      parameterNode.SetParameter(widget.name, "1") if widget.enabled else parameterNode.SetParameter(widget.name, "0")
    elif widgetClassName == "QCheckBox":
      parameterNode.SetParameter(widget.name, "1") if widget.checked else parameterNode.SetParameter(widget.name, "0")
    elif widgetClassName == "QComboBox" or widgetClassName == "ctkComboBox" :
      parameterNode.SetParameter(widget.name, str(widget.currentIndex))
    elif widgetClassName == "ctkSliderWidget":
      parameterNode.SetParameter(widget.name, str(widget.value))
    elif widgetClassName == "ctkRangeWidget":
      parameterNode.SetParameter(widget.name, str(widget.minimumValue) + ',' + str(widget.maximumValue))
    elif widgetClassName == "ctkVTKScalarsToColorsWidget": 
      volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
      transfertFunction = volumePropertyNode.GetColor()
      parameterNode.SetParameter(widget.name, "transferFunction")
      values = [0,0,0,0,0,0]
      i = 0
      res = transfertFunction.GetNodeValue(i, values)
      while (res == 1):
        parameterNode.SetParameter(widget.name+str(i), ",".join("{0}".format(n) for n in values))
        i+=1
        res = transfertFunction.GetNodeValue(i, values)
      if (parameterNode.GetParameter(widget.name+str(i)) != ''):
        parameterNode.SetParameter(widget.name+str(i), '')
    elif widgetClassName == "qMRMLNodeComboBox":
      pass #TODO same as upper function
      
    for w in self.nodeSelectorWidgets:
      parameterNode.SetNodeReferenceID(w.name, w.currentNodeID)
    parameterNode.EndModify(oldModifiedState)

      
  def addGUIObservers(self):
    """!@brief Function to add observers to the GUI's widgets.

    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
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
        w.valuesChanged.connect(lambda value, w = w : self.updateParameterNodeFromGUI(value, w))
      elif widgetClassName == "qMRMLNodeComboBox":
        pass #TODO
    for w in self.nodeSelectorWidgets:
      w.connect("currentNodeIDChanged(Qstr)", lambda value, w = w : self.updateParameterNodeFromGUI(value, w))

  def removeGUIObservers(self):
    """!@brief Function to remove observers from the GUI's widgets.
    
    """  
    log.info(get_function_name()  + str(get_function_parameters_and_values())) 
    for w in self.widgets:
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton" :
        d = w.clicked.disconnect(self.updateParameterNodeFromGUI) 
        while d :
          d = w.clicked.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "QCheckBox":
        d = w.toggled.disconnect(self.updateParameterNodeFromGUI) 
        while d :
          d = w.toggled.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "QComboBox":
        d = w.currentIndexChanged.disconnect(self.updateParameterNodeFromGUI) 
        while d :
          d = w.currentIndexChanged.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "ctkSliderWidget":
        d = w.valueChanged.disconnect(self.updateParameterNodeFromGUI) 
        while d :
          d = w.valueChanged.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "ctkRangeWidget":
        d = w.valuesChanged.disconnect(self.updateParameterNodeFromGUI) 
        while d :
          d = w.valuesChanged.disconnect(self.updateParameterNodeFromGUI)
      """
      elif widgetClassName == "qMRMLNodeComboBox":
        while True :
          pass #TODO
      """

    for w in self.nodeSelectorWidgets:
      w.disconnect("currentNodeIDChanged(Qstr)", self.updateParameterNodeFromGUI)
    
  def onParameterNodeModified(self, observer, eventid):
    """!@brief Function to update the parameter node.


        observer {[type]}  [description]
        eventid {[type]}  [description]
    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    self.updateGUIFromParameterNode()

  def getText(self):
    """!@brief Function to create a window with input to get the file name.

    @return str File name.
    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    text = qt.QInputDialog.getText(qt.QMainWindow(), "Duplicate file name","Enter file name:", qt.QLineEdit.Normal, "")
    if text != '':
      return text

  def onDuplicateCustomShaderButtonClicked(self) :
    """!@brief Function to duplicate custom shader file.

    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    duplicateShaderFileName = self.getText()
    copiedShaderFileName = str(CustomShader.GetClassName(self.ui.customShaderCombo.currentText).__name__ + ".py")

    if (duplicateShaderFileName != None):
      duplicatedFile = self.duplicateFile(copiedShaderFileName, duplicateShaderFileName)

      if self.ui.errorMsgText != "" : 
        self.duplicateErrorMsg.text = self.ui.errorMsgText
        self.duplicateErrorMsg.show()
      else:
        qt.QDesktopServices.openUrl(qt.QUrl("file:///"+duplicatedFile, qt.QUrl.TolerantMode))
  

  def onOpenCustomShaderButtonClicked(self, caller=None, event=None) :
    """!@brief Function to open custom shader file.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    shaderPath = self.getPath(CustomShader.GetClassName(self.ui.customShaderCombo.currentText).__name__)
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+shaderPath, qt.QUrl.TolerantMode))

  def onEnableRotationCheckBoxToggled(self, caller=None, event=None) :
    """!@brief Function to enable rotating ROI box.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.ui.enableRotationCheckBox.isChecked():
      self.transformDisplayNode.SetEditorRotationEnabled(True)
    else :
      self.transformDisplayNode.SetEditorRotationEnabled(False)
  

  def onEnableScalingCheckBoxToggled(self, caller=None, event=None) :
    """!@brief Function to enable scaling ROI box.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.ui.enableScalingCheckBox.isChecked():
      self.transformDisplayNode.SetEditorScalingEnabled(True)
    else :
      self.transformDisplayNode.SetEditorScalingEnabled(False)


  def onEnableROICheckBoxToggled(self, caller=None, event=None):
    """!@brief Function to enable ROI cropping and show/hide ROI Display properties.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """   
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
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
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

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
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    currentShader = self.ui.customShaderCombo.currentText
    
    shaderName = CustomShader.GetClassName(currentShader).__name__
    shaderPackageName = 'Resources.Shaders'

    submoduleName = 'CustomShader'
    submodulePackageName = 'Resources'

    shaderPath = self.getPath(shaderName)
    modulePath = self.getPath(submoduleName, submodulePackageName)

    #reload modules
    with open(shaderPath, "rt") as fp:
      shaderModule = imp.load_module(shaderPackageName+'.'+shaderName, fp, shaderPath, ('.py', 'rt', imp.PY_SOURCE))
    
    with open(modulePath, "rt") as fp:
      customShaderModule = imp.load_module(submodulePackageName+'.'+submoduleName, fp, modulePath, ('.py', 'rt', imp.PY_SOURCE))

    #update globals
    clsmembers = inspect.getmembers(shaderModule, inspect.isclass)
    globals()[shaderName] = clsmembers[1][1]
    clsmembers = inspect.getmembers(customShaderModule, inspect.isclass)
    globals()[submoduleName] = clsmembers[0][1]
    
    try :
      volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
      volumePropertyNode.SetColor(self.transfertFunction)
    except :
      pass

    #reset customShader
    #reset UI
    self.logic.setupCustomShader()
    self.UpdateShaderParametersUI()    
    
    self.cleanup()

  def onModifyCustomShaderButtonClicked(self, caller=None, event=None):
    """!@brief Function to add the new shader replacement to a file.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """

    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    shaderTagType = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    shaderTag = shaderTagType[self.modifiedShaderTag]
    
    #get selected shader path
    modifiedShaderPath = self.getPath(CustomShader.GetClassName(self.modifiedShader).__name__) 
    #get shader code
    shaderCode = self.ui.shaderModifications.document().toPlainText()
    #indent shader code
    shaderCode =  textwrap.indent(shaderCode, 3 * '\t')
    tab = "\t\t"
    shaderReplacement = (
    "replacement =  \"\"\"/*your new shader code here*/\n" +
    shaderCode + "\n" +
    tab + "\"\"\"\n"+
    tab + "self.shaderProperty.AddFragmentShaderReplacement(\""+shaderTag+"\", True, replacement, False)\n" +
    tab + "#shaderreplacement")

    #modify file
    fin = open(modifiedShaderPath, "rt")
    data = fin.read()
    data = data.replace('#shaderreplacement', shaderReplacement)
    fin.close()

    fin = open(modifiedShaderPath, "wt")
    fin.write(data)
    fin.close()
    
    #open file window
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+modifiedShaderPath, qt.QUrl.TolerantMode))
    
    self.ui.addedMsg.setText("Code added to shader \""+self.modifiedShader+"\".")
    self.ui.addedMsg.show()

  def getPath(self, name, packageName = 'Resources/Shaders') :
    """!@brief Function to get a selected shader file path.


    @param name str : Name of the shader.

    
    @param packageName str : Name of the package in which the class in contained. (default: {'Resources/Shaders'})

    @return $nPath of the shader.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    class_ = CustomShader.GetClass(name)
    if class_ :
      path_ = os.path.join(self.prismPath(), packageName, str(class_.__name__) + '.py').replace("\\", "/")
      return path_
    
    return None

  def onShaderOpenFileButtonClicked(self, caller=None, event=None):
    """!@brief Function to open a file containing the new shader replacement.

    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    shaderTagType = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    shaderTag = shaderTagType[self.modifiedShaderTag]

    #get selected shader path
    modifiedShaderPath = self.getPath(CustomShader.GetClassName(self.modifiedShader).__name__)

    #modify file 
    tab = "\t\t"
    shaderReplacement = (
    "replacement = \"\"\"/*write your shader code here*/ \"\"\" \n " +
    tab + "self.shaderProperty.AddFragmentShaderReplacement(\""+shaderTag+"\", True, replacement, False) \n "+
    tab + "#shaderreplacement" )

    fin = open(modifiedShaderPath, "rt")
    data = fin.read()
    data = data.replace('#shaderreplacement', shaderReplacement)
    fin.close()

    fin = open(modifiedShaderPath, "wt")
    fin.write(data)
    fin.close()
    
    #open file window
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+modifiedShaderPath, qt.QUrl.TolerantMode))

  def updateComboBox(self, tab, comboBox, func):
    """!@brief Function to populate a combobox from an array.


    @param tab list : List to populate the combobox.
    @param comboBox QComboBox : ComboBox to be modified.
    @param func func : [Connect function when the ComboBox index is changed.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    
    comboBox.clear()  
    for e in tab:
      comboBox.addItem(e)
    comboBox.setCurrentIndex(len(tab)-1)
    comboBox.activated.connect(func)
    
  def onModifyCustomShaderComboIndexChanged(self, value):
    """!@brief Function to set which shader will be modified


    @param value list : current value of the comboBox.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

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
      self.addParamModifyShader.shaderDisplayName = self.ui.modifyCustomShaderCombo.currentText
      self.ui.ModifyCSTabs.visible = True

  def onShaderTagsTypeComboIndexChanged(self, value):
    """!@brief Function to set which shader tag type will be added to the shader.

    @param value list : current value of the comboBox.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    
    self.modifiedShaderTagType = self.ui.shaderTagsTypeCombo.currentText
    self.ui.shaderTagsCombo.show()
    self.ui.shaderTagsComboLabel.show()
    tab = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    self.updateComboBox(tab, self.ui.shaderTagsCombo, self.onShaderTagsComboIndexChanged)
 
  def onShaderTagsComboIndexChanged(self, value):
    """!@brief Function to set which shader tag will be added to the shader.


    @param value list : current value of the comboBox.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
  
    self.modifiedShaderTag = self.ui.shaderTagsCombo.currentText
    self.ui.shaderModificationsLabel.show()
    self.ui.shaderModifications.show()
    self.ui.shaderOpenFileButton.show()
    self.ui.modifyCustomShaderButton.show()


  def onNewCustomShaderButtonClicked(self):
    """!@brief Function to create a new file with the associated class.

    @return bool Returns False when an error occurs.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    self.className = self.ui.newCustomShaderNameInput.text
    self.displayName = self.ui.newCustomShaderDisplayInput.text
    self.addParamModifyShader.shaderDisplayName = self.ui.newCustomShaderDisplayInput.text
    self.newCustomShaderFile = self.duplicateFile("Template", self.className)
    if self.ui.errorMsgText != "" : 
      self.ui.errorMsg.text = self.ui.errorMsgText
      self.ui.errorMsg.show()
      self.ui.createCustomShaderButton.enabled = False
      return False
    else:
      self.ui.createCustomShaderButton.enabled = True

    if(self.newCustomShaderFile != False):
      self.ui.errorMsg.hide()
      self.addParamModifyShader.addParamCombo.show()
      self.addParamModifyShader.addParamLayout.itemAt(0,0).widget().show()
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
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    new_file_name = self.className
    file_path = os.path.realpath(__file__)
    file_dir, filename = os.path.split(file_path)
    file_dir = os.path.join(file_dir, 'Resources', 'Shaders')
    dst_file = os.path.join(file_dir, new_file_name + ".py")

    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+self.newCustomShaderFile, qt.QUrl.TolerantMode))

  def onModify(self):
    """!@brief Function to activate or deactivate the button to modify a custom shader.

    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    self.ui.modifyCustomShaderButton.enabled = len(self.ui.shaderModifications.document().toPlainText()) > 0

  def onSelect(self):
    """!@brief Function to activate or deactivate the button to create a custom shader.

    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    self.ui.createCustomShaderButton.enabled = len(self.ui.newCustomShaderNameInput.text) > 0 and len(self.ui.newCustomShaderDisplayInput.text) > 0
    self.ui.errorMsg.hide()

  def duplicateFile(self, old_file_name, new_file_name):
    """!@brief Function to create a new class from the template.


    @param old_file_name str : Name of the file that is being duplicated.
    @param new_file_name str : Name of the file that is being created.

    @return str Path of the newly created file.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    file_path = os.path.realpath(__file__)
    file_dir, filename = os.path.split(file_path)
    file_dir = os.path.join(file_dir, 'Resources', 'Shaders')
    
    src_file = os.path.join(file_dir, old_file_name)
    dst_file = os.path.join(file_dir, new_file_name + ".py")
    
    #check if file already exists
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
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    import os, sys
    import re

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
    """!@brief Function call to initialize the all user interface based on current scene.

    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    #import shaders
    for c in self.allClasses:
      __import__('Resources.Shaders.' + str(c.__name__))
    
    # init shader
    if self.ui.volumeRenderingCheckBox.isChecked() and self.ui.imageSelector.currentNode():
      self.logic.renderVolume(self.ui.imageSelector.currentNode())
      self.ui.imageSelector.currentNodeChanged.connect(lambda value, w = self.ui.imageSelector : self.onImageSelectorChanged(value, w))
      self.ui.imageSelector.nodeAdded.disconnect()
      self.UpdateShaderParametersUI()    

  #
  # Data callbacks
  #

  def onImageSelectorNodeAdded(self, calldata):
    """!@brief Callback function when a volume node is added to the scene by the user.
    @param calldata vtkMRMLVolumeNode : Volume node added (about to be added) to the scene.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    node = calldata
    if isinstance(node, slicer.vtkMRMLVolumeNode):
      # Call showVolumeRendering using a timer instead of calling it directly
      # to allow the volume loading to fully complete.
      
      if self.ui.volumeRenderingCheckBox.isChecked() and self.ui.imageSelector.currentNode() is None:
        self.ui.imageSelector.setCurrentNode(node)
        qt.QTimer.singleShot(0, lambda: self.logic.renderVolume(node))
        self.UpdateShaderParametersUI()
      self.ui.imageSelector.currentNodeChanged.connect(lambda value, w = self.ui.imageSelector : self.onImageSelectorChanged(value, w))
      self.ui.imageSelector.nodeAdded.disconnect()

  def onImageSelectorChanged(self, node, widget):
    """!@brief Callback function when the volume node has been changed in the dedicated combobox.
    Setup slice nodes to display selected node and render it in the 3d view.

    @param node vtkMRMLVolumeNode : Volume node selected in the scene.
    @param widget QObject : Widget modified.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
    
    if not node:
      return
    
    #if the selector is a parameter of a shader
    if widget != self.ui.imageSelector :
      self.logic.renderVolume(widget.currentNode(), True)

    elif self.ui.volumeRenderingCheckBox.isChecked():
      self.ui.volumeRenderingCheckBox.setChecked(False)
      self.ui.customShaderCombo.currentIndex = self.ui.customShaderCombo.count -1 
  #
  # View setup callbacks
  #

  def onVolumeRenderingCheckBoxToggled(self, caller=None, event=None):
    """!@brief Callback function when the volume rendering check box is toggled. Activate or deactivate 
    the rendering of the selected volume
    
    @param caller Caller of the function.
    @param event Event that triggered the function.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if self.ui.volumeRenderingCheckBox.isChecked():
      if self.ui.imageSelector.currentNode():

        self.logic.renderVolume(self.ui.imageSelector.currentNode())

        #init ROI
        allTransformDisplayNodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLTransformDisplayNode','TransformDisplayNode')
        if allTransformDisplayNodes.GetNumberOfItems() > 0:
          self.transformDisplayNode = allTransformDisplayNodes.GetItemAsObject(0)
        else:
          self.transformDisplayNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformDisplayNode')
          self.transformDisplayNode.SetName('TransformDisplayNode')
          self.transformDisplayNode.SetEditorRotationEnabled(False)

        allTransformNodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLTransformNode','TransformNode')
        if allTransformNodes.GetNumberOfItems() > 0:
          self.transformNode = allTransformNodes.GetItemAsObject(0)
        else:
          self.transformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
          self.transformNode.SetName('TransformNode')
          self.transformNode.SetAndObserveDisplayNodeID(self.transformDisplayNode.GetID())

        ROINodeID = self.logic.volumeRenderingDisplayNode.GetROINodeID()
        self.ROI = slicer.util.getNode(ROINodeID)
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
        if self.logic.secondVolumeRenderingDisplayNode:
          self.logic.secondVolumeRenderingDisplayNode.SetVisibility(False)
        self.ui.enableROICheckBox.setChecked(False)
        self.ui.displayROICheckBox.setChecked(False)
        self.ui.enableROICheckBox.hide()
        self.ui.displayROICheckBox.hide()
      self.ui.customShaderCollapsibleButton.hide()
      
  def resetROI(self):
    """!@brief Function to reset the ROI in the scene.

    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    ROINode = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLAnnotationROINode','AnnotationROI')
    if ROINode.GetNumberOfItems() > 0:
      # set node used before reload in the current instance
      ROINodes = ROINode.GetItemAsObject(0)
      ROINodes.ResetAnnotations()
      ROINodes.SetName("ROI")

  def onDisplayControlsCheckBoxToggled(self, caller=None, event=None):
    """!@brief Callback function triggered when the display controls check box is toggled.
        Show/hide in the VR view scene the controls at the location of the Windows Mixed Reality controllers.

    @param caller Caller of the function.
    @param event Event that triggered the function.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

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
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    self.logic.setCustomShaderType(self.ui.customShaderCombo.currentText)
    self.UpdateShaderParametersUI()
    self.updateParameterNodeFromGUI(self.ui.customShaderCombo.currentText, self.ui.customShaderCombo)
    self.updateGUIFromParameterNode()
    if i == (self.ui.customShaderCombo.count - 1):
      self.ui.openCustomShaderButton.setEnabled(False)
      self.ui.reloadCurrentCustomShaderButton.setEnabled(False)
      self.ui.duplicateCustomShaderButton.setEnabled(False)
    else :
      self.ui.openCustomShaderButton.setEnabled(True)
      self.ui.reloadCurrentCustomShaderButton.setEnabled(True)
      self.ui.duplicateCustomShaderButton.setEnabled(True)

  def addToWidgetList(self, widget, name):
    """!@brief Function to add a widget to self.widgets without duplicate.


    @param widget QObject : Widget to be added to the list.
    @param name str : Name of the widget.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))
   
    found = 0
    for i, w in enumerate(self.widgets):
      if w.name == name :
        found = 1
        self.widgets[i] = widget
      
    if not found :
      self.widgets.append(widget)

  def UpdateShaderParametersUI(self):
    """!@brief Updates the shader parameters on the UI.

    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    if not self.logic.customShader:
      return

    # Clear all the widgets except the combobox selector
    while self.ui.customShaderParametersLayout.count() != 1:
      item = self.ui.customShaderParametersLayout.takeAt(self.ui.customShaderParametersLayout.count() - 1)
      if item != None:
        widget = item.widget()
        if widget != None:
          state = widget.blockSignals(True)
          widget.setParent(None)
    try :
      self.logic.endPoints.RemoveAllMarkups()
    except :
      pass
    lenWidgets = len(self.widgets)
    
    CSName = self.ui.customShaderCombo.currentText.replace(" ", "")

    # Instanciate a slider for each floating parameter of the active shader
    params = self.logic.customShader.shaderfParams
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
      slider.setObjectName(CSName + p)
      slider.setValue(self.logic.customShader.getShaderParameter(p, float))
      slider.valueChanged.connect(lambda value, p=p : self.logic.onCustomShaderParamChanged(value, p, float) )
      slider.valueChanged.connect(lambda value, w = slider : self.updateParameterNodeFromGUI(value, w))
      slider.setParent(self.ui.customShaderParametersLayout)
      self.ui.customShaderParametersLayout.addRow(label, slider)
      
      self.addToWidgetList(slider, CSName+p)

    # Instanciate a slider for each integer parameter of the active shader
    params = self.logic.customShader.shaderiParams
    paramNames = params.keys()
    for p in paramNames:
      label = qt.QLabel(params[p]['displayName'])
      label.setMinimumWidth(80)
      slider = ctk.ctkSliderWidget()
      slider.minimum = params[p]['min']
      slider.maximum = params[p]['max']
      slider.singleStep = ( (slider.maximum - slider.minimum) * 0.05)
      slider.setObjectName(CSName+p)
      slider.setDecimals(0)
      slider.setValue(int(self.logic.customShader.getShaderParameter(p, int)))
      slider.valueChanged.connect(lambda value, p=p : self.logic.onCustomShaderParamChanged(value, p, int) )
      slider.valueChanged.connect(lambda value, w = slider : self.updateParameterNodeFromGUI(value, w))
      slider.setParent(self.ui.customShaderParametersLayout)
      self.ui.customShaderParametersLayout.addRow(label, slider)
      
      self.addToWidgetList(slider, CSName+p)
    
    # Instanciate a markup
    params = self.logic.customShader.shader4fParams
    paramNames = params.keys()
    if params:
      for p in paramNames:
        x = params[p]['defaultValue']['x']
        y = params[p]['defaultValue']['y']
        z = params[p]['defaultValue']['z']
        w = params[p]['defaultValue']['w']

        targetPointButton = qt.QPushButton("Initialize " + params[p]['displayName'])
        targetPointButton.setToolTip( "Place a markup" )
        targetPointButton.setObjectName(CSName+p)
        targetPointButton.clicked.connect(lambda _, name = p, btn = targetPointButton : self.logic.setPlacingMarkups(paramName = name, btn = btn,  interaction = 1))
        targetPointButton.clicked.connect(lambda value, w = slider : self.updateParameterNodeFromGUI(value, w))
        targetPointButton.setParent(self.ui.customShaderParametersLayout)
        self.ui.customShaderParametersLayout.addRow(qt.QLabel(params[p]['displayName']), targetPointButton)
        self.addToWidgetList(targetPointButton, CSName+p)
    
    params = self.logic.customShader.shaderrParams
    paramNames = params.keys()
    if params:
      for p in paramNames:
        label = qt.QLabel(params[p]['displayName'])
        label.setMinimumWidth(80)
        slider = ctk.ctkRangeWidget()
        slider.minimum = params[p]['defaultValue'][0]
        slider.minimumValue = params[p]['defaultValue'][0]
        slider.maximum = params[p]['defaultValue'][1]
        slider.maximumValue = params[p]['defaultValue'][1]
        slider.singleStep = ( (slider.maximum - slider.minimum) * 0.01 )
        slider.setObjectName(CSName+p)
        slider.setParent(self.ui.customShaderParametersLayout)
        slider.valuesChanged.connect(lambda min_, max_, p=p : self.logic.onCustomShaderParamChanged([min_, max_], p, "range") )
        slider.valuesChanged.connect(lambda value1, value2, w = slider : self.updateParameterNodeFromGUI([value1, value2], w))
        self.ui.customShaderParametersLayout.addRow(label, slider)

        self.addToWidgetList(slider, CSName+p)

    params = self.logic.customShader.shadertfParams
    paramNames = params.keys()
    if params:
      if self.logic.volumeRenderingDisplayNode is None :
        return
      for p in paramNames:
        label = qt.QLabel(params[p]['displayName'])
        widget = ctk.ctkVTKScalarsToColorsWidget()
        widget.setObjectName(CSName+p)
        volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
        #TODO find a way to keep the transfert function for each shader
        self.transfertFunction = vtk.vtkColorTransferFunction()
        self.transfertFunction.DeepCopy(volumePropertyNode.GetColor())
        transfertFunction = volumePropertyNode.GetColor()
        transfertFunction.AddObserver(vtk.vtkCommand.InteractionEvent, lambda o, e, w = widget : self.updateParameterNodeFromGUI([o,e], w))

        first = [0,0,0,0,0,0]
        last = [0,0,0,0,0,0]
        transfertFunction.GetNodeValue(0, first)
        transfertFunction.GetNodeValue(1, last)

        transfertFunction.RemoveAllPoints()
        transfertFunction.AdjustRange((0, 300))
        #first point in red
        transfertFunction.SetNodeValue(0 ,[0, 1, 0, 0, first[4], first[5]])
        #last point in blue
        transfertFunction.SetNodeValue(1 ,[300, 0, 0, 1, last[4], last[5]])
       
        widget.view().addColorTransferFunction(transfertFunction)
        widget.view().setAxesToChartBounds()
        widget.setFixedHeight(100)
        widget.view().show()
        
        self.addToWidgetList(widget, CSName+p)
        self.ui.customShaderParametersLayout.addRow(label, widget)
  
    params = self.logic.customShader.shadervParams
    paramNames = params.keys()
    if params:
      for p in paramNames:
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
        imageSelector.setObjectName(CSName+p)

        self.addToWidgetList(imageSelector, CSName+p)
        self.ui.customShaderParametersLayout.addRow(label, imageSelector)
        imageSelector.currentNodeChanged.connect(lambda value, w = imageSelector : self.onImageSelectorChanged(value, w))
        imageSelector.currentNodeChanged.connect(lambda value, w = imageSelector : self.updateParameterNodeFromGUI(value, w))
    
  def prismPath(self) :
    """!@brief Function to get the module's path.

    @return str Module's path.
    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    return os.path.dirname(eval('slicer.modules.prism.path'))

  def onReload(self):
    """!@brief Reload the modules.

    """
    log.info(get_function_name()  + str(get_function_parameters_and_values()))

    log.debug("Reloading Packages")
    packageName='Resources'
    submoduleNames = ['CustomShader']
    
    for submoduleName in submoduleNames :
      modulePath = self.getPath(submoduleName, packageName)

      with open(modulePath, "rt") as fp:
        imp.load_module(packageName+'.'+submoduleName, fp, modulePath, ('.py', 'rt', imp.PY_SOURCE))

    log.debug("Reloading Shaders")
    shaderNames = []
    for c in self.allClasses:
      shaderNames.append(c.__name__)
    
    shaderPackageName = "Resources.Shaders"
    
    for shaderName in shaderNames :
      shaderPath = self.getPath(shaderName)
      with open(shaderPath, "rt") as fp:
        imp.load_module(shaderPackageName+'.'+shaderName, fp, shaderPath, ('.py', 'rt', imp.PY_SOURCE))

    log.debug("Reloading PRISM")
    packageNames=['PRISM', 'PRISMLogic']
    
    for packageName in packageNames :
      with open(shaderPath, "rt") as fp:
          imp.load_module(packageName, fp, self.prismPath(), ('.py', 'rt', imp.PY_SOURCE))

    self.cleanup()

    globals()['PRISM'] = slicer.util.reloadScriptedModule('PRISM')
    
    try :
      volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
      volumePropertyNode.SetColor(self.transfertFunction)
    except :
      pass

  def cleanup(self):
    self.resetROI()
    self.ui.enableROICheckBox.setChecked(False)
    self.ui.displayROICheckBox.setChecked(False)
    self.removeGUIObservers()
    try :
      slicer.mrmlScene.RemoveNode(self.transformNode)
      slicer.mrmlScene.RemoveNode(self.transformDisplayNode)
    except: 
      pass