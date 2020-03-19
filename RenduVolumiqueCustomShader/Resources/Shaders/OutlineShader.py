from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Outline shader
#------------------------------------------------------------------------------------
class OutlineShader(CustomShader):

  shaderParams = {  'step_min' : { 'displayName' : 'Step min', 'min' : 0.0, 'max' : 0.01, 'defaultValue' : 0.001 }, \
                    'step_max' : { 'displayName' : 'Step max', 'min' : 0.0, 'max' : 0.01, 'defaultValue' : 0.01 }, \
                   'radius' : { 'displayName' : 'Radius', 'min' : 0.0, 'max' : 100.0, 'defaultValue' : 50.0 }, \
                   'x' :  {'displayName' : 'X', 'min' : -100.0, 'max' : 100.0, 'defaultValue' : 0.0 }, \
                   'y' :  {'displayName' : 'Y', 'min' : -100.0, 'max' : 100.0, 'defaultValue' : 0.0 }, \
                   'z' :  {'displayName' : 'Z', 'min' : -100.0, 'max' : 100.0, 'defaultValue' : 0.0 }  
                    
                    }

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Outline'

  def setupShader(self):
    super(OutlineShader, self).setupShader()
    self.shaderUniforms.SetUniformf("step_min", self.paramValues['step_min'])
    self.shaderUniforms.SetUniformf("step_max", self.paramValues['step_max'])

    
    self.shaderProperty.ClearAllFragmentShaderReplacements()

    croppingDecCode = """
    vec4 ComputeGradient(in sampler3D volume, vec3 pos, float gradStep)
    {
      vec3 g1, g2, n;
      vec4 ret;
      float nLength;

      g1.x = texture3D(volume, pos + vec3(gradStep, 0.0, 0.0)).x;
      g1.y = texture3D(volume, pos + vec3(0.0, gradStep, 0.0)).x;
      g1.z = texture3D(volume, pos + vec3(0.0, 0.0, gradStep)).x;
      g2.x = texture3D(volume, pos - vec3(gradStep, 0.0, 0.0)).x;
      g2.y = texture3D(volume, pos - vec3(0.0, gradStep, 0.0)).x;
      g2.z = texture3D(volume, pos - vec3(0.0, 0.0, gradStep)).x;
      n = g2 - g1;
      
      nLength = length(n);
      if(nLength > 0.0)
          n = normalize(n);
      else
          n = vec3(0.0, 0.0, 0.0);
      
      ret.rgb = n;
      ret.a = nLength;
      return ret;
    }

    float sampleThreshold = 0.1;
    float gradStep = 0.005;
    vec2 step = vec2(step_min, step_max);
    
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

      g_srcColor = computeColor(scalar, inAlpha);
      if( inAlpha > sampleThreshold && virtualAlpha < .95 )
      {
        //finite difference gradient computed by sampling the volume
        vec4 n = ComputeGradient( in_volume[0], g_dataPos, gradStep );

        // g_dirStep = unit vector that defines the direction of the ray being integrated
        if( n.a > 0.0 )
        {
          float factor = n.a * ( 1.0 - abs(dot(n.rgb , normalize(g_dirStep ))));
          float alpha = smoothstep( step.x, step.y, factor);
          if(alpha > 0.0 )
          g_srcColor = vec4( 0.0, 0.0, 0.0, g_srcColor.a);
          else
            g_srcColor = vec4( 0.0, 0.0, 0.0, alpha);

        }
      }
      virtualAlpha += (1-virtualAlpha) * inAlpha;
      g_srcColor.rgb *= g_srcColor.a;
      g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;
    }"""
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)