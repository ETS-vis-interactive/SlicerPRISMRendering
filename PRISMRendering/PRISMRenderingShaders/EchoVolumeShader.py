from PRISMRenderingShaders.CustomShader import CustomShader
from PRISMRenderingParams import *
import vtk, qt, ctk, slicer

class EchoVolumeShader(CustomShader):

  threshold = FloatParam('threshold', 'Threshold', 20.0, 0.0, 100.0)
  edgeSmoothing = FloatParam('edgeSmoothing', 'Edge Smoothing', 5.0, 0.0, 10.0)
  depthRange = RangeParam('depthRange', 'Depth Range', [-120.0, 10.0])
  depthDarkening = IntParam('depthDarkening', 'Depth Darkening', 30, 0, 100)
  depthColoringRange = RangeParam('depthColoringRange', 'Depth Coloring Range', [-24, 23])
  brightnessScale = FloatParam('brightnessScale', 'Brightness Scale', 120.0, 0.0, 200.0)
  saturationScale = FloatParam('saturationScale', 'Saturation Scale', 120.0, 0.0, 200.0)

  param_list = [threshold, edgeSmoothing, depthRange, depthDarkening, depthColoringRange, brightnessScale, saturationScale]

  def __init__(self, shaderPropertyNode, volumeNode = None, paramlist = param_list):
    CustomShader.__init__(self, shaderPropertyNode, volumeNode)
    self.param_list = paramlist
    self.createMarkupsNodeIfNecessary()
  @classmethod

  def GetDisplayName(cls):
    return 'Echo Volume Renderer'
  
  @classmethod
  def GetBasicDescription(cls):
    """Function to get a basic description of the current shader.
    
    :return: Description of the current shader.
    :rtype: str
    """
    return 'Use custom shaders for depth-dependent coloring for volume rendering of 3D/4D ultrasound images.'

  def setupShader(self):

    super(EchoVolumeShader, self).setupShader()
    self.setAllUniforms()
    self.shaderProperty.ClearAllFragmentShaderReplacements()

    ComputeColorReplacementCommon = """

vec3 rgb2hsv(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

uniform sampler2D in_colorTransferFunc_0[1];

vec4 computeColor(vec4 scalar, float opacity)
{
    // Get base color from color transfer function (defines darkening of transparent voxels and neutral color)

    vec3 baseColorRgb = texture2D(in_colorTransferFunc_0[0], vec2(scalar.w, 0.0)).xyz;
    vec3 baseColorHsv = rgb2hsv(baseColorRgb);

    // Modulate hue and brightness depending on distance

    float hueFar = clamp(baseColorHsv.x-depthColoringRangeMin*0.01, 0.0, 1.0);
    float hueNear = clamp(baseColorHsv.x-depthColoringRangeMax*0.01, 0.0, 1.0);
    float sat = clamp(saturationScale*0.01*baseColorHsv.y,0.0,1.0);
    float brightnessNear = brightnessScale*0.01*baseColorHsv.z;
    float brightnessFar = clamp(brightnessScale*0.01*(baseColorHsv.z-depthDarkening*0.01), 0.0, 1.0);

    // Determine the ratio (dist) that serves to interpolate between the near
    // color and the far color. depthRange specifies the depth range, in voxel
    // coordinates, between the front color and back color.
    vec3 camInTexCoord = (ip_inverseTextureDataAdjusted * vec4(g_eyePosObj.xyz,1.0) ).xyz;
    float depthRangeInTexCoordStart = (ip_inverseTextureDataAdjusted * vec4(0,0,depthRangeMin,1.0) ).z;
    float depthRangeInTexCoordEnd = (ip_inverseTextureDataAdjusted * vec4(0,0,depthRangeMax,1.0) ).z;
    vec3 dp = g_dataPos - camInTexCoord;
    vec3 dv = vec3(0.5,0.5,0.5) - camInTexCoord;
    float lv = length(dv);
    float lp = dot(dp, dv) / lv;
    float dist = (lp - lv - depthRangeInTexCoordStart) / ( depthRangeInTexCoordEnd - depthRangeInTexCoordStart);
    dist = clamp( dist, 0.0, 1.0 );

    vec3 rgbNear = hsv2rgb(vec3( hueNear, sat, brightnessNear));
    vec3 rgbFar = hsv2rgb(vec3( hueFar, sat, brightnessFar));
    vec3 rgbDepthModulated = mix( rgbNear, rgbFar, dist );

    vec4 color = vec4(rgbDepthModulated, opacity);
"""

    ComputeColorReplacementVTK8 = ComputeColorReplacementCommon + """
    return computeLighting(color, 0);
}
"""

    ComputeColorReplacementVTK9 = ComputeColorReplacementCommon + """
    return computeLighting(color, 0, 0.0);
}
"""
    sp = self.shaderPropertyNode.GetShaderProperty()
    sp.ClearAllShaderReplacements()
    computeColorReplacement = ComputeColorReplacementVTK9 if vtk.vtkVersion().GetVTKMajorVersion() >= 9 else ComputeColorReplacementVTK8
    sp.AddShaderReplacement(vtk.vtkShader.Fragment, "//VTK::ComputeColor::Dec", True, computeColorReplacement, True)

    #shaderreplacement

