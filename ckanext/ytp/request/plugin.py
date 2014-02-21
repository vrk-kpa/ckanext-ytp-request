# -*- coding: utf-8 -*-

import logging

from ckan import plugins, model
from ckan.plugins import toolkit
from ckan.common import c, _

from ckanext.ytp.request import auth, logic
from ckan.lib import helpers
from sqlalchemy.sql.expression import or_

log = logging.getLogger(__name__)


class YtpRequestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)

    def _add_to_translation(self):
        """ Include dynamic values to translation search. Never called. """
        _("admin")
        _("member")
        _("editor")

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

    def _organization_role(self, organization_id):
        if not c.userobj:
            return None
        if c.userobj.sysadmin:
            return _("admin")

        query = model.Session.query(model.Member).filter(or_(model.Member.state == 'active', model.Member.state == 'pending')) \
            .filter(model.Member.table_name == 'user').filter(model.Member.group_id == organization_id).filter(model.Member.table_id == c.userobj.id)

        member = query.first()
        if not member:
            return None

        if member.state == 'pending':
            return _('Pending for approval')
        else:
            return _(member.capacity)

    def _apply_link(self, organization_name):
        return helpers.url_for('member_request_new', selected_organization=organization_name) if c.user else None

    def get_helpers(self):
        return {'list_organizations': self._list_organizations, 'organization_role': self._organization_role, 'apply_link': self._apply_link}
