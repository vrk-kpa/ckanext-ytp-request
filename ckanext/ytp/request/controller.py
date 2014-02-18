from ckan.lib import base
from ckan import model
from ckan.logic import NotFound, NotAuthorized, check_access, tuplize_dict, clean_dict, parse_params, ValidationError
from ckan.lib import helpers
from ckan.plugins import toolkit
from ckan.lib.base import c, request, render, abort
from ckan.common import _
import ckan.lib.navl.dictization_functions as dict_fns


class YtpRequestController(base.BaseController):
    def new(self, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'save': 'save' in request.params,
                   'parent': request.params.get('parent', None)}
        try:
            check_access('member_request_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a member request'))

        if context['save'] and not data:
            return self._save_new(context)

        data = data or {}
        extra_vars = {'data': data, 'errors': errors or {}, 'error_summary': error_summary or {}, 'action': 'new'}

        c.roles = toolkit.get_action('member_roles_list')(context, {})
        c.user_role = 'member'

        c.form = render("request/new_request_form.html", extra_vars=extra_vars)
        return render("request/new.html")

    def _save_new(self, context):
        try:
            data_dict = clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(request.params))))
            data_dict['group'] = data_dict['organization']
            member = toolkit.get_action('member_request_create')(context, data_dict)
            helpers.redirect_to('member_request_show', member_id=member['id'])
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % '')
        except NotFound:
            abort(404, _('Group not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)

    def list(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
        try:
            member_requests = toolkit.get_action('member_request_list')(context, {})
            extra_vars = {'member_requests': member_requests}
            return render('request/list.html', extra_vars=extra_vars)
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message)

    def show(self, member_id):
        try:
            member = model.Session.query(model.Member).get(member_id)
            if member.state != 'pending':
                abort(404, _('Request not found'))

            member_user = model.Session.query(model.User).get(member.table_id)
            extra_vars = {"member": member, "member_user": member_user}
            return render('request/show.html', extra_vars=extra_vars)
        except toolkit.ObjectNotFound:
            abort(404, _('Request not found'))
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message)

    def _process(self, member_id, approve):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
        data_dict = {"member": member_id, "approve": approve}
        try:
            toolkit.get_action('member_request_process')(context, data_dict)
            helpers.redirect_to('member_request_list')
        except NotAuthorized:
            abort(401, _('Unauthorized to process group %s') % '')
        except NotFound:
            abort(404, _('Request not found'))

    def reject(self, member_id):
        return self._process(member_id, False)

    def approve(self, member_id):
        return self._process(member_id, True)
