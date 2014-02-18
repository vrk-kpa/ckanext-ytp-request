# -*- coding: utf-8 -*-

import logging

from ckan import plugins
from ckan.plugins import toolkit
from ckan.common import c

from ckanext.ytp.request import auth, logic

log = logging.getLogger(__name__)


class YtpRequestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)

    def before_map(self, m):
        """ CKAN autocomplete discards vocabulary_id from request. Create own api for this. """
        controller = 'ckanext.ytp.request.controller:YtpRequestController'
        m.connect("member_request_new", '/member-request/new', action='new', controller=controller)
        m.connect("member_request_list", '/member-request/list', action='list', controller=controller)
        m.connect("member_request_show", '/member-request/show/{member_id}', action='show', controller=controller)
        m.connect("member_request_reject", '/member-request/reject/{member_id}', action='reject', controller=controller)
        m.connect("member_request_approve", '/member-request/approve/{member_id}', action='approve', controller=controller)
        return m

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

    def _get_function_dictionary(self, module, prefix):
        return {name: getattr(module, name) for name in dir(module) if name.startswith(prefix)}

    def get_actions(self):
        return self._get_function_dictionary(logic, "member_request_")

    def get_auth_functions(self):
        return self._get_function_dictionary(auth, "member_request_")

    def _list_organizations(self):
        context = {'user': c.user}
        data_dict = {}
        data_dict['all_fields'] = True
        data_dict['groups'] = []
        data_dict['type'] = 'organization'
        return toolkit.get_action('organization_list')(context, data_dict)

    def get_helpers(self):
        return {'list_organizations': self._list_organizations}
