import vigra
from vigra import graphs as vgraph
from vigra import ilastiktools as ilastiktools
import numpy


class NewSegmentor(object):
    def __init__(self, labels = None, volume_feat = None, edgeWeightFunctor = None, progressCallback = None,
                 h5file = None):
        self.object_names = dict()
        self.objects = dict()
        self.object_seeds_fg = dict()
        self.object_seeds_bg = dict()
        self.object_seeds_fg_voxels = dict()
        self.object_seeds_bg_voxels = dict()
        self.bg_priority =dict()
        self.no_bias_below = dict()
        self.object_lut = dict()
        self.hasSeg = False

        if h5file is None:
            self.supervoxelUint32 = labels
            self.volumeFeat = volume_feat.squeeze()
            with vigra.Timer("new rag"):
                self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()
                self.gridSegmentor.preprocessing(self.supervoxelUint32,self.volumeFeat)

            # fixe! which of both??!
            self.nodeNum = self.gridSegmentor.nodeNum()
            self.numNodes = self.nodeNum
       
            self.hasSeg = False
        else:
            self.numNodes = h5file.attrs["numNodes"]
            self.nodeNum = self.numNodes
            self.supervoxelUint32 = h5file['labels'][:]

            self.gridSegmentor = ilastiktools.GridSegmentor_3D_UInt32()

            graphS = h5file['graph'][:]
            edgeWeights = h5file['edgeWeights'][:]
            nodeSeeds = h5file['nodeSeeds'][:]
            resultSegmentation = h5file['resultSegmentation'][:]

            print "self.supervoxelUint32",type(self.supervoxelUint32),self.supervoxelUint32.dtype,self.supervoxelUint32.shape
            print "graphS",type(graphS),graphS.dtype,graphS.shape
            print "edgeWeights",type(edgeWeights),edgeWeights.dtype,edgeWeights.shape
            print "nodeSeeds",type(nodeSeeds),nodeSeeds.dtype,nodeSeeds.shape
            print "resultSegmentation",type(resultSegmentation),resultSegmentation.dtype,resultSegmentation.shape

            self.gridSegmentor.preprocessingFromSerialization(labels=self.supervoxelUint32,
                serialization=graphS, edgeWeights=edgeWeights, nodeSeeds=nodeSeeds, 
                resultSegmentation=resultSegmentation)

            self.hasSeg = resultSegmentation.max()>0

    def run(self, unaries, prios = None, uncertainty="exchangeCount",
            moving_average = False, noBiasBelow = 0, **kwargs):
        self.gridSegmentor.run(float(prios[1]),float(noBiasBelow))
        seg = self.gridSegmentor.getSuperVoxelSeg()
        print seg
        self.hasSeg = True


    def addSeeds(self, roi, brushStroke):
        roiBegin  = roi.start[1:4]
        roiEnd  = roi.stop[1:4]
        roiShape = [e-b for b,e in zip(roiBegin,roiEnd)]
        brushStroke = brushStroke.reshape(roiShape)
        self.gridSegmentor.addSeeds(brushStroke=brushStroke,roiBegin=roiBegin, 
                                    roiEnd=roiEnd, maxValidLabel=2)

    def getVoxelSegmentation(self, roi, out = None):
        return self.gridSegmentor.getSegmentation(roiBegin=roi.start[1:4],roiEnd=roi.stop[1:4], out=out)


    def setSeeds(self,fgSeeds, bgSeeds):
        self.gridSegmentor.setSeeds(fgSeeds, bgSeeds)

    def getSuperVoxelSeg(self):
        return  self.gridSegmentor.getSuperVoxelSeg()

    def getSuperVoxelSeeds(self):
        return  self.gridSegmentor.getSuperVoxelSeeds()

    def saveH5(self, filename, groupname, mode="w"):
        print "saving segmentor to %r[%r] ..." % (filename, groupname)
        f = h5py.File(filename, mode)
        try:
            f.create_group(groupname)
        except:
            pass
        h5g = f[groupname]
        self.saveH5G(h5g)

    def saveH5G(self, h5g):
        """        g = h5g
                g.attrs["numNodes"] = self.numNodes
                g.attrs["edgeWeightFunctor"] = self._edgeWeightFunctor
                g.create_dataset("labels", data = self.regionVol)



                cdef np.ndarray[dtype=np.int32_t, ndim = 2] indices = np.ndarray((self.graph.maxArcId()+1,2),dtype=np.int32)
                cdef np.ndarray[dtype=np.float32_t, ndim = 1] data = np.ndarray((self.graph.maxArcId()+1,),dtype=np.float32)
                cdef NodeIt node
                cdef OutArcIt arcit
                cdef int a,b,i

                node = NodeIt(deref(self.graph))
                i = 0
                while node != INVALID:
                    arcit = OutArcIt(deref(self.graph),Node(node))
                    while arcit != INVALID:
                        a = self.graph.id(self.graph.source(arcit))
                        b = self.graph.id(self.graph.target(arcit))
                        indices[i,0] = a
                        indices[i,1] = b
                        data[i] = deref(self.arcMap)[arcit]
                        i += 1
                        inc(arcit)
                    inc(node)
                
                g.create_dataset("coo_indices",data=indices)
                g.create_dataset("coo_data",data=data)
                g.create_dataset("regions", data=self._regionVol)
                g.create_dataset("regionCenter", data=self._regionCenter)
                g.create_dataset("regionSize", data=self._regionSize)
                g.create_dataset("seeds",data = self._seeds)
                g.create_dataset("objects",data = self._objects)

                sg = g.create_group("objects_seeds")
                
                g.file.flush()
                
                # delete old attributes
                for k in sg.attrs.keys():
                    del sg.attrs[k]
                  

                # insert new attributes
                for k,v in self.object_names.items():
                      print "   -> saving object %r with Nr=%r" % (k,v)
                      sg.attrs[k] = v
                      og = sg.create_group(k)
                      og.create_dataset("foreground", data = self.object_seeds_fg[k])
                      og.create_dataset("background", data = self.object_seeds_bg[k])

                if self._rawData is not None:
                    g.create_dataset("raw",data=self._rawData)

                g.file.flush()
                print "   done"
        """
        g = h5g

        g.attrs["numNodes"] = self.numNodes


        g.create_dataset("labels", data = self.supervoxelUint32)

        gridSeg = self.gridSegmentor
        g.create_dataset("graph", data = gridSeg.serializeGraph())
        g.create_dataset("edgeWeights", data = gridSeg.getEdgeWeights())
        g.create_dataset("nodeSeeds", data = gridSeg.getNodeSeeds())
        g.create_dataset("resultSegmentation", data = gridSeg.getResultSegmentation())
        
        g.file.flush()