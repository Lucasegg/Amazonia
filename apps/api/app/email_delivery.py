"""Entrega transacional de e-mails para verificação e recuperação de conta."""
from __future__ import annotations
import os
import smtplib
import ssl
from email.message import EmailMessage
from fastapi import HTTPException

def send_account_email(recipient: str, subject: str, body: str) -> None:
    """Envia mensagem por SMTP autenticado; não registra tokens nos logs."""
    host = os.getenv("AMAZONIA_SMTP_HOST", "").strip()
    username = os.getenv("AMAZONIA_SMTP_USERNAME", "").strip()
    password = os.getenv("AMAZONIA_SMTP_PASSWORD", "")
    sender = os.getenv("AMAZONIA_EMAIL_FROM", "").strip()
    try:
        port = int(os.getenv("AMAZONIA_SMTP_PORT", "587"))
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Porta SMTP inválida.") from exc
    if port not in {465, 587}:
        raise HTTPException(status_code=503, detail="Use SMTP SSL na porta 465 ou STARTTLS na porta 587.")
    if not all((host, username, password, sender)):
        raise HTTPException(status_code=503, detail="Serviço de e-mail não configurado. Configure SMTP no ambiente da API.")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    context = ssl.create_default_context()
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as smtp:
                smtp.login(username, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(username, password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise HTTPException(status_code=503, detail="Não foi possível enviar o e-mail. Verifique a configuração SMTP.") from exc