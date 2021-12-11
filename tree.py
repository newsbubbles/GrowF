# GrowF: Grow Function
# Original Author: Nathaniel D. Gibson

# Copyright 2021 Solana Wallet: 2VEvjzNYHG56fJHNcUPnMTpi1cuRTipqgu78YNtZhnAK

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import bpy
import bmesh
import mathutils
import math
import random
import types

_Z = mathutils.Vector((0.0, 0.0, 1.0)) # Eventually will be moved, just a way to know which way is the template normal

# Change the below variable to False if you want to only model the branching structure of your organism
_params_live = True

# Param is the basic unit of growth instruction, it uses any infinite wave function(s) to define step-increments of value, along with limits of that value
class Param():
    def __init__(self, value, vmin=None, vmax=None, func=None, steps=None, freq=1.0, sequence=None):
        self.value = value
        self.orig = value
        self.min = vmin
        self.max = vmax
        self.func = func
        self.steps = steps
        self.freq = freq
        self.sequence = sequence    # Use sequence for a repeating list

        self.cfunc = 0
        self.count = 0
        
    def next_func(self):
        lf = len(self.func)
        f = self.func[self.cfunc]
        o = f if type(f) != types.FunctionType else f(self)
        self.cfunc += 1
        if self.cfunc >= lf:
            self.cfunc = 0
        return o
        
    def next(self):
        if not _params_live:
            return self.value
        if self.max is not None:
            if type(self.func) == types.FunctionType:
                self.value = self.func(self)
            else:
                self.value = self.next_func()
        self.count += 1
        return self.value
    
    def first(self):
        return self.orig
    
    def copy(self, inherit_count=True):
        p = Param(self.orig, vmin=self.min, vmax=self.max, func=self.func, steps=self.steps, freq=self.freq, sequence=self.sequence)
        if inherit_count:
            p.count = self.count
            p.cfunc = self.cfunc
        return p
    
# DNA acts like the API for growth parameters, allowing copying, mixing, mutation, and serialization of any parameter space
class DNA():
    def __init__(self, namespace, data=None):
        self.namespace = namespace  # Having a namespace allows different random seeds based on names
                                    # should have the effect of chanigng all random phenomena so that
                                    # the same DNA creates the same exact organism, only slightly different
                                    # because randomness in the growth process can have great effects on outcome
                                    # Think of it like a multiverse space of infinite multiverses in which same DNA, different outcome
        self.data = {}
        if data is not None:
            self.add_data(data)

    def put(self, key, d):
        self.data[key] = d
        return d
        
    def get(self, key):
        return self.data[key]
    
    def add_data(self, data):
        for k, d in data.items():
            self.data[k] = d
            
    def serialize(self):
        return None

    def unserialize(self):
        return None
    
    def get_copy(self, mutation_rate=0.001):
        return None

# Cell is a representation of collaborative growth and needs to be laid down on a 3D growth lattice like a Slice
class Cell():
    def __init__(self, x, y, dna=None, z=0.0, center=None, vector_up=None):
        self.x = x
        self.y = y
        self.z = z
        self.center = center                                                    # the center or parent cell's location
        self.vector_up = vector_up                                              # what this cell knows to be "up" or the opposite of gravity
        self.origin = mathutils.Vector((x, y, z))                               # the vector representing the origin or starting point at birth
        self.origv = None if self.center is None else self.origin - self.center # the vector representing original growth orientation
        
        self.loc = mathutils.Vector((x, y, z))
        self.v = mathutils.Vector((0.0, 0.0, 0.0))
        self.nloc = self.loc
        self.nv = self.v
        
        self.maxdev = 1
        self.mindist = Param(0.001) if dna is None else dna.get("cell")[2].copy()
        self.ease = Param(0.05) if dna is None else dna.get("cell")[3].copy()
        self.ease_away = Param(0.01) if dna is None else dna.get("cell")[4].copy()
        self.ease2, self.ease_away2 = 1.0, 1.0
        self.age = 0
        self.color = mathutils.Color((0.3, 1.0, 0.2))
        self.rate_growth_radial = 5.0
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
        # TODO: Option to make cell behavior completely controlled by evolved NN
        self.ease.next()
        self.ease_away.next()
        
        self.move_random(flat=False)
        self.grow_radial()
        self.move_boids()
        #self.move_rest()
        
        self.growth_counters()
        
    def grow_radial(self):
        v = self.origv * (1 / (self.age + 1))
        self.nv = v * self.rate_growth_radial
        
    def growth_counters(self):
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
            
    def move_away(self, point, limit=0):
        # point should be a tuple of 3 floats (x, y, z)
        v = point # mathutils.Vector(point)
        a = v - self.loc
        if limit == 0 or a < limit:
            n = a * self.ease_away.value * self.ease_away2
            self.nv = self.nv + n
        
    def move_boids(self):
        rn = 1 / len(self.neighbors)
        al, av = self.loc, self.v
        for n in self.neighbors:
            al = al + n.loc
            av = av + n.v
            #self.nv = self.nv + (-n.loc * self.ease_away)
            self.move_away(n.loc)
        al = al * rn
        av = av * rn
        ad = al - self.loc
        sr = 0.1
        self.nv = self.nv + (av * self.ease.value * self.ease2)

    # Cell interactions        

    def give(self, other, hormone, volume_ratio):
        return None


