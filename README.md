# SmartMailer

SmartMailer is a Python library for sending bulk emails with templated subjects, plain-text and HTML bodies, attachments, CC/BCC, and crash-safe session tracking that stops the same recipient being emailed twice.

## Features

- Send individual or bulk emails
- Templated subjects, plain text, and HTML content (Jinja2)
- Attachments support
- CC and BCC support
- Session management to avoid duplicate sends, including resuming after a crash
- Logging for all actions

## Installation

Install the latest version from the Git repository
([`SSN-SNUC-MUN/SmartMailer`](https://github.com/SSN-SNUC-MUN/SmartMailer)),
which is ahead of PyPI:

```shell
pip install "git+https://github.com/SSN-SNUC-MUN/SmartMailer.git"
```

For development from this repository:

```shell
git clone https://github.com/SSN-SNUC-MUN/SmartMailer.git
cd SmartMailer
pip install -e ".[test]"
```

### Gmail

Gmail requires an **App Password** — your normal account password will not work over SMTP.
Enable 2-Step Verification, then create one at <https://myaccount.google.com/apppasswords>.

```shell
export SMARTPASSWORD='your-16-char-app-password'
```

Pass it as `password`. Never hardcode it in source.

## Quickstart

```python
import os

from jinja2 import Environment

from smartmailer import (
    JinjaTemplateParser,
    JinjaTemplateRenderer,
    SmartMailer,
    TemplateEngine,
    TemplateModel,
    TemplateValidator,
)


class Recipient(TemplateModel):
    name: str
    email: str          # must hold the destination address


env = Environment()
template = TemplateEngine(
    parser=JinjaTemplateParser(env),
    validator=TemplateValidator(),
    renderer=JinjaTemplateRenderer(env),
    subject="Hello {{ name }}",
    text="Dear {{ name }}, this is a test.",
    html="<p>Dear <b>{{ name }}</b>, this is a test.</p>",
)

recipients = [
    Recipient(name="Alice", email="alice@example.com"),
    Recipient(name="Bob", email="bob@example.com"),
]

mailer = SmartMailer(
    sender_email="you@gmail.com",
    password=os.environ["SMARTPASSWORD"],
    provider="gmail",          # "gmail" or "outlook"
    session_name="june_campaign",
)

mailer.send_emails(recipients=recipients, email_field="email", template=template)
```

Full documentation, including attachments, CC/BCC and filters: [DOCS.md](DOCS.md).

## Session management

Sent recipients are recorded in `mail_sessions/<session_name>-<hash>.db` under the
current working directory. Rerunning the same script after a crash resumes where
it stopped: recipients already recorded are skipped before any email is rendered
or sent. Delete the `mail_sessions/` folder (or use a new `session_name`) to start
a fresh run.

## License

[MIT License](LICENSE)

## Credits

This project was brought to life by a squad in the Tech Team of [SSN-SNUC MUN 2025](https://ssnsnucmun.in)'s Organizing Committee.

- [Nilaa](http://github.com/nil-aa)
- [Kamlesh](http://github.com/Kamlesh-DevOP)
- [Sharon](http://github.com/sharonprabhu11)
- [Nitin Karthick](http://github.com/yukii1004)
- [Mahasvan](http://github.com/Mahasvan)
