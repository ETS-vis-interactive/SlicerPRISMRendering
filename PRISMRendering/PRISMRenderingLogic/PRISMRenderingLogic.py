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

from PRISMRenderingShaders.CustomShader import CustomShader

def get_function_name():
    return traceback.extract_stack(None, 2)[0][2]

def get_function_parameters_and_values():
    frame = inspect.currentframe().f_back
    args, _, _, values = inspect.getargvalues(frame)
    return ([(i, values[i]) for i in args])

log = logging.getLogger(__name__)

"""PRISMRenderingLogic Class containing the functions to interact between the interface and the shader.

:param ScriptedLoadableModuleLogic: Uses ScriptedLoadableModuleLogic base class, available at: Https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModuleLogic.py 
:type ScriptedLoadableModuleLogic: Class.
""" 
class PRISMRenderingLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):
  def __init__(self):
    slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic.__init__(self)
    self.createEndPoints()

    ## VR interaction parameters
    self.movingEntry = False
    ## VR interaction parameters
    self.moveRelativePosition = False

    ## Volume rendering active node
    self.volumeRenderingDisplayNode = None
    ## Secondary volume rendering active nodes if there are multiple volumes
    self.secondaryVolumeRenderingDisplayNodes = [None]*20
    ## Index of the current volume
    self.currentVolume = 0

    # hide volume rendering display node possibly loaded with the scene
    renderingDisplayNodes = slicer.util.getNodesByClass("vtkMRMLVolumeRenderingDisplayNode")
    for displayNode in renderingDisplayNodes:
      displayNode.SetVisibility(False)
    renderingDisplayNodes = None

    # By default, no special shader is applied
    ## Type of the current custom shader
    self.customShaderType = 'None'
    ## Class of the current custom shader
    self.customShader = None
    ## Types of the annotation points
    self.pointTypes = ['center', 'target', 'entry']
    ## Type of the annotation point being added to the scene
    self.pointType = ''
    ## Name of the annotation point being added to the scene
    self.pointName = ''
    ## Indexes of the points added in the scene
    self.pointIndexes = {}
    ## Markup button that has been pushed when addind an annotation point to the scene
    self.currentMarkupBtn = None
    ## Current parameter node of the scene
    self.parameterNode = None
    ## Observer of the parameter node
    self.parameterNodeObserver = None
    self.addObservers()
    ## Color transfer function of the principal volume
    self.colorTransferFunction = vtk.vtkColorTransferFunction()
    ## Opacity transfer function of the principal volume
    self.opacityTransferFunction = vtk.vtkPiecewiseFunction()
    ## Names of the widgets that are optionnal in the current shader
    self.optionalWidgets = {}
    ## Number of volumes in the shader
    self.numberOfVolumes = 0
    
  def enableOption(self, paramName, type_, checkBox, CSName) :
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
    if checkBox.isChecked() : 
      ## Boolean checking of there is a boolean option enabled/disabled in the shader
      self.optionEnabled = 1
      if str(CSName + paramName) in self.optionalWidgets :
        for i in self.optionalWidgets[CSName + paramName] :
          i.show()
    else: 
      self.optionEnabled = 0
      remove = False
      if str(CSName + paramName) in self.optionalWidgets :
        for i in self.optionalWidgets[CSName +paramName] :
          for t in self.pointTypes :
            if t in i.name :
              remove = True
          i.hide()

      if remove :
        self.endPoints.RemoveAllControlPoints()
    self.customShader.setShaderParameter(paramName, self.optionEnabled, type_)

  def addObservers(self):
    """Create all observers needed in the UI to ensure a correct behaviour."""
    
    self.pointModifiedEventTag = self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.onEndPointsChanged)
    self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.onEndPointAdded)
    slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)  

  #
  # End points functions
  #

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
    type_ = caller.GetNthFiducialLabel(call_data)
    pointName = caller.GetNthFiducialAssociatedNodeID(call_data)
    if pointName in self.pointIndexes.keys() and self.pointIndexes[pointName] == call_data :
      world = [0, 0, 0, 0]
      caller.GetNthFiducialWorldCoordinates(call_data, world)
      self.onCustomShaderParamChanged(world, type_, "markup")
    
  
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
        
      caller.SetNthFiducialLabel(pointIndex, self.pointType)
      self.onCustomShaderParamChanged(world, self.pointType, "markup")
      self.currentMarkupBtn.setText('Reset ' + self.pointType)

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


  def setPlacingMarkups(self, paramType, paramName, btn, interaction = 1, persistence = 0):
    """Activate Slicer markups module to set one or multiple markups in the given markups fiducial list.

    :param paramType: Type of the parameter. 
    :param paramName: Name of the parameter. 
    :type paramName: str
    :param btn: Button pushed to place the markup. 
    :type btn: QObject
    :param interaction:  
    :type interaction: Int0: /, 1: Place, 2: View transform, 3: / ,4: Select
    :param persistence:  
    :type persistence: Int0: Unique, 1: Peristent
    """
    
    ## Current markup being modified
    self.currentMarkupBtn = btn
    interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    interactionNode.SetCurrentInteractionMode(interaction)
    interactionNode.SetPlaceModePersistence(persistence)
    
    ## Type of the point being modified
    self.pointType = paramType
    self.pointName = paramName

    
  def onCustomShaderParamChanged(self, value, paramName, type_ ):
    """Change the custom parameters in the shader.

    :param value: Value to be changed 
    :type value: str
    :param paramName: Name of the parameter to be changed 
    :type paramName: Int
    :param type_: (float or int), type of the parameter to be changed
    """
    
    self.customShader.setShaderParameter(paramName, value, type_)
  
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
    
  def getEntry(self):
    """Get Entry point position. If not yet placed, return (0,0,0).

    :return: Entry markups position if placed, empty array if not. 
    :rtype: Array[double].
    """
    
    entry = [0, 0, 0]
    if self.endPoints.GetNumberOfControlPoints() >= 2:
      self.endPoints.GetNthFiducialPosition(1, entry)
    return entry
  
  def setEntry(self, entry):
    """Set Entry point position.

    :param entry: Entry markups position.
    :type entry: Arraydouble].
    """
    self.endPoints.SetNthFiducialPositionFromArray(1, entry)

  def getTarget(self):
    """Get Target point position. If not yet placed, return (0,0,0).

    :return: Entry markups position if placed, empty array if not. 
    :rtype: Array[double].
    """
    
    target = [0, 0, 0]
    if self.endPoints.GetNumberOfControlPoints() >= 1:
      self.endPoints.GetNthFiducialPosition(0, target)
    return target

  def setTarget(self,target):
    """Set Target point position.

    :param target: Entry markups position.
    :param target: Array[double].
    """
    self.endPoints.SetNthFiducialPositionFromArray(0, target)   

  #
  # Volume Rendering functions
  #

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


  def setCustomShaderType(self, shaderTypeName, volumeNode):
    """Set given shader type as current active shader.

    :param shaderTypeName: Name corresponding to the type of rendering needed.
    :type shaderTypeName: str

    :param volumeNode: Current volume.
    :type volumeNode: vtkMRMLScalarVolumeNode
    """
    
    self.customShaderType = shaderTypeName
    self.setupCustomShader(volumeNode)

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

  def onCloseScene(self, caller, event):
    """Function called when the scene is closed. Delete nodes in the scene."""
    self.deleteNodes()