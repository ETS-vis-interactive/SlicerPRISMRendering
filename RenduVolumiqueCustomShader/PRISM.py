import os, sys
import unittest
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

from Resources.ModifyParamWidget import ModifyParamWidget
from Resources.CustomShader import CustomShader

def dumpFunctionName(func):
  def echoFunction(*args,**kwargs):
    print('')
    print('Start func: {}'.format(func.__name__))
    return func(*args, **kwargs)
  return echoFunction
    
#
# PRISM
#
class PRISMSaveDataDialog:
  def __init__(self, parent):
    self.parent = parent
    parent.fileType = 'PRISMFile'
    parent.description = 'PRISM'
    parent.action = slicer.qSlicerSaveDataDialog.Write  

class PRISM(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PRISM"
    self.parent.categories = ["Projet"]
    self.parent.dependencies = []
    self.parent.contributors = ["Simon Drouin"]
    self.parent.helpText = """A scripted module to edit custom volume rendering shaders."""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText =""" This file was developped by Simon Drouin at Ecole de Technologie Superieure (Montreal, Canada)"""
#
# PRISMWidget
#

class PRISMWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  
  def setup(self):
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
    self.ui.imageSelector.connect("nodeAdded(vtkMRMLNode*)", self.onImageSelectorNodeAdded)

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
          
    # populate combobox
    self.updateComboBox(allShaderTypes, self.ui.modifyCustomShaderCombo, self.onModifyCustomShaderComboIndexChanged)
    self.updateComboBox(list(self.allShaderTagTypes.keys()), self.ui.shaderTagsTypeCombo, self.onShaderTagsTypeComboIndexChanged)

    self.ui.shaderTagsCombo.hide()
    self.ui.shaderTagsComboLabel.hide()
    self.ui.shaderModificationsLabel.hide()
    self.ui.shaderModifications.hide()
    self.ui.shaderOpenFileButton.hide()
    self.ui.modifyCustomShaderButton.hide()
    self.ui.errorMsg.hide()
    self.ui.addedMsg.hide()
    self.ui.editSourceButton.hide()

    self.ui.errorMsg.setStyleSheet("color: red")

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
    
    #
    # Creation of Custom Shader Area
    #
    
    self.addParamCreateShader = ModifyParamWidget()
    self.addParamCreateShader.addParamButtonState()
    self.ui.emptyText2.hide()
    self.ui.newCustomShaderLayout.addLayout(self.addParamCreateShader.addParamLayout, 0, 0)
    self.ui.newCustomShaderLayout.addLayout(self.addParamCreateShader.paramLayout, 1, 0)
    
    # Initialize state
    self.onSelect()
    self.onModify()
    self.initState()
    self.currXAngle = 0.0
    self.currYAngle = 0.0
    self.currZAngle = 0.0

    #save widgets
    self.widgets = self.ui.centralWidget.findChildren(qt.QCheckBox())  \
    + self.ui.centralWidget.findChildren(qt.QPushButton()) \
    + self.ui.centralWidget.findChildren(qt.QComboBox())
    self.nodeSelectorWidgets = [self.ui.imageSelector, self.ui.parametersNodeSelector]
    
    # Set parameter node (widget will observe it)
    self.updateNodeSelector()
    self.setAndObserveParameterNode()
    self.addGUIObservers()
    # Update GUI  
    self.updateGUIFromParameterNode()


  
  def updateNodeSelector(self):
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
    self.removeGUIObservers()

    if self.logic.parameterNode and self.logic.parameterNodeObserver:
      slicer.mrmlScene.RemoveObserver(self.logic.parameterNodeObserver)
  
  
  def setAndObserveParameterNode(self, caller=None, event=None):
    # Remove observer to old parameter node
    if self.logic.parameterNode and self.logic.parameterNodeObserver:
      self.logic.parameterNode.RemoveObserver(self.logic.parameterNodeObserver)
      self.logic.parameterNodeObserver = None
    # Set and observe new parameter node
    self.logic.parameterNode = self.ui.parametersNodeSelector.currentNode()
    if self.logic.parameterNode:
      self.logic.parameterNodeObserver = self.logic.parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onParameterNodeModified)

  
  def getClassName(self, widget):
    import sys
    if sys.version_info.major == 2:
      return widget.metaObject().className()
    else:
      return widget.metaObject().getClassName()

  
  def updateGUIFromParameterNode(self, caller=None, event=None):
    if not self.logic.parameterNode:
      return
    parameterNode = self.logic.parameterNode

    if parameterNode.GetParameterCount() == 0:
      return
    
    #disables updateParameterNodeFromGUI signal 
    self.removeGUIObservers()
    print(self.widgets)
    for w in self.widgets:
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton":
        enabled = (int(parameterNode.GetParameter(w.name)) != 0)
        w.setEnabled(enabled)
      elif widgetClassName=="QCheckBox":
        checked = (int(parameterNode.GetParameter(w.name)) != 0)
        w.setChecked(checked)
      elif widgetClassName=="QComboBox" or widgetClassName == "ctkComboBox":
        index = int(parameterNode.GetParameter(w.name))
        w.setCurrentIndex(index)
      elif widgetClassName=="ctkSliderWidget":
        value = float(parameterNode.GetParameter(w.name))
        w.setValue(value)
      elif widgetClassName=="ctkRangeWidget":
        values = parameterNode.GetParameter(w.name).split(',')     
        w.minimumValue = float(values[0])
        w.maximumValue = float(values[1])
    
    for w in self.nodeSelectorWidgets:
      oldBlockSignalsState =w.blockSignals(True)
      w.setCurrentNodeID(parameterNode.GetNodeReferenceID(w.name))
      w.blockSignals(oldBlockSignalsState)

    self.addGUIObservers()

  
  def updateParameterNodeFromGUI(self, caller = None, event= None):
    parameterNode = self.logic.parameterNode
    oldModifiedState = parameterNode.StartModify()

    if self.ui.imageSelector.currentNode() is None:
      return 

    parameterNode.SetParameter("volumePath", self.ui.imageSelector.currentNode().GetStorageNode().GetFileName())
    for w in self.widgets :
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton" :
        parameterNode.SetParameter(w.name, "1") if w.enabled else parameterNode.SetParameter(w.name, "0")
      elif widgetClassName == "QCheckBox":
        parameterNode.SetParameter(w.name, "1") if w.checked else parameterNode.SetParameter(w.name, "0")
      elif widgetClassName == "QComboBox" or widgetClassName == "ctkComboBox" :
        parameterNode.SetParameter(w.name, str(w.currentIndex))
      elif widgetClassName == "ctkSliderWidget":
        parameterNode.SetParameter(w.name, str(w.value))
      elif widgetClassName == "ctkRangeWidget":
        parameterNode.SetParameter(w.name, str(w.minimumValue) + ',' + str(w.maximumValue))
    
    for w in self.nodeSelectorWidgets:
      parameterNode.SetNodeReferenceID(w.name, w.currentNodeID)
    parameterNode.EndModify(oldModifiedState)
    
  
  def addGUIObservers(self):
    for w in self.widgets:
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton" :
        w.clicked.connect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "QCheckBox":
        w.toggled.connect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "QComboBox" or widgetClassName == "ctkComboBox" :
        w.currentIndexChanged.connect(self.updateParameterNodeFromGUI)

    for w in self.nodeSelectorWidgets:
      w.connect("currentNodeIDChanged(QString)", self.updateParameterNodeFromGUI)

  
  def removeGUIObservers(self):
    for w in self.widgets:
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton" :
        w.clicked.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "QCheckBox":
        w.toggled.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "QComboBox" or widgetClassName == "ctkComboBox" :
        w.currentIndexChanged.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "ctkSliderWidget":
        w.valueChanged.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == "ctkRangeWidget":
        w.valuesChanged.disconnect(self.updateParameterNodeFromGUI)

    for w in self.nodeSelectorWidgets:
      w.disconnect("currentNodeIDChanged(QString)", self.updateParameterNodeFromGUI)
    
  
  def onParameterNodeModified(self, observer, eventid):
    self.updateGUIFromParameterNode()

  
  def getText(self):
    """ Function to create a window with input to get the file name.

    """ 
    text = qt.QInputDialog.getText(qt.QMainWindow(), "Duplicate file name","Enter file name:", qt.QLineEdit.Normal, "")
    if text != '':
      return text

  
  def onDuplicateCustomShaderButtonClicked(self) :
    """ Function to duplicate custom shader file.

    """ 
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
    """ Function to open custom shader file.

    """
    shaderPath = self.getPath(CustomShader.GetClassName(self.ui.customShaderCombo.currentText).__name__)
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+shaderPath, qt.QUrl.TolerantMode))

  
  def onEnableRotationCheckBoxToggled(self, caller=None, event=None) :
    """ Function to enable rotating ROI box.

    """
    #FIXME 'PRISMWidget' object has no attribute 'transformDisplayNode'
    if self.ui.enableRotationCheckBox.isChecked():
      self.transformDisplayNode.SetEditorRotationEnabled(True)
    else :
      self.transformDisplayNode.SetEditorRotationEnabled(False)
  

  
  def onEnableScalingCheckBoxToggled(self, caller=None, event=None) :
    """ Function to enable scaling ROI box.

    """
    if self.ui.enableScalingCheckBox.isChecked():
      self.transformDisplayNode.SetEditorScalingEnabled(True)
    else :
      self.transformDisplayNode.SetEditorScalingEnabled(False)


  
  def onEnableROICheckBoxToggled(self, caller=None, event=None):
    """ Function to enable ROI cropping and show/hide ROI Display properties.

    """
    if self.ui.enableROICheckBox.isChecked():
      self.logic.volumeRenderingDisplayNode.SetCroppingEnabled(True)
      self.ui.displayROICheckBox.show()
    else:
      self.logic.volumeRenderingDisplayNode.SetCroppingEnabled(False)
      self.ui.displayROICheckBox.hide()
      self.ui.displayROICheckBox.setChecked(False)

  
  def onDisplayROICheckBoxToggled(self, caller=None, event=None):
    """ Function to display ROI box and show/hide scaling and rotation parameters.

    """
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
    """ Function to reload the current custom shader.

    """
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
    """ Function to add the new shader replacement to a file.

    """
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
    """ Function to get a selected shader file path.

    """
    class_ = CustomShader.GetClass(name)
    if class_ :
      path_ = os.path.join(self.prismPath(), packageName, str(class_.__name__) + '.py').replace("\\", "/")
      return path_
    
    return None

  
  def onShaderOpenFileButtonClicked(self, caller=None, event=None):
    """ Function to open a file containing the new shader replacement.

    """
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
    """ Function to populate a combobox from an array.

    Args:
        tab (list): List to populate the combobox.
        comboBox (qt.QComboBox): ComboBox to be modified.
        func (func): Connect function when the ComboBox index is changed.
    """
    comboBox.clear()  
    for e in tab:
      comboBox.addItem(e)
    comboBox.setCurrentIndex(len(tab)-1)
    comboBox.activated.connect(func)
  
  
  def onModifyCustomShaderComboIndexChanged(self, value):
    """ Function to set which shader will be modified.

    Args:
        value (list): current value of the comboBox.
    """
    self.modifiedShader = self.ui.modifyCustomShaderCombo.currentText
    self.addParamModifyShader.shaderDisplayName = self.ui.modifyCustomShaderCombo.currentText
    self.ui.ModifyCSTabs.visible = True

    try :
      volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
      volumePropertyNode.SetColor(self.transfertFunction)
    except :
      pass


  
  def onShaderTagsTypeComboIndexChanged(self, value):
    """ Function to set which shader tag type will be added to the shader.

    Args:
        value (list): current value of the comboBox.
    """
    self.modifiedShaderTagType = self.ui.shaderTagsTypeCombo.currentText
    self.ui.shaderTagsCombo.show()
    self.ui.shaderTagsComboLabel.show()
    tab = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    self.updateComboBox(tab, self.ui.shaderTagsCombo, self.onShaderTagsComboIndexChanged)
 
  
  def onShaderTagsComboIndexChanged(self, value):
    """ Function to set which shader tag will be added to the shader.

    Args:
        value (list): current value of the comboBox.
    """
    self.modifiedShaderTag = self.ui.shaderTagsCombo.currentText
    self.ui.shaderModificationsLabel.show()
    self.ui.shaderModifications.show()
    self.ui.shaderOpenFileButton.show()
    self.ui.modifyCustomShaderButton.show()


  
  def onNewCustomShaderButtonClicked(self):
    """ Function to create a new file with the associated class.

    """
    self.className = self.ui.newCustomShaderNameInput.text
    self.displayName = self.ui.newCustomShaderDisplayInput.text
    self.addParamCreateShader.shaderDisplayName = self.ui.newCustomShaderDisplayInput.text
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
      self.addParamCreateShader.addParamCombo.show()
      self.addParamCreateShader.addParamLayout.itemAt(0,0).widget().show()
      self.setup_file(self.newCustomShaderFile, self.className, self.displayName)
      self.ui.editSourceButton.show()
      CustomShader.GetAllShaderClassNames()
      self.ui.customShaderCombo.addItem(self.displayName)
      self.ui.createCustomShaderButton.enabled = False
      self.ui.newCustomShaderNameInput.setEnabled(False)
      self.ui.newCustomShaderDisplayInput.setEnabled(False)

  
  def onEditSourceButtonClicked(self):
    """ Function to create a new file with the custom shader and open the file in editor

    """
    new_file_name = self.className
    file_path = os.path.realpath(__file__)
    file_dir, filename = os.path.split(file_path)
    file_dir = os.path.join(file_dir, 'Resources', 'Shaders')
    dst_file = os.path.join(file_dir, new_file_name + ".py")

    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+self.newCustomShaderFile, qt.QUrl.TolerantMode))

  
  def onModify(self):
    """ Function to activate or deactivate the button to modify a custom shader

    """
    self.ui.modifyCustomShaderButton.enabled = len(self.ui.shaderModifications.document().toPlainText()) > 0

  
  def onSelect(self):
    """ Function to activate or deactivate the button to create a custom shader

    """
    self.ui.createCustomShaderButton.enabled = len(self.ui.newCustomShaderNameInput.text) > 0 and len(self.ui.newCustomShaderDisplayInput.text) > 0
    self.ui.errorMsg.hide()

  
  def duplicateFile(self, old_file_name, new_file_name):
    """ Function to create a new class from the template

    """

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
    """ Function to modify the new class with regex to match the given infos

    """
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
    """ Function call to initialize the all user interface based on current scene.
    """ 
    #import shaders
    for c in self.allClasses:
      __import__('Resources.Shaders.' + str(c.__name__))
    
    # init shader
    if self.ui.volumeRenderingCheckBox.isChecked() and self.ui.imageSelector.currentNode():
      self.logic.renderVolume(self.ui.imageSelector.currentNode())
      self.ui.imageSelector.currentNodeChanged.connect(self.onImageSelectorChanged)
      self.ui.imageSelector.nodeAdded.disconnect()
      self.UpdateShaderParametersUI()    

  #
  # Data callbacks
  #

  
  def onImageSelectorNodeAdded(self, calldata):
    """ Callback function when a volume node is added to the scene by the user.

    Args:
        calldata (vtkMRMLVolumeNode): Volume node added (about to be added) to the scene.
    """
    node = calldata
    if isinstance(node, slicer.vtkMRMLVolumeNode):
      # Call showVolumeRendering using a timer instead of calling it directly
      # to allow the volume loading to fully complete.
      
      if self.ui.volumeRenderingCheckBox.isChecked() and self.ui.imageSelector.currentNode() is None:
        self.ui.imageSelector.setCurrentNode(node)
        qt.QTimer.singleShot(0, lambda: self.logic.renderVolume(node))
        self.UpdateShaderParametersUI()
      self.ui.imageSelector.currentNodeChanged.connect(self.onImageSelectorChanged)
      self.ui.imageSelector.nodeAdded.disconnect()

  
  def onImageSelectorChanged(self, node):
    """ Callback function when the volume node has been changed in the dedicated combobox.
        Setup slice nodes to display selected node and render it in the 3d view.
    """
    if not node:
      return
    
    # render selected volume
    if self.ui.volumeRenderingCheckBox.isChecked():
      self.ui.volumeRenderingCheckBox.setChecked(False)
      self.ui.volumeRenderingCheckBox.setChecked(True)

  #
  # View setup callbacks
  #

  
  def onVolumeRenderingCheckBoxToggled(self, caller=None, event=None)      :
    """ Callback function when the volume rendering check box is toggled. Activate or deactivate 
    the rendering of the selected volume.
    """
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
        self.ui.enableROICheckBox.setChecked(False)
        self.ui.displayROICheckBox.setChecked(False)
        self.ui.enableROICheckBox.hide()
        self.ui.displayROICheckBox.hide()
        self.ui.customShaderCombo.currentIndex = self.ui.customShaderCombo.count -1 
      self.ui.customShaderCollapsibleButton.hide()
      
  
  def resetROI(self):
    """ Function to reset the ROI in the scene.
    
    """
    ROINode = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLAnnotationROINode','AnnotationROI')
    if ROINode.GetNumberOfItems() > 0:
      # set node used before reload in the current instance
      ROINodes = ROINode.GetItemAsObject(0)
      ROINodes.ResetAnnotations()
      ROINodes.SetName("ROI")

  
  def onDisplayControlsCheckBoxToggled(self, caller=None, event=None):
    """ Callback function triggered when the display controls check box is toggled.
        Show/hide in the VR view scene the controls at the location of the Windows Mixed Reality controllers.
    """
    if self.displayControlsCheckBox.isChecked():
      self.logic.vrhelper.showVRControls()
    else:
      self.logic.hideVRControls()

  #
  # Volume rendering callbacks
  #

  
  def onCustomShaderComboIndexChanged(self, i):
    """ Callback function when the custom shader combo box is changed.

    Args:
    i (int) : index of the element
    """
    if i == (self.ui.customShaderCombo.count - 1):
      self.ui.openCustomShaderButton.setEnabled(False)
      self.ui.reloadCurrentCustomShaderButton.setEnabled(False)
      self.ui.duplicateCustomShaderButton.setEnabled(False)
    else :
      self.ui.openCustomShaderButton.setEnabled(True)
      self.ui.reloadCurrentCustomShaderButton.setEnabled(True)
      self.ui.duplicateCustomShaderButton.setEnabled(True)
    
    self.logic.setCustomShaderType(self.ui.customShaderCombo.currentText)
    self.UpdateShaderParametersUI()

  
  def UpdateShaderParametersUI(self):
    """ Updates the shader parameters on the UI.

    """
    if not self.logic.customShader:
      return
    # Clear all the widgets except the combobox selector
    while self.ui.customShaderParametersLayout.count() != 1:
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

    #FIXME parameters are saved with self.logic.parameterNode but are erased while going through this function
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
      slider.setObjectName(p)
      slider.setValue(self.logic.customShader.getShaderParameter(p, float))
      slider.valueChanged.connect(lambda value, p=p : self.logic.onCustomShaderParamChanged(value, p, float) )
      slider.valueChanged.connect(lambda value : self.updateParameterNodeFromGUI(value))
      slider.setParent(self.ui.customShaderParametersLayout)
      self.ui.customShaderParametersLayout.addRow(label,slider)
      self.widgets += (slider,)

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
      slider.setObjectName(p)
      slider.setDecimals(0)
      slider.setValue(int(self.logic.customShader.getShaderParameter(p, int)))
      slider.valueChanged.connect(lambda value, p=p : self.logic.onCustomShaderParamChanged(value, p, int) )
      slider.valueChanged.connect(lambda value : self.updateParameterNodeFromGUI(value))
      slider.setParent(self.ui.customShaderParametersLayout)
      self.ui.customShaderParametersLayout.addRow(label,slider)
      self.widgets += (slider,)
    
    #TODO add to widget list to save parameter in the scene
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
        targetPointButton.setObjectName(p)
        targetPointButton.clicked.connect(lambda _, name = p, btn = targetPointButton : self.logic.setPlacingMarkups(paramName = name, btn = btn,  interaction = 1))
        targetPointButton.setParent(self.ui.customShaderParametersLayout)
        self.ui.customShaderParametersLayout.addRow(qt.QLabel(params[p]['displayName']), targetPointButton)
      
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
        slider.setObjectName(p)
        slider.setParent(self.ui.customShaderParametersLayout)
        slider.valuesChanged.connect(lambda min_, max_, p=p : self.logic.onCustomShaderParamChanged([min_, max_], p, "range") )
        slider.valueChanged.connect(lambda value : self.updateParameterNodeFromGUI(value))
        self.ui.customShaderParametersLayout.addRow(label,slider)
        self.widgets += (slider,)

    #TODO add to widget list to save parameter in the scene
    params = self.logic.customShader.shadertfParams
    paramNames = params.keys()
    if params:
      if self.logic.volumeRenderingDisplayNode is None :
        return
      for p in paramNames:
        volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
        label = qt.QLabel(params[p]['displayName'])
        widget = ctk.ctkVTKScalarsToColorsWidget()
        transfertFunction = volumePropertyNode.GetColor()
        self.transfertFunction = vtk.vtkColorTransferFunction()
        self.transfertFunction.DeepCopy(volumePropertyNode.GetColor())
        first = [0,0,0,0,0,0]
        last = [0,0,0,0,0,0]
        transfertFunction.GetNodeValue(0, first)
        transfertFunction.GetNodeValue(1, last)

        transfertFunction.AdjustRange((0,1))
        transfertFunction.AdjustRange((0,300))
        transfertFunction.SetNodeValue(0 ,[0, 1, 0, 0, first[4], first[5]])
        transfertFunction.SetNodeValue(1 ,[300, 0, 0, 1, last[4], last[5]])
        
        widget.view().addColorTransferFunction(transfertFunction)
        widget.view().setAxesToChartBounds()
        widget.setFixedHeight(100)
        widget.view().show()

        self.ui.customShaderParametersLayout.addRow(label, widget)
    
    #check if widgets have been added
    if (len(self.widgets) > lenWidgets):
      self.updateGUIFromParameterNode()

  
  def prismPath(self) :
    """ Returns the module.

    """
    return os.path.dirname(eval('slicer.modules.prism.path'))

  
  def onReload(self):
    """ Reload the modules.

    """
    logging.debug("Reloading Packages")
    packageName='Resources'
    submoduleNames = ['CustomShader']
    
    for submoduleName in submoduleNames :
      modulePath = self.getPath(submoduleName, packageName)

      with open(modulePath, "rt") as fp:
        imp.load_module(packageName+'.'+submoduleName, fp, modulePath, ('.py', 'rt', imp.PY_SOURCE))

    logging.debug("Reloading Shaders")
    shaderNames = []
    for c in self.allClasses:
      shaderNames.append(c.__name__)
    
    shaderPackageName = "Resources.Shaders"
    
    for shaderName in shaderNames :
      shaderPath = self.getPath(shaderName)
      with open(shaderPath, "rt") as fp:
        imp.load_module(shaderPackageName+'.'+shaderName, fp, shaderPath, ('.py', 'rt', imp.PY_SOURCE))

    logging.debug("Reloading PRISM")
    packageName='PRISM'
    
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
    try :
      slicer.mrmlScene.RemoveNode(self.transformNode)
      slicer.mrmlScene.RemoveNode(self.transformDisplayNode)
    except: 
      pass

  
