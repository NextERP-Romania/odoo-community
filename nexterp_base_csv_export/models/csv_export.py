# Copyright 2020 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).
import base64
import csv
import logging
import time
from collections.abc import Callable
from io import StringIO

from odoo import models

_logger = logging.getLogger()


class CSVExporter(models.AbstractModel):
    _name = "base.csv.export"
    _description = "Mixin for csv export"

    def generate_export(self, records, export_mapping, export_padding=False):
        """Export records according to mapping"""
        model = records and records[0]._name or "unknown model"
        _logger.info("export %d %s", len(records), model)
        if not export_padding:
            export_padding = []
        memfile = StringIO()
        headers = self.get_headers(export_mapping, export_padding)
        writer = csv.DictWriter(memfile, fieldnames=headers, delimiter=",")
        writer.writeheader()
        for record in records:
            row = {}
            mapping = export_mapping
            written = False
            for odoo_field, external_field, type_field in mapping:
                try:
                    record = record.with_context(lang=self.env.user.lang)
                    value = record[odoo_field]
                    if isinstance(value, Callable):
                        value = value()
                    if not value:
                        value = ""
                    if record._fields[odoo_field].type == "many2one":
                        if value:
                            value = value.name_get()[0][1]
                    elif record._fields[odoo_field].type in ["one2many", "many2many"]:
                        value = ",".join([x.name_get()[0][1] for x in value])
                    if (not value or value == "") and type_field:
                        if type_field == "boolean":
                            value = "False"
                        if type_field == "number":
                            value = "0"
                        if type_field == "NAfield":
                            value = "n/a"
                    if value and type_field == "CharLimit50":
                        value = value[:50]
                    if type_field == "boolean_number":
                        value = "1" if value else "0"
                    if value and odoo_field == "lang":
                        value = value[0].upper()
                    row[external_field] = value
                except KeyError:
                    if isinstance(getattr(record, odoo_field, None), Callable):
                        if type_field == "m2m":
                            values = getattr(record, odoo_field)()
                            if values and values != "":
                                for _val in values:
                                    row[external_field] = value
                                    writer.writerow(row)
                            written = True
                        else:
                            value = getattr(record, odoo_field)()
                            row[external_field] = value
                    else:
                        # unknown field
                        _logger.warning('unknown field "%s"', odoo_field)
            if not written:
                writer.writerow(row)
        output = memfile.getvalue().encode()
        memfile.close()
        return output

    def get_headers(self, export_mapping, export_padding):
        headers = [x[1] for x in export_mapping]
        if export_padding:
            headers += [x[0] for x in export_padding]
        return headers

    def save_file(
        self,
        servers,
        file_type,
        output,
        config_name_for_filename,
        path=None,
        record=None,
    ):
        filename = config_name_for_filename
        filename += time.strftime("%Y_%m_%d_%H_%M_%S")
        for server in servers:
            self.save_to_sftp(server, file_type, output, filename, path=path)
        if record:
            self.save_attachment(file_type, output, filename, record)

    def save_to_sftp(self, server, file_type, output, filename, path=None):
        filename += file_type
        file = server.save_output_to_sftp(output, filename, path=path)
        return (file, filename)

    def save_attachment(self, file_type, content, filename, record=None):
        filename += file_type
        ira = self.env["ir.attachment"]
        if record:
            values = {
                "name": filename,
                "res_model": record._name,
                "res_id": record.id,
                "type": "binary",
                "datas": base64.b64encode(content),
            }
            ira.create(values)
