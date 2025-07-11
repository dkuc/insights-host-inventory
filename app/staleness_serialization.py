from datetime import datetime

from app.common import inventory_config
from app.culling import Timestamps
from lib.feature_flags import FLAG_INVENTORY_CREATE_LAST_CHECK_IN_UPDATE_PER_REPORTER_STALENESS
from lib.feature_flags import get_flag_value

__all__ = ("get_staleness_timestamps",)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def _find_host_type(host) -> str:
    return (
        "immutable"
        if host.host_type == "edge"
        or (
            hasattr(host, "system_profile_facts")
            and host.system_profile_facts
            and host.system_profile_facts.get("host_type") == "edge"
        )
        else "conventional"
    )


# Determine staleness timestamps
def get_staleness_timestamps(host, staleness_timestamps: Timestamps, staleness: AttrDict) -> dict:
    """
    Calculates staleness timestamps for a host based on its type and configuration.
    Returns a dictionary containing the stale, stale warning, and culled timestamps for the host.

    Args:
        host: The host object for which to calculate staleness timestamps.
        staleness_timestamps: An object providing methods to compute timestamps.
        staleness: A dictionary containing staleness configuration values.

    Returns:
        dict: A dictionary with keys 'stale_timestamp', 'stale_warning_timestamp', and 'culled_timestamp'.
    """

    staleness_type = _find_host_type(host)

    date_to_use = (
        host.last_check_in
        if get_flag_value(FLAG_INVENTORY_CREATE_LAST_CHECK_IN_UPDATE_PER_REPORTER_STALENESS)
        else host.modified_on
    )
    return {
        "stale_timestamp": staleness_timestamps.stale_timestamp(
            date_to_use, staleness[f"{staleness_type}_time_to_stale"]
        ),
        "stale_warning_timestamp": staleness_timestamps.stale_warning_timestamp(
            date_to_use, staleness[f"{staleness_type}_time_to_stale_warning"]
        ),
        "culled_timestamp": staleness_timestamps.culled_timestamp(
            date_to_use, staleness[f"{staleness_type}_time_to_delete"]
        ),
    }


def get_reporter_staleness_timestamps(
    host, staleness_timestamps: Timestamps, staleness: AttrDict, reporter: str
) -> dict:
    """
    Calculates staleness timestamps for a specific reporter of a host.
    Returns a dictionary containing the stale, stale warning, and culled timestamps for the reporter.

    Args:
        host: The host object for which to calculate staleness timestamps.
        staleness_timestamps: An object providing methods to compute timestamps.
        staleness: A dictionary containing staleness configuration values.
        reporter: The reporter identifier for which to calculate timestamps.

    Returns:
        dict: A dictionary with keys 'stale_timestamp', 'stale_warning_timestamp', and 'culled_timestamp'.
    """

    staleness_type = _find_host_type(host)

    date_to_use = (
        datetime.fromisoformat(host.per_reporter_staleness[reporter]["last_check_in"])
        if get_flag_value(FLAG_INVENTORY_CREATE_LAST_CHECK_IN_UPDATE_PER_REPORTER_STALENESS)
        else host.modified_on
    )
    return {
        "stale_timestamp": staleness_timestamps.stale_timestamp(
            date_to_use, staleness[f"{staleness_type}_time_to_stale"]
        ),
        "stale_warning_timestamp": staleness_timestamps.stale_warning_timestamp(
            date_to_use, staleness[f"{staleness_type}_time_to_stale_warning"]
        ),
        "culled_timestamp": staleness_timestamps.culled_timestamp(
            date_to_use, staleness[f"{staleness_type}_time_to_delete"]
        ),
    }


def get_sys_default_staleness(config=None):
    return build_staleness_sys_default("000000", config)


def get_sys_default_staleness_api(identity, config=None):
    org_id = identity.org_id or "00000"
    return build_staleness_sys_default(org_id, config)


def build_staleness_sys_default(org_id, config=None):
    if not config:
        config = inventory_config()

    return AttrDict(
        {
            "id": "system_default",
            "org_id": org_id,
            "conventional_time_to_stale": config.conventional_time_to_stale_seconds,
            "conventional_time_to_stale_warning": config.conventional_time_to_stale_warning_seconds,
            "conventional_time_to_delete": config.conventional_time_to_delete_seconds,
            "immutable_time_to_stale": config.immutable_time_to_stale_seconds,
            "immutable_time_to_stale_warning": config.immutable_time_to_stale_warning_seconds,
            "immutable_time_to_delete": config.immutable_time_to_delete_seconds,
            "created_on": None,
            "modified_on": None,
        }
    )


# This is required because we do not keep a ORM object that is attached to a session
# leaving in the global scope. Before this serialization,
# it was causing sqlalchemy.orm.exc.DetachedInstanceError
def build_serialized_acc_staleness_obj(staleness):
    return AttrDict(
        {
            "id": str(staleness.id),
            "org_id": staleness.org_id,
            "conventional_time_to_stale": staleness.conventional_time_to_stale,
            "conventional_time_to_stale_warning": staleness.conventional_time_to_stale_warning,
            "conventional_time_to_delete": staleness.conventional_time_to_delete,
            "immutable_time_to_stale": staleness.immutable_time_to_stale,
            "immutable_time_to_stale_warning": staleness.immutable_time_to_stale_warning,
            "immutable_time_to_delete": staleness.immutable_time_to_delete,
            "created_on": staleness.created_on,
            "modified_on": staleness.modified_on,
        }
    )
