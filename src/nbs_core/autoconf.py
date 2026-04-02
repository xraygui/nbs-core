from copy import deepcopy
from os.path import join, dirname, basename, exists
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
    device_file, update_file=None, translation_dict=None, default_target=None, sim_mode=False
):
    device_config = load_settings(device_file, sim_mode=sim_mode)
    if update_file is not None:
        update_config = load_settings(update_file, sim_mode=sim_mode)
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


_MERGE_MODE_KEY = "__merge__"
_MERGE_MODE_REPLACE = "replace"
_OVERLAY_REMOVE_KEY = "_remove"


def _deep_merge_dict(base, overlay):
    """
    Merge ``overlay`` into ``base`` in place.

    Mapping values are merged recursively unless the overlay value is a dict
    with ``__merge__ = "replace"``, in which case the existing subtree is
    replaced by the rest of that dict (directive keys are not kept).

    Any non-dict overlay value replaces the corresponding key in ``base``.
    If types disagree (e.g. mapping in base, scalar in overlay), the overlay
    wins.

    Overlay directives (only ``_remove`` is recognized at the current level):

    * ``_remove``: after other keys are applied, each name in this list is
      popped from ``base`` at this level. Must be a list.

    Parameters
    ----------
    base : dict
        Dictionary to update.
    overlay : dict
        Keys and values applied on top of ``base``.

    Returns
    -------
    dict
        ``base`` (same object), updated.
    """
    deferred_remove = None
    for key, value in overlay.items():
        if key == _OVERLAY_REMOVE_KEY:
            deferred_remove = value
            continue
        if (
            isinstance(value, dict)
            and value.get(_MERGE_MODE_KEY) == _MERGE_MODE_REPLACE
        ):
            branch = deepcopy(value)
            branch.pop(_MERGE_MODE_KEY, None)
            branch.pop(_OVERLAY_REMOVE_KEY, None)
            base[key] = branch
            continue
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge_dict(base[key], value)
        else:
            base[key] = deepcopy(value)

    if isinstance(deferred_remove, list):
        for k in deferred_remove:
            base.pop(k, None)

    return base


def load_settings(settings_file, sim_mode=False):
    with open(settings_file, "rb") as f:
        settings_config = tomllib.load(f)

    if sim_mode:
        sim_file = join(dirname(settings_file), basename(settings_file).replace(".toml", "_sim.toml"))
        if exists(sim_file):
            with open(sim_file, "rb") as f:
                sim_config = tomllib.load(f)
            _deep_merge_dict(settings_config, sim_config)
    return settings_config
