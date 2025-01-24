from importlib import import_module
from .utils import iterfy
from copy import deepcopy


def _find_deferred_devices(config):
    """
    Find all deferred devices and their aliases in the config.

    Parameters
    ----------
    config : dict
        The configuration dictionary

    Returns
    -------
    set
        Set of device names that should be deferred
    dict
        Filtered config without deferred devices
    dict
        Config containing only deferred devices
    """
    deferred_devices = set()

    # First find explicitly deferred devices
    for key, device_config in config.items():
        if isinstance(device_config, dict) and device_config.get(
            "_defer_loading", False
        ):
            deferred_devices.add(key)

    # Then find aliases of deferred devices
    for key, device_config in config.items():
        if isinstance(device_config, dict) and "_alias" in device_config:
            # Parse the alias path (e.g., "enpossoft.harmonic")
            alias_parts = device_config["_alias"].split(".")
            base_device = alias_parts[0]
            if base_device in deferred_devices:
                deferred_devices.add(key)

    # Create filtered configs
    filtered_config = {k: v for k, v in config.items() if k not in deferred_devices}
    deferred_config = {k: v for k, v in config.items() if k in deferred_devices}

    return deferred_devices, filtered_config, deferred_config


def simpleResolver(fullclassname):
    """
    Resolve a full class name to a class object.

    Parameters
    ----------
    fullclassname : str
        The full class name to resolve.

    Returns
    -------
    type
        The class object resolved from the full class name.
    """
    class_name = fullclassname.split(".")[-1]
    module_name = ".".join(fullclassname.split(".")[:-1])
    module = import_module(module_name)
    cls = getattr(module, class_name)
    return cls


def getMaxLoadPass(config):
    max_load_order = 1
    for device_info in config.values():
        order = device_info.get("_load_order", 1)
        max_load_order = max(max_load_order, order)
    return max_load_order


def loadFromConfig(
    config,
    instantiateDevice,
    alias=False,
    namespace=None,
    load_pass="auto",
    filter_deferred=True,
    **kwargs,
):
    """
    Load devices from configuration, optionally handling multiple load passes automatically.

    Parameters
    ----------
    config : dict
        Configuration dictionary containing device information
    instantiateDevice : callable
        Function to instantiate each device
    alias : bool, optional
        Whether to create aliases for devices
    namespace : dict, optional
        Namespace to add devices to
    load_pass : str or int, optional
        If "auto", automatically handle multiple load passes. If int, load only that pass.
    filter_deferred : bool, optional
        Whether to filter out deferred devices and their aliases. Default is True.
    **kwargs : dict
        Additional keyword arguments passed to instantiateDevice

    Returns
    -------
    tuple
        (device_dict, group_dict, role_dict) containing all loaded devices and their groupings
    """
    device_dict = {}
    group_dict = {}
    role_dict = {}
    print("Loading devices from config dictionary")
    # Handle deferred devices if filtering is enabled
    if filter_deferred:
        _, config, _ = _find_deferred_devices(config)

    if load_pass == "auto":
        # Find the highest load order in the config
        max_load_order = getMaxLoadPass(config)
        print(f"Number of load passes: {max_load_order}")
        # Load each pass sequentially
        for current_pass in range(1, max_load_order + 1):
            _load_single_pass(
                current_pass,
                config,
                instantiateDevice,
                device_dict,
                group_dict,
                role_dict,
                namespace,
                **kwargs,
            )
            if alias:
                _handle_aliases(
                    current_pass, config, device_dict, group_dict, role_dict, namespace
                )
    else:
        # Load single pass
        _load_single_pass(
            load_pass,
            config,
            instantiateDevice,
            device_dict,
            group_dict,
            role_dict,
            namespace,
            **kwargs,
        )
        if alias:
            _handle_aliases(
                load_pass, config, device_dict, group_dict, role_dict, namespace
            )

    return device_dict, group_dict, role_dict


def _load_single_pass(
    load_pass,
    config,
    instantiateDevice,
    device_dict,
    group_dict,
    role_dict,
    namespace,
    **kwargs,
):
    """Helper function to load a single pass of devices"""
    print(f"Loading devices from config dictionary for pass {load_pass}")
    for device_key, device_info in config.items():
        if device_info.get("_load_order", 1) != load_pass:
            continue
        # Skip deferred devices
        if device_info.get("_defer_loading", False):
            continue
        if device_info.get("_target", "IGNORE") != "IGNORE":
            print(f"Loading device {device_key}")
            device_dict[device_key] = instantiateDevice(
                device_key, device_info, namespace=namespace, **kwargs
            )
            groups = iterfy(device_info.get("_group", ["misc"]))
            for g in groups:
                if g not in group_dict:
                    group_dict[g] = []
                group_dict[g].append(device_key)
            if "_role" in device_info:
                role_dict[device_info["_role"]] = device_key


def _handle_aliases(load_pass, config, device_dict, group_dict, role_dict, namespace):
    """Helper function to handle aliases for a single pass"""
    for alias_key, device_info in config.items():
        if device_info.get("_load_order", 1) != load_pass:
            continue
        if "_alias" in device_info:
            device_key = device_info["_alias"]
            print(f"Trying to alias {device_key} to {alias_key}")
            device_names = device_key.split(".")
            if device_names[0] in device_dict:
                device = device_dict[device_names[0]]
                if len(device_names) > 1:
                    for key in device_names[1:]:
                        device = getattr(device, key)
                device_dict[alias_key] = device
                if namespace is not None:
                    namespace[alias_key] = device
                groups = iterfy(device_info.get("_group", ["misc"]))
                for g in groups:
                    if g not in group_dict:
                        group_dict[g] = []
                    group_dict[g].append(alias_key)
                if "_role" in device_info:
                    role_dict[device_info["_role"]] = alias_key


def instantiateOphyd(device_key, info, cls=None, namespace=None, **kwargs):
    """
    Instantiate a device with given information.

    Parameters
    ----------
    device_key : str
        The key identifying the device.
    info : dict
        The information dictionary for the device.
    cls : type, optional
        The class to instantiate the device with. If not provided, it will be resolved from the info dictionary.
    namespace : dict, optional
        The namespace to add the instantiated device to.

    Returns
    -------
    object
        The instantiated device.
    """
    device_info = deepcopy(info)
    if cls is not None:
        device_info.pop("_target", None)
    elif device_info.get("_target", None) is not None:
        cls = simpleResolver(device_info.pop("_target"))
    else:
        raise KeyError("Could not find '_target' in {}".format(device_info))

    add_to_namespace = device_info.pop("_add_to_ns", True)

    popkeys = [key for key in device_info if key.startswith("_")]
    for key in popkeys:
        device_info.pop(key)

    name = device_info.pop("name", device_key)
    prefix = device_info.pop("prefix", "")
    device = cls(prefix, name=name, **device_info, **kwargs)

    if add_to_namespace and namespace is not None:
        namespace[device_key] = device
    return device
