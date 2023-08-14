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
from PRISMRenderingVolumes import *

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
        ## Secondary volume rendering active nodes if there are multiple volumes
        self.optionalWidgets = {}
        # hide volume rendering display node possibly loaded with the scene
        renderingDisplayNodes = slicer.util.getNodesByClass("vtkMRMLVolumeRenderingDisplayNode")
        for displayNode in renderingDisplayNodes:
            displayNode.SetVisibility(False)
        renderingDisplayNodes = None
        
        self.parameterNode = None

        self.volumeIndex = None

        self.volumes = []

        self.addObservers() 

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
        for i in range(len(self.volumes[self.volumeIndex].customShader)) :
          slicer.mrmlScene.RemoveNode(self.volumes[self.volumeIndex].customShader[i].customShaderPoints.endPoints)
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
        self.volumes[self.volumeIndex].customShader[self.volumes[self.volumeIndex].shaderIndex].setShaderParameter(param, 1)
        if str(CSName + paramName) in self.optionalWidgets :
          for p in self.optionalWidgets[CSName + paramName] :
            p.show()
            try : # if there are Optional Points
              for t in self.volumes[self.volumeIndex].customShader[self.volumes[self.volumeIndex].shaderIndex].customShaderPoints.pointTypes :
                if t in p.name:
                  self.volumes[self.volumeIndex].customShader[self.volumes[self.volumeIndex].shaderIndex].customShaderPoints.endPoints.SetNthControlPointVisibility(self.volumes[self.volumeIndex].customShader[self.volumes[self.volumeIndex].shaderIndex].customShaderPoints.pointIndexes["markup" + t], 1)
            except :
              pass
      else: 
        self.volumes[self.volumeIndex].customShader[self.volumes[self.volumeIndex].shaderIndex].setShaderParameter(param, 0)
        if str(CSName + paramName) in self.optionalWidgets :
          for p in self.optionalWidgets[CSName + paramName] :
            p.hide()
            try : # if there are Optional Points
              for t in self.volumes[self.volumeIndex].customShader[self.volumes[self.volumeIndex].shaderIndex].customShaderPoints.pointTypes :
                if t in p.name:
                  self.volumes[self.volumeIndex].customShader[self.volumes[self.volumeIndex].shaderIndex].customShaderPoints.endPoints.SetNthControlPointVisibility(self.volumes[self.volumeIndex].customShader[self.volumes[self.volumeIndex].shaderIndex].customShaderPoints.pointIndexes["markup" + t], 0)
            except :
              pass

    def setupVolume(self, volumeNode, comboBoxIndex):
      
      if self.volumeIndex is not None :
        self.volumes[self.volumeIndex].comboBoxIndex = comboBoxIndex
        if self.volumes[self.volumeIndex].volumeRenderingDisplayNode:
          self.volumes[self.volumeIndex].volumeRenderingDisplayNode.SetVisibility(False)

      index = self.checkIfVolumeExists(volumeNode)
      if index == -1 :
        self.volumes.append(PRISMRenderingVolume(self, volumeNode))
        self.volumeIndex = len(self.volumes) - 1
      else :
        self.volumeIndex = index

    def checkIfVolumeExists(self, volumeNode):
      """Checks if the volume is already in the list of volumes.

      :param volumeNode: Volume node to check. 
      :type volumeNode: vtkMRMLScalarVolumeNode
      :return: True if the volume is already in the list of volumes, False otherwise.
      :rtype: bool
      """
      for i, volume in enumerate(self.volumes) :
        if volume.volumeNode == volumeNode :
          return i
      return -1