from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Plane intersecting shader
#------------------------------------------------------------------------------------
class PlaneIntersectingShader(CustomShader):

  shaderfParams = { 'relativePosition' : { 'displayName' : 'Relative Position', 'min' : 0.0, 'max' : 1.0, 'defaultValue' : 0.5 }}
  shader4fParams = {'entry': {'displayName': 'Entry', 'defaultValue': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0}}, \
                    'target': {'displayName': 'Target', 'defaultValue': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0}}}
  shaderbParams = { 'plane' : { 'displayName' : 'Third Plane', 'defaultValue' : 0}}

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

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