class Slice():
    def __init__(self, neighbors, start_radius=(1, 1), detail_depth=0.1, center=mathutils.Vector((0.0, 0.0, 0.0)), normal=mathutils.Vector((0.0, 0.0, 1.0)), rate_growth_radial=None, mult_growth_radial=1.0, dna=None):
        self.neighbors = neighbors
        self.center = center
        self.orientation = normal
        self.rot_matrix = rot_q(self.orientation)
        self.radius = start_radius
        self.rate_growth_radial = Param(1.0, vmin=1.0, vmax=10.0, func=p_random) if rate_growth_radial is None else rate_growth_radial
        self.rate_ease_radial = Param(0.1) if dna is None else dna.get("slice")[5].copy()
        self.rate_ease_away = Param(0.01) if dna is None else dna.get("slice")[6].copy()
        self.mult_growth_radial = mult_growth_radial
        self.ddepth = detail_depth / 2
        self.dna = dna
        self.cells = []
        
        self.init_circular()
        self.link()
    
    def init_circular(self):
        r = math.pi * 2 / self.neighbors
        for i in range(0, self.neighbors):
            x = math.sin(i * r) * self.radius[0]
            y = math.cos(i * r) * self.radius[1]
            v = mathutils.Vector((x, y, 0.0))
            v.rotate(self.rot_matrix.normalized())
            v = v + self.center
            c = Cell(v.x, v.y, z=v.z, center=self.center, dna=self.dna)
            c.rate_growth_radial = self.growth_rate(i)
            c.ease2 = self.rate_ease_radial.next()
            c.ease_away2 = self.rate_ease_away.next()
            self.cells.append(c)
            
    def growth_rate(self, index):
        # get the growth rate for the cell
        # index can be used to set a curve over the cells dropped in growth rate
        # rgr * curve[index]
        return self.rate_growth_radial.next() * self.mult_growth_radial
        
    def link(self, kernel=[-1, 1]): #[-3, -2, -1, 1, 2, 3]):
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
    def __init__(self, branch, loc, dir=(0.0, 0.0, 1.0), speed=0.3, hormones=[], data={}, bifurcation=(4, 3, 0.5, 0.618, 0.4, 0.8, 0, 0, 10), cell_res=8, start_at_0=True, start_radius=(0.01, 0.01), cell_growth=None, dna=None):
        
        br = dna.get("branch")
        
        # Initial configuration (can be changed by factors that affect the tip)
        self.parent = branch
        self.direction = mathutils.Vector(dir)
        self.rq = self.update_q()
        self.bifurc_period = br[0].copy()         # How many growth steps happen between bifurcations/branching
        self.bifurcations = br[1].copy()          # How many new tips grow out of this
        self.biphase_offset = br[2].copy()        # The radial offset angle (0.0-1.0) of successive bifurcations
        self.bifurc_sr = br[3].copy()             # Initial speed ratio for bifurcated child tips
        self.bifurc_inclination = br[4].copy()    # Inclination of child tips
        self.bifurc_radius_ratio = br[5].copy()   # The ratio of 
        self.bifurc_stop = br[6].copy()           # When to stop bifurcations on this branch
        self.stop_age = br[7].copy()              # if set > 0, it will make the branch stop growing after this age
        self.max_generation = br[8]               # Number of bifurcation generations allowed in entire organism
        self.speed = Param(speed) if dna is None else br[9].copy()
        self.speed_decay = Param(0.98) if dna is None else br[10].copy() #, vmin=0.818, vmax=1.16, func=p_random)     # ratio of decay of growth speed per growth
        self.photolocate_ratio = Param(0.04) if dna is None else br[11].copy()
        self.geolocate_ratio = Param(0.02) if dna is None else br[12].copy()
        self.data = data
        self.hormones = hormones    # hormones are dropped as a total of what is available        
        
        # Slices and surface cells
        self.start_radius = start_radius
        self.cell_growth_rate = cell_growth
        self.slice_growth_rate = Param(2.0) if dna is None else dna.get("slice")[4]
        self.branch = []
        self.cell_res = cell_res
        self.cur_slice = None

        # Working parameters (counters, history, etc)
        self.dna = dna
        self.cache_vertex = None
        self.loc = mathutils.Vector(loc)
        self.last_loc = self.loc
        self.phase = 0.0
        self.generation = 0
        self.age = 0
        self.bifurc_count = 0
        
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
        self.new_slice()
            
    def new_slice(self):
        # (1.0, 0.5, 10.0)
        self.cur_slice = self.branch.append(Slice(
            self.cell_res.next(),
            start_radius = self.start_radius,
            center = self.loc, 
            normal = self.direction,
            rate_growth_radial = self.cell_growth_rate,
            mult_growth_radial = self.slice_growth_rate.next(),
            dna = self.dna
        ))
    
    def update_q(self):
        rq = rot_q(self.direction)
        return rq
    
    def can_grow(self):
        return self.stop_age.value == 0 or self.age < self.stop_age.value - 1
    
    def can_bifurcate(self):
        counter = self.bifurc_stop.value == 0 or self.bifurc_count < self.bifurc_stop.value
        gen = self.max_generation.value == 0 or self.generation < self.max_generation.value
        return counter and gen

    # Actions
    
    def photolocate(self):
        if not self.can_grow():
            return False
        #negage = 1.0 if self.age == 0 else 1.0 / self.age
        #self.direction = self.direction + (self.light_axis * strength * negage)
        self.direction = self.direction.lerp(self.light_axis, self.photolocate_ratio.next())
        return True
        
    def geolocate(self):
        if not self.can_grow():
            return False
        #negage = 1.0 if self.age == 0 else 1.0 / self.age
        #self.direction = self.direction + (self.gravity_axis * strength * negage)
        self.direction = self.direction.lerp(-self.gravity_axis, self.geolocate_ratio.next())
        return True
            
    def grow(self):
        # Replace with NN

        # Always grow branch first
        for slice in self.branch:
            slice.grow()

        if self.can_grow():
            # cheating without using hormones to control direction
            self.photolocate()
            self.geolocate()
    
            self.last_loc = self.loc
            self.loc = self.loc + (self.direction * self.speed.next())
            self.rq = self.update_q()
            
            # Lay down slice
            self.new_slice()
            #self.cur_slice = self.branch.append(Slice(self.cell_res, start_radius=self.start_radius, center=self.loc, normal=self.direction, proto_cell=self.proto_cell))
            #self.speed *= self.speed_decay.next()
        
        self.age += 1
        return self.bifurcate()

    def bifurcate(self):
        if self.age % self.bifurc_period.value == 0 and self.can_bifurcate():
            vects = self.bifurcate_dir()
            self.bifurc_count += 1
            self.bifurc_period.next()
            self.bifurcations.next()
            self.biphase_offset.next()
            self.bifurc_sr.next()
            self.bifurc_inclination.next()
            self.bifurc_radius_ratio.next()
            self.bifurc_stop.next()
            self.stop_age.next()
            self.max_generation.next()
            self.speed_decay.next()
            self.photolocate_ratio.next()
            self.geolocate_ratio.next()
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
        r = mp2 / self.bifurcations.value
        p = mp2 * self.phase
        #print(self.bifurcations, r, p, self.phase)
        o = []
        for i in range(0, self.bifurcations.value):
            x = math.sin(r * i + p)
            y = math.cos(r * i + p)
            v2 = mathutils.Vector((x, y, 0.0))
            # Rotate v2 so that v1 is it's (x,y) plane's normal
            # ie: make v2 orthogonal to v1 (the direction of growth for this tip)
            v2.rotate(self.rq) # = self.normal_transpose(v2, v1)
            v2 = v2.lerp(v1, self.bifurc_inclination.value)
            o.append(v2 + self.loc)
        #print(o)
        self.phase += self.biphase_offset.value
        return o
        
