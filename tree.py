# Ki: NFTree... Growf? ... author: Nathaniel D. Gibson

import bpy
import bmesh
import mathutils
import math
import random

_Z = mathutils.Vector((0.0, 0.0, 1.0))

def rot_q(v):
    return _Z.rotation_difference(v.normalized())

class Cell():
    def __init__(self, x, y, z=0.0, center=None):
        self.x = x
        self.y = y
        self.z = z
        self.center = center
        self.origin = mathutils.Vector((x, y, z))
        self.origv = None if self.center is None else self.origin - self.center
        self.maxdev = 1
        self.loc = mathutils.Vector((x, y, z))
        self.v = mathutils.Vector((0.0, 0.0, 0.0))
        self.nloc = self.loc
        self.nv = self.v
        self.mindist = 0.001
        self.ease = 0.4
        self.ease_away = 0.01
        self.age = 0
        self.color = mathutils.Color((0.3, 1.0, 0.2))
        self.rate_growth_radial = 1.0
        self.targets = [] # Can be turned into a way to react to target objects
        self.neighbors = []
        self.hormones = []
        
        self.v = self.random_vector()
        
    def random_vector(self, vmax=0.06):
        vx = random.random() * (vmax * 2) - vmax
        vy = random.random() * (vmax * 2) - vmax
        vz = random.random() * (vmax * 2) - vmax
        return mathutils.Vector((vx, vy, vz))
    
    def add_neighbor(self, n):
        self.neighbors.append(n)
        
    def grow(self):
        
        self.move_random(flat=False)
        self.grow_out()
        self.move_boids()
        #self.move_rest()
        
        self.nloc = self.loc + self.nv
        self.age += 1

    def update(self):
        self.loc = self.nloc
        self.v = self.nv
                    
    def move_random(self, flat=True):
        self.nv = self.nv * self.random_vector(vmax=0.2)
        if flat:
            self.nv.z = 0.0
        
    def dist_origin(self):
        v = self.loc - self.origin
        return math.sqrt((v.x * v.x) + (v.y * v.y) + (v.z * v.z))
            
    def move_rest(self, ratio=0.5):
        if self.dist_origin() > self.maxdev:
            v = (self.loc + self.origin) / 2
            e = v - self.loc
            self.nv = self.nv + (e * ratio)
        
    def move_boids(self):
        rn = 1 / len(self.neighbors)
        al, av = self.loc, self.v
        for n in self.neighbors:
            al = al + n.loc
            av = av + n.v
            #self.nv = self.nv + (-n.loc * self.ease_away)
        al = al * rn
        av = av * rn
        ad = al - self.loc
        sr = 0.1
        self.nv = self.nv + (av * self.ease)
        
    def grow_out(self):
        v = self.origv * (1 / (self.age + 1))
        self.nv = v * self.rate_growth_radial
    

class Slice():
    def __init__(self, neighbors, start_radius=1, detail_depth=0.1, center=mathutils.Vector((0.0, 0.0, 0.0)), normal=mathutils.Vector((0.0, 0.0, 1.0))):
        self.neighbors = neighbors
        self.center = center
        self.orientation = normal
        self.rot_matrix = rot_q(self.orientation)
        self.radius = start_radius
        self.ddepth = detail_depth / 2
        self.cells = []
        
        self.init_circular()
        self.link()
    
    def init_circular(self):
        r = math.pi * 2 / self.neighbors
        for i in range(0, self.neighbors):
            x = math.sin(i * r) * self.radius
            y = math.cos(i * r) * self.radius
            v = mathutils.Vector((x, y, 0.0))
            v.rotate(self.rot_matrix.normalized())
            v = v + self.center
            c = Cell(v.x, v.y, z=v.z, center=self.center)
            self.cells.append(c)
        
    def link(self, kernel=[-3, -2, -1, 1, 2, 3]):
        # works because Python enumeration is the bees knees, not to mention array index notation
        for i, c in enumerate(self.cells):
            for k in kernel:
                ii = (i + k) % len(self.cells)
                c.add_neighbor(self.cells[ii])
            
    def get_vertices(self, z):
        o = []
        for i, v in enumerate(self.cells):
            o.append([v.loc.x, v.loc.y, v.loc.z])
        self.next()
        return o
    
    def grow(self):
        for v in self.cells:
            v.grow()
        for v in self.cells:
            v.update()


