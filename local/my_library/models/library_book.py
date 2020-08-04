from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.tools.translate import _
from os.path import join 
from odoo import exceptions
EXPORTS_DIR = 'srv/exports'

import logging


logger = logging.getLogger(__name__)


class BaseArchive(models.AbstractModel):
    _name = 'base.archive'
    active = fields.Boolean(default=True)
    def do_archive(self):
        for record in self:
            record.active = not record.active


class LibraryBook(models.Model):

    _name = 'library.book'
    _description = 'Library Book'
    _order = 'date_release desc, name'
    _rec_name = 'short_name'

    _inherit = ['base.archive', 'website.seo.metadata', 'website.multi.mixin']
    
    name = fields.Char('Title', required=True)
    short_name = fields.Char('Short Title')
    notes = fields.Text('Internal Notes')
    description = fields.Html('Description')
    cover = fields.Binary('Book Cover', groups='my_library.group_release_dates')
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer('Number of Pages')
    reader_rating = fields.Float(
        'Reader Average Rating',
        digits=(14, 4),  
        # Optional precision (total,decimals),
    )
    author_ids=fields.Many2many('res.partner', string = 'Authors')
    cost_price = fields.Float('Book Cost', 'Book Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Retail Price', 
        # optional: currency_field='currency_id',
    )
    publisher_id = fields.Many2one(
        'res.partner', string='Издатель',
        # optional:
        ondelete='set null',
        context={},
        domain=[],
    )
    publisher_city = fields.Char(
        'Город издателя',
        related='publisher_id.city',
        readonly=True)

    category_id = fields.Many2one('library.book.category')
    manager_remarks = fields.Text('Manager Remarks')
    isbn = fields.Char('ISBN')
    old_edition = fields.Many2one('library.book', string='Old Edition')
    is_public = fields.Boolean(groups='my_library.group_library_librarian')
    private_notes = fields.Text(groups='my_library.group_library_librarian')
    report_missing = fields.Text(
      string="Book is missing",
      groups='my_library.group_library_librarian')
    image = fields.Binary(attachment=True)
    html_description = fields.Html()
    book_issue_ids = fields.One2many('book.issue', 'book_id', copy=True, auto_join=True)
    restrict_country_ids = fields.Many2many('res.country')
    color = fields.Integer()

    """ age_days = fields.Float(
        string='Кол-во дней с релиза',
        compute='_compute_age',
        inverse='_inverse_age',
        search='_search_age',
        store=False, # optional
        compute_sudo=False # optional
    ) """

    age_days = fields.Float(
        string='Кол-во дней с релиза',
        compute='_compute_age',
        store=True, # optional
        compute_sudo=False # optional
    )

    state = fields.Selection([
        ('draft', 'Unavailable'),
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('lost', 'Lost')],
        'State', default="draft")

    ref_doc_id = fields.Reference(
        selection='_referencable_models',
        string='Reference Document')

    _sql_constraints = [
        ('name_uniq',
        'UNIQUE (name)',
        'Имя книги не уникально.')
    ]

    _sql_constraints = [
        ('positive_page', 'CHECK(pages>0)', 'No of pages must be positive')
    ]

    @api.constrains('date_release')
    def _check_release_date(self):
        for record in self:
            if record.date_release and record.date_release > fields.Date.today():
                raise models.ValidationError('Release date must be in the past')

    """ @api.depends('date_release')
    def _compute_age(self):
        today = fields.Date.today()
        for book in self.filtered('date_release'):
            delta = today - book.date_release
            book.age_days = delta.days """

    @api.depends('pages')
    def _compute_age(self):
        for book in self:
            book.age_days = book.pages

    def _inverse_age(self):
        today = fields.Date.today()
        for book in self.filtered('date_release'):
            d = today - timedelta(days=book.age_days)
            book.date_release = d

    def _search_age(self, operator, value):
        today = fields.Date.today()
        value_days = timedelta(days=value)
        value_date = today - value_days
        # convert the operator:
        # book with age > value have a date < value_date
        operator_map = {
            '>': '<', '>=': '<=',
            '<': '>', '<=': '>=',
        }
        new_op = operator_map.get(operator, operator)
        return [('date_release', new_op, value_date)]

    @api.model
    def _referencable_models(self):
        models = self.env['ir.model'].search([
            ('field_id.name', '=', 'message_ids')])
        return [(x.model, x.name) for x in models]

    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'available'),
            ('available', 'borrowed'),
            ('borrowed', 'available'),
            ('available', 'lost'),
            ('borrowed', 'lost'),
            ('lost', 'available')]
        return (old_state, new_state) in allowed

    def change_state(self, new_state):
        for book in self:
            if book.is_allowed_transition(book.state, new_state):
                book.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (book.state, new_state)
                raise UserError(msg)

    def make_available(self):
        self.change_state('available')

    def make_borrowed(self):
        self.change_state('borrowed')

    def make_lost(self):
        self.ensure_one()
        self.state = 'lost'
        if not self.env.context.get('avoid_deactivate'):
            self.active = False

    @api.model 
    def get_all_library_members(self):
        library_member_model = self.env['library.member'] 
        return library_member_model.search([])

    def create_categories(self):
        categ1 = {
            'name': 'Child category 1',
            #'description': 'Description for child 1'
        }
        categ2 = {
            'name': 'Child category 2',
            #'description': 'Description for child 2'
        }
        parent_category_val = {
            'name': 'Parent category',
            #'description': 'Description for parent category',
            'child_ids': [
                (0, 0, categ1),
                (0, 0, categ2),
            ]
        }
        # Total 3 records (1 parent and 2 child) will be craeted in library.book.category model
        record = self.env['library.book.category'].create(parent_category_val)
        return True

    def change_update_date(self):
        self.ensure_one()
        self.date_updated = fields.Datetime.now()

    def find_book(self):
        domain = [
            '|',
                '&', ('name', 'ilike', '12'),
                    ('category_id.name', 'ilike', 'Литер'),
                '&', ('name', 'ilike', 'Book Name 2'),
                    ('category_id.name', 'ilike', 'Category Name 2')
        ]
        books = self.search(domain)
        logger.info('Books found: %s', books)
        return True

    def find_partner(self):
        PartnerObj = self.env['res.partner']
        domain = [
            '&', ('name', 'ilike', 'Parth Gajjar'),
            ('company_id.name', '=', 'Odoo')
        ]
        partner = PartnerObj.search(domain)

    def filter_books(self):
        all_books = self.search([])
        filtered_books = self.books_with_multiple_authors(all_books)
        logger.info('Filtered Books: %s', filtered_books)

    @api.model
    def books_with_multiple_authors(self, all_books):
        def predicate(book):
            if len(book.author_ids) > 1:
                return True
        return all_books.filtered(predicate)

    def mapped_books(self):
        all_books = self.search([])
        books_authors = self.get_author_names(all_books)
        logger.info('Books Authors: %s', books_authors)

    @api.model 
    def get_author_names(self, books):
        return books.mapped('author_ids.name')

    def sort_books(self):
        all_books = self.search([])
        books_sorted = self.sort_books_by_date(all_books)
        logger.info('Books before sorting: %s', all_books)
        logger.info('Books after sorting: %s', books_sorted)

    @api.model 
    def sort_books_by_date(self, books):
        return books.sorted(key='date_release')

    @api.model 
    def create(self, values): 
        if not self.user_has_groups('my_library.group_library_librarian'): 
            if 'manager_remarks' in values: 
                raise UserError( 
                    'You are not allowed to modify ' 
                    'manager_remarks' 
                ) 
        return super(LibraryBook, self).create(values)

    def write(self, values): 
        if not self.user_has_groups('my_library.group_library_librarian'):
            if 'manager_remarks' in values: 
                raise UserError( 
                    'You are not allowed to modify ' 
                    'manager_remarks' 
                ) 
        return super(LibraryBook, self).write(values)

    def name_get(self): 
        result = [] 
        for book in self: 
            authors = book.author_ids.mapped('name') 
            name = '%s (%s)' % (book.name, ', '.join(authors)) 
            result.append((book.id, name)) 
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        print("===", args)
        args = [] if args is None else args.copy()
        if not(name == '' and operator == 'ilike'):
            args += ['|', '|',
                ('name', operator, name),
                ('isbn', operator, name),
                ('author_ids.name', operator, name)
            ]
            books_ids = self.search(args).ids
            return self.browse(books_ids).name_get()
        return super(LibraryBook, self)._name_search(
            name=name, args=args, operator=operator,
            limit=limit, name_get_uid=name_get_uid)

    def grouped_data(self):
        data = self._get_average_cost()
        logger.info("Groupped Data %s" % data)

    @api.model
    def _get_average_cost(self):
        grouped_result = self.read_group(
            [('cost_price', "!=", False)], # Domain
            ['category_id', 'cost_price:avg'], # Fields to access
            ['category_id'] # group_by
            )
        return grouped_result
        
    @api.model
    def _update_book_price(self):
        # NOTE: Real cases can be complex but here we just increse cost price by 10
        logger.info('Method update_book_price called from XML')
        all_books = self.search([])
        for book in all_books:
            book.cost_price += 10

    def book_rent(self):
        self.ensure_one()
        if self.state != 'available':
            raise UserError(_('Book is not available for renting'))
        rent_as_superuser = self.env['library.book.rent'].sudo()
        rent_as_superuser.create({
            'book_id': self.id,
            'borrower_id': self.env.user.partner_id.id,
        })

    def average_book_occupation(self):
        sql_query = """
            SELECT
                lb.name,
                avg((EXTRACT(epoch from age(return_date, rent_date)) / 86400))::int
            FROM
                library_book_rent AS lbr
            JOIN
                library_book as lb ON lb.id = lbr.book_id
            WHERE lbr.state = 'returned'
            GROUP BY lb.name;"""
        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchall()
        logger.info("Average book occupation: %s", result)

    def return_all_books(self):
        self.ensure_one()
        wizard = self.env['library.return.wizard']
        values = {
            'borrower_id': self.env.user.partner_id.id,
        }
        specs = wizard._onchange_spec()
        updates = wizard.onchange(values, ['borrower_id'], specs)
        value = updates.get('value', {})
        for name, val in value.items():
            if isinstance(val, tuple):
                value[name] = val[0]
        values.update(value)
        wiz = wizard.create(values)
        return wiz.sudo().books_returns()

    def report_missing_book(self):
        self.ensure_one()
        message = "Book is missing (Reported by: %s)" % self.env.user.name
        self.sudo().write({
            'report_missing': message
        })

