# Import relevant accepted modules
import graphs, digraphs, csv, itertools

def maxMinTransfers(fileName):
    # Access the file used for the method with relevant data
    with open(fileName, 'r') as thefile:
        # Translate the data from the csv file into tuples of rows
        L = { tuple(row) for row in csv.reader(thefile) }

    # Generate a dictionary that has the format Lines: Stations for each row
    LinesDictionary = { row[0]: set(row[1:]) for row in L }

    # Generate a Vertices that is the first column of the csv file (all Line names)
    V = { row[0] for row in L }

    # Generate a set of line pairs, which are all unique unordered pairs of lines
    # Edges are the start and end vertices in V which is the set of lines
    # Checks the LinesDictionary for the stations associated with the lines
    E = {
    (u, v)
    for u in V
    for v in V
    if LinesDictionary[u] & LinesDictionary[v]
    }
    
    # Make the lines undirected
    E = E | { (v, u) for (u, v) in E }
    
    # Calculate transferDistance by using graphs.distance with the lines vertices set, edge set, and onboarding Line and destination Line
    transferDistance = [
    graphs.distance(V, E, u, v)
    for u in V
    for v in V
    ]
    
    # Retrieve the maximum distance from the list of distances as an integer
    t = max(transferDistance)
    
    # Return maximum minimal transfer distance value
    return t

def assignCrew(crew, timeslots):
    
    # Times of each shift as a dictionary
    shiftTimes = {
        'Morning': (4, 12),
        'Day': (9, 17),
        'Night': (16, 24)
    }
    
    # Times of each unavailable shift time, as a dictionary for those that are peekTimeRestricted
    unavailablePeekTimes = {
        'MorningPeekTime': (8, 10),
        'AfternoonPeekTime': (16, 18)
        }
    
    # Generate a set of vertices that is the train's timeslot (line, startTime, endTime) and the role that the train needs (one driver and one guard).
    # For the left side of the bipartite graph. 
    trainVertices = { (line, startTime, endTime, role) for (line, startTime, endTime, _) in timeslots for role in ('Driver', 'Guard') }
    
    # Generate a set of vertices that uses the name of each person in crew for the right side of the bipartite graph
    peopleVertices = { name for (name, _, _, _, _) in crew }
    
        
    # Generate an edge from peopleVertices to trainVertices if the person meets all the requirements/constraints to operate the role on that train
    E = {
        # Generate a tuple that is the peopleVertices as u and trainVertices as v
        ((line, startTime, endTime, role), name)
        # Access all variables in crew (people data)
        for (name, roles, etcs_certified, shift, peekTimeRestricted) in crew
        # Access all information in timeslots (train data)
        for (line, startTime, endTime, etcs_required) in timeslots
        # Check the person's role
        for role in ('Driver', 'Guard')
        if role in roles
        # Person cannot take a shift that is before allocated shift startTime, or after allocated shift endTime
        if shift in shiftTimes and shiftTimes[shift][0] <= startTime and endTime <= shiftTimes[shift][1]
        # If the person is peek time restricted, check whether they can take a shift ensuring it does not operate in peek times
        if not peekTimeRestricted or not (startTime < unavailablePeekTimes['MorningPeekTime'][1] and endTime > unavailablePeekTimes['MorningPeekTime'][0])
        and not (startTime < unavailablePeekTimes['AfternoonPeekTime'][1] and endTime > unavailablePeekTimes['AfternoonPeekTime'][0])
        # If the person is a driver, they must be etcs_certified if the train is etcs_required
        if role == 'Guard' or not etcs_required or etcs_certified
    }
    
    # Call maxMatching to match as many people to trains as possible on the bipartite graph
    validMatches = digraphs.maxMatching(trainVertices, peopleVertices, E)
    
    # Generate a dictionary for all the valid matches
    validMatchesDictionary = { a: b for a, b in validMatches}
    
    # Assign the drivers and guards into dictionary, with the desired output format being the key "Timeslot: ('Driver, Guard')"
    assignment = {
        # Create dictionary key
        f"{line}-{startTime}-{endTime}": (
            validMatchesDictionary[(line, startTime, endTime, 'Driver')],
            validMatchesDictionary[(line, startTime, endTime, 'Guard')]
        )
        # Look through validMatchesDictionary for a value for each assignment
        for (line, startTime, endTime, _) in trainVertices
        if (line, startTime, endTime, 'Driver') in validMatchesDictionary and (line, startTime, endTime, 'Guard') in validMatchesDictionary
    }
    
    # All timeslots that are needed to be connected in trainVertices
    requiredTimeslots = { (line, startTime, endTime) for (line, startTime, endTime, _) in trainVertices }
    
    # Ensure all requiredTimeslots are filled with an assignment, as every train timeslot position must be assigned
    return assignment if len(assignment) == len(requiredTimeslots) else None
    
