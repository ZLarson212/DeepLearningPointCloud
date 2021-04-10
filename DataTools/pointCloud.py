from DataTools import defs
import open3d as o3d
import numpy as np
import os
from enum import Enum
from Visualization import visualizer as vizu
from Preprocessing import randomSampler
from Embedding import voxels
from Embedding import pointpillars
import time
from Preprocessing.Clustering import clusterer


class PointCloud:
    #initialize from file path
    def __init__(self, rootpath, pcType, samplingMethod, embeddingSize, embeddingType=defs.EmbeddingType.POINTPILLARS, clusteringType = defs.ClusterType.SKDBSCAN):
        self.viz = vizu.Visualizer()
        self.pcType = pcType
        self.allWithoutFace = np.array([])

        #read in data from file if not augmented
        if rootpath is not None:
            self.rootpath = rootpath
            self.facepath = os.path.join(rootpath, "face_segment.pcd")
            self.allpath = os.path.join(rootpath, "PointCloudCapture.pcd")
            self.face3d = o3d.io.read_point_cloud(self.facepath)
            self.all3d = o3d.io.read_point_cloud(self.allpath)
            self.faceseg = np.asarray(self.face3d.points)
            self.allseg = np.asarray(self.all3d.points)
            self.removeFaceFromAll()

            print("Read in Point Cloud object " + rootpath)
            print("Face seg shape: ", self.faceseg.shape)
            print("All seg shape: ", self.allseg.shape)        

        #establish center face location
        x = (max(self.faceseg[:,0]) - min(self.faceseg[:,0]))/2.0
        y = (max(self.faceseg[:,1]) - min(self.faceseg[:,1]))/2.0
        z = (max(self.faceseg[:,2]) - min(self.faceseg[:,2]))/2.0
        self.center = [x,y,z]

        #Downsampling
        self.randomSampler = randomSampler.RandomSampler()
        self.samplingMethod = samplingMethod
        self.sampleNumber = 1000
        self.downsample()     

        #Clustering
        #self.clusteringType = clusteringType
        #self.clusterPoints()
        self.passableClusters = [self.downsampledAll]

        #Embedding
        self.embeddingType = embeddingType
        self.embeddingSize = embeddingSize
        self.embedPointCloud()

        #Make labels
        self.generateBinaryLabels()

    @classmethod
    def augmentedPointCloud(self, allData, faceData):
        self.faceseg = self.faceData
        self.allWithoutFace = self.allData
        self.allseg = self.vstack(self.faceseg, self.allWithoutFace)

    def removeFaceFromAll(self):
        self.allWithoutFace
        for i in range(len(self.allWithoutFace)):
            if self.allWithoutFace[i] in self.allWithoutFace:
                self.allWithoutFace = np.erase(self.allWithoutFace, i, 0)
                i = i - 1

    def downsample(self):
        if(self.samplingMethod == defs.DownsampleType.RANDOM):
            self.downsampledFace = self.randomSampler.randomlySamplePoints(self.faceseg, self.sampleNumber)
            self.downsampledAll = self.randomSampler.randomlySamplePoints(self.allseg, self.sampleNumber) 
            #self.viz.visualizeFaceAndAllPlot(self.downsampledFace, self.downsampledAll)
            print("Downsampled Face shape: ", self.downsampledFace.shape)
            print("Downsampled All shape: ", self.downsampledAll.shape)
            self.numDsPointsInFace = 0
            self.dsFacePoints = []
            for point in self.downsampledAll:
                if point in self.faceseg:
                    self.dsFacePoints.append(point)
                    self.numDsPointsInFace = self.numDsPointsInFace + 1
            print("Number of points left in face after downsampling: ", self.numDsPointsInFace)
            self.dsFacePoints = np.array(self.dsFacePoints)
            print("Min width: ", min(self.dsFacePoints[:,1]), " Max width: ", max(self.dsFacePoints[:,1]))
            print("Width range: ", (max(self.dsFacePoints[:,1]) - min(self.dsFacePoints[:,1])))
            print("Min height: ", min(self.dsFacePoints[:,2]), " Max height: ", max(self.dsFacePoints[:,2]))
            print("Height range: ", (max(self.dsFacePoints[:,2]) - min(self.dsFacePoints[:,2])))

    def clusterPoints(self):
        self.clusterer = clusterer.Clusterer(self.clusteringType, self.downsampledAll)
        self.clusterer.cluster()
        self.passableClusters = self.clusterer.getClustersWorthKeeping()           

    def embedPointCloud(self):
        if self.embeddingType == defs.EmbeddingType.VOXELS:
            vox = voxels.Voxels(self.embeddingSize)
            self.embedding = vox.voxelate(self.allseg)
        elif self.embeddingType == defs.EmbeddingType.POINTPILLARS:
            print("Running through: ", len(self.passableClusters), " clusters!")
            for cluster in self.passableClusters:
                #TODO- make this work in parallel
                startTime = time.time()
                self.pointPillars = pointpillars.PointPillars(self.downsampledAll)
                self.pillarVector = self.pointPillars.buildPillars()
                endTime = time.time()
                print("Point Pillars time took: ", (endTime - startTime))
        elif self.embeddingType == defs.EmbeddingType.PARABOLAS:
            print("Parabolas")
        else:
            print("Error! Don't recognize embedding type: ", self.embeddingType)

    def generateBinaryLabels(self):
        self.binLabel = []
        for point in self.downsampledAll:
            if point in self.faceseg:
                self.binLabel.append(1)
            else:
                self.binLabel.append(0)

    def generateBoundingBoxLable(self):
        #TODO- make a label for bounding boxes
        pass
