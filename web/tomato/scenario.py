# by Chang Rui

from django.http import HttpResponse
from django.shortcuts import render

from lib import wrap_rpc

@wrap_rpc
def test(api, request):
    return HttpResponse("<h1>Test..........</h1>")

@wrap_rpc
def scenario_list(api, request):
    sc_list = api.scenario_list()
    return render(request, "scenario/list.html",
                  {
                      'scenario_list' : sc_list,
                  })

