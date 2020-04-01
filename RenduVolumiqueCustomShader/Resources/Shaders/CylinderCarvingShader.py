from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Cylinder carving shader
#------------------------------------------------------------------------------------
class CylinderCarvingShader(CustomShader):
  shaderfParams = { 'radius' : { 'displayName' : 'Radius', 'min' : 0.0, 'max' : 100.0, 'defaultValue' : 50.0 }}
  shaderiParams = {}
  shader4fParams = { 'endPoint' : { 'displayName' : 'endPoint', 'defaultValue' : {'x' : 0.0, 'y' : 0.0, 'z' : 0.0, "w" : 0.0 }}}

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Cylinder Carving'

  def setupShader(self):
    super(CylinderCarvingShader,self).setupShader()
    self.shaderUniforms.SetUniform3f("cylinderPoint1", [0.0,0.0,0.0])
    self.shaderUniforms.SetUniform3f("cylinderPoint2", [0.0,0.0,100.0])
    self.shaderUniforms.SetUniformf("radius", self.paramfValues['radius'])

    cropDecReplacement = """
      //-----------------------------------------------------
      // Compute intersection between a ray and a cylinder
      // The ray is defined by a starting point (@p start)
      // and a direction (@p dir unit vector). The cylinder
      // is defined by its central axis (the line passing
      // through points @p A and @p B) and radius (@p r)
      // The function returns true if an intersection exists
      // and returns the distance from start to first
      // intersection (@p distIn) and second
      // intersection (@p distOut).
      //-----------------------------------------------------
      bool IntersectionCylinder( vec3 start, vec3 dir, vec3 A, vec3 B, float r, out vec3 inPoint, out vec3 outPoint )
      {
        vec3 AB = B - A;
        vec3 AO = start - A;
        vec3 AOxAB = cross(AO,AB);
        vec3 VxAB  = cross(dir,AB);
        float ab2 = dot(AB,AB);
        float a = dot(VxAB,VxAB);
        float b = 2 * dot(VxAB,AOxAB);
        float c = dot(AOxAB,AOxAB) - (r*r * ab2);
        float d = b * b - 4 * a * c;
        if (d < 0)
          return false;
        float t0 = (-b - sqrt(d)) / (2 * a);
        float t1 = (-b + sqrt(d)) / (2 * a);
        inPoint = start + min(t0,t1) * dir;
        outPoint = start + max(t0,t1) * dir;
        return true;
      }
      
      // Distances (texture space) at which the
      // ray intersects with a cutout cylinder.
      float cylinderStepIn = -1.0;
      float cylinderStepOut = -1.0;
      bool hasCylIntersect = false;
      """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Dec", True, cropDecReplacement, False)

    cropInitReplacement = """
      // Transform cylinder points to volume 0  space (same as rayDir)
      vec3 cylPt1 = (in_inverseVolumeMatrix[0] * vec4( cylinderPoint1, 1.0 )).xyz;
      vec3 cylPt2 = (in_inverseVolumeMatrix[0] * vec4( cylinderPoint2, 1.0 )).xyz;

      // Compute distance of intersections with cylinder
      vec3 inPointObj = vec3( 0.0, 0.0 ,0.0 );
      vec3 outPointObj = vec3( 0.0, 0.0 ,0.0 );
      hasCylIntersect = IntersectionCylinder( g_eyePosObj.xyz, rayDir, cylPt1, cylPt2, radius, inPointObj, outPointObj );

      // Compute offset vector g_eyePosObj -> intersection
      if( hasCylIntersect )
      {
        vec3 inPointTex = (ip_inverseTextureDataAdjusted * vec4(inPointObj,0.0)).xyz;
        cylinderStepIn = length( inPointTex - g_dataPos.xyz ) / length(g_dirStep);
        vec3 outPointTex = (ip_inverseTextureDataAdjusted * vec4(outPointObj,0.0)).xyz;
        cylinderStepOut = length( outPointTex - g_dataPos.xyz ) / length(g_dirStep);
      }
    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Init", True, cropInitReplacement, False)

    cropImplReplacement = """
      //g_skip = cylinderStepIn > 0.0 && g_currentT < cylinderStepIn;
      //g_skip = g_currentT > cylinderStepIn && g_currentT < cylinderStepOut;
      g_skip = cylinderStepOut < g_terminatePointMax;
      //g_skip = cylinderStepIn > 0.0;
    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, cropImplReplacement, False)

  def setPathEnds(self,entry,target):
    self.shaderUniforms.SetUniform3f("cylinderPoint1", target)
    self.shaderUniforms.SetUniform3f("cylinderPoint2", entry)