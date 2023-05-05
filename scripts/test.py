import carb
import sys
import os
import rospy
import numpy as np
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from omni.isaac.kit import SimulationApp

headless = False

CONFIG = {"renderer": "RayTracedLighting", "headless": headless}
simulation_app = SimulationApp(CONFIG)

from omni.isaac.core.utils.extensions import enable_extension
enable_extension("omni.isaac.conveyor")
enable_extension("omni.isaac.ros_bridge")

# # # Default Livestream settings
# livestream = True
# if livestream:
#     simulation_app.set_setting("/app/window/drawMouse", True)
#     simulation_app.set_setting("/app/livestream/proto", "ws")
#     simulation_app.set_setting("/app/livestream/websocket/framerate_limit", 30)
#     simulation_app.set_setting("/ngx/enabled", False)
#     # Note: Only one livestream extension can be enabled at a time
#     # Enable Native Livestream extension
#     # Default App: Streaming Client from the Omniverse Launcher
#     enable_extension("omni.kit.livestream.native")

import rosgraph
if not rosgraph.is_master_online():
    carb.log_error("Please run roscore before executing this script")
    simulation_app.close()
    exit()

rospy.init_node("ifl_demo", anonymous=False, disable_signals=True, log_level=rospy.ERROR)


import omni
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import viewports, stage, extensions, prims, rotations, nucleus
from omni.isaac.core_nodes.scripts.utils import set_target_prims
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units, get_current_stage


from omni.isaac.core import World
from scripts.conveyor.conveyor_task import ConveyorTask
from omni.isaac.core.prims import XFormPrim



my_world = World(stage_units_in_meters=1.0)
my_world.scene.add_default_ground_plane()


scripts_path = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.dirname(scripts_path)
print("base_path", base_path)


my_task = None

with open(scripts_path+'/config.json') as f:
    d = json.load(f)
    print(type(d),d)
    for key, value in d.items():
        if value["robot_type"] == "Conveyor":
            print("start loading conveyor")
            conveyor_model = base_path + "/src/conveyor/mesh/conveyor.usd"
            conveyor_prim = value["world_prim"]
            conveyor_name = value["robot_name"]
            conveyor_init_position = np.array(value["init_position"])
            conveyor_init_orientation = np.array(value["init_rotation"])
            conveyor_init_scale = np.array(value["init_scale"])
            my_task = ConveyorTask(prim_path = conveyor_prim, 
                                    name = conveyor_name, 
                                    usd_path = conveyor_model,
                                    position = conveyor_init_position,
                                    orientation = conveyor_init_orientation,
                                    scale = conveyor_init_scale)
            my_world.add_task(my_task)

my_world.reset()

# load cube
from omni.isaac.core.objects import DynamicCuboid
cube_prim_path = "/World/Cube"
my_cube_initial_position = np.array([0.0, 0.3, 0.1]) / get_stage_units()
my_cube = my_world.scene.add(
            DynamicCuboid(
                name="cube",
                position=my_cube_initial_position,
                prim_path=cube_prim_path,
                # scale=np.array([0.50, 0.50, 0.50]) / get_stage_units(),
                color=np.array([0, 0, 1.0]),
            )
)

simulation_app.update()
my_world.reset()

# # # need to initialize physics getting any articulation..etc
# simulation_context = SimulationContext(stage_units_in_meters=1.0)
# simulation_context.initialize_physics()
# simulation_context.play()


while simulation_app.is_running():

    # runs with a realtime clock
    simulation_app.update()
    my_task._conveyor_node.publish_all()
    # simulation_context.step(render=True)
    # print("time: ", time.time()) # every 1/20s
    for i in range(10000):  # forget how to set this time interval
        if i%100 == 0:  # change to 1000, faster, but too fast
            my_task._conveyor_node.update_test()
            


simulation_app.close()

# Cleanup
rospy.signal_shutdown("Closing ROS Node")
simulation_app.close()
