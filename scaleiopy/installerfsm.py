import json
import time

from scaleioutil import ScaleIOLogger


"""
TODO:

"""

##======================================================
#       ScaleIO IM Installation process State Machine
##======================================================


##===============================================
## TRANSITIONS

class Transition(object):
	# Code executed when transitioning from one state to another
	def __init__(self, toState):
		self.toState = toState
		
	def Execute(self):
		self.logger.debug("Transitioning")


##===============================================
## STATES

class State(object):
	# The base template state which all others will inherit from
	def __init__(self, FSM, im_inst):
		self.FSM = FSM
		self.timer = 0
		self.startTime = 0
		im_instance = im_inst
		# Possible states: IDLE, PENDING, FAILED, COMPLETED
		
	def Enter(self):
		self.FSM.setCurrentStateStatus('PENDING')
		pass
	
	def Execute (self):
		pass
	
	def status (self):
		pass
	
	def Next(self):
		pass
	
	def Exit(self):
		pass

class Query(State):
	# Worker class - Takes care of managing IM QUERY phase and do status control of each phase
	def __init__(self, FSM, im_inst):
		super(Query, self).__init__(FSM, im_inst)
		self.calling_object = im_inst
		
	def Enter(self):
		self.logger.debug("Enter Query State")
		super(Query, self).Enter()

	def Execute (self):
		self.logger.debug("Start ScaleIO IM Query phase")
		self.FSM.imapi.set_state('query')
		self.logger.debug("State: {}".format(self.FSM.imapi.get_state()))

		self.pendingItemCount = self.FSM.install_process_status("query")
		while self.pendingItemCount > 0:
			self.pendingItemCount = self.FSM.install_process_status("query")
			time.sleep(0.5)
		if self.pendingItemCount < 0:
			self.logger.error("Query State Failed!")
		else:
			self.logger.debug("COMPLETED")
			self.Next()

		if self.FSM.autoTransition:
			self.FSM.Execute()

	def Next(self):
		self.logger.debug("Advance to UPLOAD phase")
		self.FSM.ToTransition("toUPLOAD") # Move to next step
		
	def Exit(self):
		pass

class Upload(State):
	# Worker class - Takes care of managing IM UPLOAD phase and do status control of each phase
	def __init__(self, FSM, im_inst):
		super(Upload, self).__init__(FSM, im_inst)
		
	def Enter(self):
		self.logger.debug("Enter Upload State")

		super(Upload, self).Enter()

	def Execute (self):
		self.logger.debug("Upload of binaries to nodes")
		# Call set_state
		self.FSM.imapi.set_state('upload') # Set IM to UPLOAD state
		self.logger.debug("State: {}".format(self.FSM.imapi.get_state()))
		self.pendingItemCount = self.FSM.install_process_status("upload")
		while self.pendingItemCount > 0:
			self.pendingItemCount = self.FSM.install_process_status("upload")
			time.sleep(2)
		if self.pendingItemCount < 0:
			self.logger.error("Upload State Failed!")
		else:
			self.logger.debug("COMPLETED")
			self.Next()
		
		if self.FSM.autoTransition:
			self.FSM.Execute()
	
	def Next(self):
		self.logger.debug("Advance to INSTALL phase")
		self.FSM.ToTransition("toINSTALL") # Move to next step
		
	def Exit(self):
		pass


class Install(State):
	# Worker class - Takes care of managing IM Install phase and do status control of each phase
	def __init__(self, FSM, im_inst):
		super(Install, self).__init__(FSM, im_inst)
		
	def Enter(self):
		self.logger.debug("Enter Install State")
		super(Install, self).Enter()

	def Execute (self):
		self.logger.debug("Installing ScaleIO binaries on nodes")
		self.FSM.imapi.set_state('install') # Set IM to INSTALL state
		self.logger.debug("State: {}".format(self.FSM.imapi.get_state()))
		self.pendingItemCount = self.FSM.install_process_status("install")
		while self.pendingItemCount > 0:
			self.pendingItemCount = self.FSM.install_process_status("install")
			time.sleep(2)
		if self.pendingItemCount < 0:
			self.logger.error("FAILED")
		else:
			self.logger.debug("COMPLETED")
			time.sleep(6)
			self.Next()
		
		if self.FSM.autoTransition:
			self.FSM.Execute()
			
	def Next(self):
		self.logger.debug("Advance to Configure Phase")
		self.FSM.ToTransition("toCONFIGURE") # Move to next step
		
	def Exit(self):
		self.logger.debug("Exit INSTALL phase")


