#!/usr/bin/env python
"""
@file    runner.py
@author  Lena Kalleske
@author  Daniel Krajzewicz
@author  Michael Behrisch
@author  Jakob Erdmann
@date    2009-03-26
@version $Id: runner.py 19535 2015-12-05 13:47:18Z behrisch $

Tutorial for traffic light control via the TraCI interface.

SUMO, Simulation of Urban MObility; see http://sumo.dlr.de/
Copyright (C) 2009-2015 DLR/TS, Germany

This file is part of SUMO.
SUMO is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.
"""

import os
import sys
import optparse
import subprocess
import socket
import random

# we need to import python modules from the $SUMO_HOME/tools directory
try:
    sys.path.append(os.path.join(os.path.dirname(
        __file__), '..', '..', '..', '..', "tools"))  # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(
        os.path.dirname(__file__), "..", "..", "..")), "tools"))  # tutorial in docs
    from sumolib import checkBinary
except ImportError:
    sys.exit(
        "please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")

import traci
from time import sleep

# the port used for communicating with your sumo instance
PORT = 8873


def run():
    """execute the TraCI control loop"""

    # we start with phase 2 where EW has green
    # traci.trafficlights.setPhase("0", 2)
    # client_socket = socket.socket()
    # client_socket.connect(('127.0.0.1', 9999))

    with open("data/zorilor.rou.xml", "w") as routes:
        print >> routes, """<routes>
        <vType accel="1.0" decel="5.0" id="Car" length="7.0" color="1,0,0" maxSpeed="100.0" sigma="0.0"/>
        <route id="r0" edges="23893226 -7932203#1 -7932203#0 10510909#1 10510909#2 -8028548 7927518"/>
        <route id="r1" edges="-7927518 8028548 10510909#3 10510909#4 10510909#0 7932203#0 7932203#1 -23893226"/>
        <route id="r2" edges="55557174 10510909#2 10510909#3 10510908#0"/>
        <route id="r3" edges="-10510908#0 10510909#4 10510909#0 10510909#1 -55557174"/>"""
        for i in range(20):
            routeId = random.randint(0, 3)
            lane = 0
            if (routeId != 0) & (routeId != 1):
                lane = random.randint(0, 1)
            print >> routes, '    <vehicle depart="%i" departLane="%i" id="veh%i" route="r%i" type="Car"/>' % (
                i, lane, i, routeId)
        print >> routes, "</routes>"

    traci.init(PORT)
    step = 0

    while traci.simulation.getMinExpectedNumber() > 0:
        if traci.vehicle.getRoadID("veh0") != "":
            spatialPosition = traci.simulation.convert2D(traci.vehicle.getRoadID("veh0"),
                                                         traci.vehicle.getLanePosition("veh0"), laneIndex=0,
                                                         toGeo=False)
            sumoPosition = traci.vehicle.getPosition("veh0")
            geoPosition = traci.simulation.convertGeo(spatialPosition[0], spatialPosition[1], fromGeo=False)
        # client_socket.send(str(geoPosition[0]) + "," + str(geoPosition[1]) + "\r\n")
        traci.simulationStep()
        step += 1
        sleep(0.2)
    traci.close()
    # client_socket.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    # sumoBinary = checkBinary('sumo')
    sumoBinary = checkBinary('sumo-gui')

# first, generate the route file for this simulation

# this is the normal way of using traci. sumo is started as a
# subprocess and then the python script connects and runs
sumoProcess = subprocess.Popen([sumoBinary, "-c", "data/zorilor.sumocfg", "--tripinfo-output",
                                "tripinfo.xml", "--remote-port", str(PORT)], stdout=sys.stdout, stderr=sys.stderr)
run()
sumoProcess.kill()
