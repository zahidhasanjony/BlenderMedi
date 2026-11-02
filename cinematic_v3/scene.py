"""BlenderMedi 5-second cinematic benchmark, 1920x1080, 30fps.
Uses CC0 MakeHuman-based geometry for the character and original Blender meshes
for physical room, medicine packaging and moving cameras.
Run with: blender -b -noaudio --python cinematic_v3/scene.py -- --render
"""
import bpy
import math
import os
import sys
import random
from pathlib import Path
from mathutils import Vector

random.seed(19)
ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/"downloaded"
OUTPUT=ROOT/"output"
OUTPUT.mkdir(parents=True,exist_ok=True)
FPS=30
TOTAL=150
def f(t):
    return min(TOTAL,max(1,1+round(t*FPS)))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=int(os.getenv('SAMPLES','12'))
scene.cycles.use_denoising=False
for vl in scene.view_layers:
    if hasattr(vl,'cycles') and hasattr(vl.cycles,'use_denoising'):
        vl.cycles.use_denoising=False
scene.render.resolution_x=1920
scene.render.resolution_y=1080
scene.render.resolution_percentage=int(os.getenv('SCALE','100'))
scene.render.fps=FPS
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUTPUT/'frame_')
scene.render.film_transparent=False
scene.frame_start=1
scene.frame_end=TOTAL
scene.render.use_file_extension=True
scene.world.use_nodes=True
worldbg=scene.world.node_tree.nodes.get('Background')
worldbg.inputs['Color'].default_value=(.012,.019,.038,1)
worldbg.inputs['Strength'].default_value=.22
try:
    scene.view_settings.view_transform='AgX'
except Exception:
    pass

