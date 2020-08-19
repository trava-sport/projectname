# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for Odoo
#   Copyright (C) 2015-TODAY Akretion (http://www.akretion.com).
#   @author Sylvain Calador <sylvain.calador@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import logging
import base64
import operator
import itertools
import traceback

from httplib2 import ServerNotFoundError
import gspread
from gspread.exceptions import NoValidUrlKeyFound, SpreadsheetNotFound
from oauth2client.client import SignedJwtAssertionCredentials
from datetime import datetime

from odoo import registry, models, fields, api, _
from odoo.exceptions import Warning
from odoo.addons.connector.session import ConnectorSession
from odoo.addons.connector.queue.job import job, related_action
from odoo.addons.connector.exception import FailedJobError
from odoo.tools import config

SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://docs.google.com/feeds']

FIELDS_RECURSION_LIMIT = 2
SHEET_APP = ("Google Spreadsheet Import Issue\n"
             "--------------------------------------------------")
INITIAL_IMPORT_DOMAIN = [('auto', '=', True), ('submission_date', '=', False)]


_logger = logging.getLogger(__name__)


def open_document(backend, document_url):
    # Auhentification
    private_key = base64.b64decode(backend.p12_key)
    credentials = SignedJwtAssertionCredentials(
        backend.email, private_key, SCOPE)
    try:
        gc = gspread.authorize(credentials)
    except ServerNotFoundError:
        if config.get('debug_mode'): raise
        raise Warning(SHEET_APP, _("Check your internet connection.\n"
                                   "Impossible to establish a connection "
                                   "with Google Services"))
    try:
        document = gc.open_by_url(document_url)
    except NoValidUrlKeyFound:
        if config.get('debug_mode'): raise
        raise Warning(SHEET_APP, _('Google Drive: No valid key found in URL'))
    except SpreadsheetNotFound:
        if config.get('debug_mode'): raise
        raise Warning(SHEET_APP,
                      _("Spreadsheet Not Found"
                        "\n\nResolution\n----------------\n"
                        "Check URL file & sharing options with it "
                        "with this google user:\n\n%s" % backend.email))
    except Exception as e:
        if config.get('debug_mode'): raise
        raise Warning(SHEET_APP,
                      _("Google Drive: %s" % e.message))
    return document


