from PRISMRenderingShaders.CustomShader import CustomShader
from PRISMRenderingParams import *

"""SphereCarvingShader Class containing the code for the Sphere Carving shader.

:param CustomShader:  Parent class containing the function to access the parameters of the shader. 
:type CustomShader: class.
""" 

class SphereCarvingShader(CustomShader):

  radiusParam = FloatParam("radius", "Radius", 50.0, 0.0, 100.0)
  centerParam = FourFParam("center", "Center", {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0})

  param_list = [radiusParam, centerParam]
  
  def __init__(self, shaderPropertyNode, volumeNode = None, paramlist = param_list):
    CustomShader.__init__(self,shaderPropertyNode, volumeNode)
    self.param_list = paramlist
  
  @classmethod
  def GetBasicDescription(cls):
    """Function to get a basic description of the current shader.
    
    :return: Description of the current shader.
    :rtype: str
    """
    return 'Makes it possible to cut out spherical parts of the volume interactively, which can obstruct structures of interest with similar intensities.'

  @classmethod
  def GetDisplayName(cls):
    return 'Sphere Carving'

  def setupShader(self):
    super(SphereCarvingShader,self).setupShader()

    replacement = """
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      g_skip = length(texCoordRAS.xyz - center.xyz) < radius;
    """
    # (bool) Skip computation of current iteration step if true
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)
    #shaderreplacement
