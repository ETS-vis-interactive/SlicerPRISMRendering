#@file PRISMLogic.py

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
import traceback

from Resources.CustomShader import CustomShader

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

"""!@class PRISMLogic
@brief class PRISMLogic
@param ScriptedLoadableModuleLogic class: Uses ScriptedLoadableModuleLogic base class, available at: https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModuleLogic.py
""" 
class PRISMLogic(ScriptedLoadableModuleLogic):
  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    self.createEndPoints()

    # VR interaction parameters
    self.movingEntry = False
    self.moveRelativePosition = False

    # init volume rendering active node
    self.volumeRenderingDisplayNode = None
    self.secondaryVolumeRenderingDisplayNodes = [None]*20
    self.currentVolume = 0

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
    self.colorTransferFunction = vtk.vtkColorTransferFunction()
    self.opacityTransferFunction = vtk.vtkPiecewiseFunction()
    self.optionalWidgets = {}
    self.numberOfVolumes = 0

  def enableOption(self, paramName, type_, checkBox, CSName) :
    """!@brief Function to add or remove parameters according to the value of the boolean.

    @param paramName str : Name of the parameter.
    @param type_ str : Type of the parameter.
    @param checkBox QCheckbox : Checkbox to enable or disable the option.
    @param CSName str : Name of the current custom shader.
    """
    if str(CSName + paramName) in self.optionalWidgets :
      if checkBox.isChecked() :  
        for i in self.optionalWidgets[CSName + paramName] :
          i.show()
        self.optionEnabled = 1
      else: 
        self.optionEnabled = 0
        for i in self.optionalWidgets[CSName +paramName] :
          i.hide()
          self.endPoints.RemoveAllMarkups()

    self.customShader.setShaderParameter(paramName, self.optionEnabled, type_)

  def addObservers(self):
    """!@brief Function to create all observers needed in the UI to ensure a correct behaviour.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    self.pointModifiedEventTag = self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.onEndPointsChanged)
    self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.onEndPointAdded)
    slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)  

  #
  # End points functions
  #

  @vtk.calldata_type(vtk.VTK_INT)
  def onEndPointsChanged(self, caller, event, call_data):
    """!@brief Callback function to get the position of the modified point.
    Note: @vtk.calldata_type(vtk.VTK_OBJECT) function get calling instance as a vtkMRMLNode to be accesed in the function.

    @param caller slicer.mrmlScene: Slicer active scene.
    @param event str: Flag corresponding to the triggered event.
    @param call_data vtkMRMLNode: Node added to the scene.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))

    #check if the point was added from the module and was set
    if (call_data == self.centerPointIndex or call_data == self.entryPointIndex or call_data == self.targetPointIndex ):
      name = caller.GetNthFiducialLabel(call_data)
      world = [0, 0, 0, 0]
      caller.GetNthFiducialWorldCoordinates(call_data, world)
      self.onCustomShaderParamChanged(world, name, "markup")
    
  def onEndPointAdded(self, caller, event):
    """!@brief Callback function to get the position of the new point.
    @param caller slicer.mrmlScene: Slicer active scene.
    @param event str: Flag corresponding to the triggered event.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    world = [0, 0, 0, 0]
    self.centerPointIndex = -1
    self.targetPointIndex = -1
    self.entryPointIndex = -1

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
    """!@brief Deletes the nodes in the scene.

    """
    try :
      node = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")
      slicer.mrmlScene.RemoveNode(node[0])
      slicer.mrmlScene.RemoveNode(self.shaderPropertyNode)
      slicer.mrmlScene.RemoveNode(self.endPoints)
      CustomShader.clear()
    except:
      pass


  def setPlacingMarkups(self, paramName, btn, interaction = 1, persistence = 0):
    """!@brief Activate Slicer markups module to set one or multiple markups in the given markups fiducial list.

    @param markupsFiducialNode vtkMRMLMarkupsFiducialNode : List in which adding new markups.
    @param interaction int : 0: /, 1: place, 2: view transform, 3: / ,4: Select
    @param persistence int : 0: unique, 1: peristent
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    ## Current markup being modified
    self.currentMarkupBtn = btn
    interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    interactionNode.SetCurrentInteractionMode(interaction)
    interactionNode.SetPlaceModePersistence(persistence)
    
    ## Type of the point being modified
    self.pointType = paramName
    
  def onCustomShaderParamChanged(self, value, paramName, type_ ):
    """!@brief Change the custom parameters in the shader.

    @param value : value to be changed
    @param paramName int : name of the parameter to be changed
    @param type_ (float or type): type of the parameter to be changed
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    self.customShader.setShaderParameter(paramName, value, type_)
  
  def createEndPoints(self):
    """!@brief Create endpoints.

    """
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
    """!@brief Get Entry point position. If not yet placed, return (0,0,0).

    @return array[double]: Entry markups position if placed, empty array if not.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    entry = [0, 0, 0]
    if self.endPoints.GetNumberOfControlPoints() >= 2:
      self.endPoints.GetNthFiducialPosition(1, entry)
    return entry
  
  def setEntry(self, entry):
    """!@brief Set Entry point position.
    @param entry array[double]: Entry markups position.
    """
    self.endPoints.SetNthFiducialPositionFromArray(1, entry)

  def getTarget(self):
    """!@brief Get Target point position. If not yet placed, return (0,0,0).

    @return array[double]: Entry markups position if placed, empty array if not.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    target = [0, 0, 0]
    if self.endPoints.GetNumberOfControlPoints() >= 1:
      self.endPoints.GetNthFiducialPosition(0, target)
    return target

  def setTarget(self,target):
    """!@brief Set Target point position.

    @param target array[double]: Entry markups position.
    """
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
    """!@brief Callback function on trigger pressed event. If controller is near the entry point, starts modification of its position.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
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
    """!@brief Callback function when right trigger is released. Drop entry point at current controller position.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    if self.movingEntry:
      # Unselect point to restore default red color. Check comment above.
      self.endPoints.SetNthControlPointSelected(1, True)
      self.endPoints.GetMarkupsDisplayNode().SetColor(0,1,1)
      self.movingEntry = False

  def onRightControllerMoved(self,caller,event):
    """!@brief Callback function when a the right controller position has changed.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
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
    """!@brief Callback function on trigger pressed event. If a shader with "relativePosition" parameter has been selected
        allows user to change this parameter based on future position compared to the position when pressed.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    if not self.customShader:
      return
    if self.customShader.hasShaderParameter('relativePosition', float):
      # Set init position to be compared with future positions
      self.leftInitPos = self.getLeftControllerPosition()
      self.leftInitRatio = self.customShader.getShaderParameter("relativePosition", float)
      self.moveRelativePosition = True

  def onLeftControllerTriggerReleased(self):
    """!@brief Callback function on trigger released event. Stop changing the relativePosition shader parameter.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    self.moveRelativePosition = False

  def onLeftControllerMoved(self,caller,event):
    """!@brief Callback function w hen a the left controller position has changed. Used to change "relativePosition"
        current shader parameter and laser position.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
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

  def renderVolume(self, volumeNode, multipleVolumes = False):
    """!@brief Use Slicer Volume Rendering module to initialize and setup rendering of the given volume node.
    
    @param volumeNode vtkMRMLVolumeNode : Volume node to be rendered.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    logic = slicer.modules.volumerendering.logic()

    # Set custom shader to renderer
    self.setupCustomShader()

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
  

  def setCustomShaderType(self, shaderTypeName):
    """ Set given shader type as current active shader

    @param shaderTypeName str : 'Sphere Carving', 'Opacity Peeling'. Name corresponding to the type of rendering needed.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
    self.customShaderType = shaderTypeName
    self.setupCustomShader()

  def setupCustomShader(self):
    """!@brief Get or create shader property node and initialize custom shader.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
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
    """!@brief Given a volume, compute a default color mapping to render volume in the given display node.
        If a volume property node is given to the function, uses it as color mapping.

    @param volumeNode: (vtkMRMLVolumeNode): Volume node to be rendered.
    @param displayNode: (vtkMRMLVolumeRenderingDisplayNode) Default rendering display node. (CPU RayCast, GPU RayCast, Multi-Volume)
    @param volumePropertyNode vtkMRMLVolumePropertyNode : Volume propery node that carries the color mapping wanted.
    """
    #log.info(get_function_name()  + str(get_function_parameters_and_values()))
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
    """!@brief Function called when the scene is closed. Delete nodes in the scene.

    """
    self.deleteNodes()