class Configure(State):
	# Worker class - Takes care of managing IM Configure phase and do status control of each phase
	def __init__(self, FSM, im_inst):
		super(Configure, self).__init__(FSM, im_inst)
		
	def Enter(self):
		self.logger.debug("Entering Configure Phase")
		super(Configure, self).Enter()

	def Execute (self):
		self.logger.debug("Configure ScaleIO Cluster")
		# Call set_state
		self.FSM.imapi.set_state('configure') # Set IM to QUERY state
		self.logger.debug("State: {}".format(self.FSM.imapi.get_state()))
		self.pendingItemCount = self.FSM.install_process_status("configure")
		while self.pendingItemCount > 0:
			self.pendingItemCount = self.FSM.install_process_status("configure")
			time.sleep(2)
		if self.pendingItemCount < 0:
			self.logger.error("FAILED")
		else:
			self.logger.debug("COMPLETED")
			self.Next()

		if self.FSM.autoTransition:
			self.FSM.Execute()
		
	def Next(self):
		self.logger.debug("Advance to ARCHIVE State")
		self.FSM.ToTransition("toARCHIVE") # Move to next step
		
	def Exit(self):
		pass

class Archive(State):
	# Worker class - Takes care of managing IM Archive phase and do status control of each phase
	def __init__(self, FSM, im_inst):
		super(Archive, self).__init__(FSM, im_inst)
		
	def Enter(self):
		self.logger.debug("Entering Archive phase")
		super(Archive, self).Enter()

	def Execute (self):
		self.logger.debug("Completing ScaleIO cluster installation")
		self.FSM.imapi.set_archive_all()
		self.logger.debug("State: {}".format(self.FSM.imapi.get_state()))
		time.sleep(3)
		
		self.Next()
		if self.FSM.autoTransition:
			self.FSM.Execute()
		
	def Next(self):
		self.logger.debug("Advance to COMPLETE step")
		self.FSM.ToTransition("toCOMPLETE") # Move to next step
		
	def Exit(self):
		self.logger.debug("Exiting ARCHIVE phase")

class Complete(State):
	# Worker class - Takes care of managing IM "Completing" phase and do status control of each phase
	def __init__(self, FSM, im_inst):
		super(Complete, self).__init__(FSM, im_inst)
		
	def Enter(self):
		self.logger.debug("Entering COMPLETE phase")
		super(Complete, self).Enter()

	def Execute (self):
		self.logger.debug("Installation complete!")
		self.FSM.setCurrentStateStatus('COMPLETED')
		self.logger.debug("Current State Status: {}".format(self.FSM.getCurrentStateStatus()))
		self.logger.debug("State: {}".format(self.FSM.imapi.get_state()))


	def Next(self):
		self.FSM.setCurrentStateStatus('COMPLETED')

	def Exit(self):
		self.logger.debug("Exiting COMPLETE phase")

##===============================================
## FINITE STATE MACHINE

