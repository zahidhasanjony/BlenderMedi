"""BlenderMedi: 5-second opening | reusable stylized asset builder.
Works with Blender 4.0 on Ubuntu GitHub runners, no add-ons or paid models.
Creates original editable Blender objects and optional GLB asset exports.
This generates assets and review stills, NOT the final animated video.
"""
import bpy, math, random, os, sys
from pathlib import Path
from mathutils import Vector
random.seed(19)
OUT = Path(__file__).resolve().parent / 'output'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine=os.getenv('RENDER_ENGINE','CYCLES')
if scene.render.engine=='CYCLES':
    scene.cycles.samples=int(os.getenv('SAMPLES','20'))
    # Ubuntu's Blender package may not have OpenImageDenoiser.
    scene.cycles.use_denoising=False
    for view_layer in scene.view_layers:
        if hasattr(view_layer, 'cycles') and hasattr(view_layer.cycles, 'use_denoising'):
            view_layer.cycles.use_denoising=False
scene.render.resolution_x=1920
scene.render.resolution_y=1080
scene.render.resolution_percentage=60
scene.render.fps=30
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value=(.020,.028,.055,1)
bg.inputs['Strength'].default_value=.4
try: scene.view_settings.view_transform='AgX'
except Exception: pass

COL={}
for name in ('CHARACTER_MALE','BEDROOM_SET','MEDICINE_CABINET','LIGHTS_CAMERAS'):
    c=bpy.data.collections.new(name)
    scene.collection.children.link(c)
    COL[name]=c

def assign(obj,collection):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    COL[collection].objects.link(obj)
    return obj

def material(name,rgb,rough=.55,metal=0,sss=0,texture=0,emit=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
    nodes=m.node_tree.nodes;link=m.node_tree.links
    b=nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*rgb,1)
    b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal
    if 'Subsurface Weight' in b.inputs:b.inputs['Subsurface Weight'].default_value=sss
    if emit and 'Emission Color' in b.inputs:
        b.inputs['Emission Color'].default_value=(*rgb,1)
        b.inputs['Emission Strength'].default_value=emit
    if texture:
        n=nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value=110
        n.inputs['Detail'].default_value=2
        bnode=nodes.new('ShaderNodeBump')
        bnode.inputs['Strength'].default_value=.12
        bnode.inputs['Distance'].default_value=texture
        link.new(n.outputs['Fac'],bnode.inputs['Height'])
        link.new(bnode.outputs['Normal'],b.inputs['Normal'])
    return m

skin=material('Skin | warm brown',(.43,.231,.137),.50,sss=.12,texture=.003)
shadow=material('Skin features',(.24,.10,.066),.63)
lip=material('Lips warm rose',(.44,.17,.12),.68)
sclera=material('Ivory eye white',(.89,.84,.78),.17)
iris=material('Dark amber iris',(.14,.074,.038),.13)
black=material('Iris pupil',(.013,.010,.015),.12)
highlight=material('Eye highlight',(.95,.99,1.0),.08,emit=.6)
hair=material('Hair | near-black wavy',(.016,.019,.028),.32)
hairwarm=material('Hair | highlights',(.045,.042,.052),.35)
shirt=material('T-shirt | slate',(.14,.18,.21),.79,texture=.006)
stitch=material('Shirt stitching',(.27,.33,.37),.90)
pants=material('Joggers | graphite',(.055,.065,.079),.82,texture=.008)
shoe=material('Trainers | dark',(.025,.031,.044),.72)
cream=material('Pillow warm ivory',(.76,.77,.75),.88,texture=.008)
navy=material('Duvet | muted indigo',(.10,.16,.28),.86,texture=.008)
cotton=material('Bed linen blue',(.19,.29,.40),.89,texture=.008)
wood=material('Wood | walnut',(.20,.106,.060),.57,texture=.030)
oak=material('Wood | light trim',(.43,.255,.145),.56,texture=.014)
wall=material('Wall | midnight slate',(.065,.097,.151),.93,texture=.008)
wall2=material('Wall | navy',(.105,.160,.235),.92,texture=.008)
fabric=material('Curtains | cotton blue',(.12,.22,.34),.94,texture=.008)
gold=material('Lamp | brass',(.49,.34,.18),.26,metal=.7)
metal=material('Clock & cabinet metal',(.052,.061,.077),.29,metal=.62)
glass=material('Cabinet shelf | tinted glass',(.12,.22,.29),.16,metal=.22)
bottle_mat=material('Medicine bottle | matte ivory',(.84,.78,.64),.33)
paper=material('Medicine label paper',(.93,.87,.72),.91)
red=material('Clock | red LED',(.97,.056,.029),.20,emit=5)
redglass=material('Clock | glass face',(.17,.025,.023),.20)
night=material('Night sky',(.019,.055,.12),.22)
moon=material('Moon | pale ivory',(.92,.94,.87),.22,emit=1.5)

