# Growth ... author: Nathaniel D. Gibson

import bpy
import bmesh
import mathutils
import math
import random

_Z = mathutils.Vector((0.0, 0.0, 1.0))

def toward(point, q):
    # Transposes an (x*, y*, z=0) vector plane to orient in the direction of another vector
    point.rotate(q)
    return point
    #return v2d.cross(axis)
    #z = mathutils.Vector((0.0, 0.0, 1.0))
    #q = normal.
    #a = mathutils.Vector(origin)
    #n = normal.normalized()
    #o = n.orthogonal()
    #p = point.project(o)
    #return p
    
def rot_q(v):
    return _Z.rotation_difference(v)

class CellCA():
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
        self.age = 0
        self.rate_growth_radial = 2
        self.targets = [] # Can be turned into a way to react to target objects
        #self.w = w
        self.neighbors = []
        
        self.v = self.random_vector()
        
        # Grows outward... can sense 
        
    def random_vector(self, vmax=0.06):
        vx = random.random() * (vmax * 2) - vmax
        vy = random.random() * (vmax * 2) - vmax
        vz = random.random() * (vmax * 2) - vmax
        return mathutils.Vector((vx, vy, vz))
    
    def add_neighbor(self, n):
        self.neighbors.append(n)
        
    def move(self):
        # Replace this all with a NN based GA
        #  INPUTS possible: neighbor data, light sources, scene physics objects, sensors, 
        #    particle systems data, neighbor types, starting location, gravity coefficient
        #  HIDDEN LAYER: up to 10 hidden units
        #  OUTPUT: move x, move y, move z, follow x neighbor, decouple x neighbor
        # GA: When moving, a cell is being generated from the cell that is within... 
        #  this means that genetic mutation can happen on a per cell basis at some point
        # Hormonics
        #   Generating a next cell out eats up growth hormones
        # For now use Boids modified
        # 1. same dir as neighbors
        # 2. Same dir as a light source
        # 3. Toward center of neighbors
        # 4. Don't hit a neighbor
        # ... 
        self.move_random(flat=False)
        self.grow_out()
        self.move_boids()
        #self.move_rest()
        
        self.nloc = self.loc + self.nv
        self.age += 1
            
        
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
        al = al * rn
        av = av * rn
        #print(" avg:", al, av)
        #print("self:", self.loc, self.v)
        ad = al - self.loc
        sr = 0.1
        self.nv = self.nv + (av * self.ease)
        
    def grow_out(self):
        v = self.origv * (1 / (self.age + 1))
        #self.origin = self.origin + v
        self.nv = v
    
    def update(self):
        self.loc = self.nloc
        self.v = self.nv

class SliceCA():
    def __init__(self, neighbors, n=1, start_radius=1, detail_depth=0.1):
        self.neighbors = neighbors
        self.n = n
        self.center = mathutils.Vector((0.0, 0.0, 0.0))
        self.orientation = mathutils.Vector((0.0, 1.0, 1.0))
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
            nv = toward(v, self.rot_matrix)
            print(nv)
            c = CellCA(nv.x, nv.y, z=nv.z, center=self.center)
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
    
    def next(self):
        for v in self.cells:
            v.move()
        for v in self.cells:
            v.update()

def link_new_obj(name):
    m = bpy.data.meshes.new("Tree")

    # Instantiates a new object with the previous mesh specified by m
    o = bpy.data.objects.new(name, m)

    # Links object to scene's collection
    scene = bpy.context.scene
    scene.collection.objects.link(o)
    return o, m

def make_tree(name, resolution=24, age=60, density=5):
    # Instantiates a new type of mesh
    ca = SliceCA(resolution, n=2, start_radius=0.01)
    o, m = link_new_obj(name)
    
    # Get bmesh
    bm = bmesh.new()
    bm.from_mesh(m)

    # Add verts
    for z in range(0, age):
        msh = ca.get_vertices(0.0) #z / density)
        for i, v in enumerate(msh):
            bm.verts.new(v)
    print(bm.verts)
    
    # Make sure faces can be made by looking up vertices
    if hasattr(bm.verts, "ensure_lookup_table"): 
        bm.verts.ensure_lookup_table()
        
    # Face connectivity kernels (explains a relative n-gon to current vertex)
    fcon = [0, 1, resolution + 1, resolution]
    fconr = [0, -(resolution - 1), 1, resolution]
    
    # Add all faces to the mesh
    mod = resolution
    for i in range(0, len(bm.verts)):
        if i < len(bm.verts) - resolution:
            fo = []
            f = fconr if i % mod == resolution - 1 else fcon
            for c in f:
                fo.append(bm.verts[i + c])
            bm.faces.new(tuple(fo))
            

    # Write data to mesh
    bm.to_mesh(m)

    # Destroy bmesh
    bm.free()

make_tree("MyTree")