class Shoot(Tip):
    def __init__(self, branch, loc, dir=(0.0, 0.0, 1.0), speed=0.45, hormones=[], data={}, bifurcation=(4, 2, 0.33, 0.618, 0.4, 0.8, 0, 0, 10), cell_res=8, start_at_0=True, start_radius=(0.01, 0.01), cell_growth=None, dna=None):
        super().__init__(branch, loc, dir=dir, speed=speed, hormones=hormones, data=data, bifurcation=bifurcation, cell_res=cell_res, start_at_0=start_at_0, start_radius=start_radius, cell_growth=cell_growth, dna=dna)
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
    def __init__(self, branch, loc, dir=(0.0, 0.0, 1.0), speed=0.3, hormones=[], data={}, bifurcation=(4, 3, 0.5, 0.618, 0.4, 0.8, 0, 0, 10), cell_res=8, start_at_0=True, start_radius=(0.01, 0.01), cell_growth=None, dna=None):
        super().__init__(branch, loc, dir=dir, speed=speed, hormones=hormones, data=data, bifurcation=bifurcation, cell_res=cell_res, start_at_0=start_at_0, start_radius=start_radius, cell_growth=cell_growth, dna=dna)
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
        
    # Uses some volume of the hormone 
    def use(self, volume):
        o = self.volume
        v = self.volume - volume
        if v < 0:
            self.volume -= o
            return o
        else:
            self.volume -= volume
            return volume
        
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


        
# Util functions for Params