class Tip():
    def __init__(self, branch, loc, dir=(0.0, 0.0, 1.0), speed=0.3, hormones=[], data={}, bifurcation=(4, 3, 0.5, 0.618, 0.4, 0.8), cell_res=8, start_at_0=True):
        
        # Initial configuration (can be changed by factors that affect the tip)
        self.parent = branch
        self.direction = mathutils.Vector(dir)
        self.rq = self.update_q()
        self.bifurc_period = bifurcation[0]
        self.bifurcations = bifurcation[1]
        self.biphase_offset = bifurcation[2]
        self.bifurc_sr = bifurcation[3] # initial speed ratio for bifurcated children
        self.bifurc_inclination = bifurcation[4]
        self.bifurc_radius_ratio = bifurcation[5]
        self.speed = speed
        self.speed_decay = 0.98 # ratio of decay of growth speed per growth
        self.data = data
        self.hormones = hormones    # hormones are dropped as a total of what is available
        
        # Slices and surface cells
        self.start_radius = 0.01
        self.branch = []
        self.cell_res = cell_res
        self.cur_slice = None

        # Working parameters (counters, history, etc)
        self.cache_vertex = None
        self.loc = mathutils.Vector(loc)
        self.last_loc = None
        self.phase = 0.0
        self.age = 0
        
        # direction of gravity and direction of light are unit vectors that point toward gravity and toward the brightest light
        self.light_axis = mathutils.Vector((0.5, 0.5, 1.0))
        self.gravity_axis = mathutils.Vector((0.0, 0.0, -1.0))
        
        if start_at_0:
            self.start()

        # auxins specifically in tip growth are 
        # What makes plants grow? these hormones.
        # bending happens because light hits one side of the stem, spending the auxins
        # slowing down growth on that side!!!! intense, causing the shoots and leaves to turn toward the light
        # As this tip grows it needs to drop auxins to the cells it's dropping
        # The cells it's dropping are 
        # in roots, auxins cause less growth, causing them to bend away from the light
        # Each cell dropped has same amount of auxins
        # when the dropped cells receive light, they can spend their auxins
        # literally each cell needs to raytrace to a light source
        # upon receiving the light, it slowly depreciates the amount of auxins it has
        # other cells can pass it auxins if 
        # how will curvature of final outward mesh handle things like where branch nodes meet their parents?
        #  since the tip only drops a growing surface cell, it will be included as a neighbor to the cells dropped by the tip's parent branch
        
    def start(self):
        self.cur_slice = self.branch.append(Slice(self.cell_res, start_radius=self.start_radius, center=self.loc, normal=self.direction))    
    
    def update_q(self):
        rq = rot_q(self.direction)
        return rq

    # Actions
    
    def photolocate(self, strength=0.04):
        #negage = 1.0 if self.age == 0 else 1.0 / self.age
        #self.direction = self.direction + (self.light_axis * strength * negage)
        self.direction = self.direction.lerp(self.light_axis, strength)
        
    def geolocate(self, strength=0.02):
        #negage = 1.0 if self.age == 0 else 1.0 / self.age
        #self.direction = self.direction + (self.gravity_axis * strength * negage)
        self.direction = self.direction.lerp(-self.gravity_axis, strength)
            
    def grow(self):
        # Replace with NN

        # cheating without using hormones to control direction
        self.photolocate()
        self.geolocate()

        self.last_loc = self.loc
        self.loc = self.loc + (self.direction * self.speed)
        self.rq = self.update_q()
        
        # Lay down slice
        self.cur_slice = self.branch.append(Slice(self.cell_res, start_radius=self.start_radius, center=self.loc, normal=self.direction))
        for slice in self.branch:
            slice.grow()
        
        self.age += 1
        self.speed *= self.speed_decay
        return self.bifurcate()

    def bifurcate(self):
        if self.age % self.bifurc_period == 0:
            vects = self.bifurcate_dir()
            return vects
        else:
            return None
    # Util
    
    def bifurcate_dir(self):
        # returns a list of directions for new tips to grow in
        # use direction of growth's normal for lat
        v1 = self.direction
        # use number of bifurcations as longitudinal slice width for branch direction
        mp2 = math.pi * 2
        r = mp2 / self.bifurcations
        p = mp2 * self.phase
        o = []
        for i in range(0, self.bifurcations):
            x = math.sin(r * i + p)
            y = math.cos(r * i + p)
            v2 = mathutils.Vector((x, y, 0.0))
            # Rotate v2 so that v1 is it's (x,y) plane's normal
            # ie: make v2 orthogonal to v1 (the direction of growth for this tip)
            v2.rotate(self.rq) # = self.normal_transpose(v2, v1)
            v2 = v2.lerp(v1, self.bifurc_inclination)
            o.append(v2 + self.loc)
        self.phase += self.biphase_offset
        return o
        
