"""Cluster Class Module """
from threading import Thread, Lock
import time
import os
from node import Node, App
import logging
import sys
import json

#times for tasks given in milliseconds
Wapp = 5 # 5 milliseconds
Rapp = 5
Dsc = 100 # deployment
Fsc = 5
Wsc = 5
Rl = 100
Sl = 100

class Cluster(object):
	""" Manages the Nodes of a Cluster"""
	def __init__(self,clusterDataFile):
		#self._nodeID = nodeId
		self.nodeSet = []
		self.appSet = []
		self.numberOfStages = 6 # this is the number of computational stages.
		self.numberOfNodes = 0
		self.leaderIndex = 0		
		self.appFailureCount = 0
		self.scFailureCount = 0
		self.nodeFailureCount = 0
		self.leaderFailureCount = 0
		#self._readInNodeData(clusterDataFile)	
		self._readInData(clusterDataFile)		

	def _readInData(self,clusterDataFile):
		file_object = 0
		try:
			file_object = open(clusterDataFile, 'r')
		except IOError as var:
			print("Error:", var)
			exit(0)
		line = file_object.readlines()
		data = json.loads(line[0])
		self._createNodes(data)
		self._createApplications(data)
		self._fitAppsIntoCluster()
		self._attachAppSetToNodes()		

	# parse the data for nodes
	def _createNodes(self,data):
		print("Nodes:")
		n = None
		nodeId = 0
		for node in data["Nodes"]:			
			cpuSpeed = node["CpuSpeed"]
			ram = node["Ram"]
			storage = node["Storage"]
			isLeader = False
			scData = [Dsc, 0, 0, Fsc, Sl, Rl + Wsc]
			if node["Leader"] == True:
				isLeader = True
				scData =  [Dsc, 0, 0, Fsc, Rl, Sl]

			n = Node(nodeId, cpuSpeed, ram, storage,scData)

			if isLeader:
				n.setLeader(nodeId)

			if node["Failure"] == True:
				item = node["Item"]
				onIteration = node["Iteration"]
				stage = node["Stage"]

				if isLeader:
					self.leaderFailureCount += 1

				if item == "SC":
					self.scFailureCount += 1
					n.setSCToFail(stage,onIteration)
				else:
					self.nodeFailureCount += 1
					n.setNodeToFail(stage, onIteration)
			self.nodeSet.append(n)
			nodeId += 1
			#print(node)

		#make sure each node has a reference to all of the nodes
		for node in self.nodeSet:
			node.addNodeSet(self.nodeSet)
		

	#"NumberOfIterations":2,"Failure":false,"OnIteration":0,"Stage":0},
	#"DeploymentTime":100,"ExecutionTime"
	# parse the data for applications
	def _createApplications(self,data):
		print("Nodes:")
		n = None
		application = None
		appID = 0
	
		for app in data["Applications"]:
			cpuSpeed = app["CpuSpeed"]
			ram = app["Ram"]
			storage = app["Storage"]
			deployment = app["DeploymentTime"]
			execution = app["ExecutionTime"]
			numberOfIterations = app["NumberOfIterations"]
			application = App(cpuSpeed, ram, storage,deployment, execution, numberOfIterations, appID)
			if app["Failure"] == True:
				onIteration = app["OnIteration"]
				stage = app["Stage"]
				application.setAppToFail(stage, onIteration)
				self.appFailureCount += 1
			self.appSet.append(application)
			appID += 1
		
	 # give each app a node if it fits
	def _fitAppsIntoCluster(self):
		numberOfAttachedApps = 0
		for index in range(len(self.appSet)):
			for node in self.nodeSet:
				if node.attachAppToNode(self.appSet[index],index):
					numberOfAttachedApps += 1
					break

	def _attachAppSetToNodes(self):
		for i in range(len(self.nodeSet)):
			# attaches the application set and creates the RDS for each node
			self.nodeSet[i].attachAppSet(self.appSet)


	def _readInNodeData(self,nodeDataFile):
		# The data file should have the format:
		# first line gives the index of the leader sc/node (zero indexing)
		# All lines after that have this format:
		# deployment, execution, iterations
		# where the first two are times in milliseconds and the last is the number of iterations
		file_object = 0
		try:
			file_object = open(nodeDataFile, 'r')
		except IOError as var:
			print("Error:", var)
			exit(0)
		
		line = file_object.readline()
		line = line.strip()
		self.numberOfNodes = int(line)
		logging.debug(f" numberOfNodes= {self.numberOfNodes}")
		
		line = file_object.readline()
		line = line.strip()
		self.leaderIndex = int(line)
		logging.debug(" leaderIndex= {self.leaderIndex}")
		nodeID = 0
		itemTypes = ["App","SC", "Node"]
		for line in file_object:
			line = line.strip()
			nodeData = line.split(' ')
			deployTime = int(nodeData[0])
			execTime = int(nodeData[1])
			numberOfIterations = int(nodeData[2])
			scData = [Dsc, 0, 0, Fsc, Sl, Rl + Wsc]
			# If leader, designate it
			if nodeID == self.leaderIndex:
				scData =  [Dsc, 0, 0, Fsc, Rl, Sl]
		
			appData = [nodeID,deployTime,execTime,Wapp,execTime,Rapp,execTime]

			n = Node(nodeID,self.numberOfNodes, self.numberOfNodes, scData, appData ,numberOfIterations)

			numberOfElements = len(nodeData)
			logging.debug(f" deployment time = {deployTime}, execution time = {execTime},  iterations = {numberOfIterations}")
			if numberOfElements > 3:
				itemType = int(nodeData[3])
				stage = int(nodeData[4])
				onIteration = int(nodeData[5])

				logging.debug(f"    itemType = {itemTypes[itemType]},  stage = {stage}, onIteration = {onIteration}")
				if itemType == 0:  # application
					self.appFailureCount += 1
					n.setAppToFail(stage,onIteration)			
				elif itemType == 1: # SC
					self.scFailureCount += 1
					n.setSCToFail(stage,onIteration)					
				elif itemType == 2: # Node					
					self.nodeFailureCount += 1
					n.setNodeToFail(stage, onIteration)					
			
			# establish the leader
			if nodeID == self.leaderIndex:				
				n.setLeader(self.leaderIndex)
				if numberOfElements > 3:
					self.leaderFailureCount += 1

			self.nodeSet.append(n)
			logging.debug(nodeData)
			nodeID += 1
		
		#make sure each node has a reference to all of the nodes
		for node in self.nodeSet:
			node.addNodeSet(self.nodeSet)

	# all of the rds array in the nodes must be equal for synchronization
	def checkNodeSynchronization(self):
		rdsLeader = self.nodeSet[self.leaderIndex].rdsArray
		i=0
		while i < len(self.nodeSet):
			if i != rdsLeader:
				temp = self.nodeSet[i].rdsArray
				j = 0
				while j < len(temp):
					if rdsLeader[j] != temp[j]:
						return False
					j += 1
			i += 1
		return True


	def runTest(self):	
		#logging.basicConfig(level=logging.DEBUG)
		#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)				
	
		#quit()
		iterate = True
		iteration = 1
		syncTimeStart = 0.0
		syncTimeEnd = 0.0
		syncTimeTotal = 0.0
		numberOfNodes = len(self.nodeSet)
		tStart = 0.0
		tEnd = 0.0
		syncMeasured = True # start out as if sync was measured.  This is a trigger mechanism to determine if sync can be remeasured
		deltaTime = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # t0, t1, t2, t3, t4, t5, the delta times for each stage
		syncCount = 0 # number of times the system synchronized
		totalOperationTime = time.perf_counter()
		appFailureCount = 0
		scFailureCount = 0
		nodeFailureCount = 0
		leaderFailureCount = 0
		
		while iterate == True:
			stage = 0
			if iteration > 1:
				stage = 1
			logging.info(f"\n\n************ iteration number: {iteration} ************")
			print(f"\n\n************ iteration number: {iteration} ************")
			while stage < self.numberOfStages:
				logging.info(f"\n***** Stage: {stage} *****")
				print(f"\n***** Stage: {stage} *****")


				tStart = time.perf_counter()				

				if stage == 2 and syncMeasured:
					syncMeasured = False					
					None #timer start

				for k in range(numberOfNodes):
					self.nodeSet[k].run(stage, iteration)       

				for k in range(numberOfNodes):
					self.nodeSet[k].joinThreads()

				tEnd = time.perf_counter()
				deltaTime[stage] = tEnd - tStart # the time required for this stage

				for k in range(numberOfNodes):
					self.nodeSet[k].displayRDS()

				
				if stage == 5:
					iterate = False
					# function to test sync state to determine if cluster is in sync after stage 5
					if self.checkNodeSynchronization():				
						syncMeasured = True				
						# check to see if there are any iterations left to do
						for k in range(numberOfNodes):
							if iteration <  self.nodeSet[k].getLastIteration():
								iterate = True # go for another iteration
								break
						logging.debug(f" cluster.py iterate = {iterate}")
					else: # If not synchronized, continue with iteration
						iterate = True

				stage += 1

			if syncMeasured:
				syncCount += 1
			syncTimeTotal += deltaTime[2] + deltaTime[3] + deltaTime[4] + deltaTime[5]
			#syncTimeTotal += syncTimeEnd - syncTimeStart
			iteration += 1

			# debug exit
			#if iteration > 3:
			#	iterate = 0

		totalOperationTime = time.perf_counter() - totalOperationTime

		logging.info(f"\n\n RESULTS: \n")

		logging.info(f"\n Total Iterations = {iteration-1}")
	
		logging.info(f" Total Synchronization Delay = {syncTimeTotal} seconds")
		logging.info(f" Number of times the system synchronized = {syncCount}")
		averageSyncTime = syncTimeTotal/syncCount
		logging.info(f" Average Synchronization Delay = {averageSyncTime} seconds")
		logging.info(f" Total Operation Time = {totalOperationTime}")

		if self.appFailureCount > 0:
			mttf = totalOperationTime / self.appFailureCount
			logging.info(f" MTTF of applications = {mttf}")
		if self.scFailureCount > 0:
			mttf = totalOperationTime / self.scFailureCount
			logging.info(f" MTTF of SCs = {mttf}")
		if self.nodeFailureCount > 0:
			mttf = totalOperationTime / self.nodeFailureCount
			logging.info(f" MTTF of Nodes = {mttf}")
		if self.leaderFailureCount > 0:
			mttf = totalOperationTime / self.leaderFailureCount
			logging.info(f" MTTF of Leader = {mttf}")

		# empty nodes:
		logging.info(f"The following Nodes Are Empty:")
		count = 0
		for node in self.nodeSet:
			if node.Empty:
				count += 1
				logging.info(f" NodeID = {node.getNodeID()} ")
		if count == 0:
			logging.info(f" No nodes are empty")

def main():
	num = len(sys.argv)

	if num != 2:
		print(" Program use:\n python cluster.py dataInputFile")
		return 0


	#logging.basicConfig(filename='clusterLog2.txt',level=logging.DEBUG)
	#logging.basicConfig(level=logging.DEBUG)
	#logging.basicConfig(level=logging.INFO)

	logging.basicConfig(filename='clusterLog.txt',level=logging.INFO)
	logging.info("\n\n\n\n\n  ***** START NEW TEST ***** \n")
	print("\n\n\n\n\n  ***** START NEW TEST ***** \n")
		
	#cluster = Cluster("ClusterData10N10A1F.txt")
	#cluster = Cluster("ClusterData100N100A.txt")
	
	cluster = Cluster(sys.argv[1])
	cluster.runTest()
	return 0
	

if __name__ == '__main__':
	sys.exit(main())

