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
import json

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


def send_data_to_rsu(client_socket, cars_in_perimeter):
    for veh_id in cars_in_perimeter:
        spatial_pos = traci.simulation.convert2D(traci.vehicle.getRoadID(veh_id), traci.vehicle.getLanePosition(veh_id), 0, False)
        geo_pos = traci.simulation.convertGeo(spatial_pos[0], spatial_pos[1], False)
        position = {}
        position['latitude'] = str(geo_pos[1])
        position['longitude'] = str(geo_pos[0])
        data = {}
        data['position'] = position
        data['vehicleId'] = veh_id
        data['speed'] = traci.vehicle.getSpeed(veh_id)
        data['acceleration'] = traci.vehicle.getAccel(veh_id)
        client_socket.send(json.dumps(data) + "\n")


def run():
    # create_random_routes()

    client_socket = socket.socket()
    client_socket.connect(('127.0.0.1', 9999))

    traci.init(PORT)
    step = 0
    cars_in_perimeter = set()

    while traci.simulation.getMinExpectedNumber() > 0:
        manage_car_set(cars_in_perimeter)
        send_data_to_rsu(client_socket, cars_in_perimeter)
        traci.simulationStep()
        step += 1
        # sleep(0.1)
    traci.close()
    client_socket.close()
    sys.stdout.flush()


def manage_car_set(car_set):
    manage_car_set_lane(car_set, "a")
    # manage_car_set_lane(car_set, "b")


def manage_car_set_lane(car_set, lane):
    number_of_vehicles_entered = traci.inductionloop.traci.inductionloop.getLastStepVehicleNumber(lane + "_start")
    number_of_vehicles_exiting = traci.inductionloop.traci.inductionloop.getLastStepVehicleNumber(lane + "_end")
    vehicles_ids_entered = traci.inductionloop.traci.inductionloop.getLastStepVehicleIDs(lane + "_start")
    vehicles_ids_exiting = traci.inductionloop.traci.inductionloop.getLastStepVehicleIDs(lane + "_end")
    if number_of_vehicles_entered > 0:
        for i in range(len(vehicles_ids_entered)):
            # if traci.vehicle.getRouteID(vehicles_ids_entered[i]) == "r0":
            #     traci.vehicle.setSpeedMode(vehicles_ids_entered[i], 0)
            car_set.add(vehicles_ids_entered[i])
    if number_of_vehicles_exiting > 0:
        for i in range(len(vehicles_ids_exiting)):
            car_set.discard(vehicles_ids_exiting[i])


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# def create_car_model():
#     with open("data/zorilor.rou.xml", "w") as routes:
#         print >> routes, """<routes>
#     <vType accel="7.0" decel="2.0" id="model1" length="7.0" color="1,0,0" maxSpeed="60.0" sigma="0.0"/>
#     <vType accel="7.0" decel="2.5" id="model2" length="7.0" color="1,0,0" maxSpeed="60.0" sigma="0.0"/>
#     <vType accel="7.5" decel="1.5" id="model3" length="7.0" color="1,0,0" maxSpeed="60.0" sigma="0.0"/>"""
#
#
# def create_random_routes():
#     create_car_model()
#     with open("data/zorilor.rou.xml", "a") as routes:
#         print >> routes, """
#     <route id="r0" edges="7926735#0 7926735#1 55557174"/>
#     <route id="r1" edges="289919844#0 289919844#1 289919844#2 55557174"/>"""
#         for i in range(10):
#             route_id = 1
#             car_id = random.randint(1, 3)
#             lane = random.randint(0, 1)
#             print >> routes, '    <vehicle depart="%i" departLane="%i" id="veh%i" route="r%i" type="model%i"/>' % (
#                 i * 6, lane, i, route_id, car_id)
#         for i in range(10):
#             route_id = 0
#             car_id = random.randint(1, 3)
#             lane = 0
#             print >> routes, '    <vehicle depart="%i" departLane="%i" id="veh%i" route="r%i" type="model%i"/>' % (
#                 i * 15 + 60, lane, i + 10, route_id, car_id)
#         print >> routes, "</routes>"

def create_car_model():
    with open("data/zorilor.rou.xml", "w") as routes:
        print >> routes, """<routes>
    <vType accel="5.0" decel="2.0" id="model1" length="7.0" color="1,0,0" maxSpeed="60.0" sigma="0.0"/>
    <vType accel="3.0" decel="2.5" id="model2" length="7.0" color="1,0,0" maxSpeed="45.0" sigma="0.0"/>
    <vType accel="4.0" decel="1.5" id="model3" length="7.0" color="1,0,0" maxSpeed="53.0" sigma="0.0"/>"""


def create_random_routes():
    create_car_model()
    with open("data/zorilor.rou.xml", "a") as routes:
        print >> routes, """
    <route id="r0" edges="-46331812 31649598#0 31649598#1"/>
    <route id="r1" edges="-31581244#0 46331812"/>
    <route id="r2" edges="-31649598#1 -31649598#0 31581244#0"/>"""
        for i in range(20):
            route_id = random.randint(0, 1)
            car_id = random.randint(1, 3)
            lane = 0
            print >> routes, '    <vehicle depart="%i" departLane="%i" id="veh%i" route="r%i" type="model%i"/>' % (
                i * 2, lane, i, route_id, car_id)
        print >> routes, "</routes>"


if __name__ == "__main__":
    options = get_options()
    sumoBinary = checkBinary('sumo')
    # sumoBinary = checkBinary('sumo-gui')

sumoProcess = subprocess.Popen([sumoBinary, "-c", "data/zorilor.sumocfg", "--tripinfo-output", "tripinfo.xml", "--remote-port", str(PORT)], stdout=sys.stdout, stderr=sys.stderr)
run()
sumoProcess.kill()
