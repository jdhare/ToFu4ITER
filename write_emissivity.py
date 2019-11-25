from synthetic_emissivity import ff
import TFI_read_camera_parameters as tfi
import csv
from login_details import usr, pwd

camera_table = tfi.ReadCollimatorTable(usr=usr, pwd=pwd, version=0.25)

p_fmt='{:.8f}'

with open('output_data/Bolometer_power.csv', mode='w') as power:
    writer = csv.writer(power, delimiter=',')
    writer.writerow(['Camera Name', 'Channel','Power [W]', 'Etendue [m^2]'])

    #Vacuum vessel cameras
    camera_table.create_VV_cameras()
    for camera in camera_table.VV_cameras.values():
        res, m = camera.calc_signal(ff, Brightness=False, plot=False)
        power_W = res.data[0]/2.0 #factor 2 due to ECRH grids
        for channel, pow in enumerate(power_W):
            writer.writerow(['VV'+camera.Id.Name, channel+1, p_fmt.format(pow), camera.Etendues[0]])

    # Divertor cameras
    camera_table.create_DC_cameras()
    for camera in camera_table.DC_cameras.values():
        res, m = camera.calc_signal(ff, Brightness=False, plot=False)
        power_W = res.data[0]/2.0 #factor 2 due to ECRH grids
        for channel, pow in enumerate(power_W):
            writer.writerow(['DC'+camera.Id.Name, channel+1, p_fmt.format(pow), camera.Etendues[0]])

    # Port plug collimator cameras
    camera_table.create_PPC_cameras()
    for camera in camera_table.PPC_cameras.values():
        res, m = camera.calc_signal(ff, Brightness=False, plot=False)
        power_W = res.data[0]/2.0 #factor 2 due to ECRH grids
        for channel, pow in enumerate(power_W):
            writer.writerow([camera.Id.Name, channel+1, p_fmt.format(pow), camera.Etendues[0]])

    #Port plug pinhole cameras
    camera_table.create_PPP_cameras()
    for camera in camera_table.PPP_cameras.values():
        for i, sub_cam in enumerate(camera):
            res, m = sub_cam.calc_signal(ff, Brightness=False, plot=False)
            power_W = res.data[0]/2.0 #factor 2 due to ECRH grids
            for channel, pow in enumerate(power_W):
                writer.writerow([sub_cam.Id.Name, i*5+channel + 1, p_fmt.format(pow), sub_cam.Etendues[0]])





