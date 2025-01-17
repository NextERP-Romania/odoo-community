# Copyright 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).
import logging
import os
from io import StringIO

import paramiko

from odoo import fields, models

_logger = logging.getLogger("SFTP")


class SFTPServer(models.Model):
    _name = "sftp.server"
    _inherit = "mail.thread"
    _description = "SFTP Mixim for save, fetch files"

    name = fields.Char("Server Name", tracking=True)
    host = fields.Char("Server URL", tracking=True)
    port = fields.Integer("Server Port", tracking=True)
    username = fields.Char("Server User", tracking=True)
    password = fields.Char("Server Password")
    read_directory = fields.Char(tracking=True)
    write_directory = fields.Char(tracking=True)
    company_ids = fields.Many2many("res.company", string="Company", tracking=True)
    active = fields.Boolean(default=True)
    errors = fields.Text(help="here you can see errors from running", default="")

    def _open_sftp_client(self):
        _logger.info("open sftp connection")
        self.ensure_one()
        sftp_client = None
        try:
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            transport.set_keepalive(10)
            sftp_client = paramiko.SFTPClient.from_transport(transport)
        except paramiko.SSHException as exc:
            error = f"UTC{fields.datetime.now()}ERROR in _open_sftp_client! {exc}\n"
            _logger.error(error)
            return error
        return sftp_client

    def _close_sftp_client(self, sftp_client):
        _logger.info("Close sftp client %s", sftp_client)
        if sftp_client:
            _logger.info("close sftp connection")
            sftp_client.close()

    def save_output_to_sftp(self, output, filename, path=None):
        _logger.info("save to %s - %s" % (path, filename))
        sftp_client = self._open_sftp_client()
        fileObj = StringIO(output.decode())
        try:
            if not path:
                path = self.write_directory
            sftp_client.chdir(path)
        except paramiko.SSHException as exc:
            _logger.error(
                "Error while trying to cd to sftp directory %s: %s", filename, exc
            )
            _logger.info("Trying to reconnect")
            self._close_sftp_client(sftp_client)
            sftp_client = self._open_sftp_client()
            sftp_client.chdir(self.write_directory)
        sftp_client.putfo(fileObj, os.path.basename(filename), confirm=False)
        self._close_sftp_client(sftp_client)

    def get_file_list_from_sftp(self, filepath, sftp_client=None):
        _logger.info(">ls %s", filepath)
        close_sftp_client = not bool(sftp_client)
        if not sftp_client:
            sftp_client = self._open_sftp_client()
        if type(sftp_client) is str:
            _logger.error(sftp_client)
            self.errors = sftp_client + self.errors
            return []
        filename_list = []
        filepath_content_list = []
        try:
            filepath_content_list = sftp_client.listdir(filepath)
        except Exception as e:
            error = f"Error while trying to list sftp directory {filepath}: {e}\n"
            _logger.error(error)
            self.errors = error + self.errors

        for fname in filepath_content_list:
            lstat = sftp_client.lstat(filepath + "/" + fname)
            if "d" not in str(lstat).split()[0]:  # do not take directories
                filename_list.append(fname)
        if close_sftp_client:
            self._close_sftp_client(sftp_client)
        return filename_list

    def move_files_on_sftp(self, files, destination_path):
        _logger.info("mv %s %s", files, destination_path)
        sftp_client = self._open_sftp_client()

        for sftp_file in files:
            sftp_client.rename(
                sftp_file, destination_path + os.path.basename(sftp_file)
            )

        self._close_sftp_client(sftp_client)

    def read_file(self, filename):
        sftp_client = self._open_sftp_client()
        file_content = False
        if sftp_client:
            try:
                opened_file = sftp_client.open(filename, mode="r")
                file_content = opened_file.read()
            except paramiko.SSHException as exc:
                _logger.error(f"ERROR in read_file!\n{exc}")
            finally:
                opened_file.close()
        self._close_sftp_client(sftp_client)
        return file_content

    def test_sftp_connection(self):
        title = "no error at connection to sftp servers:\n"

        for server in self:
            title += (
                f"({server},name={server.name},host={server.host},"
                f"username={server.username})\n"
            )
            sftp = server._open_sftp_client()
            if type(sftp) == str:  # means is a error
                title = sftp
                server.errors = sftp + (server.errors if server.errors else "")
                break
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": "",
                "sticky": False,
            },
        }
