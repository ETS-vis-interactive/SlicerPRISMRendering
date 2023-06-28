from PRISMRenderingShaders.CustomShader import CustomShader
from PRISMRenderingParams import *

"""OpacityPeelingShader Class containing the code for the Opacity Peeling shader.

:param CustomShader:  Parent class containing the function to access the parameters of the shader. 
:type CustomShader: class.
""" 


class OpacityPeelingShader(CustomShader):

  TLowParam = FloatParam("T_low", "Low Threshold", 0.3, 0.0, 1.0)
  THighParam = FloatParam("T_high", "High Threshold", 0.8, 0.01, 1.0)
  radiusParam = FloatParam("radius", "Sphere Radius", 75.0, 0.0, 150.0)

  wantedLayerParam = IntParam("wantedLayer", "Wanted Layer", 1, 1, 20)

  sphereParam = BoolParam("sphere", "Sphere Carving", 0, ['center', 'radius'])

  centerParam = FourFParam("center", "Center", {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0})

  param_list = [TLowParam, THighParam, radiusParam, wantedLayerParam, sphereParam, centerParam]

  def __init__(self, shaderPropertyNode, volumeNode = None, paramlist = param_list):
    CustomShader.__init__(self, shaderPropertyNode)
    self.param_list = paramlist
  @classmethod
  def GetDisplayName(cls):
    return 'Opacity Peeling'
  
  @classmethod
  def GetBasicDescription(cls):
    """Function to get a basic description of the current shader.
    
    :return: Description of the current shader.
    :rtype: str
    """
    return 'Responds to the problem of occlusion of certain structures in the volume. Removes the first n layers of tissue during the integration of the ray.'

  def setupShader(self):

    super(OpacityPeelingShader, self).setupShader()
    self.setAllUniforms()
    self.shaderProperty.ClearAllFragmentShaderReplacements()

    croppingDecCode = """
    int currentLayer = 0;
    float layerAlpha = 0.0;"""

    shadingImplCode = """
    if (!g_skip)
    {
      // Get alpha for current pos according to transfer function
      vec4 scalar = texture3D(in_volume[0], g_dataPos);
      scalar.r = scalar.r * in_volume_scale[0].r + in_volume_bias[0].r;
      scalar = vec4(scalar.r);
      g_srcColor = vec4(0.0);
      g_srcColor.a = computeOpacity(scalar);
      
      // Determine if the current position is within the spherical ROI
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      bool isInROI = length(texCoordRAS.xyz - center.xyz) < radius;
      
      if((sphere == 1 && isInROI || sphere == 0) && currentLayer < wantedLayer)
      {
        layerAlpha = layerAlpha + ( 1.0 - layerAlpha ) * g_srcColor.a;
        if( layerAlpha > T_high && g_srcColor.a < T_low )
        {
          currentLayer = currentLayer + 1;
          layerAlpha = 0.0;
        }
      }

      else if (g_srcColor.a > 0.0)
      {
        g_srcColor = computeColor(scalar, g_srcColor.a);
        g_srcColor.rgb *= g_srcColor.a;
        g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;
      }
    }"""

    self.shaderProperty.ClearAllFragmentShaderReplacements()
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Dec", True, croppingDecCode, False)
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)
    
    #shaderreplacement

