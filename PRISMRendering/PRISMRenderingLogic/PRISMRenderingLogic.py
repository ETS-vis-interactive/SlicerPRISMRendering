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

        self.currentMarkupBtn = None

        self.pointTypes = ['center', 'target', 'entry']
        self.pointType = ''
        self.pointName = ''
        self.pointIndexes = {}

        self.optionalWidgets = {}
        # hide volume rendering display node possibly loaded with the scene
        renderingDisplayNodes = slicer.util.getNodesByClass("vtkMRMLVolumeRenderingDisplayNode")
        for displayNode in renderingDisplayNodes:
            displayNode.SetVisibility(False)
        renderingDisplayNodes = None
        ## Type of the current custom shader
        self.customShaderType = 'None'
        ## Class of the current custom shader
        self.customShader = None
        ## Number of volumes in the shader
        self.numberOfVolumes = 0
        
        self.parameterNode = None

        ## Color transfer function of the principal volume
        self.colorTransferFunction = vtk.vtkColorTransferFunction()
        ## Opacity transfer function of the principal volume
        self.opacityTransferFunction = vtk.vtkPiecewiseFunction()

        self.createEndPoints()
        self.addObservers()

    def createEndPoints(self):
      """Create endpoints."""
      # retrieve end points in the scene or create the node
      allEndPoints = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsFiducialNode','EndPoints')
      if allEndPoints.GetNumberOfItems() > 0:
        # set node used before reload in the current instance
        ## All endpoints in the scene
        self.endPoints = allEndPoints.GetItemAsObject(0)
        self.endPoints.RemoveAllControlPoints()
        self.endPoints.GetDisplayNode().SetGlyphScale(6.0)
      else:
        self.endPoints = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
        self.endPoints.SetName("EndPoints")
        self.endPoints.GetDisplayNode().SetGlyphScale(6.0)
        self.endPoints.RemoveAllControlPoints()
      allEndPoints = None  
 
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

        displayNode.SetNodeReferenceID("shaderProperty", self.customShader.shaderPropertyNode.GetID())

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

      shaderPropertyName = "ShaderProperty"
      CustomShader.GetAllShaderClassNames()
      if self.volumeRenderingDisplayNode is None :
        ## Property node of the current shader
        self.shaderPropertyNode = slicer.vtkMRMLShaderPropertyNode()
        self.shaderPropertyNode.SetName(shaderPropertyName)
        slicer.mrmlScene.AddNode(self.shaderPropertyNode)
      else :
        self.shaderPropertyNode = self.volumeRenderingDisplayNode.GetShaderPropertyNode()

      self.customShader = CustomShader.InstanciateCustomShader(self.customShaderType, self.shaderPropertyNode, volumeNode)
      self.customShader.setupShader() 

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
      
      self.customShader.setShaderParameter(Param, value)

    def onCustomShaderParamChangedMarkup(self, value, paramName):
      """Change the custom parameters in the shader.

      :param value: Value to be changed 
      :type value: str
      :param paramName: Name of the parameter to be changed 
      :type paramName: Int
      :param type_: (float or int), type of the parameter to be changed
      """

      self.customShader.setShaderParameterMarkup(paramName, value)

    def setPlacingMarkups(self, paramType, paramName, btn, interaction = 1, persistence = 0):
      """Activate Slicer markups module to set one or multiple markups in the given markups fiducial list.

      :param btn: Button pushed to place the markup. 
      :type btn: QObject
      :param interaction:  
      :type interaction: Int0: /, 1: Place, 2: View transform, 3: / ,4: Select
      :param persistence:  
      :type persistence: Int0: Unique, 1: Peristent
      """
    
      self.currentMarkupBtn = btn
      self.pointType = paramType
      self.pointName = paramName

      # Getting the "EndPoints" node (always first MarkupsFiducial created)
      node = slicer.mrmlScene.GetNodeByID("vtkMRMLMarkupsFiducialNode1")
      # Setting the active node of markup list
      slicer.modules.markups.logic().SetActiveList(node)

      interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
      interactionNode.SetCurrentInteractionMode(interaction)
      interactionNode.SetPlaceModePersistence(persistence)

    def onEndPointAdded(self, caller, event):
     """Callback function to get the position of the new point.

     :param caller: Slicer.mrmlScene, Slicer active scene.
     :param event: Flag corresponding to the triggered event. 
     :type event: str
     """

     world = [0, 0, 0, 0]

     if self.pointType in self.pointTypes:
       pointIndex = caller.GetDisplayNode().GetActiveControlPoint()
       caller.GetNthFiducialWorldCoordinates(pointIndex, world)
       # If the point was already defined
       if self.pointName in self.pointIndexes.keys() :
         index = self.pointIndexes[self.pointName]
         caller.SetNthFiducialWorldCoordinates(index, world)
         caller.RemoveNthControlPoint(pointIndex)
       else :
         self.pointIndexes[self.pointName] = pointIndex

       caller.SetNthControlPointLabel(pointIndex, self.pointType)
       self.onCustomShaderParamChangedMarkup(world, self.pointType)
       self.currentMarkupBtn.setText('Reset ' + self.pointType)

    def addObservers(self):
      self.pointModifiedEventTag = self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.onEndPointsChanged)
      self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.onEndPointAdded)
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
        slicer.mrmlScene.RemoveNode(self.endPoints)
        CustomShader.clear()
      except:
        pass

    @vtk.calldata_type(vtk.VTK_INT)
    def onEndPointsChanged(self, caller, event, call_data):
      """Callback function to get the position of the modified point.
      Note: Vtk.calldata_type(vtk.VTK_OBJECT) function get calling instance as a vtkMRMLNode to be accesed in the function.
   
      :param caller: Slicer active scene.
      :type caller: SlicermrmlScene.
      :param event: Flag corresponding to the triggered event. 
      :type event: str
      :param call_data: VtkMRMLNode, Node added to the scene.
      """
      
   
      #check if the point was added from the module and was set
      type_ = caller.GetNthControlPointLabel(call_data)
      pointName = caller.GetNthControlPointAssociatedNodeID(call_data)
      if pointName in self.pointIndexes.keys() and self.pointIndexes[pointName] == call_data :
        world = [0, 0, 0, 0]
        caller.GetNthFiducialWorldCoordinates(call_data, world)
        self.onCustomShaderParamChangedMarkup(world, type_)
    
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
        self.customShader.setShaderParameter(param, 1)
        if str(CSName + paramName) in self.optionalWidgets :
          for p in self.optionalWidgets[CSName + paramName] :
            p.widget.show()
            try :
              p.label.show()
            except :
              pass
            # for t in self.pointTypes :
            #   if t in i.name:
            #    pointListNode = slicer.util.getNode("vtkMRMLMarkupsFiducialNode1")
            #    pointListDisplayNode = pointListNode.GetDisplayNode()
            #    pointListDisplayNode.SetVisibility(True)
      else: 
        self.customShader.setShaderParameter(param, 0)
        if str(CSName + paramName) in self.optionalWidgets :
          for p in self.optionalWidgets[CSName + paramName] :
            p.widget.hide()
            try :
              p.label.hide()
            except :
              pass
            # for t in self.pointTypes :
            #   if t in i.name:
            #    pointListNode = slicer.util.getNode("vtkMRMLMarkupsFiducialNode1")
            #    pointListDisplayNode = pointListNode.GetDisplayNode()
            #    pointListDisplayNode.SetVisibility(False)