def ball(n,pos,scale,m,col,seg=40):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=20,location=pos)
    o=assign(bpy.context.object,col)
    o.name=n;o.scale=scale;o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
    return o

def box(n,pos,size,m,col,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=assign(bpy.context.object,col)
    o.name=n;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(m)
    if bevel>0:
        mod=o.modifiers.new('Rounded manufactured edges','BEVEL')
        mod.width=min(bevel,min(size)*.24)
        mod.segments=3
        o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    return o

def link(n,pts,width,m,col):
    cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D'
    cu.bevel_depth=width;cu.bevel_resolution=3;cu.resolution_u=20
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for p,co in zip(sp.bezier_points,pts):
        p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(n,cu)
    COL[col].objects.link(o)
    cu.materials.append(m)
    return o

def limb(n,start,end,width,mat,col):
    a,b=Vector(start),Vector(end)
    o=ball(n,tuple((a+b)*.5),(width,width,(b-a).length*.58),mat,col)
    o.rotation_euler=Vector((0,0,1)).rotation_difference(b-a).to_euler()
    return o

def text3(n,body,pos,size,mat,col):
    cu=bpy.data.curves.new(n,'FONT')
    cu.body=body;cu.size=size;cu.extrude=.0015;cu.align_x='CENTER'
    o=bpy.data.objects.new(n,cu)
    COL[col].objects.link(o)
    o.location=pos;o.rotation_euler=(math.pi/2,0,0)
    cu.materials.append(mat)
    return o

def keep_parent(o, parent):
    # Explicit matrix-parent-inverse: preserve the object's world transform.
    # The old assignment/restoration moved nested head parts on Blender 4.0.
    o.parent=parent
    o.matrix_parent_inverse=parent.matrix_world.inverted()


def controller(name,pos,size):
    o=bpy.data.objects.new(name,None)
    COL['CHARACTER_MALE'].objects.link(o)
    o.empty_display_type='SPHERE';o.empty_display_size=size
    o.location=pos
    return o

# Original stylized 3D character. Deliberately separate face parts for expression controls.
x=-1.12;y=-.14
root=controller('CTRL_ROOT__move_character',(x,y,0),.12)
head_ctl=controller('CTRL_HEAD__rotate_expression',(x,y-.07,2.35),.39)
hand_ctl=controller('CTRL_HAND_R__gesture',(-.79,y-.32,2.26),.10)
headparts=[];handparts=[]
ball('Body chest',(x,y,1.62),(.42,.28,.55),shirt,'CHARACTER_MALE')
ball('Shoulder garment',(x,y,1.91),(.53,.30,.24),shirt,'CHARACTER_MALE')
ball('Waist & hips',(x,y,1.10),(.35,.24,.21),pants,'CHARACTER_MALE')
ball('Exposed neck',(x,y-.01,2.07),(.13,.13,.20),skin,'CHARACTER_MALE')
for side in (-1,1):
    px=x+side*.22
    limb('Thigh '+str(side),(px,y,1.03),(px+side*.03,y,.62),.18,pants,'CHARACTER_MALE')
    limb('Shin '+str(side),(px+side*.03,y,.64),(px+side*.05,y,.19),.145,pants,'CHARACTER_MALE')
    ball('Shoe upper '+str(side),(px+side*.05,y-.15,.155),(.19,.30,.14),shoe,'CHARACTER_MALE')
    box('Sneaker sole '+str(side),(px+side*.05,y-.15,.068),(.37,.57,.078),cream,'CHARACTER_MALE',.035)
    for j in range(3):
        link('Sneaker laces '+str(side)+str(j),
          [(px-.07,y-.38+j*.045,.23),(px,y-.41+j*.045,.23),(px+.07,y-.38+j*.045,.23)],
          .008,stitch,'CHARACTER_MALE')
    link('Sleeve stitching '+str(side),
         [(x+side*.42,y-.15,1.85),(x+side*.48,y-.18,1.77),(x+side*.47,y-.17,1.72)],
         .010,stitch,'CHARACTER_MALE')
link('T-shirt collar',[(x-.16,y-.26,2.02),(x-.08,y-.27,1.99),(x,y-.278,1.96),
    (x+.08,y-.27,1.99),(x+.16,y-.26,2.02)],.014,stitch,'CHARACTER_MALE')
for j in range(4):
    s=-1 if j%2 else 1
    link('T-shirt fabric fold '+str(j),[(x+.08*s,y-.257,1.53+j*.1),
         (x+.16*s,y-.261,1.50+j*.10),(x+.10*s,y-.257,1.46+j*.10)],
         .006,stitch,'CHARACTER_MALE')
# Left arm down, right arm bent with fingers touching temple.
limb('Left tee sleeve',(x-.43,y,1.83),(x-.58,y-.04,1.65),.17,shirt,'CHARACTER_MALE')
limb('Left forearm',(x-.57,y-.04,1.65),(x-.65,y-.16,1.12),.108,skin,'CHARACTER_MALE')
ball('Left palm',(x-.65,y-.16,1.11),(.11,.08,.15),skin,'CHARACTER_MALE')
limb('Right tee sleeve',(x+.43,y,1.84),(x+.58,y-.05,1.72),.17,shirt,'CHARACTER_MALE')
limb('Right forearm',(x+.58,y-.05,1.73),(x+.34,y-.36,2.24),.108,skin,'CHARACTER_MALE')
rhand=ball('Hand on temple',(x+.34,y-.38,2.25),(.12,.08,.16),skin,'CHARACTER_MALE')
handparts.append(rhand)
for side in (-1,1):
    hx=x+side*.30
    for j in range(4):
        px=hx+.036*(j-1.5)
        if side==1:
            ob=limb('Raised hand finger '+str(j),(px,y-.40,2.31),(px-.01,y-.42,2.49),.030,skin,'CHARACTER_MALE')
            handparts.append(ob)
        else:
            limb('Resting hand finger '+str(j),(px,y-.16,1.06),(px,y-.20,.90),.029,skin,'CHARACTER_MALE')
# Face and grooming; larger eyes, layered eyelids, hair locks, sculpted ears.
headparts.append(ball('Head stylized sculpt',(x,y-.08,2.38),(.40,.32,.44),skin,'CHARACTER_MALE'))
headparts.append(ball('Chin',(x,y-.18,2.10),(.25,.20,.145),skin,'CHARACTER_MALE'))
for s in (-1,1):
    headparts.append(ball('Ear rim '+str(s),(x+s*.399,y-.07,2.32),(.08,.07,.145),skin,'CHARACTER_MALE'))
    headparts.append(ball('Ear interior '+str(s),(x+s*.41,y-.125,2.31),(.044,.019,.079),shadow,'CHARACTER_MALE'))
    headparts.append(ball('Cheek '+str(s),(x+s*.22,y-.31,2.26),(.125,.05,.09),skin,'CHARACTER_MALE'))
    headparts.append(ball('Eye white '+str(s),(x+s*.157,y-.347,2.436),(.111,.054,.092),sclera,'CHARACTER_MALE'))
    headparts.append(ball('Iris '+str(s),(x+s*.157,y-.397,2.43),(.057,.023,.058),iris,'CHARACTER_MALE'))
    headparts.append(ball('Pupil '+str(s),(x+s*.157,y-.417,2.43),(.030,.009,.038),black,'CHARACTER_MALE'))
    headparts.append(ball('Cornea catchlight '+str(s),(x+s*.139,y-.430,2.455),(.017,.009,.015),highlight,'CHARACTER_MALE'))
    headparts.append(link('Upper eye lid '+str(s),[(x+s*.06,y-.350,2.48),(x+s*.11,y-.380,2.52),
                        (x+s*.157,y-.39,2.527),(x+s*.217,y-.373,2.50),(x+s*.26,y-.35,2.47)],
                        .014,shadow,'CHARACTER_MALE'))
    headparts.append(link('Worried eyebrow '+str(s),[(x+s*.065,y-.33,2.58),(x+s*.12,y-.36,2.618),
                       (x+s*.21,y-.355,2.625),(x+s*.29,y-.31,2.58)],.024,hair,'CHARACTER_MALE'))
headparts.append(ball('Nose bridge',(x,y-.364,2.34),(.071,.062,.13),skin,'CHARACTER_MALE'))
headparts.append(ball('Nose tip',(x,y-.438,2.27),(.081,.071,.055),skin,'CHARACTER_MALE'))
for s in (-1,1):
    headparts.append(ball('Nostril '+str(s),(x+s*.054,y-.48,2.253),(.018,.01,.011),shadow,'CHARACTER_MALE'))
headparts.append(link('Concerned mouth',[(x-.088,y-.365,2.145),(x-.04,y-.39,2.129),
                 (x,y-.394,2.122),(x+.04,y-.39,2.129),(x+.088,y-.365,2.145)],
                 .012,lip,'CHARACTER_MALE'))
headparts.append(ball('Lower lip',(x,y-.372,2.11),(.07,.018,.016),lip,'CHARACTER_MALE'))
headparts.append(ball('Hair scalp',(x,y-.006,2.717),(.402,.312,.184),hair,'CHARACTER_MALE'))
for j in range(30):
    a=2*math.pi*j/30
    ob=ball('Wavy hair sculpt %02d'%j,(x+.31*math.cos(a),y+.24*math.sin(a),
                2.72+.035*math.sin(3*a)),(.12,.11,.086),hair if j%4 else hairwarm,'CHARACTER_MALE',24)
    ob.rotation_euler[1]=random.uniform(-.23,.23)
    headparts.append(ob)
for j in range(8):
    px=x-.32+j*.089
    headparts.append(link('Forehead hair fringe %02d'%j,
              [(px,y-.13,2.81),(px-.02,y-.25,2.75),(px+.01,y-.32,2.67-.025*(j%2))],
              .037 if j%2 else .044,hair,'CHARACTER_MALE'))
for o in headparts:keep_parent(o,head_ctl)
for o in handparts:keep_parent(o,hand_ctl)
for o in list(COL['CHARACTER_MALE'].objects):
    if o!=root and o.parent is None:keep_parent(o,root)

# Physical bedroom set: flooring, quilt, headboard, drawers, clock, moonlit window.
box('Walnut plank floor',(0,1.7,-.13),(10,9,.24),wood,'BEDROOM_SET',.03)
for j in range(22):
    box('Wood plank joint %02d'%j,(-4.6+(j%11)*.91,-.3+(j//11)*3.6,-.005),
         (.86,3.5,.012),wood if j%6 else oak,'BEDROOM_SET',.006)
box('Midnight back wall',(0,4.12,1.92),(10,.2,4.1),wall,'BEDROOM_SET',.03)
box('Left plaster wall',(-5,1.7,1.92),(.2,6,4.1),wall2,'BEDROOM_SET',.03)
box('Right plaster wall',(5,1.7,1.92),(.2,6,4.1),wall2,'BEDROOM_SET',.03)
for z in (.25,1.2,3.69):
    box('Wooden wall molding '+str(z),(0,3.97,z),(9.8,.06,.038),oak,'BEDROOM_SET',.009)
# Sky and curtains
box('Window blue night',(2.56,3.93,2.37),(2.35,.07,1.74),night,'BEDROOM_SET',.02)
for dx in (-1.18,0,1.18):
    box('Window upright '+str(dx),(2.56+dx,3.82,2.37),(.07,.10,1.75),oak,'BEDROOM_SET',.01)
for dz in (-.88,0,.88):
    box('Window horizontal '+str(dz),(2.56,3.82,2.37+dz),(2.43,.10,.065),oak,'BEDROOM_SET',.01)
ball('Moon through window',(3.06,3.85,2.78),(.16,.025,.16),moon,'BEDROOM_SET')
for side in (-1,1):
    cx=2.56+side*1.02
    box('Curtain fabric '+str(side),(cx,3.68,2.35),(.40,.11,2.08),fabric,'BEDROOM_SET',.04)
    for j in range(4):
        link('Fabric drape '+str(side)+str(j),[(cx-.15+j*.085,3.57,3.35),
               (cx-.15+j*.085,3.54,2.4),(cx-.15+j*.085,3.57,1.30)],.011,cotton,'BEDROOM_SET')
box('Curtain curtain rod',(2.56,3.58,3.48),(2.86,.085,.085),gold,'BEDROOM_SET')
# Soft bed and quilted blanket
box('Walnut bed frame',(-2.55,2.12,.34),(3.35,2.54,.55),wood,'BEDROOM_SET',.10)
box('Soft mattress',(-2.55,2.07,.69),(3.21,2.32,.31),cream,'BEDROOM_SET',.12)
box('Navy upholstered headboard',(-2.55,3.30,1.13),(3.36,.35,1.48),navy,'BEDROOM_SET',.15)
for j in range(8):
    ball('Headboard upholstery tuft '+str(j),(-3.76+j%4*.80,3.08,.75+j//4*.4),
         (.37,.085,.15),cotton,'BEDROOM_SET')
for s in (-1,1):
    box('Soft pillow '+str(s),(-2.55+s*.76,2.90,.98),(1.03,.50,.19),cream,'BEDROOM_SET',.13)
box('Duvet blanket',(-2.55,1.63,.98),(3.18,1.56,.30),navy,'BEDROOM_SET',.15)
for j in range(12):
    ball('Quilted puff %02d'%j,(-3.75+j%4*.81,1.12+j//4*.46,1.10),
         (.35,.22,.05),navy,'BEDROOM_SET')
box('Wool floor rug',(.15,.65,.022),(3.6,2.5,.04),cotton,'BEDROOM_SET',.08)
# Nightstand with physical RED clock
box('Nightstand top',(-.32,2.39,.88),(.82,.72,.11),oak,'BEDROOM_SET',.06)
box('Nightstand drawer',(-.32,2.40,.61),(.74,.61,.48),wood,'BEDROOM_SET',.05)
box('Drawer front',(-.32,2.071,.65),(.67,.045,.22),oak,'BEDROOM_SET',.025)
ball('Drawer bronze knob',(-.32,2.029,.65),(.052,.025,.052),gold,'BEDROOM_SET')
box('Clock graphite housing',(-.32,1.92,1.07),(.66,.30,.31),metal,'BEDROOM_SET',.065)
box('Clock dark face',(-.32,1.753,1.07),(.57,.015,.22),redglass,'BEDROOM_SET',.013)
text3('2AM glowing digital clock','02:00',(-.32,1.736,1.022),.176,red,'BEDROOM_SET')
box('Clock top button',(-.32,1.90,1.24),(.16,.14,.035),metal,'BEDROOM_SET',.015)
box('Bedside lamp base',(-.67,2.60,1.04),(.12,.13,.035),gold,'BEDROOM_SET')
box('Lamp vertical stem',(-.67,2.60,1.20),(.055,.055,.29),gold,'BEDROOM_SET')
ball('Lamp shade warm brass',(-.67,2.60,1.38),(.20,.19,.15),gold,'BEDROOM_SET')
ball('Lamp glowing pearl',(-.67,2.49,1.31),(.09,.073,.075),moon,'BEDROOM_SET')
for j in range(3):
    box('Bedside book '+str(j),(-.08+j*.067,2.58,1.0+j*.051),
         (.36,.20,.047),wall2 if j%2 else cotton,'BEDROOM_SET',.009)
for j in range(2):
    box('Walnut picture frame '+str(j),(-4.08+j*.88,3.99,2.40),(.71,.08,.81),oak,'BEDROOM_SET',.022)
    box('Picture artwork '+str(j),(-4.08+j*.88,3.939,2.40),(.56,.018,.66),
        navy if j else cotton,'BEDROOM_SET',.006)

# Medicine cabinet designed to share the same room coordinates.
box('Medicine cabinet walnut shell',(4.04,3.68,1.66),(1.27,.26,2.30),oak,'MEDICINE_CABINET',.08)
box('Cabinet dark inside',(4.04,3.48,1.66),(1.04,.12,1.99),wall,'MEDICINE_CABINET',.02)
for z in (.75,1.44,2.13):
    box('Tempered glass shelf '+str(z),(4.04,3.11,z),(1.05,.63,.06),glass,'MEDICINE_CABINET',.015)
for j in range(4):
    xx=3.76+j%2*.57; zz=1.04+j//2*.71
    ball('Unbranded pharmacy bottle '+str(j),(xx,3.18,zz),(.125,.135,.28),
         bottle_mat,'MEDICINE_CABINET')
    box('Small product label '+str(j),(xx,3.03,zz),(.23,.015,.19),paper,'MEDICINE_CABINET',.006)
ball('Hero medicine bottle',(4.04,2.96,1.20),(.205,.21,.41),bottle_mat,'MEDICINE_CABINET')
box('Hero label paper',(4.04,2.734,1.18),(.38,.018,.37),paper,'MEDICINE_CABINET',.014)
text3('Hero product generic','PAINKILLER',(4.04,2.718,1.30),.064,black,'MEDICINE_CABINET')
text3('Expired label year','EXP 2023',(4.04,2.718,1.14),.092,shadow,'MEDICINE_CABINET')
box('Child-resistant bottle cap',(4.04,2.96,1.66),(.44,.44,.15),metal,'MEDICINE_CABINET',.037)
for j in range(12):
    box('Bottle cap ridges '+str(j),(3.875+j*.03,2.726,1.66),(.008,.010,.095),
        gold,'MEDICINE_CABINET',.002)

# Four review cameras; these are source rigs for the future 5-second animation.
def cam(name,pos,target,focal):
    d=bpy.data.cameras.new(name)
    o=bpy.data.objects.new(name,d)
    COL['LIGHTS_CAMERAS'].objects.link(o)
    o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.lens=focal
    d.dof.use_dof=True
    d.dof.focus_distance=(Vector(target)-Vector(pos)).length
    d.dof.aperture_fstop=3.0
    return o
cams={
 'bedroom_wide':cam('CAM_Bedroom_master',(0,-7.6,2.43),(-.8,1.0,1.70),38),
 'character_face':cam('CAM_Man_headache',(-.85,-4.7,2.48),(-1.10,-.14,2.39),68),
 'clock_closeup':cam('CAM_2AM_clock',(-.27,-.19,1.34),(-.32,1.75,1.065),84),
 'medicine_closeup':cam('CAM_Expired_bottle',(4.08,.18,1.45),(4.04,2.92,1.17),80)
}
def light(name,loc,target,energy,color,size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy;data.color=color;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data)
    COL['LIGHTS_CAMERAS'].objects.link(o)
    o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('Moon blue key',(2.0,-2.8,4.2),(-1,0,2.2),900,(.60,.76,1),5)
light('Bedside amber fill',(-2,.2,3.2),(-1,0,2.4),560,(1,.68,.47),3.4)
light('Hair edge rim',(0,2.5,3.5),(-1,0,2.5),710,(.70,.81,1),2.7)
light('Cabinet fill',(3.5,1.5,3.1),(4,3.0,1.3),450,(1,.81,.63),2.6)
light('Face shadow softener',(-.25,-2.8,2.6),(-1,0,2.4),250,(.85,.87,1),3)

for name in ('CHARACTER_MALE','BEDROOM_SET','MEDICINE_CABINET'):
    try:COL[name].asset_mark()
    except Exception:pass
# Geometry QA before saving and preview renders.
for n in ('CTRL_ROOT__move_character','CTRL_HEAD__rotate_expression',
          'Head stylized sculpt','Eye white -1','Eye white 1',
          'Hair scalp','Torso chest','Bedside lamp base'):
    o=bpy.data.objects.get(n)
    if o:
        print('OBJECT_QA', n, 'center=',[round(v,3) for v in o.matrix_world.translation],
              'dimensions=',[round(v,3) for v in o.dimensions],
              'parent=',o.parent.name if o.parent else 'none')
scene.frame_start=1;scene.frame_end=150;scene.frame_set(1)
scene.camera=cams['bedroom_wide']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BlenderMedi_stylized_assets.blend'))
print('ASSET_LIBRARY_CREATED',len(bpy.data.objects))
if '--export-glb' in sys.argv:
    for c,f in [('CHARACTER_MALE','male_character.glb'),
                ('BEDROOM_SET','bedroom_environment.glb'),
                ('MEDICINE_CABINET','medicine_cabinet.glb')]:
        bpy.ops.object.select_all(action='DESELECT')
        selection=list(COL[c].objects)
        for o in selection:o.select_set(True)
        if selection:bpy.context.view_layer.objects.active=selection[0]
        try:
            bpy.ops.export_scene.gltf(filepath=str(OUT/f),export_format='GLB',use_selection=True)
            print('GLB_EXPORTED',f)
        except Exception as ex: print('GLB_EXPORT_FAILED',f,str(ex))
        bpy.ops.object.select_all(action='DESELECT')
if '--previews' in sys.argv:
    scene.render.resolution_percentage=int(os.getenv('PREVIEW_PERCENT','45'))
    for name,c in cams.items():
        scene.camera=c
        scene.render.filepath=str(OUT/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        print('PREVIEW_CREATED',name)
