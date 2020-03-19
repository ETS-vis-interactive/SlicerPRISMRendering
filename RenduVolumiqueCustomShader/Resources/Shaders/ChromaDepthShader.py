from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Chroma depth shader
#------------------------------------------------------------------------------------
class ChromaDepthShader(CustomShader):

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Chroma Depth Perception'

  def setupShader(self):
    super(ChromaDepthShader,self).setupShader()

    self.shaderProperty.ClearAllFragmentShaderReplacements()
    shadingImplCode = """
    float val; //debug
    float distCam, range, normalizedDistCam;
    vec4 sampleAlpha, sample;
    if (!g_skip)
    {
      val = 1.0;
      // Sample the volume at the current position
      vec4 sampleAlpha = texture3D(in_volume[0], g_dataPos);
      sampleAlpha.r = sampleAlpha.r * in_volume_scale[0].r + in_volume_bias[0].r;
      sampleAlpha = vec4(sampleAlpha.r);
      
      // Compute normalized distance of sample to camera
      //distCam = length(g_dataPos - in_cameraPos) ;

      //volumeDistanceRange is another built-in variable that contains the minimum and maximum distance between the camera and the volume.
      //float originalZ = gl_FragCoord.z;
      //range = volumeDistanceRange.y − volumeDistanceRange.x;
      //normalizedDistCam = (distCam − volumeDistanceRange.x) / range;

      // Use transfer function to determine color based on distance
      //sample = texture3D(in_volume[0], g_dataPos, gl_FragCoord.z);
      //sample.r = sample.r * in_volume_scale[0].r + in_volume_bias[0].r;
      //sample = vec4(sample.r);

      //Assign RGB based on distance and alpha based on volume content
      //sample.a = sampleAlpha.a;
      //g_srcColor = sample;
     
      g_srcColor = vec4(0.0);
      g_srcColor.a =  gl_FragCoord.z / gl_FragCoord.w;
      g_srcColor = computeColor(sampleAlpha, g_srcColor.a);
      g_srcColor.rgb *= g_srcColor.a;
      g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;
      /*
      g_fragColor = vec4(val,val,val,val); //debug
      */

    }"""
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)