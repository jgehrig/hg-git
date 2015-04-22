from dulwich.client import SubprocessWrapper
from mercurial import util
import subprocess

class SSHVendor(object):
    """Parent class for ui-linked Vendor classes."""


def generate_ssh_vendor(ui):
    """
    Allows dulwich to use hg's ui.ssh config. The dulwich.client.get_ssh_vendor
    property should point to the return value.
    """

    class _Vendor(SSHVendor):
        def run_command(self, host, command, username=None, port=None):
            sshcmd = ui.config("ui", "ssh", "ssh")
            args = util.sshargs(sshcmd, host, username, port)
            cmd = '%s %s %s' % (sshcmd, args,
                                util.shellquote(' '.join(command)))
            ui.debug('calling ssh: %s\n' % cmd)
            proc = subprocess.Popen(util.quotecommand(cmd), shell=True,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
            return SubprocessWrapper(proc)

    return _Vendor