class Shoot(Tip):
    def __init__(self, branch, loc, dir=(0.0, 0.0, 1.0), speed=0.45, hormones=[], data={}, bifurcation=(4, 2, 0.33, 0.618, 0.4, 0.8), cell_res=8):
        super().__init__(branch, loc, dir=dir, speed=speed, hormones=hormones, data=data, bifurcation=bifurcation, cell_res=cell_res)
        # Shoots are positively phototropic (towards the light), negatively geotropic (away from gravity)
        # Shoots react to certain hormones in different ways (auxins are what cause the above)
        # ie: in the cells dropped, the auxins accumulate on a shaded side
        # the cells will be able to share auxins with it's neighbors
        # depending on the calculated light the cell is receiving
        # as the auxins will accumulate mostly in the side that is
        #   a) in the shade
        #   b) in the direction of gravity
        # causing the negative effect because auxins generate growth 
        # causing the cells to grow faster in the growth direction
        
class Root(Tip):
    def __init__(self, branch, loc, dir=(0.0, 0.0, 1.0), speed=0.3, hormones=[], data={}, bifurcation=(4, 3, 0.5, 0.618, 0.4, 0.8), cell_res=8):
        super().__init__(branch, loc, dir=dir, speed=speed, hormones=hormones, data=data, bifurcation=bifurcation, cell_res=cell_res)
        # Roots are negatively phototropic and positively geotropic
        

# Hormonal system

class Hormone():
    
    # Known as phytofaormones or plant growth substances
    # Control morphological, physiological and biochemical responses at very low concentrations
    # Hormones act locally as they are disolved usually through the cells in the shaft backward
    AUXINS = 1010
    GIBBERELLINS = 1011
    CYTOKININS = 1012
    ETHYLENE = 1013
    ABSCISIC = 1014    #abscisic acid
    BRASSINO = 1015    #brassinosteroids
    OLIGO = 1016       #oligosaccharides
    POLYAMINES = 1017
    
    def __init__(self, type, volume, makeup=None):
        self.type = type
        self.volume = volume
        self.makeup = makeup
        
class Auxin(Hormone):
    
    # Auxins are transported basipetally through polar transport cell to cell
    # they stay away from the light, the cell they are in will grow in growth direction
    # If all neighboring cells in a slice are 
    
    IAA = 1050 # Indole-3 -acetic acid (Synthesized in the Tip) (human synthesized from tryptophan)
                # delays shedding of leafs, promotes seedless fruits
                # stimulates differentiation of xylem and phloem
                # promote formation of lateral and adventitious roots

    # Synthetics (cause flowering, fruiting, stimulate root growth from any cell)
    NAA = 1051 # Synthetic (Napthalene acetic acid)
    IBA = 1052 # Synthetic (Indolebutyric acid)

    # Herbicides
    _24D = 1053 # Synthetic (Dicholorophenoxyacetic acid)
    _245T = 1054 # Synthetic (Tricholrophenoxyacetic acid)
    
    def __init__(self, volume, makeup=IAA):
        super().__init__(Hormone.AUXINS, volume, makeup=makeup)
    
class Cytokinin(Hormone):
    
    # Works together with auxins to promote growth
    # related to cell division and differentiation
    # Synthesized in root apical meristem
    # transported upward
    # promotes lateral bud growth and choloroplast maturation
    # promotes nutrient mobilization from parts to leaves
    # delays leaf senescence (Richmond-Lang effect)
    # Stimulate the release of dormancy of seeds and buds
    # Increases resistance to adverse factors
    
    ZEATIN = 1060  # Trans-6 Purine    
    
    def __init__(self, volume, makeup=ZEATIN):
        super().__init__(Hormone.AUXINS, volume, makeup=makeup)
        
class Gibberellins(Hormone):
    
    # Synthesis of this occurs in young leaves and buds, developing seeds, fruits and roots
    # transported by non-polar method
    
    GAG = 1070  # GAg (gibberelic acid)
    GA1 = 1071
    GA2 = 1072
    GA3 = 1073  # Causes extension of stem due to cell elongation, externally applied induces parthenocarpy
    
    def __init__(self, volume, makeup=GAG):
        super().__init__(Hormone.AUXINS, volume, makeup=makeup)
        
