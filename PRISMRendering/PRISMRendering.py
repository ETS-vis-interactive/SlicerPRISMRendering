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

from PRISMRenderingShaders.CustomShader import *
from PRISMRenderingParams import *
from PRISMRenderingLogic import *
class PRISMRendering(slicer.ScriptedLoadableModule.ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        slicer.ScriptedLoadableModule.ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "PRISMRendering"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Rendering"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Tiphaine RICHARD (ETS), Simon Drouin (ETS), Camille Hascoët (ETS)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """This module is an implementation of the PRISM customizable volume rendering framework in 3D Slicer."""
        self.parent.helpText += "<p>For more information see the <a href=\"https://ets-vis-interactive.github.io/SlicerPRISM/\">online documentation</a>.</p>"
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """This file was developped by Tiphaine RICHARD at Ecole de Technologie Superieure (Montreal, Canada)"""

        # Additional initialization step after application startup is complete

    # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)



def registerSampleData():
  """
  Add data sets to Sample Data module.
  """
  # It is always recommended to provide sample data for users to make it easy to try the module,
  # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

  import SampleData
  iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

  # To ensure that the source code repository remains small (can be downloaded and installed quickly)
  # it is recommended to store data sets that are larger than a few MB in a Github release.

  # TemplateKey1
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='TemplateKey',
    sampleName='TemplateKey1',
    # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
    # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
    thumbnailFileName=os.path.join(iconsPath, 'TemplateKey1.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
    fileNames='TemplateKey1.nrrd',
    # Checksum to ensure file integrity. Can be computed by this command:
    #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
    checksums = 'SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
    # This node name will be used when the data set is loaded
    nodeNames='TemplateKey1'
  )

  # TemplateKey2
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='TemplateKey',
    sampleName='TemplateKey2',
    thumbnailFileName=os.path.join(iconsPath, 'TemplateKey2.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
    fileNames='TemplateKey2.nrrd',
    checksums = 'SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
    # This node name will be used when the data set is loaded
    nodeNames='TemplateKey2'
  )

class PRISMRenderingWidget(slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setup(self):
      """Function to setup the class.

      """   
      slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.setup(self)

      ## Logic of module
      self.logic = PRISMRenderingLogic()
      ## All class names of shaders
      allShaderTypes = CustomShader.GetAllShaderClassNames()
      ## All classes of shaders

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
      
      self.ROIdisplay = None
      #
      # View Setup Area
      #
      # Keep the widgets in position even when hiding
      sp = self.ui.volumeRenderingCheckBox.sizePolicy
      sp.setRetainSizeWhenHidden(True)
      self.ui.enableROICheckBox.setSizePolicy(sp)
      self.ui.displayROICheckBox.setSizePolicy(sp)

      self.ui.volumeRenderingCheckBox.toggled.connect(self.onVolumeRenderingCheckBoxToggled)
      self.ui.sampleDataCheckBox.toggled.connect(self.onSampleDataCheckBoxToggled)
      self.ui.enableROICheckBox.toggled.connect(self.onEnableROICheckBoxToggled)
      self.ui.displayROICheckBox.toggled.connect(self.onDisplayROICheckBoxToggled)
      self.ui.enableScalingCheckBox.toggled.connect(self.onEnableScalingCheckBoxToggled)
      self.ui.enableRotationCheckBox.toggled.connect(self.onEnableRotationCheckBoxToggled)

      self.ui.sampleDataCheckBox.hide()
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

      self.setAndObserveParameterNode()
    
      slicer.mrmlScene.AddNode(self.logic.parameterNode)
      if self.logic.parameterNode.GetParameterCount() != 0:
        volumePath = self.logic.parameterNode.GetParameter("volumePath")
        # Set volume node
        if len(volumePath) != 0 :
          volumeNode = slicer.util.loadVolume(volumePath)
          self.ui.imageSelector.setCurrentNode(volumeNode)
    
        # Update GUI 
      self.addAllGUIObservers()
      if self.ui.imageSelector.currentNode() != None :
        self.updateWidgetParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)
      self.updateBaseGUIFromParameterNode()

      print(self.ui.imageSelector.currentNode().GetClassName())

      #self.ui.enableScalingCheckBox.setChecked(True)
      self.ROIdisplay = None

      self.storedParamsValues = [] # To store the parameters' values of the shader while displaying sample data
      self.storedVolume = None # To store the volume while displaying sample data
    
    def updateBaseGUIFromParameterNode(self, caller=None, event=None):
        """Function to update GUI from parameter node values

        :param caller: Caller of the function.
        :param event: Event that triggered the function.
        """   
        parameterNode = self.logic.parameterNode
        if not parameterNode or parameterNode.GetParameterCount() == 0:
          return

        # Disables updateParameterNodeFromGUI signal 
        self.removeAllGUIObservers()
        for w in self.widgets:
         if not isinstance(w, Param):
           self.updateWidgetGUIFromParameterNode(w, caller, event)
        self.addAllGUIObservers()
    
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
        self.updateWidgetParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)

      else:
        self.updateWidgetParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)
    
    def onSampleDataCheckBoxToggled(self, caller=None, event=None):
      import SampleData
      if self.ui.sampleDataCheckBox.isChecked():
        self.storedParamsValues = []
        for p in self.logic.customShader[self.logic.shaderIndex].param_list:
          self.storedParamsValues.append(p.getValue())
          # add code to setValue of the parameters to the sample data values, for the moment, it will be the default values
          p.setValue(p.defaultValue)
          # add code to store old volume and show sample data one
        self.storedVolume = self.ui.imageSelector.currentNode()
        volumeNode = SampleData.downloadSample('TemplateKey1')
        self.ui.imageSelector.setCurrentNode(volumeNode)
        self.updateWidgetParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)
        self.logic.renderVolume(self.ui.imageSelector.currentNode())
        self.setupShader()
      else:
        for i, p in enumerate(self.logic.customShader[self.logic.shaderIndex].param_list):
          p.setValue(self.storedParamsValues[i])
          # add code to restore old volume and hide sample data one

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
          self.ui.sampleDataCheckBox.show()
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
          self.ui.sampleDataCheckBox.setChecked(False)
          self.ui.sampleDataCheckBox.hide()
          self.ui.enableROICheckBox.hide()
          self.ui.displayROICheckBox.hide()
        self.ui.customShaderCollapsibleButton.hide()

    def onEnableRotationCheckBoxToggled(self, caller=None, event=None) :
      """Function to enable rotating ROI box.

      :param caller: Caller of the function.
      :param event: Event that triggered the function.
      """

      if self.ui.enableRotationCheckBox.isChecked():
        self.ROIdisplay.RotationHandleVisibilityOn()
      else:
        self.ROIdisplay.RotationHandleVisibilityOff()

    def onToolCustomShaderButton(self) :
        if self.ui.reloadCurrentCustomShaderButton.visible == True:
          self.ui.reloadCurrentCustomShaderButton.hide()
          self.ui.openCustomShaderButton.hide()
        else :
          self.ui.reloadCurrentCustomShaderButton.show()
          self.ui.openCustomShaderButton.show()
  
    def onCustomShaderComboIndexChanged(self, i):
      """Callback function when the custom shader combo box is changed.

      :param i: Index of the element. 
      :type i: int
      """
      self.setupShader()
      self.updateWidgetParameterNodeFromGUI(self.ui.customShaderCombo.currentText, self.ui.customShaderCombo)
      # If there is no selected shader, disables the buttons.
      if (self.ui.customShaderCombo.currentText == "None"):
        self.ui.openCustomShaderButton.setEnabled(False)
        self.ui.reloadCurrentCustomShaderButton.setEnabled(False)
      else :
        self.ui.openCustomShaderButton.setEnabled(True)
        self.ui.reloadCurrentCustomShaderButton.setEnabled(True)

      self.ui.customShaderCollapsibleButton.setToolTip(self.logic.customShader[self.logic.shaderIndex].GetBasicDescription())

    def setupShader(self):
      try: # if the old shader has points
        self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints.SetDisplayVisibility(0)
      except:
        pass
      self.logic.setCustomShaderType(self.ui.customShaderCombo.currentText, self.ui.imageSelector.currentNode())
      self.UpdateShaderParametersUI()
      self.logic.customShader[self.logic.shaderIndex].setupShader()
      try: # if the new shader has points
        self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints.SetDisplayVisibility(1)
      except:
        pass

    def updateParameterNodeFromGUI(self, value, w):
      """Function to update the parameter node from gui values.

      :param value: Value of the widget.  
      :type value: float
      :param w: Widget being modified.  
      :type w: QObject
      """   
      if self.ui.imageSelector.currentNode() is None:
        return 

      if w not in self.widgets :
        return
      
      if isinstance(w, Param):
        w.updateParameterNodeFromGUI(self)
      else :
        self.updateWidgetParameterNodeFromGUI(value, w)


    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

            # Compute output
            self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
                               self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

            # Compute inverted output (if needed)
            if self.ui.invertedOutputSelector.currentNode():
                # If additional output volume is selected then result with inverted threshold is written there
                self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)

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

    def setAndObserveParameterNode(self, caller=None, event=None):
      """Function to set the parameter node.

      """
      # Remove observer to old parameter node
      if self.logic.parameterNode and self.logic.parameterNodeObserver:
        self.logic.parameterNode.RemoveObserver(self.logic.parameterNodeObserver)
        self.logic.parameterNodeObserver = None

      # Set and observe new parameter node
      self.logic.parameterNode = self.logic.getParameterNode()
      # if self.logic.parameterNode:
      #   self.logic.parameterNodeObserver = self.logic.parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onParameterNodeModified)

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

      if self.logic.customShader[self.logic.shaderIndex] == None:
        return

      # Clear all the widgets except the combobox selector
      while self.ui.customShaderParametersLayout.count() != 1:
        ## Item of the combobox
        item = self.ui.customShaderParametersLayout.takeAt(self.ui.customShaderParametersLayout.count() - 1)
        if item != None:
          widget = item.widget()
          if widget != None:
            widget.setParent(None)

      # if self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints.GetNumberOfControlPoints() > 0 : 
        # self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints.RemoveAllControlPoints()

      ## Name of the current shader, without spaces
      volumeName = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode().GetName()
      self.CSName = self.ui.customShaderCombo.currentText.replace(" ", "") + volumeName
      param_list = self.logic.customShader[self.logic.shaderIndex].param_list
      for p in param_list:
          if not isinstance(p, TransferFunctionParam):
            hideWidget = False
            Optional = False
            for i in self.logic.customShader[self.logic.shaderIndex].param_list:
              if isinstance(i,  BoolParam):
                if p.name in i.optionalWidgets:
                  Optional  = True
                  bool_param = i
                  if self.logic.optionalWidgets.get(self.CSName + bool_param.name) == None:
                    self.logic.optionalWidgets[self.CSName + bool_param.name] = []
                  elif len(self.logic.optionalWidgets[self.CSName + bool_param.name]) == len(bool_param.optionalWidgets) : #To avoid duplicates & reset after next GUI Setup
                    self.logic.optionalWidgets[self.CSName + bool_param.name] = []
                  if i.value == True:
                    hideWidget = False
                  else:
                    hideWidget = True
                  break
            p.SetupGUI(self)
            try :
              self.ui.customShaderParametersLayout.addRow(p.label, p.widget)
              if Optional :
                self.logic.optionalWidgets[self.CSName + bool_param.name] += [p]
                if hideWidget :
                  p.widget.hide()
                  p.label.hide()
            except :
              self.ui.customShaderParametersLayout.addRow(p.widget)
              if Optional :
                self.logic.optionalWidgets[self.CSName + bool_param.name] += [p]
                if hideWidget :
                  p.widget.hide()
              
      if any(isinstance(item, FourFParam) for item in param_list):
        self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints.name = self.CSName + "markup"
        self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.pointModified)
        self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, 
        lambda c, e, name = self.CSName + "markup": 
        self.logic.customShader[self.logic.shaderIndex].customShaderPoints.updateParameterNodeFromGUI(self.logic, [c, "PointPositionDefinedEvent", name]))

        ## Transfer function of the first volume
      params = [p for p in self.logic.customShader[self.logic.shaderIndex].param_list if isinstance(p, TransferFunctionParam)]
      if len(params) > self.numberOfTFTypes:
        logging.error("Too many transfer function have been defined.")


      TFTypes = [p.type for p in params]
      # Check that each volume has only one of each type of transfer functions.
      my_set = {i for i in TFTypes}
      if len(TFTypes) != len(my_set) and len(TFTypes) > self.numberOfTFTypes:
        logging.error("One transfer function has been assigned multiple times to the same volume2.")

      if params != []:
        # If a transfer function is specified, add the widget
        if self.logic.volumeRenderingDisplayNode is None :
          return

        self.addTransferFunctions(params, 0)

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
            self.updateWidgetParameterNodeFromGUI(colorTransferFunction, colorTransferFunction)
          else :
            values = self.logic.parameterNode.GetParameter(colorTransferFunction.name+str(0))
            i = 0
            while values != "":
              v = [float(k) for k in values.split(",")]
              colorTransferFunction.AddRGBPoint(v[0], v[1], v[2], v[3], v[4], v[5])
              i += 1
              values = self.logic.parameterNode.GetParameter(colorTransferFunction.name+str(i))

          if not colorTransferFunction.HasObserver(vtk.vtkCommand.ModifiedEvent):
            colorTransferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = colorTransferFunction : self.updateWidgetParameterNodeFromGUI([o,e], w))
          volumePropertyNode.SetColor(colorTransferFunction)

          if self.logic.opacityTransferFunction.GetSize() > 0 :
            opacityTransferFunction.DeepCopy(self.logic.opacityTransferFunction)
            self.updateWidgetParameterNodeFromGUI(opacityTransferFunction, opacityTransferFunction)
          else :
            values = self.logic.parameterNode.GetParameter(opacityTransferFunction.name+str(0))
            i = 0
            while values != "":
              v = [float(k) for k in values.split(",")]
              opacityTransferFunction.AddPoint(v[0], v[1], v[2], v[3])
              i += 1
              values = self.logic.parameterNode.GetParameter(opacityTransferFunction.name+str(i))

          if not opacityTransferFunction.HasObserver(vtk.vtkCommand.ModifiedEvent):
            opacityTransferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = opacityTransferFunction : self.updateWidgetParameterNodeFromGUI([o,e], w))
          volumePropertyNode.SetScalarOpacity(opacityTransferFunction)

    def addTransferFunctions(self, params, volumeID):
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
       for i, p in enumerate(params):
         # IF this is the principal volume
         if volumePrincipal :
           volumePropertyNode = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode()
           self.createTransferFunctionWidget(volumePropertyNode, p, False, volumeID)
         else : 
           # If this is a secondary volume
           transferFunctionID = volumeID * self.numberOfTFTypes
           # If the volume of the transfer function is already rendered create the widget
           if self.logic.secondaryVolumeRenderingDisplayNodes[volumeID] is not None: 
             volumePropertyNode = self.logic.secondaryVolumeRenderingDisplayNodes[volumeID].GetVolumePropertyNode()
             self.createTransferFunctionWidget(volumePropertyNode, p, True, volumeID)
           else :
             # Add the transfer functions to a list, so when the volume is rendered the widgets can be created
             if len(self.transferFunctionParams) <= transferFunctionID + i:
               self.transferFunctionParams.append(p)
               self.transferFunctionParamsName.append(p.name)
             else :
               self.transferFunctionParams[transferFunctionID + i] = p
               ## Name of the transfer function
               self.transferFunctionParamsName[transferFunctionID + i] = p

    def createTransferFunctionWidget(self, volumePropertyNode, param, secondTf, volumeID) :
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

      TFType = param.type
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
          label = self.ui.centralWidget.findChild(qt.QLabel, self.CSName + transferFunction.GetClassName() + param.name + "Label")
          if label != None:
            label.setParent(None)

      # Create the widget
      label = qt.QLabel(param.display_name)
      label.setObjectName(self.CSName + transferFunction.GetClassName() + param.name + "Label")

      widget = ctk.ctkVTKScalarsToColorsWidget()
      widget.setObjectName(self.CSName + transferFunction.GetClassName() + param.name + "Widget")
      transferFunction.name = self.CSName + transferFunction.GetClassName() + param.name
      transferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = transferFunction : self.updateWidgetParameterNodeFromGUI([o,"add widget"], w))

      # Change the points to the ones specified in the shader
      if param.default_colors != [] :
        colors = param.default_colors
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

      self.ui.customShaderParametersLayout.addRow(label, widget)

      if secondTf :
        self.secondColorTransferFunctionWidget[volumeID][TFType] = widget

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

    @vtk.calldata_type(vtk.VTK_INT)
    def pointModified(self, caller, event, index):
      self.updateWidgetParameterNodeFromGUI([caller, "PointModifiedEvent", index], self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints)

    def addAllGUIObservers(self):
      for w in self.widgets:
        if isinstance(w, Param):
          w.addGUIObservers(self)
        else:
          self.addGUIObservers(w)

    def removeAllGUIObservers(self):
      for w in self.widgets:
          if isinstance(w, Param):
            w.removeGUIObservers()
          else:
            self.removeGUIObservers(w)

    def addGUIObservers(self, w):
      """Function to add observers to the GUI's widget.

      """   
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton" :
        w.clicked.connect(lambda value, w = w : self.updateWidgetParameterNodeFromGUI(value, w))
      elif widgetClassName == "QCheckBox":
        w.toggled.connect(lambda value, w = w : self.updateWidgetParameterNodeFromGUI(value, w))
      elif widgetClassName == "QComboBox":
        w.currentIndexChanged.connect(lambda value, w = w : self.updateWidgetParameterNodeFromGUI(value, w))
      elif widgetClassName == "ctkSliderWidget":
        w.valueChanged.connect(lambda value, w = w : self.updateWidgetParameterNodeFromGUI(value, w))
      elif widgetClassName == "ctkRangeWidget":
        w.valuesChanged.connect(lambda value1, value2, w = w : self.updateWidgetParameterNodeFromGUI([value2, value2], w))
      elif widgetClassName == "vtkColorTransferFunction" or widgetClassName == "vtkPiecewiseFunction":
        if not w.HasObserver(vtk.vtkCommand.ModifiedEvent):
          w.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e, w = w : self.updateWidgetParameterNodeFromGUI([o,"add observers"], w))
      elif widgetClassName == "qMRMLNodeComboBox":
        w.currentNodeChanged.connect(lambda value, w = w : self.updateWidgetParameterNodeFromGUI(value, w))
      elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':
        self.logic.customShader[self.logic.shaderIndex].customShaderPoints.pointModifiedEventTag = w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.logic.customShader[self.logic.shaderIndex].customShaderPoints.onEndPointsChanged)
        w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.logic.customShader[self.logic.shaderIndex].customShaderPoints.onEndPointAdded)
        w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.pointModified)
        w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, lambda c, e, name = w.name, w = w : self.updateWidgetParameterNodeFromGUI([c, "PointPositionDefinedEvent", name], w))

    def removeGUIObservers(self, w):
      """Function to remove observers from the GUI's widget.

      """  
      
      widgetClassName = self.getClassName(w)
      if widgetClassName=="QPushButton" :
        w.clicked.disconnect(self.updateWidgetParameterNodeFromGUI) 
      elif widgetClassName == "QCheckBox":
        w.toggled.disconnect(self.updateWidgetParameterNodeFromGUI) 
      elif widgetClassName == "QComboBox":
        w.currentIndexChanged.disconnect(self.updateWidgetParameterNodeFromGUI)
      elif widgetClassName == "ctkSliderWidget":
        w.valueChanged.disconnect(self.updateWidgetParameterNodeFromGUI)
      elif widgetClassName == "ctkRangeWidget":
        w.valuesChanged.disconnect(self.updateWidgetParameterNodeFromGUI)
      elif widgetClassName == "vtkColorTransferFunction" or widgetClassName == "vtkPiecewiseFunction":
        w.RemoveAllObservers()
      elif widgetClassName == "qMRMLNodeComboBox":
        w.currentNodeChanged.disconnect(self.updateWidgetParameterNodeFromGUI)
      elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':
        w.RemoveObservers(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent)
        w.RemoveObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent)

    def updateWidgetGUIFromParameterNode(self, w, caller=None, event=None):
        """Function to update GUI from parameter node values

        :param caller: Caller of the function.
        :param event: Event that triggered the function.
        """   
        parameterNode = self.logic.parameterNode

        # Disables updateParameterNodeFromGUI signal 
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
            endPoints = self.logic.customShader[self.logic.shaderIndex].customShaderPoints.endPoints
            # endPoints.RemoveAllControlPoints()
            volumeName = self.logic.volumeRenderingDisplayNode.GetVolumePropertyNode().GetName()
            for m in markups :
              values = parameterNode.GetParameter(m)
              #If point was defined
              values = [float(k) for k in values.split(",")]
              if len(values) > 1 :
                type_ = m.replace(w.name, '')
                values.pop()
                index = endPoints.AddFiducialFromArray(values, type_)
                endPoints.SetNthControlPointAssociatedNodeID(index, m)
                CSName = w.name.replace(volumeName+'markup'+type_, '')
                visible = self.CSName+"markup" == CSName 
                self.logic.customShader[self.logic.shaderIndex].customShaderPoints.pointIndexes[m] = index
                world = [0,0,0]
                endPoints.GetNthControlPointPositionWorld(index, world)  
                self.logic.customShader[self.logic.shaderIndex].customShaderPoints.onCustomShaderParamChangedMarkup(world, type_)
                endPoints.SetNthFiducialVisibility(index, visible)
        elif widgetClassName == "qMRMLNodeComboBox":
          w.setCurrentNodeID(parameterNode.GetNodeReferenceID(w.name))

    def updateWidgetParameterNodeFromGUI(self, value, w):
      """Function to update the parameter node from gui values.

      :param value: Value of the widget.  
      :type value: float
      :param w: Widget being modified.  
      :type w: QObject
      """
      parameterNode = self.logic.parameterNode
      oldModifiedState = parameterNode.StartModify()
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
        name = w.name + self.logic.customShader[self.logic.shaderIndex].customShaderPoints.pointType
        world = [0, 0, 0]
        if event == "PointPositionDefinedEvent" :
          index = caller.GetDisplayNode().GetActiveControlPoint()
          # Initialise point
          if parameterNode.GetParameter(name) == "":
            index = caller.GetDisplayNode().GetActiveControlPoint()
            caller.SetNthControlPointAssociatedNodeID(index, name)
            caller.GetNthControlPointPositionWorld(index, world)
            parameterNode.SetParameter(name, ",".join("{0}".format(n) for n in world))
            parameterNode.SetParameter(w.name, str(index))
            self.logic.customShader[self.logic.shaderIndex].customShaderPoints.pointIndexes[name] = index
          # Reset point
          elif self.logic.customShader[self.logic.shaderIndex].customShaderPoints.pointName != '' :
            name = self.logic.customShader[self.logic.shaderIndex].customShaderPoints.pointName
            index = self.logic.customShader[self.logic.shaderIndex].customShaderPoints.pointIndexes[name] 
            caller.GetNthControlPointPositionWorld(index, world)
            parameterNode.SetParameter(name, ",".join("{0}".format(n) for n in world))
            self.logic.customShader[self.logic.shaderIndex].customShaderPoints.pointName = ''
        if event == "PointModifiedEvent" :
          if parameterNode.GetParameter(w.name) != "" and index <= int(parameterNode.GetParameter(w.name)):
            pointName = caller.GetNthControlPointAssociatedNodeID(index)
            if parameterNode.GetParameter(pointName) != "":
              caller.GetNthControlPointPositionWorld(index, world)
              parameterNode.SetParameter(pointName, ",".join("{0}".format(n) for n in world))

      parameterNode.EndModify(oldModifiedState)









