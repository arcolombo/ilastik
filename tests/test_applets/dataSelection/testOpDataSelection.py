###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import os
import numpy
import vigra
import lazyflow
import h5py
from lazyflow.graph import OperatorWrapper
from ilastik.applets.dataSelection.opDataSelection import OpDataSelection, DatasetInfo

import tempfile

class TestOpDataSelection_Basic():
    
    @classmethod
    def setupClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.testNpyFileName = os.path.join(cls.tmpdir, 'testImage1.npy')
        cls.testPngFileName = os.path.join(cls.tmpdir, 'testImage2.png')
        cls.projectFileName = os.path.join(cls.tmpdir, 'testProject.ilp')

        # Create a couple test images of different types
        cls.imgData2D = numpy.zeros((10, 11))
        for x in range(0,10):
            for y in range(0,11):
                cls.imgData2D[x,y] = x+y
        numpy.save(cls.testNpyFileName, cls.imgData2D)

        cls.imgData2Dc = numpy.zeros((100, 200, 3))
        for x in range(cls.imgData2Dc.shape[0]):
            for y in range(cls.imgData2Dc.shape[1]):
                for c in range(cls.imgData2Dc.shape[2]):
                    cls.imgData2Dc[x, y, c] = (x + y) % 256
        vigra.impex.writeImage(cls.imgData2Dc, cls.testPngFileName)
        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName)
        cls.projectFile.create_group('DataSelection')
        cls.projectFile['DataSelection'].create_group('local_data')
        # Use the same data as the png data (above)
        cls.projectFile['DataSelection/local_data'].create_dataset('dataset1', data=cls.imgData2Dc)
        cls.projectFile.flush()

    @classmethod
    def teardownClass(cls):
        cls.projectFile.close()
        for path in [ cls.testNpyFileName, cls.testPngFileName, cls.projectFileName ]:
            try:
                os.remove(path)
            except:
                pass
    
    def testBasic2D(self):
        graph = lazyflow.graph.Graph()
        reader = OperatorWrapper( OpDataSelection, graph=graph )
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue( os.getcwd() )
        reader.ProjectDataGroup.setValue( 'DataSelection/local_data' )
        
        # Create a list of dataset infos . . .
        datasetInfos = []
        
        # npy
        info = DatasetInfo()
        # Will be read from the filesystem since the data won't be found in the project file.
        info.location = DatasetInfo.Location.ProjectInternal
        info.filePath = self.testNpyFileName
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)
        
        # png
        info = DatasetInfo()
        info.location = DatasetInfo.Location.FileSystem
        info.filePath = self.testPngFileName
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)

        reader.Dataset.setValues(datasetInfos)

        # Read the test files using the data selection operator and verify the contents
        imgData2D = reader.Image[0][...].wait()
        imgData2Dc = reader.Image[1][...].wait()

        # Check the file name output
        print reader.ImageName[0].value
        assert reader.ImageName[0].value == self.testNpyFileName
        assert reader.ImageName[1].value == self.testPngFileName

        # Check raw images
        assert imgData2D.shape == (10,11,1)
        for y in range(imgData2D.shape[0]):
            for x in range(imgData2D.shape[1]):
                assert imgData2D[y,x,0] == x+y

        assert imgData2Dc.shape == (200, 100, 3)
        for y in range(imgData2Dc.shape[0]):
            for x in range(imgData2Dc.shape[1]):
                for c in range(imgData2Dc.shape[2]):
                    assert imgData2Dc[y, x, c] == (x + y) % 256