class Ethylene(Hormone):
    
    # Synthesis of this occurs in young leaves and buds, developing seeds, fruits and roots
    # transported by non-polar method
    
    def __init__(self, volume):
        super().__init__(Hormone.ETHYLENE, volume)
        

# Main functions


def link_new_obj(name):
    m = bpy.data.meshes.new("Tree")

    # Instantiates a new object with the previous mesh specified by m
    o = bpy.data.objects.new(name, m)

    # Links object to scene's collection
    scene = bpy.context.scene
    scene.collection.objects.link(o)
    return o, m

def set_mesh(bm, m):
    # Write data to mesh
    bm.to_mesh(m)

    # Destroy bmesh
    bm.free()
    
def make_mesh(name):
    # Instantiates a new type of mesh
    o, m = link_new_obj(name)
    
    # Get bmesh
    bm = bmesh.new()
    bm.from_mesh(m)
    return o, m, bm

def make(name, age=48):
    # Goal ... create a growth matrix of cells 
    # Decouple the actual mesh making part from growth (helps with being able to calculate mesh from history)
    # A branch is a tip's location history stored as a Slice which consists of Cells
    o, m, bm = make_mesh(name)

    bifurc = (8, 1, 0.55, 0.718, 0.5, 0.3)
    random.seed(a='NFTree', version=2)
    cell_res = 4
    dir_init = mathutils.Vector((0.0, 0.0, 1.0))
    
    u1 = Shoot(None, (0.0, 0.0, 0.0), dir=dir_init.normalized(), bifurcation=bifurc, cell_res=cell_res)
    tips = [u1]


    # Growth loop (z = age = generations in CA or whatever time is calculated as)
    nv = None
    for z in range(0, age):
        for t in tips: # For all Tips
            nv = bm.verts.new(t.loc)
            if t.cache_vertex is not None:
                bm.edges.new((nv, t.cache_vertex))
            t.cache_vertex = nv
            eg = t.grow()
            
            if eg is not None:  # Bifurcation
                for e in eg:
                    dir = e - t.loc
                    nt = Shoot(t, tuple(t.last_loc), dir=dir.normalized(), speed=t.speed * t.bifurc_sr, bifurcation=bifurc, cell_res=cell_res)
                    nt.phase = t.phase
                    nt.cache_vertex = nv
                    tips.append(nt)
    
    # Make sure faces can be made by looking up vertices
    #if hasattr(bm.verts, "ensure_lookup_table"): 
    #    bm.verts.ensure_lookup_table()

    #Skin it!
    prevslice, prevvert = None, None
    for tip in tips:
        tv = bm.verts.new(tip.loc)
        lb = len(tip.branch)
        for si, slice in enumerate(tip.branch):
            if True:
                verts = []
                lsc = len(slice.cells)
                for i, cell in enumerate(slice.cells):
                    vert = bm.verts.new(cell.loc)
                    #print(verts)
                    vv = vert if i == 0 else verts[0] if i == lsc else verts[-1]
                    # Vertices for adding faces and the like
                    if si > 0 and i > 0:
                        f = (
                            vert,
                            vv,
                            prevvert[i-1],
                            prevvert[i],
                        )
                        bm.faces.new(f)
                    #else:
                    #    if si == lb - 1:
                    #        print(si, lb)
                    #        print(vert, tv, vv)
                    #        f = (
                    #            vert,
                    #            tv,
                    #            vv
                    #        )
                    #        bm.faces.new(f)

                    if si > 0:
                        # Add the cell neighborhood (Should be offloaded to another loop)
                        gn = prevslice.cells[i]
                        cell.add_neighbor(gn)
                        gn.add_neighbor(cell)

                    verts.append(vert)
                prevvert = verts
                prevslice = slice
    
    # Face connectivity kernels (explains a relative n-gon to current vertex)
    #fcon = [0, 1]
    #fconr = [0, -(resolution - 1), 1, resolution]
    
    # Add all faces to the mesh
    #mod = resolution
    #for i in range(0, len(bm.verts)):
    #    if i < len(bm.verts) - resolution:
    #        fo = []
    #        f = fconr if i % mod == resolution - 1 else fcon
    #        for c in f:
    #            fo.append(bm.verts[i + c])
    #        bm.faces.new(tuple(fo))
            

    bm.verts.index_update()
            
    print("Final Tips:", len(tips))
    set_mesh(bm, m)
    
make("Tree")