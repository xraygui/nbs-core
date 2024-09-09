class BeamlineModel:
    default_groups = [
        "shutters",
        "gatevalves",
        "apertures",
        "pinholes",
        "gauges",
        "motors",
        "detectors",
        "manipulators",
        "mirrors",
        "controllers",
        "vacuum",
        "misc",
    ]

    def __init__(self, devices, groups, roles, *args, **kwargs):
        super().__init__(
            *args, **kwargs
        )  # Needed for multiple inheritance! Do not remove!
        self.devices = devices
        self.energy = None
        self.primary_manipulator = None
        self.default_shutter = None
        self.groups = list(self.default_groups)  # Create a copy of the default groups
        self.roles = ["energy", "primary_manipulator", "default_shutter"]

        # Initialize empty dictionaries for each default group
        for group in self.default_groups:
            setattr(self, group, {})

        self.loadDevices(devices, groups, roles)

    def loadDevices(self, devices, groups, roles):
        self.devices.update(devices)
        for groupname, devicelist in groups.items():
            if groupname not in self.groups:
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