#
#    def testColorInversion(self):
#        graph = lazyflow.graph.Graph()
#        reader = OpDataSelection(graph=graph)
#        reader.ProjectFile.setValue(self.projectFile)
#        reader.WorkingDirectory.setValue( os.getcwd() )
#        
#        # Create a list of dataset infos . . .
#        datasetInfos = []
#        
#        # npy inverted
#        info = DatasetInfo()
#        info.location = DatasetInfo.Location.FileSystem
#        info.filePath = self.testNpyFileName
#        info.internalPath = ""
#        info.invertColors = True
#        info.convertToGrayscale = False
#        datasetInfos.append(info)
#        
#        # png inverted
#        info = DatasetInfo()
#        info.location = DatasetInfo.Location.FileSystem
#        info.filePath = self.testPngFileName
#        info.internalPath = ""
#        info.invertColors = True
#        info.convertToGrayscale = False
#        datasetInfos.append(info)
#
#        reader.Dataset.setValues(datasetInfos)
#
#        invertedNpyData = reader.ProcessedImages[0][...].wait()
#        invertedPngData = reader.ProcessedImages[1][...].wait()
#
#        # Check inverted images
#        assert invertedNpyData.shape == self.imgData2D.shape + (1,) # (Reader appends a channel dimension for this data)
#        for x in range(invertedNpyData.shape[0]):
#            for y in range(invertedNpyData.shape[1]):
#                assert invertedNpyData[x,y,0] == 255-self.imgData2D[x,y]
#        
#        assert invertedPngData.shape == self.imgData2Dc.shape
#        for x in range(invertedPngData.shape[0]):
#            for y in range(invertedPngData.shape[1]):
#                for c in range(invertedPngData.shape[2]):
#                    assert invertedPngData[x,y,c] == 255-self.imgData2Dc[x,y,0]
#
#    def testGrayscaling(self):
#        graph = lazyflow.graph.Graph()
#        reader = OpDataSelection(graph=graph)
#        reader.ProjectFile.setValue(self.projectFile)
#        reader.WorkingDirectory.setValue( os.getcwd() )
#        
#        # Create a list of dataset infos . . .
#        datasetInfos = []
#        
#        # png grayscale
#        info = DatasetInfo()
#        info.location = DatasetInfo.Location.FileSystem
#        info.filePath = self.testPngFileName
#        info.internalPath = ""
#        info.invertColors = False
#        info.convertToGrayscale = True
#        datasetInfos.append(info)
#
#        reader.Dataset.setValues(datasetInfos)
#        
#        grayscalePngData = reader.ProcessedImages[0][...].wait()
#
#        # Check grayscale conversion 
#        assert grayscalePngData.shape == self.imgData2Dc.shape[:-1] + (1,) # Only one channel
#        for x in range(grayscalePngData.shape[0]):
#            for y in range(grayscalePngData.shape[1]):
#                # (See formula in OpRgbToGrayscale)
#                assert grayscalePngData[x,y,0] == int(numpy.round(  0.299*self.imgData2Dc[x,y,0]
#                                                                  + 0.587*self.imgData2Dc[x,y,1]
#                                                                  + 0.114*self.imgData2Dc[x,y,2] ))
#    def testInvertedGrayscaling(self):
#        graph = lazyflow.graph.Graph()
#        reader = OpDataSelection(graph=graph)
#        reader.ProjectFile.setValue(self.projectFile)
#        reader.WorkingDirectory.setValue( os.getcwd() )
#        
#        # Create a list of dataset infos . . .
#        datasetInfos = []
#
#        # png grayscale & inverted
#        info = DatasetInfo()
#        info.location = DatasetInfo.Location.FileSystem
#        info.filePath = self.testPngFileName
#        info.internalPath = ""
#        info.invertColors = True
#        info.convertToGrayscale = True
#        datasetInfos.append(info)
#
#        reader.Dataset.setValues(datasetInfos)
#        
#        invertedGrayscalePngData = reader.ProcessedImages[0][...].wait()
#        
#
#        # Check inverted grayscale conversion 
#        assert invertedGrayscalePngData.shape == (100, 200, 1)
#        for x in range(invertedGrayscalePngData.shape[0]):
#            for y in range(invertedGrayscalePngData.shape[1]):
#                # (See formula in OpRgbToGrayscale)
#                assert invertedGrayscalePngData[x,y,0] == int(numpy.round(  0.299*(255-self.imgData2Dc[x,y,0])
#                                                                          + 0.587*(255-self.imgData2Dc[x,y,1]) 
#                                                                          + 0.114*(255-self.imgData2Dc[x,y,2]) ))
    def testProjectLocalData(self):
        graph = lazyflow.graph.Graph()
        reader = OperatorWrapper( OpDataSelection, graph=graph )
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue( os.getcwd() )
        reader.ProjectDataGroup.setValue( 'DataSelection/local_data' )
        
        # Create a list of dataset infos . . .
        datasetInfos = []

        # From project
        info = DatasetInfo()
        info.location = DatasetInfo.Location.ProjectInternal
        info.filePath = "This string should be ignored..."
        info._datasetId = 'dataset1' # (Cheating a bit here...)
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)

        reader.Dataset.setValues(datasetInfos)

        projectInternalData = reader.Image[0][...].wait()

        assert projectInternalData.shape == self.imgData2Dc.shape
        assert (projectInternalData == self.imgData2Dc).all()


if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE': 1})
































