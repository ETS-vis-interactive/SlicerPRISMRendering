import os, sys
import unittest
from PythonQt.QtCore import *
import vtk, qt, ctk

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
import SampleData
import hashlib

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

from PRISMRenderingShaders.CustomShader import *
from PRISMRenderingParams import *
from PRISMRenderingLogic import *


class PRISMRendering(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        slicer.ScriptedLoadableModule.ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "PRISMRendering"  # TODO: make this more human readable by adding spaces
        self.parent.categories = [
            "Rendering"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = [
            "Tiphaine RICHARD (ETS), Simon Drouin (ETS), Camille Hascoët (ETS)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """This module is an implementation of the PRISM customizable volume rendering framework in 3D Slicer."""
        self.parent.helpText += "<p>For more information see the <a href=\"https://ets-vis-interactive.github.io/SlicerPRISM/\">online documentation</a>.</p>"
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """This file was developped by Tiphaine RICHARD at Ecole de Technologie Superieure (Montreal, Canada)"""

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


def registerSampleData():
    """
  Add data sets to Sample Data module.
  """
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # TemplateKey1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='PRISMSampleData',
        sampleName='SphereCarvingSampleData',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'SphereCarving.png'),
        # Download URL and target file name
        uris="https://ets-vis-interactive.github.io/SlicerPRISMRenderingDatabase/Volumes/MRI_Head.mnc",
        fileNames='SphereCarvingSampleData.mnc',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:4802487c31c1dcd24434cb370906e1002d515c3abed1ce00385b2307f1370c13',
        # This node name will be used when the data set is loaded
        nodeNames='SphereCarvingSampleData'
    )

    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='PRISMSampleData',
        sampleName='OutlineSampleData',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'Outline.png'),
        # Download URL and target file name
        uris="https://ets-vis-interactive.github.io/SlicerPRISMRenderingDatabase/Volumes/CTA_Brain.mnc",
        fileNames='OutlineSampleData.mnc',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:4278daf18bd75542d68305d56630e78379ca8cbe295e9cf4fa52bb318445858b',
        # This node name will be used when the data set is loaded
        nodeNames='OutlineSampleData'
    )

    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='PRISMSampleData',
        sampleName='OpacityPeelingSampleData',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'OpacityPeeling.png'),
        # Download URL and target file name
        uris="https://ets-vis-interactive.github.io/SlicerPRISMRenderingDatabase/Volumes/MRI_Head.mnc",
        fileNames='OpacityPeelingSampleData.mnc',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:4802487c31c1dcd24434cb370906e1002d515c3abed1ce00385b2307f1370c13',
        # This node name will be used when the data set is loaded
        nodeNames='OpacityPeelingSampleData'
    )

    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='PRISMSampleData',
        sampleName='ChromaDepthPerceptionSampleData',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'ChromaDepthPerception.png'),
        # Download URL and target file name
        uris="https://ets-vis-interactive.github.io/SlicerPRISMRenderingDatabase/Volumes/CTA_Brain.mnc",
        fileNames='ChromaDepthPerceptionSampleData.mnc',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:4278daf18bd75542d68305d56630e78379ca8cbe295e9cf4fa52bb318445858b',
        # This node name will be used when the data set is loaded
        nodeNames='ChromaDepthPerceptionSampleData'
    )


class PRISMRenderingWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self.parameterNode = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""

        ScriptedLoadableModuleWidget.setup(self)

        ## Create module logic
        self.logic = PRISMRenderingLogic()

        ## Find all custom shader classes available
        allShaderTypes = CustomShader.GetAllShaderClassNames()

        # Load widget from .ui file (created by Qt Designer)
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/PRISMRendering.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        #
        # Data Area
        #
        self.ui.imageSelector.currentNodeChanged.connect(
            lambda value, w=self.ui.imageSelector: self.onImageSelectorChanged(value, w))

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
        self.ui.sampleDataButton.clicked.connect(self.onSampleDataButtonClicked)
        self.ui.enableROICheckBox.toggled.connect(self.onEnableROICheckBoxToggled)
        self.ui.displayROICheckBox.toggled.connect(self.onDisplayROICheckBoxToggled)
        self.ui.enableScalingCheckBox.toggled.connect(self.onEnableScalingCheckBoxToggled)
        self.ui.enableRotationCheckBox.toggled.connect(self.onEnableRotationCheckBoxToggled)
        self.ui.virtualRealityEnableButton.clicked.connect(self.onVirtualRealityButtonClicked)
        self.ui.virtualRealityReloadButton.clicked.connect(self.onVirtualRealityReloadClicked)

        #On cache aussi la selection du volume aui sera dispo au moment où le shader sera choisi
        #On cache aussi la partie des parametres
        if not self.logic.volumes:
            self.ui.viewSetupCollapsibleButton.hide()
            self.ui.volumeRenderingCheckBox.hide()
        self.ui.sampleDataButton.setEnabled(False)
        self.ui.enableROICheckBox.hide()
        self.ui.displayROICheckBox.hide()
        self.ui.enableScalingCheckBox.hide()
        self.ui.enableRotationCheckBox.hide()

        #
        # Custom Shader Area
        #
        
        # TODO: this is not working, find out why
        reloadIconPath = 'Resources/UI/reload.png'
        self.ui.reloadCurrentCustomShaderButton.setIcon(qt.QIcon(qt.QPixmap(reloadIconPath)))
        
        # Icons

        # Load all necessary icons for the Custom Shader Area
        self.loadIcons({
            'reloadCurrentCustomShaderButton': ('reload.png', 15, 24),
            'resetParametersButton': ('reset.png', 13, 24),
            'openCustomShaderButton': ('edit.png', 15, 24),
        })

        
        # Reset the parameters of the current custom shader
        self.ui.resetParametersButton.clicked.connect(self.onResetParametersButtonClicked)


        # Populate combobox with every types of shader available
        for shaderType in allShaderTypes:
            self.ui.customShaderCombo.addItem(shaderType)
        self.ui.customShaderCombo.setCurrentIndex(0)
        self.ui.customShaderCombo.currentIndexChanged.connect(self.onCustomShaderComboIndexChanged)

        ## All widgets of the UI that will be saved
        self.widgets = list(self.ui.centralWidget.findChildren(qt.QCheckBox()) \
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

        # TODO: check if this is working. We probably don't want to load a volume ever
        if self.logic.parameterNode.GetParameterCount() != 0:
            volumePath = self.logic.parameterNode.GetParameter("volumePath")
            # Set volume node
            if len(volumePath) != 0:
                volumeNode = slicer.util.loadVolume(volumePath)
                self.ui.imageSelector.setCurrentNode(volumeNode)

        # Update GUI
        self.addAllGUIObservers()
        if self.ui.imageSelector.currentNode() != None:
            self.updateWidgetParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)
            self.logic.setupVolume(self.ui.imageSelector.currentNode(), self.ui.customShaderCombo.currentIndex)
        self.updateBaseGUIFromParameterNode()

        self.sampleDatasNodeID = {}  # To store the sample data nodes
        self.sampleDataSwitch = False  # To know if the volume switch is when the user downloaded sample data so we setup the right shader
        self.firstSampleDataSwitch = False  # To know if it is the first time you load the sample data to set the right default values

        # Virtual Reality section
        if "SlicerVirtualReality" not in slicer.app.extensionsManagerModel().enabledExtensions:
            self.ui.virtualRealityEnableButton.setEnabled(False)
            self.ui.virtualRealityStatusLabel.setText(
                "Virtual Reality module not installed, go to extension manager to download it")
        else:
            self.checkVirtualReality()
            self.ui.virtualRealityStatusLabel.setText("Function not implemented")

        self.ui.virtualRealityCollapsibleButton.hide()
        self.ui.virtualRealityEnableButton.hide()
        self.ui.virtualRealityStatusLabel.hide()
        self.ui.virtualRealityReloadButton.hide()

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def loadIcons(self, button_icon_dict):
        """
        Loads icons for specified buttons given in a dictionary, with an optional size specification.

        :param button_icon_dict: A dictionary where keys are the attribute names of self.ui for each button,
                                 and values are tuples containing the filenames of the icons and optionally their sizes
                                 in the resources directory (filename, width, height).
        """
        script_dir = os.path.dirname(__file__)
        resources_dir = os.path.join(script_dir, "../PRISMRendering/Resources/Icons")

        for button_name, icon_details in button_icon_dict.items():
            icon_name, width, height = icon_details  # Unpack details
            icon_path = os.path.join(resources_dir, icon_name)
            if not os.path.exists(icon_path):
                print(f"Icon file does not exist: {icon_path}")
            else:
                pixmap = qt.QPixmap(icon_path)
                if pixmap.isNull():
                    print(f"Failed to load QPixmap for {icon_name}")
                else:
                    if width and height:  # Resize if width and height are provided
                        pixmap = pixmap.scaled(width, height, qt.Qt.KeepAspectRatio, qt.Qt.SmoothTransformation)
                    getattr(self.ui, button_name).setIcon(qt.QIcon(pixmap))

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
        if self.logic.volumes:
            if hasattr(self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex], 'customShaderPoints'):  # if the new shader has points
                self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.endPoints.SetDisplayVisibility(0)


        self.logic.setupVolume(self.ui.imageSelector.currentNode(), self.ui.customShaderCombo.currentIndex)
        self.ui.viewSetupCollapsibleButton.show()
        self.ui.volumeRenderingCheckBox.show()

        if self.ui.volumeRenderingCheckBox.isChecked():
            self.logic.volumes[self.logic.volumeIndex].renderVolume()
            if self.sampleDataSwitch:
                currentIndex = self.ui.customShaderCombo.currentIndex
                self.ui.customShaderCombo.setCurrentIndex(0)
                self.ui.customShaderCombo.setCurrentIndex(currentIndex)
                # for specified sample data values if defined
                if self.firstSampleDataSwitch:
                    if self.logic.volumes[self.logic.volumeIndex].customShader[
                        self.logic.volumes[self.logic.volumeIndex].shaderIndex].sampleValues != {}:
                        for p in self.logic.volumes[self.logic.volumeIndex].customShader[
                            self.logic.volumes[self.logic.volumeIndex].shaderIndex].param_list:
                            if self.logic.volumes[self.logic.volumeIndex].customShader[
                                self.logic.volumes[self.logic.volumeIndex].shaderIndex].sampleValues.get(
                                    p.name) is not None:
                                sampleValue = self.logic.volumes[self.logic.volumeIndex].customShader[
                                    self.logic.volumes[self.logic.volumeIndex].shaderIndex].sampleValues[p.name]
                                p.setValue(sampleValue, True)
                                p.defaultValue = sampleValue
                self.sampleDataSwitch = False
            else:
                if self.ui.customShaderCombo.currentIndex == self.logic.volumes[self.logic.volumeIndex].comboBoxIndex:
                    self.ui.customShaderCombo.setCurrentIndex(0)
                    self.ui.customShaderCombo.setCurrentIndex(self.logic.volumes[self.logic.volumeIndex].comboBoxIndex)
                else:
                    self.ui.customShaderCombo.setCurrentIndex(0)
                    self.ui.customShaderCombo.setCurrentIndex(self.logic.volumes[self.logic.volumeIndex].comboBoxIndex)
                    self.updateWidgetParameterNodeFromGUI(self.ui.customShaderCombo.currentText,
                                                          self.ui.customShaderCombo)

        self.updateWidgetParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)

    def checkVirtualReality(self):
        # Obtenir le noeud logique du module VR
        vrLogic = slicer.modules.virtualreality.logic()

        # Vérifier si un casque VR est connecté
        if vrLogic is not None and vrLogic.GetVirtualRealityActive():
            self.ui.virtualRealityEnableButton.setEnabled(True)
            self.ui.virtualRealityStatusLabel.setText("ready to use")
        else:
            self.ui.virtualRealityEnableButton.setEnabled(False)
            self.ui.virtualRealityStatusLabel.setText("no VR headset connected")

    def onVirtualRealityReloadClicked(self):
        self.checkVirtualReality()

    def onVirtualRealityButtonClicked(self):
        # slicer.modules.virtualreality.setVirtualRealityConnected(True)   # Verif si un casque est branché
        # slicer.modules.virtualreality.enableVirtualReality(True)     # Active la vue VR
        # slicer.modules.virtualreality.logic().SetGestureButtonToNone() // Est supposé unbind les touches, directement codé dans l'ext VR
        # print("ok")
        self.ui.virtualRealityStatusLabel.setText("Function not implemented")

    def createTestVolume(self):
        nodeName = "Volume"
        imageSize = [512, 512, 512]
        voxelType = vtk.VTK_UNSIGNED_CHAR
        imageOrigin = [0.0, 0.0, 0.0]
        imageSpacing = [1.0, 1.0, 1.0]
        imageDirections = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        fillVoxelValue = 0

        # Create an empty image volume, filled with fillVoxelValue
        imageData = vtk.vtkImageData()
        imageData.SetDimensions(imageSize)
        imageData.AllocateScalars(voxelType, 1)
        imageData.GetPointData().GetScalars().Fill(fillVoxelValue)
        # Create volume node
        volumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", nodeName)
        volumeNode.SetOrigin(imageOrigin)
        volumeNode.SetSpacing(imageSpacing)
        volumeNode.SetIJKToRASDirections(imageDirections)
        volumeNode.SetAndObserveImageData(imageData)
        volumeNode.CreateDefaultDisplayNodes()
        volumeNode.CreateDefaultStorageNode()
        return volumeNode

    def onSampleDataButtonClicked(self, caller=None, event=None):
        if slicer.mrmlScene.GetFirstNodeByName('Volume'):
            slicer.mrmlScene.RemoveNode(slicer.mrmlScene.GetFirstNodeByName('Volume'))
        if self.logic.volumeIndex is None:
            self.ui.imageSelector.setCurrentNode(self.createTestVolume())
        shaderName = self.ui.customShaderCombo.currentText
        self.sampleDataSwitch = True
        self.firstSampleDataSwitch = True

        if self.sampleDatasNodeID.get(shaderName) is not None:
            if self.sampleDatasNodeID[shaderName] != -1:

                self.firstSampleDataSwitch = False
                slicer.mrmlScene.RemoveNode(slicer.mrmlScene.GetFirstNodeByName('Volume'))
                self.ui.imageSelector.setCurrentNodeID(self.sampleDatasNodeID[shaderName])
                self.updateWidgetParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)

                self.ui.viewSetupCollapsibleButton.show()
                self.ui.volumeRenderingCheckBox.show()

            else:
                self.sampleDataSwitch = False

        else:
            #slicer.mrmlScene.RemoveNode(slicer.mrmlScene.GetFirstNodeByName('Volume'))
            self.logic.volumes[self.logic.volumeIndex].customShader[
                self.logic.volumes[self.logic.volumeIndex].shaderIndex].downloadSampleData(self.ui.imageSelector,
                                                                                           self.sampleDatasNodeID,
                                                                                           self.ui.customShaderCombo.currentText)
            if self.sampleDatasNodeID[shaderName] != -1:
                self.updateWidgetParameterNodeFromGUI(self.ui.imageSelector.currentNode, self.ui.imageSelector)
                self.ui.viewSetupCollapsibleButton.show()
                self.ui.volumeRenderingCheckBox.show()
            else:
                self.firstSampleDataSwitch = False
                self.sampleDataSwitch = False

    def onResetParametersButtonClicked(self, caller=None, event=None):
        """
        Reset the parameters of the custom shader to their default values.

        :param caller: Caller of the function.
        :param event: Event that triggered the function.
        """
        for p in self.logic.volumes[self.logic.volumeIndex].customShader[
            self.logic.volumes[self.logic.volumeIndex].shaderIndex].param_list:
            p.setValue(p.defaultValue, True)
        if self.logic.volumes[self.logic.volumeIndex].customShader[
            self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints is not None:
            self.logic.volumes[self.logic.volumeIndex].customShader[
                self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.UpdateGUIFromValues(
                self.logic)

    def onEnableRotationCheckBoxToggled(self, caller=None, event=None):
        """Function to enable rotating ROI box.
      :param caller: Caller of the function.
      :param event: Event that triggered the function.
      """
        if self.ui.enableRotationCheckBox.isChecked():
            self.ROIdisplay.RotationHandleVisibilityOn()
        else:
            self.ROIdisplay.RotationHandleVisibilityOff()

    def onEnableScalingCheckBoxToggled(self, caller=None, event=None):
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
            self.logic.volumes[self.logic.volumeIndex].volumeRenderingDisplayNode.SetCroppingEnabled(True)
            self.ui.displayROICheckBox.show()
        else:
            self.logic.volumes[self.logic.volumeIndex].volumeRenderingDisplayNode.SetCroppingEnabled(False)
            self.ui.displayROICheckBox.hide()
            self.ui.displayROICheckBox.setChecked(False)

    def onDisplayROICheckBoxToggled(self, caller=None, event=None):
        """Function to display ROI box and show/hide scaling and rotation parameters.

      :param caller: Caller of the function.
      :param event: Event that triggered the function.
      """

        if self.ui.displayROICheckBox.isChecked():
            self.ROI.SetDisplayVisibility(1)
            self.ui.enableScalingCheckBox.show()
            self.ui.enableRotationCheckBox.show()
        else:
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

        # Permet de supprimer le volume crée pour les modèles de test, il faut le supprimer pour avoir le rendu de base.
        if slicer.mrmlScene.GetFirstNodeByName('Volume'):
            slicer.mrmlScene.RemoveNode(slicer.mrmlScene.GetFirstNodeByName('Volume'))
        if self.ui.volumeRenderingCheckBox.isChecked():
            if self.ui.imageSelector.currentNode():
                self.logic.volumes[self.logic.volumeIndex].renderVolume()

                ## ROI of the current volume
                self.ROI = self.logic.volumes[self.logic.volumeIndex].volumeRenderingDisplayNode.GetMarkupsROINode()
                #self.ROI.SetAndObserveDisplayNodeID(self.transformDisplayNode.GetID())
                #self.ROI.SetAndObserveTransformNodeID(self.transformNode.GetID())
                self.ROI.SetDisplayVisibility(0)
                self.renameROI()
                self.ui.enableROICheckBox.show()
                self.UpdateShaderParametersUI()
                self.ui.customShaderCollapsibleButton.show()

                if self.ROIdisplay is None:
                    allRoiDisplayNodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsROIDisplayNode',
                                                                                'MarkupsROIDisplay')
                    if allRoiDisplayNodes.GetNumberOfItems() > 0:
                        self.ROIdisplay = allRoiDisplayNodes.GetItemAsObject(0)
                        self.ROIdisplayObserver = self.ROIdisplay.AddObserver(vtk.vtkCommand.ModifiedEvent,
                                                                              self.onROIdisplayChanged)

        else:
            for volume in self.logic.volumes:
                if volume.volumeRenderingDisplayNode:
                    volume.volumeRenderingDisplayNode.SetVisibility(False)
            if hasattr(self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex],'customShaderPoints'):  # if the new shader has points
                self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.endPoints.SetDisplayVisibility(0)
            self.ui.enableROICheckBox.setChecked(False)
            self.ui.displayROICheckBox.setChecked(False)
            #self.ui.sampleDataButton.hide()
            self.ui.enableROICheckBox.hide()
            self.ui.displayROICheckBox.hide()
            #self.ui.customShaderCollapsibleButton.hide()
        self.onCustomShaderComboIndexChanged(self.ui.customShaderCombo.currentIndex)

    def onEnableRotationCheckBoxToggled(self, caller=None, event=None):
        """Function to enable rotating ROI box.

          :param caller: Caller of the function.
          :param event: Event that triggered the function.
          """

        if self.ui.enableRotationCheckBox.isChecked():
            self.ROIdisplay.RotationHandleVisibilityOn()
        else:
            self.ROIdisplay.RotationHandleVisibilityOff()

    def onCustomShaderComboIndexChanged(self, i):
        """Callback function when the custom shader combo box is changed.
          :param i: Index of the element.
          :type i: int
          """
        if self.logic.volumes :
            if hasattr(self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex], 'customShaderPoints'):
                self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.endPoints.SetDisplayVisibility(0)

        if self.ui.customShaderCombo.currentText != "None":
            #If there is no volume
            if self.ui.imageSelector.currentNode() is not None:
                self.logic.volumes[self.logic.volumeIndex].setCustomShaderType(self.ui.customShaderCombo.currentText)
                self.logic.volumes[self.logic.volumeIndex].customShader[
                    self.logic.volumes[self.logic.volumeIndex].shaderIndex].setupShader()

                self.UpdateShaderParametersUI()
                self.updateWidgetParameterNodeFromGUI(self.ui.customShaderCombo.currentText, self.ui.customShaderCombo)

            #If a volume is existing
            """else:
                shaderNameList = []
                for i in self.logic.customShaderWithoutVolume:
                    shaderNameList.append(i[0])
                if self.ui.customShaderCombo.currentText not in shaderNameList:
                    self.logic.currentShader = CustomShader.InstanciateCustomShader(
                        self.ui.customShaderCombo.currentText, slicer.vtkMRMLShaderPropertyNode(), None, None)
                    self.logic.customShaderWithoutVolume.append(
                        [self.ui.customShaderCombo.currentText, self.logic.currentShader])
                else:
                    for shader in self.logic.customShaderWithoutVolume:
                        if shader[0] == self.ui.customShaderCombo.currentText:
                            self.logic.currentShader = shader[1]
                            break"""

        # If there is no selected shader, disables the buttons.
        if self.ui.customShaderCombo.currentText == "None":
            self.ui.openCustomShaderButton.setEnabled(False)
            self.ui.reloadCurrentCustomShaderButton.setEnabled(False)
        else:
            if self.ui.customShaderCombo.currentText in self.logic.samplesAvailable:
                self.ui.sampleDataButton.setEnabled(True)
            else:
                self.ui.sampleDataButton.setEnabled(False)

            self.ui.openCustomShaderButton.setEnabled(True)
            self.ui.reloadCurrentCustomShaderButton.setEnabled(True)
            if self.ui.imageSelector.currentNode is not None:
                self.ui.viewSetupCollapsibleButton.show()
                self.ui.volumeRenderingCheckBox.show()

        # TODO: fix this. The tooltip should only be related to shader and shouldn't have anything to do with volume index
        #self.ui.customShaderCollapsibleButton.setToolTip(self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex].GetBasicDescription())

    def updateParameterNodeFromGUI(self, value, w):
        """Function to update the parameter node from gui values.

      :param value: Value of the widget.  
      :type value: float
      :param w: Widget being modified.  
      :type w: QObject
      """
        if self.ui.imageSelector.currentNode() is None:
            return

        if w not in self.widgets:
            return

        if isinstance(w, Param):
            w.updateParameterNodeFromGUI(self)
        else:
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
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked,
                                   showResult=False)

    def renameROI(self):
        """Function to reset the ROI in the scene.

      """

        ## Node of the roi
        ROINodes = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsROINode', 'Volume rendering ROI')
        if ROINodes.GetNumberOfItems() > 0:
            # Set node used before reload in the current instance
            ROINode = ROINodes.GetItemAsObject(0)
            #ROINodes.ResetAnnotations()
            #slicer.modules.volumerendering.logic().FitROIToVolume(self.logic.volumes[self.logic.volumeIndex].volumeRenderingDisplayNode)
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
        # if self.logic.parameterNode and self.logic.parameterNodeObserver:
        #   self.logic.parameterNode.RemoveObserver(self.logic.parameterNodeObserver)
        #   self.logic.parameterNodeObserver = None

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
            if w.name == name and name != "":
                found = True
                index = i
                break

        if found:
            self.widgets[index] = widget
        else:
            self.widgets.append(widget)

    def UpdateShaderParametersUI(self):
        """Updates the shader parameters on the UI.

      """
        if self.ui.customShaderCombo.currentText is None:
            return

        if hasattr(self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex],'customShaderPoints'):  # if the new shader has points
            self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[
                self.logic.volumeIndex].shaderIndex].customShaderPoints.endPoints.SetDisplayVisibility(1)

        # Clear all the widgets except the combobox selector
        while self.ui.customShaderParametersLayout.count() != 1:
            ## Item of the combobox
            item = self.ui.customShaderParametersLayout.takeAt(self.ui.customShaderParametersLayout.count() - 1)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)

        # if self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.endPoints.GetNumberOfControlPoints() > 0 :
        # self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.endPoints.RemoveAllControlPoints()

        ## Name of the current shader, without spaces
        volumeName = self.logic.volumes[
            self.logic.volumeIndex].volumeRenderingDisplayNode.GetVolumePropertyNode().GetName()
        self.CSName = self.ui.customShaderCombo.currentText.replace(" ", "") + volumeName
        param_list = self.logic.volumes[self.logic.volumeIndex].customShader[
            self.logic.volumes[self.logic.volumeIndex].shaderIndex].param_list
        TFIndex = 0
        TFTypes = []
        self.setupDefaultTransferFunctions()
        for p in param_list:
            hideWidget = False
            Optional = False
            for i in self.logic.volumes[self.logic.volumeIndex].customShader[
                self.logic.volumes[self.logic.volumeIndex].shaderIndex].param_list:
                if isinstance(i, BoolParam):
                    if p.name in i.optionalWidgets:
                        Optional = True
                        bool_param = i
                        if self.logic.optionalWidgets.get(self.CSName + bool_param.name) == None:
                            self.logic.optionalWidgets[self.CSName + bool_param.name] = []
                        elif len(self.logic.optionalWidgets[self.CSName + bool_param.name]) == len(
                                bool_param.optionalWidgets):  #To avoid duplicates & reset after next GUI Setup
                            self.logic.optionalWidgets[self.CSName + bool_param.name] = []
                        if i.value == True:
                            hideWidget = False
                        else:
                            hideWidget = True
                        break
            if not isinstance(p, TransferFunctionParam):
                p.SetupGUI(self)
            else:
                TFIndex += 1
                TFTypes += [p.type]
                if TFIndex > self.numberOfTFTypes:
                    logging.error("Too many transfer function have been defined.")
                if len(TFTypes) > self.numberOfTFTypes:
                    logging.error("One transfer function has been assigned multiple times to the same volume.")
                p.SetupGUI(self, 0, TFIndex)
            try:
                self.ui.customShaderParametersLayout.addRow(p.label, p.widget)
                if Optional:
                    self.logic.optionalWidgets[self.CSName + bool_param.name] += [p]
                    if hideWidget:
                        p.widget.hide()
                        p.label.hide()
            except:
                self.ui.customShaderParametersLayout.addRow(p.widget)
                if Optional:
                    self.logic.optionalWidgets[self.CSName + bool_param.name] += [p]
                    if hideWidget:
                        p.widget.hide()

    def setupDefaultTransferFunctions(self):
        volumeName = self.logic.volumes[
            self.logic.volumeIndex].volumeRenderingDisplayNode.GetVolumePropertyNode().GetName()
        if self.logic.volumes[self.logic.volumeIndex].volumeRenderingDisplayNode != None:
            volumePropertyNode = self.logic.volumes[
                self.logic.volumeIndex].volumeRenderingDisplayNode.GetVolumePropertyNode()
            colorTransferFunction = vtk.vtkColorTransferFunction()
            opacityTransferFunction = vtk.vtkPiecewiseFunction()
            colorTransferFunction.RemoveAllObservers()
            opacityTransferFunction.RemoveAllObservers()
            colorTransferFunction.name = volumeName + "Original" + colorTransferFunction.GetClassName()
            opacityTransferFunction.name = volumeName + "Original" + opacityTransferFunction.GetClassName()
            self.appendList(opacityTransferFunction, opacityTransferFunction.name)
            self.appendList(colorTransferFunction, colorTransferFunction.name)
            # Keep the original transfert functions
            if self.logic.volumes[self.logic.volumeIndex].colorTransferFunction.GetSize() > 0:
                colorTransferFunction.DeepCopy(self.logic.volumes[self.logic.volumeIndex].colorTransferFunction)
                self.updateWidgetParameterNodeFromGUI(colorTransferFunction, colorTransferFunction.name)
            else:
                values = self.logic.parameterNode.GetParameter(colorTransferFunction.name + str(0))
                i = 0
                while values != "":
                    v = [float(k) for k in values.split(",")]
                    colorTransferFunction.AddRGBPoint(v[0], v[1], v[2], v[3], v[4], v[5])
                    i += 1
                    values = self.logic.parameterNode.GetParameter(colorTransferFunction.name + str(i))
            if not colorTransferFunction.HasObserver(vtk.vtkCommand.ModifiedEvent):
                colorTransferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e,
                                                                                       w=colorTransferFunction: self.updateWidgetParameterNodeFromGUI(
                    [o, e], w))
            volumePropertyNode.SetColor(colorTransferFunction)
            if self.logic.volumes[self.logic.volumeIndex].opacityTransferFunction.GetSize() > 0:
                opacityTransferFunction.DeepCopy(self.logic.volumes[self.logic.volumeIndex].opacityTransferFunction)
                self.updateWidgetParameterNodeFromGUI(opacityTransferFunction, opacityTransferFunction.name)
            else:
                values = self.logic.parameterNode.GetParameter(opacityTransferFunction.name + str(0))
                i = 0
                while values != "":
                    v = [float(k) for k in values.split(",")]
                    opacityTransferFunction.AddPoint(v[0], v[1], v[2], v[3])
                    i += 1
                    values = self.logic.parameterNode.GetParameter(opacityTransferFunction.name + str(i))
            if not opacityTransferFunction.HasObserver(vtk.vtkCommand.ModifiedEvent):
                opacityTransferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e,
                                                                                         w=opacityTransferFunction: self.updateWidgetParameterNodeFromGUI(
                    [o, e], w))
            volumePropertyNode.SetScalarOpacity(opacityTransferFunction)

    def getClassName(self, widget):
        """Function to get the class name of a widget.

      :param widget: Wanted widget. 
      :type widget: QObject
      :return: widget's class name. 
      :rtype: str
      """
        try:
            return widget.metaObject().getClassName()
        except:
            pass
        try:
            return widget.view().metaObject().getClassName()
        except:
            pass
        try:
            return widget.GetClassName()
        except:
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
            if item != None:
                widget = item.widget()
                if widget != None:
                    if (widget.name == widgetName):
                        return i

    @vtk.calldata_type(vtk.VTK_INT)
    def pointModified(self, caller, event, index):
        self.updateWidgetParameterNodeFromGUI([caller, "PointModifiedEvent", index],
                                              self.logic.volumes[self.logic.volumeIndex].customShader[
                                                  self.logic.volumes[
                                                      self.logic.volumeIndex].shaderIndex].customShaderPoints.endPoints)

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
        if widgetClassName == "QPushButton":
            w.clicked.connect(lambda value, w=w: self.updateWidgetParameterNodeFromGUI(value, w))
        elif widgetClassName == "QCheckBox":
            w.toggled.connect(lambda value, w=w: self.updateWidgetParameterNodeFromGUI(value, w))
        elif widgetClassName == "QComboBox":
            w.currentIndexChanged.connect(lambda value, w=w: self.updateWidgetParameterNodeFromGUI(value, w))
        elif widgetClassName == "ctkSliderWidget":
            w.valueChanged.connect(lambda value, w=w: self.updateWidgetParameterNodeFromGUI(value, w))
        elif widgetClassName == "ctkRangeWidget":
            w.valuesChanged.connect(
                lambda value1, value2, w=w: self.updateWidgetParameterNodeFromGUI([value2, value2], w))
        elif widgetClassName == "vtkColorTransferFunction" or widgetClassName == "vtkPiecewiseFunction":
            if not w.HasObserver(vtk.vtkCommand.ModifiedEvent):
                w.AddObserver(vtk.vtkCommand.ModifiedEvent,
                              lambda o, e, w=w: self.updateWidgetParameterNodeFromGUI([o, "add observers"], w))
        elif widgetClassName == "qMRMLNodeComboBox":
            w.currentNodeChanged.connect(lambda value, w=w: self.updateWidgetParameterNodeFromGUI(value, w))
        elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':
            self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[
                self.logic.volumeIndex].shaderIndex].customShaderPoints.pointModifiedEventTag = w.AddObserver(
                slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent,
                self.logic.volumes[self.logic.volumeIndex].customShader[
                    self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.onEndPointsChanged)
            w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent,
                          self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[
                              self.logic.volumeIndex].shaderIndex].customShaderPoints.onEndPointAdded)
            w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.pointModified)
            w.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent,
                          lambda c, e, name=w.name, w=w: self.updateWidgetParameterNodeFromGUI(
                              [c, "PointPositionDefinedEvent", name], w))

    def removeGUIObservers(self, w):
        """Function to remove observers from the GUI's widget.

      """

        widgetClassName = self.getClassName(w)
        if widgetClassName == "QPushButton":
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
        if value != '':
            if widgetClassName == "QPushButton":
                enabled = (int(value) != 0)
                w.setEnabled(enabled)
            elif widgetClassName == "QCheckBox":
                checked = (int(value) != 0)
                w.setChecked(checked)
            elif widgetClassName == "QComboBox":
                index = int(value)
                w.setCurrentIndex(index)
            elif widgetClassName == "ctkSliderWidget":
                value = float(value)
                w.setValue(value)
            elif widgetClassName == "ctkRangeWidget":
                values = value.split(',')
                w.minimumValue = float(values[0])
                w.maximumValue = float(values[1])
            elif widgetClassName == "vtkColorTransferFunction" or widgetClassName == "vtkPiecewiseFunction":
                for i in range(w.GetSize()):
                    values = self.logic.parameterNode.GetParameter(w.name + str(i))
                    if values != "":
                        w.SetNodeValue(i, [float(k) for k in values.split(",")])
            elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':
                params = parameterNode.GetParameterNames()
                markups = []
                for p in params:
                    if w.name in p:
                        markups.append(p)
                endPoints = self.logic.volumes[self.logic.volumeIndex].customShader[
                    self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.endPoints
                # endPoints.RemoveAllControlPoints()
                volumeName = self.logic.volumes[
                    self.logic.volumeIndex].volumeRenderingDisplayNode.GetVolumePropertyNode().GetName()
                for m in markups:
                    values = parameterNode.GetParameter(m)
                    #If point was defined
                    values = [float(k) for k in values.split(",")]
                    if len(values) > 1:
                        type_ = m.replace(w.name, '')
                        values.pop()
                        index = endPoints.AddFiducialFromArray(values, type_)
                        endPoints.SetNthControlPointAssociatedNodeID(index, m)
                        CSName = w.name.replace(volumeName + 'markup' + type_, '')
                        visible = self.CSName + "markup" == CSName
                        self.logic.volumes[self.logic.volumeIndex].customShader[
                            self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.pointIndexes[
                            m] = index
                        world = [0, 0, 0]
                        endPoints.GetNthControlPointPositionWorld(index, world)
                        self.logic.volumes[self.logic.volumeIndex].customShader[self.logic.volumes[
                            self.logic.volumeIndex].shaderIndex].customShaderPoints.onCustomShaderParamChangedMarkup(
                            world, type_)
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
        if widgetClassName == "QPushButton":
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
            if widgetClassName == "vtkColorTransferFunction":
                values = [0, 0, 0, 0, 0, 0]
            else:
                values = [0, 0, 0, 0]
            if nbPoints > 0:
                for i in range(nbPoints):
                    w.GetNodeValue(i, values)
                    parameterNode.SetParameter(w.name + str(i), ",".join("{0}".format(n) for n in values))
                # If points are deleted, remove them from the parameter node
                i += 1
                val = parameterNode.GetParameter(w.name + str(i))
                while val != '':
                    parameterNode.UnsetParameter(w.name + str(i))
                    i += 1
                    val = parameterNode.GetParameter(w.name + str(i))
        elif widgetClassName == "qMRMLNodeComboBox":
            parameterNode.SetNodeReferenceID(w.name, w.currentNodeID)
        elif widgetClassName == 'vtkMRMLMarkupsFiducialNode':
            caller = value[0]
            event = value[1]
            index = value[2]
            name = w.name + self.logic.volumes[self.logic.volumeIndex].customShader[
                self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.pointType
            world = [0, 0, 0]
            if event == "PointPositionDefinedEvent":
                index = caller.GetDisplayNode().GetActiveControlPoint()
                # Initialise point
                if parameterNode.GetParameter(name) == "":
                    index = caller.GetDisplayNode().GetActiveControlPoint()
                    caller.SetNthControlPointAssociatedNodeID(index, name)
                    caller.GetNthControlPointPositionWorld(index, world)
                    parameterNode.SetParameter(name, ",".join("{0}".format(n) for n in world))
                    parameterNode.SetParameter(w.name, str(index))
                    self.logic.volumes[self.logic.volumeIndex].customShader[
                        self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.pointIndexes[
                        name] = index
                # Reset point
                elif self.logic.volumes[self.logic.volumeIndex].customShader[
                    self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.pointName != '':
                    name = self.logic.volumes[self.logic.volumeIndex].customShader[
                        self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.pointName
                    index = self.logic.volumes[self.logic.volumeIndex].customShader[
                        self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.pointIndexes[name]
                    caller.GetNthControlPointPositionWorld(index, world)
                    parameterNode.SetParameter(name, ",".join("{0}".format(n) for n in world))
                    self.logic.volumes[self.logic.volumeIndex].customShader[
                        self.logic.volumes[self.logic.volumeIndex].shaderIndex].customShaderPoints.pointName = ''
            if event == "PointModifiedEvent":
                if parameterNode.GetParameter(w.name) != "" and index <= int(parameterNode.GetParameter(w.name)):
                    pointName = caller.GetNthControlPointAssociatedNodeID(index)
                    if parameterNode.GetParameter(pointName) != "":
                        caller.GetNthControlPointPositionWorld(index, world)
                        parameterNode.SetParameter(pointName, ",".join("{0}".format(n) for n in world))

        parameterNode.EndModify(oldModifiedState)
