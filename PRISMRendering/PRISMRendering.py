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

from PRISMRenderingShaders.CustomShader import CustomShader
from PRISMRenderingLogic.PRISMRenderingLogic import PRISMRenderingLogic


"""
class PRISMRendering Class containing the informations about the module.

:param ScriptedLoadableModule: Uses ScriptedLoadableModule base class, available at: https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py 
:type ScriptedLoadableModule: class.
"""
class PRISMRendering(slicer.ScriptedLoadableModule.ScriptedLoadableModule):
  
  def __init__(self, parent):
    slicer.ScriptedLoadableModule.ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PRISM Rendering"
    self.parent.categories = ["Rendering"]
    self.parent.dependencies = []
    self.parent.contributors = ["Tiphaine RICHARD (ETS), Simon Drouin (ETS)"]
    self.parent.helpText = """This module is an implementation of the PRISM customizable volume rendering framework in 3D Slicer. """
    self.parent.helpText += "<p>For more information see the <a href=\"https://ets-vis-interactive.github.io/SlicerPRISM/\">online documentation</a>.</p>"
    self.parent.acknowledgementText ="""This file was developped by Tiphaine RICHARD at Ecole de Technologie Superieure (Montreal, Canada)"""

"""
class PRISMRenderingWidget Class containing the informations about the module.

:param ScriptedLoadableModuleWidget: Uses ScriptedLoadableModuleWidget base class, available at: https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py 
:type ScriptedLoadableModuleWidget: class.
"""
class PRISMRenderingWidget(slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget):

  def setup(self):
    """Function to setup the class.

    """   
    slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.setup(self)

    ## Logic of module
    self.logic = PRISMRenderingLogic()
    ## All class names of shaders
    allShaderTypes = CustomShader.GetAllShaderClassNames()
    ## All classes of shaders
    self.allClasses = CustomShader.allClasses

    # Instantiate and connect widgets ..
    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/PRISMRendering.ui'))
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
    # Keep the widgets in position even when hiding
    sp = self.ui.volumeRenderingCheckBox.sizePolicy
    sp.setRetainSizeWhenHidden(True)
    self.ui.enableROICheckBox.setSizePolicy(sp)
    self.ui.displayROICheckBox.setSizePolicy(sp)

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
    reloadIconPath = 'Resources/UI/reload.png'

    self.ui.reloadCurrentCustomShaderButton.setIcon(qt.QIcon(qt.QPixmap(reloadIconPath)))

    self.ui.customShaderCollapsibleButton.hide()

    # Custom shader combobox to select a type of custom shader
    self.ui.reloadCurrentCustomShaderButton.hide()
    self.ui.openCustomShaderButton.hide()
    self.ui.toolCustomShaderButton.clicked.connect(self.onToolCustomShaderButton)

    # Populate combobox with every types of shader available
    
    for shaderType in allShaderTypes:
      self.ui.customShaderCombo.addItem(shaderType)
    self.ui.customShaderCombo.setCurrentIndex(len(allShaderTypes)-1)
    self.ui.customShaderCombo.currentIndexChanged.connect(self.onCustomShaderComboIndexChanged)

    self.ui.reloadCurrentCustomShaderButton.clicked.connect(self.onReloadCurrentCustomShaderButtonClicked)
    self.ui.openCustomShaderButton.clicked.connect(self.onOpenCustomShaderButtonClicked)

    ## Error message (the created shader has the name of an existing shader)
    self.duplicateErrorMsg = qt.QLabel()
    self.duplicateErrorMsg.hide()
    self.duplicateErrorMsg.setStyleSheet("color: red")

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
    
    # Update GUI 
    self.addGUIObservers()
    if self.ui.imageSelector.currentNode() != None :
      self.updateParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)
    self.updateGUIFromParameterNode()

    #self.ui.enableScalingCheckBox.setChecked(True)
    self.ROIdisplay = None

  def setAndObserveParameterNode(self, caller=None, event=None):
    """Function to set the parameter node.

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
    """Function to get the class name of a widget.

    :param widget: Wanted widget. 
    :type widget: QObject
    :return: widget's class name. 
    :rtype: str
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
    """Function to update GUI from parameter node values

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """   
    parameterNode = self.logic.parameterNode
    if not parameterNode or parameterNode.GetParameterCount() == 0:
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
              w.SetNodeValue(i, [float(k) for k in values.split(",")])
        elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':     
          params = parameterNode.GetParameterNames()
          markups = []
          for p in params:
            if w.name in p :
              markups.append(p)
          endPoints = self.logic.endPoints
          endPoints.RemoveAllControlPoints()
          volumeName = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode().GetName()
          for m in markups :
            values = parameterNode.GetParameter(m)
            #If point was defined
            values = [float(k) for k in values.split(",")]
            if len(values) > 1 :
              type_ = m.replace(w.name, '')
              values.pop()
              index = endPoints.AddFiducialFromArray(values, type_)
              endPoints.SetNthFiducialAssociatedNodeID(index, m)
              CSName = w.name.replace(volumeName+'markup'+type_, '')
              visible = self.CSName+"markup" == CSName 
              self.logic.pointIndexes[m] = index
              world = [0, 0, 0, 0]
              endPoints.GetNthFiducialWorldCoordinates(index, world)
              self.logic.onCustomShaderParamChanged(world, type_, "markup")
              endPoints.SetNthFiducialVisibility(index, visible)
      elif widgetClassName == "qMRMLNodeComboBox":
        w.setCurrentNodeID(parameterNode.GetNodeReferenceID(w.name))

    self.addGUIObservers()

  def updateParameterNodeFromGUI(self, value, w):
    """Function to update the parameter node from gui values.

    :param value: Value of the widget.  
    :type value: float
    :param w: Widget being modified.  
    :type w: QObject
    """   
    parameterNode = self.logic.parameterNode
    oldModifiedState = parameterNode.StartModify()
    if self.ui.imageSelector.currentNode() is None:
      return 

    if w not in self.widgets :
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
    
    elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':
      caller = value[0]
      event = value[1]
      index = value[2]
      name = w.name + self.logic.pointType
      world = [0, 0, 0, 0]
      if event == "PointPositionDefinedEvent" :
        index = caller.GetDisplayNode().GetActiveControlPoint()
        # Initialise point
        if parameterNode.GetParameter(name) == "":
          index = caller.GetDisplayNode().GetActiveControlPoint()
          caller.SetNthFiducialAssociatedNodeID(index, name)
          caller.GetNthFiducialWorldCoordinates(index, world)
          parameterNode.SetParameter(name, ",".join("{0}".format(n) for n in world))
          parameterNode.SetParameter(w.name, str(index))
          self.logic.pointIndexes[name] = index

        # Reset point
        elif self.logic.pointName != '' :
          name = self.logic.pointName
          index = self.logic.pointIndexes[name] 
          caller.GetNthFiducialWorldCoordinates(index, world)
          parameterNode.SetParameter(name, ",".join("{0}".format(n) for n in world))
          self.logic.pointName = ''
      if event == "PointModifiedEvent" :
        if parameterNode.GetParameter(w.name) != "" and index <= int(parameterNode.GetParameter(w.name)):
          pointName = caller.GetNthFiducialAssociatedNodeID(index)
          if parameterNode.GetParameter(pointName) != "":
            caller.GetNthFiducialWorldCoordinates(index, world)
            parameterNode.SetParameter(pointName, ",".join("{0}".format(n) for n in world))

    parameterNode.EndModify(oldModifiedState)

      
  def addGUIObservers(self):
    """Function to add observers to the GUI's widgets.

    """   
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
        if not w.HasObserver(vtk.vtkCommand.ModifiedEvent):
          w.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = w : self.updateParameterNodeFromGUI([o,"add observers"], w))
      elif widgetClassName == "qMRMLNodeComboBox":
        w.currentNodeChanged.connect(lambda value, w = w : self.updateParameterNodeFromGUI(value, w))
      elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':
        self.logic.pointModifiedEventTag = w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.logic.onEndPointsChanged)
        w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.logic.onEndPointAdded)
        w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.pointModified)
        w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, lambda c, e, name = w.name, w = w : self.updateParameterNodeFromGUI([c, "PointPositionDefinedEvent", name], w))
      
  def removeGUIObservers(self):
    """Function to remove observers from the GUI's widgets.
    
    """  
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
        w.RemoveAllObservers()
      elif widgetClassName == "qMRMLNodeComboBox":
        w.currentNodeChanged.disconnect(self.updateParameterNodeFromGUI)
      elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':
        w.RemoveObservers(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent)
        w.RemoveObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent)
  
  def onParameterNodeModified(self, caller, event):
    """Function to update the parameter node.

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """   
    
    self.updateGUIFromParameterNode()

  def onOpenCustomShaderButtonClicked(self, caller=None, event=None) :
    """Function to open custom shader file.

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """   
    
    shaderPath = self.getPath(CustomShader.GetClassName(self.ui.customShaderCombo.currentText).__name__)
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+shaderPath, qt.QUrl.TolerantMode))

  def onEnableRotationCheckBoxToggled(self, caller=None, event=None) :
    """Function to enable rotating ROI box.

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """
    
    if self.ui.enableRotationCheckBox.isChecked():
      self.ROIdisplay.RotationHandleVisibilityOn()
    else:
      self.ROIdisplay.RotationHandleVisibilityOff()

  def onEnableScalingCheckBoxToggled(self, caller=None, event=None) :
    """Function to enable scaling ROI box.

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """
    
    if self.ui.enableScalingCheckBox.isChecked():
      self.ROIdisplay.ScaleHandleVisibilityOn()
    else:
      self.ROIdisplay.ScaleHandleVisibilityOff()

  def onEnableROICheckBoxToggled(self, caller=None, event=None):
    """Function to enable ROI cropping and show/hide ROI Display properties.

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """   
    

    if self.ui.enableROICheckBox.isChecked():
      self.logic.volumeRenderingDisplayNode.SetCroppingEnabled(True)
      self.ui.displayROICheckBox.show()
    else:
      self.logic.volumeRenderingDisplayNode.SetCroppingEnabled(False)
      self.ui.displayROICheckBox.hide()
      self.ui.displayROICheckBox.setChecked(False)

  def onDisplayROICheckBoxToggled(self, caller=None, event=None):
    """Function to display ROI box and show/hide scaling and rotation parameters.

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """   
    
    if self.ui.displayROICheckBox.isChecked():
      # self.transformDisplayNode.EditorVisibilityOn()
      self.ROI.SetDisplayVisibility(1)
      self.ui.enableScalingCheckBox.show()
      self.ui.enableRotationCheckBox.show()
    else :
      # self.transformDisplayNode.EditorVisibilityOff()
      self.ROI.SetDisplayVisibility(0)
      self.ui.enableScalingCheckBox.hide()
      self.ui.enableScalingCheckBox.setChecked(False)
      self.ui.enableRotationCheckBox.hide()
      self.ui.enableRotationCheckBox.setChecked(False)
  
  def onToolCustomShaderButton(self) :
    if self.ui.reloadCurrentCustomShaderButton.visible == True:
      self.ui.reloadCurrentCustomShaderButton.hide()
      self.ui.openCustomShaderButton.hide()
    else :
      self.ui.reloadCurrentCustomShaderButton.show()
      self.ui.openCustomShaderButton.show()
  
  def onReloadCurrentCustomShaderButtonClicked(self, caller=None, event=None):
    """Function to reload the current custom shader.
    
    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """   

    ## Current shader display name
    currentShader = self.ui.customShaderCombo.currentText
    
    ## Current shader class name
    shaderName = CustomShader.GetClassName(currentShader).__name__

    ## Package name
    shaderPackageName = 'PRISMRenderingShaders'
    
    ## Submodule name
    submoduleName = 'CustomShader'

    ## Submodule package name
    submodulePackageName = 'PRISMRenderingShaders'
    
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
    

  def getPath(self, name, packageName = 'PRISMRenderingShaders') :
    """Function to get a selected shader file path.

    :param name: Name of the shader. 
    :type name: str
    :param packageName: Name of the package in which the class in contained, defaults to 'PRISMRenderingShaders'.  
    :type packageName: str
    :return: Selected shader's path. 
		:rtype: str
    """
    

    ## Class of the specified shader.
    class_ = CustomShader.GetClass(name)
    if class_ :
      ## Path of the class.
      path_ = os.path.join(self.prismPath(), packageName, str(class_.__name__) + '.py').replace("\\", "/")
      return path_
    
    return None

  def updateComboBox(self, tab, comboBox, func):
    """Function to populate a combobox from an array.

    :param tab: List to populate the combobox. 
    :type tab: list
    :param comboBox: ComboBox to be modified. 
    :type comboBox: QComboBox
    :param func: Connect function when the ComboBox index is changed
    :type func: func
    """
    
    
    comboBox.clear()  
    for e in tab:
      comboBox.addItem(e)
    comboBox.setCurrentIndex(len(tab)-1)
    comboBox.activated.connect(func)

  def initState(self):
    """Function to initialize the all user interface based on current scene.

    """
    
    # Import shaders
    for c in self.allClasses:
      __import__('PRISMRenderingShaders.' + str(c.__name__))
    
    # Init shader
    if self.ui.volumeRenderingCheckBox.isChecked() and self.ui.imageSelector.currentNode():
      self.logic.renderVolume(self.ui.imageSelector.currentNode())
      self.ui.imageSelector.currentNodeChanged.connect(lambda value, w = self.ui.imageSelector : self.onImageSelectorChanged(value, w))
      self.ui.imageSelector.nodeAdded.disconnect()
      self.UpdateShaderParametersUI()    

  #
  # Data callbacks
  #

  def onImageSelectorChanged(self, node, widget, index=0):
    """Callback function when the volume node has been changed in the dedicated combobox.
    Setup slice nodes to display selected node and render it in the 3d view.

    :param node: Volume node selected in the scene. 
    :type node: vtkMRMLVolumeNode
    :param widget: Widget modified. 
    :type widget: QObject
    :param index: Index of the widget being modified. 
    :type index: int
    """
    
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
    
    else:
      self.updateParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)
      self.ui.customShaderCombo.currentIndex = self.ui.customShaderCombo.count -1 
      self.ui.volumeRenderingCheckBox.setChecked(False)
  
  #
  # View setup callbacks
  #

  def onVolumeRenderingCheckBoxToggled(self, caller=None, event=None):
    """Callback function when the volume rendering check box is toggled. Activate or deactivate 
    the rendering of the selected volume.
    
    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """
    

    if self.ui.volumeRenderingCheckBox.isChecked():
      if self.ui.imageSelector.currentNode():
        self.logic.renderVolume(self.ui.imageSelector.currentNode())
        # Init ROI
        # allTransformDisplayNodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLTransformDisplayNode','TransformDisplayNode')
        # if allTransformDisplayNodes.GetNumberOfItems() > 0:
        #   ## Transforme Display node to apply transformations to the ROI
        #   self.transformDisplayNode = allTransformDisplayNodes.GetItemAsObject(0)
        # else:
        #   self.transformDisplayNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformDisplayNode')
        #   self.transformDisplayNode.SetName('TransformDisplayNode')
        #   self.transformDisplayNode.SetEditorRotationEnabled(False)

        # allTransformNodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLTransformNode','TransformNode')
        # if allTransformNodes.GetNumberOfItems() > 0:
        #   ## Transform node to apply transformations to the ROI
        #   self.transformNode = allTransformNodes.GetItemAsObject(0)
        # else:
        #   self.transformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
        #   self.transformNode.SetName('TransformNode')
        #   self.transformNode.SetAndObserveDisplayNodeID(self.transformDisplayNode.GetID())

        ## ROI of the current volume
        self.ROI = self.logic.volumeRenderingDisplayNode.GetMarkupsROINode()
        #self.ROI.SetAndObserveDisplayNodeID(self.transformDisplayNode.GetID())
        #self.ROI.SetAndObserveTransformNodeID(self.transformNode.GetID())
        self.ROI.SetDisplayVisibility(0)
        self.renameROI()
        self.ui.enableROICheckBox.show()
        self.UpdateShaderParametersUI()
        self.ui.customShaderCollapsibleButton.show()
        
        if self.ROIdisplay is None:
          allRoiDisplayNodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsROIDisplayNode', 'MarkupsROIDisplay')
          if allRoiDisplayNodes.GetNumberOfItems() > 0:
            self.ROIdisplay = allRoiDisplayNodes.GetItemAsObject(0)
            self.ROIdisplayObserver = self.ROIdisplay.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onROIdisplayChanged)
          
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

  def onROIdisplayChanged(self, caller, event):
    """Function to update the parameter node.

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """

    if self.ui.enableScalingCheckBox.isChecked() != caller.GetScaleHandleVisibility():
      self.ui.enableScalingCheckBox.setChecked(caller.GetScaleHandleVisibility())
      # logging.info("lol")
    if self.ui.enableRotationCheckBox.isChecked() != caller.GetRotationHandleVisibility():
      self.ui.enableRotationCheckBox.setChecked(caller.GetRotationHandleVisibility())
      
  def renameROI(self):
    """Function to reset the ROI in the scene.

    """


    ## Node of the roi
    ROINodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsROINode','Volume rendering ROI')
    if ROINodes.GetNumberOfItems() > 0:
      # Set node used before reload in the current instance
      ROINode = ROINodes.GetItemAsObject(0)
      #ROINodes.ResetAnnotations()
      #slicer.modules.volumerendering.logic().FitROIToVolume(self.logic.volumeRenderingDisplayNode)
      ROINode.SetName("ROI")

  def onDisplayControlsCheckBoxToggled(self, caller=None, event=None):
    """Callback function triggered when the display controls check box is toggled.
        Show/hide in the VR view scene the controls at the location of the Windows Mixed Reality controllers.

    :param caller: Caller of the function.
    :param event: Event that triggered the function.
    """
    

    if self.displayControlsCheckBox.isChecked():
      self.logic.vrhelper.showVRControls()
    else:
      self.logic.hideVRControls()

  #
  # Volume rendering callbacks
  #

  def onCustomShaderComboIndexChanged(self, i):
    """Callback function when the custom shader combo box is changed.

    :param i: Index of the element. 
    :type i: int
    """
    
    self.logic.setCustomShaderType(self.ui.customShaderCombo.currentText, self.ui.imageSelector.currentNode())
    self.UpdateShaderParametersUI()
    self.updateParameterNodeFromGUI(self.ui.customShaderCombo.currentText, self.ui.customShaderCombo)
    self.updateGUIFromParameterNode()
    # If there is no selected shader, disables the buttons.
    if (self.ui.customShaderCombo.currentText == "None"):
      self.ui.openCustomShaderButton.setEnabled(False)
      self.ui.reloadCurrentCustomShaderButton.setEnabled(False)
    else :
      self.ui.openCustomShaderButton.setEnabled(True)
      self.ui.reloadCurrentCustomShaderButton.setEnabled(True)
    
    self.ui.customShaderCollapsibleButton.setToolTip(self.logic.customShader.GetBasicDescription())

  def appendList(self, widget, name):
    """Function to add a widget to self.widgets without duplicate.

    :param widget: Widget to be added to the list. 
    :type widget: QObject
    :param name: Name of the widget. 
    :type name: str
    """
    
   
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
    """Updates the shader parameters on the UI.

    """
    
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
      
    if self.logic.endPoints.GetNumberOfControlPoints() > 0 : 
      self.logic.endPoints.RemoveAllControlPoints()

    lenWidgets = len(self.widgets)
    
    ## Name of the current shader, without spaces
    volumeName = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode().GetName()
    self.CSName = self.ui.customShaderCombo.currentText.replace(" ", "") + volumeName

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
      slider.setDecimals(f[::-1].find('.')+1)
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
      targetPointButton.clicked.connect(lambda _, name = p, btn = targetPointButton : self.logic.setPlacingMarkups(paramType = name, paramName = self.CSName + "markup" + name, btn = btn,  interaction = 1))
      targetPointButton.clicked.connect(lambda value, w = slider : self.updateParameterNodeFromGUI(value, w))
      targetPointButton.setParent(self.ui.customShaderParametersLayout)

      self.ui.customShaderParametersLayout.addRow(qt.QLabel(params[p]['displayName']), targetPointButton)
      self.appendList(targetPointButton, self.CSName+p)
    
    if params:
      self.logic.endPoints.name = self.CSName + "markup"
      self.logic.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.pointModified)
      self.logic.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, lambda c, e, name = self.CSName + "markup", w = self.logic.endPoints : self.updateParameterNodeFromGUI([c, "PointPositionDefinedEvent", name], w))
      self.appendList(self.logic.endPoints, self.logic.endPoints.name)
    
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
      logging.error("Too many transfer function have been defined.")
    

    TFTypes = [params[p]['type'] for p in paramNames]
    # Check that each volume has only one of each type of transfer functions.
    if len(TFTypes) != len(set(TFTypes)) and len(TFTypes) > self.numberOfTFTypes:
      logging.error("One transfer function has been assigned multiple times to the same volume2.")
    
    if paramNames:
      # If a transfer function is specified, add the widget
      if self.logic.volumeRenderingDisplayNode is None :
        return

      self.addTransferFunctions(params, paramNames, 0)

    else :
      
      if self.logic.volumeRenderingDisplayNode != None:
        volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
        colorTransferFunction = vtk.vtkColorTransferFunction()
        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        colorTransferFunction.RemoveAllObservers()
        opacityTransferFunction.RemoveAllObservers()
        colorTransferFunction.name = volumeName + "Original" + colorTransferFunction.GetClassName() 
        opacityTransferFunction.name = volumeName + "Original" + opacityTransferFunction.GetClassName()
        self.appendList(opacityTransferFunction, opacityTransferFunction.name)
        self.appendList(colorTransferFunction, colorTransferFunction.name)

        # Keep the original transfert functions
        if self.logic.colorTransferFunction.GetSize() > 0 :
          colorTransferFunction.DeepCopy(self.logic.colorTransferFunction)
          self.updateParameterNodeFromGUI(colorTransferFunction, colorTransferFunction)
        else :
          values = self.logic.parameterNode.GetParameter(colorTransferFunction.name+str(0))
          i = 0
          while values != "":
            v = [float(k) for k in values.split(",")]
            colorTransferFunction.AddRGBPoint(v[0], v[1], v[2], v[3], v[4], v[5])
            i += 1
            values = self.logic.parameterNode.GetParameter(colorTransferFunction.name+str(i))

        if not colorTransferFunction.HasObserver(vtk.vtkCommand.ModifiedEvent):
          colorTransferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = colorTransferFunction : self.updateParameterNodeFromGUI([o,e], w))
        volumePropertyNode.SetColor(colorTransferFunction)

        if self.logic.opacityTransferFunction.GetSize() > 0 :
          opacityTransferFunction.DeepCopy(self.logic.opacityTransferFunction)
          self.updateParameterNodeFromGUI(opacityTransferFunction, opacityTransferFunction)
        else :
          values = self.logic.parameterNode.GetParameter(opacityTransferFunction.name+str(0))
          i = 0
          while values != "":
            v = [float(k) for k in values.split(",")]
            opacityTransferFunction.AddPoint(v[0], v[1], v[2], v[3])
            i += 1
            values = self.logic.parameterNode.GetParameter(opacityTransferFunction.name+str(i))
        
        if not opacityTransferFunction.HasObserver(vtk.vtkCommand.ModifiedEvent):
          opacityTransferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = opacityTransferFunction : self.updateParameterNodeFromGUI([o,e], w))
        volumePropertyNode.SetScalarOpacity(opacityTransferFunction)

    ## Volumes parameters
    params = self.logic.customShader.shadervParams
    paramNames = params.keys()

    if params :
      # Check that each volume is used only once
      volumes = [params[p]['defaultVolume'] for p in paramNames]
      if len(set(volumes)) != len(params):
        logging.error("Multiples volumes defined.")
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
          logging.error("One transfer function has been assigned multiple times to the same volume.")
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
  
  @vtk.calldata_type(vtk.VTK_INT)
  def pointModified(self, caller, event, index):
    self.updateParameterNodeFromGUI([caller, "PointModifiedEvent", index], self.logic.endPoints)

  def addTransferFunctions(self, parameters, paramNames, volumeID):

    
    """Function to add transfer function widgets to the ui.

    :param parameters: Dictionnary of transfert functions. 
    :type parameters: str
    :param paramNames: Name of the transfert functions.
    :type paramNames: dictstr].
    :param volumeID: ID of the volume. 
    :type volumeID: int
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
        self.createTransferFunctionWidget(volumePropertyNode, parameters[p], p, False, volumeID)
      else : 
        # If this is a secondary volume
        transferFunctionID = volumeID * self.numberOfTFTypes
        # If the volume of the transfer function is already rendered create the widget
        if self.logic.secondaryVolumeRenderingDisplayNodes[volumeID] is not None: 
          volumePropertyNode = self.logic.secondaryVolumeRenderingDisplayNodes[volumeID].GetVolumePropertyNode()
          self.createTransferFunctionWidget(volumePropertyNode, parameters[p], p, True, volumeID)
        else :
          # Add the transfer functions to a list, so when the volume is rendered the widgets can be created
          if len(self.transferFunctionParams) <= transferFunctionID + i:
            self.transferFunctionParams.append(parameters[p])
            self.transferFunctionParamsName.append(p)
          else :
            self.transferFunctionParams[transferFunctionID + i] = parameters[p]
            ## Name of the transfer function
            self.transferFunctionParamsName[transferFunctionID + i] = p

  def getWidgetPosition(self, layout, widgetName):
    """Function to get the widget's position in a layout.

    :param layout: Layout in which the widget is containted. 
    :type layout: QObject
    :param widgetName: Name of the widget being searched. 
    :type widgetName: str

    :return: Position of the widget. 
    :rtype: int.
    """
    for i in range(layout.count()):
      item = layout.itemAt(i)
      if item != None :
        widget = item.widget()
        if widget!= None :
          if (widget.name == widgetName):
            return i

  def createTransferFunctionWidget(self, volumePropertyNode, params, p, secondTf, volumeID) :
    """Function to create a transfert fuction widget.

    :param volumePropertyNode: Volume property node to be associated to the widget. 
    :type volumePropertyNode: vtkMRMLVolumePropertyNode
    :param params: Parameters of the widget. 
    :type params: 
    :param p: Parameter 
    :type p: str's name.
    :param secondTf: If the widget is one of the secondary volumes. 
    :type secondTf: bool
    :param volumeID: ID of the volume. 
    :type volumeID: 
    """
    
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
      for i in range(nbColors): 
        if TFType == 'color':
          transferFunction.AddRGBPoint(colors[i][0], colors[i][1], colors[i][2], colors[i][3], colors[i][4], colors[i][5])  
        elif TFType == 'scalarOpacity':
          transferFunction.AddPoint(colors[i][0], colors[i][1], colors[i][2], colors[i][3])  

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
    """Function to get the module's path.

    :return: Module's path. 
    :rtype: str
    """
    

    return os.path.dirname(eval('slicer.modules.prismrendering.path'))

  def onReload(self):
    """Reload the modules.

    """
    
    logging.debug("Reloading Packages")
    packageName='PRISMRenderingLogic'
    submoduleNames = ['PRISMRenderingLogic']
    
    for submoduleName in submoduleNames :
      modulePath = os.path.join(self.prismPath(), packageName, submoduleName  + '.py').replace("\\", "/")

      with open(modulePath, "rt") as fp:
        imp.load_module(packageName+'.'+submoduleName, fp, modulePath, ('.py', 'rt', imp.PY_SOURCE))

    logging.debug("Reloading Shaders")
    try :
      shaderNames = []
      for c in self.allClasses:
        shaderNames.append(c.__name__)
      
      shaderNames.append('CustomShader')
      shaderPackageName = "PRISMRenderingShaders"
      
      for shaderName in shaderNames :
        shaderPath = self.getPath(shaderName)
        with open(shaderPath, "rt") as fp:
          imp.load_module(shaderPackageName+'.'+shaderName, fp, shaderPath, ('.py', 'rt', imp.PY_SOURCE))
    except:
      pass

    logging.debug("Reloading PRISM")
    packageNames=['PRISMRendering']
    
    for packageName in packageNames :
      path = os.path.join(self.prismPath(), packageName + '.py').replace("\\", "/")
      with open(path, "rt") as fp:
        imp.load_module(packageName, fp, self.prismPath(), ('.py', 'rt', imp.PY_SOURCE))

    globals()['PRISMRendering'] = slicer.util.reloadScriptedModule('PRISMRendering')

  def cleanup(self):
    """Function to clean up the scene.

    """
    

    self.removeGUIObservers()
    if self.logic.parameterNode and self.logic.parameterNodeObserver:
      self.logic.parameterNode.RemoveObserver(self.logic.parameterNodeObserver)
      
    if self.ROIdisplay:
      self.ROIdisplay.RemoveObserver(self.ROIdisplayObserver)
    
    # self.resetROI()
    self.ui.enableROICheckBox.setChecked(False)
    self.ui.displayROICheckBox.setChecked(False)
    # try :
    #   slicer.mrmlScene.RemoveNode(self.transformNode)
    #   slicer.mrmlScene.RemoveNode(self.transformDisplayNode)
    # except:
    #   pass