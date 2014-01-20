# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2012 Integrated Communication Systems Lab, University of Kaiserslautern
#
# This file is part of the ToMaTo project
#
# ToMaTo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms
from django.core.urlresolvers import reverse
from admin_common import organization_name_list
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from admin_common import BootstrapForm, RemoveConfirmForm

from lib import wrap_rpc, getapi, AuthError

class FixedText(forms.HiddenInput):
	is_hidden = False
	def render(self, name, value, attrs=None):
		return forms.HiddenInput.render(self, name, value) + value

class FixedList(forms.MultipleHiddenInput):
	is_hidden = False
	def render(self, name, value, attrs=None):
		return forms.MultipleHiddenInput.render(self, name, value) + ", ".join(value)
	def value_from_datadict(self, data, files, name):
		value = forms.MultipleHiddenInput.value_from_datadict(self, data, files, name)
		# fix django bug
		if isinstance(value, list):
			return value
		else:
			return [value]

CategoryTranslationDict = {
		   'manager_user_global':'Global User Management',
		   'manager_user_orga':'Organization-Internal User Management',
		   'manager_host_global':'Global Host Management',
		   'manager_host_orga':'Organization-Internal Host Management',
		   'user':'User',
		   'other':'Other'
		}

category_order = [
		'manager_user_global',
		'manager_user_orga',
		'manager_host_global',
		'manager_host_orga',
		'user'
	]
			
class AccountFlagFixedList(FixedList):
	api = None
	def render(self, name, value, attrs=None):
		
		print value
		
		FlagTranslationDict = self.api.account_flags()
		categories = self.api.account_flag_categories()
		catlist = category_order
		
		output = []
		isFirst = True
		for cat in categories.keys():
			if not cat in catlist:
				catlist.append(cat)
		
		for cat in catlist:
			foundOne = False
			for v in categories[cat]:
				if v in value:
					if not foundOne:
						if not isFirst:
							output.append('</ul>')
						else:
							isFirst = False
						output.append('<ul>')
						output.append('<b>' + CategoryTranslationDict.get(cat,cat) + '</b>')
						foundOne = True
					output.append('<li style="margin-left:20px;">' + FlagTranslationDict.get(v,v) + '</li>')
		if output == []:
			output = ['None']
			
			
		return forms.MultipleHiddenInput.render(self, name, value) + mark_safe(u'\n'.join(output))
	
	def __init__(self, api, *args, **kwargs):
		super(AccountFlagFixedList, self).__init__(*args, **kwargs)
		self.api = api
		

class AccountFlagCheckboxList(forms.widgets.CheckboxSelectMultiple):
	api = None
	def render(self, name, value, attrs=None):
		if value is None: value = []
		has_id = attrs and 'id' in attrs
		final_attrs = self.build_attrs(attrs, name=name)
		str_values = set([force_unicode(v) for v in value])
	
		FlagTranslationDict = self.api.account_flags()
		categories = self.api.account_flag_categories()
		catlist = category_order
		
		output = ['<ul>']
		isFirst = True
		for cat in categories.keys():
			if not cat in catlist:
				catlist.append(cat)
		
		for cat in catlist:
			foundOne = False
			for v in categories[cat]:
				if not foundOne:
					if not isFirst:
						output.append('<br />')
					else:
						isFirst = False
					output.append('<b>' + CategoryTranslationDict.get(cat,cat) + '</b>')
					foundOne = True
					
				if has_id:
					final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], self.choices.index((v,FlagTranslationDict.get(v,v)))))
					label_for = u' for="%s"' % final_attrs['id']
				else:
					label_for = ''
					
				cb = forms.widgets.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
				option_value = force_unicode(v)
				rendered_cb = cb.render(name, option_value)
				option_label = conditional_escape(force_unicode(FlagTranslationDict.get(v,v)))
				output.append(u'<li><label%s>%s %s</label></li>' % (label_for, rendered_cb, option_label))
		output.append('</ul>')
		return mark_safe(u'\n'.join(output))
	
	def __init__(self, api, *args, **kwargs):
		super(AccountFlagCheckboxList, self).__init__(*args, **kwargs)
		self.api = api
		self.choices = api.account_flags().items()
	
class AccountForm(forms.Form):
	name = forms.CharField(label="Account name", max_length=50)
	password = forms.CharField(label="Password", widget=forms.PasswordInput, required=False)
	password2 = forms.CharField(label="Password (repeated)", widget=forms.PasswordInput, required=False)
	organization = forms.CharField(max_length=50)
	origin = forms.CharField(label="Origin", widget=forms.HiddenInput, required=False)
	realname = forms.CharField(label="Full name")
	email = forms.EmailField()
	flags = forms.MultipleChoiceField(required=False)
	_reason = forms.CharField(widget = forms.Textarea, required=False, label="Reason for Registering")
	def __init__(self, api, *args, **kwargs):
		super(AccountForm, self).__init__(*args, **kwargs)
		self.fields["organization"].widget = forms.widgets.Select(choices=organization_name_list(api))
		
	def clean_password(self):
		if self.data.get('password') != self.data.get('password2'):
			raise forms.ValidationError('Passwords are not the same')
		return self.data.get('password')
	
	def clean(self, *args, **kwargs):
		self.clean_password()
		return forms.Form.clean(self, *args, **kwargs)