class FSM(object):
	# Holds the states and transitions available, 
	# executes current states main functions and transitions
	def __init__(self, imapi):
		self.states = {}
		self.transitions = {}
		self.curState = None
		self.prevState = None ## USE TO PREVENT LOOPING 2 STATES FOREVER
		self.trans = None
		self.autoTransition = False
		self.completed = False
		self.curStateStatus = 'IDLE'
		self.imapi = imapi

	def AddTransition(self, transName, transition):
		self.transitions[transName] = transition
		
	def enableAutoTransition(self):
		self.autoTransition = True
	
	def disableAutoTransition(self):
		self.autoTransition = False

	def AddState(self, stateName, state):
		self.states[stateName] = state

	def SetState(self, stateName):
		self.prevState = self.curState
		self.curState = self.states[stateName]
	
	def getState(self):
		return curState
	
	def setCurrentStateStatus(self, status):
		self.logger.debug("*** Setting currentStateStatus to {} ***".format(status))
		self.curStateStatus = status
		if status == 'COMPLETED':
			self.trans = None
		#	self.curState = None
	
	def getCurrentStateStatus(self):
		return self.curStateStatus
		# Return IDLE, FAILED, PENDING, COMPLETE
		
	def ToTransition(self, toTrans):
		self.trans = self.transitions[toTrans]

	def Next(self):
		if self.curStateStatus == 'IDLE' or self.curStateStatus == 'PENDING':
			self.curState.Next()
			if self.autoTransition:
				self.Execute()
		else:
			self.trans = None
			self.logger.debug("Status is COMPLETE - Next() wont do anything")
			
	def Execute(self):
		self.logger.debug("FSM Execute() - curStateStatus = ".format(self.curStateStatus))
		if self.curStateStatus == 'IDLE' or self.curStateStatus == 'PENDING':
			self.setCurrentStateStatus('PENDING')
			if (self.trans):
				self.curState.Exit()
				self.trans.Execute()
				self.SetState(self.trans.toState)
				self.curState.Enter()
				self.trans = None
			self.curState.Execute()
		else:
			self.logger.debug("Statemachine COMPLETE")
			self.trans = None

	
	def install_process_status(self, expectState):
		self.imapi.get_state()
		self.cStatusItems = json.loads(self.imapi.get_command_state())
		self.allCompleted = False
		self.pendingItemCount = 0
		for kOuter,vOuter in self.cStatusItems.items():
			for innerArray in vOuter:
				if innerArray['allowedState'] == str(expectState):
					if innerArray['commandState'] == 'failed':
						return -1
					if innerArray['commandState'] == 'pending':
						self.pendingItemCount += 1
		self.logger.debug("Pending Items: ".format(str(self.pendingItemCount)))
		if self.pendingItemCount == 0:
			return 0
		else:
			return self.pendingItemCount

		# IM State:        
		# idle, query, upload, install, configure
		# IM Command state:
		# pending, failed, completed

##===============================================
## IMPLEMENTATION

Char = type("Char", (object,), {})

class InstallerFSM:
	# Base character which will be holding the Finite State Machine,
	# which in turn will hold the states and transitions.
	def __init__(self, imapi, automatic=False):
		self.loggerInstance = ScaleIOLogger.get() # Create logger Singleton
		self.logger = self.loggerInstance.getLoglevel(debugLevel) # Get logger instance with defined logging level
		self.FSM = FSM(imapi)
		if automatic:
			self.FSM.enableAutoTransition()

		## STATES
		self.FSM.AddState("QUERY", Query(self.FSM, imapi))
		self.FSM.AddState("UPLOAD", Upload(self.FSM, imapi))
		self.FSM.AddState("INSTALL", Install(self.FSM, imapi))
		self.FSM.AddState("CONFIGURE", Configure(self.FSM, imapi))
		self.FSM.AddState("ARCHIVE", Archive(self.FSM, imapi))
		self.FSM.AddState("COMPLETE", Complete(self.FSM, imapi))

		## TRANSITIONS
		self.FSM.AddTransition("toQUERY", Transition("QUERY"))
		self.FSM.AddTransition("toUPLOAD", Transition("UPLOAD"))
		self.FSM.AddTransition("toINSTALL", Transition("INSTALL"))
		self.FSM.AddTransition("toCONFIGURE", Transition("CONFIGURE"))
		self.FSM.AddTransition("toARCHIVE", Transition("ARCHIVE"))
		self.FSM.AddTransition("toCOMPLETE", Transition("COMPLETE"))
		
		self.FSM.SetState("QUERY") # When executing FSM first time always start at QUERY phase
	
	def Next(self):
		self.FSM.Next()
	
	def getCurrentStateStatus(self):
		return self.FSM.getCurrentStateStatus()
		
	def Execute(self):
		self.FSM.Execute()