class LibraryMember(models.Model):
    _name = 'library.member'
    _inherits = {'res.partner': 'partner_id'}
    partner_id = fields.Many2one(
        'res.partner', ondelete='cascade', required=True)
    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()
    date_of_birth = fields.Date('Date of birth')

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'
    published_book_ids = fields.One2many(
        'library.book', 'publisher_id',
        string='Published Books')
    authored_book_ids = fields.Many2many(
        'library.book',
        string='Authored Books',
        # relation='library_book_res_partner_rel'
    )
    count_books = fields.Integer( 'Number of Authored Books',
        compute='_compute_count_books' )

    @api.depends('authored_book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.authored_book_ids)

class ProductProduct(models.Model): 
    _inherit = 'product.product' 

    @api.model 
    def export_stock_level(self, stock_location):
        logger.info('export stock level for %s',
                      stock_location.name)
        products = self.with_context(
             location=stock_location.id).search([]) 
        products = products.filtered('qty_available') 
        logger.debug('%d products in the location',
                      len(products)) 
        fname = join(EXPORTS_DIR, 'stock_level.txt') 
        try: 
            with open(fname, 'w') as fobj: 
                for prod in products: 
                    fobj.write('%s\t%f\n' % (
                        prod.name, prod.qty_available)) 
        except IOError: 
            logger.exception( 
                'Error while writing to %s in %s', 
                'stock_level.txt', EXPORTS_DIR) 
            raise exceptions.UserError('unable to save file') 

class LibraryBookIssues(models.Model):
    _name = 'book.issue'

    _inherit = ['utm.mixin']

    book_id = fields.Many2one('library.book', required=True, ondelete='cascade', index=True, copy=False)
    submitted_by = fields.Many2one('res.users')
    issue_description = fields.Text()