def mat(name,color,rough=.5,metal=0,alpha=1,emission=0,trans=0,sss=0,bump=0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True;m.diffuse_color=(*color,1)
    n=m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value=(*color,1)
    n.inputs['Roughness'].default_value=rough
    n.inputs['Metallic'].default_value=metal
    if 'Alpha' in n.inputs:n.inputs['Alpha'].default_value=alpha
    if 'Transmission Weight' in n.inputs:n.inputs['Transmission Weight'].default_value=trans
    if 'Subsurface Weight' in n.inputs:n.inputs['Subsurface Weight'].default_value=sss
    if 'Emission Color' in n.inputs and emission:
        n.inputs['Emission Color'].default_value=(*color,1)
        n.inputs['Emission Strength'].default_value=emission
    if bump:
        tex=m.node_tree.nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value=120
        bm=m.node_tree.nodes.new('ShaderNodeBump')
        bm.inputs['Strength'].default_value=.13
        bm.inputs['Distance'].default_value=bump
        m.node_tree.links.new(tex.outputs['Fac'],bm.inputs['Height'])
        m.node_tree.links.new(bm.outputs['Normal'],n.inputs['Normal'])
    return m
navy=mat('Bedroom navy panel',(.045,.075,.130),.87,bump=.008)
navyFabric=mat('Quilt | royal slate',(.075,.14,.22),.86,bump=.010)
linen=mat('Cotton linen',(.65,.69,.70),.79,bump=.009)
wood=mat('Dark walnut',(.23,.108,.051),.44,bump=.017)
oat=mat('Warm oak',(.48,.28,.146),.52,bump=.014)
charcoal=mat('Enamel black',(.017,.021,.029),.28)
brass=mat('Brushed antique brass',(.46,.29,.13),.27,metal=.75,bump=.002)
redLed=mat('Red LED numerals',(.97,.038,.023),.28,emission=5.5)
amber=mat('Translucent amber medicine bottle',(.52,.16,.045),.12,alpha=.95,trans=.64)
label=mat('Uncoated medicine label paper',(.90,.84,.70),.80,bump=.004)
bone=mat('Ribbed cream plastic',(.82,.77,.66),.40,bump=.003)
tile=mat('Warm ceramic tile',(.59,.59,.55),.17)
grout=mat('Thin grout',(.18,.20,.20),.74)
mirror=mat('Mirror tinted silver',(.62,.67,.68),.02,metal=.96)
glass=mat('Tempered glass',(.56,.69,.70),.12,trans=.52,alpha=.8)
white=mat('Ivory tablets',(.87,.81,.68),.68)
night=mat('Midnight window',(.011,.035,.093),.21)
moon=mat('Pearl moon glow',(.79,.87,1.0),.32,emission=1.2)
sage=mat('Wardrobe sage',(.30,.38,.34),.75,bump=.005)
warm=mat('Warm lamp glass',(.96,.67,.34),.19,emission=.5)

def box(name,xyz,dimensions,material,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=xyz)
    ob=bpy.context.object;ob.name=name
    ob.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(material)
    if bevel:
        md=ob.modifiers.new('Soft manufactured edges','BEVEL')
        md.width=min(bevel,min(dimensions)*.25);md.segments=3
        ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return ob
def sphere(name,xyz,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=xyz)
    ob=bpy.context.object;ob.name=name;ob.scale=scale
    ob.data.materials.append(material)
    for p in ob.data.polygons:p.use_smooth=True
    return ob
def cylinder(name,xyz,radius,depth,material,verts=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=xyz)
    ob=bpy.context.object;ob.name=name;ob.data.materials.append(material)
    md=ob.modifiers.new('Edge highlights','BEVEL');md.width=min(.014,radius*.15);md.segments=3
    ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return ob
def text(name,content,xyz,size,material):
    cu=bpy.data.curves.new(name,'FONT')
    cu.body=content;cu.align_x='CENTER'
    cu.size=size;cu.extrude=.0008
    ob=bpy.data.objects.new(name,cu)
    scene.collection.objects.link(ob)
    ob.location=xyz
    ob.rotation_euler=(math.pi/2,0,0)
    cu.materials.append(material)
    return ob
def tube(name,coords,radius,material):
    curve=bpy.data.curves.new(name,'CURVE')
    curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=3
    sp=curve.splines.new('POLY')
    sp.points.add(len(coords)-1)
    for i,p in enumerate(coords):
        sp.points[i].co=(*p,1)
    ob=bpy.data.objects.new(name,curve)
    scene.collection.objects.link(ob);curve.materials.append(material)
    return ob
def point_camera(name,pos,target,lens=55,fstop=3.0):
    datablock=bpy.data.cameras.new(name)
    obj=bpy.data.objects.new(name,datablock)
    scene.collection.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    datablock.lens=lens
    datablock.dof.use_dof=True
    datablock.dof.focus_distance=(Vector(target)-Vector(pos)).length
    datablock.dof.aperture_fstop=fstop
    return obj
def move_camera(ob,p1,p2,start,end):
    for frame,pos in ((start,p1),(end,p2)):
        ob.location=pos
        ob.keyframe_insert(data_path='location',frame=frame)
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points:kp.interpolation='BEZIER'
def area(name,pos,target,power,color,size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power;data.color=color;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    return obj

# Import a higher-quality existing skinned CC0 human, rather than approximating
# its face with the previous round primitive model.
files=[
 ('base_body','base_body.glb'),
 ('hair_short02','hair_short02.glb'),
 ('clothing_tshirt','clothing_tshirt.glb'),
 ('clothing_shirt','clothing_shirt.glb'),
 ('clothing_jeans','clothing_jeans.glb'),
 ('clothing_shoes','clothing_shoes.glb')
]
model_objects=[]
body_objects=[]
armatures=[]
for category,fn in files:
    path=ASSETS/fn
    if not path.is_file() or path.stat().st_size<50000:
        raise RuntimeError('Missing CC0 character asset '+str(path))
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported=list(set(bpy.data.objects)-before)
    if not imported:
        raise RuntimeError('Blender failed to import '+fn)
    if category=='base_body':body_objects=imported[:]
    for ob in imported:
        ob['asset_source']='CC0 MakeHuman via kblood CharacterCreator'
        if ob.type=='ARMATURE':
            armatures.append(ob)
        if ob.type=='MESH':
            for material in ob.data.materials:
                if material is None or not material.use_nodes:continue
                principled=material.node_tree.nodes.get('Principled BSDF')
                if principled is None:continue
                nam=material.name.lower()
                if category=='base_body' and ('skin' in nam or 'body' in nam):
                    # The source texture is normalized to grey for real-time tinting.
                    principled.inputs['Base Color'].default_value=(.47,.235,.155,1)
                    if 'Subsurface Weight' in principled.inputs:principled.inputs['Subsurface Weight'].default_value=.12
                elif category=='hair_short02':
                    principled.inputs['Base Color'].default_value=(.055,.047,.041,1)
                elif category=='clothing_shirt':
                    principled.inputs['Base Color'].default_value=(.34,.43,.37,1)
                elif category=='clothing_tshirt':
                    principled.inputs['Base Color'].default_value=(.83,.79,.71,1)
                elif category=='clothing_jeans':
                    principled.inputs['Base Color'].default_value=(.07,.095,.14,1)
    model_objects.extend(imported)
    print('IMPORTED',fn,len(imported),'arms',sum(1 for ob in imported if ob.type=='ARMATURE'))
# Base bounding box, measured before transforming the root.
points=[]
for ob in body_objects:
    if ob.type=='MESH':
        points.extend([ob.matrix_world@Vector(corner) for corner in ob.bound_box])
if not points:raise RuntimeError('No body mesh: cannot frame hero')
lo=Vector((min(p.x for p in points),min(p.y for p in points),min(p.z for p in points)))
hi=Vector((max(p.x for p in points),max(p.y for p in points),max(p.z for p in points)))
height=hi.z-lo.z
if height<.25:raise RuntimeError('Unexpected human geometry height '+str(height))
scale=1.82/height
root=bpy.data.objects.new('HERO_ROOT__animate_character',None)
scene.collection.objects.link(root)
for ob in model_objects:
    if ob.parent is None:ob.parent=root
root.scale=(scale,)*3
root.location=(-scale*(lo.x+hi.x)/2,1.05-scale*(lo.y+hi.y)/2,-scale*lo.z)
print('CHARACTER_BOUNDS',list(lo),list(hi),'scale',scale)
for a in armatures:
    print('ARMATURE',a.name,'BONES',','.join(b.name for b in list(a.pose.bones)[:75]))
# Body sways, headache reaction, and face micro-movement.
for time,dx,head in [(0,0,0),(1.5,0,0),(1.9,-.018,-.035),(2.37,.015,.025),(3.1,0,0),(5,0,0)]:
    root.location.x=-scale*(lo.x+hi.x)/2+dx
    root.rotation_euler.z=head*.5
    root.keyframe_insert('location',frame=f(time))
    root.keyframe_insert('rotation_euler',frame=f(time))
for arm in armatures:
    headbone=next((b for b in arm.pose.bones if b.name.lower()=='head'),None)
    if headbone:
        headbone.rotation_mode='XYZ'
        for t,ang in [(0,0),(1.55,0),(1.95,-.072),(2.65,.035),(3.1,0)]:
            headbone.rotation_euler.x=ang
            headbone.keyframe_insert('rotation_euler',frame=f(t))
# Blink from existing MakeHuman eyelid morphs, where available.
for ob in body_objects:
    if ob.type!='MESH' or ob.data.shape_keys is None:continue
    for kb in ob.data.shape_keys.key_blocks:
        name=kb.name.lower()
        if 'blink' not in name and 'eyelid' not in name:continue
        for t,value in [(1.4,0),(1.73,0),(1.83,.82),(1.94,0),(3,0)]:
            kb.value=value
            kb.keyframe_insert('value',frame=f(t))
print('CHARACTER_READY',len(model_objects),len(armatures))

# NIGHT BEDROOM (0.0-3.1). Physical set in consistent world space.
box('Bedroom floor',(0,2,-.13),(10,8,.22),wood)
box('Deep navy wall',(0,4.65,1.85),(10,.24,4),navy)
box('Side plaster wall',(-5,2.0,1.8),(.19,8,4),navy)
for z in (.26,3.61):
    box('Warm trim',(0,4.44,z),(9.7,.045,.055),oat,.009)
# Window/moonlight framing
box('Night sky in window',(-2.1,4.45,2.35),(2.28,.09,1.78),night)
for x in (-3.26,-2.1,-.94):
    box('Window vertical trim',(x,4.37,2.35),(.067,.10,1.88),oat,.007)
box('Window horizontal trim',(-2.1,4.36,2.34),(2.36,.11,.067),oat,.007)
sphere('Moon',(-2.65,4.30,2.74),(.14,.012,.14),moon)
for s in (-1,1):
    box('Fabric curtain %s'%s,(-2.1+s*1.2,4.13,2.29),(.37,.12,2.0),navyFabric,.07)
    for k in range(4):
        x=-2.1+s*1.2+(k-1.5)*.065
        tube('Curtain seam %s_%s'%(s,k),[(x,4.048,3.29),(x+.018,4.047,2.24),(x,4.04,1.33)],.006,linen)
# Bed, the hero is standing near foreground bed.
box('Bed walnut frame',(-.60,3.02,.37),(3.60,2.28,.55),wood,.10)
box('Tufted headboard',(-.60,4.14,1.19),(3.7,.31,1.48),navyFabric,.16)
for row in range(2):
    for col in range(5):
        sphere('Headboard buttons',( -2.00+.7*col,3.99, .88+.48*row),(.22,.05,.15),navyFabric)
box('Mattress',(-.6,2.9,.76),(3.47,2.08,.29),linen,.10)
box('Duvet',(-.6,2.65,.99),(3.39,1.47,.21),navyFabric,.12)
for ix in range(3):
    for iy in range(4):
        sphere('Fabric quilt pillow',(-1.6+ix,.2+iy*.45+2.0,1.07),(.48,.20,.045),navyFabric)
for s in (-1,1):
    box('Bed pillow',(-.6+s*.82,3.76,1.01),(.98,.50,.18),linen,.10)
# Right bedside table and clock
box('Bedside table',(2.30,1.51,.70),(.96,.75,.90),wood,.06)
box('Drawer face',(2.30,1.106,.67),(.79,.04,.26),oat,.018)
sphere('Drawer brass knob',(2.30,1.075,.67),(.045,.023,.045),brass)
box('Clock satin casing',(2.30,.99,1.27),(.75,.32,.37),charcoal,.07)
box('Clock face',(2.30,.824,1.28),(.66,.023,.28),night,.016)
text('Clock numerals','02:00',(2.30,.808,1.204),.21,redLed)
box('Clock snooze button',(2.30,1.01,1.49),(.16,.11,.035),brass,.01)
box('Brass bedside lamp stand',(2.83,1.75,1.42),(.05,.05,.58),brass,.01)
sphere('Lamp shade',(2.83,1.75,1.77),(.23,.23,.16),warm)
for i in range(3):
    box('Book stack %02d'%i,(1.85,1.60,1.18+i*.051),(.39,.30,.045),linen if i%2 else navyFabric,.005)
area('Bedroom moon cool',(-3.3,1.3,3.6),(0,1,1.8),710,(.42,.63,1),4)
area('Bedroom tungsten bedside',(3.6,-.3,3.0),(0,1,1.6),450,(1,.64,.40),3)
area('Soft skin bounce',(0,-3.0,2.6),(0,1,1.7),210,(.95,.85,.74),3)

# BATHROOM CABINET (3.1-5.0), separated physically from bedroom.
cx=12.0
box('Bathroom tiled wall',(cx,3.9,1.72),(7.3,.15,4.2),tile,.015)
for xj in range(13):
    xp=cx-3.35+xj*.56
    box('Vertical ceramic grout',(xp,3.815,1.73),(.009,.02,4.02),grout,.003)
for zj in range(8):
    box('Horizontal ceramic grout',(cx,3.808,-.14+zj*.54),(7.1,.02,.009),grout,.002)
box('Bathroom vanity',(cx,1.75,.45),(3.4,1.18,.89),navy,.07)
box('Bathroom ceramic sink',(cx,1.75,.88),(2.55,1.07,.14),linen,.09)
sphere('Bathroom basin recess',(cx,1.65,.915),(.72,.36,.047),tile)
cylinder('Bathroom tap', (cx,2.13,1.08),.045,.25,brass)
box('Faucet spout',(cx,1.95,1.22),(.08,.35,.08),brass,.02)
# Mirror-cabinet with shelves, physically opens on hinges.
cab=cx
box('Medicine cabinet back',(cab,3.48,2.12),(1.91,.48,2.05),wood,.06)
box('Medicine cabinet interior',(cab,3.197,2.12),(1.69,.075,1.85),navy,.018)
for z in (1.47,2.02,2.54):
    box('Glass medicine shelf',(cab,2.93,z),(1.73,.44,.045),glass,.006)
for i in range(4):
    bx=cab-.61+(i%2)*1.23
    bz=1.70+(i//2)*.59
    cylinder('Background medical bottle %s'%i,(bx,2.97,bz),.125,.38,bone)
    cylinder('Cap on medicine bottle %s'%i,(bx,2.97,bz+.22),.14,.11,brass)
    text('Generic bottle label','MED',(bx,2.839,bz-.055),.085,navy)
# Hero amber bottle with visible white medicine and warm paper label.
cylinder('Amber medicine bottle',(cab,2.87,1.70),.27,.75,amber)
cylinder('Amber bottle neck',(cab,2.87,2.09),.22,.15,amber)
cylinder('Cream ribbed childproof cap',(cab,2.87,2.21),.29,.25,bone)
for j in range(45):
    th=math.tau*j/45
    obj=box('Cap vertical rib %02d'%j,(cab+.289*math.cos(th),2.87+.289*math.sin(th),2.21),(.012,.012,.195),bone,.002)
    obj.rotation_euler.z=th
box('Matte expiry label',(cab,2.586,1.68),(.48,.013,.42),label,.009)
text('Bottle upper label','PAINKILLER',(cab,2.567,1.76),.073,navy)
text('Bottle expiry date','EXP 2023',(cab,2.563,1.58),.085,charcoal)
for i in range(4):
    sphere('Visible tablets %02d'%i,(cab+.10*math.cos(math.tau*i/4),2.87+.10*math.sin(math.tau*i/4),1.43),(.085,.085,.05),white)
# Hinged mirror front, opening to reveal pill bottle.
hinge=bpy.data.objects.new('ANIMATE_CABINET_DOOR_HINGE',None);scene.collection.objects.link(hinge)
hinge.location=(cab+.98,2.70,2.12)
door=box('Mirror cabinet door',(cab+1.25,2.68,2.14),(.55,.085,2.0),mirror,.018)
doorframe=box('Mirror door walnut border',(cab+1.25,2.76,2.14),(.62,.055,2.11),wood,.020)
for ob in (door,doorframe):
    m=ob.matrix_world.copy()
    ob.parent=hinge
    ob.matrix_world=m
for time,rot in [(3.1,0),(3.55,-.25),(4.45,-1.26),(5,-1.37)]:
    hinge.rotation_euler.z=rot
    hinge.keyframe_insert(data_path='rotation_euler',frame=f(time))
# light above medicine cabinet
box('Bathroom tube wall fixture',(cab,3.38,3.42),(1.50,.35,.15),warm,.07)
area('Bathroom warm wall lamp',(cab,1.1,3.66),(cab,3.0,1.9),750,(1,.77,.56),3)
area('Blue bathroom window reflection',(cab+2.9,.5,2.8),(cab,3.0,1.75),520,(.33,.58,.94),4)

# Three explicit 3D camera rigs with planned camera motion, not still-image pans.
clock_cam=point_camera('CAM_01__CLOCK',(2.32,-1.03,1.39),(2.3,1.0,1.28),88,2.9)
face_cam=point_camera('CAM_02__HEADACHE',(.40,-2.3,1.77),(0,1.05,1.65),77,3.8)
med_cam=point_camera('CAM_03__MEDICINE',(cab-.30,-.52,2.10),(cab,2.85,1.80),81,3.0)
move_camera(clock_cam,(2.20,-1.08,1.36),(2.30,-.72,1.33),1,45)
move_camera(face_cam,(.38,-2.55,1.74),(-.18,-2.03,1.81),46,93)
move_camera(med_cam,(cab-.72,-1.22,2.08),(cab+.11,-.55,1.85),94,150)
for i,(name,frame,camera) in enumerate([
    ('Clock 02:00',1,clock_cam),
    ('Headache character reaction',46,face_cam),
    ('Opening medicine cabinet',94,med_cam)
]):
    mark=scene.timeline_markers.new(name,frame=frame)
    mark.camera=camera
scene.camera=clock_cam
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/'BlenderMedi_5s_cinematic.blend'))
print('SCENE_READY 1920x1080 30fps 150frames',
      'objects',len(bpy.data.objects),'characterMeshes',len(model_objects))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--stills' in args:
    for frame in (1,28,46,69,94,127,149):
        scene.frame_set(frame)
        scene.render.filepath=str(OUTPUT/('still_%03d.png'%frame))
        bpy.ops.render.render(write_still=True)
        print('STILL_DONE',frame)
    scene.render.filepath=str(OUTPUT/'frame_')
if '--render' in args:
    scene.render.filepath=str(OUTPUT/'frame_')
    bpy.ops.render.render(animation=True)
    print('ALL_FRAMES_RENDERED',TOTAL)