##################################################################################
# PRISMLogic
##################################################################################

class PRISMLogic(ScriptedLoadableModuleLogic):
  
  
  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    self.createEndPoints()

    # VR interaction parameters
    self.movingEntry = False
    self.moveRelativePosition = False

    # init volume rendering active node
    self.volumeRenderingDisplayNode = None

    # hide volume rendering display node possibly loaded with the scene
    renderingDisplayNodes = slicer.util.getNodesByClass("vtkMRMLVolumeRenderingDisplayNode")
    for displayNode in renderingDisplayNodes:
      displayNode.SetVisibility(False)
    renderingDisplayNodes = None

    # By default, no special shader is applied
    self.customShaderType = 'None'
    self.customShader = None
    
    self.pointType = ''
    self.centerPointIndex = -1
    self.targetPointIndex = -1
    self.entryPointIndex = -1
    self.currentMarkupBtn = None
    self.parameterNode = None
    self.parameterNodeObserver = None
    self.addObservers()
  


  
  def enableCarving(self, paramName, type_, checkBox) :
    if checkBox.isChecked() :  
      if paramName == 'sphere' :
        self.radiusSlider[0].show()
        self.radiusSlider[1].show()
        self.centerButton[0].show()
        self.centerButton[1].show()
      self.carvingEnabled = 1
    else: 
      self.carvingEnabled = 0
      if paramName == 'sphere' :
        self.radiusSlider[0].hide()
        self.radiusSlider[1].hide()
        self.centerButton[0].hide()
        self.centerButton[1].hide()
        self.endPoints.RemoveAllMarkups()

    self.customShader.setShaderParameter(paramName, self.carvingEnabled, type_)

  
  def addObservers(self):
    """ Create all observers needed in the UI to ensure a correct behaviour
    """
    self.pointModifiedEventTag = self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.onEndPointsChanged)
    self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.onEndPointAdded)
    slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)  

  #
  # End points functions
  #

  @vtk.calldata_type(vtk.VTK_INT)
  
  def onEndPointsChanged(self, caller, event, call_data):
    """ Callback function to get the position of the modified point
    Note: @vtk.calldata_type(vtk.VTK_OBJECT) function get calling instance as a vtkMRMLNode to be accesed in the function.

    Args:
        caller (slicer.mrmlScene): Slicer active scene.
        event (string): Flag corresponding to the triggered event.
        call_data (vtkMRMLNode): Node added to the scene.
    """

    #check if the point was added from the module and was set
    if (call_data == self.centerPointIndex or call_data == self.entryPointIndex or call_data == self.targetPointIndex ):
      name = caller.GetNthFiducialLabel(call_data)
      world = [0, 0, 0, 0]
      caller.GetNthFiducialWorldCoordinates(call_data, world)
      self.onCustomShaderParamChanged(world, name, "markup")
    
  
  def onEndPointAdded(self, caller, event):
    """ Callback function to get the position of the new point.
    Args:
        caller (slicer.mrmlScene): Slicer active scene.
        event (string): Flag corresponding to the triggered event.
    """
    world = [0, 0, 0, 0]

    if (self.pointType == 'center'):
      
      pointIndex = caller.GetDisplayNode().GetActiveControlPoint()
      caller.GetNthFiducialWorldCoordinates(pointIndex, world)
      if self.centerPointIndex != -1 :
        caller.SetNthFiducialWorldCoordinates(self.centerPointIndex, world)
        caller.RemoveNthControlPoint(pointIndex)
      else :
        caller.SetNthFiducialLabel(pointIndex, self.pointType)
        self.centerPointIndex = pointIndex
      
      self.onCustomShaderParamChanged(world, self.pointType, "markup")
      self.currentMarkupBtn.setText('Reset ' + self.pointType)
      self.pointType  = ''

    elif (self.pointType == 'entry'):
      pointIndex = caller.GetDisplayNode().GetActiveControlPoint()
      caller.GetNthFiducialWorldCoordinates(pointIndex, world)
      
      if self.entryPointIndex != -1 :
        caller.SetNthFiducialWorldCoordinates(self.entryPointIndex, world)
        caller.RemoveNthControlPoint(pointIndex)
      else :
        caller.SetNthFiducialLabel(pointIndex, self.pointType)
        self.entryPointIndex = pointIndex
      
      self.onCustomShaderParamChanged(world, self.pointType, "markup")
      self.currentMarkupBtn.setText('Reset ' + self.pointType)
      self.pointType  = ''

    elif (self.pointType == 'target'):
      pointIndex = caller.GetDisplayNode().GetActiveControlPoint()
      caller.GetNthFiducialWorldCoordinates(pointIndex, world)
      
      if self.targetPointIndex != -1 :
        caller.SetNthFiducialWorldCoordinates(self.targetPointIndex, world)
        caller.RemoveNthControlPoint(pointIndex)
      else :
        caller.SetNthFiducialLabel(pointIndex, self.pointType)
        self.targetPointIndex = pointIndex
      
      self.onCustomShaderParamChanged(world, self.pointType, "markup")
      self.currentMarkupBtn.setText('Reset ' + self.pointType)
      self.pointType  = ''

  
  def deleteNodes(self):
    try :
      node = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")
      slicer.mrmlScene.RemoveNode(node[0])
      slicer.mrmlScene.RemoveNode(self.shaderPropertyNode)
      slicer.mrmlScene.RemoveNode(self.endPoints)
      CustomShader.clear()
    except:
      pass


  
  def setPlacingMarkups(self, paramName, btn, interaction = 1, persistence = 0):
    """ Activate Slicer markups module to set one or multiple markups in the given markups fiducial list.

    Args:
        markupsFiducialNode (vtkMRMLMarkupsFiducialNode): List in which adding new markups.
        interaction (int): 0: /, 1: place, 2: view transform, 3: / ,4: Select
        persistence (int): 0: unique, 1: peristent
    """
    self.currentMarkupBtn = btn
    interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    interactionNode.SetCurrentInteractionMode(interaction)
    interactionNode.SetPlaceModePersistence(persistence)
    
    self.pointType = paramName
    
  
  def onCustomShaderParamChanged(self, value, paramName, type_ ):
    """ Change the custom parameters in the shader.

    Args:
        value : value to be changed
        paramName (int): name of the parameter to be changed
        type_ (float or type): type of the parameter to be changed
    """
    self.customShader.setShaderParameter(paramName, value, type_)

  
  def createEndPoints(self):
    # retrieve end points in the scene or create the node
    allEndPoints = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsFiducialNode','EndPoints')
    if allEndPoints.GetNumberOfItems() > 0:
      # set node used before reload in the current instance
      self.endPoints = allEndPoints.GetItemAsObject(0)
      self.endPoints.RemoveAllMarkups()
      self.endPoints.GetDisplayNode().SetGlyphScale(6.0)
    else:
      self.endPoints = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
      self.endPoints.SetName("EndPoints")
      self.endPoints.GetDisplayNode().SetGlyphScale(6.0)
      self.endPoints.RemoveAllMarkups()
    allEndPoints = None 
  
  
  def getEntry(self):
    """ Get Entry point position. If not yet placed, return (0,0,0).

    Returns:
        array[double]: Entry markups position if placed, empty array if not.
    """
    entry = [0, 0, 0]
    if self.endPoints.GetNumberOfControlPoints() >= 2:
      self.endPoints.GetNthFiducialPosition(1, entry)
    return entry
  
  
  def setEntry(self,entry):
    self.endPoints.SetNthFiducialPositionFromArray(1, entry)

  
  def getTarget(self):
    """ Get Target point position. If not yet placed, return (0,0,0).

    Returns:
        array[double]: Entry markups position if placed, empty array if not.
    """
    target = [0, 0, 0]
    if self.endPoints.GetNumberOfControlPoints() >= 1:
      self.endPoints.GetNthFiducialPosition(0, target)
    return target

  
  def setTarget(self,target):
    self.endPoints.SetNthFiducialPositionFromArray(0, target)   

  #
  # VR Related functions
  #


  
  def activateVR(self):
    from Resources.VirtualRealityHelper import VirtualRealityHelper
    self.vrhelper = VirtualRealityHelper(self.volumeRenderingDisplayNode)
    self.vrhelper.vr.viewWidget().RightControllerTriggerPressed.connect(self.onRightControllerTriggerPressed)
    self.vrhelper.vr.viewWidget().RightControllerTriggerReleased.connect(self.onRightControllerTriggerReleased)
    self.vrhelper.vr.viewWidget().LeftControllerTriggerPressed.connect(self.onLeftControllerTriggerPressed)
    self.vrhelper.vr.viewWidget().LeftControllerTriggerReleased.connect(self.onLeftControllerTriggerReleased)

    qt.QTimer.singleShot(0, lambda: self.delayedInitVRObserver())  


  
  def delayedInitVRObserver(self):
    ltn = self.vrhelper.getLeftTransformNode()
    self.leftTransformModifiedTag = ltn.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent,self.onLeftControllerMoved)
    rtn = self.vrhelper.getRightTransformNode()
    self.rightTransformModifiedTag = rtn.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent,self.onRightControllerMoved)


  
  def onRightControllerTriggerPressed(self):
    """ Callback function on trigger pressed event. If controller is near the entry point, starts modification of its position.
    """
    if not self.getNumberOfPoints(self.endPoints) == 2:
      return
    controllerPos = self.vrhelper.getRightControllerPosition()
    entryPos = self.getEntry()
    diff = np.subtract(entryPos,controllerPos)
    dist = np.linalg.norm(diff)
    # Check distance from controller to entry point
    if dist < 30.0:
      # When created in Slicer, markups are selected. To change the color of the point selected by the VR controller,
      # we need to unselect the point and change the unselected color to fit Slicer color code. This can be miss leading
      # for developpers. The other approach would be missleading for Slicer users expecting markups to be red when inactive
      # and green when modified.
      self.endPoints.SetNthControlPointSelected(1, False)
      # store previous position for motion tracking
      self.vrhelper.lastControllerPos = controllerPos
      self.movingEntry = True
      self.endPoints.GetMarkupsDisplayNode().SetColor(0,1,0) # Unselected color
    elif not self.endPoints.GetNthControlPointSelected(1):
      self.endPoints.SetNthControlPointSelected(1, True)

  
  def onRightControllerTriggerReleased(self):
    """ Callback function when right trigger is released. Drop entry point at current controller position.
    """
    if self.movingEntry:
      # Unselect point to restore default red color. Check comment above.
      self.endPoints.SetNthControlPointSelected(1, True)
      self.endPoints.GetMarkupsDisplayNode().SetColor(0,1,1)
      self.movingEntry = False

  
  def onRightControllerMoved(self,caller,event):
    """ Callback function when a the right controller position has changed.
    """
    if self.vrhelper.rightControlsDisplayMarkups.GetDisplayNode().GetVisibility():
      self.vrhelper.setControlsMarkupsPositions("Right")
    if not self.getNumberOfPoints(self.endPoints) == 2:
      return
    controllerPos = self.vrhelper.getRightControllerPosition()
    diff = np.subtract(controllerPos,self.vrhelper.lastControllerPos)
    entryPos = self.getEntry()
    newEntryPos = np.add(entryPos,diff)
    dist = np.linalg.norm(np.subtract(entryPos,controllerPos))
    # If controller is near, unselected the markup the change color
    if dist < 30.0:
      self.endPoints.SetNthControlPointSelected(1, False)
    elif not self.movingEntry:
      self.endPoints.SetNthControlPointSelected(1, True)
    # Check if entry point is currently being modified by user
    self.vrhelper.lastControllerPos = controllerPos

  
  def onLeftControllerTriggerPressed(self):
    """ Callback function on trigger pressed event. If a shader with "relativePosition" parameter has been selected
        allows user to change this parameter based on future position compared to the position when pressed.
    """
    if not self.customShader:
      return
    if self.customShader.hasShaderParameter('relativePosition', float):
      # Set init position to be compared with future positions
      self.leftInitPos = self.getLeftControllerPosition()
      self.leftInitRatio = self.customShader.getShaderParameter("relativePosition", float)
      self.moveRelativePosition = True

  
  def onLeftControllerTriggerReleased(self):
    """ Callback function on trigger released event. Stop changing the relativePosition shader parameter.
    """
    self.moveRelativePosition = False

  
  def onLeftControllerMoved(self,caller,event):
    """ Callback function when a the left controller position has changed. Used to change "relativePosition"
        current shader parameter and laser position.
    """
    # Check if the trigger is currently being pressed
    if self.moveRelativePosition:
      # Compute distance between entry and target, then normalize
      entry = self.getEntry()
      target = self.getTarget()
      diff = np.subtract(target, entry)
      range = np.linalg.norm(diff)
      dir = diff / range
      # Compute current position compared to the position when the trigger has been pressed
      curPos = self.getLeftControllerPosition()
      motion = np.subtract(curPos,self.leftInitPos)
      offsetRatio = np.dot( motion, dir )/range
      # Change relative position based on the position
      newRatio = np.clip(self.leftInitRatio + offsetRatio,0.0,1.0)
      self.customShader.setShaderParameter("relativePosition", newRatio, float)
    self.vrhelper.updateLaserPosition()
    if self.vrhelper.rightControlsDisplayMarkups.GetDisplayNode().GetVisibility():
      self.vrhelper.setControlsMarkupsPositions("Left")           

  #
  # Volume Rendering functions
  #

  
  def renderVolume(self, volumeNode):
    """ Use Slicer Volume Rendering module to initialize and setup rendering of the given volume node.
    Args:
        volumeNode (vtkMRMLVolumeNode): Volume node to be rendered.
    """
    logic = slicer.modules.volumerendering.logic()

    # Set custom shader to renderer
    self.setupCustomShader()

    # Turn off previous rendering
    if self.volumeRenderingDisplayNode:
      self.volumeRenderingDisplayNode.SetVisibility(False)

    # Check if node selected has a renderer
    displayNode = logic.GetFirstVolumeRenderingDisplayNode(volumeNode)
    if displayNode:
      self.volumeRenderingDisplayNode = displayNode
      self.volumeRenderingDisplayNode.SetVisibility(True)
      self.volumeRenderingDisplayNode.SetNodeReferenceID("shaderProperty", self.shaderPropertyNode.GetID())
      return

    # if not, create a renderer
    # Slicer default command to create renderer and add node to scene
    displayNode = logic.CreateDefaultVolumeRenderingNodes(volumeNode)
    slicer.mrmlScene.AddNode(displayNode)
    displayNode.UnRegister(logic)
    logic.UpdateDisplayNodeFromVolumeNode(displayNode, volumeNode)
    volumeNode.AddAndObserveDisplayNodeID(displayNode.GetID())

    displayNode.SetNodeReferenceID("shaderProperty", self.customShader.shaderPropertyNode.GetID())

    # Add a color preset based on volume range
    self.updateVolumeColorMapping(volumeNode, displayNode)

    # Prevent volume to be moved in VR
    volumeNode.SetSelectable(False)
    volumeNode.GetImageData()
    # Display given volume
    displayNode.SetVisibility(True)

    # Set value as class parameter to be accesed in other functions
    self.volumeRenderingDisplayNode = displayNode

  
  def setCustomShaderType(self, shaderTypeName):
    """ Set given shader type as current active shader

    Args:
        shaderTypeName (string): 'Sphere Carving', 'Opacity Peeling'. Name corresponding to the type of rendering needed.
    """
    self.customShaderType = shaderTypeName
    self.setupCustomShader()

  
  def setupCustomShader(self):
    """ Get or create shader property node and initialize custom shader.
    """
    shaderPropertyName = "ShaderProperty"
    CustomShader.GetAllShaderClassNames()
    if self.volumeRenderingDisplayNode is None :
      self.shaderPropertyNode = slicer.vtkMRMLShaderPropertyNode()
      self.shaderPropertyNode.SetName(shaderPropertyName)
      slicer.mrmlScene.AddNode(self.shaderPropertyNode)
    else :
      self.shaderPropertyNode = self.volumeRenderingDisplayNode.GetShaderPropertyNode()

    self.customShader = CustomShader.InstanciateCustomShader(self.customShaderType, self.shaderPropertyNode)
    self.customShader.setupShader()

  
  def updateVolumeColorMapping(self, volumeNode, displayNode, volumePropertyNode = None):
    """ Given a volume, compute a default color mapping to render volume in the given display node.
        If a volume property node is given to the function, uses it as color mapping.

    Args:
        volumeNode: (vtkMRMLVolumeNode): Volume node to be rendered.
        displayNode: (vtkMRMLVolumeRenderingDisplayNode) Default rendering display node. (CPU RayCast, GPU RayCast, Multi-Volume)
        volumePropertyNode (vtkMRMLVolumePropertyNode): Volume propery node that carries the color mapping wanted.
    """
    if not displayNode:
      return
    if volumePropertyNode:
      displayNode.GetVolumePropertyNode().Copy(volumePropertyNode)
    else:
      logic = slicer.modules.volumerendering.logic()
      # Select a color preset based on volume range
      scalarRange = volumeNode.GetImageData().GetScalarRange()
      if scalarRange[1]-scalarRange[0] < 1500:
        # small dynamic range, probably MRI
        displayNode.GetVolumePropertyNode().Copy(logic.GetPresetByName('MR-Default'))
      else:
        # larger dynamic range, probably CT
        displayNode.GetVolumePropertyNode().Copy(logic.GetPresetByName('CT-Chest-Contrast-Enhanced'))
      # Turn off shading
      displayNode.GetVolumePropertyNode().GetVolumeProperty().SetShade(False)

  
  def onCloseScene(self, caller, event):
    self.deleteNodes()