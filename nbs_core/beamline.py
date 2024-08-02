from .autoload import loadFromConfig


class BeamlineModel:
    def __init__(self, devices, groups, roles,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.devices = devices
        self.shutters = {}
        self.gatevalves = {}
        self.apertures = {}
        self.pinholes = {}
        self.gauges = {}
        self.motors = {}
        self.detectors = {}
        self.manipulators = {}
        self.mirrors = {}
        self.controllers = {}
        self.vacuum = {}
        self.energy = None
        self.primary_manipulator = None
        self.default_shutter = None
        self.groups = ["shutters", "gatevalves", "apertures", "pinholes", "gauges", "motors", "detectors", "manipulators", "mirrors", "controllers", "vacuum", "misc"]
        self.roles = ["energy", "primary_manipulator", "default_shutter"]
        self.loadDevices(devices, groups, roles)

    def loadDevices(self, devices, groups, roles):
        self.devices.update(devices)
        for groupname, devicelist in groups.items():
            self.groups.append(groupname)
            setattr(self, groupname, {})
            gdict = getattr(self, groupname)
            for key in devicelist:
                print(f"Setting {groupname}[{key}]")
                gdict[key] = devices[key]
        print(roles)
        for role, key in roles.items():
            if role != "":
                self.roles.append(role)
                print(f"Setting {role} to {key}")
                setattr(self, role, devices[key])
