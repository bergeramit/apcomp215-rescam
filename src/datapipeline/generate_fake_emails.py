"""
Generate fake email dataset for testing the phishing detection pipeline.
Creates CSV files with realistic-looking legitimate and phishing emails.
"""
import csv
import random
from datetime import datetime, timedelta

# Fake data pools
LEGIT_SENDERS = [
    "notifications@github.com",
    "team@slack.com",
    "noreply@google.com",
    "updates@linkedin.com",
    "support@dropbox.com",
    "billing@stripe.com",
    "hello@notion.so",
]

PHISHING_SENDERS = [
    "security@paypa1.com",  # Note the "1" instead of "l"
    "verify@amazon-security.net",
    "urgent@apple-support.xyz",
    "admin@netflix-billing.info",
    "alert@bankofamerica-secure.com",
    "support@microsoft-account.co",
]

RECEIVERS = ["user@company.com", "john.doe@email.com", "test@example.com"]

LEGIT_SUBJECTS = [
    "Weekly team update",
    "Your invoice is ready",
    "Meeting reminder: Tomorrow at 2pm",
    "Pull request merged: Feature #123",
    "Welcome to our service",
    "Password changed successfully",
    "Your monthly report is ready",
]

PHISHING_SUBJECTS = [
    "URGENT: Verify your account immediately",
    "Your account will be closed in 24 hours",
    "You've won $1,000,000!",
    "Suspicious activity detected - Click here",
    "Re: Your payment failed",
    "Confirm your identity to avoid suspension",
    "Action required: Update billing information",
]

LEGIT_BODIES = [
    "Hi there,\n\nThis is your weekly update. Everything is running smoothly.\n\nBest regards,\nThe Team",
    "Your invoice for this month is attached. Thank you for your business.\n\nCustomer Support",
    "Just a reminder about our meeting tomorrow at 2pm. See you there!\n\nBest,\nSarah",
    "Your pull request has been reviewed and merged. Great work!\n\nGitHub",
    "Welcome! We're excited to have you. Get started by exploring our features.\n\nThe Team",
    "Your password was successfully changed. If this wasn't you, please contact support.\n\nSecurity Team",
    "Your monthly report is ready to view in your dashboard.\n\nAnalytics Team",
]

PHISHING_BODIES = [
    "URGENT: We detected unusual activity on your account. Click here immediately to verify: http://evil-site.com/verify\n\nDo not ignore this message!",
    "Dear user,\n\nYour account will be permanently closed in 24 hours unless you confirm your identity at: http://fake-bank.net/login\n\nCustomer Service",
    "Congratulations! You are the lucky winner of our $1,000,000 prize! Click here to claim: http://scam-lottery.com\n\nPrize Team",
    "We noticed suspicious login attempts. Verify your account here: http://phishing-site.com or your account will be locked.\n\nSecurity Alert",
    "Your payment of $500 has failed. Update your billing information immediately: http://fake-payment.com\n\nBilling Department",
    "Action Required: Your account has been flagged. Confirm your identity within 12 hours: http://malicious-link.com\n\nAccount Security",
    "Click here to update your billing details or your services will be interrupted: http://scam-billing.com\n\nSupport Team",
]

PHISHING_URLS = [
    "http://evil-site.com/verify",
    "http://fake-bank.net/login",
    "http://scam-lottery.com",
    "http://phishing-site.com",
    "http://fake-payment.com",
    "http://malicious-link.com",
    "http://scam-billing.com",
]

LEGIT_URLS = [
    "https://github.com/notifications",
    "https://slack.com/messages",
    "https://support.google.com",
    "https://www.linkedin.com/updates",
    "https://www.dropbox.com/help",
    "",  # Some emails have no URLs
]


def generate_date():
    """Generate random date within last 90 days"""
    days_ago = random.randint(0, 90)
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime("%Y-%m-%d %H:%M:%S")


def generate_legit_email():
    """Generate a legitimate email"""
    return {
        "sender": random.choice(LEGIT_SENDERS),
        "receiver": random.choice(RECEIVERS),
        "date": generate_date(),
        "subject": random.choice(LEGIT_SUBJECTS),
        "body": random.choice(LEGIT_BODIES),
        "label": "0",  # 0 = legitimate
        "urls": random.choice(LEGIT_URLS),
        "spam_flag": "0",  # Email provider didn't mark as spam
    }


def generate_phishing_email():
    """Generate a phishing email"""
    # Some phishing emails get caught by spam filters (70%), some don't (30%)
    spam_flag = "1" if random.random() < 0.7 else "0"
    
    return {
        "sender": random.choice(PHISHING_SENDERS),
        "receiver": random.choice(RECEIVERS),
        "date": generate_date(),
        "subject": random.choice(PHISHING_SUBJECTS),
        "body": random.choice(PHISHING_BODIES),
        "label": "1",  # 1 = phishing
        "urls": random.choice(PHISHING_URLS),
        "spam_flag": spam_flag,  # Email provider's spam classification
    }


def generate_dataset(num_legit=50, num_phishing=50, filename="fake_emails.csv"):
    """
    Generate a fake email dataset
    
    Args:
        num_legit: Number of legitimate emails to generate
        num_phishing: Number of phishing emails to generate
        filename: Output CSV filename
    """
    emails = []
    
    # Generate legitimate emails
    for _ in range(num_legit):
        emails.append(generate_legit_email())
    
    # Generate phishing emails
    for _ in range(num_phishing):
        emails.append(generate_phishing_email())
    
    # Shuffle to mix legitimate and phishing
    random.shuffle(emails)
    
    # Write to CSV
    fieldnames = ["sender", "receiver", "date", "subject", "body", "label", "urls", "spam_flag"]
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(emails)
    
    print(f"✅ Generated {len(emails)} fake emails ({num_legit} legit, {num_phishing} phishing)")
    print(f"✅ Saved to: {filename}")
    
    return filename


if __name__ == "__main__":
    # Generate a test dataset
    # You can adjust these numbers
    generate_dataset(
        num_legit=100,      # 100 legitimate emails
        num_phishing=100,   # 100 phishing emails
        filename="raw-datasets/fake_phishing_dataset.csv"
    )

