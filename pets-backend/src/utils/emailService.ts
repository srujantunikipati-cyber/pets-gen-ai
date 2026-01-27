// src/utils/emailService.ts
import sgMail, { MailDataRequired } from '@sendgrid/mail';
import dotenv from 'dotenv';
import { logger } from './logger';

dotenv.config();

sgMail.setApiKey(process.env.SENDGRID_API_KEY || '');

interface EmailPayload {
  subject: string;
  text?: string;
  html?: string;
}

export async function sendEmail(recipients: string[], payload: EmailPayload) {
  if (!payload.text && !payload.html) {
    throw new Error("Email must have either text or html content");
  }

  // SendGrid expects a `content` array if using TypeScript
  const msg: MailDataRequired = {
    to: recipients, // array of emails
    from: 'petroastapp@gmail.com', // must be verified in SendGrid
    subject: payload.subject,
    // text: payload.text || "",
    html: payload.html || "",
    // content: [
    //   {
    //     type: payload.html ? 'text/html' : 'text/plain',
    //     value: payload.html || payload.text || ''
    //   }
    // ]
  };

  try {
    logger.info(`📧 Sending email to: ${recipients.join(', ')}. Subject: ${payload.subject}`);
    const response = await sgMail.send(msg);
    logger.info(`✅ Email sent to ${recipients.join(', ')} - status: ${response[0].statusCode}`);
  } catch (err: any) {
    // Log the detailed error from SendGrid (like "Maximum credits exceeded")
    const errorBody = err.response?.body;
    logger.error(`❌ Failed to send email (Non-blocking): ${err.message || err}`);
    if (errorBody) {
      logger.error(`   SendGrid Error Details: ${JSON.stringify(errorBody)}`);
    }

    // DEVELOPMENT MODE FIX: 
    // Do NOT throw the error. Allow the process to continue so you can test user creation.
    // If you are in production, you might want to uncomment the line below.
    // throw err; 
  }
}
