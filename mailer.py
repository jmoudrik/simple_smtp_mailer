#!/usr/bin/env python3
import sys
import os

import textwrap
import argparse
import smtplib
from email.encoders import encode_base64
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


def stderr(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def file2mime(filename, pretty_filename):
    """
    :filename - where to load the data from
    :pretty_filename - hwo will the file be called on receiving end
    """
    part = MIMEBase('application', "octet-stream")
    with open(filename, "rb") as fin:
        part.set_payload(fin.read())
    # ugh, ugly non-pure function
    encode_base64(part)
    part.add_header('content-disposition', 'attachment',
                    filename=pretty_filename)
    return part


def send_mail(send_to, subject, text,
              server,
              username,
              password,
              port=465,
              reply_to=None,
              mime_files=None,
              fake=False,
              print_mime=False
              ):
    if mime_files is None:
        mime_files = []

    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = ", ".join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = Header(subject.encode('utf-8'), 'UTF-8').encode()
    if reply_to is not None:
        msg.add_header('reply-to', reply_to)
    msg.attach(MIMEText(text.encode('utf-8'), 'plain', 'UTF-8'))

    for f in mime_files:
        msg.attach(f)
    msg_as_str = msg.as_string()

    if print_mime:
        print(msg_as_str)

    if fake:
        stderr("not sending mail")
        return

    smtp = smtplib.SMTP_SSL(server, port=port)
    smtp.login(username, password)
    smtp.sendmail(username, send_to, msg_as_str)
    smtp.close()


if __name__ == "__main__":
    prog = 'jmmailer'
    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='A simple, self-contained SMTP mailer.'
        ' To be used (in scripts preferably) instead of'
        ' the builtin `mail` command without all the config.',
        epilog=textwrap.dedent(f"""\
        Example:
MAIL_SMTP=smtp.gmail.com MAIL_USERNAME=test@gmail.com MAIL_PASSWORD=1234 {prog}\
john@doe.com -s 'this is a test' <<EOF
Hi John,
this is a test mail!
EOF"""))

    parser.add_argument('address', nargs='+',
                        help='the recipient(s) of the mail')
    parser.add_argument('-s', '--subject',
                        default='NO SUBJECT', help='set subject of the mail')
    parser.add_argument('-f', '--file',
                        default=[],
                        action='append',
                        help="""attach given FILE in the mail;
            the FILE specified can be either a `FILENAME`,
            or `FILENAME:PRETTY_FILENAME`. In the later, the file's name
            (as seen by recipient) will be `PRETTY_FILENAME`.
            Use --file-separator to provide different separator than `:`.""")
    parser.add_argument('--reply-to',
                        help='set the reply to adress')
    parser.add_argument('--smtp',
                        help='set smtp server to send the message to; if not present, read from MAIL_SMTP env variable')
    parser.add_argument('--port',
                        default=465,
                        type=int,
                        help='set smtp port')
    parser.add_argument('--username',
                        help='set the username to login at the SMTP server; if not present, read from MAIL_USERNAME env variable')
    parser.add_argument('--password',
                        help='set the password to login at the SMTP server; if not present, read from MAIL_PASSWORD env variable')
    parser.add_argument('-fs', '--file-separator',
                        default=':',
                        help='set separator for attaching files, see --file; default separator is `:`')
    parser.add_argument('-n', '--no-mail',
                        action='store_true', default=False,
                        help='do not send the mail for real, just parse args & load input files & prep mime message')
    parser.add_argument('--print-mime',
                        action='store_true', default=False,
                        help='print mime text of the message to STDOUT')

    args = parser.parse_args()
    print(args)
    print()

    mfs = []
    for f in args.file:
        toks = f.split(args.file_separator)
        if len(toks) not in (1, 2):
            stderr(
                f"Invalid filename {f!r}; with separator {args.file_separator!r}, we got {len(toks)} parts, must be 1 or 2")
            sys.exit(1)
        filename, pretty = toks[0], os.path.basename(toks[0])
        if len(toks) == 2:
            pretty = toks[1]
        if not os.path.exists(filename):
            stderr(f"the file {filename!r} does not exist")
            sys.exit(1)

        stderr(f"will send file {filename!r} as {pretty!r}")

        mf = file2mime(filename, pretty)
        mfs.append(mf)

    server = args.smtp or os.environ.get('MAIL_SMTP')
    if server is None:
        stderr("smtp server not provided, use --smtp or MAIL_SMTP env variable")
        sys.exit(1)
    username = args.username or os.environ.get('MAIL_USERNAME')
    if username is None:
        stderr("smtp username not provided, use --username or MAIL_USERNAME env variable")
        sys.exit(1)
    password = args.password or os.environ.get('MAIL_PASSWORD')
    if password is None:
        stderr("smtp password not provided, use --password or MAIL_PASSWORD env variable")
        sys.exit(1)

    body = sys.stdin.read()

    send_mail(args.address, args.subject,
              body,
              server, username, password,
              port=args.port,
              mime_files=mfs,
              reply_to=args.reply_to,
              fake=args.no_mail,
              print_mime=args.print_mime)
