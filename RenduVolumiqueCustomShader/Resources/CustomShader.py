import imp
import sys
import inspect
import os
import importlib.util

#------------------------------------------------------------------------------------
# Generic Custom Shader
#------------------------------------------------------------------------------------
class CustomShader():

  shaderfParams = {}
  shaderiParams = {}
  shader4fParams = {}
  shaderbParams = {}

  def __init__(self, shaderPropertyNode):
    assert shaderPropertyNode != None, 'CustomShader: a valid shader property node must provided to the constructor'
    self.shaderPropertyNode = shaderPropertyNode
    self.shaderProperty = shaderPropertyNode.GetShaderProperty()
    self.shaderUniforms = self.shaderPropertyNode.GetFragmentUniforms()
    self.paramfValues = {}
    for p in self.shaderfParams.keys():
      self.paramfValues[p] = self.shaderfParams[p]['defaultValue']
    self.paramiValues = {}
    for p in self.shaderiParams.keys():
      self.paramiValues[p] = self.shaderiParams[p]['defaultValue']
    self.param4fValues = {}
    for p in self.shader4fParams.keys():
      self.param4fValues[p] = self.shader4fParams[p]['defaultValue']   
    self.parambValues = {}   
    for p in self.shaderbParams.keys():
      self.parambValues[p] = self.shaderbParams[p]['defaultValue']   

  @classmethod
  def InstanciateCustomShader(cls, shaderDisplayName,shaderPropertyNode):
    if shaderDisplayName == cls.GetDisplayName():
      return CustomShader(shaderPropertyNode)

    for c in cls.allClasses:
      if c.GetDisplayName() == shaderDisplayName:
        return c(shaderPropertyNode)
    return None

  @classmethod
  def GetAllShaderClassNames(cls):
    
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
    return 'None'
  
  @classmethod
  def GetClassName(cls, shaderDisplayName):
    if shaderDisplayName == cls.GetDisplayName():
      return CustomShader

    for c in cls.allClasses:
      if c.GetDisplayName() == shaderDisplayName:
        return c
    return None

  @classmethod
  def hasShaderParameter(cls, name, type_):
    if type_ == float :
      return name in cls.shaderfParams
    elif type_ == int :
      return name in cls.shaderiParams

  def getParameterNames(self):
    return []

  def getShaderPropertyNode(self):
    return self.shaderPropertyNode

  def setupShader(self):
    self.clear()
    self.setAllUniforms()

  def setPathEnds(self,entry,target):
    pass

  def setAllUniforms(self):
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

  def setShaderParameter(self, paramName, paramValue, type_):
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

  def getShaderParameter(self, paramName, type_):
    if type_ == float :
      return self.paramfValues.get(paramName)
    if type_ == int :
      return self.paramiValues.get(paramName)

  def clear(self):
    self.shaderUniforms.RemoveAllUniforms()
    self.shaderProperty.ClearAllFragmentShaderReplacements()