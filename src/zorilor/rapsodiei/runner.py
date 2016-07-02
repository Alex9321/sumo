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

accident_cars = set()


# def create_accident(veh_id):
#     if (veh_id in accident_cars) and (traci.vehicle.getLanePosition > 20) and (traci.vehicle.getLanePosition(veh_id) < 85):
#         traci.vehicle.setSpeedMode(veh_id, 0)
#         traci.vehicle.setSpeed(veh_id, traci.vehicle.getMaxSpeed(veh_id))
#     else:
#         traci.vehicle.setSpeedMode(veh_id, 31)


def create_accident(veh_id):
    if (traci.vehicle.getRouteID(veh_id) == "r0") and (traci.vehicle.getLanePosition > 20) and (traci.vehicle.getLanePosition(veh_id) < 70):
        traci.vehicle.setSpeedMode(veh_id, 0)
        traci.vehicle.setSpeed(veh_id, traci.vehicle.getMaxSpeed(veh_id))
    else:
        traci.vehicle.setSpeedMode(veh_id, 31)


def send_data_to_rsu(client_socket, cars_in_perimeter):
    for veh_id in cars_in_perimeter:
        # create_accident(veh_id)
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
        if message != "Safe":
            print message
            traci.vehicle.setStop(message, traci.vehicle.getRoadID(message), 85, 0, 300)


def run():
    # create_simulation_scenario()
    client_socket = socket.socket()
    client_socket.connect(('127.0.0.1', 9999))
    traci.init(PORT)
    step = 0
    cars_in_perimeter = set()
    for i in range(200):
        if random.uniform(0, 1) > 0.5:
            accident_cars.add("veh" + str(i))

    while traci.simulation.getMinExpectedNumber() > 0:
        manage_car_set(cars_in_perimeter)
        send_data_to_rsu(client_socket, cars_in_perimeter)
        traci.simulationStep()
        step += 1
        sleep(0.2)
    traci.close()
    client_socket.close()


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
            car_set.add(vehicles_ids_entered[i])
    if number_of_vehicles_exiting > 0:
        for i in range(len(vehicles_ids_exiting)):
            car_set.discard(vehicles_ids_exiting[i])


def create_car_model():
    with open("data/zorilor.rou.xml", "w") as routes:
        print >> routes, '<routes>'
        for i in range(200):
            vehicle_accel = random.uniform(10, 15)
            vehicle_decel = random.uniform(1.5, 2.0)
            vehicle_max_speed = random.uniform(18, 22)
            print >> routes, '<vType accel="%f" decel="%f" id="model%i" length="7.0" color="1,0,0" maxSpeed="%f" sigma="0.0"/>' % (
                vehicle_accel, vehicle_decel, i, vehicle_max_speed)


def create_simulation_scenario():
    create_car_model()
    with open("data/zorilor.rou.xml", "a") as routes:
        print >> routes, """
    <route id="r0" edges="7926735#0 7926639#0"/>
    <route id="r1" edges="-7926735#1 7926639#0"/>"""
        depart = 0
        depart_r0 = 0
        for i in range(200):
            # route_id = random.randint(0,1)
            route_id = 0
            car_id = random.randint(0, 199)
            depart_r0 += 1
            depart += 15
            # if depart_r0 == 20:
            #     route_id = 0
            #     depart_r0 = 0
            print >> routes, '<vehicle depart="%i" departLane="0" id="veh%i" route="r%i" type="model%i"/>' % (
                depart, i, route_id, car_id)
        print >> routes, "</routes>"


if __name__ == "__main__":
    # sumoBinary = checkBinary('sumo')
    sumoBinary = checkBinary('sumo-gui')

sumoProcess = subprocess.Popen([sumoBinary, "-c", "data/zorilor.sumocfg", "--tripinfo-output", "tripinfo.xml", "--remote-port", str(PORT)], stdout=sys.stdout, stderr=sys.stderr)
run()
sumoProcess.kill()
