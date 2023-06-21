
param map = localPath('../../tests/formats/opendrive/maps/CARLA/Town01.xodr')
param carla_map = 'Town01'
model scenic.simulators.carla.model

EGO_MODEL = 'vehicle.lincoln.mkz_2017'

import carla

ego = Car with behavior AutopilotBehavior()

for i in range(15):
	civildrone =CivilianDrone with elevation Range(5,20), with behavior DroneBehavior()

for i in range(15):
	mildrone =MilitaryDrone with elevation Range(5,20), with behavior DroneBehavior()

require ego can see civildrone
