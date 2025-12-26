import imaplib
import email
import getpass
import re
import time

# ==============================================================
# XXXX >>> НАСТРОЙКИ — МЕНЯЙ ТОЛЬКО ЭТО <<< XXXX

# 👉 ДВА GMAIL ЯЩИКА
EMAIL_ACCOUNTS = [
    "youremail1@mail.com",
    "youremail2@mail.com"
]

# 👉 КОНТРОЛЬНЫЕ СЛОВА (можно несколько через запятую)
KEYWORDS = [
    "tinyurl.com",
    "www.tinyurl.com"
]

# 👉 ПАПКИ ДЛЯ ПРОВЕРКИ
FOLDERS_TO_CHECK = ["INBOX", "[Gmail]/&BCEEPwQwBDw-"]

# 👉 Частота проверки (в секундах)
CHECK_EVERY_SECONDS = 30

# XXXX >>> КОНЕЦ НАСТРОЕК <<< XXXX
# ==============================================================

IMAP_HOST = 'imap.gmail.com'
IMAP_PORT = 993


def login(email_account, password):
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(email_account, password)
    return mail


def delete_in_mailbox(mail, mailbox, keywords):
    deleted = 0
    status, _ = mail.select(mailbox)
    if status != "OK":
        print(f"Не удалось открыть папку: {mailbox}")
        return 0

    status, data = mail.search(None, "ALL")
    if status != "OK":
        return 0

    for uid in data[0].split():
        status, msg_data = mail.fetch(uid, '(RFC822)')
        if status != "OK":
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode(
                            part.get_content_charset() or 'utf-8',
                            errors='ignore'
                        )
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or 'utf-8',
                    errors='ignore'
                )
            except:
                pass

        # Проверяем каждое слово
        for word in keywords:
            if word.lower() in body.lower():
                subj = msg.get('Subject')
                print(f"🗑 Удаляю письмо: {subj} (в '{mailbox}')")
                mail.store(uid, '+FLAGS', r'(\Deleted)')
                deleted += 1
                break

    mail.expunge()
    return deleted


def main():
    print("=== АВТО-УДАЛЕНИЕ ПИСЕМ GMAIL ПО СЛОВАМ ===")

    # Пароли приложений для двух ящиков
    passwords = []
    for email_acc in EMAIL_ACCOUNTS:
        print(f"\nПароль приложения для {email_acc}:")
        password = getpass.getpass("> ")
        passwords.append(password)

    while True:
        total = 0

        for i, email_acc in enumerate(EMAIL_ACCOUNTS):
            print(f"\n📬 Проверяю: {email_acc}")

            try:
                mail = login(email_acc, passwords[i])
            except:
                print("Ошибка входа! Проверь пароль приложения.")
                continue

            for folder in FOLDERS_TO_CHECK:
                print(f" → Папка: {folder}")
                deleted = delete_in_mailbox(mail, folder, KEYWORDS)
                print(f"   Удалено: {deleted}")
                total += deleted

            mail.logout()

        print(f"\n✔️ Итог: удалено писем за цикл: {total}")
        print(f"⏳ Следующая проверка через {CHECK_EVERY_SECONDS} секунд...\n")
        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    main()
