#@file CustomShader.py

import imp
import sys
import inspect
import os
import importlib.util
import math

from PRISMRenderingParams import *
from PRISMRenderingPoints import *


"""CustomShader Class containing the function to access the parameters of the shader.
Generic Custom Shader
""" 

class CustomShader():
   
    def __init__(self, shaderPropertyNode, id, volumeNode = None):
        
        assert shaderPropertyNode != None, 'CustomShader: a valid shader property node must provided to the constructor'
        ## Property node of the shader
        self.shaderPropertyNode = shaderPropertyNode
        ## Properies of the shader
        self.shaderProperty = shaderPropertyNode.GetShaderProperty()
        ## Uniforms of the shader
        self.shaderUniforms = self.shaderPropertyNode.GetFragmentUniforms()

        self.allClasses = []

        self.param_list = []

        self.customShaderPoints = CustomShaderPoints(self, id)
    
    def setAllUniforms(self):
      for p in self.param_list:       
        p.setUniform(self)

    def setupShader(self):
      
      self.clear()
      self.setAllUniforms()

    @classmethod
    def InstanciateCustomShader(cls, shaderDisplayName, shaderPropertyNode, id, volumeNode):
        if shaderDisplayName == cls.GetDisplayName():
          return CustomShader(shaderPropertyNode, id,  volumeNode)

        for c in cls.allClasses:
          if c.GetDisplayName() == shaderDisplayName:
            return c(shaderPropertyNode, id, volumeNode)
        return None

    @classmethod
    def GetDisplayName(cls):
      """Function to get the name of the current class.

      :return: Name of the current class.
      :rtype: str
      """
      return 'None'          

    @classmethod
    def GetAllShaderClassNames(cls):
        allNames = []  # Noms des shaders
        cls.allClasses = []  # Classes des shaders

        packageName = 'PRISMRenderingShaders'
        package = __import__(packageName)

        csPath = os.path.dirname(package.__file__).replace("\\", "/")

        # Parcourir les fichiers Python dans le répertoire
        for dirpath, _, filenames in os.walk(csPath):
            for filename in filenames:
                filename, file_extension = os.path.splitext(filename)
                if file_extension == ".py":
                    module_name = filename
                    module_path = os.path.join(dirpath, filename + file_extension)

                    # Charger le module
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)

                    # Parcourir les membres du module pour vérifier les sous-classes de CustomShader
                    for name, obj in inspect.getmembers(mod):
                        if inspect.isclass(obj) and issubclass(obj, cls) and obj != cls:
                            cls.allClasses.append(obj)
                            allNames.append(obj.GetDisplayName())   
        allNames.append(cls.GetDisplayName())
        cls.allClasses.append(None)
        return allNames

    def clear(self):
      """Function to clear the shader.

      """
      self.shaderUniforms.RemoveAllUniforms()
      self.shaderProperty.ClearAllFragmentShaderReplacements()    

    @classmethod
    def GetBasicDescription(cls):
        """Function to get a basic description of the current shader.
        
        :return: Description of the current shader.
        :rtype: str
        """
        return 'Basic volume rendering shader.'
    
    def setShaderParameter(self, Param, paramValue):
      """Set the shader parameter.

      :param Param: Parameter to be changed 
      :type Param: str
      :param paramValue: Value to be changed 
      :type paramValue: str
      """
      Param.setValue(paramValue)
      Param.setUniform(self)

    def setShaderParameterMarkup(self, paramName, value):
      for i in self.param_list:
        if i.name == paramName:
          i.setValue(value)
          i.setUniform(self)
          break