def trainSchedule(timeSlots):

    # Generate vertices of timeSlots V for each given timeSlots in the provided data structure
    V = { (line, startTime, endTime) for (line, startTime, endTime) in timeSlots }
    
    # Define relocationTime constraint of 1 hour, as all time is in integers from 0 to 24
    relocationTime = 1
    
    # Generate edge set E of conflicts to build conflict graph
    E = {
        (timeSlot1, timeSlot2)
        # Check starting vertices and ending vertices
        for timeSlot1 in V
        for timeSlot2 in V
        # Check for conflicting timeSlots, where a timeSlot must overlap with another timeSlot, and have enough time to relocate (1 hour)
        if timeSlot1 != timeSlot2 and (
        timeSlot1[1] < timeSlot2[2] + relocationTime and
        timeSlot2[1] < timeSlot1[2] + relocationTime
        )
    }

    # Make the edges in the conflict graph undirected
    E = E | { (timeSlot2, timeSlot1) for (timeSlot1, timeSlot2) in E }

    # Generate the minimum amount of trains required, by finding the minimum amount of colours needed to colour the conflict graph
    k, C = graphs.minColouring(V, E)
    return k
    
def trackNetworkCapacity(trackNetwork, blockTimes, destination):

    # Generate edge set as pairs from trackNetwork data structure
    E = {
        (a, b)
        for block in trackNetwork
        for a, b in itertools.pairwise(block)
    }
    
    # Generate vertices set from edge set E, where pairs are split for each individual station/signal
    V = { a for a, _ in E } | { b for _, b in E }
    # outer_stations set includes all stations that trackNetwork begins with, as they indicate the start of a block
    O = { station[0] for station in trackNetwork }

    # Define weight for maxFlow calculation
    w = {
        # Apply calculation to determine weight of each edge
        (a, b): 60 // blockTimes[(a, b)]
        # Generate a calculated weight for each edge in edge set E
        for (a, b) in E
        }
    
    # Generate a super source to unify the sources into an individual source to calculate maxFlow
    superSource = 'Super Source'
    # Add super_source to the vertices
    V = V | {superSource}
    # Add super source edges to the outer stations
    E = E | { (superSource, s) for s in O }
    # Add weights for super source edges to the outer stations, set super source value to 60 as it is the maximum amount of trains per block (60/60)
    w = w | { (superSource, s): 60 for s in O }

    # Calculate maxFlow using digraphs.py library function
    flow = digraphs.maxFlow(V, E, w, superSource, destination)

    # Return maxFlow originating from super source, indicating the maxFlow from the source 
    maxFlowSource = sum(f for (u, _), f in flow.items() if u == superSource)
    
    # Return maxFlow going into destination, indicating the maxFlow into the drain
    maxFlowDrain = sum(f for (_, v), f in flow.items() if v == destination)
    
    # return the maxFlows if the maximum flow from the source is the maximum flow into the drain
    return maxFlowSource if maxFlowSource == maxFlowDrain else None