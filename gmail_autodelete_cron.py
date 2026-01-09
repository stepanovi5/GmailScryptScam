import imaplib
import email
import os
import sys

# ==============================================================
# НАСТРОЙКИ — МЕНЯЙ ТОЛЬКО ЭТО
# ==============================================================

EMAIL_ACCOUNTS = [
    "youremail1@gmail.com",
    "youremail2@gmail.com"
]

# Переменные окружения с паролями приложений
# export GMAIL_PASS_1="пароль"
# export GMAIL_PASS_2="пароль"
PASSWORD_ENV_VARS = [
    "GMAIL_PASS_1",
    "GMAIL_PASS_2"
]

KEYWORDS = [
    "tinyurl.com",
    "https://oro-z.com/",
    "Codeby",
    "getmatch",
    "мы не зафиксировали получение необходимых документов",
    "колесо фортуны",
    "я планирую осуществить возврат согласованной суммы.",
    "OpenSea",
    "Талисман удачи",
    "FLAGMAN",
    "MARTIN",
    "ФАРТ",
    "Сейчас у тебя есть преимущество: пополняешь депозит",
    "Бонус до 200"
]

# INBOX и СПАМ
FOLDERS_TO_CHECK = [
    "INBOX",
    "[Gmail]/&BCEEPwQwBDw-"
]

# ==============================================================
# КОНЕЦ НАСТРОЕК
# ==============================================================

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993


def log(msg):
    print(msg)
    sys.stdout.flush()


def login(email_account, password):
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(email_account, password)
    return mail


def extract_body(msg):
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get("Content-Disposition"):
                try:
                    body += part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8",
                        errors="ignore"
                    )
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8",
                errors="ignore"
            )
        except:
            pass

    return body


def delete_in_mailbox(mail, mailbox, keywords):
    deleted = 0

    status, _ = mail.select(mailbox)
    if status != "OK":
        log(f"⚠️ Не удалось открыть папку: {mailbox}")
        return 0

    status, data = mail.search(None, "ALL")
    if status != "OK":
        return 0

    for uid in data[0].split():
        status, msg_data = mail.fetch(uid, "(RFC822)")
        if status != "OK":
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        body = extract_body(msg)

        for word in keywords:
            if word.lower() in body.lower():
                subject = msg.get("Subject", "(без темы)")
                log(f"🗑 Удаляю: {subject} | папка: {mailbox}")
                mail.store(uid, "+FLAGS", r"(\Deleted)")
                deleted += 1
                break

    mail.expunge()
    return deleted


def main():
    log("=== АВТО-ЧИСТКА GMAIL (CRON) ===")

    passwords = []
    for env_var in PASSWORD_ENV_VARS:
        pwd = os.environ.get(env_var)
        if not pwd:
            log(f"❌ Не задана переменная окружения: {env_var}")
            return
        passwords.append(pwd)

    total_deleted = 0

    for i, email_acc in enumerate(EMAIL_ACCOUNTS):
        log(f"\n📬 Проверка ящика: {email_acc}")

        try:
            mail = login(email_acc, passwords[i])
        except Exception as e:
            log(f"❌ Ошибка входа: {e}")
            continue

        for folder in FOLDERS_TO_CHECK:
            log(f" → Папка: {folder}")
            deleted = delete_in_mailbox(mail, folder, KEYWORDS)
            log(f"   Удалено: {deleted}")
            total_deleted += deleted

        mail.logout()

    log(f"\n✔️ ИТОГО удалено писем: {total_deleted}")


if __name__ == "__main__":
    main()
