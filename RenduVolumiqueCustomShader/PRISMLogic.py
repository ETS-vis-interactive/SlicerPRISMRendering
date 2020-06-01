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
    """ Callback function w hen a the left controller position has changed. Used to change "relativePosition"
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