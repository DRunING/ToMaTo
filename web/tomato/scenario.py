# by Chang Rui

from django.http import HttpResponse
from django.shortcuts import render

from lib import wrap_rpc


@wrap_rpc
def list(api, request):
    scenario_list = api.scenario_list()
    show = 'all'    # TODO: all, my, public
    return render(request, "scenario/list.html",
                  {
                      'scenario_list' : scenario_list,
                      'show' : show,
                  })


@wrap_rpc
def info(api, request, id_):
    # template = api.template_info(res_id)
    # return render(request, "templates/info.html", {"template": template, "techs_dict": techs_dict})
    scenario = api.scenario_info(id_)
    return render(request, "scenario/info.html", {"scenario": scenario})


@wrap_rpc
def edit(api, request, id_):
    return HttpResponse("Edit: %s" % id_)


@wrap_rpc
def remove(api, request, id_):
    return HttpResponse("Remove: %s" % id_)