class GoogleSpreadsheetDocument(models.Model):
    _name = 'google.spreadsheet.document'
    _description = 'Google Spreadsheet Document'
    _order = 'sequence ASC'

    auto = fields.Boolean(
        help="If checked, tasks are run at startup "
             "(until all those tasks are launched)")
    name = fields.Char('Name', required=True)
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        help="ERP Model")
    document_url = fields.Char(
        'URL',
        required=True,
        help="URL of the spreadsheet")
    document_sheet = fields.Char(
        'Sheet Name',
        required=True,
        help="Document tab name")
    submission_date = fields.Datetime('Submission date')
    header_row = fields.Integer(
        'Header',
        default=1,
        help="Columns name position")
    data_row_start = fields.Integer(
        string='First Row',
        default=2,
        help="First row of data")
    data_row_end = fields.Integer(
        string='Last Row',
        default=0,
        help="Last row of data: 0 means last row")
    chunk_size = fields.Integer('Chunk size', default=100)
    active = fields.Boolean(default=True)
    sequence = fields.Integer()
    backend_id = fields.Many2one(
        'google.spreadsheet.backend',
        string='Google Spreadsheet Backend'
    )

    def toggle_chunk_size(self):
        for record in self:
            if record.chunk_size != 1:
                chunk_size = 1
            else:
                chunk_size = 100
            record.write({'chunk_size': chunk_size})

    @api.model
    def startup_import(self, *args, **kwargs):
        tasks = self.search(INITIAL_IMPORT_DOMAIN, order='sequence')
        if tasks:
            # run only one task at a once because execution time
            # is unpredictable: it depends of Google
            tasks[0].run()
        else:
            # when all tasks have been run, the cron can be inactivated
            cron = self.env.ref(
                'connector_google_spreadsheet.ir_cron_spreadsheet_import')
            session = ConnectorSession(
                self.env.cr,
                self.env.uid,
                self.env.context,
            )
            description = "Inactive spreadsheet startup cron"
            # a cron can't change its state itself
            # define a job to unactive the cron
            set_cron_inactive.delay(session, self._name,
                                    {'cron_id': cron.id}, priority=1,
                                    description=description)
            return True

    def _prepare_import_args(
            self, fields, row_start, row_end, col_start, col_end, error_col):
        return {
            'document_url': self.document_url,
            'document_sheet': self.document_sheet,
            'fields': fields,
            'chunk_row_start': row_start,
            'chunk_row_end': row_end,
            'sheet_col_start': col_start,
            'sheet_col_end': col_end,
            'error_col': error_col,
            'erp_model': self.model_id.model,
            'backend_id': self.backend_id.id,
        }

    def run(self):
        session = ConnectorSession(
            self.env.cr,
            self.env.uid,
            self.env.context,
        )
        task_result = ''
        count_created_job = 0
        backend = self.backend_id
        document = open_document(backend, self.document_url)
        sheet = document.worksheet(self.document_sheet)

        header_row = max(self.header_row, 1)
        data_row_start = max(self.data_row_start, 2)
        data_row_end = max(self.data_row_end, 0)
        if header_row >= data_row_start:
            message = _('The header row must precede data! '
                        'Check the row parameters')
            raise Warning(SHEET_APP, message)
        if data_row_end and data_row_end < data_row_start:
            message = _('The data row start must precede data row end! '
                        'Check the row parameters')
            raise Warning(SHEET_APP, message)

        first_row = [c or '' for c in sheet.row_values(header_row)]
        if not first_row:
            raise Warning(SHEET_APP, _('Header cells seems empty!'))
        if first_row[0].lower() in ('error', 'errors'):
            col_start = 2
            import_fields = first_row[1:]
            error_col = 1
        else:
            col_start = 1
            import_fields = first_row
            error_col = None

        # first column data cells
        first_column_data_cells = sheet.col_values(col_start)[header_row:]
        if not first_column_data_cells:
            message = _('Nothing to import,'
                        'the first column of data seams empty!')
            raise Warning(SHEET_APP, message)

        col_end = len(first_row)

        eof = header_row + len(first_column_data_cells)

        if data_row_end > 0:
            eof = min(data_row_end, eof)

        # chunks logic

        row_start = header_row + 1
        row_end = row_start
        cells = first_column_data_cells

        # calculate "real" end of "file" (eof)
        # (if the user has not specified the data row end)
        if not data_row_end and sheet.row_count > eof:
            start = sheet.get_addr_int(eof+1, col_start)
            stop = sheet.get_addr_int(sheet.row_count, col_end)
            eof_chunk = sheet.range(start + ':' + stop)
            for cell in eof_chunk:
                if cell.value and cell.row > eof:
                    eof = cell.row
                    # append missing cells (empty)
                    cells.append(cell.value)

        indexes = [
            i-1 for i, cell in enumerate(cells) if cell and i
        ]

        def cut_allowed(index, indexes):
            return index in indexes or index >= max(indexes or [0])

        # Iterate on first data column
        for i, cell in enumerate(cells):

            if row_start < data_row_start:
                row_start += 1
                row_end = row_start
                continue

            # If the row start and row end is the same then we import one line
            # So the minimal size is 1
            size = row_end - row_start + 1
            if cut_allowed(i, indexes) \
                    and size >= self.chunk_size or row_end == eof:

                import_args = self._prepare_import_args(
                    import_fields,
                    row_start,
                    row_end,
                    col_start,
                    col_end,
                    error_col
                )
                description = "Spreadsheet import: %s" % self.name
                import_document.delay(session, self._name,
                                      import_args, priority=self.sequence,
                                      description=description)
                count_created_job += 1

                if row_end == eof:
                    break

                row_end += 1
                row_start = row_end
            else:
                row_end += 1

        # log result (job creation)
        self.submission_date = fields.Datetime.now()
        if count_created_job:
            task_result = (
                _("Last executed task '%s'\n%s created jobs ") % (
                    self.name, count_created_job))
            task_result += _("(menu Connectors > Queue > Jobs).")
            vals = {'task_result': task_result}
            self.backend_id.write(vals)
        else:
            task_result = _("Task '%s'\nNo created job") % self.name
            task_result += (_("\nCheck coherence between chunk size '%s' "
                            "and real end of file '%s'")
                            % (self.chunk_size, eof))
            vals = {'task_result': task_result}
            self.backend_id.write(vals)

        self.ensure_one()
        view_id = self.env.ref('connector_google_spreadsheet.'
                               'view_google_spreadsheet_backend_form')
        return {
            'res_model': 'google.spreadsheet.backend',
            'view_id': view_id.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.backend_id.id,
            'target': 'current',
        }