class AccountChangeForm(AccountForm):
	def __init__(self, api, data=None):
		AccountForm.__init__(self, api, data)
		flags = api.account_flags().items()
		self.fields["name"].widget = FixedText()
		del self.fields["origin"]
		del self.fields["_reason"]
		self.fields["flags"].choices = flags
		if api.user.isAdmin(data["organization"]):
			self.fields["flags"].widget = AccountFlagCheckboxList(api)
		else:
			self.fields["flags"].widget = AccountFlagFixedList(api)
			

class AccountRegisterForm(AccountForm):
	aup = forms.BooleanField(label="", required=True)
	
	def __init__(self, api, data=None):
		AccountForm.__init__(self, api, data)
		self.fields["password"].required = True
		del self.fields["flags"]
		del self.fields["origin"]
		self.fields['aup'].help_text = 'I accept the <a href="'+ api.server_info()['external_urls']['aup'] +'" target="_blank">terms and conditions</a>'
		

class AccountRemoveForm(forms.Form):
	username = forms.CharField(max_length=250, widget=forms.HiddenInput)
	
@wrap_rpc
def list(api, request, with_flag=None, organization=True):
	if not api.user:
		raise AuthError()
	if organization is True:
		organization = api.user.organization
	accs = api.account_list(organization=organization)
	account_flags = api.account_flags()
	orgas = api.organization_list()
	if with_flag:
		acclist_new = []
		for acc in accs:
			if with_flag in acc['flags']:
				acclist_new.append(acc)
		accs = acclist_new
	for acc in accs:
		acc['flags_name'] = []
		for flag in acc['flags']:
			if flag in account_flags:
				acc['flags_name'].append(account_flags[flag])
			else:
				acc['flags_name'].append(flag+" (unknown flag)")
	return render(request, "account/list.html", {'accounts': accs, 'orgas': orgas, 'with_flag': with_flag, 'organization':organization})

@wrap_rpc
def info(api, request, id=None):
	if not api.user:
		raise AuthError()
	user = api.account_info(id) if id else api.user.data
	account_flags = api.account_flags()
	organization = api.organization_info(user["organization"])
	user["reason"] = user.get("_reason")
	flags = []
	for flag in user["flags"]:
		if flag in account_flags:
			flags.append(account_flags[flag])
		else:
			flags.append(flag+" (unknown flag)")
	return render(request, "account/info.html", {"account": user, "organization": organization, "flags": flags})

@wrap_rpc
def accept(api, request, id):
	if not api.user:
		raise AuthError()
	user = api.account_info(id)
	flags = user["flags"]
	flags.remove("new_account")
	flags.remove("over_quota")
	api.account_modify(id, attrs={"flags": flags})
	return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": id}))

@wrap_rpc
def edit(api, request, id):
	if not api.user:
		raise AuthError()
	user = api.account_info(id)
	if request.method=='POST':
		form = AccountChangeForm(api, request.REQUEST)
		if form.is_valid():
			data = form.cleaned_data
			if not api.user.isAdmin(data["organization"]):
				del data["flags"]
			del data["name"]
			del data["password2"]
			if not data["password"]:
				del data["password"]
			api.account_modify(id, attrs=data)
			return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": id}))
	else:
		form = AccountChangeForm(api, user)
	return render(request, "account/edit.html", {"account": user, "form": form})
	
@wrap_rpc
def register(api, request):
	if request.method=='POST':
		form = AccountRegisterForm(api, request.REQUEST)
		if form.is_valid():
			data = form.cleaned_data
			username = data["name"]
			password = data["password"]
			organization=data["organization"]
			del data["password"]
			del data["password2"]
			del data["name"]
			del data["aup"]
			del data["organization"]
			try:
				account = api.account_create(username, password=password, organization=organization, attrs=data)
				if not api.user:
					request.session["auth"] = "%s:%s" % (username, password)
					api = getapi(request)
					request.session["user"] = api.user  
				return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": account["name"]}))
			except:
				import traceback
				print traceback.print_exc()
				form._errors["name"] = form.error_class(["This name is already taken"])
	else:
		form = AccountRegisterForm(api) 
	return render(request, "account/register.html", {"form": form})

@wrap_rpc
def remove(api, request, id=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.account_remove(id)
			return HttpResponseRedirect(reverse("account_list"))
	form = RemoveConfirmForm.build(reverse("tomato.account.remove", kwargs={"id": id}))
	return render(request, "form.html", {"heading": "Remove Account", "message_before": "Are you sure you want to remove the account '"+id+"'?", 'form': form})