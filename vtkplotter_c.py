#!E:\venvs\telemed36\Scripts\python.exe
#
from __future__ import division, print_function
from vtkplotter import Plotter, ProgressBar
from vtkplotter.mesh import Mesh
from vtkplotter.volume import Volume
from vtkplotter import settings, printc, getColor, humansort, __version__
from vtkplotter import vtkio, utils, datadir
import vtk
import sys, argparse, os

print(__version__)

#################################################################################################
class MyArgs:
    def __init__(self):
        self.files = []
        self.color = None
        self.alpha = 1
        self.wireframe = False
        self.point_size = -1
        self.showedges = False ##
        self.lighting = 'default'##
        self.flat = False##
        self.axes_type = 4
        self.no_camera_share = False
        self.legend_off = True
        self.full_screen = False
        self.background = ""
        self.background_grad = None
        self.zoom = 1
        self.quiet = False
        self.multirenderer_mode = False
        self.scrolling_mode = False
        self.ray_cast_mode = False
        self.z_spacing = None
        self.y_spacing = None
        self.x_spacing = None
        self.slicer = False
        self.lego = False
        self.cmap = "jet"
        self.mode = 0

#################################################################################################
vp = None
args = MyArgs()
_alphaslider0, _alphaslider1, _alphaslider2 = 0.33, 0.66, 1  # defaults
kact = 0

#################################################################################################
def _setspacing(img):
    if args.x_spacing:
        ispa = img.GetSpacing()
        img.SetSpacing(ispa[0] * args.x_spacing, ispa[1], ispa[2])
    if args.y_spacing:
        ispa = img.GetSpacing()
        img.SetSpacing(ispa[0], ispa[1] * args.y_spacing, ispa[2])
    if args.z_spacing:
        ispa = img.GetSpacing()
        img.SetSpacing(ispa[0], ispa[1], ispa[2] * args.z_spacing)

