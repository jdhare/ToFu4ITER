'''
module purge
module load IMAS/3.23.1-4.0.4
module load ToFu/1.4.0-intel-2018a-Python-3.6.4
module load IPython/6.3.1-intel-2018a-Python-3.6.4 
ipython

import TFI_read_camera_parameters as tfi
u='username'
p='password'
#This next line downloadsn the optimisation spreadsheet
#Stores the data for the various camera types in different dictionaries
#And calculates the location 'D' and the line of sight unit vector 'u'
#for each camera
tf=tfi.ReadCollimatorTable(version=0.21, usr=u, pwd=p)
#this next line creates a dictionary of the Divertor Collimator cameras
#Similar functions exist for VV, PPC (port plug collimator) and PPP (port plug pinhole, not yet implemented
tf.create_DC_cameras()
tf.DC_cameras # is a dictionary
c=tf.DC_cameras['5410'] #is a specific camera

#you can clumsily plot the LoS with
tfi.plot_save(c)
#Use c.plot? for more information about plotting.
#Actually, the ? interface is quite good for most ToFu objects for more information.
'''

import pyexcel_ods3 as ods
import requests, os
from urllib.parse import urlparse
import numpy as np
import tofu as tf
import matplotlib.pyplot as plt

delta_D = 5.08 * 1e-3  # separation between channels in mm
channels = np.array([-2, -1, 0, 1, 2])  # five channels per sensor!

config = tf.geom.utils.create_config('A2')  # this is the ITER vacuum vessel


def trim(X):
    """remove empty lists from list of lists"""
    return [x for x in X if x != []]