def prng(value, param):
    return (value * (param.max - param.min)) + param.min

def p_log(param):
    return prng(math.log(param.value - param.min), param)

def p_rat(param):
    return param.value * param.freq

def p_none(param):
    return param.value

def p_sin1(param):
    return prng(math.sin(param.value - param.min) + 1.0, param)

def p_sin(param):
    o = prng((math.sin(param.count * param.freq) + 1.0) * 0.5, param)
    return o
    
def p_square(param):
    return prng((math.sin(param.count * param.freq) + 1.0) * 0.5, param)

def p_square_y(param):
    return prng((math.cos(param.count * param.freq) + 1.0) * 0.5, param)
    
def p_sin2(param):
    return prng(math.sin(param.count * param.value) + 1.0, param)

def p_spike(param):
    return prng(1.0 - abs(math.sin(param.count * param.freq)), param)

def p_spike_y(param):
    return prng(1.0 - abs(math.cos(param.count * param.freq)), param)

def p_bump(param):
    return prng(abs(math.sin(param.count * param.freq)), param)

def p_bump_y(param):
    return prng(abs(math.sin(param.count * param.freq)), param)

def p_rlog(param):
    return prng(math.sin(param.value - param.min) + 1.0, param)

def p_random(param):
    return prng(random.random(), param)

def p_random_int(param):
    return int(p_random(param))

def p_cos1(param):
    return prng(math.cos(param.value - param.min) + 1.0, param)

def p_cos(param):
    return prng(math.cos(param.value * param.freq) + 1.0, param)

def p_tuple_next(bt):
    o = []
    for i in bt:
        o.append(i.next())
    return tuple(o)

def p_tuple_first(bt):
    o = []
    for i in bt:
        o.append(i.first())
    return tuple(o)

# 3D Vector utility functions

def rot_q(v):
    # Returns a Quaternion rotation where a point on an (x, y) plane turns to face vector (v) as the new z axis
    # Use the output of this function as the argument to the mathutils Vector.rotate() function
    return _Z.rotation_difference(v.normalized())