def draw_scene():
    global kact

    nfiles = len(args.files)
    if nfiles == 0:
        print("No input files provided.")
        return
    humansort(args.files)

    wsize = "auto"
    if args.full_screen:
        wsize = "full"

    if args.lego:
        if args.background == "":
            args.background = "white"
        if args.axes_type == 4:
            args.axes_type = 1

    if args.background == "":
        args.background = "blackboard"

    if args.background_grad:
        b = getColor(args.background)
        args.background_grad = (b[0]/1.8, b[1]/1.8, b[2]/1.8)

    if args.scrolling_mode and 3 < args.axes_type < 5:  # types 4 and 5 are not good for scrolling
        args.axes_type = 8

    N = None
    if args.multirenderer_mode:
        if nfiles < 201:
            N = nfiles
        if nfiles > 200:
            printc("~lightning Warning: option '-n' allows a maximum of 200 files", c=1)
            printc("         you are trying to load ", nfiles, " files.\n", c=1)
            N = 200
        vp = Plotter(size=wsize, N=N, bg=args.background, bg2=args.background_grad)
        if args.axes_type == 1:
            vp.axes = 0
    else:
        N = nfiles
        vp = Plotter(size=wsize, bg=args.background, bg2=args.background_grad)
        vp.axes = args.axes_type

    vp.verbose = not args.quiet
    vp.sharecam = not args.no_camera_share

    leg = True
    wire = False
    if args.legend_off or nfiles == 1:
        leg = None
    if args.wireframe:
        wire = True

    ########################################################################
    def _showVoxelImage():

        import vtkplotter.colors as vc
        from vtkplotter import Volume
        import numpy as np

        printc("GPU Ray-casting Mode", c="b", invert=1)
        printc("Press j to toggle jittering", c="b", invert=0, bold=0)
        printc("      q to quit.", c="b", invert=0, bold=0)

        vp.show(interactive=0)

        filename = args.files[0]

        vol = vtkio.load(filename)

        if not isinstance(vol, Volume):
            printc("~times Type Error:\nExpected a Volume but loaded", type(vol),
                   'object.', c=1)
            return

        img = vol.imagedata()
        _setspacing(img)

        volume = Volume(img, mode=int(args.mode))
        volumeProperty = volume.GetProperty()

        smin, smax = img.GetScalarRange()
        if smax > 1e10:
            print("Warning, high scalar range detected:", smax)
            smax = abs(10 * smin) + 0.1
            print("         reset to:", smax)

        x0alpha = smin + (smax - smin) * 0.25
        x1alpha = smin + (smax - smin) * 0.5
        x2alpha = smin + (smax - smin) * 1.0

        ############################## color map slider
        # Create transfer mapping scalar value to color
        colorTransferFunction = volumeProperty.GetRGBTransferFunction()
        cmaps = [
            args.cmap,
            "rainbow",
            "viridis",
            "bone",
            "hot",
            "plasma",
            "winter",
            "cool",
            "gist_earth",
            "coolwarm",
            "tab10",
        ]
        cols_cmaps = []
        for cm in cmaps:
            cols = vc.colorMap(range(0, 21), cm, 0, 20)  # sample 20 colors
            cols_cmaps.append(cols)
        Ncols = len(cmaps)
        csl = (0.9, 0.9, 0.9)
        if sum(vc.getColor(args.background)) > 1.5:
            csl = (0.1, 0.1, 0.1)

        def setCMAP(k):
            cols = cols_cmaps[k]
            colorTransferFunction.RemoveAllPoints()
            for i, s in enumerate(np.linspace(smin, smax, num=20, endpoint=True)):
                r, g, b = cols[i]
                colorTransferFunction.AddRGBPoint(s, r, g, b)

        setCMAP(0)

        def sliderColorMap(widget, event):
            sliderRep = widget.GetRepresentation()
            k = int(sliderRep.GetValue())
            sliderRep.SetTitleText(cmaps[k])
            setCMAP(k)

        w1 = vp.addSlider2D(
            sliderColorMap,
            0,
            Ncols - 1,
            value=0,
            showValue=0,
            title=cmaps[0],
            c=csl,
            pos=[(0.8, 0.05), (0.965, 0.05)],
        )
        w1.GetRepresentation().SetTitleHeight(0.018)

        ############################## alpha sliders
        # Create transfer mapping scalar value to opacity
        opacityTransferFunction = volumeProperty.GetScalarOpacity()

        def setOTF():
            opacityTransferFunction.RemoveAllPoints()
            opacityTransferFunction.AddPoint(smin, 0.0)
            opacityTransferFunction.AddPoint(smin + (smax - smin) * 0.1, 0.0)
            opacityTransferFunction.AddPoint(x0alpha, _alphaslider0)
            opacityTransferFunction.AddPoint(x1alpha, _alphaslider1)
            opacityTransferFunction.AddPoint(x2alpha, _alphaslider2)

        setOTF()

        def sliderA0(widget, event):
            global _alphaslider0
            _alphaslider0 = widget.GetRepresentation().GetValue()
            setOTF()

        w0 = vp.addSlider2D(
            sliderA0, 0, 1, value=_alphaslider0, pos=[(0.84, 0.1), (0.84, 0.26)], c=csl, showValue=0
        )

        def sliderA1(widget, event):
            global _alphaslider1
            _alphaslider1 = widget.GetRepresentation().GetValue()
            setOTF()

        w1 = vp.addSlider2D(
            sliderA1, 0, 1, value=_alphaslider1, pos=[(0.89, 0.1), (0.89, 0.26)], c=csl, showValue=0
        )

        def sliderA2(widget, event):
            global _alphaslider2
            _alphaslider2 = widget.GetRepresentation().GetValue()
            setOTF()

        w2 = vp.addSlider2D(
            sliderA2, 0, 1, value=_alphaslider2, pos=[(0.96, 0.1), (0.96, 0.26)], c=csl, showValue=0,
            title="Opacity levels",
        )
        w2.GetRepresentation().SetTitleHeight(0.016)

        # add a button
        def buttonfuncMode():
            s = volume.mode()
            snew = (s + 1) % 2
            volume.mode(snew)
            bum.switch()

        bum = vp.addButton(
            buttonfuncMode,
            pos=(0.7, 0.035),
            states=["composite", "max proj."],
            c=["bb", "gray"],
            bc=["gray", "bb"],  # colors of states
            font="arial",
            size=16,
            bold=0,
            italic=False,
        ).status(int(args.mode))

        def keyfuncJitter(key):  # toggle jittering
            if key != "j":
                return
            if volume.jittering() is not None:
                s = int(volume.jittering())
                snew = (s + 1) % 2
                volume.jittering(snew)
                vp.interactor.Render()

        volume.jittering(True)
        vp.keyPressFunction = keyfuncJitter  # make it known to Plotter class

        def CheckAbort(obj, event):
            if obj.GetEventPending() != 0:
                obj.SetAbortRender(1)

        vp.window.AddObserver("AbortCheckEvent", CheckAbort)

        # add histogram of scalar
        from vtkplotter.pyplot import cornerHistogram

        dims = img.GetDimensions()
        nvx = min(100000, dims[0] * dims[1] * dims[2])
        np.random.seed(0)
        idxs = np.random.randint(0, min(dims), size=(nvx, 3))
        data = []
        for ix, iy, iz in idxs:
            d = img.GetScalarComponentAsFloat(ix, iy, iz, 0)
            data.append(d)

        plot = cornerHistogram(
            data, bins=40, logscale=1, c="gray", bg="gray", pos=(0.78, 0.065)
        )
        plot.GetPosition2Coordinate().SetValue(0.197, 0.20, 0)
        plot.SetNumberOfXLabels(2)
        plot.GetXAxisActor2D().SetFontFactor(0.8)
        plot.GetProperty().SetOpacity(0.5)

        vp.add(plot)
        vp.add(volume)

        vp.show(viewup="z", zoom=1.2, interactive=1)
        w0.SetEnabled(0)
        w1.SetEnabled(0)
        w2.SetEnabled(0)

    ##########################################################
    # special case of SLC/TIFF volumes with -g option
    if args.ray_cast_mode:
        # print('DEBUG special case of SLC/TIFF volumes with -g option')
        if args.axes_type in [1, 2, 3]:
            vp.axes = 4
        wsize = "auto"
        if args.full_screen:
            wsize = "full"
        _showVoxelImage()
        return

    ##########################################################
    # special case of SLC/TIFF/DICOM volumes with --slicer option
    elif args.slicer:
        # print('DEBUG special case of SLC/TIFF/DICOM volumes with --slicer option')

        filename = args.files[0]
        img = vtkio.load(filename).imagedata()

        ren1 = vtk.vtkRenderer()
        renWin = vtk.vtkRenderWindow()
        renWin.AddRenderer(ren1)
        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(renWin)

        im = vtk.vtkImageResliceMapper()
        im.SetInputData(img)
        im.SliceFacesCameraOn()
        im.SliceAtFocalPointOn()
        im.BorderOn()

        ip = vtk.vtkImageProperty()
        ip.SetInterpolationTypeToLinear()

        ia = vtk.vtkImageSlice()
        ia.SetMapper(im)
        ia.SetProperty(ip)

        ren1.AddViewProp(ia)
        ren1.SetBackground(0.6, 0.6, 0.7)
        renWin.SetSize(900, 900)

        iren = vtk.vtkRenderWindowInteractor()
        style = vtk.vtkInteractorStyleImage()
        style.SetInteractionModeToImage3D()
        iren.SetInteractorStyle(style)
        renWin.SetInteractor(iren)

        renWin.Render()
        cam1 = ren1.GetActiveCamera()
        cam1.ParallelProjectionOn()
        ren1.ResetCameraClippingRange()
        cam1.Zoom(1.3)
        renWin.Render()

        printc("Slicer Mode:", invert=1, c="m")
        printc(
            """Press  SHIFT+Left mouse    to rotate the camera for oblique slicing
           SHIFT+Middle mouse  to slice perpendicularly through the image
           Left mouse and Drag to modify luminosity and contrast
           X                   to Reset to sagittal view
           Y                   to Reset to coronal view
           Z                   to Reset to axial view
           R                   to Reset the Window/Levels
           Q                   to Quit.""",
            c="m",
        )

        iren.Start()
        return

    ########################################################################
    # normal mode for single VOXEL file with Isosurface Slider or LEGO mode
    elif nfiles == 1 and (
        ".slc" in args.files[0]
        or ".vti" in args.files[0]
        or ".tif" in args.files[0]
        or ".mhd" in args.files[0]
        or ".nrrd" in args.files[0]
        or ".dem" in args.files[0]
    ):
        # print('DEBUG normal mode for single VOXEL file with Isosurface Slider or LEGO mode')
        image = vtkio.loadImageData(args.files[0])
        scrange = image.GetScalarRange()
        threshold = (scrange[1] - scrange[0]) / 3.0 + scrange[0]
        _setspacing(image)
        vol = Volume(image)

        if args.lego:
            sliderpos = ((0.79, 0.035), (0.975, 0.035))
            slidertitle = ""
            showval = False
            act = vol.legosurface(vmin=threshold, cmap=args.cmap)
            act.addScalarBar(horizontal=1, vmin=scrange[0], vmax=scrange[1])
        else:
            sliderpos = 4
            slidertitle = "isosurface threshold"
            showval = True
            cf = vtk.vtkContourFilter()
            cf.SetInputData(image)
            cf.ComputeScalarsOff()
            ic = "gold"
            if args.color is not None:
                if args.color.isdigit():
                    ic = int(args.color)
                else:
                    ic = args.color
            cf.SetValue(0, threshold)
            cf.Update()
            act = Mesh(cf.GetOutput(), c=ic, alpha=args.alpha).wireframe(args.wireframe)
            if args.flat:
                act.flat()
            else:
                act.phong()
            if args.lighting != 'default':
                act.lighting(args.lighting)
            if args.showedges:
                act.GetProperty().SetEdgeVisibility(1)
                act.GetProperty().SetLineWidth(0.1)

        ############################## threshold slider
        bacts = dict()
        def sliderThres(widget, event):

            prevact = vp.actors[0]
            prevact_prp = prevact.GetProperty()
            wval =  widget.GetRepresentation().GetValue()
            wval_2 = utils.precision(wval, 2)
            if wval_2 in bacts.keys():
                a = bacts[wval_2] # reusing the already available mesh
            else:                 # else generate it
                if args.lego:
                    a = vol.legosurface(vmin=wval, cmap=args.cmap)
                else:
                    cf = vtk.vtkContourFilter()
                    cf.SetInputData(image)
                    cf.ComputeScalarsOff()
                    cf.SetValue(0, wval)
                    cf.Update()
                    a = Mesh(cf.GetOutput(), ic, alpha=act.alpha())
                bacts.update({wval_2: a}) # store it
                #print('generated', wval_2, wval, len(bacts.keys()))

            act_prp = a.GetProperty()
            act_prp.SetRepresentation(prevact_prp.GetRepresentation())
            act_prp.SetInterpolation(prevact_prp.GetInterpolation())
            act_prp.SetEdgeVisibility(prevact_prp.GetEdgeVisibility())
            act_prp.SetColor(prevact_prp.GetColor())
            act_prp.SetOpacity(prevact_prp.GetOpacity())
            act_prp.SetAmbient(prevact_prp.GetAmbient())
            act_prp.SetDiffuse(prevact_prp.GetDiffuse())
            act_prp.SetSpecular(prevact_prp.GetSpecular())
            act_prp.SetSpecularPower(prevact_prp.GetSpecularPower())
            act_prp.SetSpecularColor(prevact_prp.GetSpecularColor())

            vp.renderer.RemoveActor(prevact)
            vp.renderer.AddActor(a)
            vp.actors = [a]

        dr = scrange[1] - scrange[0]
        vp.addSlider2D(
            sliderThres,
            scrange[0] + 0.02 * dr,
            scrange[1] - 0.02 * dr,
            value=threshold,
            pos=sliderpos,
            title=slidertitle,
            showValue=showval,
        )

        def CheckAbort(obj, event):
            if obj.GetEventPending() != 0:
                obj.SetAbortRender(1)
        vp.window.AddObserver("AbortCheckEvent", CheckAbort)

        #act.legend(leg)
        vp.show(act, zoom=args.zoom, viewup="z")
        return

    ########################################################################
    # NORMAL mode for single or multiple files, or multiren mode, or numpy scene
    elif nfiles == 1 or (not args.scrolling_mode):
        # print('DEBUG NORMAL mode for single or multiple files, or multiren mode')

        ##########################################################
        # loading a full scene
        if ".npy" in args.files[0] and nfiles == 1:
            import numpy

            data = numpy.load(args.files[0], allow_pickle=True, encoding='latin1').flatten()[0]
            if "objects" in data.keys():
                vp = vtkio.importWindow(args.files[0])
                vp.show()
                return
        ##########################################################

        actors = []
        for i in range(N):
            f = args.files[i]

            colb = args.color
            if args.color is None and N > 1:
                colb = i

            actor = vp.load(f, c=colb, alpha=args.alpha)

            if isinstance(actor, vtk.vtkActor):

                if isinstance(actor, Mesh):
                    actors.append(actor)
                    actor.wireframe(wire)
                    actor.lighting(args.lighting)
                    if args.flat:
                        actor.flat()
                    else:
                        actor.phong()

                    if leg:
                        actor.legend(os.path.basename(f))

                    if args.point_size > 0:
                        try:
                            actor.GetProperty().SetPointSize(args.point_size)
                            actor.GetProperty().SetRepresentationToPoints()
                        except AttributeError:
                            pass

                    if args.showedges:
                        try:
                            actor.GetProperty().SetEdgeVisibility(1)
                            actor.GetProperty().SetLineWidth(0.1)
                            actor.GetProperty().SetRepresentationToSurface()
                        except AttributeError:
                            pass

                    if args.multirenderer_mode:
                        actor._legend = None
                        vp.show(actor, at=i, interactive=False, zoom=args.zoom)
                        vp.actors = actors

        if args.multirenderer_mode:
            vp.interactor.Start()
        else:
            vp.show(interactive=True, zoom=args.zoom)
        return

    ########################################################################
    # scrolling mode  -s
    else:
        #print("DEBUG scrolling mode  -s")
        import numpy

        n = len(args.files)
        pb = ProgressBar(0, n)

        # load files first
        for i, f in enumerate(args.files):
            pb.print("..loading")

            ic = None
            if args.color is not None:
                if args.color.isdigit():
                    ic = int(args.color)
                else:
                    ic = args.color

            actor = vp.load(f, c=ic, alpha=args.alpha)
            if hasattr(actor, "wireframe"):  # can be Image or volume
                actor.wireframe(wire)
                if args.point_size > 0:
                    actor.pointSize(args.point_size)
                if args.showedges:
                    actor.lw(0.1)

                actor.lighting(args.lighting)
                if args.flat:
                    actor.flat()
                else:
                    actor.phong()

        # calculate max actors bounds
        bns = []
        for a in vp.actors:
            if a and a.GetPickable():
                b = a.GetBounds()
                if b:
                    bns.append(b)
        if len(bns):
            max_bns = numpy.max(bns, axis=0)
            min_bns = numpy.min(bns, axis=0)
            vbb = (min_bns[0], max_bns[1], min_bns[2], max_bns[3], min_bns[4], max_bns[5])

        # show the first
        saveacts = vp.actors
        vp.show(vp.actors[0], interactive=False, zoom=args.zoom)
        vp.actors = saveacts

        if isinstance(vp.axes_instances[0], vtk.vtkCubeAxesActor):
            vp.axes_instances[0].SetBounds(vbb)
        cb = (1, 1, 1)
        if numpy.sum(vp.renderer.GetBackground()) > 1.5:
            cb = (0.1, 0.1, 0.1)

        # define the slider
        for a in vp.actors:
            a.off()
        vp.actors[0].on()

        def sliderf(widget, event):
            global kact
            kactnew = int(widget.GetRepresentation().GetValue())
            if kactnew == kact:
                return
            vp.actors[kact].off()

            prevact_prp = vp.actors[kact].GetProperty()
            act_prp = vp.actors[kactnew].GetProperty()
            if hasattr(act_prp, 'SetRepresentation'):
                act_prp.SetRepresentation(prevact_prp.GetRepresentation())
                act_prp.SetInterpolation(prevact_prp.GetInterpolation())
                act_prp.SetEdgeVisibility(prevact_prp.GetEdgeVisibility())
                act_prp.SetColor(prevact_prp.GetColor())
                act_prp.SetSpecular(prevact_prp.GetSpecular())
                act_prp.SetSpecularPower(prevact_prp.GetSpecularPower())
                act_prp.SetSpecularColor(prevact_prp.GetSpecularColor())
            act_prp.SetOpacity(prevact_prp.GetOpacity())
            act_prp.SetAmbient(prevact_prp.GetAmbient())
            act_prp.SetDiffuse(prevact_prp.GetDiffuse())

            vp.actors[kactnew].on()

            kact = kactnew
            printc("Scrolling Mode:", c="y", invert=1, end="")
            printc(" showing file nr.", kact, args.files[kact].split("/")[-1],
                   "\r", c="y", bold=0, end="")

        vp.addSlider2D(sliderf, 0, n - 1, pos=4, c=cb, showValue=False)

        vp.show(interactive=True, zoom=args.zoom)
        print()
        return


