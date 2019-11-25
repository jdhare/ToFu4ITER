import TFI_read_camera_parameters as tfi
import matplotlib.pyplot as plt
plt.switch_backend('Qt5Agg')
from login_details import usr, pwd

camera_table = tfi.ReadCollimatorTable(usr=usr, pwd=pwd, version=0.23)

fig, ax = plt.subplots()
ax.set_aspect('equal')

#Port plug pinhole cameras
#dL: dictionary for plotting lines, 'c' is colour.
camera_table.create_PPP_cameras()
for camera in camera_table.PPP_cameras.values():
    for sub_cam in camera:
        sub_cam.plot([ax], proj='Cross',dL={'c':'green'})

#Port plug collimator cameras
camera_table.create_PPC_cameras()
for camera in camera_table.PPC_cameras.values():
    camera.plot([ax], proj='Cross',dL={'c':'blue'})

#Divertor cameras
camera_table.create_DC_cameras()
for camera in camera_table.DC_cameras.values():
    camera.plot([ax], proj='Cross')

#Vacuum vessel cameras
camera_table.create_VV_cameras()
for camera in camera_table.VV_cameras.values():
    camera.plot([ax], proj='Cross', dL={'c':'red'})