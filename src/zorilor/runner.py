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
        message = client_socket.recv(1024).splitlines()[0]
        if message != "Nu":
            print message
            traci.vehicle.setStop(message, traci.vehicle.getRoadID(message), 105, 0, 10)


def run():
    create_random_routes()

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
        sleep(0.3)
    traci.close()
    client_socket.close()
    # sys.stdout.flush()


def manage_car_set(car_set):
    manage_car_set_lane(car_set, "a")
    manage_car_set_lane(car_set, "b")


def manage_car_set_lane(car_set, lane):
    number_of_vehicles_entered = traci.inductionloop.traci.inductionloop.getLastStepVehicleNumber(lane + "_start")
    number_of_vehicles_exiting = traci.inductionloop.traci.inductionloop.getLastStepVehicleNumber(lane + "_end")
    vehicles_ids_entered = traci.inductionloop.traci.inductionloop.getLastStepVehicleIDs(lane + "_start")
    vehicles_ids_exiting = traci.inductionloop.traci.inductionloop.getLastStepVehicleIDs(lane + "_end")
    if number_of_vehicles_entered > 0:
        for i in range(len(vehicles_ids_entered)):
            # if (random.uniform(0, 1) > 0.5) and (traci.vehicle.getRouteID(vehicles_ids_entered[i]) == "r0"):
            if traci.vehicle.getRouteID(vehicles_ids_entered[i]) == "r0":
                traci.vehicle.setSpeedMode(vehicles_ids_entered[i], 0)
            car_set.add(vehicles_ids_entered[i])
    if number_of_vehicles_exiting > 0:
        for i in range(len(vehicles_ids_exiting)):
            car_set.discard(vehicles_ids_exiting[i])


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", "store_true", False, "run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


def create_car_model():
    with open("data/zorilor.rou.xml", "w") as routes:
        print >> routes, '<routes>'
        for i in range(10):
            vehicle_accel = random.uniform(3, 5)
            vehicle_decel = random.uniform(1.5, 2.5)
            vehicle_max_speed = random.uniform(17, 20)
            print >> routes, '<vType accel="%f" decel="%f" id="model%i" length="7.0" color="1,0,0" maxSpeed="%f" sigma="0.0"/>' % (
                vehicle_accel, vehicle_decel, i, vehicle_max_speed)


def create_random_routes():
    create_car_model()
    with open("data/zorilor.rou.xml", "a") as routes:
        print >> routes, """
    <route id="r0" edges="-46331812 31649598#0 31649598#1"/>
    <route id="r1" edges="-31581244#0 46331812"/>
    <route id="r2" edges="-31649598#1 -31649598#0 31581244#0"/>"""
        depart = 0
        for i in range(20):
            route_id = random.randint(0, 1)
            car_id = random.randint(0, 9)
            depart = random.randint(depart, depart + 10)
            lane = 0
            print >> routes, '<vehicle depart="%i" departLane="%i" id="veh%i" route="r%i" type="model%i"/>' % (
                depart, lane, i, route_id, car_id)
        print >> routes, "</routes>"


if __name__ == "__main__":
    # options = get_options()
    # sumoBinary = checkBinary('sumo')
    sumoBinary = checkBinary('sumo-gui')

sumoProcess = subprocess.Popen([sumoBinary, "-c", "data/zorilor.sumocfg", "--tripinfo-output", "tripinfo.xml", "--remote-port", str(PORT)], stdout=sys.stdout, stderr=sys.stderr)
run()
sumoProcess.kill()