#################################################################################
# GUI or argparse
#################################################################################
if len(sys.argv) == 1 or os.name == "ntt":  # no args are passed, pop up GUI

    # print('DEBUG gui started')
    if sys.version_info[0] > 2:
        from tkinter import Frame, Tk, BOTH, Label, Scale, Checkbutton, BooleanVar, StringVar
        from tkinter.ttk import Button, Style, Combobox, Entry
        from tkinter import filedialog as tkFileDialog
    else:
        from Tkinter import Frame, Tk, BOTH, Label, Scale, Checkbutton, BooleanVar, StringVar
        from ttk import Button, Style, Combobox, Entry
        import tkFileDialog

    ######################
    class vtkplotterGUI(Frame):
        def __init__(self, parent):
            Frame.__init__(self, parent, bg="white")
            self.parent = parent
            self.filenames = []
            self.noshare = BooleanVar()
            self.flat = BooleanVar()
            self.xspacing = StringVar()
            self.yspacing = StringVar()
            self.zspacing = StringVar()
            self.background_grad = BooleanVar()
            self.initUI()

        def initUI(self):
            self.parent.title("vtkplotter")
            self.style = Style()
            self.style.theme_use("clam")
            self.pack(fill=BOTH, expand=True)

            ############import
            Button(self, text="Import Files", command=self._importCMD, width=15).place(x=115, y=17)

            ############meshes
            Frame(root, height=1, width=398, bg="grey").place(x=1, y=60)
            Label(self, text="Meshes", fg="white", bg="green", font=("Courier 11 bold")).place(x=20, y=65)

            # color
            Label(self, text="Color:", bg="white").place(x=30, y=98)
            colvalues = ('by scalar', 'gold','red','green','blue', 'coral','plum','tomato')
            self.colorCB = Combobox(self, state="readonly", values=colvalues, width=10)
            self.colorCB.current(0)
            self.colorCB.place(x=100, y=98)

            # mode
            modvalues = ('surface', 'surf. & edges','wireframe','point cloud')
            self.surfmodeCB = Combobox(self, state="readonly", values=modvalues, width=14)
            self.surfmodeCB.current(0)
            self.surfmodeCB.place(x=205, y=98)

            # alpha
            Label(self, text="Alpha:", bg="white").place(x=30, y=145)
            self.alphaCB = Scale(
                self,
                from_=0,
                to=1,
                resolution=0.02,
                bg="white",
                length=220,
                orient="horizontal",
            )
            self.alphaCB.set(1.0)
            self.alphaCB.place(x=100, y=125)

            # lighting
            Label(self, text="Lighting:", bg="white").place(x=30, y=180)
            lightvalues = ('default','metallic','plastic','shiny','glossy')
            self.lightCB = Combobox(self, state="readonly", values=lightvalues, width=10)
            self.lightCB.current(0)
            self.lightCB.place(x=100, y=180)
            # shading phong or flat
            self.flatCB = Checkbutton(self, text="flat shading", var=self.flat, bg="white")
            #self.flatCB.select()
            self.flatCB.place(x=210, y=180)

            # rendering arrangement
            Label(self, text="Arrange as:", bg="white").place(x=30, y=220)
            schemevalues = ('superpose (default)','mesh browser', 'n sync-ed renderers')
            self.schememodeCB = Combobox(self, state="readonly", values=schemevalues, width=20)
            self.schememodeCB.current(0)
            self.schememodeCB.place(x=160, y=220)

            # share cam
            self.noshareCB = Checkbutton(self, text="independent cameras",
                                         variable=self.noshare, bg="white")
            self.noshareCB.place(x=160, y=245)


            ############volumes
            Frame(root, height=1, width=398, bg="grey").place(x=1, y=275)
            Label(self, text="Volumes", fg="white", bg="blue", font=("Courier 11 bold")).place(x=20, y=280)

            # mode
            Label(self, text="Rendering mode:", bg="white").place(x=30, y=310)
            modevalues = (
                "isosurface (default)",
                "composite",
                "maximum proj",
                "lego",
                "slicer",
            )
            self.modeCB = Combobox(self, state="readonly", values=modevalues, width=20)
            self.modeCB.current(0)
            self.modeCB.place(x=160, y=310)

            Label(self, text="Spacing factors:", bg="white").place(x=30, y=335)
            self.xspacingCB = Entry(self, textvariable=self.xspacing, width=3)
            self.xspacing.set('1.0')
            self.xspacingCB.place(x=160, y=335)
            self.yspacingCB = Entry(self, textvariable=self.yspacing, width=3)
            self.yspacing.set('1.0')
            self.yspacingCB.place(x=210, y=335)
            self.zspacingCB = Entry(self, textvariable=self.zspacing, width=3)
            self.zspacing.set('1.0')
            self.zspacingCB.place(x=260, y=335)


            ############## options
            Frame(root, height=1, width=398,bg="grey").place(x=1, y=370)
            Label(self, text="Options", fg='white', bg="brown", font=("Courier 11 bold")).place(x=20, y=375)

            # backgr color
            Label(self, text="Background color:", bg="white").place(x=30, y=405)
            bgcolvalues = ("white", "lightyellow", "azure", "blackboard", "black")
            self.bgcolorCB = Combobox(self, state="readonly", values=bgcolvalues, width=9)
            self.bgcolorCB.current(3)
            self.bgcolorCB.place(x=160, y=405)
            # backgr color gradient
            self.backgroundGradCB = Checkbutton(self, text="gradient",
                                                variable=self.background_grad, bg="white")
            self.backgroundGradCB.place(x=255, y=405)

            ################ render button
            Frame(root, height=1, width=398, bg="grey").place(x=1, y=437)
            Button(self, text="Render", command=self._run, width=15).place(x=115, y=454)


        def _importCMD(self):
            ftypes = [
                ("All files", "*"),
                ("VTK files", "*.vtk"),
                ("VTK files", "*.vtp"),
                ("VTK files", "*.vts"),
                ("VTK files", "*.vtu"),
                ("Surface Mesh", "*.ply"),
                ("Surface Mesh", "*.obj"),
                ("Surface Mesh", "*.stl"),
                ("Surface Mesh", "*.off"),
                ("Surface Mesh", "*.facet"),
                ("Volume files", "*.tif"),
                ("Volume files", "*.slc"),
                ("Volume files", "*.vti"),
                ("Volume files", "*.mhd"),
                ("Volume files", "*.nrrd"),
                ("Volume files", "*.nii"),
                ("Volume files", "*.dem"),
                ("Picture files", "*.png"),
                ("Picture files", "*.jpg"),
                ("Picture files", "*.bmp"),
                ("Picture files", "*.jpeg"),
                ("Geojson files", "*.geojson"),
                ("DOLFIN files", "*.xml.gz"),
                ("DOLFIN files", "*.xml"),
                ("DOLFIN files", "*.xdmf"),
                ("Neutral mesh", "*.neu*"),
                ("GMESH", "*.gmsh"),
                ("Point Cloud", "*.pcd"),
                ("3DS", "*.3ds"),
                ("Numpy scene file", "*.npy"),
            ]
            self.filenames = tkFileDialog.askopenfilenames(parent=root, filetypes=ftypes)
            args.files = list(self.filenames)


        def _run(self):

            from vtkplotter.docs import tips
            tips()

            args.files = list(self.filenames)
            if self.colorCB.get() == "by scalar":
                args.color = None
            else:
                if self.colorCB.get() == 'red':
                    args.color = 'crimson'
                elif self.colorCB.get() == 'green':
                    args.color = 'limegreen'
                elif self.colorCB.get() == 'blue':
                    args.color = 'darkcyan'
                else:
                    args.color = self.colorCB.get()

            args.alpha = self.alphaCB.get()

            args.wireframe = False
            args.showedges = False
            args.point_size = 0
            if self.surfmodeCB.get() == 'point cloud':
                args.point_size = 2
            elif self.surfmodeCB.get() == 'wireframe':
                args.wireframe = True
            elif self.surfmodeCB.get() == 'surf. & edges':
                args.showedges = True
            else:
                pass # normal surface mode

            args.lighting = self.lightCB.get()
            args.flat = self.flat.get()

            args.no_camera_share = self.noshare.get()
            args.background = self.bgcolorCB.get()

            args.background_grad = None
            if self.background_grad.get():
                b = getColor(args.background)
                args.background_grad = (b[0]/1.8, b[1]/1.8, b[2]/1.8)

            args.multirenderer_mode = False
            args.scrolling_mode = False
            if self.schememodeCB.get() == "n sync-ed renderers":
                args.multirenderer_mode = True
            elif self.schememodeCB.get() == "mesh browser":
                args.scrolling_mode = True

            args.ray_cast_mode = False
            args.lego = False
            args.slicer = False
            args.lego = False
            args.mode = 0
            if self.modeCB.get() == "composite":
                args.ray_cast_mode = True
                args.mode = 0
            elif self.modeCB.get() == "maximum proj":
                args.ray_cast_mode = True
                args.mode = 1
            elif self.modeCB.get() == "slicer":
                args.slicer = True
            elif self.modeCB.get() == "lego":
                args.lego = True

            args.x_spacing = None
            args.y_spacing = None
            args.z_spacing = None
            if self.xspacing.get() != '1.0': args.x_spacing = float(self.xspacing.get())
            if self.yspacing.get() != '1.0': args.y_spacing = float(self.yspacing.get())
            if self.zspacing.get() != '1.0': args.z_spacing = float(self.zspacing.get())

            draw_scene()
            if os.name == "nt":
                exit()
            if settings.plotter_instance:
                settings.plotter_instance.close()

    root = Tk()
    root.geometry("360x500")
    app = vtkplotterGUI(root)

    def tkcallback(event):
        #printc("xy cursor position:", event.x, event.y, event.char)
        if event.char == 'q':
            root.destroy()

    app.bind("<Key>", tkcallback)
    app.focus_set()
    app.pack()

    if os.name == "nt" and len(sys.argv) > 1:
        app.filenames = sys.argv[1:]
        print("Already", len(app.filenames), "files loaded.")

    root.mainloop()


