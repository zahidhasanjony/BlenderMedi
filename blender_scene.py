import bpy, math, os, sys
from mathutils import Vector
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"
OUT.mkdir(exist_ok=True)
FPS=60
def frame(t): return round(t*FPS)+1
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.cycles.samples=int(os.getenv("SAMPLES","8"))
# The Ubuntu Blender package used in GitHub Actions may be built without OIDN.
# Explicitly disable BOTH final-render and view-layer denoising so Cycles
# works on headless CPU-only runners without OpenImageDenoiser.
sc.cycles.use_denoising=False
for layer in sc.view_layers:
 if hasattr(layer, "cycles") and hasattr(layer.cycles, "use_denoising"):
  layer.cycles.use_denoising=False
print("Cloud renderer: Cycles denoising disabled (OIDN not required)")
sc.render.resolution_x=1280
sc.render.resolution_y=720
sc.render.resolution_percentage=int(os.getenv("SCALE","60"))
sc.render.fps=FPS
sc.frame_start=1
sc.frame_end=600
sc.render.image_settings.file_format="PNG"
sc.render.filepath=str(OUT/"f_")
sc.world.color=(.016,.022,.035)
sc.camera=None

groups={}
for name in ("bedroom","cabinet","swallow","anatomy"):
 c=bpy.data.collections.new(name);sc.collection.children.link(c);groups[name]=c
def togroup(o,g):
 for c in list(o.users_collection):c.objects.unlink(o)
 groups[g].objects.link(o)
 return o
def mat(name,rgb,metal=0,rough=.45,alpha=1,glow=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,alpha);m.use_nodes=True
 p=m.node_tree.nodes.get("Principled BSDF")
 p.inputs["Base Color"].default_value=(*rgb,1)
 p.inputs["Metallic"].default_value=metal;p.inputs["Roughness"].default_value=rough
 p.inputs["Alpha"].default_value=alpha
 if glow and "Emission Color" in p.inputs:
  p.inputs["Emission Color"].default_value=(*rgb,1)
  p.inputs["Emission Strength"].default_value=glow
 if alpha<1:
  try:m.surface_render_method="DITHERED"
  except:pass
 return m
skin=mat("warm skin",(.49,.225,.128));skinlight=mat("nose",(.64,.32,.19))
hair=mat("near black hair",(.012,.015,.024));eye=mat("eye whites",(.78,.81,.78))
shirt=mat("charcoal navy shirt",(.065,.11,.17))
pants=mat("dark pants",(.033,.047,.067))
red=mat("alarm emission",(.92,.044,.035),glow=1.6)
blue=mat("midnight blue",(.025,.055,.098))
cloth=mat("pillows",(.52,.61,.69))
cab=mat("cabinet",(.055,.083,.10))
cream=mat("bottle",(.77,.78,.69),rough=.26)
label=mat("paper label",(.89,.82,.61))
tabletmat=mat("pale medicine",(.94,.91,.81))
organ=mat("stomach tissue",(.70,.16,.22),rough=.38)
translucent=mat("skin anatomical cutaway",(.12,.36,.48),alpha=.25,rough=.24)
acid=mat("gold stomach fluid",(.94,.34,.035),glow=.45)

def sphere(n,loc,scale,m,g):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=loc)
 o=togroup(bpy.context.object,g);o.name=n;o.scale=scale;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o
def cube(n,loc,scale,m,g):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 o=togroup(bpy.context.object,g);o.name=n;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(m);return o
def cyl(n,loc,r,d,m,g):
 bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=r,depth=d,location=loc)
 o=togroup(bpy.context.object,g);o.name=n;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o
def txt(n,t,loc,size,m,g):
 cu=bpy.data.curves.new(n,"FONT");cu.body=t;cu.size=size;cu.align_x="CENTER";cu.extrude=.002
 o=bpy.data.objects.new(n,cu);groups[g].objects.link(o)
 o.location=loc;o.rotation_euler=(math.pi/2,0,0);o.data.materials.append(m);return o
def tube(n,pts,r,m,g):
 cv=bpy.data.curves.new(n,"CURVE");cv.dimensions="3D";cv.bevel_depth=r;cv.bevel_resolution=3
 s=cv.splines.new("BEZIER");s.bezier_points.add(len(pts)-1)
 for p,co in zip(s.bezier_points,pts):
  p.co=co;p.handle_left_type="AUTO";p.handle_right_type="AUTO"
 o=bpy.data.objects.new(n,cv);groups[g].objects.link(o);o.data.materials.append(m)
 return o