# Mesh functions for bmesh

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

#class Gene():
#    def __init__(self):
  
class Tree():
    def __init__(self, name="Tree", seed_r="GrowF"):
        self.dna = DNA(seed_r)
        self.age = 0
        self.name = name
        self.random_seed = seed_r
        self.tips = []
        
        # Working vars
        self.cell_count = 0
        
    # Seed Construction and Pre-Seed functions
    #  TODO: add a method that loads tips directly from DNA
    
    def add_tip(self, tip):
        tip.dna = self.dna
        self.tips.append(tip)
        
    def set_dna(self, dna):
        self.dna.data = dna.data
        
    # Actions
    
    def plant(self, location=(0.0, 0.0, 0.0)):
        return None
    
    def begin(self):
        # represents one growth step
        bifurc = (8, 2, 0.2, 0.718, 0.5, 0.3, 8, 0, 4)
        # between bifurc, branches, situation, tip growth ratio, tip growth angle, stop branching, stop growing, level depth, speed, speed decay
        bparams = self.dna.put("branch", (
            Param(2, vmin=3, vmax=8, func=p_bump, freq=10),          # section height
            Param(1, vmin=1, vmax=4, func=[2]),                 # branch number
            Param(0.15, vmin=0.0, vmax=0.5, func=p_none),           # radial branch angle
            Param(0.718, vmin=0.9, vmax=1.0, func=p_none),          # tip growth ratio
            Param(0.5, vmin=0.0, vmax=0.9, func=p_sin, freq=3),            # branch inclination
            Param(0.3, vmin=0.0, vmax=0.8, func=p_none),            # radius ratio
            Param(0, vmin=5, vmax=12, func=p_none),                 # stop branching at growth steps
            Param(0, vmin=0, vmax=20, func=p_none),                 # stop growing at growth steps
            Param(4, vmin=3, vmax=20, func=p_none),                 # level depth
            Param(0.25, vmin=0.1, vmax=2.0, func=p_none),           # speed
            Param(0.98, vmin=0.618, vmax=1.11, func=p_none, freq=5), # speed decay
            Param(0.04, vmin=-0.2, vmax=0.2, func=p_none, freq=10),  # photolocate ratio
            Param(0.02, vmin=0.02, vmax=0.02, func=p_none, freq=10) # geolocate_ratio
        ))
        #(x scale, y scale, x growth matrix, y growth matrix, growth rate all, rate ease radial, rate ease away)
        start_radius = self.dna.put("slice", (
            Param(0.01, vmin=0.005, vmax=0.05, func=[p_square,p_none], freq=100),
            Param(0.01, vmin=0.005, vmax=0.05, func=p_square_y, freq=3),
            Param(1.0,  vmin=1.0, vmax=5.0, func=p_square, freq=100),
            Param(1.0,  vmin=1.0, vmax=5.0, func=p_square_y, freq=100),
            Param(1.0, vmin=1.0, vmax=2.0, func=p_none, freq=100),
            Param(1.0, vmin=0.1, vmax=2.0, func=p_none, freq=0.5),
            Param(1.0, vmin=0.1, vmax=2.0, func=p_none, freq=0.5)
        ))
        # cell growth, cell resolution, minimum neighbor distance, cell "toward" movement ease, cell ease for "away"
        cell = self.dna.put("cell", (
            Param(3.0, vmin=0.5, vmax=8.0, func=[p_square,p_none], freq=8),
            Param(24), #, vmin=8, vmax=80, func=p_random_int)
            Param(0.001, vmin=0.001, vmax=0.002, func=p_none),
            Param(0.05, vmin=0.01, vmax=0.8, func=p_none, freq=3),
            Param(0.01, vmin=0.01, vmax=0.2, func=p_none, freq=3)
        ))
        cell_growth, cell_res = cell[0], cell[1]
        
        self.cell_count = cell_res.value
        # Comment this out if you want to set specific starting bifurcation parameters
        #bifurc = p_tuple_next(bparams)
        #srad = p_tuple_next(start_radius)
        
        dir_init = mathutils.Vector((0.0, 0.0, 1.0))

        # print(cell_res, cell_growth)
        u1 = Shoot(None, (0.0, 0.0, 0.0), dir=dir_init.normalized(), dna=self.dna, bifurcation=bifurc, cell_res=cell_res, cell_growth=cell_growth)
        self.tips = [u1]
    
    def grow(self, steps=1):
        bparams = self.dna.get("branch")
        start_radius = self.dna.get("slice")
        cell = self.dna.get("cell")
        cell_growth, cell_res = cell[0], cell[1]

        # Growth loop (z = age = generations in CA or whatever time is calculated as)
        nv = None
        for z in range(0, steps):
            for t in self.tips: # For all Tips
                eg = t.grow()
                self.cell_count += cell_res.next()
                
                if eg is not None:  # Bifurcation
                    bifurc = p_tuple_next(bparams)
                    for e in eg:
                        dir = e - t.loc
                        #bifurc = p_tuple_next(bparams) # Comment out to use uniform bifurcation parameters
                        #srad = p_tuple_next(start_radius)
                        #print(bifurc, t, dir, t.last_loc)
                        #nt = Shoot(t, tuple(t.last_loc), dir=dir.normalized(), dna=self.dna, bifurcation=bifurc, cell_res=cell_res, start_radius=srad, cell_growth=cell_growth)
                        nt = Shoot(t, tuple(t.last_loc), dir=dir.normalized(), dna=t.dna, cell_res=cell_res, cell_growth=cell_growth)
                        nt.phase = t.phase
                        nt.generation = t.generation + 1
                        nt.max_generation = t.max_generation
                        nt.cache_vertex = nv
                        self.tips.append(nt)
            self.age += 1
            
    def make_skeleton(self, bm):
        for t in self.tips:
            nv = bm.verts.new(t.loc)
            if t.cache_vertex is not None:
                bm.edges.new((nv, t.cache_vertex))
            t.cache_vertex = nv


    def make(self, steps=1):
        # Goal ... create a growth matrix of cells 
        # Decouple the actual mesh making part from growth (helps with being able to calculate mesh from history)
        # A branch is a tip's location history stored as a Slice which consists of Cells
        o, m, bm = make_mesh(self.name)

        # Set the random seed, can be set also by the GA
        random.seed(a=self.random_seed, version=2)

        self.begin()
        self.grow(steps=steps)
        
        # The skinning loop I created below is set up to not use the commented out code here
        # It is considered a slowdown to ensure the lookup table while creating a mesh in blender
        # so if you edit the algorithm and decide to 
        # Make sure faces can be made by looking up vertices
        #if hasattr(bm.verts, "ensure_lookup_table"): 
        #    bm.verts.ensure_lookup_table()

        #Skin it!
        prevslice, prevvert = [], []
        for tip in self.tips:
            tv = bm.verts.new(tip.loc)
            lb = len(tip.branch)
            for si, slc in enumerate(tip.branch):
                if True:
                    verts = []
                    lsc = len(slc.cells)
                    for i, cell in enumerate(slc.cells):
                        vert = bm.verts.new(cell.loc)
                        vv = vert if i == 0 else verts[0] if i == lsc else verts[-1]
                        if si > 0:
                            if i > 0:
                                if i < lsc:
                                    f = (
                                        vert,           # 0, 0
                                        vv,             # 0, -1
                                        prevvert[i-1],  # -1, -1
                                        prevvert[i],    # -1, 0
                                    )
                                    bm.faces.new(f)
                                    if i == lsc - 1:
                                        f = (
                                            verts[0],
                                            vert,
                                            prevvert[-1],
                                            prevvert[0]
                                        )
                                        bm.faces.new(f)

                        if si > 0:
                            # Add the cell neighborhood (Should be offloaded to another loop)
                            gn = prevslice.cells[i]
                            cell.add_neighbor(gn)
                            gn.add_neighbor(cell)

                        verts.append(vert)
                    prevvert = verts
                    prevslice = slc                

        bm.verts.index_update()
                
        print("Final Tips:", len(self.tips))
        print("Final Cells:", self.cell_count)
        set_mesh(bm, m)
    
t = Tree(seed_r="GrowF")
t.make(steps=10)

#t.grow(20)