else:  ################################################################################################# command line mode

    pr = argparse.ArgumentParser(description="version "+str(__version__)+""" -
                                 check out home page https://github.com/marcomusy/vtkplotter""")
    pr.add_argument('files', nargs='*',             help="Input filename(s)")
    pr.add_argument("-c", "--color", type=str,      help="mesh color [integer or color name]", default=None, metavar='')
    pr.add_argument("-a", "--alpha",    type=float, help="alpha value [0-1]", default=1, metavar='')
    pr.add_argument("-w", "--wireframe",            help="use wireframe representation", action="store_true")
    pr.add_argument("-p", "--point-size", type=float, help="specify point size", default=-1, metavar='')
    pr.add_argument("-e", "--showedges",            help="show a thin line on mesh edges", action="store_true")
    pr.add_argument("-k", "--lighting", type=str,   help="metallic, plastic, shiny or glossy", default='default', metavar='')
    pr.add_argument("-K", "--flat",                 help="use flat shading", action="store_true")
    pr.add_argument("-x", "--axes-type", type=int,  help="specify axes type [0-5]", default=4, metavar='')
    pr.add_argument("-i", "--no-camera-share",      help="do not share camera in renderers", action="store_true")
    pr.add_argument("-l", "--legend-off",           help="do not show legends", action="store_true")
    pr.add_argument("-f", "--full-screen",          help="full screen mode", action="store_true")
    pr.add_argument("-bg","--background", type=str, help="background color [integer or color name]", default='', metavar='')
    pr.add_argument(      "--background-grad",      help="use background color gradient", action="store_true")
    pr.add_argument("-z", "--zoom", type=float,     help="zooming factor", default=1, metavar='')
    pr.add_argument("-q", "--quiet",                help="quiet mode, less verbose", default=False, action="store_false")
    pr.add_argument("-n", "--multirenderer-mode",   help="Multi renderer Mode: files go to separate renderers", action="store_true")
    pr.add_argument("-s", "--scrolling-mode",       help="Scrolling Mode: use arrows to scroll files", action="store_true")
    pr.add_argument("-g", "--ray-cast-mode",        help="GPU Ray-casting Mode for 3D image files", action="store_true")
    pr.add_argument("-gx", "--x-spacing", type=float, help="Volume x-spacing factor [1]", default=None, metavar='')
    pr.add_argument("-gy", "--y-spacing", type=float, help="Volume y-spacing factor [1]", default=None, metavar='')
    pr.add_argument("-gz", "--z-spacing", type=float, help="Volume z-spacing factor [1]", default=None, metavar='')
    pr.add_argument("--slicer",                     help="Slicer Mode for 3D image files", action="store_true")
    pr.add_argument("--lego",                       help="Voxel rendering for 3D image files", action="store_true")
    pr.add_argument("--cmap",                       help="Voxel rendering color map name", default='jet', metavar='')
    pr.add_argument("--mode",                       help="Voxel rendering composite mode", default=0, metavar='')
    pr.add_argument("-r", "--run",                  help="Run example from vtkplotter-examples", metavar='')
    pr.add_argument("--list",                       help="List examples in vtkplotter-examples", action="store_true")
    args = pr.parse_args()

    if args.run:
        import glob
        exfiles = [f for f in glob.glob(datadir.replace('data','') + "**/*.py", recursive=True)]
        matching = [s for s in exfiles if (args.run.lower() in os.path.basename(s).lower() and "__" not in s)]
        matching = list(sorted(matching))
        nmat = len(matching)
        if nmat == 0:
            printc("No matching example found containing string:", args.run, c=1)
            printc(" Use vtkplotter --list to show available scripts.", c=1)
            printc(" Current datadir is:", datadir, c=1)
            exit(1)

        if nmat > 1:
            printc("\nSelect one of", nmat, "matching scripts:", c='y', italic=1)

        for mat in matching[:25]:
            printc(os.path.basename(mat).replace('.py',''), c='y', italic=1, end=' ')
            with open(mat) as fm:
                lline = ''.join(fm.readlines(60))
                lline = lline.replace('\n','').replace('\'','').replace('\"','').replace('-','')
                line = lline[:56] #cut
                if line.startswith('from'): line=''
                if line.startswith('import'): line=''
                if len(lline) > len(line):
                    line += '..'
                if len(line)>5:
                    printc('-', line,  c='y', bold=0, italic=1)
                else:
                    print()

        if nmat>25:
            printc('...', c='y')

        if nmat > 1:
            exit(0)

        if args.no_camera_share: # -i option to dump the full code
            print()
            with open(matching[0]) as fm:
                codedump = fm.readlines()
            for line in codedump:
                printc(line.strip(), c='cyan', italic=1, bold=0)
            print()

        printc("(in", os.path.dirname(matching[0])+')', c='y', bold=0, italic=1)
        os.system('python3 ' + matching[0])

    elif args.list:
        print()
        printc("Available examples are:", box='-')
        expath = datadir.replace('data','')

        import glob
        exfiles = [(f, os.path.basename(f))
                    for f in glob.glob(expath + "**/*.py", recursive=True)]
        nl = 4

        if not len(exfiles):
            printc("vtkplotter-example not installed?")
            printc("> pip install -U git+https://github.com/marcomusy/vtkplotter-examples")
            exit()

        printc("Basic examples:", c='g', bold=1, underline=1)
        scs = []
        for f,bn in exfiles:
            if "basic" in f:
                lb = ' ' if (len(scs)+1)%nl else '\n'
                scs.append(lb+bn.replace('.py',''))
        printc("".join(scs), c='g', bold=0)

        printc("Advanced examples:", c='y', bold=1, underline=1)
        scs = []
        for f,bn in exfiles:
            if "advanced" in f:
                lb = ' ' if (len(scs)+1)%nl else '\n'
                scs.append(lb+bn.replace('.py',''))
        printc("".join(scs), c='y', bold=0)

        printc("Simulation examples:", c='m', bold=1, underline=1)
        scs = []
        for f,bn in exfiles:
            if "simulation" in f:
                lb = ' ' if (len(scs)+1)%nl else '\n'
                scs.append(lb+bn.replace('.py',''))
        printc("".join(scs), c='m', bold=0)

        printc("Plotting 2D examples:", c='w', bold=1, underline=1)
        scs = []
        for f,bn in exfiles:
            if "pyplot" in f:
                lb = ' ' if (len(scs)+1)%nl else '\n'
                scs.append(lb+bn.replace('.py',''))
        printc("".join(scs), c='w', bold=0)

        printc("Volumetric examples:", c='b', bold=1, underline=1)
        scs = []
        for f,bn in exfiles:
            if "volumetric" in f:
                lb = ' ' if (len(scs)+1)%nl else '\n'
                scs.append(lb+bn.replace('.py',''))
        printc("".join(scs), c='b', bold=0)

        printc("Other examples:", c='cyan', bold=1, underline=1)
        scs = []
        for f,bn in exfiles:
            if "other" in f and "dolfin" not in f and "trimesh" not in f:
                lb = ' ' if (len(scs)+1)%nl else '\n'
                scs.append(lb+bn.replace('.py',''))
        printc("".join(scs), c='cyan', bold=0)

        printc("      Dolfin examples:", c='r', bold=1, underline=1)
        scs = []
        for f,bn in exfiles:
            if "dolfin" in f:
                lb = ' ' if (len(scs)+1)%nl else '\n'
                scs.append(lb+bn.replace('.py',''))
        printc("".join(scs), c='r', bold=0)

        printc("      Trimesh examples:", c='m', bold=1, underline=1)
        scs = []
        for f,bn in exfiles:
            if "trimesh" in f:
                lb = ' ' if (len(scs)+1)%nl else '\n'
                scs.append(lb+bn.replace('.py',''))
        printc("".join(scs), c='m', bold=0)
        print()

    else:
        draw_scene()
