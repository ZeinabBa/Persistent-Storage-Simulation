""" Node class module"""
from threading import Thread, Lock
import time
import os
import logging
# import threading

#g_rdsMutex = Lock()

#times for tasks given in milliseconds
Wapp = 5 # 5 milliseconds
Rapp = 5
Dsc = 10 # deployment
Fsc = 5
Wsc = 5
Rl = 50
Sl = 50

# class acts similar to an enum
# this gives the mode or state of the node wrt failures
class Mode:
    Normal = 0
    AppFailure1 = 1
    AppFailure2 = 2
    SCFailure1 = 3
    SCFailure2 = 4
    NodeFailure1 = 5
    NodeFailure2 = 6

    def __init__(self):
        self.state = Mode.Normal

    def getState(self):
        return self.state

    def setState(self,state):
        self.state = state

class SCCommElement:
    def __init__(self):
        self.data = 0 # the value retained here
        self.readFlag = 0 #1 means it hasn't yet been read, and you can read it.  If it's a 0, it's ready to be written to.
    
class App:
    def __init__(self, cpuSpeed, ram, storage, deploy, exec, finalIteration, appID):
        #appData = [nodeID,deployTime,execTime,Wapp,execTime,Rapp,execTime]
        self.appData = [deploy, exec, Wapp, exec, Rapp, exec] #The time for each stage for this application
        self.cpuSpeed = cpuSpeed
        self.ram = ram
        self.storage = storage
        self.deploy = deploy
        self.exec = exec
        self.finalIteration = finalIteration
        self.appID = appID
        self.nodeID = -1 # Initially an application is not associated with a node, the value -1 indicates this.
        self.mode = Mode.Normal
        self.appLocalVariable = 0
        self.appThread = None
        self.appTrigger = 0 # trigger that a failure will happen
        self.failureStage = -1 # stage where failure will happen
        self.failureIteration = -1 # iteration where failure will happen
        self.nodeRds = []
        self.applicationFailed = False # designates if an application has failed. 


    def attachToNode(self, nodeID):
        self.nodeID = nodeID

    # assign the rds of the node to the app.  This is a convenient way to 
    # access the Node's rds
    def setRdsFromNode(self,rds):
        self.nodeRds = rds
        None

    # force Node failure on the application
    def injectNodeFailure(self):
        self.mode = Mode.NodeFailure1
        
    def setAppToFail(self,stage, iteration):
        self.appTrigger = 1
        self.failureStage = stage
        self.failureIteration = iteration

    def triggerFailure(self, stage, currentIteration):       
        if self.appTrigger == 1 and self.failureStage == stage and self.failureIteration == currentIteration and self.mode == Mode.Normal:
            self.mode = Mode.AppFailure1
            self.appTrigger = 0 # reset trigger  

    # Increment finalIteration value if the current interation value
    # is less than or equal to it
    def incrementIteration(self,currentIteration):
        logging.debug(f" appID = {self.appID} before incrementIteration finalIteration = {self.finalIteration}")
        if currentIteration <= self.finalIteration:
            self.finalIteration += 1
        logging.debug(f" appID = {self.appID} after incrementIteration finalIteration = {self.finalIteration}")

    def writeStateToRDS(self):
        self.nodeRds[self.appID] = self.appLocalVariable

    def getStateFromRDS(self):
        self.appLocalVariable = self.nodeRds[self.appId]

    def processApp(self, stage, currentIteration):
        self.appThread = None     
        appData = self.appData[stage]
        # keep track of the number of iterations the application takes
        if currentIteration <= self.finalIteration:
            # tigger failure if it's set for this stage
           
                        
            if self.mode == Mode.NodeFailure1:
                logging.debug(f" >>>>  Node Failure -- appID = {self.appID} app failing")
                appData = self.appData[0] # redeploy application
                self.appThread = Thread(target=self.appRecoveryFunction, args=[stage, appData])
                self.mode = Mode.NodeFailure2 # do nothing

                # if the application is set to fail in this iteration, reset the trigger, because node failure takes precedence
                if currentIteration == self.failureIteration:
                    self.appTrigger = 0

                if stage == 5: # if stage five is reached, go back to normal operation and add an iteration if necessary
                    self.mode = Mode.Normal
                    self.finalIteration += 1 # add missed iteration 
                    logging.debug(f" >>>>  Node Failure1 -- appID = {self.appID} finalIteration={self.finalIteration}")

            elif self.mode == Mode.NodeFailure2:
                appData = 0 # Do nothing
                self.appThread = Thread(target=self.appRecoveryFunction, args=[stage, appData])
                if stage == 5: # if stage five is reached, go back to normal operation and add an iteration if necessary
                    self.mode = Mode.Normal
                    self.finalIteration += 1 # add missed iteration 
                    logging.debug(f" >>>>  Node Failure2 -- appID = {self.appID} finalIteration={self.finalIteration}")

            elif self.mode == Mode.AppFailure1 or self.mode == Mode.AppFailure2: # deal with application failure
                logging.debug(f" >>> Acknowledge App failure mode")
                appData = 0
                if self.mode == Mode.AppFailure1:
                    appData = self.appData[0] # for app failure, lanuch the re-deployment delay                
                self.appThread = Thread(target=self.appRecoveryFunction, args=[stage, appData])
                if stage == 5: # if stage five is reached, go back to normal operation and add an iteration if necessary
                    self.mode = Mode.Normal
                    self.finalIteration += 1 # add missed iteration                   
                else:
                    self.mode = Mode.AppFailure2 # do nothing    
            else:
                self.appThread = Thread(target=self.appFunction, args=[stage, appData])

            self.appThread.start()
        None

    def appFunction(self,stage, msDelay): 
        logging.debug(f"appFunc: {self.appID}")

        if stage == 0: # deployment
            None
        elif stage == 1: # Read from RDS
            # since the initial value is known to be zero,readRDS() can be ignored
            #if self.mode == Mode.AppFailure3: # self.appFailure == 3: # recovering                
            #    self.appLocalVariable = self.readRds(self.appID)
            #    self.appFailure = 0 # back to normal operation
            #    self.mode = Mode.Normal
            #    print(" appFunc recovering appLocalVariable = ",self.appLocalVariable)
            #else:
                #Execute task, change state 
            self.appLocalVariable += 1
        elif stage == 2: # write to RDS
            self.writeStateToRDS()
        elif stage == 3:  #Execute task
            # change state 
            self.appLocalVariable += 1            
        elif stage == 4: # Read external app
            None
        elif stage == 5: #Execute task
            # change state 
            self.appLocalVariable += 1   
        logging.debug(f"appLocalVariable = {self.appLocalVariable}, msDelay = {msDelay}")
        self.delay(msDelay)

    def appRecoveryFunction(self,stage, msDelay):
        logging.debug(f" ********>>>>> Failed ... appRecoveryFunction, nodeID = {self.nodeID}, appID = {self.appID}, msDelay = {msDelay}")
        self.delay(msDelay)      
        
    def delay(self, msDelay):
        secondsDelay = msDelay/1000
        time.sleep(secondsDelay)

    def joinThread(self):
        if self.appThread != None:
            self.appThread.join() 

