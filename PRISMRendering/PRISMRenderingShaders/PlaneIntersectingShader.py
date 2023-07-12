from PRISMRenderingShaders.CustomShader import CustomShader
from PRISMRenderingParams import *

"""PlaneIntersectingShader Class containing the code for the Plane intersecting shader.

:param CustomShader:  Parent class containing the function to access the parameters of the shader. 
:type CustomShader: class.
""" 

class PlaneIntersectingShader(CustomShader):

  relativePositionParam = FloatParam("relativePosition", "Relative Position", 1.0, 0.0, 1.0)

  entryParam = FourFParam("entry", "Entry", {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0})

  targetParam = FourFParam("target", "Target", {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0})

  planeParam = BoolParam("plane", "Third Plane", 0, [])

  param_list = [relativePositionParam, entryParam, targetParam, planeParam]

  def __init__(self, shaderPropertyNode, volumeNode = None, paramlist = param_list):
    CustomShader.__init__(self,shaderPropertyNode, volumeNode)
    self.param_list = paramlist
    self.createMarkupsNodeIfNecessary()
  
  @classmethod
  def GetBasicDescription(cls):
    """Function to get a basic description of the current shader.
    
    :return: Description of the current shader.
    :rtype: str
    """
    return 'Allows to visualize the anatomy along the approach plane for surgery'

  @classmethod
  def GetDisplayName(cls):
    return 'Plane intersecting'

  def setupShader(self):
    super(PlaneIntersectingShader,self).setupShader()
    replacement = """
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      vec3 dirVect = normalize(entry.xyz - target.xyz);

      bool skipAlongAxis = dot(texCoordRAS.xyz - entry.xyz, dirVect) + length(entry.xyz - target.xyz) * relativePosition > 0;

      vec3 vPlaneN = cross(vec3(0.0,0.0,1.0), dirVect);
      float dirCoord = dot(texCoordRAS.xyz - entry.xyz, vPlaneN);
      float dirCam = dot(in_cameraPos - entry.xyz, vPlaneN);
      bool skipVertical = dirCoord * dirCam > 0.0;
      
      vec3 hPlaneN = cross(vPlaneN, dirVect);
      dirCoord = dot(texCoordRAS.xyz - entry.xyz, hPlaneN);
      dirCam = dot(in_cameraPos - entry.xyz, hPlaneN);
      bool skipHorizontal = dirCoord * dirCam > 0.0;

      if (plane == 1)
        g_skip = skipAlongAxis && skipVertical && skipHorizontal;
      else 
        g_skip = skipAlongAxis && skipVertical;

    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)
    #shaderreplacement
