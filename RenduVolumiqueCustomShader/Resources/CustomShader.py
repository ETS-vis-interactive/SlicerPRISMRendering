#@file CustomShader.py

import imp
import sys
import inspect
import os
import importlib.util

"""!@class CustomShader
@brief class CustomShader
Generic Custom Shader
""" 
class CustomShader():

  shaderfParams = {}
  shaderiParams = {}
  shader4fParams = {}
  shaderbParams = {}
  shaderrParams = {}
  shadertfParams = {}
  shadervParams = {}
  
  def __init__(self, shaderPropertyNode):
    assert shaderPropertyNode != None, 'CustomShader: a valid shader property node must provided to the constructor'
    self.shaderPropertyNode = shaderPropertyNode
    self.shaderProperty = shaderPropertyNode.GetShaderProperty()
    self.shaderUniforms = self.shaderPropertyNode.GetFragmentUniforms()
    self.paramfValues = {}
    self.paramiValues = {}
    self.param4fValues = {}
    self.parambValues = {}   
    self.paramrValues = {}   
    self.paramtfValues = {}   
    self.paramvValues = {}   
    for p in self.shaderfParams.keys():
      self.paramfValues[p] = self.shaderfParams[p]['defaultValue']
    for p in self.shaderiParams.keys():
      self.paramiValues[p] = self.shaderiParams[p]['defaultValue']
    for p in self.shader4fParams.keys():
      self.param4fValues[p] = self.shader4fParams[p]['defaultValue']   
    for p in self.shaderbParams.keys():
      self.parambValues[p] = self.shaderbParams[p]['defaultValue']   
    for p in self.shaderrParams.keys():
      self.paramrValues[p] = self.shaderrParams[p]['defaultValue']  
    for p in self.shadertfParams.keys():
      self.paramtfValues[p] = self.shadertfParams[p]['defaultVolume']  
    for p in self.shadervParams.keys():
      self.paramvValues[p] = self.shadervParams[p]['defaultValue']  

  @classmethod
  def InstanciateCustomShader(cls, shaderDisplayName, shaderPropertyNode):
    """!@brief Function instanciate a custom shdaer.

    @param shaderDisplayName str : Display name of the shader.
    @param shaderPropertyNode vtkMRMLShaderPropertyNode : Shader property node.
    """
    if shaderDisplayName == cls.GetDisplayName():
      return CustomShader(shaderPropertyNode)

    for c in cls.allClasses:
      if c.GetDisplayName() == shaderDisplayName:
        return c(shaderPropertyNode)
    return None

  @classmethod
  def GetAllShaderClassNames(cls):
    """!@brief Function to get the class names of all of the shaders.
    @return array[str] names of all the classes.

    """
    allNames = [] #names of shaders
    cls.allClasses = [] #classes of shaders

    #get path of package
    packageName = 'Resources'
    f, filename, description = imp.find_module(packageName)
    package = imp.load_module(packageName, f, filename, description)
    csPath = os.path.dirname(package.__file__)

    csClass = getattr(sys.modules[__name__], "CustomShader") # Custom shader class
    
    #find python files in directory
    for dirpath, _, filenames in os.walk(csPath):
      for filename in filenames:
        filename, file_extension = os.path.splitext(dirpath+"/"+filename)
        if file_extension == ".py":
          
          #load the module and save it
          dirpath, filename = os.path.split(filename + file_extension)
          loader = importlib.machinery.SourceFileLoader(filename, dirpath+"/"+filename)
          spec = importlib.util.spec_from_loader(loader.name, loader)
          mod = importlib.util.module_from_spec(spec)
          loader.exec_module(mod)

          #check if module is subclass of CustomShader
          currentModule = inspect.getmembers(mod, inspect.isclass)
          if (len(currentModule)) > 1 :
            m1 = currentModule[0][1]
            m2 = currentModule[1][1]
            if issubclass(m1, csClass) and (m1 != csClass ) :
              cls.allClasses.append(m1)
              allNames.append( m1.GetDisplayName()) 
            elif issubclass(m2, csClass) and (m2 != csClass ):
              cls.allClasses.append(m2)
              allNames.append( m2.GetDisplayName() )
    allNames.append( cls.GetDisplayName() )
    
    return allNames

  @classmethod
  def GetDisplayName(cls):
    """!@brief Function to get the name of the current class.
    @return str Display name.
    """
    return 'None'
  
  @classmethod
  def GetClassName(cls, shaderDisplayName):
    """!@brief Function to get a class from it's display name.
    @return cls class.
    """
    if shaderDisplayName == cls.GetDisplayName():
      return CustomShader

    for c in cls.allClasses:
      if c.GetDisplayName() == shaderDisplayName:
        return c
    return None
  
  @classmethod
  def GetClass(cls, shaderName):
    """!@brief Function to get a class from it's name.
    @return cls class.
    """
    if shaderName == cls.__name__:
      return CustomShader
  
    if not hasattr(cls, "allClasses"):
      print("ok")
      cls.GetAllShaderClassNames()
    for c in cls.allClasses:
      if c.__name__ == shaderName:
        return c
    return None

  @classmethod
  def hasShaderParameter(cls, name, type_):
    """!@brief Function to check if a parameter is in the shader.
    @param name str : name of the parameter.
    @param type str : type of the parameter.
    @return bool True if the parameter is in the shader, else False.
    """
    if type_ == float :
      return name in cls.shaderfParams
    elif type_ == int :
      return name in cls.shaderiParams

  def getParameterNames(self):
    """!@brief Function to get the shader parameter names
    @return array[str] Names of the parameters.
    """
    return []

  def getShaderPropertyNode(self):
    """!@brief Function to get the shader property node of the shader.
    @return vtkMRMLShaderPropertyNode shader property node of the shader.
    """
    return self.shaderPropertyNode

  def setupShader(self):
    """!@brief Function to setup the shader.
    """
    self.clear()
    self.setAllUniforms()

  def setPathEnds(self,entry,target):
    pass

  def setAllUniforms(self):
    """!@brief Function to set the uniforms of the shader.
    """
    for p in self.paramfValues.keys():
      self.shaderUniforms.SetUniformf(p, self.paramfValues[p])

    for p in self.paramiValues.keys():
      self.shaderUniforms.SetUniformi(p, int(self.paramiValues[p]))

    for p in self.parambValues.keys():
      self.shaderUniforms.SetUniformi(p, int(self.parambValues[p]))

    for p in self.param4fValues.keys():
      x = self.param4fValues.get(p).get('x')
      y = self.param4fValues.get(p).get('y')
      z = self.param4fValues.get(p).get('z')
      w = self.param4fValues.get(p).get('w')
      self.shaderUniforms.SetUniform4f(p, [x, y, z , w])
    
    for p in self.paramrValues.keys():
      self.shaderUniforms.SetUniformi(p+ "Min", int(self.paramrValues[p][0]))
      self.shaderUniforms.SetUniformi(p+ "Max", int(self.paramrValues[p][1]))

  def setShaderParameter(self, paramName, paramValue, type_):
    """!@brief Function to set the parameters of the shader.
    @param paramName str : Name of the parameter.
    @param paramValue int|float|str : Value of the parameter.
    @param type_ str : Type of the parameter.
    """
    if type_ == float :
      p = self.paramfValues.get(paramName)
      if p != None:
        self.paramfValues[paramName] = paramValue
        self.shaderUniforms.SetUniformf(paramName, paramValue)

    elif type_ == int :
      p = self.paramiValues.get(paramName)
      if p != None:
        self.paramiValues[paramName] = paramValue
        self.shaderUniforms.SetUniformi(paramName, int(paramValue))
    
    elif type_ == "markup":
      p = self.param4fValues.get(paramName)
      if p != None:
        self.param4fValues[paramName] = paramValue
        self.shaderUniforms.SetUniform4f(paramName, paramValue)

    elif type_ == "bool":
      p = self.parambValues.get(paramName)
      if p != None:
        self.param4fValues[paramName] = paramValue
        self.shaderUniforms.SetUniformi(paramName, int(paramValue))
    elif type_ == "range" :
      p = self.paramrValues.get(paramName)
      if p != None:
        self.paramrValues[paramName] = paramValue
        self.shaderUniforms.SetUniformi(paramName+ "Min", int(paramValue[0]))
        self.shaderUniforms.SetUniformi(paramName+ "Max", int(paramValue[1]))

  def getShaderParameter(self, paramName, type_):
    """!@brief Function to get the parameters of the shader.
    @return paramValue int|float|str : Value of the parameter.
    """
    if type_ == float :
      return self.paramfValues.get(paramName)
    if type_ == int :
      return self.paramiValues.get(paramName)

  def clear(self):
    """!@brief Function to clear the shader.
    """
    self.shaderUniforms.RemoveAllUniforms()
    self.shaderProperty.ClearAllFragmentShaderReplacements()