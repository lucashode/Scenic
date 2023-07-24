
param map = localPath('../../tests/formats/opendrive/maps/CARLA/Town01.xodr')
param carla_map = 'Town01'
model scenic.simulators.carla.model



import carla

ego = Debris with elevation 10

for i in range(10):
	civildrone =CivilianDrone with elevation Range(10,20), with behavior FlyingBehavior()

for i in range(10):
	mildrone =MilitaryDrone with elevation Range(10,20), with behavior FlyingBehavior()

for i in range(10):
	bird =Bird with elevation Range(10,20), with behavior FlyingBehavior()

require ego can see civildrone
