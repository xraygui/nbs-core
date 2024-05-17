from copy import deepcopy
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def replace_target_values(data, translation_dict, default_target=None):
    """
    Recursively replaces target values in a nested dictionary based on a translation dictionary.

    Parameters:
    data (dict): The nested dictionary whose values are to be replaced.
    translation_dict (dict): A dictionary mapping class names to their new values. Used to replace "_target_" values in the data.
    default_target (str, optional): A default translation for class names that are not provided in translation_dict. If None, classes not found in the translation_dict will raise a KeyError.

    Returns:
    dict: The modified dictionary with replaced values.
    """
    new_data = {}
    for device_key, device_info in data.items():
        new_data[device_key] = deepcopy(device_info)
        for key, value in device_info.items():
            if key == "_target":
                class_name = value.split(".")[-1]
                if value in translation_dict:
                    new_data[device_key]["_target"] = translation_dict[value]
                elif class_name in translation_dict:
                    new_data[device_key]["_target"] = translation_dict[class_name]
                elif default_target is not None:
                    new_data[device_key]["_target"] = default_target
                else:
                    print(
                        f"{class_name} not found in translation_dict and no default target was provided, _target set to IGNORE"
                    )
                    new_data[device_key]["_target"] = "IGNORE"
    return new_data


def generate_device_config(
    device_file, update_file=None, translation_dict=None, default_target=None
):
    with open(device_file, "rb") as f:
        device_config = tomllib.load(f)
    if update_file is not None:
        with open(update_file, "rb") as f:
            update_config = tomllib.load(f)
    else:
        update_config = {}
    translation_updates = {}
    translation_updates.update(update_config.get("loaders", {}))
    if translation_dict is not None:
        translation_updates.update(translation_dict)
    new_dev_config = replace_target_values(device_config, translation_updates, default_target)
    update_devices = update_config.get("devices", {})
    for key in list(new_dev_config.keys()):
        update = update_devices.get(key, {})
        new_dev_config[key].update(update)

    return new_dev_config
