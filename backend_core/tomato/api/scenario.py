# by Chang Rui

from ..scenario import Scenario

def scenario_save(id_, data=None):
    """Save the topology specified by topology id"""
    # return "Success from backend_core. id=%s, data=%s" % (_id, data
    # return "Now there are %s scenarios in DB." % Scenario.get_count()
    scenario_info = Scenario.create(**data)
    return scenario_info


# def scenario_deploy(id_):
#     """Get the scenario specified by scenario id, and import it"""
#     pass


def scenario_topology_info_json(id_):
    return Scenario.get_topology_info_json(id_)


def scenario_list():
    """Return the list of all scenarios"""
    # need serializable, use Scenario.info()
    # return Scenario.get_all()
    return [scenario.info() for scenario in Scenario.get_all()]


def scenario_modify(id_, data=None):
    """Edit the scenario, return scenario info"""
    response = Scenario.modify_by_id(id_, **data)
    return response


def scenario_remove(id_):
    """Remove the scenario specified by scenario id"""
    try:
        Scenario.remove_by_id(id_)
    except Scenario.DoesNotExist, Scenario.MultipleObjectsReturned:
        return False
    return True


def scenario_count():
    """Return the number of scenarios, debug usage"""
    return Scenario.get_count()


def scenario_info(id_):
    return Scenario.info_by_id(id_)