class GoogleSpreadsheetBackend(models.Model):
    _name = 'google.spreadsheet.backend'
    _description = 'Google Spreadsheet Backend'

    _inherit = 'connector.backend'

    _backend_type = 'google.spreadsheet'

    name = fields.Char(
        default="?", copy=False,
        help="Choose a name according tasks defined below.")
    email = fields.Char(required=True, help='Google developer email account')
    p12_key = fields.Binary(
        string='P12 key', required=True,
        help="Google Sheets Key\n see https://developers.google.com/"
             "console/help/new/#service_accounts")
    version = fields.Selection(
        selection=[('3.0', 'Version 3')], default='3.0',
        help="Google Sheet API\n"
             "https://developers.google.com/google-apps/spreadsheets/")
    task_result = fields.Text(
        'Last Task Result', readonly=True, copy=False,
        help="Here is the log of last action occured during "
             "the importation process")
    document_ids = fields.One2many(
        'google.spreadsheet.document',
        'backend_id', string='Google spreadsheet documents',
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         _("Spreadsheet Import Backend 'Name' field must be unique")),
    ]

    def active_cron_sheet(self):
        self.ensure_one()
        tasks = self.env['google.spreadsheet.document'].search(
            INITIAL_IMPORT_DOMAIN)
        domain_string = ['%s %s %s' % (x[0], x[1], x[2])
                         for x in INITIAL_IMPORT_DOMAIN]
        message = _("No task with satisfied conditions (fields %s)"
                    " to import" % ' and '.join(domain_string))
        if not tasks:
            return self.write({'task_result': message})
        cron = self.env.ref(
            'connector_google_spreadsheet.ir_cron_spreadsheet_import')
        cron.write({'active': True})
        params = {'interval_number': cron.interval_number,
                  'interval_type': cron.interval_type,
                  'now': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        message = _("Initial import will begin less than %(interval_number)s"
                    " %(interval_type)s after %(now)s" % params)
        self.write({'task_result': message})

    @api.model
    def format_spreadsheet_error(self, message):
        """ Used by the import_document function
            You may override it to customize your messages
            Default behavior add connection identification to error message
        """
        string_uuid = self.env['ir.config_parameter'].get_param(
            'database.uuid', default='')
        connect_string = " || database '%s', uuid '%s'" % (self._cr.dbname,
                                                           string_uuid)
        return message + connect_string


def open_document_url(session, job):
    url = job.args[1]['document_url']
    action = {
        'type': 'ir.actions.act_url',
        'target': 'new',
        'url': url,
    }
    return action


def convert_import_data(rows_to_import, fields):

    indices = [index for index, field in enumerate(fields) if field]

    if len(indices) == 1:
        mapper = lambda row: [row[indices[0]]]
    else:
        mapper = operator.itemgetter(*indices)

    import_fields = filter(None, fields)
    filter_row = False
    if 'skip_import' in import_fields:
        skip_import = import_fields.index('skip_import')
        filter_row = True

    data = []
    original_position = {}
    row_number = -1
    for row in itertools.imap(mapper, rows_to_import):
        row_number += 1
        if any(row):
            if filter_row:
                if row[skip_import]:
                    continue
                else:
                    row = list(row)
                    row.pop(skip_import)
            original_position[len(data)] = row_number
            data.append(row)
    if filter_row:
        import_fields.remove('skip_import')
    return data, import_fields, original_position


@job
def set_cron_inactive(session, model_name, args):
    """ Job created by the cron to unactive itself """
    cr = registry(session.cr.dbname).cursor()
    cron_id = args['cron_id']
    cr.execute("UPDATE ir_cron SET active='f' WHERE id = %s" % cron_id)
    cr.commit()
    cr.close()
    return True


@job
@related_action(action=open_document_url)
def import_document(session, model_name, args):

    import_obj = session.pool['base_import.import']
    model_obj = session.pool[args['erp_model']]

    backend_id = args['backend_id']
    document_url = args['document_url']
    document_sheet = args['document_sheet']
    fields = args['fields']
    row_start = args['chunk_row_start']
    row_end = args['chunk_row_end']
    col_start = args['sheet_col_start']
    col_end = args['sheet_col_end']
    error_col = args['error_col']

    backend = session.env['google.spreadsheet.backend'].browse(
        backend_id)

    document = open_document(backend, document_url)
    sheet = document.worksheet(document_sheet)

    start = sheet.get_addr_int(row_start, col_start)
    stop = sheet.get_addr_int(row_end, col_end)
    chunk = sheet.range(start + ':' + stop)

    cols = col_end - col_start + 1
    rows = row_end - row_start + 1
    data = [['' for c in range(cols)] for r in range(rows)]

    for cell in chunk:
        i = cell.row - row_start
        j = cell.col - col_start
        data[i][j] = cell.value

    available_fields = import_obj.get_fields(
        session.cr,
        session.uid,
        model_obj._name,
        context=session.context,
        depth=FIELDS_RECURSION_LIMIT
    )
    available_fields.append({
        u'name': u'skip_import',
        u'string': u'Skip Import',
        })

    headers_raw = iter([fields])
    headers_rawders, headers_match = import_obj._match_headers(
        headers_raw,
        available_fields,
        options={'headers': True},
    )

    fields = [False] * len(headers_match)
    for indice, header in headers_match.items():
        if isinstance(header, list) and len(header):
            fields[indice] = '/'.join(header)
        else:
            fields[indice] = False
    data, import_fields, original_position = convert_import_data(data, fields)
    try:
        # import the chunk of clean data
        result = model_obj.load(session.cr,
                                session.uid,
                                import_fields,
                                data,
                                context=session.context)
    except Exception as e:
        if config.get('debug_mode'): raise
        first_row = {}
        imported_fields = [x for x in headers_raw if x in fields]
        unimported_fields = [x for x in headers_raw if x not in fields]
        traceb = traceback.format_exc()
        if data:
            first_row = dict(zip(imported_fields, data[0]))
        raise Warning(
            SHEET_APP,
            "convert_import_data method can't finish its job. "
            "Here is your input data:\n\nNOT imported fields %s"
            "\n\nIMPORTED fields %s"
            "\n\nDATA %s\n\nFirst Row Data: %s\n\n"
            "Returned Error Value: %s\n\nTraceback:\n %s" % (
                unimported_fields, imported_fields, data,
                first_row, e.message, traceb))

    # clear previous errors
    error_cells = None
    if error_col is not None:
        start = sheet.get_addr_int(row_start, error_col)
        stop = sheet.get_addr_int(row_end, error_col)
        error_cells = sheet.range(start + ':' + stop)
        for cell in error_cells:
            cell.value = ''

    # log errors
    errors = False
    messages = []
    for m in result['messages']:
        row_from = row_start + original_position[m['rows']['from']]
        row_to = row_start + original_position[m['rows']['to']]

        for row in range(row_from, row_to+1):
            message = m['message']
            message_type = m['type']
            messages.append('%s:line %i: %s' % (message_type, row, message))
            if message_type == 'error':
                errors = True
                if error_cells:
                    for cell in error_cells:
                        if cell.row == row:
                            cell.value = backend.format_spreadsheet_error(message)
                            break

    if error_cells:
        sheet.update_cells(error_cells)

    if errors:
        raise FailedJobError(messages)
    else:
        imported_ids = ', '.join([str(id_) for id_ in result['ids']])
        messages.append('Imported/Updated ids: %s' % imported_ids)

    return '\n'.join(messages)
