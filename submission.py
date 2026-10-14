"""Explicit report submission through Gmail; credentials are server-only."""
from email.message import EmailMessage
from email.headerregistry import Address
import smtplib
import ssl

from reporting import export_docx,filename,period

def email_config(get):
    sender=str(get('EMAIL_ADDRESS','')).strip()
    password=str(get('EMAIL_PASSWORD',''))
    mode=str(get('EMAIL_MODE','testing')).strip().lower()
    if mode not in ['testing','administrator']:
        raise ValueError('EMAIL_MODE must be testing or administrator.')
    recipient=sender if mode=='testing' else str(get('ADMIN_EMAIL','')).strip()
    if not password.strip():raise ValueError('Set EMAIL_PASSWORD privately to your Google App Password before submitting.')
    for label,value in [('EMAIL_ADDRESS',sender),('ADMIN_EMAIL' if mode=='administrator' else 'EMAIL_ADDRESS',recipient)]:
        try:
            address=Address(addr_spec=value)
            if not address.domain or not address.username or any(c.isspace() for c in value):raise ValueError()
        except (ValueError,IndexError):raise ValueError(f'{label} must be a valid email address without spaces.')
    return sender,password,recipient,mode

def build_email(draft,sender,recipient,mode):
    m=draft['meta'];msg=EmailMessage()
    msg['From']=sender;msg['To']=recipient
    stream=' '.join(m['substream'].split())
    msg['Subject']=f"{'[TEST] ' if mode=='testing' else ''}DM RMO monthly submission — {stream} — {m['report_start']}"
    msg.set_content(f"Monthly RMO submission\n\nSub-stream: {m['substream']}\nPrepared by: {m['prepared_by']}\nProgress period: {period(m,'report')}\nWorkplan period: {period(m,'plan')}\n\nThe progress report and monthly workplan are attached as Word documents. Hours and evidence remain subject to verification and signature.\n"+ ('\nTesting mode: this submission was routed to the testing mailbox.\n' if mode=='testing' else ''))
    for kind in ['progress','workplan']:
        msg.add_attachment(export_docx(draft,kind),maintype='application',subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',filename=filename(draft,kind))
    return msg

def send_submission(draft,get):
    sender,password,recipient,mode=email_config(get)
    msg=build_email(draft,sender,recipient,mode)
    with smtplib.SMTP_SSL('smtp.gmail.com',465,context=ssl.create_default_context(),timeout=20) as smtp:
        smtp.login(sender,password)
        refused=smtp.send_message(msg)
        if refused:raise smtplib.SMTPRecipientsRefused(refused)
    return recipient
