from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Carve opacity peeling shader
#------------------------------------------------------------------------------------
class CarveOpacityPeelingShader(CustomShader):

  shaderParams = { 'radius' : { 'displayName' : 'Radius', 'min' : 0.0, 'max' : 100.0, 'defaultValue' : 50.0 }, \
                   'T_low' : { 'displayName' : 'Low Threshold', 'min' : 0.0, 'max' : 1.0, 'defaultValue' : 0.3 }, \
                   'T_high' : { 'displayName' : 'High Threshold', 'min' : 0.01, 'max' : 1.0, 'defaultValue' : 0.8 }}

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Carve Opacity Peeling'

  def setupShader(self):
    super(CarveOpacityPeelingShader,self).setupShader()
    self.setAllUniforms()
    self.shaderUniforms.SetUniform3f("center", [0.0,0.0,0.0])
    self.shaderUniforms.SetUniformi("wantedLayer",2)
    self.shaderProperty.ClearAllFragmentShaderReplacements()

    croppingDecCode = """
    int currentLayer = 0;
    float layerAlpha = 0.0;"""
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Dec", True, croppingDecCode, False)

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
      bool isInROI = length(texCoordRAS.xyz - center) < radius;

      if( isInROI && currentLayer < wantedLayer )
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
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)

  def setPathEnds(self,entry,target):
    self.shaderUniforms.SetUniform3f("center", entry)