def person(g,cut=False):
 s=translucent if cut else shirt
 sphere("torso", (0,0,1.11),(.49,.29,.66),s,g)
 sphere("head",(0,-.03,1.91),(.33,.285,.385),skin,g)
 sphere("neck",(0,-.035,1.58),(.115,.12,.24),skin,g)
 sphere("nose",(0,-.298,1.85),(.045,.067,.065),skinlight,g)
 sphere("hair",(0,.015,2.20),(.345,.28,.17),hair,g)
 for i in range(6):
  x=.25*math.sin(i*2.0)
  sphere("wavy fringe",(x,-.21,2.194+.03*math.cos(i)),(.097,.085,.072),hair,g)
 for sign in (-1,1):
  sphere("eye",(sign*.145,-.296,1.97),(.070,.032,.045),eye,g)
  sphere("iris",(sign*.145,-.324,1.97),(.032,.018,.035),hair,g)
  sphere("eyebrow",(sign*.145,-.307,2.064),(.105,.02,.024),hair,g)
  sphere("ear",(sign*.33,-.02,1.86),(.055,.055,.11),skin,g)
  sphere("arm",(sign*.52,-.02,1.16),(.16,.18,.48),translucent if cut else shirt,g)
  sphere("leg",(sign*.19,.025,.40),(.19,.22,.47),pants,g)
  sphere("shoe",(sign*.19,-.16,.085),(.20,.28,.10),hair,g)
 sphere("mouth",(0,-.286,1.72),(.08,.015,.010),hair,g)

# Scene 1, rapid camera cuts in the first second
cube("bedroom back wall",(0,2,1.5),(9,.12,4),blue,"bedroom")
cube("floor",(0,.8,-.12),(9,6,.22),cab,"bedroom")
cube("bed frame",(-2.5,.75,.44),(2.9,2.0,.66),blue,"bedroom")
cube("pillow",(-2.55,.32,.83),(.9,.68,.18),cloth,"bedroom")
cube("side table",(2.15,.2,.74),(.9,.7,1.0),cab,"bedroom")
cube("alarm clock",(2.15,-.22,1.40),(.87,.22,.41),hair,"bedroom")
txt("2AM clock","02:00",(2.15,-.347,1.34),.27,red,"bedroom")
person("bedroom")
for i in range(3):
 ring=sphere("headache pulse",(.34+.13*i,-.08,1.98),(.025,.055,.06),red,"bedroom")
 ring.hide_render=True
 ring.keyframe_insert(data_path="hide_render",frame=1)
 ring.hide_render=False
 ring.keyframe_insert(data_path="hide_render",frame=frame(1.5+.18*i))
 ring.hide_render=True
 ring.keyframe_insert(data_path="hide_render",frame=frame(2.85))
# Scene 2 medicine cabinet
cube("cabinet rear",(0,1.3,1.55),(5,.11,3.4),cab,"cabinet")
for z in (.4,1.65,2.78): cube("glass shelf",(0,.85,z),(4.6,1.6,.085),blue,"cabinet")
for x in (-1.65,-1.13,1.17,1.73):
 cyl("background medicine",(x,.75,1.05),.19,.75,cloth,"cabinet")
 cyl("cap",(x,.75,1.46),.22,.11,cab,"cabinet")
cyl("expired bottle",(0,-.30,1.12),.45,1.23,cream,"cabinet")
cyl("label band",(0,-.30,1.12),.459,.57,label,"cabinet")
cyl("bottle cap",(0,-.30,1.80),.49,.21,blue,"cabinet")
txt("expiry date","EXP 2023",(0,-.766,1.18),.15,red,"cabinet")
txt("3 years expired","3 YEARS EXPIRED",(0,-.769,.99),.092,hair,"cabinet")
for j in range(4):
 p=sphere("reaching fingertips",(.81+.12*j,-1.0,1.01),(.065,.135,.077),skin,"cabinet")
 for t,x in [(3.1,.81+.12*j),(5.4,.50+.11*j),(6.6,.76+.12*j)]:
  p.location.x=x;p.keyframe_insert(data_path="location",frame=frame(t))
# Scene 3 medicine swallowed
person("swallow")
pill=sphere("single white pill",(.49,-.48,1.47),(.067,.06,.105),tabletmat,"swallow")
hand=sphere("same man's hand",(.49,-.34,1.40),(.13,.14,.15),skin,"swallow")
for t,x,z in [(6.6,.49,1.4),(7.18,.37,1.54),(7.68,.21,1.69),(8.2,.19,1.70)]:
 hand.location=(x,-.34,z);hand.keyframe_insert(data_path="location",frame=frame(t))
 pill.location=(x,-.48,z+.08);pill.keyframe_insert(data_path="location",frame=frame(t))
