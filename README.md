# simple_smtp_mailer
A simple, selfcontained, command-line smtp mailer.

## Features
- command-line interface
- send files as attachment (with easily configurable pretty names)
- multiple recipients
- secret config (username & password) configurable from env variables
- dry run


## Example Usage
```
$ export MAIL_SMTP=smtp.gmail.com MAIL_USERNAME=test@gmail.com MAIL_PASSWORD=1234

$ ./mailer.py john@doe.com -s 'this is a test' <<EOF
Hi John,
this is a test mail!
EOF
```

## Installation
- depends just on vanilla python3
- then just `chmod +x mailer.py` & include the file in Your `PATH`