class Node:
    scLeaderNode = 0 # The current SC Leader node

    # The time in milliseconds is provided in the arrays below for each stage of the process, except appID is not a time    
    # scData = [deployment, FetchRds, SendToLeader, ReceiveFromLeader, WriteToRds, synch]
    # appData = [appID, deployment, execute, writeToRDS, execute, readExternApp, execute]
    # 
    def __init__(self,nodeId, cpuSpeed, ram, storage, scData):
        self._nodeID = nodeId
        self.cpuSpeed = cpuSpeed
        self.ram = ram
        self.storage = storage
        self.appIndices = None # the indicies of the apps on this node

        #self.numberOfNodes = numberOfNodes
        #self.numberOfApps = numberOfApps
        self.scData = scData
        #self.appData = appData[1:]
        #self.appLocalVariable = 0
        self.scLocalVariables = [] # a slot for each application
        #self.appID = appData[0]
        self.rdsArray = [] # initialize the rds array
        self.leaderArray = [] # initialize rds state tracking array for leader
        self.nodeSet = []
        self.appIndices = []
        self.appSet = []
        #self.numberOfIterations = numberOfIterations # number of iterations the application must perform
        #self.lastIteration = lastIteration #the iteration where the app will run
        # Add the sc thread 
        #self.appThread = 0
        self.scThread = 0
        #self.appFailure = 0 #This is the index for the AppState list, the global variable
        #self.scFailure = 0
        #self.nodeFailure = 0
        self.scTrigger = 0
        self.nodeTrigger = 0
        self.appTrigger = 0
        self.failureStage = -1
        self.failureIteration = -1
        self.scDeployed = False # On the first iteration the application is deployed, after that it is idle during this stage
        self.mode =  Mode.Normal
        self.Empty = True #  A node defaults to empty, i.e. no applications attached
        self.ramRemaining = self.ram
        self.storageRemaining = self.storage        

    def getNodeID(self):
        return self._nodeID

    #Attaches an app to the node if it fits
    def attachAppToNode(self,app, appIndex):
        if app.cpuSpeed <= self.cpuSpeed and app.ram <= self.ramRemaining and app.storage <= self.storageRemaining:
            self.ramRemaining -= app.ram
            self.storageRemaining -= app.storage
            app.attachToNode(self._nodeID)
            #app.setRdsFromNode(self.rdsArray) # This may not work... 5/23/22, 11:00 p.m.
            self.appIndices.append(appIndex)
            self.Empty = False
            return True
        return False
        
    # attach appSet to the node and make sure the
    # RDS is set for it
    def attachAppSet(self,appSet):
        self.appSet = appSet
        self.rdsArray = [0]*len(appSet) 
        self.scLocalVariables = [0]*len(appSet)
        for idx in self.appIndices:
            self.appSet[idx].setRdsFromNode(self.rdsArray)

    def setNumberOfApps(self,numberOfApps):
        self.rdsArray = [0]*numberOfApps

    def addAppIndex(self,index):
        self.appIndices.append(index)

    # set app, sc or node to fail
    def setAppToFail(self, stage, iteration):
        self.appTrigger = 1
        self.failureStage = stage
        self.failureIteration = iteration
           
    def setSCToFail(self, stage, iteration):        
        self.scTrigger = 1
        self.failureStage = stage
        self.failureIteration = iteration

    def setNodeToFail(self, stage, iteration):
        self.nodeTrigger = 1
        self.failureStage = stage
        self.failureIteration = iteration 

  
    def setNumberOfApps(self, numberOfApps):
        self.numberOfApps = numberOfApps

    def setNumberOfNodes(self):
        self.NumberOfNodes = len(self.nodeSet)

    # returns the number of iterations remaining for the application in this node
    # that has the largest number of iterations
    def getLastIteration(self):
        #return self.lastIteration
        maxVal = 0
        for idx in self.appIndices:
            val = self.appSet[idx].finalIteration
            if val > maxVal:
                maxVal = val
        return maxVal

    def scThreadStart(self, stage, currentIteration):
        self.scThread = None
        scData = 0
        if self.scDeployed == False:
            scData = self.scData[stage]
       
        if self.mode == Mode.NodeFailure1: #.nodeFailure == 1:
            logging.debug(f" >>> Acknowledge Node failure causing SC failure")
            deployment = self.scData[0]
            self.scThread = Thread(target=self.scRecoveryFunction, args=[stage, deployment]) 
        elif self.mode == Mode.NodeFailure2: # self.nodeFailure == 2:
            deployment = 0
            self.scThread = Thread(target=self.scRecoveryFunction, args=[stage, deployment]) 
        elif self.mode == Mode.SCFailure1 and stage < 3: # if stage is less than three, recovery is possible within this iteration after deployment
            logging.debug(f" >>> Acknowledge SC failure mode before state 3")
            deployment = self.scData[0] 
            self.scThread = Thread(target=self.scRecoveryFunction, args=[stage, deployment])
            self.mode = Mode.Normal # self.scFailure = 0    
        elif self.mode == Mode.SCFailure1: #.scFailure == 1:
            logging.debug(f" >>> Acknowledge SC failure mode at or after state 3 <-- not implmented")
            deployment = self.scData[0] 
            self.scThread = Thread(target=self.scRecoveryFunction, args=[stage, deployment])
            #self.scFailure = 2
            self.mode = Mode.SCFailure2
            # add an iteration to the applications on this node
            self.incrementAppIterations(currentIteration)
        elif self.mode == Mode.NodeFailure2: #.scFailure == 2:
            logging.debug(f" >>> Acknowledge SC failure == 2")
            delay = 0
            self.scThread = Thread(target=self.scRecoveryFunction, args=[stage, delay])
        elif(self._nodeID == Node.scLeaderNode):
            logging.debug(f" ******************* run leaderFunction() ")
            self.scThread = Thread(target=self.leaderFunction, args=[stage, scData])  
            self.scDeployed = True
        else:
            self.scThread = Thread(target=self.scFunction, args=[stage, scData])
            self.scDeployed = True
            
        logging.debug(f"scThread.start()")
        self.scThread.start()
               

    # make sure that the broadcast mode time delay data is applied to the leader
    def swapDataOfSCwithLeader(self,leaderId,SCId):
        temp = self.nodeSet[leaderId].scData
        self.nodeSet[leaderId].scData = self.nodeSet[SCId].scData
        self.nodeSet[SCId].scData = temp
        
    # This only looks for SC or Node failures, not App failures
    def isNodeItemSetToTrigger(self,nodeIndex):
        if self.nodeSet[nodeIndex].scTrigger == 1 or self.nodeSet[nodeIndex].nodeTrigger == 1:
            return True
        return False

    # rotates to new leader if current node is the leader
    def changeLeader(self):
        if self._nodeID != Node.scLeaderNode:
            return
        logging.debug(f" ********** CHANGE LEADER!!!")
        saveNode = Node.scLeaderNode
        temp = saveNode
        loop = True
        numberOfNodes = len(self.nodeSet)
        while loop:
            temp += 1
            if temp == Node.scLeaderNode:
                logging.warning(f" No Node Available To Be Leader")
                exit(0)

            if temp >= numberOfNodes:
                temp = 0
            if self.isNodeItemSetToTrigger(temp) == False:
                Node.scLeaderNode = temp
                self.swapDataOfSCwithLeader(saveNode,Node.scLeaderNode)
                loop = False

    # used for node failure
    def zeroRDS(self):
        size = len(self.rdsArray)
        for i in range(size):
            self.rdsArray[i] = 0
        
    def incrementAppIterations(self, currentIteration):
        for index in self.appIndices:
            self.appSet[index].incrementIteration(currentIteration)

    def triggerAppsThatFail(self, stage, iteration):
        for index in self.appIndices:
            self.appSet[index].triggerFailure(stage, iteration)        

    def triggerFailure(self, stage, currentIteration):
        self.triggerAppsThatFail(stage, currentIteration)
        if self.failureStage == stage and self.failureIteration == currentIteration:
            if self.nodeTrigger == 1:
                #self.nodeFailure = 1
                self.mode = Mode.NodeFailure1
                self.nodeTrigger = 0 
                # force app failures due to node failure, which takes precedence over app failure
                for index in self.appIndices:
                    self.appSet[index].injectNodeFailure()
            elif self.scTrigger == 1:                
                #self.scFailure = 1
                self.mode = Mode.SCFailure1
                self.scTrigger = 0
                logging.debug(f" SC failure triggered! stage = {stage} failureStage = {self.failureStage}")
            

    def runApps(self, stage, iteration):
        for index in self.appIndices:
            self.appSet[index].processApp(stage, iteration)   

    # start the cpus/threads
    def run(self, stage, currentIteration):
        logging.debug(f"In run()")
        #if self.iterationNumber >= self.numberOfIterations:
        #    return

        #scData = self.scData[stage]        
        #appData = self.appData[stage]
        logging.debug(f"Starting Threads: ")
        #print(" scData = ", scData)
        #print(" appData = ", appData)
        self.scThread = None
        #self.appThread = None

        self.triggerFailure(stage,currentIteration)

        #time.sleep(0.2)
        if self.mode == Mode.NodeFailure1:
            self.zeroRDS()            

        self.scThreadStart(stage, currentIteration)
       
        #processApp(self, stage, currentIteration):
        self.runApps(stage,currentIteration)
        #self.appThreadStart(stage, currentIteration) 
        
        if self.mode == Mode.NodeFailure1:
            self.mode = Mode.NodeFailure2

        # increment to next iteration if no failure has occurred
        if stage == 5:
            if self.mode == Mode.NodeFailure2:  # don't increase iteration count, but go back to normal operation next iteration
                #self.nodeFailure= 0
                self.mode = Mode.Normal
                self.changeLeader()          
                #self.lastIteration += 1 # Needs another iteration to run                         
            elif self.mode == Mode.SCFailure2: # Don't increment iteration count if SC failed after or at stage 3
                #self.scFailure = 0 # back to normal operation in next iteration
                self.mode = Mode.Normal
                self.changeLeader()

    def joinThreads(self):
        self.scThread.join()
        for idx in self.appIndices:
            self.appSet[idx].joinThread()            

    def displayRDS(self):
        if(self._nodeID == Node.scLeaderNode):
            logging.info(f"nodeId: {self._nodeID}  rds = {self.rdsArray} <-- leader")
        else:
            logging.info(f"nodeId: {self._nodeID}  rds = {self.rdsArray}")

    def setLeader(self, leaderNode):
        Node.scLeaderNode = leaderNode

    # all all of the external nodes of the cluster here
    def addNode(self, node):
        self.nodeSet.append(node)

    def addNodeSet(self, nodeSet):
        self.nodeSet = nodeSet
        
    def delay(self, msDelay):
        secondsDelay = msDelay/1000
        time.sleep(secondsDelay)

    def getLeaderRdsState(self, appID):
        #g_rdsMutex.acquire()
        value = self.nodeSet[Node.scLeaderNode].leaderArray[appID]
        #g_rdsMutex.release()
        return value

    def setLeaderRdsState(self, appID, value):
        #g_rdsMutex.acquire()
        #self.mode = Mode.SCFailure2
        logging.debug(f" setLeaderRdsState: Leader.mode = {self.nodeSet[Node.scLeaderNode].mode }")
        if self.nodeSet[Node.scLeaderNode].mode == Mode.Normal:
            self.nodeSet[Node.scLeaderNode].rdsArray[appID] = value
        #g_rdsMutex.release()

    def readRds(self, appID):
        #g_rdsMutex.acquire()
        value = self.rdsArray[appID]
        #g_rdsMutex.release()
        return value
    
    def writeToRds(self, appID, value):
        #g_rdsMutex.acquire()
        self.rdsArray[appID] = value
        #g_rdsMutex.release()

    def sendToLeader(self, appID, value):
        self.nodeSet[Node.scLeaderNode].writeToRds(appID,value) 
       
    def copyNodeRdsToNodeRds(self, fromIdx, toIdx):       
        for i in range(len(self.rdsArray)):
            skip = False
            for idx in self.nodeSet[toIdx].appIndices: # ignore entries for apps of the node, because they are most up to date
                if idx == i:
                    skip = True
                    break

            if skip: # This value should not be changed, since it's a local value and is the most up to date
                continue                
            value = self.nodeSet[fromIdx].readRds(i)
            self.nodeSet[toIdx].writeToRds(i,value)        

    def broadcastToSCs(self):   
        logging.debug(" ***** BROADCASTING *****")
        # If Leader is a failed node, it can't broadcast
        mode = self.nodeSet[Node.scLeaderNode].mode
        if mode == Mode.NodeFailure1 or mode == Mode.NodeFailure2:
            return
        for i in range(len(self.nodeSet)):
            # Can't broadcast to failed node
            mode = self.nodeSet[i].mode
            if mode == Mode.NodeFailure1 or mode == Mode.NodeFailure2:
                continue
            if Node.scLeaderNode != i:
                self.copyNodeRdsToNodeRds(Node.scLeaderNode,i)

    def appFunction(self, stage, msDelay):
        logging.debug(f"appFunc: {self.appID}")

        if stage == 0: # deployment
            None
        elif stage == 1: # Read from RDS
            # since the initial value is known to be zero,readRDS() can be ignored
            #if self.mode == Mode.AppFailure3: # self.appFailure == 3: # recovering                
            #    self.appLocalVariable = self.readRds(self.appID)
            #    self.appFailure = 0 # back to normal operation
            #    self.mode = Mode.Normal
            #    print(" appFunc recovering appLocalVariable = ",self.appLocalVariable)
            #else:
                #Execute task, change state 
            self.appLocalVariable += 1
        elif stage == 2: # write to RDS
            self.writeToRds(self.appID,self.appLocalVariable)
        elif stage == 3:  #Execute task
            # change state 
            self.appLocalVariable += 1            
        elif stage == 4: # Read external app
            None
        elif stage == 5: #Execute task
            # change state 
            self.appLocalVariable += 1   
        logging.debug(f"appLocalVariable = {self.appLocalVariable}, msDelay = {msDelay}")
        self.delay(msDelay)
          
        #Upon failure this function is run
    def appRecoveryFunction(self,stage, msDelay):
        logging.debug(f" ********>>>>> Failed ... appRecoveryFunction, appID =  {self.appID}, msDelay = {msDelay}")
        self.delay(msDelay)  

        # This function is run when the application is in idle mode with nothing to do
    def appDummyFunction(self,stage, msDelay):
        #print(" ********>>>>> Failed ... appRecoveryFunction, appID =  ",self.appID)
        self.delay(msDelay)  

    def scFunction(self, stage, msDelay):
        logging.debug(f"scFunc: {self._nodeID}")
        if stage == 0: # deployment
            None
        elif stage == 1: # Fetch from RDS
            None
        elif stage == 2: # Send To Leader
            None            
        elif stage == 3: # receive from leader
            for idx in self.appIndices:                
                self.scLocalVariables[idx] = self.readRds(idx) 
                logging.debug(f"scLocalVariables[{idx}] = {self.scLocalVariables[idx]}")
        elif stage == 4: # synchronization, send values to leader
            for idx in self.appIndices: 
                #self.sendToLeader(idx,self.scLocalVariables[idx])
                self.setLeaderRdsState(idx,self.scLocalVariables[idx])
        elif stage == 5: # synchronization
            None
        self.delay(msDelay)

    def leaderFunction(self, stage, msDelay):
        logging.debug(f"leaderFunc: {self._nodeID}")
        if stage == 0: # deployment
            None
        elif stage == 1:
            None
        elif stage == 2:
            None
        elif stage == 3: # Fetch from RDS
            for idx in self.appIndices:                
                self.scLocalVariables[idx] = self.readRds(idx)               
                logging.debug(f"Leader: scLocalVariables[{idx}] = {self.scLocalVariables[idx]}")
        elif stage == 4: # Receive from SCs
            None
        elif stage == 5: # Send to SCs
            self.broadcastToSCs()
            None
        self.delay(msDelay)

    def scRecoveryFunction(self, stage, msDelay):
        if self._nodeID == Node.scLeaderNode:
            logging.debug(f" ********>>>>> Failed ... scRecoveryFunction, Leader nodeID =  {self._nodeID}")
        else:
            logging.debug(f" ********>>>>> Failed ... scRecoveryFunction, nodeID =  {self._nodeID}")
        self.delay(msDelay)
        None