class ReadCollimatorTable:
    def __init__(self, filename=None, url='https://bscw.rzg.mpg.de/bscw/bscw.cgi/d424071/CollimatorOptimisation_ITER',
                 version=None, usr=None, pwd=None):
        """
        Downloads the Collimator Optimisation table from BCSW (or uses a local version),
        Gathers the data for the Vacuum Vessel (VV) and Divertor Cassette (DC) cameras
        Uses this data to create dictionaries of parameters for each camera
        These parameters can then be used to calculate the location (D) and normal (u) of each LOS in a 5 channel collimator
        D and u can then be used by tofu.geom.CamLOS1D(dgeom=(D,u)...) to create a camera with 5 channels.

        :param filename: path to local file. Leave as None to load file from BCSW
        :param url: url of remote file on BCSW. Leave as default
        :param version: you must specify a version if downloading from BCSW. The version matters a lot!
        :param usr: your BCSW username
        :param pwd: your BCSW password
        """
        if filename is None:
            if version is None:
                raise Exception("Specify a version. Know what version you want.")
            if version is not None:
                url = url + '.ods?version=' + str(version)
            if usr is None:
                raise Exception("Please enter a BSCW username")
            if pwd is None:
                raise Exception("Please enter a BSCW password which corresponds to the username")

            print("Loading:" + url)
            resp = requests.get(url, auth=(usr, pwd))
            print("Response:" + str(resp.status_code))
            filename = os.path.basename(urlparse(url).path) + '.ods'
            open(filename, 'wb').write(resp.content)
            self.filename = filename
        self.raw_data = ods.get_data(filename)

        self._VV = trim(self.raw_data['Geometrical_data_VV'])  # remove empty lists
        self._DC = trim(self.raw_data['Geometrical_data_DC'])
        self._PPC = trim(self.raw_data['PortPlugs_Collimator'])
        self._PPP = trim(self.raw_data['PortPlugs_PinHole'])

        self.column_headings_Col = self._DC[10]  # use these as keys in the following dictionaries
        self.column_headings_PH = self._PPP[9]  # use these as keys in the following dictionaries

        self.start_of_cameras = 12  # row upon which the cameras start
        self.DC_parameters = self.gather_parameters_Col(self._DC, self.column_headings_Col,
                                                        start_row=12)  # empty dictionaries.
        self.VV_parameters = self.gather_parameters_Col(self._VV, self.column_headings_Col, start_row=12)
        self.PPC_parameters = self.gather_parameters_Col(self._PPC, self.column_headings_Col, start_row=12)
        self.PPP_parameters = self.gather_parameters_PH(self._PPP, self.column_headings_PH, start_row=11)

        for camera in self.DC_parameters.values():
            D, u = self.calculate_Du_Col(camera)
            camera['D'] = D
            camera['u'] = u
        for camera in self.VV_parameters.values():
            D, u = self.calculate_Du_Col(camera)
            camera['D'] = D
            camera['u'] = u
        for camera in self.PPC_parameters.values():
            D, u = self.calculate_Du_Col(camera)
            camera['D'] = D
            camera['u'] = u
        for camera in self.PPP_parameters.values():
            D, pinhole = self.calculate_Du_PH(camera)
            camera['D'] = D
            camera['pinhole'] = pinhole

    def gather_parameters_Col(self, sheet, column_headings, start_row):
        dParameters = {}
        for camera in sheet[start_row:]:
            # Create dictionary with camera name as key and another dict as the value
            # This dictionary contains the column headings as keys and the values from the spreadsheet
            k = str(camera[1])
            d = dict(zip(column_headings, camera))
            name = d['TP'] + '_' + d['PP']
            if name == '_':
                name = str(d['No.'])
            d['Name'] = name
            dParameters[name] = d
        return dParameters

    def gather_parameters_PH(self, sheet, column_headings, start_row):
        dParameters = {}
        for camera in sheet[start_row:]:
            # Create dictionary with camera name as key and another dict as the value
            # This dictionary contains the column headings as keys and the values from the spreadsheet
            name = camera[2] + '_' + camera[3]
            dParameters[name] = dict(zip(column_headings, camera))
            dParameters[name]['Name']=name
        return dParameters

    def calculate_Du_Col(self, camera, RZ=True):
        R = camera['R']  # R,Z coordinates of central detector
        Z = camera['z']
        dir = camera['dir.'] * (np.pi / 180.0)  # convert angle to radians. Angle measured from horizontal (XY) plane.
        d_vec = np.array([R, 0, Z])  # displacement vector for center of front face of central LOS
        n_vec = np.array([np.cos(dir), 0, np.sin(dir)])  # normal vector to center of central LOS
        y_vec = np.array([0, 1, 0])  # the vector in the "toroidal" direction, currently set as +Y
        p_vec = np.cross(n_vec, y_vec)  # vector between adjacent channels in the same camera

        theta = camera['theta'] * (np.pi / 180.0)
        D = np.array([d_vec + p_vec * delta_D * i for i in channels])
        u = np.array([[np.cos(dir + c * theta), 0, np.sin(dir + c * theta)] for c in channels])
        return D, u

    def calculate_Du_PH(self, camera, RZ=True):
        R = camera['R']  # R,Z coordinates of pinhole
        Z = camera['z']
        pinhole=np.array([R, 0, Z])

        dir = camera['dir.'] * (np.pi / 180.0)  # convert angle to radians. Angle measured from horizontal (XY) plane.
        theta = camera['theta'] * (np.pi / 180.0)  # angle between adjacent channels

        d_vec = np.array([R, 0, Z])  # displacement vector for center pinhole
        y_vec = np.array([0, 1, 0])  # the vector in the "toroidal" direction, currently set as +Y

        N_c = camera['N_SL']  # number of channels
        N_d = N_c // 5  # group channels into 5s
        L_c = camera['Lc'] * 1e-3  # distance from pinhole to central channel of detectors
        Ds = np.zeros((N_d, 5, 3))
        us = np.zeros((N_d, 5, 3))
        # odd case first
        if N_d % 2 is 1:
            detectors = np.arange(-(N_d - 1) / 2, (N_d - 1) / 2 + 1, 1)  # detectors from eg -2 to 2, central is 0
        if N_d % 2 is 0:
            detectors = np.arange(- N_d / 2, N_d / 2, 1) + 0.5  # detectors from eg -2 to 2, central is 0

        dir0 = detectors * 5 * theta + dir  # 5 is number of channels, so central channel of adjacent detectors differ by 5.
        n_vec0 = -1 * np.array(
            [[np.cos(dd), 0, np.sin(dd)] for dd in dir0])  # normal vectors to detector central channels
        D0 = np.array([d_vec + nn * L_c for nn in n_vec0])  # location of detector central channels
        p_vecs = np.array(
            [np.cross(nv, y_vec) for nv in n_vec0])  # vector between adjacent channels on one detector/chip
        for j in range(N_d):
            d = np.array([D0[j, :] + p_vecs[j, :] * delta_D * c for c in channels])
            #u = np.array([[np.cos(dir0[j] + c * theta), 0, np.sin(dir0[j] + c * theta)] for c in channels])
            Ds[j, :] = d
            #us[j, :] = u


        return Ds, pinhole

    def save_D_u(self, Cam_parameters, fn):
        np.savez(fn, Cam_parameters)

    def create_collimator_camera(self, parameters):
        '''
        Create camera from D and u vectors in dictionary
        :return:
        '''
        cam = tf.geom.CamLOS1D(dgeom=(parameters['D'], parameters['u']), config=config, Exp='ITER',
                               Diag='Bolometer', Etendues=parameters['Etendue'], Name=parameters['Name'])
        return cam

    def create_pinhole_camera(self, parameters):
        '''
        Create camera from D and u vectors in dictionary
        :return:
        '''
        '''
        {'D': array([[4. , 0. , 0. ],
        [4. , 0. , 0.1]]), 'pinhole': array([4.4, 0. , 0. ])}'''
        cameras=[]
        for sensor in parameters['D']:
            dgeom={'D': sensor, 'pinhole': parameters['pinhole']}
            cam = tf.geom.CamLOS1D(dgeom=dgeom, config=config, Exp='ITER',
                                   Diag='Bolometer', Etendues=parameters['E'], Name=parameters['Name'])
            cameras.append(cam)
        return cameras


    def create_cameras(self, dParameters, camera_type):
        '''
        Create cameras from D and u vectors in dictionary
        :return:
        '''
        cameras = {}
        if camera_type == 'collimator':
            create = self.create_collimator_camera
        if camera_type == 'pinhole':
            create = self.create_pinhole_camera

        for parameters in dParameters.values():
            try:
                cam = create(parameters)
                cameras[parameters['Name']] = cam
            except NotImplementedError:
                print('Camera {} not created due to ToFu bug'.format(parameters['Name']))
        return cameras

    def create_DC_cameras(self):
        '''
        Divertor collimator cameras
        :return:
        '''

        self.DC_cameras = self.create_cameras(self.DC_parameters, camera_type='collimator')

    def create_VV_cameras(self):
        '''
        Vacuum vessel vollimator cameras
        :return:
        '''
        self.VV_cameras = self.create_cameras(self.VV_parameters, camera_type='collimator')

    def create_PPC_cameras(self):
        '''
        Port plug (upper PP and Equatorial PP) collimator cameras
        :return:
        '''
        self.PPC_cameras = self.create_cameras(self.PPC_parameters, camera_type='collimator')

    def create_PPP_cameras(self):
        '''
        Port plug (upper PP and Equatorial PP) pinhole cameras
        Not currently working. There will be an easier way to create pinhole cameras in ToFu 1.4.1
        We will use that instead cos this is quite involved.
        :return:
        '''
        self.PPP_cameras = self.create_cameras(self.PPP_parameters, camera_type='pinhole')


def plot_save(cam, fn='out.png'):
    fig, axs = plt.subplots(1, 2)
    cam.plot([axs[0], axs[1]])
    fig.savefig(fn)


def plot_save_many(dCams, fn='out.png'):
    fig, axs = plt.subplots(1, 2)
    for cam in dCams.values():
        cam.plot([axs[0], axs[1]])
    fig.savefig(fn)

def plot_pinhole_camera(Cams):
    fig, ax= plt.subplots()
    for cam in Cams:
        cam.plot([ax], proj='Cross')
    ax.set_aspect('equal')