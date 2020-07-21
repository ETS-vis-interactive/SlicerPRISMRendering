from PRISMRenderingShaders.CustomShader import CustomShader

"""OutlineShader Class containing the code for the Outline shader.

:param CustomShader:  Parent class containing the function to access the parameters of the shader. 
:type CustomShader: class.
""" 
class OutlineShader(CustomShader):
  shaderfParams = { 'gradStep' : { 'displayName' : 'Gradient Step', 'min' : 0.0, 'max' : 0.02, 'defaultValue' : 0.005 }}
  shaderrParams = { 'step' : { 'displayName' : 'Step', 'defaultValue' : [0.000, 1000]}}  

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Outline'

  def setupShader(self):
    super(OutlineShader,self).setupShader()

    self.shaderProperty.ClearAllFragmentShaderReplacements()

    croppingDecCode = """
    vec4 ComputeGradient(in sampler3D volume, vec3 pos, float gradStep)
    {
      vec3 g1;
      g1.x = texture3D(volume, pos + vec3(gradStep,0.0,0.0) ).x;
      g1.y = texture3D(volume, pos +  vec3(0.0, gradStep, 0.0)).x;
      g1.z = texture3D(volume, pos +  vec3(0.0,0.0, gradStep)).x;
      vec3 g2;
      g2.x = texture3D(volume, pos -  vec3(gradStep,0.0,0.0)).x;
      g2.y = texture3D(volume, pos -  vec3(0.0, gradStep, 0.0)).x;
      g2.z = texture3D(volume, pos -  vec3(0.0,0.0,gradStep)).x;
      vec3 n = g2 - g1;
      float nLength = length(n);
      if(nLength > 0.0)
          n = normalize(n);
      else
          n = vec3(0.0, 0.0, 0.0);
      vec4 ret;
      ret.rgb = n;
      ret.a = nLength;
      return ret;
    }

    float sampleThreshold = 0.1;
    vec2 step = vec2(stepMin, stepMax);
    float virtualAlpha = 0.0;
    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Dec", True, croppingDecCode, False)

    shadingImplCode = """
    if (!g_skip)
    {
      vec4 scalar = texture3D(in_volume[0], g_dataPos);
      scalar.r = scalar.r * in_volume_scale[0].r + in_volume_bias[0].r;
      scalar = vec4(scalar.r);
      g_srcColor = vec4(0.0);
      float inAlpha = computeOpacity(scalar);
      if(inAlpha > sampleThreshold && virtualAlpha < .95)
      {
        vec4 n = ComputeGradient(in_volume[0], g_dataPos, gradStep);
        if(n.a > 0.0)
        {
          float factor = n.a * (1.0 - abs(dot(normalize(g_dirStep), n.rgb)));
          float alpha = smoothstep(step.x, step.y , factor);
          g_srcColor = vec4(1.0, 1.0, 1.0, alpha);
        }
      }
      virtualAlpha += (1-virtualAlpha) * inAlpha;
      g_srcColor.rgb *= g_srcColor.a;
      g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;
    }"""
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)

