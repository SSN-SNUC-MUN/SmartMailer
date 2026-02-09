# SmartMailer

## Introduction

This is a library that makes it easy to handle mass-emailing on a large scale.
The main purpose of this library is to streamline and standardize template usage, and to assist in crash recovery by incorporating state management.

## Usage

### Install the Library

The process is not as straightforward as "pip install smartmailer", and we're working on it!

Until then,

```shell
pip install sqlalchemy tabulate pydantic jinja2

pip install -i https://test.pypi.org/simple/ smartmailer==0.0.3
```

Or,

```shell
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ smartmailer
```

### Gmail App Password Setup

To send emails using Gmail, you need to generate an **App Password** instead of your regular Gmail password. Follow these steps:

1. **Enable 2-Step Verification**
   - Go to your [Google Account Security Settings](https://myaccount.google.com/security)
   - Click on "2-Step Verification" and follow the prompts to enable it

2. **Generate an App Password**
   - After enabling 2-Step Verification, go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" as the app and "Other (Custom Name)" as the device
   - Name it something like "SmartMailer"
   - Click "Generate" and copy the 16-character password shown

3. **Use the App Password in SmartMailer**
   - Use this 16-character password (without spaces) as the `password` argument when initializing `SmartMailer`

**NOTE**: App Passwords can only be generated if 2-Step Verification is enabled on your Google account. Keep your App Password secure and do not share it.

### Importing and Using the Library

```python
from smartmailer import SmartMailer, TemplateModel, TemplateEngine
from smartmailer.core.template import JinjaTemplateParser, JinjaTemplateRenderer, TemplateValidator
from jinja2 import Environment

```

After importing, we need to define a schema for our data model.
This MySchema class inherits from TemplateModel.

(It's like defining a `Pydantic` model from its `BaseModel` class!)

We have four fields for this example. These four fields will be all we need to build the metadata for our email.

**NOTE**: Make sure to have a field for the **destination email address** (`email` here), as that will be used for the internal email logic.
You will use this as the `sender_email` argument when calling `send_emails`.

```python
class MySchema(TemplateModel):
    name: str
    committee: str
    allotment: str
    email: str
    
```

Next up, we define the templates for our subject and body.

### Defining Templates

SmartMailer uses **Jinja2** for templating. Jinja2 is a powerful templating engine that allows you to use variables, conditionals, loops, and more.

- Template variables are defined using **Double Curly Braces**: `{{ variable_name }}`
- Variable names correspond to the `MySchema` fields you defined previously.
- Whitespaces between the variable name and the curly braces are optional, but we recommend them for better readability.

**NOTE**: Variable names must match the field names in your schema exactly. All field names **must be lowercase Python identifiers** (e.g., `name`, `email`, `committee_name`). Uppercase characters or special characters will cause validation errors.

Now, let's define the templates for the subject and body in these two files:

`subject.txt`:

```text
MUN Allotment Details
```

`body.txt`:

```text
Dear {{ name }},
Congratulations!! 
You are assigned to the {{ committee }} committee with the allotment of {{ allotment }}.
Regards,
The Organizing Committee
```

Let's load them into string objects, and initialize our Template Engine with the required components.

```python
with open("body.txt", "r") as f:
    body = f.read()

with open("subject.txt", "r") as f:
    subject = f.read()

# Create Jinja2 environment
env = Environment()

# Initialize the template components
parser = JinjaTemplateParser(env)
renderer = JinjaTemplateRenderer(env)
validator = TemplateValidator()

# Create the template engine with all components
template = TemplateEngine(
    parser=parser,
    validator=validator,
    renderer=renderer,
    subject=subject,
    text=body
)
```

### Advanced Jinja2 Features

**Conditionals:**

```text
Dear {{ name }},
{% if allotment %}
You have been assigned: {{ allotment }}
{% else %}
Your allotment is pending.
{% endif %}
```

**Loops (if your data contains lists):**

```text
Your committees:
{% for item in committees %}
- {{ item }}
{% endfor %}
```

**Filters:**

```text
Dear {{ name | upper }},
Your email is: {{ email | lower }}
```

## Loading Data

The list of recipients is expected to be a list of `MySchema` objects, where we defined `MySchema` previously.
From whatever data source you have, convert the data into the schema that you defined.

In this example, my datasource is a list of dictionaries, for convenience.

```python
recipients = [
    {"name": "John", "committee": "ECOSOC", "allotment": "Algeria", "email": "myEmail@gmail.com"},
    {"name": "John", "committee": "ECOSOC", "allotment": "Algeria", "email": "myEmail@outlook.com"},
    {"name": "John", "committee": "ECOSOC", "allotment": "Algeria", "email": "myEmail@snuchennai.edu.in"},
]

obj_recipients = [MySchema(name=recipient['name'], committee=recipient['committee'], allotment=recipient['allotment'], email= recipient['email'])  for recipient in recipients]
```

### Sending the Emails

Next, we define the SmartMailer instance which handles the email-sending for these recipients.
We need to provide the source email credentials, as well as the email provider to be used.

Currently supported options are: `"gmail"` and `"outlook"`. (case sensitive).

```python
smartmailer = SmartMailer(
    sender_email="myEmail@gmail.com",
    password="your-16-char-app-password",  # Use App Password for Gmail
    provider="gmail",
    session_name="test"
)
```

After that's done, all that's left is to send the emails.

```python
smartmailer.send_emails(
    recipients=obj_recipients,
    email_field="email",
    template=template
)
```

And we're done!

## Adding CC, BCC, and Attachments

Sometimes, you might want to send emails with CC, BCC, or include attachments. SmartMailer makes this easy — just add the relevant fields to your schema and pass the field names to `send_emails`.

First, update your schema to include optional fields for `cc`, `bcc`, and `attachments`:

```python
from typing import List, Optional

class MySchema(TemplateModel):
    name: str
    committee: str
    allotment: str
    email: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
```

When preparing your recipient data, you can now include these fields:

```python
recipients = [
    {
        "name": "Arjun",
        "committee": "UNDP",
        "allotment": "India",
        "email": "arjun@example.com",
        "cc": ["ccperson@example.com"],
        "bcc": ["bccperson@example.com"],
        "attachments": [r"C:\path\to\file.pdf"]
    },
    # ... more recipients ...
]

obj_recipients = [
    MySchema(
        name=recipient['name'],
        committee=recipient['committee'],
        allotment=recipient['allotment'],
        email=recipient['email'],
        cc=recipient.get('cc'),
        bcc=recipient.get('bcc'),
        attachments=recipient.get('attachments')
    )
    for recipient in recipients
]
```

When calling `send_emails`, just specify the field names for CC, BCC, and attachments:

```python
smartmailer.send_emails(
    recipients=obj_recipients,
    email_field="email",
    template=template,
    cc_field="cc",
    bcc_field="bcc",
    attachment_field="attachments"
)
```

That's it! Your emails will now include CC, BCC, and any attachments (all file types supported) you specify for each recipient.

## HTML Emails

SmartMailer supports sending HTML emails alongside plain text. When creating your template engine, you can specify both `text` and `html` content:

```python
html_body = """
<html>
<body>
    <h1>Welcome, {{ name }}!</h1>
    <p>You are assigned to the <strong>{{ committee }}</strong> committee.</p>
    <p>Your allotment: <em>{{ allotment }}</em></p>
</body>
</html>
"""

template = TemplateEngine(
    parser=parser,
    validator=validator,
    renderer=renderer,
    subject=subject,
    text=body,
    html=html_body
)
```

When both `text` and `html` are provided, the email will be sent as a multipart message, allowing email clients to display whichever format they prefer.

## Outlook Configuration

For Outlook/Hotmail accounts, use the following configuration:

```python
smartmailer = SmartMailer(
    sender_email="myEmail@outlook.com",
    password="your-outlook-password",
    provider="outlook",
    session_name="outlook-session"
)
```

**NOTE**: For personal Outlook accounts, you may need to enable SMTP in your Outlook settings:
1. Go to [Outlook Settings](https://outlook.live.com/mail/0/options/mail/accounts)
2. Navigate to "Sync email"
3. Enable "Let devices and apps use POP" (this also enables SMTP)