# Scene 4 anatomically integrated left-upper-abdomen stomach
person("anatomy",cut=True)
sphere("anatomical stomach body left of patient",(.25,-.05,1.12),(.245,.19,.31),organ,"anatomy")
sphere("stomach fundus",(.32,-.05,1.31),(.20,.17,.15),organ,"anatomy")
sphere("pylorus",(.06,-.04,.93),(.13,.15,.13),organ,"anatomy")
cyl("esophagus midline",(.025,-.05,1.56),.065,.72,organ,"anatomy")
for z in (1.34,1.49,1.62):
 for side in (-1,1):
  pts=[]
  for i in range(12):
   th=i/11*2.2
   pts.append((side*(.06+.42*math.sin(th)),-.28-.03*math.sin(th),z-.11*th))
  tube("rib",pts,.009,cloth,"anatomy")
sphere("acid pool",(.25,-.22,.99),(.18,.024,.06),acid,"anatomy")
travel=sphere("tablet descending esophagus",(.025,-.22,1.75),(.055,.05,.088),tabletmat,"anatomy")
for t,k in [(8.2,0),(8.6,.18),(9.0,.39),(9.5,.70),(10,1)]:
 travel.location=(.025+.21*k,-.22,1.75-.58*k)
 travel.keyframe_insert(data_path="location",frame=frame(t))
# Animate a continuous camera through marked cuts.
def camera(name,at,look,fov):
 cu=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,cu);sc.collection.objects.link(ob)
 ob.location=at;ob.rotation_euler=(Vector(look)-ob.location).to_track_quat("-Z","Y").to_euler()
 cu.angle=math.radians(fov);return ob
shots=[
 (0,"Clock macro",(2.15,-3.4,1.48),(2.15,0,1.40),23),
 (.20,"Face close-up",(0,-2.35,2.03),(0,0,1.95),35),
 (.48,"Headache close-up",(.05,-2.47,2.02),(0,0,1.96),35),
 (.78,"Bedroom reveal",(1.4,-5.7,2.6),(0,0,1.44),46),
 (1.50,"Pulsing headache",(0,-2.50,2.01),(0,0,1.92),34),
 (3.10,"Cabinet reveal",(.23,-4.6,1.83),(0,0,1.3),40),
 (4.53,"Expired date close-up",(0,-2.53,1.45),(0,0,1.18),30),
 (6.60,"Swallow close-up",(.2,-3.0,1.95),(0,0,1.69),39),
 (8.20,"Torso-integrated cutaway",(.09,-2.70,1.45),(.15,0,1.26),37)]
for t,n,at,look,fov in shots:
 c=camera(n,at,look,fov)
 marker=sc.timeline_markers.new(n,frame=frame(t));marker.camera=c
sc.camera=bpy.data.objects["Clock macro"]
# Lights
def light(name,loc,power,col,size):
 cu=bpy.data.lights.new(name,"AREA");cu.energy=power;cu.color=col;cu.shape="DISK";cu.size=size
 o=bpy.data.objects.new(name,cu);sc.collection.objects.link(o);o.location=loc
 o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat("-Z","Y").to_euler()
light("soft cinematic cool key",(-3,-4,5),650,(.49,.69,1),5)
light("red night rim",(3,0,4),380,(1,.21,.13),3)
light("skin fill",(0,-5,3),300,(1,.73,.53),4)
# Timeline-based collection visibility
windows={"bedroom":(1,frame(3.1)),"cabinet":(frame(3.1),frame(6.6)),
         "swallow":(frame(6.6),frame(8.2)),"anatomy":(frame(8.2),601)}
for g,(start,stop) in windows.items():
 for obj in groups[g].objects:
  for fr,hidden in ((1,start!=1),(start,False),(stop,True)):
   obj.hide_render=hidden
   obj.keyframe_insert(data_path="hide_render",frame=fr)
  if obj.animation_data and obj.animation_data.action:
   for fc in obj.animation_data.action.fcurves:
    if fc.data_path=="hide_render":
     for k in fc.keyframe_points:k.interpolation="CONSTANT"
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"expired_medicine.blend"))
print("BLENDER_SCENE_READY")
if "--render" in sys.argv:
 bpy.ops.render.render(animation=True)
