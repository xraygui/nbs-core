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
        self.groups = list(self.default_groups)
        self.roles = ["energy", "primary_manipulator", "default_shutter"]
        self.mode = None

        # Initialize empty dictionaries for each default group
        for group in self.default_groups:
            setattr(self, group, {})

        self.loadDevices(devices, groups, roles)

    def loadDevices(self, devices, groups, roles):
        """Load devices and handle mode configuration.

        Parameters
        ----------
        devices : dict
            Dictionary of device objects
        groups : dict
            Dictionary mapping group names to lists of device keys
        roles : dict
            Dictionary mapping role names to device keys
        """
        # First load the mode controller if it exists
        if "mode" in roles:
            self.mode = devices[roles["mode"]]
            print(f"Loaded mode controller: {self.mode.name}")

        # Then load all other devices
        self.devices.update(devices)
        for groupname, devicelist in groups.items():
            if groupname not in self.groups:
                self.groups.append(groupname)
                setattr(self, groupname, {})
            gdict = getattr(self, groupname)
            for key in devicelist:
                print(f"Setting {groupname}[{key}]")
                device = devices[key]
                # Store mode info on device if specified
                gdict[key] = device

        print(roles)
        for role, key in roles.items():
            if role != "":
                self.roles.append(role)
                print(f"Setting {role} to {key}")
                setattr(self, role, devices[key])

    def get_available_devices(self, mode=None):
        """Get devices available in the specified mode.

        Parameters
        ----------
        mode : str, optional
            Mode to check. If None, uses current mode

        Returns
        -------
        dict
            Dictionary of available devices by group
        """
        if mode is None and self.mode:
            mode = self.mode.get()

        available = {}
        for group in self.groups:
            available[group] = {}
            group_dict = getattr(self, group)
            for key, device in group_dict.items():
                if self._is_device_available(device, mode):
                    available[group][key] = device
        return available

    def _is_device_available(self, device, mode):
        """Check if device is available in specified mode.

        Parameters
        ----------
        device : object
            Device to check
        mode : str
            Mode to check

        Returns
        -------
        bool
            Whether device is available
        """
        if not hasattr(device, "_mode_info"):
            # No mode restrictions
            return True

        modes = device._mode_info.get("modes", [])
        if not modes:
            # No modes specified, always available
            return True
        elif mode in modes:
            # Mode explicitly allowed
            return True
        else:
            # Mode not allowed
            return False
