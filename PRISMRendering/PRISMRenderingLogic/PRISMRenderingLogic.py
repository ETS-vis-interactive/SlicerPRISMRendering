import os, sys
import unittest
import vtk, qt, ctk, slicer
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
import traceback
import logging

from PRISMRenderingShaders.CustomShader import *
from PRISMRenderingParams import *

class PRISMRenderingLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic.__init__(self)

        self.volumeRenderingDisplayNode = None
        ## Secondary volume rendering active nodes if there are multiple volumes
        self.secondaryVolumeRenderingDisplayNodes = [None]*20
        ## Index of the current volume
        self.currentVolume = 0

        self.optionalWidgets = {}
        # hide volume rendering display node possibly loaded with the scene
        renderingDisplayNodes = slicer.util.getNodesByClass("vtkMRMLVolumeRenderingDisplayNode")
        for displayNode in renderingDisplayNodes:
            displayNode.SetVisibility(False)
        renderingDisplayNodes = None
        ## Type of the current custom shader
        self.customShaderType = 'None'
        ## Class of the current custom shader
        self.customShader = []
        ## Number of volumes in the shader
        self.numberOfVolumes = 0

        self.shaderIndex = 0
        
        self.parameterNode = None

        ## Color transfer function of the principal volume
        self.colorTransferFunction = vtk.vtkColorTransferFunction()
        ## Opacity transfer function of the principal volume
        self.opacityTransferFunction = vtk.vtkPiecewiseFunction()

        self.addObservers() 
 
    def renderVolume(self, volumeNode, multipleVolumes = False):
        """Use Slicer Volume Rendering module to initialize and setup rendering of the given volume node.
        
        :param volumeNode: Volume node to be rendered. 
        :type volumeNode: VtkMRMLVolumeNode
        :param multipleVolumes: If the rendered volume is a secondary volume. 
        :type multipleVolumes: Bool
        """
        logic = slicer.modules.volumerendering.logic()

        # Set custom shader to renderer
        if multipleVolumes == False :
          self.setupCustomShader(volumeNode)

        #if multiple volumes not enabled, turn off previous rendering
        if not multipleVolumes and self.volumeRenderingDisplayNode:
          self.volumeRenderingDisplayNode.SetVisibility(False)

        #if multiple volumes is enabled and number of volumes > 1, , turn off second rendering
        allVolumeRenderingDisplayNodes = set(slicer.util.getNodesByClass("vtkMRMLVolumeRenderingDisplayNode"))

        numberOfVolumeRenderingDisplayNodes = len([i for i in allVolumeRenderingDisplayNodes if i.GetVisibility() == 1])

        if self.secondaryVolumeRenderingDisplayNodes[self.currentVolume]:
          if numberOfVolumeRenderingDisplayNodes > self.numberOfVolumes and multipleVolumes:
            self.secondaryVolumeRenderingDisplayNodes[self.currentVolume].SetVisibility(False)

        # Check if node selected has a renderer
        displayNode = logic.GetFirstVolumeRenderingDisplayNode(volumeNode)
        if displayNode:
          displayNode.SetVisibility(True)
          displayNode.SetNodeReferenceID("shaderProperty", self.shaderPropertyNode.GetID())

          roi = displayNode.GetMarkupsROINode()
          if roi is None:
            logic.CreateROINode(displayNode)
            logic.FitROIToVolume(displayNode)

          if multipleVolumes :
            self.secondaryVolumeRenderingDisplayNodes[self.currentVolume] = displayNode
          else:
            self.volumeRenderingDisplayNode = displayNode
          return
        # if not, create a renderer
        # Slicer default command to create renderer and add node to scene
        displayNode = logic.CreateDefaultVolumeRenderingNodes(volumeNode)
        slicer.mrmlScene.AddNode(displayNode)
        displayNode.UnRegister(logic)
        logic.UpdateDisplayNodeFromVolumeNode(displayNode, volumeNode)
        volumeNode.AddAndObserveDisplayNodeID(displayNode.GetID())

        displayNode.SetNodeReferenceID("shaderProperty", self.customShader[self.shaderIndex].shaderPropertyNode.GetID())

        logic.FitROIToVolume(displayNode)

        # Add a color preset based on volume range
        self.updateVolumeColorMapping(volumeNode, displayNode)

        # Prevent volume to be moved in VR
        volumeNode.SetSelectable(False)
        volumeNode.GetImageData()
        # Display given volume
        displayNode.SetVisibility(True)

        # Set value as class parameter to be accesed in other functions
        if multipleVolumes :
          self.secondaryVolumeRenderingDisplayNodes[self.currentVolume] = displayNode
        else:
          self.volumeRenderingDisplayNode = displayNode
          volumePropertyNode = displayNode.GetVolumePropertyNode()
          self.colorTransferFunction = volumePropertyNode.GetColor() 
          self.opacityTransferFunction = volumePropertyNode.GetScalarOpacity() 
          volumeName = volumePropertyNode.GetName()
          self.colorTransferFunction.name = volumeName+"Original" + self.colorTransferFunction.GetClassName() 
          self.opacityTransferFunction.name = volumeName+"Original" + self.opacityTransferFunction.GetClassName()

    def setupCustomShader(self, volumeNode = None):
      """Get or create shader property node and initialize custom shader.

      :param volumeNode: Current volume.
      :type volumeNode: vtkMRMLScalarVolumeNode
      """
      CSExists = self.checkIfCSExists()
      if CSExists == -1:
        shaderPropertyName = "ShaderProperty"
        CustomShader.GetAllShaderClassNames()
        if self.volumeRenderingDisplayNode is None :
          ## Property node of the current shader
          self.shaderPropertyNode = slicer.vtkMRMLShaderPropertyNode()
          self.shaderPropertyNode.SetName(shaderPropertyName)
          slicer.mrmlScene.AddNode(self.shaderPropertyNode)
        else :
          self.shaderPropertyNode = self.volumeRenderingDisplayNode.GetShaderPropertyNode()
        if self.customShader != [] :
          self.customShader[self.shaderIndex].resetVolumeProperty()
        self.customShader.append(CustomShader.InstanciateCustomShader(self.customShaderType, self.shaderPropertyNode, volumeNode, self))
        self.shaderIndex = len(self.customShader)-1
        try :
          self.customShader[self.shaderIndex].customShaderPoints.updateGUIFromParameterNode(self)
        except :
          pass
        
      else :
        self.customShader[self.shaderIndex].resetVolumeProperty()
        self.shaderIndex = CSExists
        self.customShader[self.shaderIndex].shaderPropertyNode = self.shaderPropertyNode
        self.customShader[self.shaderIndex].volumeNode = volumeNode

    def setCustomShaderType(self, shaderTypeName, volumeNode):
      """Set given shader type as current active shader.

      :param shaderTypeName: Name corresponding to the type of rendering needed.
      :type shaderTypeName: str

      :param volumeNode: Current volume.
      :type volumeNode: vtkMRMLScalarVolumeNode
      """

      self.customShaderType = shaderTypeName
      self.setupCustomShader(volumeNode)

    def updateVolumeColorMapping(self, volumeNode, displayNode, volumePropertyNode = None):
      """Given a volume, compute a default color mapping to render volume in the given display node.
        If a volume property node is given to the function, uses it as color mapping.

      :param volumeNode: Volume node to be rendered.
      :type volumeNode: vtkMRMLVolumeNode
      :param displayNode: Default rendering display node. (CPU RayCast, GPU RayCast, Multi-Volume)
      :type displayNode: vtkMRMLVolumeRenderingDisplayNode
      :param volumePropertyNode: Volume propery node that carries the color mapping wanted. 
      :type volumePropertyNode: VtkMRMLVolumePropertyNode
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

    def onCustomShaderParamChanged(self, value, Param ):
      """Change the custom parameters in the shader.

      :param value: Value to be changed 
      :type value: str
      :param paramName: Name of the parameter to be changed 
      :type paramName: Int
      :param type_: (float or int), type of the parameter to be changed
      """
      
      self.customShader[self.shaderIndex].setShaderParameter(Param, value)

    def addObservers(self):
      slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)  

    def onCloseScene(self, caller, event):
      """Function called when the scene is closed. Delete nodes in the scene."""
      self.deleteNodes()

    def deleteNodes(self):
      """Deletes the nodes in the scene."""
      try :
        node = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.RemoveNode(node[0])
        slicer.mrmlScene.RemoveNode(self.shaderPropertyNode)
        for i in range(len(self.customShader)) :
          slicer.mrmlScene.RemoveNode(self.customShader[i].customShaderPoints.endPoints)
        CustomShader.clear()
      except:
        pass
    
    def enableOption(self, param, checkBox, CSName) :
      """Function to add or remove parameters according to the value of the boolean.

      :param paramName: Name of the parameter. 
      :type paramName: str
      :param type_: Type of the parameter.
      :type type_: str.
      :param checkBox: Checkbox to enable or disable the option. 
      :type checkBox: QCheckbox
      :param CSName: Name of the current custom shader. 
      :type CSName: str
      """
      paramName = param.name
      if checkBox.isChecked() :
        self.customShader[self.shaderIndex].setShaderParameter(param, 1)
        if str(CSName + paramName) in self.optionalWidgets :
          for p in self.optionalWidgets[CSName + paramName] :
            p.widget.show()
            try :
              p.label.show()
            except :
              pass
            try : # if there are Optional Points
              for t in self.customShader[self.shaderIndex].customShaderPoints.pointTypes :
                if t in p.name:
                  self.customShader[self.shaderIndex].customShaderPoints.endPoints.SetNthControlPointVisibility(self.customShader[self.shaderIndex].customShaderPoints.pointIndexes["markup" + t], 1)
            except :
              pass
      else: 
        self.customShader[self.shaderIndex].setShaderParameter(param, 0)
        if str(CSName + paramName) in self.optionalWidgets :
          for p in self.optionalWidgets[CSName + paramName] :
            p.widget.hide()
            try :
              p.label.hide()
            except :
              pass
            try : # if there are Optional Points
              for t in self.customShader[self.shaderIndex].customShaderPoints.pointTypes :
                if t in p.name:
                  self.customShader[self.shaderIndex].customShaderPoints.endPoints.SetNthControlPointVisibility(self.customShader[self.shaderIndex].customShaderPoints.pointIndexes["markup" + t], 0)
            except :
              pass

    def checkIfCSExists(self) :
      """Check if a custom shader exists.

      :param CSName: Name of the current custom shader. 
      :type CSName: str
      """
      for i, CS in enumerate(self.customShader) :
        if CS.GetDisplayName() == self.customShaderType :
          return i
      return -1
