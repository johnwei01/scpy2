from traits.api import HasTraits, Button, Instance, Range, Float
from traitsui.api import View, Item, VGroup, HGroup, Controller
from tvtk.api import tvtk
from tvtk.pyface.scene_editor import SceneEditor
from tvtk.pyface.scene import Scene
from tvtk.pyface.scene_model import SceneModel


def get_source(obj, target):
    while True:
        for attr in "producer_port","producer","input":
            if hasattr(obj, attr):
                obj = getattr(obj, attr)
                break
        else:
            break
        if isinstance(obj, target):
            break
    return obj


def difference(pd1, pd2):
    bf = tvtk.BooleanOperationPolyDataFilter()
    bf.operation = "difference"
    bf.set_input(0, pd1)
    bf.set_input(1, pd2)
    m = tvtk.PolyDataMapper(input=bf.output, scalar_visibility=False)
    a = tvtk.Actor(mapper=m)
    return bf.output, a


def intersection(pd1, pd2, color=(1.0, 0, 0), width=2.0):
    ipd = tvtk.IntersectionPolyDataFilter()
    ipd.set_input(0, pd1)
    ipd.set_input(1, pd2)
    m = tvtk.PolyDataMapper(input=ipd.output)
    a = tvtk.Actor(mapper=m)
    a.property.diffuse_color = 1.0, 0, 0
    a.property.line_width = 2.0    
    return ipd.output, a


def make_tube(height, radius, resolution, rx=0, ry=0, rz=0):
    cs1 = tvtk.CylinderSource(height=height, radius=radius[0], resolution=resolution)
    cs2 = tvtk.CylinderSource(height=height+0.1, radius=radius[1], resolution=resolution)    
    triangle1 = tvtk.TriangleFilter(input=cs1.output)
    triangle2 = tvtk.TriangleFilter(input=cs2.output)
    tr = tvtk.Transform()
    tr.rotate_x(rx)
    tr.rotate_y(ry)
    tr.rotate_z(rz)
    tf1 = tvtk.TransformFilter(transform=tr, input=triangle1.output)   
    tf2 = tvtk.TransformFilter(transform=tr, input=triangle2.output)   
    bf = tvtk.BooleanOperationPolyDataFilter()
    bf.operation = "difference"
    bf.set_input(0, tf1.output)
    bf.set_input(1, tf2.output)
    m = tvtk.PolyDataMapper(input=bf.output, scalar_visibility=False)
    a = tvtk.Actor(mapper=m)
    return bf.output, a, tf1.output, tf2.output


class TVTKSceneController(Controller):
    def position(self, info):
        super(TVTKSceneController, self).position(info)
        self.model.depth_peeling()


class TubeDemoApp(HasTraits):
    max_radius = Float(1.0)
    ri1 = Range(0.0, 1.0, 0.8)
    ro1 = Range("ri1", "max_radius", 1.0)
    ri2 = Range(0.0, 1.0, 0.4)
    ro2 = Range("ri2", "max_radius", 0.6)
    update = Button("Update")
    scene = Instance(SceneModel, ())
    view = View(
                VGroup(
                    Item(name="scene", editor=SceneEditor(scene_class=Scene)),
                    HGroup("ri1", "ro1"),
                    HGroup("ri2", "ro2"),
                    "update",
                    show_labels=False                    
                ),
                resizable=True,
                height = 500,
                width = 500,
            )
    
    def __init__(self, **kw):
        super(TubeDemoApp, self).__init__(**kw)
        self.plot()
        
    def plot(self):
        t1, a1, o1, i1 = make_tube(5.0, [self.ro1, self.ri1], 32)
        t2, a2, o2, i2 = make_tube(5.0, [self.ro2, self.ri2], 32, rx=90)
        th1, ah1 = difference(t1, i2)
        th2, ah2 = difference(t2, i1)
        ah1.property.opacity = 0.6
        ah2.property.opacity = 0.6
        _, aline = intersection(t1, t2)
    
        #bind events
        self.co1 = get_source(o1, tvtk.CylinderSource)
        self.ci1 = get_source(i1, tvtk.CylinderSource)
        self.co2 = get_source(o2, tvtk.CylinderSource)
        self.ci2 = get_source(i2, tvtk.CylinderSource)
        self.scene.add_actors([ah1, ah2, aline])
        #self.sync_trait("ro1", self.co1, alias="radius", mutual=False)
        #self.sync_trait("ri1", self.ci1, alias="radius", mutual=False)
        #self.sync_trait("ro2", self.co2, alias="radius", mutual=False)
        #self.sync_trait("ri2", self.ci2, alias="radius", mutual=False)
    
    def _update_fired(self):
        self.co1.radius = self.ro1
        self.ci1.radius = self.ri1
        self.co2.radius = self.ro2
        self.ci2.radius = self.ri2
        self.scene.render_window.render()
        
    def depth_peeling(self):
        rw = self.scene.render_window
        renderer = self.scene.renderer
        rw.alpha_bit_planes = 1
        rw.multi_samples = 0
        renderer.use_depth_peeling = 1
        renderer.maximum_number_of_peels = 100
        renderer.occlusion_ratio = 0.1   

if __name__ == "__main__":
    app = TubeDemoApp()
    #app.edit_traits(handler=TVTKSceneController(app))
    app.configure_traits(handler=TVTKSceneController(app))