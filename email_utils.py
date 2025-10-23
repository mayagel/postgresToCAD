"""
Email utilities for sending notifications
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ENVIRONMENT

class EmailNotifier:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        
    def send_email(self, to_addresses, subject, body):
        """
        Send email notification
        
        Args:
            to_addresses (list): List of email addresses to send to
            subject (str): Email subject
            body (str): Email body
        """
        try:
            if ENVIRONMENT == "production":
                self.logger.warning("Production environment - email not sent (placeholder values)")
                self.logger.info(f"Would send email to {to_addresses} with subject: {subject}")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(body, 'plain'))
            
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable security
            server.login(self.smtp_user, self.smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.smtp_user, to_addresses, text)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {to_addresses}")
            
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            # Don't raise exception to avoid stopping the main process
            self.logger.warning("Email sending failed, but continuing with the process")
            
    def test_email_connection(self):
        """
        Test email connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if ENVIRONMENT == "production":
                self.logger.warning("Production environment - cannot test email connection")
                return False
                
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.quit()
            
            self.logger.info("Email connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Email connection test failed: {str(e)}")
            return False
